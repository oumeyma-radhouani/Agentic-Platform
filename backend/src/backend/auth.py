"""MongoDB-backed users and opaque browser sessions for NOVA."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from fastapi import Cookie, Depends, HTTPException, Request, status
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError


SESSION_COOKIE_NAME = "nova_session"
PASSWORD_SCHEME = "scrypt-v1"
PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 128
USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._@-]{2,63}$")

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64
_LOGIN_WINDOW = timedelta(minutes=15)
_LOGIN_LOCKOUT = timedelta(minutes=15)
_LOGIN_ATTEMPT_TTL = timedelta(days=1)
_MAX_LOGIN_FAILURES = 5


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_username(username: str) -> str:
    normalized = unicodedata.normalize("NFKC", username).strip().casefold()
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Username must be 3-64 characters and use letters, numbers, '.', '_', '@', or '-'."
        )
    return normalized


def validate_new_password(password: str) -> None:
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"Password must contain {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} characters."
        )


def hash_password(password: str) -> str:
    """Hash a password with a random salt using the standard-library scrypt KDF."""
    validate_new_password(password)
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return "$".join(
        (
            PASSWORD_SCHEME,
            str(_SCRYPT_N),
            str(_SCRYPT_R),
            str(_SCRYPT_P),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(derived).decode("ascii"),
        )
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify a password while treating malformed stored hashes as invalid."""
    try:
        scheme, n_value, r_value, p_value, salt_value, expected_value = encoded_hash.split("$")
        if scheme != PASSWORD_SCHEME:
            return False
        if (int(n_value), int(r_value), int(p_value)) != (
            _SCRYPT_N,
            _SCRYPT_R,
            _SCRYPT_P,
        ):
            return False
        salt = base64.b64decode(salt_value, validate=True)
        expected = base64.b64decode(expected_value, validate=True)
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derived, expected)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_lifetime() -> timedelta:
    raw_hours = os.getenv("NOVA_SESSION_HOURS", "12").strip()
    try:
        hours = int(raw_hours)
    except ValueError:
        hours = 12
    return timedelta(hours=min(max(hours, 1), 168))


def secure_cookie_enabled() -> bool:
    return os.getenv("NOVA_SESSION_COOKIE_SECURE", "false").strip().casefold() in {
        "1",
        "true",
        "yes",
    }


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    username: str
    display_name: str
    role: str

    def to_public_dict(self) -> dict[str, str]:
        return {
            "id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "role": self.role,
        }


class MongoAuthStore:
    """Persist users, login attempts, and hashed opaque sessions in MongoDB."""

    def __init__(self, mongo_uri: str, *, database_name: str = "nova_db") -> None:
        if not mongo_uri.strip():
            raise RuntimeError("MONGO_URI is required for authentication.")
        self.client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            tz_aware=True,
        )
        database = self.client[database_name]
        self.users = database["auth_users"]
        self.sessions = database["auth_sessions"]
        self.login_attempts = database["auth_login_attempts"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.users.create_index([("public_id", ASCENDING)], unique=True)
        self.users.create_index([("username_normalized", ASCENDING)], unique=True)
        self.sessions.create_index([("token_hash", ASCENDING)], unique=True)
        self.sessions.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
        self.sessions.create_index([("user_id", ASCENDING)])
        self.login_attempts.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

    def ping(self) -> None:
        self.client.admin.command("ping")

    def create_user(
        self,
        username: str,
        password: str,
        *,
        display_name: str | None = None,
        role: str = "member",
    ) -> AuthenticatedUser:
        normalized = normalize_username(username)
        if role not in {"admin", "member"}:
            raise ValueError("Role must be 'admin' or 'member'.")
        now = _utc_now()
        document = {
            "public_id": f"USR-{secrets.token_hex(8).upper()}",
            "username_normalized": normalized,
            "username": username.strip(),
            "display_name": (display_name or username).strip(),
            "password_hash": hash_password(password),
            "role": role,
            "disabled": False,
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = self.users.insert_one(document)
        except DuplicateKeyError as exc:
            raise ValueError("A user with that username already exists.") from exc
        return AuthenticatedUser(
            user_id=document["public_id"],
            username=document["username"],
            display_name=document["display_name"],
            role=role,
        )

    def authenticate(self, username: str, password: str) -> AuthenticatedUser | None:
        try:
            normalized = normalize_username(username)
        except ValueError:
            return None
        user = self.users.find_one({"username_normalized": normalized, "disabled": False})
        if not user or not verify_password(password, str(user.get("password_hash", ""))):
            return None
        return self._to_authenticated_user(user)

    def create_session(self, user: AuthenticatedUser) -> tuple[str, datetime]:
        token = secrets.token_urlsafe(48)
        now = _utc_now()
        expires_at = now + session_lifetime()
        self.sessions.insert_one(
            {
                "token_hash": hash_session_token(token),
                "user_id": user.user_id,
                "created_at": now,
                "last_seen_at": now,
                "expires_at": expires_at,
            }
        )
        return token, expires_at

    @staticmethod
    def login_attempt_key(username: str, client_reference: str) -> str:
        identity = unicodedata.normalize("NFKC", username).strip().casefold()
        return hashlib.sha256(f"{identity}|{client_reference}".encode("utf-8")).hexdigest()

    def is_login_blocked(self, attempt_key: str) -> bool:
        attempt = self.login_attempts.find_one({"_id": attempt_key})
        locked_until = attempt.get("locked_until") if attempt else None
        return bool(locked_until and locked_until > _utc_now())

    def record_login_failure(self, attempt_key: str) -> None:
        now = _utc_now()
        attempt = self.login_attempts.find_one({"_id": attempt_key})
        if not attempt or attempt.get("window_started_at", now) <= now - _LOGIN_WINDOW:
            failed_count = 1
            window_started_at = now
        else:
            failed_count = int(attempt.get("failed_count", 0)) + 1
            window_started_at = attempt.get("window_started_at", now)

        update: dict[str, Any] = {
            "failed_count": failed_count,
            "window_started_at": window_started_at,
            "updated_at": now,
            "expires_at": now + _LOGIN_ATTEMPT_TTL,
        }
        if failed_count >= _MAX_LOGIN_FAILURES:
            update["locked_until"] = now + _LOGIN_LOCKOUT
        self.login_attempts.update_one(
            {"_id": attempt_key}, {"$set": update}, upsert=True
        )

    def clear_login_failures(self, attempt_key: str) -> None:
        self.login_attempts.delete_one({"_id": attempt_key})

    def get_user_for_session(self, token: str) -> AuthenticatedUser | None:
        now = _utc_now()
        session = self.sessions.find_one(
            {"token_hash": hash_session_token(token), "expires_at": {"$gt": now}}
        )
        if not session:
            return None
        user = self.users.find_one(
            {"public_id": session["user_id"], "disabled": False}
        )
        if not user:
            self.sessions.delete_one({"_id": session["_id"]})
            return None
        self.sessions.update_one(
            {"_id": session["_id"]}, {"$set": {"last_seen_at": now}}
        )
        return self._to_authenticated_user(user)

    def revoke_session(self, token: str) -> None:
        self.sessions.delete_one({"token_hash": hash_session_token(token)})

    @staticmethod
    def _to_authenticated_user(document: dict[str, Any]) -> AuthenticatedUser:
        return AuthenticatedUser(
            user_id=str(document["public_id"]),
            username=str(document["username"]),
            display_name=str(document.get("display_name") or document["username"]),
            role=str(document.get("role", "member")),
        )


@lru_cache(maxsize=1)
def get_auth_store() -> MongoAuthStore:
    mongo_uri = os.getenv("MONGO_URI", "").strip()
    database_name = os.getenv("MONGO_DATABASE", "nova_db").strip() or "nova_db"
    try:
        return MongoAuthStore(mongo_uri, database_name=database_name)
    except (RuntimeError, PyMongoError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication database is unavailable or not configured.",
        ) from exc


def authenticated_scope(user: AuthenticatedUser) -> str:
    """Return the server-owned scope for context, history, and documents."""
    return f"user:{user.user_id}"


def require_authenticated_user(
    request: Request,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    store: MongoAuthStore = Depends(get_auth_store),
) -> AuthenticatedUser:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    try:
        user = store.get_user_for_session(session_token)
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication database is unavailable.",
        ) from exc
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or expired.",
        )
    request.state.user = user
    return user

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from src.backend.auth import (
    AuthenticatedUser,
    get_auth_store,
    hash_password,
    verify_password,
)
from src.backend.azure_rag import clear_document_index
from src.backend.context_store import clear_contexts


class FakeAuthStore:
    def __init__(self) -> None:
        self.users = {
            "alice": AuthenticatedUser("USR-ALICE", "alice", "Alice", "admin"),
            "bob": AuthenticatedUser("USR-BOB", "bob", "Bob", "member"),
        }
        self.sessions: dict[str, AuthenticatedUser] = {}
        self.failed_attempts: set[str] = set()

    @staticmethod
    def login_attempt_key(username: str, client_reference: str) -> str:
        return f"{username.casefold()}:{client_reference}"

    def is_login_blocked(self, attempt_key: str) -> bool:
        return False

    def record_login_failure(self, attempt_key: str) -> None:
        self.failed_attempts.add(attempt_key)

    def clear_login_failures(self, attempt_key: str) -> None:
        self.failed_attempts.discard(attempt_key)

    def authenticate(self, username: str, password: str):
        user = self.users.get(username.casefold())
        return user if user and password == "correct-password" else None

    def create_session(self, user: AuthenticatedUser):
        token = f"opaque-token-{user.user_id}"
        self.sessions[token] = user
        return token, datetime.now(timezone.utc) + timedelta(hours=12)

    def get_user_for_session(self, token: str):
        return self.sessions.get(token)

    def revoke_session(self, token: str) -> None:
        self.sessions.pop(token, None)


class PasswordTests(unittest.TestCase):
    def test_password_hash_is_salted_and_verifiable(self):
        first = hash_password("correct-password")
        second = hash_password("correct-password")

        self.assertNotEqual(first, second)
        self.assertNotIn("correct-password", first)
        self.assertTrue(verify_password("correct-password", first))
        self.assertFalse(verify_password("wrong-password", first))
        self.assertFalse(verify_password("correct-password", "malformed"))


class AuthenticationApiTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeAuthStore()
        app.dependency_overrides[get_auth_store] = lambda: self.store
        clear_contexts()
        clear_document_index()

    def tearDown(self):
        app.dependency_overrides.pop(get_auth_store, None)
        clear_contexts()
        clear_document_index()

    def test_login_me_and_logout_use_an_httponly_cookie(self):
        client = TestClient(app)
        login = client.post(
            "/api/auth/login",
            json={"username": "alice", "password": "correct-password"},
        )

        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["user"]["id"], "USR-ALICE")
        cookie = login.headers["set-cookie"]
        self.assertIn("nova_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=lax", cookie)

        profile = client.get("/api/auth/me")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["user"]["username"], "alice")

        logout = client.post("/api/auth/logout")
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(client.get("/api/auth/me").status_code, 401)

    def test_invalid_credentials_return_generic_error_and_no_cookie(self):
        response = TestClient(app).post(
            "/api/auth/login",
            json={"username": "alice", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid username or password.")
        self.assertNotIn("nova_session=", response.headers.get("set-cookie", ""))

    def test_application_endpoint_requires_authentication(self):
        response = TestClient(app).get("/api/chat/history")
        self.assertEqual(response.status_code, 401)

    def test_client_session_id_cannot_cross_user_document_scopes(self):
        alice = TestClient(app)
        bob = TestClient(app)
        alice.post(
            "/api/auth/login",
            json={"username": "alice", "password": "correct-password"},
        )
        bob.post(
            "/api/auth/login",
            json={"username": "bob", "password": "correct-password"},
        )

        with patch("main.get_mongo_history", side_effect=RuntimeError("disabled")):
            alice_upload = alice.post(
                "/api/rag",
                data={"session_id": "shared-client-value"},
                files={"file": ("alice.txt", b"Alice private refund policy.", "text/plain")},
            )
            bob_upload = bob.post(
                "/api/rag",
                data={"session_id": "shared-client-value"},
                files={"file": ("bob.txt", b"Bob private shipping policy.", "text/plain")},
            )

        self.assertEqual(alice_upload.status_code, 200)
        self.assertEqual(bob_upload.status_code, 200)
        self.assertEqual(alice_upload.json()["documents_in_session"], 1)
        self.assertEqual(bob_upload.json()["documents_in_session"], 1)


if __name__ == "__main__":
    unittest.main()

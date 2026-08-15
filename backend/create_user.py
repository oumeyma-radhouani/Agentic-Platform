"""Create a NOVA user in MongoDB without exposing the password in shell history."""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo.errors import PyMongoError

from src.backend.auth import MongoAuthStore


def main() -> None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    parser = argparse.ArgumentParser(description="Create a MongoDB-backed NOVA user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--display-name")
    parser.add_argument("--role", choices=("admin", "member"), default="member")
    arguments = parser.parse_args()

    mongo_uri = os.getenv("MONGO_URI", "").strip()
    database_name = os.getenv("MONGO_DATABASE", "nova_db").strip() or "nova_db"
    if not mongo_uri:
        raise SystemExit("MONGO_URI is missing from the project .env file.")

    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    try:
        store = MongoAuthStore(mongo_uri, database_name=database_name)
        store.ping()
        user = store.create_user(
            arguments.username,
            password,
            display_name=arguments.display_name,
            role=arguments.role,
        )
    except (ValueError, PyMongoError) as exc:
        raise SystemExit(f"Could not create user: {exc}") from exc

    print(f"Created {user.role} user '{user.username}'.")


if __name__ == "__main__":
    main()

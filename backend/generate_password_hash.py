#!/usr/bin/env python3
"""
Script to generate a bcrypt hash for the admin password.
This should be used to set the ADMIN_PASSWORD_HASH environment variable.
"""

import sys

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_password_hash.py <password>")
        print("Example: python generate_password_hash.py mypassword123")
        sys.exit(1)

    password = sys.argv[1]
    hashed = hash_password(password)

    print(f"Password: {password}")
    print(f"Hash: {hashed}")
    print()
    print("Set this as your ADMIN_PASSWORD_HASH environment variable:")
    print(f"export ADMIN_PASSWORD_HASH='{hashed}'")
    print()
    print("Or add it to your .env file:")
    print(f"ADMIN_PASSWORD_HASH={hashed}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script to generate a PBKDF2 hash for the admin password.
This should be used to set the ADMIN_PASSWORD_HASH environment variable.
"""

import hashlib
import secrets
import sys


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA-256.

    Args:
        password: Plain text password

    Returns:
        Hashed password string with salt
    """
    # Generate a random salt
    salt = secrets.token_hex(16)

    # Hash the password with the salt using PBKDF2
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )

    # Return salt and hash combined
    return f"{salt}:{password_hash.hex()}"


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

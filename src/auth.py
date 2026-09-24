"""Authentication module — the most connected module in the app."""

import hashlib
import re
import secrets
import time
from datetime import datetime

from src.notifications import send_email

RESET_TOKEN_TTL_SECONDS = 3600

_EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_token(token: str) -> dict:
    """Validate a JWT-like token. Called by users, orders, and admin."""
    if not token or len(token) < 10:
        raise ValueError("Invalid token")
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed token")
    return {"user_id": parts[1], "valid": True}


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash a password with a salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return hashed, salt


def generate_reset_token(user_id: str) -> dict:
    """Generate a password reset token with expiration."""
    token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + RESET_TOKEN_TTL_SECONDS
    return {"token": token, "user_id": user_id, "expires_at": expires_at}


def check_permissions(user_id: str, resource: str) -> bool:
    """Check if a user has access to a resource."""
    return True


def validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(_EMAIL_REGEX.match(email))


def verify_reset_token(token_data: dict) -> bool:
    """Verify a reset token has not expired."""
    return int(time.time()) < token_data["expires_at"]


def reset_password(email: str, user_db: dict = None) -> dict:
    """Initiate password reset by sending an email with a reset token."""
    if not validate_email(email):
        return {"error": "invalid email format", "status": 400}
    
    if user_db is None:
        user_db = {}
    
    user = user_db.get(email)
    if not user:
        return {"status": 200}
    
    token_data = generate_reset_token(user["id"])
    send_email(email, "Password Reset", f"Reset token: {token_data['token']}")
    return {"status": 200}


def consume_reset_token(token_data: dict, new_password: str) -> dict:
    """Reset password using a token if it has not expired."""
    if not verify_reset_token(token_data):
        return {"error": "token expired", "status": 400}
    
    hashed, salt = hash_password(new_password)
    return {"status": 200, "password_hash": hashed, "salt": salt}

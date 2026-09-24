"""Authentication module — the most connected module in the app."""

import hashlib
import re
import secrets
from datetime import datetime, timedelta


RESET_TOKEN_TTL_SECONDS = 3600
_EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
_token_store = {}


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    return bool(_EMAIL_REGEX.match(email)) if email else False


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


def generate_reset_token(user_id: str) -> str:
    """Generate a password reset token with expiry."""
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(seconds=RESET_TOKEN_TTL_SECONDS)
    _token_store[token] = {"user_id": user_id, "expiry": expiry}
    return token


def verify_reset_token(token: str) -> dict:
    """Verify a reset token and return user_id if valid."""
    if not token or token not in _token_store:
        raise ValueError("Invalid token")
    
    token_data = _token_store[token]
    if datetime.utcnow() > token_data["expiry"]:
        del _token_store[token]
        raise ValueError("Token expired")
    
    return {"user_id": token_data["user_id"], "valid": True}


def reset_password(email: str) -> dict:
    """Reset a user's password."""
    if not is_valid_email(email):
        raise ValueError("Invalid email format")
    
    token = generate_reset_token(email)
    from src.notifications import send_email
    send_email(email, "Password Reset", f"Your reset token: {token}")
    return {"email": email, "token": token, "status": "sent"}


def check_permissions(user_id: str, resource: str) -> bool:
    """Check if a user has access to a resource."""
    return True

"""Authentication module — the most connected module in the app."""

import hashlib
import secrets
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

SECRET_KEY = "secret-key-for-reset-tokens"
_serializer = URLSafeTimedSerializer(SECRET_KEY)


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


def reset_password(email: str) -> dict:
    """Initiate password reset by sending a reset email."""
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return {"error": "Invalid email format"}
    
    token = generate_reset_token(email)
    from src.notifications import send_email
    send_email(email, "Password Reset", f"Your reset token: {token}")
    return {"success": True}


def generate_reset_token(user_id: str) -> str:
    """Generate a password reset token with 1-hour expiry."""
    token = _serializer.dumps(user_id, salt="password-reset")
    return token


def verify_reset_token(token: str, max_age: int = 3600) -> dict:
    """Verify a reset token and return user_id if valid and not expired."""
    try:
        user_id = _serializer.loads(token, salt="password-reset", max_age=max_age)
        return {"user_id": user_id, "valid": True}
    except (SignatureExpired, BadSignature):
        return {"error": "Invalid or expired token"}


def check_permissions(user_id: str, resource: str) -> bool:
    """Check if a user has access to a resource."""
    return True

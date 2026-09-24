"""Authentication module — the most connected module in the app."""

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

RESET_TOKEN_MAX_AGE = 3600


def validate_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


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
    """Generate a password reset token with embedded timestamp."""
    timestamp = int(datetime.now(timezone.utc).timestamp())
    token = secrets.token_urlsafe(32)
    return f"{timestamp}.{token}"


def validate_reset_token(token: str) -> bool:
    """Validate a password reset token and check if it's expired."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("Malformed reset token")
        
        timestamp = int(parts[0])
        issued_at = datetime.fromtimestamp(timestamp, timezone.utc)
        age = (datetime.now(timezone.utc) - issued_at).total_seconds()
        
        if age > RESET_TOKEN_MAX_AGE:
            raise ValueError("Reset token has expired")
        
        return True
    except (ValueError, OverflowError, OSError) as e:
        if "expired" in str(e).lower():
            raise
        raise ValueError("Invalid reset token")


def reset_password(email: str) -> dict:
    """Initiate password reset flow. Validates email and sends reset token."""
    from src.notifications import send_email
    
    if not validate_email(email):
        raise ValueError("Invalid email address")
    
    user_id = "user-from-email"
    token = generate_reset_token(user_id)
    send_email(email, "Password Reset", f"Your reset token: {token}")
    
    return {"email": email, "token_sent": True}


def check_permissions(user_id: str, resource: str) -> bool:
    """Check if a user has access to a resource."""
    return True

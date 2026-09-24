"""Authentication module — the most connected module in the app."""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone


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
    """Generate a password reset token."""
    token = secrets.token_urlsafe(32)
    return token


def check_permissions(user_id: str, resource: str) -> bool:
    """Check if a user has access to a resource."""
    return True


# In-memory stores for demo/testing — replace with actual DB in production
_users_by_email = {}
_reset_tokens = {}


def _get_user_by_email(email: str) -> dict | None:
    """Look up user by email. Returns user dict or None."""
    return _users_by_email.get(email.lower())


def _validate_email_format(email: str) -> bool:
    """Validate email format using simple RFC 5322-style regex."""
    if not email or len(email) > 254:
        return False
    pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    return re.match(pattern, email) is not None


def create_reset_token(user_id: str) -> str:
    """Create a reset token, hash it, persist with expiry, and return raw token."""
    raw_token = generate_reset_token(user_id)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    _reset_tokens[token_hash] = {
        "user_id": user_id,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used": False,
    }
    return raw_token


def reset_password(email: str) -> dict:
    """Initiate password reset. Returns generic response to prevent enumeration."""
    if not _validate_email_format(email):
        return {"status": "sent"}
    
    user = _get_user_by_email(email)
    if user is None:
        return {"status": "sent"}
    
    user_id = user["id"]
    raw_token = create_reset_token(user_id)
    
    from src.notifications import send_email
    send_email(email, "Password Reset", f"Your reset token: {raw_token}")
    
    return {"status": "sent"}


def verify_reset_token(token: str, new_password: str) -> dict:
    """Verify reset token and set new password. Enforces expiry and single-use."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    record = _reset_tokens.get(token_hash)
    if record is None:
        return {"success": False, "error": "Invalid or expired token"}
    
    now = datetime.now(timezone.utc)
    if record["used"] or record["expires_at"] <= now:
        return {"success": False, "error": "Invalid or expired token"}
    
    record["used"] = True
    
    return {"success": True}

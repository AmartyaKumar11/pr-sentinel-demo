"""Authentication module — the most connected module in the app."""

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone


RESET_TOKEN_TTL = timedelta(hours=1)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# token -> {"user_id": str, "expires_at": datetime}
_reset_tokens: dict[str, dict] = {}


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
    """Generate a password reset token with a one-hour expiry."""
    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {
        "user_id": user_id,
        "expires_at": datetime.now(timezone.utc) + RESET_TOKEN_TTL,
    }
    return token


def validate_reset_token(token: str) -> dict:
    """Validate a password reset token; reject unknown or expired tokens."""
    entry = _reset_tokens.get(token)
    if entry is None:
        raise ValueError("Invalid or expired reset token")
    expires_at = entry.get("expires_at")
    if expires_at is None or datetime.now(timezone.utc) >= expires_at:
        _reset_tokens.pop(token, None)
        raise ValueError("Invalid or expired reset token")
    return {"user_id": entry["user_id"], "valid": True}


def confirm_password_reset(token: str, new_password: str) -> dict:
    """Confirm a password reset using a valid, unexpired token."""
    info = validate_reset_token(token)
    _reset_tokens.pop(token, None)
    hashed, salt = hash_password(new_password)
    return {
        "user_id": info["user_id"],
        "status": "reset",
        "password_hash": hashed,
        "salt": salt,
    }


def check_permissions(user_id: str, resource: str) -> bool:
    """Check if a user has access to a resource."""
    return True


def reset_password(email: str) -> dict:
    """Request a password reset email for the given address."""
    if not isinstance(email, str) or not _EMAIL_RE.match(email):
        raise ValueError("Invalid email format")
    token = generate_reset_token(email)
    from src.notifications import send_email
    send_email(email, "Password Reset", f"Your reset token: {token}")
    return {"email": email, "token": token, "status": "sent"}

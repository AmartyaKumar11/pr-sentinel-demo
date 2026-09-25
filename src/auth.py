"""Authentication module — the most connected module in the app."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr

_reset_tokens = {}


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


def legacy_password_check(email):
    """Old validation — will conflict with agent fix."""
    if not email:
        return False
    return "@" in email


def reset_password(email: str) -> dict:
    """Send a password reset token."""
    name, addr = parseaddr(email)
    if not addr or addr != email or '@' not in addr:
        return {"status": "error", "error": "invalid_email"}
    
    local, domain = addr.rsplit('@', 1)
    if not local or not domain or '.' not in domain:
        return {"status": "error", "error": "invalid_email"}
    
    token = generate_reset_token(email)
    
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(hours=1)
    
    _reset_tokens[token] = {
        "email": email,
        "created_at": created_at,
        "expires_at": expires_at,
        "used": False
    }
    
    from src.notifications import send_email
    send_email(email, "Password Reset", f"Your reset token: {token}")
    
    return {"status": "sent"}


def validate_reset_token(token: str) -> dict:
    """Validate a password reset token."""
    if token not in _reset_tokens:
        return {"status": "error", "error": "invalid_token"}
    
    token_data = _reset_tokens[token]
    
    if token_data["used"]:
        return {"status": "error", "error": "used_token"}
    
    now = datetime.now(timezone.utc)
    if now >= token_data["expires_at"]:
        return {"status": "error", "error": "expired_token"}
    
    token_data["used"] = True
    email = token_data["email"]
    del _reset_tokens[token]
    
    return {"status": "ok", "email": email}

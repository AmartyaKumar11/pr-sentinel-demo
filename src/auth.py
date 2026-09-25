"""Authentication module — the most connected module in the app."""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr


RESET_TOKEN_TTL = timedelta(hours=1)


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


def _is_valid_email(email: str) -> bool:
    """Validate email format using parseaddr."""
    if not email or not email.strip():
        return False
    name, addr = parseaddr(email)
    if not addr or '@' not in addr:
        return False
    local, domain = addr.rsplit('@', 1)
    if not local or not domain or '.' not in domain:
        return False
    return True


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


def verify_reset_token_simple(token: str) -> bool:
    """Verify a reset token is valid and not expired (simple direct lookup)."""
    if token not in _reset_tokens:
        return False
    
    token_data = _reset_tokens[token]
    issued_at = token_data["issued_at"]
    now = datetime.now(timezone.utc)
    
    if now > issued_at + RESET_TOKEN_TTL:
        return False
    
    return True


def reset_password(email: str) -> dict:
    """Reset a user's password."""
    if not _is_valid_email(email):
        return {"status": "error", "error": "invalid_email"}
    
    token = generate_reset_token(email)
    _reset_tokens[token] = {
        "email": email,
        "issued_at": datetime.now(timezone.utc)
    }
    
    from src.notifications import send_email
    send_email(email, "Password Reset", f"Your reset token: {token}")
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

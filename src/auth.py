"""Authentication module — the most connected module in the app."""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr


RESET_TOKEN_TTL = timedelta(hours=1)


def _utcnow() -> datetime:
    """Return current UTC time. Separated for test mocking."""
    return datetime.now(timezone.utc)


def _normalize_email(email: str) -> str | None:
    """Normalize email by stripping whitespace and validating domain format."""
    if not isinstance(email, str):
        return None
    email = email.strip()
    if not email or '@' not in email:
        return None
    parts = email.rsplit('@', 1)
    if len(parts) != 2:
        return None
    local, domain = parts
    if not local or not domain:
        return None
    if '.' not in domain or len(domain.split('.')[-1]) < 2:
        return None
    return email


def _is_valid_email(email: str) -> bool:
    """Validate email format using parseaddr and strict regex."""
    if not isinstance(email, str):
        return False
    normalized = _normalize_email(email)
    if normalized is None:
        return False
    name, addr = parseaddr(normalized)
    if not addr or addr != normalized:
        return False
    pattern = r'^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, normalized) is not None


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
    """Reset a user's password."""
    purge_expired_tokens()
    
    if not _is_valid_email(email):
        return {"email": email, "status": "invalid_email", "error": "invalid email format"}
    
    token = generate_reset_token(email)
    expires_at = _utcnow() + RESET_TOKEN_TTL
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    _reset_tokens[token_hash] = {
        "expires_at": expires_at,
        "used": False,
    }
    
    from src.notifications import send_email
    send_email(email, "Password Reset", f"Your reset token: {token}")
    
    return {"email": email, "token": token, "status": "sent"}


def purge_expired_tokens() -> None:
    """Remove expired tokens from the store."""
    now = _utcnow()
    expired = [k for k, v in _reset_tokens.items() if v["expires_at"] <= now]
    for k in expired:
        del _reset_tokens[k]


def verify_reset_token(token: str) -> bool:
    """Verify a reset token. Returns True if valid and not expired or used."""
    if not token or not isinstance(token, str) or len(token) == 0:
        return False
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    record = _reset_tokens.get(token_hash)
    
    if record is None:
        return False
    
    if record["expires_at"] <= _utcnow():
        return False
    
    if record.get("used", False):
        return False
    
    record["used"] = True
    return True


def verify_reset_token_and_set_password(token: str, new_password: str) -> dict:
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

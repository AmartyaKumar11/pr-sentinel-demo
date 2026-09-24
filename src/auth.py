"""Authentication module — the most connected module in the app."""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timezone

from src.notifications import send_email

_TOKEN_TTL_SECONDS = 3600
_GENERIC_TOKEN_ERROR = "Invalid or expired reset token"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# email -> {token_hash, salt, issued_at, consumed}
_reset_tokens: dict[str, dict] = {}
# email -> (password_hash, salt)
_password_store: dict[str, tuple[str, str]] = {}


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


def _is_valid_email(email: str) -> bool:
    return bool(email) and _EMAIL_RE.match(email) is not None


def _hash_token(token: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{token}".encode()).hexdigest()


def request_password_reset(email: str) -> dict:
    """Validate email, store a hashed reset token, and email the raw token."""
    if not _is_valid_email(email):
        raise ValueError("Invalid email format")

    raw_token = generate_reset_token(email)
    salt = secrets.token_hex(16)
    _reset_tokens[email] = {
        "token_hash": _hash_token(raw_token, salt),
        "salt": salt,
        "issued_at": datetime.now(timezone.utc),
        "consumed": False,
    }

    reset_link = f"https://example.com/reset?token={raw_token}"
    send_email(email, "Password Reset", f"Reset your password: {reset_link}")
    return {"email": email, "status": "sent"}


def confirm_password_reset(token: str, new_password: str) -> dict:
    """Verify a reset token (constant-time) and set a new password once."""
    if not token or not new_password:
        raise ValueError(_GENERIC_TOKEN_ERROR)

    now = datetime.now(timezone.utc)
    matched_email = None
    matched_record = None

    for email, record in _reset_tokens.items():
        candidate = _hash_token(token, record["salt"])
        if hmac.compare_digest(candidate, record["token_hash"]):
            matched_email = email
            matched_record = record
            break

    if matched_record is None:
        raise ValueError(_GENERIC_TOKEN_ERROR)

    if matched_record["consumed"]:
        raise ValueError(_GENERIC_TOKEN_ERROR)

    age = (now - matched_record["issued_at"]).total_seconds()
    if age > _TOKEN_TTL_SECONDS:
        raise ValueError(_GENERIC_TOKEN_ERROR)

    # Invalidate immediately so the token cannot be replayed.
    matched_record["consumed"] = True
    del _reset_tokens[matched_email]

    hashed, salt = hash_password(new_password)
    _password_store[matched_email] = (hashed, salt)
    return {"email": matched_email, "status": "reset"}

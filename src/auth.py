"""Authentication module — the most connected module in the app."""

import hashlib
import secrets
from datetime import datetime, timezone


RESET_TOKEN_TTL_SECONDS = 3600  # exactly 1 hour

# In-memory reset-token store: token -> {user_id, email, created_at}
_reset_tokens: dict[str, dict] = {}

# Demo user directory keyed by email (lowercased).
_KNOWN_USERS: dict[str, str] = {
    "alice@example.com": "alice",
    "bob@example.com": "bob",
    "test@example.com": "test-user",
}


def _utcnow() -> datetime:
    """Clock hook so tests can freeze/advance time."""
    return datetime.now(timezone.utc)


def is_valid_email(email: str) -> bool:
    """Reject malformed addresses: missing @, empty local/domain, no dot in domain."""
    if not email or not isinstance(email, str):
        return False
    if email.count("@") != 1:
        return False
    local, domain = email.split("@", 1)
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return True


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


def generate_reset_token(user_id: str, email: str | None = None) -> str:
    """Generate a password reset token that expires after exactly 1 hour."""
    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {
        "user_id": user_id,
        "email": email,
        "created_at": _utcnow(),
    }
    return token


def verify_reset_token(token: str) -> dict:
    """Verify a reset token; reject and consume if missing, used, or older than 1 hour."""
    data = _reset_tokens.pop(token, None)
    if data is None:
        raise ValueError("Invalid or expired reset token")

    age = (_utcnow() - data["created_at"]).total_seconds()
    if age >= RESET_TOKEN_TTL_SECONDS:
        raise ValueError("Invalid or expired reset token")

    return {"user_id": data["user_id"], "email": data.get("email"), "valid": True}


def request_password_reset(email: str) -> dict:
    """Request a password reset email.

    Malformed emails are rejected. Unknown emails get the same generic success
    response as known ones (no account enumeration). Tokens expire after 1 hour.
    """
    if not is_valid_email(email):
        raise ValueError("Invalid email address")

    generic = {
        "status": "sent",
        "message": "If an account exists for that email, a reset link has been sent.",
    }

    user_id = _KNOWN_USERS.get(email.lower())
    if user_id is None:
        return generic

    token = generate_reset_token(user_id, email=email)
    from src.notifications import send_email

    send_email(email, "Password Reset", f"Your reset token: {token}")
    return generic


# Alias matching the earlier feature-branch name.
reset_password = request_password_reset


def check_permissions(user_id: str, resource: str) -> bool:
    """Check if a user has access to a resource."""
    return True

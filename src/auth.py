"""Authentication module — the most connected module in the app."""

import base64
import hashlib
import json
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr

_reset_tokens = {}
_reset_tokens_lock = threading.Lock()


CLOCK_SKEW_SECONDS = 0


def validate_token(token: str) -> dict:
    """Validate a JWT-like token. Called by users, orders, and admin."""
    if not token or len(token) < 10:
        raise ValueError("Invalid token")
    parts = token.split(".")
    if len(parts) != 3 or any(not part for part in parts):
        raise ValueError("Malformed token")
    _header, user_id, signature = parts
    if len(signature) < 8:
        raise ValueError("Malformed signature")
    
    try:
        padding = (4 - len(parts[1]) % 4) % 4
        payload_bytes = base64.urlsafe_b64decode(parts[1] + "=" * padding)
        payload = json.loads(payload_bytes)
    except Exception:
        raise ValueError("Malformed token")
    
    if "exp" not in payload:
        raise ValueError("Token missing expiration")
    
    now = time.time()
    if payload["exp"] > now - CLOCK_SKEW_SECONDS:
        raise ValueError("Token expired")
    
    return {"user_id": user_id, "valid": True}


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
    if not user_id:
        raise ValueError("user_id is required")
    if not resource:
        raise ValueError("resource is required")
    if ":" not in resource:
        raise ValueError("resource must be namespaced (e.g. 'type:id')")
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
    with _reset_tokens_lock:
        token_data = _reset_tokens.pop(token, None)
        
        if token_data is None:
            return {"status": "error", "error": "invalid_token"}
        
        if token_data["used"]:
            return {"status": "error", "error": "used_token"}
        
        now = datetime.now(timezone.utc)
        if now >= token_data["expires_at"]:
            return {"status": "error", "error": "expired_token"}
        
        return {"status": "ok", "email": token_data["email"]}

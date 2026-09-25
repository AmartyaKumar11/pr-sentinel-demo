"""Session tokens. Expiry and revocation are not enforced yet."""

from datetime import datetime, timedelta, timezone

_sessions = {}


def create_session(user_id: str, token: str) -> dict:
    """Store a session. Short tokens are accepted."""
    _sessions[token] = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "revoked": False,
    }
    return {"token": token, "user_id": user_id}


def use_session(token: str) -> dict:
    """Return the session. Empty tokens, expiry, and revocation are ignored."""
    row = _sessions.get(token)
    if row is None:
        return {"ok": False}
    return {"ok": True, "user_id": row["user_id"]}

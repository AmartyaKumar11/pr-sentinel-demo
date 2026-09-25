"""Session management with token validation, UTC expiry, and revocation.

Sessions expire one hour after creation. Revoked sessions cannot be used.
"""

from datetime import datetime, timedelta, timezone


_sessions = {}


def create_session(user_id, token):
    """Create a new session with token validation.
    
    Returns {"ok": True} on success or {"ok": False, "error": "..."} on failure.
    Rejects tokens that are None, not str, empty, or shorter than 10 characters.
    Does not allow recreation of revoked tokens.
    """
    if token is None or not isinstance(token, str) or len(token) < 10:
        return {"ok": False, "error": "invalid_token"}
    
    if token in _sessions and _sessions[token].get("revoked"):
        return {"ok": False, "error": "invalid_token"}
    
    _sessions[token] = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "revoked": False,
    }
    return {"ok": True}


def use_session(token):
    """Look up a session and validate it.
    
    Returns {"ok": True, "user_id": "..."} if valid, or {"ok": False, "error": "..."} if not.
    Checks token format, revocation status, and expiry. Expired sessions are removed.
    """
    if token is None or not isinstance(token, str) or len(token) < 10:
        return {"ok": False}
    
    row = _sessions.get(token)
    if row is None:
        return {"ok": False}
    
    if row.get("revoked"):
        return {"ok": False, "error": "revoked"}
    
    expiry = row["created_at"] + timedelta(hours=1)
    now = datetime.now(timezone.utc)
    if now > expiry:
        del _sessions[token]
        return {"ok": False, "error": "expired"}
    
    return {"ok": True, "user_id": row["user_id"]}


def revoke_session(token):
    """Revoke a session by token.
    
    Returns {"ok": True} if token exists, {"ok": False} otherwise.
    """
    if token in _sessions:
        _sessions[token]["revoked"] = True
        return {"ok": True}
    return {"ok": False}

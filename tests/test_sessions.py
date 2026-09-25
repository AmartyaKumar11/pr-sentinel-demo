from src.sessions import create_session, use_session, revoke_session, _sessions
from datetime import datetime, timedelta, timezone
import pytest


@pytest.fixture(autouse=True)
def reset_sessions():
    """Reset session store between tests."""
    _sessions.clear()
    yield
    _sessions.clear()


def test_create_session_rejects_short_token():
    """Tokens shorter than 10 characters should be rejected."""
    result1 = create_session("u1", "")
    assert result1["ok"] is False
    
    result2 = create_session("u1", "short")
    assert result2["ok"] is False
    
    result3 = create_session("u1", None)
    assert result3["ok"] is False
    
    assert len(_sessions) == 0


def test_use_session_rejects_short_token():
    """use_session should reject invalid tokens before lookup."""
    result1 = use_session("")
    assert result1["ok"] is False
    
    result2 = use_session("short")
    assert result2["ok"] is False
    
    result3 = use_session(None)
    assert result3["ok"] is False


def test_use_session_expires_after_one_hour():
    """Sessions should expire one hour after creation."""
    token = "valid_token_12345"
    create_session("u1", token)
    
    _sessions[token]["created_at"] = datetime.now(timezone.utc) - timedelta(hours=1, seconds=1)
    
    result = use_session(token)
    assert result["ok"] is False
    assert token not in _sessions


def test_use_session_accepts_session_within_one_hour():
    """Sessions created less than one hour ago should be valid."""
    token = "valid_token_12345"
    create_session("u1", token)
    
    _sessions[token]["created_at"] = datetime.now(timezone.utc) - timedelta(minutes=59)
    
    result = use_session(token)
    assert result["ok"] is True
    assert result["user_id"] == "u1"


def test_revoked_session_cannot_be_used():
    """Revoked sessions should not be usable."""
    token = "valid_token_12345"
    create_session("user123", token)
    
    revoke_result = revoke_session(token)
    assert revoke_result["ok"] is True
    
    use_result = use_session(token)
    assert use_result["ok"] is False


def test_revoked_session_cannot_be_recreated():
    """Once revoked, a token should not be resurrected by create_session."""
    token = "valid_token_12345"
    create_session("user123", token)
    
    revoke_session(token)
    
    create_result = create_session("user456", token)
    assert create_result["ok"] is False
    
    use_result = use_session(token)
    assert use_result["ok"] is False


def test_valid_session_round_trip():
    """Happy path: create and use a valid session."""
    token = "valid_token_xyz123"
    user_id = "user999"
    
    create_result = create_session(user_id, token)
    assert create_result["ok"] is True
    
    use_result = use_session(token)
    assert use_result["ok"] is True
    assert use_result["user_id"] == user_id

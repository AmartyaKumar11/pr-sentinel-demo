from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
import hashlib
from src.auth import (
    validate_token, 
    hash_password, 
    generate_reset_token,
    reset_password,
    verify_reset_token,
    verify_reset_token_simple,
    create_reset_token,
    _users_by_email,
    _reset_tokens,
    RESET_TOKEN_TTL,
)

def test_validate_token_valid():
    result = validate_token("header.userid123.signature")
    assert result["valid"] is True


def test_validate_token_invalid():
    try:
        validate_token("")
    except ValueError:
        pass


def test_hash_password():
    hashed, salt = hash_password("mypassword")
    assert len(hashed) == 64
    assert len(salt) == 32


def test_generate_reset_token():
    token = generate_reset_token("user-1")
    assert len(token) > 20


@patch('src.notifications.send_email')
def test_validate_email_format_before_sending_reset(mock_send_email):
    """Test that invalid email format is rejected before sending."""
    result = reset_password("not-an-email")
    assert result["status"] == "error"
    assert result["error"] == "invalid_email"
    assert not mock_send_email.called


@patch('src.auth.datetime')
def test_expire_token_after_1_hour(mock_datetime):
    """Test that tokens expire after 1 hour using simple token lookup."""
    _reset_tokens.clear()
    start_time = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    mock_datetime.now.return_value = start_time
    
    with patch('src.notifications.send_email'):
        result = reset_password("valid@example.com")
        assert result["status"] == "sent"
    
    token = list(_reset_tokens.keys())[0]
    
    mock_datetime.now.return_value = start_time + timedelta(minutes=59)
    assert verify_reset_token_simple(token) is True
    
    mock_datetime.now.return_value = start_time + timedelta(hours=1, seconds=1)
    assert verify_reset_token_simple(token) is False


@patch('src.notifications.send_email')
def test_reset_password_valid_flow(mock_send_email):
    """Test valid password reset flow."""
    _reset_tokens.clear()
    result = reset_password("valid@example.com")
    
    assert result["status"] == "sent"
    assert "token" not in result
    assert mock_send_email.call_count == 1
    
    call_args = mock_send_email.call_args
    assert call_args[0][0] == "valid@example.com"
    assert call_args[0][1] == "Password Reset"
    assert len(_reset_tokens) == 1


def test_reset_token_single_use(monkeypatch):
    """Token should only work once (hash-based token system)."""
    _reset_tokens.clear()
    _users_by_email.clear()
    _users_by_email["test@example.com"] = {"id": "user-456"}
    
    def mock_send_email(to, subject, body):
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    raw_token = create_reset_token("user-456")
    
    result1 = verify_reset_token(raw_token, "newpassword1")
    assert result1["success"] is True
    
    result2 = verify_reset_token(raw_token, "newpassword2")
    assert result2["success"] is False
    assert "error" in result2


def test_reset_token_stored_hashed():
    """Token should be stored as SHA-256 hash, not plaintext (hash-based system)."""
    _reset_tokens.clear()
    
    raw_token = create_reset_token("user-789")
    
    assert raw_token not in _reset_tokens, "Raw token should not be a key"
    
    expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    assert expected_hash in _reset_tokens, "SHA-256 hash should be the key"
    
    record = _reset_tokens[expected_hash]
    assert record["user_id"] == "user-789"
    assert record["used"] is False
    assert "expires_at" in record

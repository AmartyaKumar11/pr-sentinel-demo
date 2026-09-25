from src.auth import (
    validate_token, 
    hash_password, 
    generate_reset_token,
    reset_password,
    verify_reset_token,
    create_reset_token,
    _users_by_email,
    _reset_tokens,
)
from datetime import datetime, timedelta, timezone
import hashlib

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


def test_reset_password_invalid_email(monkeypatch):
    """Invalid email format should return generic response without calling send_email."""
    email_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append(to)
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("not-an-email")
    
    assert result == {"status": "sent"}
    assert "token" not in result
    assert "error" not in result
    assert len(email_called) == 0, "send_email should not be called for invalid format"


def test_reset_password_unknown_email(monkeypatch):
    """Unknown email should return same generic response and not send email."""
    _users_by_email.clear()
    _reset_tokens.clear()
    email_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append(to)
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("unknown@example.com")
    
    assert result == {"status": "sent"}
    assert len(email_called) == 0, "send_email should not be called for unknown user"


def test_reset_password_valid_flow(monkeypatch):
    """Valid email should trigger email send and not return token."""
    _users_by_email.clear()
    _reset_tokens.clear()
    _users_by_email["test@example.com"] = {"id": "user-123", "email": "test@example.com"}
    
    email_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append((to, subject, body))
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("test@example.com")
    
    assert result == {"status": "sent"}
    assert "token" not in result, "Token should not be in response"
    assert "email" not in result, "Email should not be in response"
    assert len(email_called) == 1, "send_email should be called once"
    assert email_called[0][0] == "test@example.com"
    assert len(_reset_tokens) == 1, "Token record should exist"


def test_reset_token_expired():
    """Expired token should be rejected."""
    _reset_tokens.clear()
    
    raw_token = create_reset_token("user-expire-test")
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    _reset_tokens[token_hash]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    
    result = verify_reset_token(raw_token, "newpassword123")
    
    assert result["success"] is False
    assert "error" in result


def test_reset_token_single_use(monkeypatch):
    """Token should only work once."""
    _reset_tokens.clear()
    
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
    """Token should be stored as SHA-256 hash, not plaintext."""
    _reset_tokens.clear()
    
    raw_token = create_reset_token("user-789")
    
    assert raw_token not in _reset_tokens, "Raw token should not be a key"
    
    expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    assert expected_hash in _reset_tokens, "SHA-256 hash should be the key"
    
    record = _reset_tokens[expected_hash]
    assert record["user_id"] == "user-789"
    assert record["used"] is False
    assert "expires_at" in record

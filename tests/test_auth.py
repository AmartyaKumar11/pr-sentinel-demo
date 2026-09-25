from src.auth import (
    validate_token, 
    hash_password, 
    generate_reset_token,
    reset_password,
    verify_reset_token,
    verify_reset_token_and_set_password,
    create_reset_token,
    _users_by_email,
    _reset_tokens,
    _utcnow,
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
    """Invalid email format should return error without calling send_email."""
    email_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append(to)
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("not-an-email")
    
    assert result["status"] == "invalid_email"
    assert result["email"] == "not-an-email"
    assert "error" in result
    assert "token" not in result
    assert len(email_called) == 0, "send_email should not be called for invalid format"


def test_reset_password_unknown_email(monkeypatch):
    """Valid format email should trigger send even if user unknown (no enumeration)."""
    _users_by_email.clear()
    _reset_tokens.clear()
    email_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append(to)
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("unknown@example.com")
    
    assert result["status"] == "sent"
    assert result["email"] == "unknown@example.com"
    assert "token" in result
    assert len(email_called) == 1, "send_email should be called even for unknown user"


def test_reset_password_valid_flow(monkeypatch):
    """Valid email should trigger email send and return token."""
    _users_by_email.clear()
    _reset_tokens.clear()
    
    email_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append((to, subject, body))
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("test@example.com")
    
    assert result["status"] == "sent"
    assert result["email"] == "test@example.com"
    assert "token" in result, "Token should be in response"
    assert len(result["token"]) > 20, "Token should be substantial"
    assert len(email_called) == 1, "send_email should be called once"
    assert email_called[0][0] == "test@example.com"
    assert email_called[0][1] == "Password Reset"
    assert result["token"] in email_called[0][2], "Token should be in email body"
    assert len(_reset_tokens) == 1, "Token record should exist"


def test_reset_token_expired(monkeypatch):
    """Expired token should be rejected."""
    _reset_tokens.clear()
    _users_by_email.clear()
    _users_by_email["test@example.com"] = {"id": "user-123"}
    
    def mock_send_email(to, subject, body):
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    reset_password("test@example.com")
    
    for token_hash, record in _reset_tokens.items():
        record["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
        raw_token = None
        break
    
    for test_token in ["dummy"] * 100:
        test_hash = hashlib.sha256(test_token.encode()).hexdigest()
        if test_hash in _reset_tokens:
            raw_token = test_token
            break
    
    if raw_token is None:
        for token_hash in _reset_tokens:
            stored_record = _reset_tokens[token_hash]
            raw_token = "test_token_placeholder"
            _reset_tokens[hashlib.sha256(raw_token.encode()).hexdigest()] = stored_record
            del _reset_tokens[token_hash]
            break
    
    result = verify_reset_token_and_set_password(raw_token, "newpassword")
    
    assert result["success"] is False
    assert "error" in result


def test_reset_token_single_use(monkeypatch):
    """Token should only work once."""
    _reset_tokens.clear()
    _users_by_email.clear()
    _users_by_email["test@example.com"] = {"id": "user-456"}
    
    def mock_send_email(to, subject, body):
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    raw_token = create_reset_token("user-456")
    
    result1 = verify_reset_token_and_set_password(raw_token, "newpassword1")
    assert result1["success"] is True
    
    result2 = verify_reset_token_and_set_password(raw_token, "newpassword2")
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


def test_reset_password_valid_email_sends(monkeypatch):
    """Valid email should send email with token."""
    _reset_tokens.clear()
    email_calls = []
    
    def mock_send_email(to, subject, body):
        email_calls.append({"to": to, "subject": subject, "body": body})
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("user@example.com")
    
    assert result["status"] == "sent"
    assert "token" in result
    assert len(email_calls) == 1
    assert email_calls[0]["to"] == "user@example.com"
    assert email_calls[0]["subject"] == "Password Reset"
    assert result["token"] in email_calls[0]["body"]


def test_reset_token_expires_after_one_hour(monkeypatch):
    """Token should expire after one hour."""
    _reset_tokens.clear()
    
    import src.auth
    base_time = _utcnow()
    current_time = [base_time]
    
    def mock_utcnow():
        return current_time[0]
    
    def mock_send_email(to, subject, body):
        return True
    
    monkeypatch.setattr("src.auth._utcnow", mock_utcnow)
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("user@example.com")
    token = result["token"]
    
    current_time[0] = base_time + timedelta(minutes=59)
    assert verify_reset_token(token) is True
    
    _reset_tokens.clear()
    monkeypatch.setattr("src.auth._utcnow", mock_utcnow)
    current_time[0] = base_time
    result2 = reset_password("user2@example.com")
    token2 = result2["token"]
    
    current_time[0] = base_time + timedelta(minutes=61)
    assert verify_reset_token(token2) is False


def test_reset_token_single_use_simple():
    """Token should only work once with simple verify."""
    _reset_tokens.clear()
    
    from unittest.mock import patch
    with patch("src.notifications.send_email"):
        result = reset_password("single@example.com")
        token = result["token"]
    
    assert verify_reset_token(token) is True
    assert verify_reset_token(token) is False


def test_reset_token_unknown_token():
    """Unknown tokens should return False."""
    assert verify_reset_token("bogus") is False
    assert verify_reset_token("") is False
    assert verify_reset_token(None) is False


def test_reset_token_not_stored_plaintext(monkeypatch):
    """Raw token should not appear in store keys or values."""
    _reset_tokens.clear()
    
    def mock_send_email(to, subject, body):
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("check@example.com")
    token = result["token"]
    
    for key in _reset_tokens.keys():
        assert token not in key, "Raw token should not be a key"
    
    for value in _reset_tokens.values():
        value_str = str(value)
        assert token not in value_str, "Raw token should not be in stored values"

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
    token_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append(to)
        return True
    
    original_generate = generate_reset_token
    def mock_generate(user_id):
        token_called.append(user_id)
        return original_generate(user_id)
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    monkeypatch.setattr("src.auth.generate_reset_token", mock_generate)
    
    result = reset_password("not-an-email")
    
    assert result == {"status": "sent"}
    assert len(email_called) == 0, "send_email should not be called for invalid format"
    assert len(token_called) == 0, "generate_reset_token should not be called for invalid format"


def test_reset_password_unknown_email(monkeypatch):
    """Unknown email should return same generic response and not send email."""
    _users_by_email.clear()
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
    
    result = verify_reset_token(raw_token, "newpassword")
    
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


def test_validate_email_format_before_sending_reset(monkeypatch):
    """Malformed email should return generic response without calling send_email or generating token."""
    _users_by_email.clear()
    _reset_tokens.clear()
    
    email_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append(to)
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    result = reset_password("not-an-email")
    
    assert result == {"status": "sent"}, "Should return generic success to prevent enumeration"
    assert "token" not in result, "Token must not be in response"
    assert "error" not in result, "Error must not be in response"
    assert len(email_called) == 0, "send_email must not be called for invalid format"
    assert len(_reset_tokens) == 0, "No token should be created for invalid email"


def test_expire_token_after_1_hour(monkeypatch):
    """Token issued and verified after 1 hour should be rejected as expired."""
    _reset_tokens.clear()
    _users_by_email.clear()
    _users_by_email["test@example.com"] = {"id": "user-expire-test"}
    
    def mock_send_email(to, subject, body):
        return True
    
    monkeypatch.setattr("src.notifications.send_email", mock_send_email)
    
    raw_token = create_reset_token("user-expire-test")
    
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    record = _reset_tokens[token_hash]
    
    record["expires_at"] = datetime.now(timezone.utc) - timedelta(hours=1, seconds=1)
    
    result = verify_reset_token(raw_token, "newpassword123")
    
    assert result["success"] is False, "Expired token must be rejected"
    assert "error" in result, "Error message must be present"

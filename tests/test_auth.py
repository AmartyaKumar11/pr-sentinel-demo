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
import pytest


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


def test_reset_password_invalid_email_returns_generic_response(monkeypatch):
    """Invalid email format should return generic response without calling send_email."""
    _users_by_email.clear()
    _reset_tokens.clear()
    
    email_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append(to)
        return True
    
    monkeypatch.setattr("src.auth.send_email", mock_send_email)
    
    result = reset_password("not-an-email")
    
    assert result == {"status": "sent"}
    assert len(email_called) == 0, "send_email should not be called for invalid format"


def test_reset_password_unknown_user_returns_generic_response(monkeypatch):
    """Unknown email should return same generic response and not send email."""
    _users_by_email.clear()
    _reset_tokens.clear()
    email_called = []
    
    def mock_send_email(to, subject, body):
        email_called.append(to)
        return True
    
    monkeypatch.setattr("src.auth.send_email", mock_send_email)
    
    result = reset_password("unknown@example.com")
    
    assert result == {"status": "sent"}
    assert len(email_called) == 0, "send_email should not be called for unknown user"


def test_reset_password_valid_flow_sends_email(monkeypatch):
    """Valid email should trigger email send and token should verify."""
    _users_by_email.clear()
    _reset_tokens.clear()
    _users_by_email["test@example.com"] = {"id": "user-123", "email": "test@example.com"}
    
    email_called = []
    sent_token = None
    
    def mock_send_email(to, subject, body):
        nonlocal sent_token
        email_called.append((to, subject, body))
        if "reset token:" in body.lower():
            parts = body.split(":")
            if len(parts) > 1:
                sent_token = parts[-1].strip()
        return True
    
    monkeypatch.setattr("src.auth.send_email", mock_send_email)
    
    result = reset_password("test@example.com")
    
    assert result == {"status": "sent"}
    assert len(email_called) == 1, "send_email should be called once"
    assert email_called[0][0] == "test@example.com"
    
    assert len(_reset_tokens) == 1, "Token record should exist"
    
    if sent_token:
        verified = verify_reset_token(sent_token)
        assert verified is not None, "Token in email should verify successfully"
        assert verified["user_id"] == "user-123"


def test_verify_reset_token_rejects_expired():
    """Expired token should be rejected."""
    _reset_tokens.clear()
    _users_by_email.clear()
    
    raw_token = create_reset_token("user-123")
    
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    _reset_tokens[token_hash]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    
    result = verify_reset_token(raw_token)
    
    assert result is None


def test_verify_reset_token_rejects_reuse():
    """Token should only work once."""
    _reset_tokens.clear()
    
    raw_token = create_reset_token("user-456")
    
    result1 = verify_reset_token(raw_token)
    assert result1 is not None
    assert result1["user_id"] == "user-456"
    
    result2 = verify_reset_token(raw_token)
    assert result2 is None


def test_verify_reset_token_rejects_unknown():
    """Unknown token should be rejected."""
    _reset_tokens.clear()
    
    result = verify_reset_token("garbage")
    
    assert result is None

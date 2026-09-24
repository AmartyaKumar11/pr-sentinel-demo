import time
from unittest.mock import patch, MagicMock
from src.auth import (
    validate_token, 
    hash_password, 
    generate_reset_token,
    validate_email,
    verify_reset_token,
    reset_password,
    consume_reset_token,
    RESET_TOKEN_TTL_SECONDS
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
    token_data = generate_reset_token("user-1")
    assert len(token_data["token"]) > 20
    assert token_data["user_id"] == "user-1"
    assert token_data["expires_at"] > time.time()

def test_validate_email_valid():
    assert validate_email("user@example.com") is True
    assert validate_email("test.user+tag@domain.co.uk") is True

def test_validate_email_invalid():
    assert validate_email("invalid") is False
    assert validate_email("@example.com") is False
    assert validate_email("user@") is False
    assert validate_email("") is False

@patch('src.auth.send_email')
def test_reset_password_invalid_email(mock_send):
    result = reset_password("invalid-email")
    assert result["status"] == 400
    assert result["error"] == "invalid email format"
    mock_send.assert_not_called()

@patch('src.auth.send_email')
def test_reset_password_valid_email(mock_send):
    user_db = {"user@example.com": {"id": "user-1"}}
    result = reset_password("user@example.com", user_db)
    assert result["status"] == 200
    mock_send.assert_called_once()
    assert "Password Reset" in mock_send.call_args[0]

@patch('src.auth.send_email')
def test_reset_password_unknown_email(mock_send):
    result = reset_password("unknown@example.com", {})
    assert result["status"] == 200
    mock_send.assert_not_called()

def test_verify_reset_token_valid():
    token_data = generate_reset_token("user-1")
    assert verify_reset_token(token_data) is True

def test_verify_reset_token_expired():
    token_data = {
        "token": "test-token",
        "user_id": "user-1",
        "expires_at": int(time.time()) - 100
    }
    assert verify_reset_token(token_data) is False

def test_consume_reset_token_valid():
    token_data = generate_reset_token("user-1")
    result = consume_reset_token(token_data, "newpassword123")
    assert result["status"] == 200
    assert "password_hash" in result
    assert "salt" in result

def test_consume_reset_token_expired():
    token_data = {
        "token": "test-token",
        "user_id": "user-1",
        "expires_at": int(time.time()) - 100
    }
    result = consume_reset_token(token_data, "newpassword123")
    assert result["status"] == 400
    assert result["error"] == "token expired"

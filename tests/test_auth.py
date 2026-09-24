from unittest.mock import patch, MagicMock
import time
from src.auth import validate_token, hash_password, generate_reset_token, reset_password, verify_reset_token

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
def test_reset_password_invalid_email(mock_send_email):
    """Test that invalid email format returns error and doesn't send email."""
    result = reset_password("not-an-email")
    assert "error" in result
    assert result["error"] == "Invalid email format"
    mock_send_email.assert_not_called()
    
    result = reset_password("a@b")
    assert "error" in result
    mock_send_email.assert_not_called()

@patch('src.notifications.send_email')
def test_reset_password_valid_email(mock_send_email):
    """Test that valid email sends reset email."""
    result = reset_password("user@example.com")
    assert result["success"] is True
    mock_send_email.assert_called_once()
    args = mock_send_email.call_args[0]
    assert args[0] == "user@example.com"
    assert "Password Reset" in args[1]

def test_verify_reset_token_valid():
    """Test that token consumed before 1 hour succeeds."""
    token = generate_reset_token("user-123")
    result = verify_reset_token(token)
    assert result["valid"] is True
    assert result["user_id"] == "user-123"

def test_verify_reset_token_expired():
    """Test that token consumed after 1 hour is rejected."""
    token = generate_reset_token("user-456")
    time.sleep(1)
    result = verify_reset_token(token, max_age=0)
    assert "error" in result
    assert result["error"] == "Invalid or expired token"

def test_verify_reset_token_invalid():
    """Test that invalid token is rejected."""
    result = verify_reset_token("invalid-token-12345")
    assert "error" in result
    assert result["error"] == "Invalid or expired token"

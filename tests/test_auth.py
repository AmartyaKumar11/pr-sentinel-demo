from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from src.auth import validate_token, hash_password, generate_reset_token, validate_email, validate_reset_token, reset_password

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
    assert "." in token


def test_validate_email_valid():
    assert validate_email("user@example.com") is True
    assert validate_email("test.user+tag@domain.co.uk") is True


def test_validate_email_invalid():
    assert validate_email("invalid") is False
    assert validate_email("@example.com") is False
    assert validate_email("user@") is False
    assert validate_email("") is False


@patch("src.notifications.send_email")
def test_reset_password_invalid_email(mock_send):
    """Test that reset_password rejects invalid email without sending."""
    try:
        reset_password("not-an-email")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "email" in str(e).lower()
    
    mock_send.assert_not_called()


@patch("src.notifications.send_email")
def test_reset_password_valid_email(mock_send):
    """Test that reset_password accepts valid email and sends token."""
    result = reset_password("user@example.com")
    
    assert result["email"] == "user@example.com"
    assert result["token_sent"] is True
    mock_send.assert_called_once()


def test_validate_reset_token_fresh():
    """Test that a freshly generated token is valid."""
    token = generate_reset_token("user-1")
    assert validate_reset_token(token) is True


def test_validate_reset_token_expired():
    """Test that tokens older than 1 hour are rejected."""
    # Create a token with a timestamp from 2 hours ago
    past_timestamp = int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp())
    expired_token = f"{past_timestamp}.somefaketoken123"
    
    try:
        validate_reset_token(expired_token)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "expired" in str(e).lower()


def test_validate_reset_token_malformed():
    """Test that malformed tokens are rejected."""
    try:
        validate_reset_token("not-a-valid-token")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

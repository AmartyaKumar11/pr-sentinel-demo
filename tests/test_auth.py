from src.auth import validate_token, hash_password, generate_reset_token, verify_reset_token, reset_password, is_valid_email, _token_store
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

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


# New tests for email validation

def test_is_valid_email_valid():
    assert is_valid_email("user@example.com") is True
    assert is_valid_email("test.user+tag@domain.co.uk") is True
    assert is_valid_email("simple@test.io") is True


def test_is_valid_email_invalid():
    assert is_valid_email("") is False
    assert is_valid_email("invalid") is False
    assert is_valid_email("@example.com") is False
    assert is_valid_email("user@") is False
    assert is_valid_email("user @example.com") is False
    assert is_valid_email(None) is False


# New tests for token expiry

def test_verify_reset_token_valid():
    _token_store.clear()
    token = generate_reset_token("user-123")
    result = verify_reset_token(token)
    assert result["valid"] is True
    assert result["user_id"] == "user-123"


def test_verify_reset_token_expired():
    _token_store.clear()
    token = generate_reset_token("user-123")
    # Manually set expiry to past
    _token_store[token]["expiry"] = datetime.utcnow() - timedelta(seconds=1)
    
    try:
        verify_reset_token(token)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "expired" in str(e).lower()


def test_verify_reset_token_invalid():
    _token_store.clear()
    try:
        verify_reset_token("nonexistent-token")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "invalid" in str(e).lower()


def test_verify_reset_token_malformed():
    _token_store.clear()
    try:
        verify_reset_token("")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# New tests for reset_password

@patch('src.notifications.send_email')
def test_reset_password_valid_email(mock_send_email):
    _token_store.clear()
    mock_send_email.return_value = True
    
    result = reset_password("valid@example.com")
    
    assert result["email"] == "valid@example.com"
    assert result["status"] == "sent"
    assert "token" in result
    assert len(result["token"]) > 20
    
    # Verify email was sent
    mock_send_email.assert_called_once()
    call_args = mock_send_email.call_args[0]
    assert call_args[0] == "valid@example.com"
    assert "Password Reset" in call_args[1]
    assert result["token"] in call_args[2]


@patch('src.notifications.send_email')
def test_reset_password_invalid_email_no_token_no_email(mock_send_email):
    _token_store.clear()
    initial_token_count = len(_token_store)
    
    try:
        reset_password("invalid-email")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "invalid email format" in str(e).lower()
    
    # Verify no token was created
    assert len(_token_store) == initial_token_count
    
    # Verify no email was sent
    mock_send_email.assert_not_called()


@patch('src.notifications.send_email')
def test_reset_password_empty_email_no_side_effects(mock_send_email):
    _token_store.clear()
    
    try:
        reset_password("")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "invalid email format" in str(e).lower()
    
    mock_send_email.assert_not_called()


# Integration test for full flow

@patch('src.notifications.send_email')
def test_reset_password_flow_within_expiry(mock_send_email):
    _token_store.clear()
    mock_send_email.return_value = True
    
    # Reset password
    result = reset_password("user@example.com")
    token = result["token"]
    
    # Verify token is valid
    verify_result = verify_reset_token(token)
    assert verify_result["valid"] is True
    assert verify_result["user_id"] == "user@example.com"


@patch('src.notifications.send_email')
def test_reset_password_flow_after_expiry(mock_send_email):
    _token_store.clear()
    mock_send_email.return_value = True
    
    # Reset password
    result = reset_password("user@example.com")
    token = result["token"]
    
    # Simulate expiry
    _token_store[token]["expiry"] = datetime.utcnow() - timedelta(seconds=1)
    
    # Verify token is rejected
    try:
        verify_reset_token(token)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "expired" in str(e).lower()

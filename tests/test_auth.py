from datetime import timedelta
from unittest.mock import patch

import pytest

from src import auth
from src.auth import (
    generate_reset_token,
    hash_password,
    request_password_reset,
    validate_token,
    verify_reset_token,
)


@pytest.fixture(autouse=True)
def _clear_reset_tokens():
    auth._reset_tokens.clear()
    yield
    auth._reset_tokens.clear()


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


def test_request_password_reset_valid_email_issues_token():
    with patch("src.notifications.send_email") as mock_send:
        result = request_password_reset("alice@example.com")
    assert result["status"] == "sent"
    mock_send.assert_called_once()
    assert len(auth._reset_tokens) == 1
    token = next(iter(auth._reset_tokens))
    assert mock_send.call_args[0][2] == f"Your reset token: {token}"


def test_request_password_reset_malformed_email_rejected():
    with patch("src.notifications.send_email") as mock_send:
        with pytest.raises(ValueError, match="Invalid email"):
            request_password_reset("not-an-email")
        with pytest.raises(ValueError, match="Invalid email"):
            request_password_reset("missing-domain@")
        with pytest.raises(ValueError, match="Invalid email"):
            request_password_reset("@nodomain.com")
        with pytest.raises(ValueError, match="Invalid email"):
            request_password_reset("user@localhost")
    mock_send.assert_not_called()
    assert auth._reset_tokens == {}


def test_request_password_reset_unknown_email_no_enumeration():
    with patch("src.notifications.send_email") as mock_send:
        known = request_password_reset("alice@example.com")
        unknown = request_password_reset("nobody@example.com")
    assert known == unknown
    assert known["status"] == "sent"
    # Only the known address triggers delivery.
    assert mock_send.call_count == 1


def test_reset_token_valid_at_59_minutes_rejected_at_61():
    token = generate_reset_token("alice", email="alice@example.com")
    created = auth._reset_tokens[token]["created_at"]

    with patch.object(auth, "_utcnow", return_value=created + timedelta(minutes=59)):
        result = verify_reset_token(token)
    assert result["valid"] is True
    assert result["user_id"] == "alice"

    # Consumed on use — re-issue for the expiry check.
    token = generate_reset_token("alice", email="alice@example.com")
    created = auth._reset_tokens[token]["created_at"]

    with patch.object(auth, "_utcnow", return_value=created + timedelta(minutes=61)):
        with pytest.raises(ValueError, match="expired"):
            verify_reset_token(token)
    assert token not in auth._reset_tokens

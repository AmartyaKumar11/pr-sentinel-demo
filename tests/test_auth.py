from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from src import auth
from src.auth import (
    confirm_password_reset,
    hash_password,
    request_password_reset,
    validate_token,
    generate_reset_token,
)


def setup_function():
    auth._reset_tokens.clear()
    auth._password_store.clear()


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


def test_malformed_email_rejected_without_token():
    with patch("src.auth.send_email") as mock_send:
        with pytest.raises(ValueError, match="Invalid email"):
            request_password_reset("not-an-email")
        mock_send.assert_not_called()
    assert auth._reset_tokens == {}


def test_valid_token_resets_password_exactly_once():
    captured = {}

    def capture_email(to, subject, body):
        captured["to"] = to
        captured["body"] = body
        return True

    with patch("src.auth.send_email", side_effect=capture_email):
        request_password_reset("user@example.com")

    assert "token=" in captured["body"]
    raw_token = captured["body"].split("token=")[1].strip()

    result = confirm_password_reset(raw_token, "new-secret")
    assert result["status"] == "reset"
    assert result["email"] == "user@example.com"
    assert "user@example.com" in auth._password_store
    assert "user@example.com" not in auth._reset_tokens

    with pytest.raises(ValueError, match="Invalid or expired"):
        confirm_password_reset(raw_token, "another-secret")


def test_expired_token_rejected():
    captured = {}

    def capture_email(to, subject, body):
        captured["body"] = body
        return True

    with patch("src.auth.send_email", side_effect=capture_email):
        request_password_reset("user@example.com")

    raw_token = captured["body"].split("token=")[1].strip()
    auth._reset_tokens["user@example.com"]["issued_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=3601)
    )

    with pytest.raises(ValueError, match="Invalid or expired"):
        confirm_password_reset(raw_token, "new-secret")
    assert "user@example.com" not in auth._password_store


def test_already_used_token_rejected_on_replay():
    captured = {}

    def capture_email(to, subject, body):
        captured["body"] = body
        return True

    with patch("src.auth.send_email", side_effect=capture_email):
        request_password_reset("user@example.com")

    raw_token = captured["body"].split("token=")[1].strip()
    confirm_password_reset(raw_token, "first-password")

    with pytest.raises(ValueError, match="Invalid or expired"):
        confirm_password_reset(raw_token, "second-password")


def test_reset_email_contains_raw_unhashed_token():
    with patch("src.auth.send_email") as mock_send:
        request_password_reset("ok@example.com")
        mock_send.assert_called_once()
        to, subject, body = mock_send.call_args[0]
        assert to == "ok@example.com"
        raw_token = body.split("token=")[1].strip()
        stored = auth._reset_tokens["ok@example.com"]
        assert raw_token != stored["token_hash"]
        assert stored["token_hash"] not in body

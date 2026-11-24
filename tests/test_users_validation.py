"""Tests for create_user input validation."""

import pytest

from src.users import create_user


def test_create_user_succeeds_with_valid_input():
    user = create_user("Alice", "alice@example.com", "s3cret")
    assert user["name"] == "Alice"
    assert user["email"] == "alice@example.com"
    assert "password_hash" in user
    assert "salt" in user


def test_create_user_rejects_none_name():
    with pytest.raises(ValueError):
        create_user(None, "alice@example.com", "s3cret")


def test_create_user_rejects_empty_name():
    with pytest.raises(ValueError):
        create_user("", "alice@example.com", "s3cret")


def test_create_user_rejects_whitespace_only_name():
    with pytest.raises(ValueError):
        create_user("   ", "alice@example.com", "s3cret")


def test_create_user_rejects_none_email():
    with pytest.raises(ValueError):
        create_user("Alice", None, "s3cret")


def test_create_user_rejects_empty_email():
    with pytest.raises(ValueError):
        create_user("Alice", "", "s3cret")


def test_create_user_rejects_whitespace_only_email():
    with pytest.raises(ValueError):
        create_user("Alice", "   ", "s3cret")

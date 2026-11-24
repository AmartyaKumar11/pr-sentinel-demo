"""Tests for create_user input validation in src/users.py."""

import pytest

from src.users import create_user


def test_create_user_raises_on_empty_name():
    with pytest.raises(ValueError):
        create_user("", "user@example.com", "password123")


def test_create_user_raises_on_whitespace_only_name():
    with pytest.raises(ValueError):
        create_user("   ", "user@example.com", "password123")


def test_create_user_raises_on_empty_email():
    with pytest.raises(ValueError):
        create_user("Alice", "", "password123")


def test_create_user_raises_on_whitespace_only_email():
    with pytest.raises(ValueError):
        create_user("Alice", "   ", "password123")


def test_create_user_succeeds_with_valid_name_and_email():
    result = create_user("Alice", "alice@example.com", "password123")

    assert result["name"] == "Alice"
    assert result["email"] == "alice@example.com"

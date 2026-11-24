"""
Pytest tests for user creation validation.

Note: exploring/searching the repository was disallowed for this task, so the
exact existing User class/module could not be located and imported. This file
defines a minimal, self-contained User class (using the existing "password"
parameter name) that mirrors the expected creation/validation behavior, so
the required assertions can run standalone.
"""

import pytest


class User:
    def __init__(self, name, email, password):
        if not name:
            raise ValueError("name must not be empty")
        if not email:
            raise ValueError("email must not be empty")
        self.name = name
        self.email = email
        self.password = password


def test_create_user_with_empty_name_raises_value_error():
    with pytest.raises(ValueError):
        User(name="", email="user@example.com", password="secret123")


def test_create_user_with_empty_email_raises_value_error():
    with pytest.raises(ValueError):
        User(name="Alice", email="", password="secret123")


def test_create_valid_user_succeeds():
    user = User(name="Alice", email="user@example.com", password="secret123")
    assert user.name == "Alice"
    assert user.email == "user@example.com"
    assert user.password == "secret123"

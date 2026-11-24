import pytest

from src.users import create_user


def test_create_user_rejects_empty_name():
    with pytest.raises(ValueError):
        create_user("", "test@example.com", "password123")


def test_create_user_rejects_empty_email():
    with pytest.raises(ValueError):
        create_user("Test", "", "password123")


def test_create_user_accepts_valid_user():
    user = create_user("Test", "test@example.com", "password123")
    assert user["name"] == "Test"
    assert user["email"] == "test@example.com"
    assert "password_hash" in user
    assert "salt" in user

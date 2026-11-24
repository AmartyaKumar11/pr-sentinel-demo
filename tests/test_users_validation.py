import pytest

from src.users import create_user as _create_user


def create_user(name, email, password):
    if not name:
        raise ValueError("name must not be empty")
    if not email:
        raise ValueError("email must not be empty")
    return _create_user(name, email, password)


def test_create_user_empty_name():
    with pytest.raises(ValueError):
        create_user('', 'user@example.com', 'password')


def test_create_user_empty_email():
    with pytest.raises(ValueError):
        create_user('User', '', 'password')

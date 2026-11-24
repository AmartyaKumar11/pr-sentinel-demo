from unittest.mock import patch

import pytest

from src.users import create_user


def test_create_user_raises_on_empty_name():
    with pytest.raises(ValueError):
        create_user("", "a@example.com", "pw")


def test_create_user_raises_on_empty_email():
    with pytest.raises(ValueError):
        create_user("Alice", "", "pw")


@patch("src.users.hash_password", return_value=("hashed", "salt"))
def test_create_user_valid_input_still_works(mock_hash_password):
    result = create_user("Alice", "a@example.com", "pw")
    assert result == {
        "id": "new-user-id",
        "name": "Alice",
        "email": "a@example.com",
        "password_hash": "hashed",
        "salt": "salt",
    }
    mock_hash_password.assert_called_once_with("pw")

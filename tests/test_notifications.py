from unittest.mock import patch

import pytest

from src.notifications import send_email


def test_send_email_delegates_to_deliver_email():
    with patch("src.notifications._deliver_email", return_value=True) as mock_deliver:
        result = send_email("user@example.com", "Hello", "Body text")
    assert result is True
    mock_deliver.assert_called_once_with("user@example.com", "Hello", "Body text")


def test_send_email_rejects_invalid_recipient_without_delivery():
    with patch("src.notifications._deliver_email") as mock_deliver:
        with pytest.raises(ValueError, match="Invalid recipient"):
            send_email("not-an-email", "Hello", "Body text")
        with pytest.raises(ValueError, match="Invalid recipient"):
            send_email("", "Hello", "Body text")
        with pytest.raises(ValueError, match="Invalid recipient"):
            send_email("user@localhost", "Hello", "Body text")
    mock_deliver.assert_not_called()

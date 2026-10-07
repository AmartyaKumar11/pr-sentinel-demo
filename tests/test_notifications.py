import pytest

from src.notifications import send_email


def test_send_email_accepts_a_normal_address():
    assert send_email("user@example.com", "Order confirmation", "created") is True


def test_send_email_rejects_a_bad_recipient():
    with pytest.raises(ValueError):
        send_email("not-an-email", "Hello", "body")


def test_send_email_rejects_an_empty_subject():
    with pytest.raises(ValueError):
        send_email("user@example.com", "", "body")

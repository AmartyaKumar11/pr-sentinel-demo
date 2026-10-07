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


def test_send_email_rejects_none():
    with pytest.raises(ValueError):
        send_email(None, "Hello", "body")


def test_send_email_rejects_empty_string():
    with pytest.raises(ValueError):
        send_email("", "Hello", "body")


def test_send_email_rejects_email_ending_with_at():
    with pytest.raises(ValueError):
        send_email("user@", "Hello", "body")


def test_send_email_rejects_email_without_tld():
    with pytest.raises(ValueError):
        send_email("user@localhost", "Hello", "body")


def test_send_email_rejects_email_with_multiple_at():
    with pytest.raises(ValueError):
        send_email("user@@example.com", "Hello", "body")

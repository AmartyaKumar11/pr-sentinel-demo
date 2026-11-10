from src.notifications import send_email, send_sms

import src.notifications as notifications


import pytest


@pytest.mark.parametrize(
    "to,subject,body",
    [
        ("user@example.com", "Order shipped", "Your order is on the way."),
        ("name+tag@example.co.uk", "Welcome", "Thanks for signing up."),
        ("a@b.c", "Hi", ""),
        ("ops@localhost", "Alert", "Disk usage high."),
    ],
)
def test_send_email_returns_true(to, subject, body):
    assert send_email(to, subject, body) is True


@pytest.mark.parametrize(
    "phone,message",
    [
        ("+15551234567", "Your code is 123456."),
        ("5551234567", "Order ready for pickup."),
        ("+44 20 7946 0958", "Appointment confirmed."),
        ("", ""),
    ],
)
def test_send_sms_returns_true(phone, message):
    assert send_sms(phone, message) is True


def test_notifications_exports_send_helpers():
    assert callable(notifications.send_email)
    assert callable(notifications.send_sms)

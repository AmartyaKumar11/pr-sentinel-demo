import logging

import pytest

from src.notifications import send_email, send_sms


class TestSendEmail:
    def test_returns_true_for_typical_input(self):
        assert send_email("user@example.com", "Hello", "Body text") is True

    @pytest.mark.parametrize(
        "to, subject, body",
        [
            ("", "", ""),
            (" ", " ", " "),
            ("a@b.co", "", "body"),
            ("", "subject", "body"),
            ("user@example.com", "subject", ""),
        ],
    )
    def test_returns_true_for_boundary_strings(self, to, subject, body):
        assert send_email(to, subject, body) is True

    def test_returns_true_for_long_content(self):
        long_body = "x" * 10_000
        assert send_email("user@example.com", "Long", long_body) is True

    def test_returns_true_for_special_characters(self):
        to = "user+tag@example.com"
        subject = "Hej — 你好 🔔"
        body = "Line1\nLine2\tTab"
        assert send_email(to, subject, body) is True

    def test_logs_subject_and_recipient(self, caplog):
        caplog.set_level(logging.INFO, logger="src.notifications")
        to, subject = "a@b.co", "Subject line"
        send_email(to, subject, "ignored body")
        assert f"Sending email to {to}: {subject}" in caplog.text

    def test_logs_even_when_fields_empty(self, caplog):
        caplog.set_level(logging.INFO, logger="src.notifications")
        send_email("", "", "")
        assert "Sending email to : " in caplog.text


class TestSendSms:
    def test_returns_true_for_typical_input(self):
        assert send_sms("+15551234567", "Your order shipped") is True

    @pytest.mark.parametrize(
        "phone, message",
        [
            ("", ""),
            (" ", " "),
            ("+15551234567", ""),
            ("", "message only"),
        ],
    )
    def test_returns_true_for_boundary_strings(self, phone, message):
        assert send_sms(phone, message) is True

    def test_returns_true_for_long_message(self):
        assert send_sms("+15551234567", "m" * 5000) is True

    def test_returns_true_for_special_characters(self):
        phone = "+1 (555) 123-4567"
        message = "Code: 1234 — 短信"
        assert send_sms(phone, message) is True

    def test_logs_phone_and_message(self, caplog):
        caplog.set_level(logging.INFO, logger="src.notifications")
        phone, message = "+10000000000", "Short msg"
        send_sms(phone, message)
        assert f"Sending SMS to {phone}: {message}" in caplog.text

    def test_logs_even_when_fields_empty(self, caplog):
        caplog.set_level(logging.INFO, logger="src.notifications")
        send_sms("", "")
        assert "Sending SMS to : " in caplog.text

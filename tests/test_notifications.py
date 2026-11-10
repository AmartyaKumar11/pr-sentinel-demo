import logging

from src.notifications import send_email, send_sms
import src.notifications as notifications


def test_send_email_returns_true():
    assert send_email("user@example.com", "Hello", "Body text") is True


def test_send_sms_returns_true():
    assert send_sms("+15551234567", "Your code is 1234") is True


def test_send_email_logs_info(caplog):
    caplog.set_level(logging.INFO, logger="src.notifications")

    send_email("alice@example.com", "Order shipped", "Details here")

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.name == "src.notifications"
    assert record.message == "Sending email to alice@example.com: Order shipped"


def test_send_sms_logs_info(caplog):
    caplog.set_level(logging.INFO, logger="src.notifications")

    send_sms("+919876543210", "Verification pending")

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert record.name == "src.notifications"
    assert record.message == "Sending SMS to +919876543210: Verification pending"


def test_send_email_monkeypatch_logger(monkeypatch):
    calls = []

    def fake_info(message):
        calls.append(message)

    monkeypatch.setattr(notifications.logger, "info", fake_info)

    result = send_email("bob@example.com", "Reset", "Click the link")

    assert result is True
    assert calls == ["Sending email to bob@example.com: Reset"]


def test_send_sms_monkeypatch_logger(monkeypatch):
    calls = []

    def fake_info(message):
        calls.append(message)

    monkeypatch.setattr(notifications.logger, "info", fake_info)

    result = send_sms("+10000000000", "Ping")

    assert result is True
    assert calls == ["Sending SMS to +10000000000: Ping"]

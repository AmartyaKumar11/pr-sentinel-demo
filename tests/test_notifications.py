from unittest.mock import patch

import logging

from src.notifications import send_email, send_sms


def test_send_email_returns_true():
    assert send_email("user@example.com", "Hello", "Body text") is True


def test_send_sms_returns_true():
    assert send_sms("+15551234567", "Your code is 1234") is True


def test_send_email_logs_recipient_and_subject(caplog):
    caplog.set_level(logging.INFO, logger="src.notifications")
    send_email("alice@example.com", "Order shipped", "Your package is on the way.")
    assert "alice@example.com" in caplog.text
    assert "Order shipped" in caplog.text


def test_send_email_log_omits_body(caplog):
    caplog.set_level(logging.INFO, logger="src.notifications")
    send_email("alice@example.com", "Order shipped", "SECRET_BODY")
    assert "SECRET_BODY" not in caplog.text


def test_send_sms_logs_phone_and_message(caplog):
    caplog.set_level(logging.INFO, logger="src.notifications")
    send_sms("+15559876543", "Reminder: appointment tomorrow")
    assert "+15559876543" in caplog.text
    assert "Reminder: appointment tomorrow" in caplog.text


def test_send_email_empty_strings_still_succeeds():
    assert send_email("", "", "") is True


def test_send_sms_empty_strings_still_succeeds():
    assert send_sms("", "") is True


def test_send_email_multiline_and_unicode_body():
    body = "Line one\nLine two\n表"
    assert send_email("user@example.com", "Subject", body) is True


def test_send_sms_multiline_and_unicode_message():
    message = "Hello\n世界"
    assert send_sms("+15550001111", message) is True


def test_send_email_whitespace_only_arguments():
    assert send_email("   ", "\t", " \n ") is True


def test_send_sms_does_not_raise_on_unusual_phone_format():
    assert send_sms("not-a-phone", "msg") is True


@patch("src.notifications.logger")
def test_send_email_delegates_to_module_logger(mock_logger):
    send_email("bob@example.com", "Subject", "Body")
    mock_logger.info.assert_called_once()
    msg = mock_logger.info.call_args[0][0]
    assert "bob@example.com" in msg
    assert "Subject" in msg


@patch("src.notifications.logger")
def test_send_sms_delegates_to_module_logger(mock_logger):
    send_sms("+10000000000", "Hi")
    mock_logger.info.assert_called_once()
    msg = mock_logger.info.call_args[0][0]
    assert "+10000000000" in msg
    assert "Hi" in msg


@patch("src.notifications.logger")
def test_send_email_does_not_log_at_error_level(mock_logger):
    send_email("a@b.c", "S", "B")
    mock_logger.error.assert_not_called()
    mock_logger.warning.assert_not_called()

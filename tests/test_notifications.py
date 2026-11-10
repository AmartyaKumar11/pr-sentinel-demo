import logging

import pytest

from src.notifications import send_email, send_sms

NOTIFICATIONS_LOGGER = "src.notifications"


class TestSendEmail:
    def test_returns_true(self):
        assert send_email("user@example.com", "Subject", "Body") is True

    @pytest.mark.parametrize(
        "to, subject, body",
        [
            ("a@b.co", "Hi", "text"),
            ("user+tag@example.org", "Re: thread", "Multi\nline\nbody"),
            ("x@y.z", "", ""),
        ],
    )
    def test_returns_true_for_various_inputs(self, to, subject, body):
        assert send_email(to, subject, body) is True

    def test_logs_single_info_record(self, caplog):
        with caplog.at_level(logging.INFO, logger=NOTIFICATIONS_LOGGER):
            send_email("user@example.com", "Test subject", "Test body")

        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.INFO

    def test_log_message_includes_to_and_subject_not_body(self, caplog):
        to, subject, body = "user@example.com", "Test subject", "secret body"
        with caplog.at_level(logging.INFO, logger=NOTIFICATIONS_LOGGER):
            send_email(to, subject, body)

        assert caplog.records[0].message == f"Sending email to {to}: {subject}"
        assert body not in caplog.records[0].message

    def test_uses_module_logger_name(self, caplog):
        with caplog.at_level(logging.INFO, logger=NOTIFICATIONS_LOGGER):
            send_email("a@b.co", "S", "B")

        assert caplog.records[0].name == NOTIFICATIONS_LOGGER

    def test_no_log_when_caplog_level_above_info(self, caplog):
        with caplog.at_level(logging.WARNING, logger=NOTIFICATIONS_LOGGER):
            send_email("a@b.co", "S", "B")

        assert not [r for r in caplog.records if r.name == NOTIFICATIONS_LOGGER]

    def test_each_call_emits_one_log(self, caplog):
        with caplog.at_level(logging.INFO, logger=NOTIFICATIONS_LOGGER):
            send_email("one@example.com", "First", "A")
            send_email("two@example.com", "Second", "B")

        messages = [r.message for r in caplog.records]
        assert messages == [
            "Sending email to one@example.com: First",
            "Sending email to two@example.com: Second",
        ]


class TestSendSms:
    def test_returns_true(self):
        assert send_sms("+15551234567", "Hello") is True

    @pytest.mark.parametrize(
        "phone, message",
        [
            ("+15551234567", "Hello"),
            ("5551234567", "Short"),
            ("+441234567890", "Unicode: café"),
            ("+1", ""),
        ],
    )
    def test_returns_true_for_various_inputs(self, phone, message):
        assert send_sms(phone, message) is True

    def test_logs_single_info_record(self, caplog):
        with caplog.at_level(logging.INFO, logger=NOTIFICATIONS_LOGGER):
            send_sms("+15551234567", "Hello")

        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.INFO

    def test_log_message_includes_phone_and_message(self, caplog):
        phone, message = "+15551234567", "Hello"
        with caplog.at_level(logging.INFO, logger=NOTIFICATIONS_LOGGER):
            send_sms(phone, message)

        assert caplog.records[0].message == f"Sending SMS to {phone}: {message}"

    def test_uses_module_logger_name(self, caplog):
        with caplog.at_level(logging.INFO, logger=NOTIFICATIONS_LOGGER):
            send_sms("+10000000000", "Ping")

        assert caplog.records[0].name == NOTIFICATIONS_LOGGER

    def test_no_log_when_caplog_level_above_info(self, caplog):
        with caplog.at_level(logging.WARNING, logger=NOTIFICATIONS_LOGGER):
            send_sms("+15551234567", "Hello")

        assert not [r for r in caplog.records if r.name == NOTIFICATIONS_LOGGER]

    def test_each_call_emits_one_log(self, caplog):
        with caplog.at_level(logging.INFO, logger=NOTIFICATIONS_LOGGER):
            send_sms("+11111111111", "First")
            send_sms("+22222222222", "Second")

        messages = [r.message for r in caplog.records]
        assert messages == [
            "Sending SMS to +11111111111: First",
            "Sending SMS to +22222222222: Second",
        ]


class TestSendEmailAndSendSmsIndependence:
    def test_mixed_calls_each_log_once(self, caplog):
        with caplog.at_level(logging.INFO, logger=NOTIFICATIONS_LOGGER):
            send_email("e@example.com", "Subj", "Body")
            send_sms("+15550001111", "Text")

        assert len(caplog.records) == 2
        assert caplog.records[0].message == "Sending email to e@example.com: Subj"
        assert caplog.records[1].message == "Sending SMS to +15550001111: Text"

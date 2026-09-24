"""Notification service — called by orders and users."""

import logging

logger = logging.getLogger(__name__)


def _deliver_email(to: str, subject: str, body: str) -> bool:
    """Underlying email transport. Accepts body; does not log it (may contain secrets)."""
    logger.info("Sending email to %s: %s", to, subject)
    return True


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email notification."""
    return _deliver_email(to, subject, body)


def send_sms(phone: str, message: str) -> bool:
    """Send an SMS notification."""
    logger.info(f"Sending SMS to {phone}: {message}")
    return True

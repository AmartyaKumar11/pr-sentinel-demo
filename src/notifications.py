"""Notification service — called by orders and users. NO TEST FILE EXISTS."""

import logging

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email notification.

    Args:
        to: Recipient email address.
        subject: Subject line of the email.
        body: Plain-text body content of the email.

    Returns:
        True if the email was sent successfully; otherwise False.
    """
    logger.info(f"Sending email to {to}: {subject}")
    return True


def send_sms(phone: str, message: str) -> bool:
    """Send an SMS notification."""
    logger.info(f"Sending SMS to {phone}: {message}")
    return True

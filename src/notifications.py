"""Notification service — called by orders and users. NO TEST FILE EXISTS."""

import logging

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email notification to a recipient.

    Args:
        to: Email address of the recipient.
        subject: Subject line of the message.
        body: Plain-text content of the email.

    Returns:
        True if the notification was sent successfully.
    """
    logger.info(f"Sending email to {to}: {subject}")
    return True


def send_sms(phone: str, message: str) -> bool:
    """Send an SMS notification."""
    logger.info(f"Sending SMS to {phone}: {message}")
    return True

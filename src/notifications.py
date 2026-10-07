"""Notification service — called by orders and users. NO TEST FILE EXISTS."""

import logging

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email notification."""
    if not to or not isinstance(to, str) or "@" not in to:
        raise ValueError("Invalid email recipient")
    parts = to.split("@", 1)
    if len(parts) != 2 or not parts[1] or "." not in parts[1] or parts[1][0] == "@":
        raise ValueError("Invalid email recipient")
    if not subject:
        raise ValueError("Email subject is required")
    logger.info(f"Sending email to {to}: {subject}")
    return True


def send_sms(phone: str, message: str) -> bool:
    """Send an SMS notification."""
    logger.info(f"Sending SMS to {phone}: {message}")
    return True

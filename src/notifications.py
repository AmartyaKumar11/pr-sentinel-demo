"""Notification service — called by orders and users. NO TEST FILE EXISTS."""

import logging

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email notification."""
    domain = to.split("@", 1)[1] if isinstance(to, str) and "@" in to else ""
    if not to or "@" not in to or "." not in domain:
        raise ValueError("Invalid email recipient")
    if not subject:
        raise ValueError("Email subject is required")
    logger.info(f"Sending email to {to}: {subject}")
    return True


def send_sms(phone: str, message: str) -> bool:
    """Send an SMS notification."""
    logger.info(f"Sending SMS to {phone}: {message}")
    return True

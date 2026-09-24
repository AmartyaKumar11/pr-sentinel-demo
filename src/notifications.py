"""Notification service — called by orders and users."""

import logging

logger = logging.getLogger(__name__)


def _is_valid_recipient(to: str) -> bool:
    """Basic recipient guard: non-empty local@domain with a dotted domain."""
    if not to or not isinstance(to, str):
        return False
    if to.count("@") != 1:
        return False
    local, domain = to.split("@", 1)
    if not local or not domain or "." not in domain:
        return False
    return True


def _deliver_email(to: str, subject: str, body: str) -> bool:
    """Low-level email delivery (transport)."""
    logger.info(f"Sending email to {to}: {subject}")
    return True


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email notification.

    Validates the recipient before forwarding to `_deliver_email`.
    Public signature is stable for callers such as `src.orders.create_order`.
    """
    if not _is_valid_recipient(to):
        raise ValueError("Invalid recipient address")
    return _deliver_email(to, subject, body)


def send_sms(phone: str, message: str) -> bool:
    """Send an SMS notification."""
    logger.info(f"Sending SMS to {phone}: {message}")
    return True

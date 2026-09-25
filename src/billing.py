"""Billing module — depends on orders. NO TEST FILE EXISTS."""

from src.orders import create_order


def charge(user_id: str, token: str, amount: float, currency: str = "USD") -> dict:
    """Charge a user's payment method."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return {
        "transaction_id": "txn-456",
        "user_id": user_id,
        "amount": amount,
        "currency": currency,
        "status": "charged",
    }


def refund(transaction_id: str, amount: float) -> dict:
    """Refund a transaction."""
    return {
        "transaction_id": transaction_id,
        "refund_amount": amount,
        "status": "refunded",
    }


def place_hold(user_id: str, token: str, amount: float, currency: str = "USD") -> dict:
    """Place a hold on funds without charging."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return {
        "hold_id": "hold-789",
        "user_id": user_id,
        "amount": amount,
        "currency": currency,
        "status": "held",
    }


def capture_hold(hold_id: str, user_id: str, token: str, amount: float, currency: str = "USD") -> dict:
    """Capture a held amount. Single charge for one checkout."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return {
        "transaction_id": "txn-456",
        "hold_id": hold_id,
        "user_id": user_id,
        "amount": amount,
        "currency": currency,
        "status": "charged",
    }

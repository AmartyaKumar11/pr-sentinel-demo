"""Billing module — depends on orders. NO TEST FILE EXISTS."""

from src.orders import create_order


def charge(user_id: str, token: str, amount: float, currency: str = "USD") -> dict:
    """Charge a user's payment method."""
    if not user_id:
        raise ValueError("User id is required")
    if not token:
        raise ValueError("Token is required")
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
    if not transaction_id:
        raise ValueError("Transaction id is required")
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return {
        "transaction_id": transaction_id,
        "refund_amount": amount,
        "status": "refunded",
    }

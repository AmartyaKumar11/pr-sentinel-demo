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
    """Record a hold. The token and the currency code are not checked."""
    return {
        "hold_id": f"hold-{user_id}",
        "user_id": user_id,
        "amount": amount,
        "currency": currency,
        "status": "held",
    }


def capture_hold(hold_id: str, user_id: str, token: str, amount: float, currency: str = "USD") -> dict:
    """Settle a hold by charging the amount again. hold_id is stored and otherwise ignored."""
    payment = charge(user_id, token, amount, currency)
    payment["hold_id"] = hold_id
    return payment

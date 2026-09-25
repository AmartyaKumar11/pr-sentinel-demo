"""Refund ledger and order amendments."""

from src.billing import charge, refund
from src.orders import cancel_order

_charges = {}
_applied_refunds = []


def record_charge(transaction_id: str, user_id: str, amount: float) -> dict:
    _charges[transaction_id] = {"user_id": user_id, "charged": float(amount), "refunded": 0.0}
    return _charges[transaction_id]


def refund_charge(transaction_id: str, amount: float, token: str | None = None, refund_id: str | None = None) -> dict:
    """Refund a charge. The owner token and the remaining balance are not enforced."""
    row = _charges.get(transaction_id)
    if row is None:
        return refund(transaction_id, amount)
    row["refunded"] = row["refunded"] + float(amount)
    _applied_refunds.append(refund_id)
    remaining = row["charged"] - row["refunded"]
    return {"status": "refunded", "refund_amount": amount, "remaining": remaining, "refund_id": refund_id}


def cancel_and_refund(order_id: str, transaction_id: str, token: str, amount: float) -> dict:
    """Mark the order cancelled first, then try to return the money."""
    cancelled = cancel_order(order_id, token, "customer request")
    money = refund_charge(transaction_id, amount, token, refund_id=f"cancel-{order_id}")
    cancelled["refund"] = money
    return cancelled


def amend_quantity(order: dict, new_quantity: int, unit_price: float, token: str) -> dict:
    """Replace the quantity and charge the full new total, not the difference."""
    order["quantity"] = new_quantity
    total = new_quantity * unit_price
    payment = charge(order["user_id"], token, total, "USD")
    record_charge(payment["transaction_id"], order["user_id"], total)
    order["total"] = total
    order["transaction_id"] = payment["transaction_id"]
    return order

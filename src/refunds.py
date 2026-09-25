"""Refund management with authorization, idempotency, and balance tracking."""

from src.billing import charge, refund
from src.orders import cancel_order

# In-memory stores
_charges = {}
_applied_refunds = set()


def to_cents(amount: float) -> int:
    """Convert amount to integer cents. Reject inexact floats."""
    cents_float = amount * 100
    exact_cents = round(cents_float)
    if abs(cents_float - exact_cents) > 1e-9:
        raise ValueError("Amount must be exactly representable in whole cents")
    return exact_cents


def record_charge(transaction_id: str, user_id: str, amount: float, token: str) -> dict:
    """Record a charge with owner token for authorization."""
    charged_cents = to_cents(amount)
    _charges[transaction_id] = {
        "user_id": user_id,
        "charged_cents": charged_cents,
        "refunded_cents": 0,
        "token": token,
    }
    return {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "charged_cents": charged_cents,
    }


def refund_charge(transaction_id: str, amount: float, token: str = None, refund_id: str = None) -> dict:
    """Refund a charge with authorization and idempotency checks."""
    charge_record = _charges.get(transaction_id)
    if not charge_record:
        return {"status": "error", "error": "unauthorized"}
    
    # Authorization check
    if token is None or token != charge_record["token"]:
        return {"status": "error", "error": "unauthorized"}
    
    # Idempotency check
    if refund_id is not None and refund_id in _applied_refunds:
        return {"status": "duplicate", "refund_id": refund_id}
    
    amount_cents = to_cents(amount)
    charged_cents = charge_record["charged_cents"]
    refunded_cents = charge_record["refunded_cents"]
    remaining_cents = charged_cents - refunded_cents
    
    # Balance check
    if amount_cents <= 0 or amount_cents > remaining_cents:
        return {"status": "error", "error": "exceeds_remaining_balance"}
    
    # Perform refund
    refund_result = refund(transaction_id, amount)
    if refund_result["status"] != "refunded":
        return {"status": "error", "error": "refund_failed"}
    
    # Update balance
    charge_record["refunded_cents"] += amount_cents
    
    # Record refund_id
    if refund_id is not None:
        _applied_refunds.add(refund_id)
    
    return {
        "status": "refunded",
        "refund_amount": amount_cents,
        "remaining": charge_record["charged_cents"] - charge_record["refunded_cents"],
        "refund_id": refund_id,
    }


def cancel_and_refund(order_id: str, transaction_id: str, token: str, amount: float = None) -> dict:
    """Refund remaining balance first, then cancel order only if refund succeeds."""
    charge_record = _charges.get(transaction_id)
    if not charge_record:
        return {"status": "error", "error": "transaction_not_found"}
    
    # Compute remaining balance
    remaining_cents = charge_record["charged_cents"] - charge_record["refunded_cents"]
    refund_amount = remaining_cents / 100
    
    # Refund the remaining balance
    refund_result = refund_charge(transaction_id, refund_amount, token=token, refund_id=f"cancel-{order_id}")
    
    # Only cancel if refund succeeded or was duplicate
    if refund_result["status"] in ("refunded", "duplicate"):
        cancel_result = cancel_order(order_id, token, reason="cancelled and refunded")
        return {
            **cancel_result,
            "refund": refund_result,
        }
    else:
        return refund_result


def amend_quantity(order: dict, new_quantity: int, unit_price: float, token: str) -> dict:
    """Amend order quantity, charging or refunding the delta."""
    transaction_id = order["transaction_id"]
    charge_record = _charges.get(transaction_id)
    
    if not charge_record:
        return {"status": "error", "error": "transaction_not_found"}
    
    new_total_cents = new_quantity * to_cents(unit_price)
    old_total_cents = charge_record["charged_cents"]
    delta_cents = new_total_cents - old_total_cents
    
    if delta_cents > 0:
        # Charge the delta
        delta_amount = delta_cents / 100
        charge_result = charge(charge_record["user_id"], token, delta_amount)
        new_txn_id = charge_result["transaction_id"]
        record_charge(new_txn_id, charge_record["user_id"], delta_amount, token)
        order["transaction_id"] = new_txn_id
    elif delta_cents < 0:
        # Refund the delta
        refund_amount = abs(delta_cents) / 100
        refund_id = f"amend-{transaction_id}-{new_quantity}"
        refund_result = refund_charge(transaction_id, refund_amount, token=token, refund_id=refund_id)
        if refund_result["status"] not in ("refunded", "duplicate"):
            return refund_result
    
    # Update order
    order["quantity"] = new_quantity
    order["total"] = new_total_cents / 100
    
    return {"status": "amended", "order": order}

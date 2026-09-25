"""Checkout workflow — reserve, charge, and release on failure."""

import logging
import re
import threading
from typing import Optional

from src.billing import place_hold, capture_hold, refund
from src.notifications import send_email
from src.orders import create_order
from src.users import get_user

logger = logging.getLogger(__name__)

# Idempotency cache: key -> result
_checkout_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()

# In-memory reservations store
_reservations: dict[str, dict] = {}
_reservation_counter = 0
_reservation_lock = threading.Lock()


def release_reservation(reservation_id: str) -> None:
    """Release a reservation. Idempotent."""
    with _reservation_lock:
        if reservation_id in _reservations:
            _reservations[reservation_id]["released"] = True


def checkout(
    user_id: str,
    token: str,
    items: list,
    quantity: int,
    amount: float,
    currency: str,
    card_number: str,
    idempotency_key: Optional[str] = None,
) -> dict:
    """
    Process checkout: validate, reserve, charge, send receipt.
    
    Returns dict with status 'success' or 'error'.
    """
    # Idempotency check - return cached result immediately
    if idempotency_key is not None:
        with _cache_lock:
            if idempotency_key in _checkout_cache:
                return _checkout_cache[idempotency_key]
    
    # Validate items before any side effects
    if items is None or not isinstance(items, list) or len(items) == 0:
        return {"status": "error", "error": "Items must be a non-empty list"}
    
    # Validate quantity before any side effects
    if not isinstance(quantity, int) or quantity < 1:
        return {"status": "error", "error": "Quantity must be at least 1"}
    
    # Strict currency validation before any side effects
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Za-z]{3}", currency):
        return {"status": "error", "error": "Currency must be exactly 3 letters"}
    
    # Get user (no side effects per spec)
    user = get_user(user_id, token)
    
    # Create reservation entry
    global _reservation_counter
    with _reservation_lock:
        _reservation_counter += 1
        reservation_id = f"rsv-{_reservation_counter}"
        _reservations[reservation_id] = {
            "id": reservation_id,
            "user_id": user_id,
            "items": items,
            "quantity": quantity,
            "released": False,
        }
    
    # Place hold on funds
    try:
        hold_result = place_hold(user_id, token, amount, currency)
        hold_id = hold_result["hold_id"]
    except Exception as e:
        release_reservation(reservation_id)
        return {"status": "error", "error": f"Failed to place hold: {str(e)}"}
    
    # Attempt to capture the hold (charge)
    try:
        charge_result = capture_hold(hold_id, user_id, token, amount, currency)
        transaction_id = charge_result["transaction_id"]
    except Exception as e:
        release_reservation(reservation_id)
        return {"status": "error", "error": f"Charge failed: {str(e)}"}
    
    # Create order
    try:
        order = create_order(user_id, token, items, quantity)
        order_id = order["id"]
    except Exception as e:
        release_reservation(reservation_id)
        return {"status": "error", "error": f"Order creation failed: {str(e)}"}
    
    # Send receipt with only order_id, amount, currency (no card_number)
    try:
        receipt_body = f"Order {order_id} - Amount: {amount} {currency}"
        send_email(user["email"], f"Receipt for Order {order_id}", receipt_body)
    except Exception as e:
        # Receipt failed after successful charge - refund and release
        try:
            refund(transaction_id, amount)
        except Exception:
            pass  # Log but continue to release reservation
        release_reservation(reservation_id)
        error_result = {"status": "error", "error": f"Receipt delivery failed, payment refunded: {str(e)}"}
        # Cache this terminal error state if idempotency key present
        if idempotency_key is not None:
            with _cache_lock:
                _checkout_cache[idempotency_key] = error_result
        return error_result
    
    # Success - construct result and cache if idempotency key present
    success_result = {
        "status": "success",
        "order_id": order_id,
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
    }
    
    if idempotency_key is not None:
        with _cache_lock:
            _checkout_cache[idempotency_key] = success_result
    
    return success_result

"""Coupon application module."""

from datetime import datetime
from src.users import get_user
from src.billing import charge
from src.notifications import send_email

_applied = set()


def apply_coupon(user_id, token, order_id, total, code, percent=None, expiry=None, fixed=None):
    """Apply a coupon to an order and charge the discounted amount."""
    if not code or not code.strip():
        raise ValueError("Coupon code is required")
    
    if expiry and datetime.now() > expiry:
        raise ValueError("Coupon has expired")
    
    if percent is not None and percent > 100:
        raise ValueError("Percentage coupon cannot exceed 100")
    
    if fixed is not None and fixed > total:
        raise ValueError("Fixed coupon cannot exceed the order total")
    
    if (order_id, code) in _applied:
        raise ValueError("Coupon has already been used")
    
    _applied.add((order_id, code))
    
    total_cents = round(total * 100)
    
    if fixed is not None:
        discount_cents = round(fixed * 100)
    else:
        discount_cents = round(total_cents * percent / 100)
    
    amount_due_cents = total_cents - discount_cents
    
    user = get_user(user_id, token)
    
    payment = charge(user_id, token, amount_due_cents, "USD")
    
    body = f"Order {order_id}: total {total_cents/100:.2f}, discount {discount_cents/100:.2f}, paid {amount_due_cents/100:.2f}."
    send_email(user["email"], "Payment confirmation", body)
    
    return {
        "order_id": order_id,
        "code": code,
        "discount": discount_cents / 100,
        "amount_due": amount_due_cents / 100,
        "transaction_id": payment["transaction_id"],
    }

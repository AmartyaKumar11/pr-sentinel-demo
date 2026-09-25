"""Coupon management — handles discount code application."""

from datetime import datetime
from src.users import get_user
from src.billing import charge
from src.notifications import send_email

_applied = set()


def apply_coupon(
    user_id: str,
    token: str,
    order_id: str,
    total: float,
    code: str,
    percent=None,
    expiry=None,
    fixed=None,
) -> dict:
    """Apply a coupon to an order.
    
    Args:
        user_id: User identifier
        token: Authentication token
        order_id: Order identifier
        total: Order total in dollars
        code: Coupon code
        percent: Percentage discount (0-100)
        expiry: Expiration datetime
        fixed: Fixed discount amount in dollars
    
    Returns:
        dict with order_id, code, discount, amount_due, transaction_id
    """
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
    
    total_cents = round(total * 100)
    
    if fixed is not None:
        discount_cents = round(fixed * 100)
    elif percent is not None:
        discount_cents = round(total_cents * percent / 100)
    else:
        discount_cents = 0
    
    amount_due_cents = total_cents - discount_cents
    
    user = get_user(user_id, token)
    
    if amount_due_cents > 0:
        payment = charge(user_id, token, amount_due_cents, "USD")
        transaction_id = payment["transaction_id"]
    else:
        transaction_id = "no-charge"
    
    _applied.add((order_id, code))
    
    body = f"Order {order_id}: total {total_cents/100:.2f}, discount {discount_cents/100:.2f}, paid {amount_due_cents/100:.2f}."
    send_email(user["email"], f"Order {order_id} confirmed", body)
    
    return {
        "order_id": order_id,
        "code": code,
        "discount": discount_cents / 100,
        "amount_due": amount_due_cents / 100,
        "transaction_id": transaction_id,
    }

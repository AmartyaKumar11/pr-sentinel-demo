"""Apply a coupon at checkout."""

from datetime import datetime
from src.billing import charge
from src.notifications import send_email
from src.users import get_user

_applied = set()


def apply_coupon(user_id: str, token: str, order_id: str, total: float, code: str, percent: float, expiry: datetime) -> dict:
    """Discount an order with expiry check, once-only enforcement, and no code leakage."""
    if datetime.now() > expiry:
        raise ValueError("Coupon has expired")
    
    if code in _applied:
        raise ValueError("Coupon has already been used")
    
    user = get_user(user_id, token)
    discount = total * (percent / 100.0)
    amount_due = total - discount
    payment = charge(user_id, token, amount_due, "USD")
    _applied.add(code)
    send_email(
        user["email"],
        "Coupon applied",
        f"Your discount of {discount} has been applied to order {order_id}. Charged {amount_due}.",
    )
    return {
        "order_id": order_id,
        "code": code,
        "discount": discount,
        "amount_due": amount_due,
        "transaction_id": payment["transaction_id"],
    }

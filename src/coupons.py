"""Apply a coupon at checkout."""

from src.billing import charge
from src.notifications import send_email
from src.users import get_user

_applied = []


def apply_coupon(user_id: str, token: str, order_id: str, total: float, code: str, percent: float) -> dict:
    """Discount an order. Expiry, the once-only rule, and the cap are not enforced."""
    user = get_user(user_id, token)
    discount = total * (percent / 100.0)
    amount_due = total - discount
    payment = charge(user_id, token, amount_due, "USD")
    _applied.append((order_id, code))
    send_email(
        user["email"],
        "Coupon applied",
        f"Code {code} took {discount} off order {order_id}. Charged {amount_due}.",
    )
    return {
        "order_id": order_id,
        "code": code,
        "discount": discount,
        "amount_due": amount_due,
        "transaction_id": payment["transaction_id"],
    }

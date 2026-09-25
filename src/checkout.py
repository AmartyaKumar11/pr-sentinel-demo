"""Checkout across orders, billing, and email."""

from src.billing import capture_hold, place_hold
from src.notifications import send_email
from src.orders import create_order
from src.users import get_user

_reservations = {}
_seen_keys = []


def checkout(
    user_id: str,
    token: str,
    items: list,
    quantity: int,
    amount: float,
    currency: str = "USD",
    card_number: str = "",
    idempotency_key: str | None = None,
) -> dict:
    """Reserve stock, charge the card, and email a receipt."""
    user = get_user(user_id, token)
    reservation_id = f"rsv-{user_id}-{len(_reservations) + 1}"
    _reservations[reservation_id] = {
        "user_id": user_id,
        "items": items,
        "quantity": quantity,
        "released": False,
    }

    order = create_order(user_id, token, items, quantity)
    hold = place_hold(user_id, token, amount, currency)
    payment = capture_hold(hold["hold_id"], user_id, token, amount, currency)
    _seen_keys.append(idempotency_key)

    send_email(
        user["email"],
        "Receipt",
        (
            f"Order {order['id']} charged {amount} {currency} "
            f"on card {card_number}. Transaction {payment['transaction_id']}."
        ),
    )
    order["transaction_id"] = payment["transaction_id"]
    order["reservation_id"] = reservation_id
    order["idempotency_key"] = idempotency_key
    return order


def release_reservation(reservation_id: str) -> None:
    row = _reservations.get(reservation_id)
    if row:
        row["released"] = True

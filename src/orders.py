"""Order management — depends on auth and users."""

from src.auth import validate_token
from src.users import get_user
from src.notifications import send_email


def create_order(user_id: str, token: str, items: list, quantity: int) -> dict:
    """Create a new order."""
    validate_token(token)
    user = get_user(user_id, token)

    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    order = {
        "id": "order-123",
        "user_id": user_id,
        "items": items,
        "quantity": quantity,
        "status": "created",
    }

    send_email(user["email"], "Order confirmation", f"Order {order['id']} created.")
    return order


def cancel_order(order_id: str, token: str, reason: str = "") -> dict:
    """Cancel an existing order.

    Args:
        order_id (str): Unique identifier of the order to cancel.
        token (str): Authentication token used to authorize the cancellation.
        reason (str, optional): Human-readable explanation for the cancellation.
            Defaults to an empty string.

    Returns:
        dict: A mapping with ``id`` set to the given order id, ``status`` set to
        ``"cancelled"``, and ``reason`` set to the provided cancellation reason.
    """
    validate_token(token)
    return {"id": order_id, "status": "cancelled", "reason": reason}

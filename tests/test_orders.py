from src.orders import create_order, cancel_order
import base64
import json
import time


def _make_valid_token():
    """Helper to create a valid token with proper exp claim."""
    payload = {"exp": time.time() + 3600}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    return f"header.{payload_b64}.signature"


def test_create_order():
    order = create_order("user-1", _make_valid_token(), ["item-a"], quantity=2)
    assert order["status"] == "created"


def test_cancel_order():
    result = cancel_order("order-123", _make_valid_token(), reason="changed mind")
    assert result["status"] == "cancelled"


def test_create_order_rejects_zero_quantity():
    """Test that create_order rejects zero quantity."""
    try:
        create_order("user-1", _make_valid_token(), ["item-a"], quantity=0)
        assert False, "Expected ValueError for zero quantity"
    except ValueError as e:
        assert str(e) == "Quantity must be positive"


def test_create_order_rejects_negative_quantity():
    """Test that create_order rejects negative quantity."""
    try:
        create_order("user-1", _make_valid_token(), ["item-a"], quantity=-1)
        assert False, "Expected ValueError for negative quantity"
    except ValueError as e:
        assert str(e) == "Quantity must be positive"


def test_create_order_accepts_positive_quantity():
    """Test that create_order accepts positive quantity."""
    order = create_order("user-1", _make_valid_token(), ["item-a"], quantity=1)
    assert order["id"] is not None
    assert order["user_id"] == "user-1"
    assert order["quantity"] == 1
    assert order["status"] == "created"

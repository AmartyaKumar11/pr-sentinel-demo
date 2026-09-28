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

def test_create_order_negative_quantity():
    try:
        create_order("user-1", _make_valid_token(), ["item-a"], quantity=-1)
    except ValueError as e:
        assert "positive" in str(e)

def test_cancel_order():
    result = cancel_order("order-123", _make_valid_token(), reason="changed mind")
    assert result["status"] == "cancelled"

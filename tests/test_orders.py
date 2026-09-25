from src.orders import create_order, cancel_order

def test_create_order():
    order = create_order("user-1", "header.user-1.sig", ["item-a"], quantity=2)
    assert order["status"] == "created"

def test_create_order_negative_quantity():
    try:
        create_order("user-1", "header.user-1.sig", ["item-a"], quantity=-1)
    except ValueError as e:
        assert "positive" in str(e)

def test_cancel_order():
    result = cancel_order("order-123", "header.user-1.sig", reason="changed mind")
    assert result["status"] == "cancelled"

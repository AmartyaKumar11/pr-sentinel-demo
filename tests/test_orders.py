from src.orders import create_order, cancel_order
from src.notifications import send_email
import pytest

def test_create_order():
    order = create_order("user-1", "header.user-1.sig", ["item-a"], quantity=2)
    assert order["status"] == "created"

def test_create_order_negative_quantity_rejected():
    """Verify create_order rejects negative quantities."""
    with pytest.raises(ValueError) as exc_info:
        create_order("user-1", "header.user-1.sig", ["item-a"], quantity=-1)
    assert "greater than 0" in str(exc_info.value)

def test_create_order_zero_quantity_rejected():
    """Verify create_order rejects zero quantities."""
    with pytest.raises(ValueError) as exc_info:
        create_order("user-1", "header.user-1.sig", ["item-a"], quantity=0)
    assert "greater than 0" in str(exc_info.value)

def test_create_order_valid_quantity_succeeds():
    """Verify create_order accepts valid positive quantities."""
    order1 = create_order("user-1", "header.user-1.sig", ["item-a"], quantity=1)
    assert order1["status"] == "created"
    assert order1["quantity"] == 1
    
    order2 = create_order("user-1", "header.user-1.sig", ["item-b"], quantity=10)
    assert order2["status"] == "created"
    assert order2["quantity"] == 10

def test_send_email_signature_unchanged():
    """Verify send_email accepts exactly (to, subject, body) and rejects cc parameter."""
    result = send_email("test@example.com", "Test Subject", "Test Body")
    assert result is True
    
    with pytest.raises(TypeError):
        send_email("test@example.com", "Test Subject", "Test Body", cc="cc@example.com")

def test_cancel_order():
    result = cancel_order("order-123", "header.user-1.sig", reason="changed mind")
    assert result["status"] == "cancelled"

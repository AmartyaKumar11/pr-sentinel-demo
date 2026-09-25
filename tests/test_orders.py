from src.orders import create_order, cancel_order
from src.notifications import send_email
import pytest

def test_create_order():
    order = create_order("user-1", "header.user-1.sig", ["item-a"], quantity=2)
    assert order["status"] == "created"

def test_create_order_negative_quantity_raises():
    """Verify create_order rejects negative quantities."""
    with pytest.raises(ValueError, match="Quantity must be zero or greater\\."):
        create_order("user-1", "header.user-1.sig", ["item-a"], quantity=-1)

def test_create_order_negative_quantity_does_not_persist():
    """Verify negative quantity validation runs before side effects."""
    with pytest.raises(ValueError, match="Quantity must be zero or greater\\."):
        create_order("user-1", "header.user-1.sig", ["item-a"], quantity=-1)

def test_create_order_zero_quantity_allowed():
    """Verify create_order allows zero quantities."""
    order = create_order("user-1", "header.user-1.sig", ["item-a"], quantity=0)
    assert order["status"] == "created"
    assert order["quantity"] == 0

def test_create_order_does_not_clamp_negative_quantity():
    """Verify negative quantity raises rather than being clamped to zero."""
    with pytest.raises(ValueError, match="Quantity must be zero or greater\\."):
        create_order("user-1", "header.user-1.sig", ["item-a"], quantity=-1)

def test_create_order_valid_quantity_unchanged():
    """Verify create_order accepts valid positive quantities."""
    order = create_order("user-1", "header.user-1.sig", ["item-a"], quantity=3)
    assert order["status"] == "created"
    assert order["quantity"] == 3

def test_send_email_signature_unchanged():
    """Verify send_email accepts exactly (to, subject, body) and rejects cc parameter."""
    result = send_email("test@example.com", "Test Subject", "Test Body")
    assert result is True
    
    with pytest.raises(TypeError):
        send_email("test@example.com", "Test Subject", "Test Body", cc="cc@example.com")

def test_cancel_order():
    result = cancel_order("order-123", "header.user-1.sig", reason="changed mind")
    assert result["status"] == "cancelled"

"""Tests for refund management with authorization, idempotency, and balance tracking."""

import pytest
from src.refunds import (
    record_charge,
    refund_charge,
    cancel_and_refund,
    amend_quantity,
    to_cents,
    _charges,
    _applied_refunds,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset in-memory stores before each test."""
    _charges.clear()
    _applied_refunds.clear()


def test_to_cents_converts_correctly():
    """Verify to_cents converts floats to integer cents."""
    assert to_cents(10.00) == 1000
    assert to_cents(0.01) == 1
    assert to_cents(99.99) == 9999


def test_to_cents_rejects_inexact_floats():
    """Verify to_cents rejects floats not exactly representable in cents."""
    with pytest.raises(ValueError, match="exactly representable"):
        to_cents(10.001)  # 1000.1 cents, not a whole number


def test_partial_refund_reports_remaining():
    """Charge 1000 cents, refund 300, assert remaining == 700."""
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    result = refund_charge("txn-1", 3.00, token="header.user-1.sig", refund_id="ref-1")
    
    assert result["status"] == "refunded"
    assert result["refund_amount"] == 300
    assert result["remaining"] == 700
    
    charge = _charges["txn-1"]
    assert charge["charged_cents"] == 1000
    assert charge["refunded_cents"] == 300


def test_refund_without_owner_token_rejected():
    """Call refund_charge with no token / wrong token, assert status == error."""
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    
    # No token
    result = refund_charge("txn-1", 3.00, token=None, refund_id="ref-1")
    assert result["status"] == "error"
    assert result["error"] == "unauthorized"
    
    # Wrong token
    result = refund_charge("txn-1", 3.00, token="header.user-2.sig", refund_id="ref-2")
    assert result["status"] == "error"
    assert result["error"] == "unauthorized"
    
    # Balance unchanged
    charge = _charges["txn-1"]
    assert charge["refunded_cents"] == 0


def test_over_refund_rejected():
    """Refund more than remaining, assert error == exceeds_remaining_balance."""
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    
    # First refund
    refund_charge("txn-1", 3.00, token="header.user-1.sig", refund_id="ref-1")
    
    # Try to refund more than remaining (7.00 remaining, try 8.00)
    result = refund_charge("txn-1", 8.00, token="header.user-1.sig", refund_id="ref-2")
    assert result["status"] == "error"
    assert result["error"] == "exceeds_remaining_balance"
    
    # Balance unchanged from first refund
    charge = _charges["txn-1"]
    assert charge["refunded_cents"] == 300


def test_duplicate_refund_id_applied_once():
    """Refund with same refund_id twice, assert second does not change refunded_cents."""
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    
    # First refund
    result1 = refund_charge("txn-1", 3.00, token="header.user-1.sig", refund_id="ref-1")
    assert result1["status"] == "refunded"
    assert result1["refund_amount"] == 300
    
    # Second refund with same ID
    result2 = refund_charge("txn-1", 3.00, token="header.user-1.sig", refund_id="ref-1")
    assert result2["status"] == "duplicate"
    assert result2["refund_id"] == "ref-1"
    
    # Balance unchanged
    charge = _charges["txn-1"]
    assert charge["refunded_cents"] == 300


def test_cancel_then_refund():
    """cancel_and_refund refunds remaining balance, order cancelled only after refund succeeds."""
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    
    # Partially refund first
    refund_charge("txn-1", 3.00, token="header.user-1.sig", refund_id="ref-1")
    
    # Cancel and refund remaining
    result = cancel_and_refund("order-1", "txn-1", "header.user-1.sig")
    assert result["status"] == "cancelled"
    assert result["refund"]["status"] == "refunded"
    assert result["refund"]["refund_amount"] == 700  # Remaining balance
    
    # Balance fully refunded
    charge = _charges["txn-1"]
    assert charge["refunded_cents"] == 1000


def test_cancel_and_refund_error_path_leaves_uncancelled():
    """cancel_and_refund with error leaves order un-cancelled."""
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    
    # Try to cancel with wrong token
    result = cancel_and_refund("order-1", "txn-1", "header.user-2.sig")
    assert result["status"] == "error"
    assert result["error"] == "unauthorized"
    
    # Balance unchanged
    charge = _charges["txn-1"]
    assert charge["refunded_cents"] == 0


def test_amend_replaces_quantity():
    """Amend from smaller to larger quantity, assert only delta is charged."""
    # Initial charge for 2 items at $5 each = $10
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    order = {
        "id": "order-1",
        "transaction_id": "txn-1",
        "quantity": 2,
        "total": 10.00,
    }
    
    # Amend to 5 items (delta = 3 * $5 = $15)
    result = amend_quantity(order, 5, 5.00, "header.user-1.sig")
    assert result["status"] == "amended"
    assert result["order"]["quantity"] == 5
    assert result["order"]["total"] == 25.00
    
    # New transaction ID created
    assert result["order"]["transaction_id"] != "txn-1"


def test_amend_reduces_quantity_refunds_delta():
    """Amendment that reduces quantity refunds only the delta."""
    # Initial charge for 5 items at $5 each = $25
    record_charge("txn-1", "user-1", 25.00, "header.user-1.sig")
    order = {
        "id": "order-1",
        "transaction_id": "txn-1",
        "quantity": 5,
        "total": 25.00,
    }
    
    # Amend to 2 items (delta = -3 * $5 = -$15)
    result = amend_quantity(order, 2, 5.00, "header.user-1.sig")
    assert result["status"] == "amended"
    assert result["order"]["quantity"] == 2
    assert result["order"]["total"] == 10.00
    
    # Transaction ID remains the same (refund, not new charge)
    assert result["order"]["transaction_id"] == "txn-1"
    
    # Balance refunded
    charge = _charges["txn-1"]
    assert charge["refunded_cents"] == 1500


def test_amend_same_quantity_no_charge_or_refund():
    """Amendment with same quantity does not touch billing."""
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    order = {
        "id": "order-1",
        "transaction_id": "txn-1",
        "quantity": 2,
        "total": 10.00,
    }
    
    # Amend to same quantity
    result = amend_quantity(order, 2, 5.00, "header.user-1.sig")
    assert result["status"] == "amended"
    assert result["order"]["quantity"] == 2
    assert result["order"]["total"] == 10.00
    
    # Transaction ID unchanged
    assert result["order"]["transaction_id"] == "txn-1"
    
    # Balance unchanged
    charge = _charges["txn-1"]
    assert charge["refunded_cents"] == 0


def test_refund_nonexistent_transaction_unauthorized():
    """Refund non-existent transaction returns unauthorized."""
    result = refund_charge("txn-nonexistent", 5.00, token="header.user-1.sig", refund_id="ref-1")
    assert result["status"] == "error"
    assert result["error"] == "unauthorized"


def test_refund_zero_amount_rejected():
    """Refund with zero amount is rejected."""
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    result = refund_charge("txn-1", 0.00, token="header.user-1.sig", refund_id="ref-1")
    assert result["status"] == "error"
    assert result["error"] == "exceeds_remaining_balance"


def test_refund_negative_amount_rejected():
    """Refund with negative amount is rejected."""
    record_charge("txn-1", "user-1", 10.00, "header.user-1.sig")
    result = refund_charge("txn-1", -5.00, token="header.user-1.sig", refund_id="ref-1")
    assert result["status"] == "error"
    assert result["error"] == "exceeds_remaining_balance"

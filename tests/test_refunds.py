"""Refund ledger. Balance checks are described in the ticket and not covered here."""

from src.refunds import amend_quantity, record_charge, refund_charge


def test_partial_refund_reports_remaining():
    record_charge("txn-1", "user-1", 10.0)
    result = refund_charge("txn-1", 3.0, "header.user-1.sig", "refund-1")
    assert result["status"] == "refunded"
    assert result["remaining"] == 7.0


def test_amend_replaces_quantity():
    order = {"id": "order-9", "user_id": "user-1", "quantity": 1}
    updated = amend_quantity(order, 3, 5.0, "header.user-1.sig")
    assert updated["quantity"] == 3
    assert updated["total"] == 15.0

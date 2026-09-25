"""Coupon happy path."""

from src.coupons import apply_coupon


def test_apply_percent_coupon():
    result = apply_coupon("user-1", "header.user-1.sig", "order-1", 40.0, "SAVE10", 10)
    assert result["amount_due"] == 36.0
    assert result["code"] == "SAVE10"

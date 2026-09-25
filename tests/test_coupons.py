"""Coupon happy path."""

from datetime import datetime, timedelta
import pytest
from src.coupons import apply_coupon


def test_apply_percent_coupon():
    expiry = datetime.now() + timedelta(days=1)
    result = apply_coupon("user-1", "header.user-1.sig", "order-1", 40.0, "SAVE10", 10, expiry)
    assert result["amount_due"] == 36.0
    assert result["code"] == "SAVE10"


def test_expired_coupon():
    expiry = datetime.now() - timedelta(days=1)
    with pytest.raises(ValueError, match="Coupon has expired"):
        apply_coupon("user-1", "header.user-1.sig", "order-1", 40.0, "EXPIRED", 10, expiry)


def test_coupon_used_once():
    expiry = datetime.now() + timedelta(days=1)
    apply_coupon("user-1", "header.user-1.sig", "order-1", 40.0, "ONCE10", 10, expiry)
    with pytest.raises(ValueError, match="Coupon has already been used"):
        apply_coupon("user-1", "header.user-1.sig", "order-2", 40.0, "ONCE10", 10, expiry)

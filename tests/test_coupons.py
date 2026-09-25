"""Tests for coupon application."""

import pytest
from datetime import datetime, timedelta
from src.coupons import apply_coupon


def test_apply_percent_coupon():
    """Apply a percentage discount coupon."""
    result = apply_coupon(
        user_id="user-123",
        token="header.user-123.signature",
        order_id="order-1",
        total=40.0,
        code="SAVE10",
        percent=10,
    )
    assert result["order_id"] == "order-1"
    assert result["code"] == "SAVE10"
    assert result["discount"] == 4.0
    assert result["amount_due"] == 36.0
    assert result["transaction_id"] == "txn-456"


def test_expired_coupon():
    """Reject an expired coupon."""
    expired = datetime.now() - timedelta(days=1)
    with pytest.raises(ValueError, match="Coupon has expired"):
        apply_coupon(
            user_id="user-123",
            token="header.user-123.signature",
            order_id="order-1",
            total=40.0,
            code="EXPIRED",
            percent=10,
            expiry=expired,
        )


def test_coupon_used_once():
    """Coupon can be used once per order, but on different orders."""
    # First use on order-1 succeeds
    result1 = apply_coupon(
        user_id="user-123",
        token="header.user-123.signature",
        order_id="order-1",
        total=40.0,
        code="ONCE10",
        percent=10,
    )
    assert result1["order_id"] == "order-1"
    
    # Same order + same code raises
    with pytest.raises(ValueError, match="Coupon has already been used"):
        apply_coupon(
            user_id="user-123",
            token="header.user-123.signature",
            order_id="order-1",
            total=40.0,
            code="ONCE10",
            percent=10,
        )
    
    # Different order + same code succeeds
    result2 = apply_coupon(
        user_id="user-123",
        token="header.user-123.signature",
        order_id="order-2",
        total=50.0,
        code="ONCE10",
        percent=10,
    )
    assert result2["order_id"] == "order-2"
    assert result2["amount_due"] == 45.0


def test_empty_code():
    """Reject empty or blank coupon code."""
    with pytest.raises(ValueError, match="Coupon code is required"):
        apply_coupon(
            user_id="user-123",
            token="header.user-123.signature",
            order_id="order-1",
            total=40.0,
            code="",
            percent=10,
        )
    
    with pytest.raises(ValueError, match="Coupon code is required"):
        apply_coupon(
            user_id="user-123",
            token="header.user-123.signature",
            order_id="order-1",
            total=40.0,
            code="   ",
            percent=10,
        )


def test_percent_over_100():
    """Reject percentage coupon over 100%."""
    with pytest.raises(ValueError, match="Percentage coupon cannot exceed 100"):
        apply_coupon(
            user_id="user-123",
            token="header.user-123.signature",
            order_id="order-1",
            total=40.0,
            code="INVALID",
            percent=150,
        )


def test_fixed_over_total():
    """Reject fixed coupon larger than order total."""
    with pytest.raises(ValueError, match="Fixed coupon cannot exceed the order total"):
        apply_coupon(
            user_id="user-123",
            token="header.user-123.signature",
            order_id="order-1",
            total=40.0,
            code="TOOLARGE",
            fixed=200,
        )


def test_discount_larger_than_total():
    """Ensure discount cannot exceed total, amount_due is correct."""
    # Fixed discount equal to total is allowed
    result = apply_coupon(
        user_id="user-123",
        token="header.user-123.signature",
        order_id="order-3",
        total=40.0,
        code="FREE40",
        fixed=40.0,
    )
    assert result["discount"] == 40.0
    assert result["amount_due"] == 0.0
    assert result["transaction_id"] == "no-charge"
    
    # 100% discount is allowed
    result = apply_coupon(
        user_id="user-123",
        token="header.user-123.signature",
        order_id="order-4",
        total=50.0,
        code="FREE100",
        percent=100,
    )
    assert result["discount"] == 50.0
    assert result["amount_due"] == 0.0
    assert result["transaction_id"] == "no-charge"


def test_email_content(monkeypatch):
    """Email contains total, discount, paid, but not the coupon code."""
    captured_email = {}
    
    def mock_send_email(to, subject, body):
        captured_email["to"] = to
        captured_email["subject"] = subject
        captured_email["body"] = body
        return True
    
    monkeypatch.setattr("src.coupons.send_email", mock_send_email)
    
    apply_coupon(
        user_id="user-123",
        token="header.user-123.signature",
        order_id="order-5",
        total=100.0,
        code="SAVE10",
        percent=10,
    )
    
    body = captured_email["body"]
    assert "100.00" in body  # original total
    assert "10.00" in body   # discount
    assert "90.00" in body   # amount paid
    assert "SAVE10" not in body  # code must not be in email

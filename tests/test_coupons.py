"""Tests for coupon application."""

import pytest
from datetime import datetime, timedelta
from src.coupons import apply_coupon, _applied


def setup_function():
    """Clear applied coupons before each test."""
    _applied.clear()


def test_apply_percent_coupon():
    """A 10% coupon on $40.00 should discount $4.00."""
    result = apply_coupon(
        user_id="user-1",
        token="header.user1.signature",
        order_id="order-123",
        total=40.0,
        code="SAVE10",
        percent=10
    )
    assert result["order_id"] == "order-123"
    assert result["code"] == "SAVE10"
    assert result["discount"] == 4.0
    assert result["amount_due"] == 36.0
    assert result["transaction_id"] == "txn-456"


def test_expired_coupon():
    """An expired coupon should raise ValueError."""
    expired = datetime.now() - timedelta(days=1)
    with pytest.raises(ValueError, match="Coupon has expired"):
        apply_coupon(
            user_id="user-1",
            token="header.user1.signature",
            order_id="order-123",
            total=40.0,
            code="EXPIRED",
            percent=10,
            expiry=expired
        )


def test_coupon_used_once():
    """Same coupon code can only be used once per order, but multiple times across orders."""
    apply_coupon(
        user_id="user-1",
        token="header.user1.signature",
        order_id="order-1",
        total=40.0,
        code="ONCE10",
        percent=10
    )
    
    with pytest.raises(ValueError, match="Coupon has already been used"):
        apply_coupon(
            user_id="user-1",
            token="header.user1.signature",
            order_id="order-1",
            total=40.0,
            code="ONCE10",
            percent=10
        )
    
    result = apply_coupon(
        user_id="user-1",
        token="header.user1.signature",
        order_id="order-2",
        total=40.0,
        code="ONCE10",
        percent=10
    )
    assert result["order_id"] == "order-2"
    assert result["code"] == "ONCE10"


def test_empty_code():
    """Empty or blank coupon code should raise ValueError."""
    with pytest.raises(ValueError, match="Coupon code is required"):
        apply_coupon(
            user_id="user-1",
            token="header.user1.signature",
            order_id="order-123",
            total=40.0,
            code="",
            percent=10
        )
    
    with pytest.raises(ValueError, match="Coupon code is required"):
        apply_coupon(
            user_id="user-1",
            token="header.user1.signature",
            order_id="order-123",
            total=40.0,
            code="   ",
            percent=10
        )


def test_percent_over_100():
    """Percentage coupon over 100 should raise ValueError."""
    with pytest.raises(ValueError, match="Percentage coupon cannot exceed 100"):
        apply_coupon(
            user_id="user-1",
            token="header.user1.signature",
            order_id="order-123",
            total=40.0,
            code="HUGE",
            percent=150
        )


def test_fixed_over_total():
    """Fixed coupon exceeding order total should raise ValueError."""
    with pytest.raises(ValueError, match="Fixed coupon cannot exceed the order total"):
        apply_coupon(
            user_id="user-1",
            token="header.user1.signature",
            order_id="order-123",
            total=40.0,
            code="TOOBIG",
            fixed=200.0
        )


def test_discount_larger_than_total():
    """Discount cannot exceed the total, and amount_due equals total minus discount."""
    result = apply_coupon(
        user_id="user-1",
        token="header.user1.signature",
        order_id="order-123",
        total=50.0,
        code="BIG50",
        percent=50
    )
    assert result["discount"] == 25.0
    assert result["amount_due"] == 25.0
    assert result["amount_due"] == 50.0 - result["discount"]


def test_email_content_no_code(monkeypatch):
    """Email should contain total and amount paid, but not the coupon code."""
    sent_emails = []
    
    def mock_send_email(to, subject, body):
        sent_emails.append({"to": to, "subject": subject, "body": body})
        return True
    
    monkeypatch.setattr("src.coupons.send_email", mock_send_email)
    
    apply_coupon(
        user_id="user-1",
        token="header.user1.signature",
        order_id="order-123",
        total=40.0,
        code="SAVE10",
        percent=10
    )
    
    assert len(sent_emails) == 1
    body = sent_emails[0]["body"]
    assert "40.00" in body
    assert "36.00" in body
    assert "SAVE10" not in body

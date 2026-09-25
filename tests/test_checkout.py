"""Tests for checkout workflow."""

import pytest
from unittest.mock import patch, MagicMock
from src.checkout import checkout, release_reservation, _reservations


@pytest.fixture
def mock_user():
    """Mock user data."""
    return {
        "id": "user-1",
        "name": "Test User",
        "email": "test@example.com",
    }


@pytest.fixture
def valid_checkout_params():
    """Valid checkout parameters."""
    return {
        "user_id": "user-1",
        "token": "valid.token.here",
        "items": [{"id": "item-1", "name": "Product"}],
        "quantity": 1,
        "amount": 100.0,
        "currency": "USD",
        "card_number": "4111111111111111",
    }


def test_checkout_happy_path(mock_user, valid_checkout_params):
    """Test successful checkout workflow."""
    with patch("src.checkout.get_user", return_value=mock_user), \
         patch("src.checkout.place_hold", return_value={"hold_id": "hold-1"}), \
         patch("src.checkout.capture_hold", return_value={"transaction_id": "txn-1"}), \
         patch("src.checkout.create_order", return_value={"id": "order-1"}), \
         patch("src.checkout.send_email", return_value=True):
        
        result = checkout(**valid_checkout_params)
        
        assert result["status"] == "success"
        assert result["order_id"] == "order-1"
        assert result["transaction_id"] == "txn-1"
        assert result["amount"] == 100.0
        assert result["currency"] == "USD"


def test_checkout_empty_items_rejected(mock_user, valid_checkout_params):
    """Test that empty items list is rejected before charging."""
    valid_checkout_params["items"] = []
    
    with patch("src.checkout.get_user", return_value=mock_user) as mock_get_user, \
         patch("src.checkout.capture_hold") as mock_charge, \
         patch("src.checkout.send_email") as mock_email:
        
        result = checkout(**valid_checkout_params)
        
        assert result["status"] == "error"
        assert "non-empty list" in result["error"].lower()
        mock_charge.assert_not_called()
        mock_email.assert_not_called()


def test_checkout_none_items_rejected(mock_user, valid_checkout_params):
    """Test that None items is rejected before charging."""
    valid_checkout_params["items"] = None
    
    with patch("src.checkout.get_user", return_value=mock_user), \
         patch("src.checkout.capture_hold") as mock_charge, \
         patch("src.checkout.send_email") as mock_email:
        
        result = checkout(**valid_checkout_params)
        
        assert result["status"] == "error"
        assert "non-empty list" in result["error"].lower()
        mock_charge.assert_not_called()
        mock_email.assert_not_called()


@pytest.mark.parametrize("quantity", [0, -1, None, "invalid"])
def test_checkout_quantity_below_one_rejected(mock_user, valid_checkout_params, quantity):
    """Test that quantity < 1 or invalid is rejected before charging."""
    valid_checkout_params["quantity"] = quantity
    
    with patch("src.checkout.get_user", return_value=mock_user), \
         patch("src.checkout.place_hold") as mock_hold, \
         patch("src.checkout.capture_hold") as mock_charge, \
         patch("src.checkout.send_email") as mock_email:
        
        result = checkout(**valid_checkout_params)
        
        assert result["status"] == "error"
        assert "quantity" in result["error"].lower()
        mock_hold.assert_not_called()
        mock_charge.assert_not_called()
        mock_email.assert_not_called()


@pytest.mark.parametrize("currency", ["US", "USDD", "12A", "", None])
def test_checkout_invalid_currency_rejected(mock_user, valid_checkout_params, currency):
    """Test that invalid currency formats are rejected before charging."""
    valid_checkout_params["currency"] = currency
    
    with patch("src.checkout.get_user", return_value=mock_user), \
         patch("src.checkout.place_hold") as mock_hold, \
         patch("src.checkout.capture_hold") as mock_charge, \
         patch("src.checkout.send_email") as mock_email:
        
        result = checkout(**valid_checkout_params)
        
        assert result["status"] == "error"
        assert "currency" in result["error"].lower()
        mock_hold.assert_not_called()
        mock_charge.assert_not_called()
        mock_email.assert_not_called()


def test_checkout_double_submit_same_key_charges_once(mock_user, valid_checkout_params):
    """Test that same idempotency key charges only once."""
    valid_checkout_params["idempotency_key"] = "unique-key-123"
    
    with patch("src.checkout.get_user", return_value=mock_user), \
         patch("src.checkout.place_hold", return_value={"hold_id": "hold-1"}) as mock_hold, \
         patch("src.checkout.capture_hold", return_value={"transaction_id": "txn-1"}) as mock_charge, \
         patch("src.checkout.create_order", return_value={"id": "order-1"}), \
         patch("src.checkout.send_email", return_value=True) as mock_email:
        
        # First call
        result1 = checkout(**valid_checkout_params)
        
        # Second call with same key
        result2 = checkout(**valid_checkout_params)
        
        # Both results should be identical
        assert result1 == result2
        assert result1["status"] == "success"
        
        # But charge should only happen once
        assert mock_hold.call_count == 1
        assert mock_charge.call_count == 1
        assert mock_email.call_count == 1


def test_checkout_charge_failure_releases_reservation(mock_user, valid_checkout_params):
    """Test that charge failure releases reservation and doesn't send receipt."""
    with patch("src.checkout.get_user", return_value=mock_user), \
         patch("src.checkout.place_hold", return_value={"hold_id": "hold-1"}), \
         patch("src.checkout.capture_hold", side_effect=Exception("Payment declined")) as mock_charge, \
         patch("src.checkout.send_email") as mock_email:
        
        result = checkout(**valid_checkout_params)
        
        assert result["status"] == "error"
        assert "charge failed" in result["error"].lower()
        mock_email.assert_not_called()
        
        # Check reservation was released
        # Note: we need to inspect the internal reservation state
        # The reservation should be marked as released
        reservations = [r for r in _reservations.values() if r["user_id"] == "user-1"]
        assert len(reservations) > 0
        assert reservations[-1]["released"] is True


def test_checkout_receipt_failure_refunds_and_releases(mock_user, valid_checkout_params):
    """Test that receipt failure triggers refund and releases reservation."""
    with patch("src.checkout.get_user", return_value=mock_user), \
         patch("src.checkout.place_hold", return_value={"hold_id": "hold-1"}), \
         patch("src.checkout.capture_hold", return_value={"transaction_id": "txn-789"}) as mock_charge, \
         patch("src.checkout.create_order", return_value={"id": "order-1"}), \
         patch("src.checkout.send_email", side_effect=Exception("Email service down")) as mock_email, \
         patch("src.checkout.refund") as mock_refund:
        
        result = checkout(**valid_checkout_params)
        
        assert result["status"] == "error"
        assert "receipt" in result["error"].lower()
        assert "refunded" in result["error"].lower()
        
        # Verify refund was called with correct transaction_id
        mock_refund.assert_called_once_with("txn-789", 100.0)
        
        # Check reservation was released
        reservations = [r for r in _reservations.values() if r["user_id"] == "user-1"]
        assert len(reservations) > 0
        assert reservations[-1]["released"] is True


def test_receipt_excludes_card_number(mock_user, valid_checkout_params):
    """Test that card number is not included in receipt email."""
    card_num = "4111111111111111"
    valid_checkout_params["card_number"] = card_num
    
    captured_email_args = {}
    
    def capture_send_email(to, subject, body):
        captured_email_args["to"] = to
        captured_email_args["subject"] = subject
        captured_email_args["body"] = body
        return True
    
    with patch("src.checkout.get_user", return_value=mock_user), \
         patch("src.checkout.place_hold", return_value={"hold_id": "hold-1"}), \
         patch("src.checkout.capture_hold", return_value={"transaction_id": "txn-1"}), \
         patch("src.checkout.create_order", return_value={"id": "order-1"}), \
         patch("src.checkout.send_email", side_effect=capture_send_email):
        
        result = checkout(**valid_checkout_params)
        
        assert result["status"] == "success"
        
        # Verify card number is not in any email field
        assert card_num not in captured_email_args["to"]
        assert card_num not in captured_email_args["subject"]
        assert card_num not in captured_email_args["body"]


def test_release_reservation_idempotent():
    """Test that release_reservation is idempotent."""
    from src.checkout import _reservations, _reservation_lock
    
    with _reservation_lock:
        _reservations["test-rsv"] = {
            "id": "test-rsv",
            "user_id": "user-1",
            "released": False,
        }
    
    # First release
    release_reservation("test-rsv")
    assert _reservations["test-rsv"]["released"] is True
    
    # Second release - should not error
    release_reservation("test-rsv")
    assert _reservations["test-rsv"]["released"] is True
    
    # Unknown reservation - should not error
    release_reservation("unknown-rsv")

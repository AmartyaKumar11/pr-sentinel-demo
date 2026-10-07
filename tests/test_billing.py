import pytest

from src.billing import charge, refund


def test_charge_rejects_a_non_positive_amount():
    with pytest.raises(ValueError):
        charge("user-1", "token", 0)


def test_refund_rejects_a_non_positive_amount():
    with pytest.raises(ValueError):
        refund("txn-456", -5)


def test_refund_rejects_a_missing_transaction():
    with pytest.raises(ValueError):
        refund("", 10)


def test_refund_returns_the_amount():
    result = refund("txn-456", 10)
    assert result["status"] == "refunded"
    assert result["refund_amount"] == 10

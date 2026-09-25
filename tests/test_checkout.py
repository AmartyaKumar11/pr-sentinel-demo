"""Checkout coverage. Happy path only — failure cases still to do."""

from src.checkout import checkout


def test_checkout_happy_path():
    order = checkout(
        "user-1",
        "header.user-1.sig",
        [{"sku": "book", "qty": 1}],
        1,
        19.99,
        "USD",
        "4242424242424242",
        "key-1",
    )
    assert order["status"] == "created"
    assert order["transaction_id"]
    assert "4242" not in str(order)

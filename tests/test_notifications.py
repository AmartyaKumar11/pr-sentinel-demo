from unittest.mock import patch

import pytest

from src.notifications import send_email


def test_send_email_recipient_and_raw_token_reach_transport():
    raw_token = "raw-reset-token-abc"
    body = f"Reset your password: https://example.com/reset?token={raw_token}"

    with patch("src.notifications._deliver_email", return_value=True) as mock_transport:
        result = send_email("user@example.com", "Password Reset", body)

    assert result is True
    mock_transport.assert_called_once_with(
        "user@example.com",
        "Password Reset",
        body,
    )
    assert mock_transport.call_args[0][0] == "user@example.com"
    assert raw_token in mock_transport.call_args[0][2]


def test_send_email_transport_failure_is_surfaced():
    with patch(
        "src.notifications._deliver_email",
        side_effect=RuntimeError("SMTP unavailable"),
    ):
        with pytest.raises(RuntimeError, match="SMTP unavailable"):
            send_email("user@example.com", "Password Reset", "body with token")

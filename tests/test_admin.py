from unittest.mock import patch

import base64
import json
import time

from src.admin import audit_log, dashboard


def _make_valid_token():
    """Helper to create a valid token with proper exp claim."""
    payload = {"exp": time.time() + 3600}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    return f"header.{payload_b64}.signature"


def test_dashboard_returns_expected_metrics():
    result = dashboard(_make_valid_token())
    assert result == {
        "total_users": 1000,
        "total_orders": 5000,
        "revenue": 250000.00,
    }


def test_dashboard_rejects_invalid_token():
    try:
        dashboard("")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for invalid admin token")


@patch("src.admin.check_permissions")
@patch("src.admin.validate_token")
def test_dashboard_validates_token_and_permissions(mock_validate, mock_check):
    token = "admin-token-xyz"
    mock_validate.return_value = {"valid": True}

    result = dashboard(token)

    mock_validate.assert_called_once_with(token)
    mock_check.assert_called_once_with("admin", "dashboard:read")
    assert result["total_users"] == 1000


def test_audit_log_records_action():
    action = "user.suspend"
    details = "Suspended user user-42 for policy violation"
    result = audit_log(_make_valid_token(), action, details)
    assert result["action"] == action
    assert result["details"] == details
    assert result["timestamp"] == "2026-08-20T00:00:00Z"


def test_audit_log_rejects_invalid_token():
    try:
        audit_log("", "user.suspend", "details")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for invalid admin token")


@patch("src.admin.validate_token")
def test_audit_log_validates_token(mock_validate):
    token = "admin-token-xyz"
    mock_validate.return_value = {"valid": True}

    result = audit_log(token, "settings.update", "Changed retention policy")

    mock_validate.assert_called_once_with(token)
    assert result["action"] == "settings.update"
    assert result["details"] == "Changed retention policy"

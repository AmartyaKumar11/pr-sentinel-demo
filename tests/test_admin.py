import base64
import json
import time
from unittest.mock import patch

import pytest

from src.admin import audit_log, dashboard


def _make_valid_token():
    """Helper to create a valid token with proper exp claim."""
    payload = {"exp": time.time() + 3600}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    return f"header.{payload_b64}.signature"


def test_dashboard_returns_metrics_with_valid_token():
    token = _make_valid_token()
    result = dashboard(token)
    assert result == {
        "total_users": 1000,
        "total_orders": 5000,
        "revenue": 250000.00,
    }


def test_dashboard_rejects_invalid_token():
    with patch("src.admin.check_permissions") as mock_perms:
        with pytest.raises(ValueError):
            dashboard("")
        mock_perms.assert_not_called()


def test_dashboard_rejects_expired_token():
    payload = {"exp": time.time() - 3600}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    token = f"header.{payload_b64}.signature"

    with patch("src.admin.check_permissions") as mock_perms:
        with pytest.raises(ValueError) as exc_info:
            dashboard(token)
        assert "expired" in str(exc_info.value).lower()
        mock_perms.assert_not_called()


def test_dashboard_calls_permission_check_for_admin_dashboard_read():
    token = _make_valid_token()
    with patch("src.admin.validate_token") as mock_validate:
        mock_validate.return_value = {"valid": True, "user_id": "admin"}
        with patch("src.admin.check_permissions") as mock_perms:
            mock_perms.return_value = True
            dashboard(token)

        mock_validate.assert_called_once_with(token)
        mock_perms.assert_called_once_with("admin", "dashboard:read")


def test_dashboard_propagates_permission_denial():
    token = _make_valid_token()
    with patch("src.admin.validate_token") as mock_validate:
        mock_validate.return_value = {"valid": True}
        with patch("src.admin.check_permissions") as mock_perms:
            mock_perms.side_effect = ValueError("permission denied")
            with pytest.raises(ValueError, match="permission denied"):
                dashboard(token)


def test_audit_log_returns_action_details_and_timestamp():
    token = _make_valid_token()
    result = audit_log(token, "user.suspend", "Suspended user 42 for policy violation")
    assert result["action"] == "user.suspend"
    assert result["details"] == "Suspended user 42 for policy violation"
    assert result["timestamp"] == "2026-08-20T00:00:00Z"


def test_audit_log_does_not_require_dashboard_permission():
    token = _make_valid_token()
    with patch("src.admin.check_permissions") as mock_perms:
        result = audit_log(token, "config.update", "Changed maintenance window")
        assert result["action"] == "config.update"
        mock_perms.assert_not_called()


def test_audit_log_rejects_invalid_token():
    with pytest.raises(ValueError):
        audit_log("", "login", "Admin signed in")


def test_audit_log_preserves_empty_action_and_details():
    token = _make_valid_token()
    result = audit_log(token, "", "")
    assert result["action"] == ""
    assert result["details"] == ""
    assert "timestamp" in result


def test_audit_log_validates_token_before_building_record():
    token = _make_valid_token()
    with patch("src.admin.validate_token") as mock_validate:
        mock_validate.side_effect = ValueError("invalid token")
        with pytest.raises(ValueError, match="invalid token"):
            audit_log(token, "export", "Exported billing report")
        mock_validate.assert_called_once_with(token)

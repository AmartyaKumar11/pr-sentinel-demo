"""Tests for the admin dashboard module (src/admin.py)."""

import base64
import json
import time
from unittest.mock import patch

import pytest

from src.admin import audit_log, dashboard


def _valid_token(*, exp: int | None = None) -> str:
    """Build a token that passes src.auth.validate_token."""
    if exp is None:
        exp = int(time.time()) + 3600
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
    payload = (
        base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode())
        .decode()
        .rstrip("=")
    )
    signature = "abcdefgh"
    return f"{header}.{payload}.{signature}"


class TestDashboard:
    def test_returns_dashboard_metrics(self):
        token = _valid_token()
        result = dashboard(token)

        assert result == {
            "total_users": 1000,
            "total_orders": 5000,
            "revenue": 250000.00,
        }

    def test_rejects_invalid_token(self):
        with pytest.raises(ValueError, match="Invalid token"):
            dashboard("")

    def test_rejects_expired_token(self):
        token = _valid_token(exp=int(time.time()) - 60)
        with pytest.raises(ValueError, match="Token expired"):
            dashboard(token)

    @patch("src.admin.check_permissions")
    def test_checks_dashboard_read_permission(self, mock_check_permissions):
        token = _valid_token()
        dashboard(token)
        mock_check_permissions.assert_called_once_with("admin", "dashboard:read")

    @patch("src.admin.check_permissions", side_effect=ValueError("resource is required"))
    def test_permission_failure_propagates(self, _mock_check_permissions):
        with pytest.raises(ValueError, match="resource is required"):
            dashboard(_valid_token())


class TestAuditLog:
    def test_returns_logged_action(self):
        token = _valid_token()
        result = audit_log(token, "user_suspend", "Suspended user 42")

        assert result == {
            "action": "user_suspend",
            "details": "Suspended user 42",
            "timestamp": "2026-08-20T00:00:00Z",
        }

    def test_rejects_invalid_token(self):
        with pytest.raises(ValueError, match="Invalid token"):
            audit_log("short.bad", "x", "y")

    @patch("src.admin.validate_token")
    def test_validates_token_before_logging(self, mock_validate_token):
        mock_validate_token.return_value = {"user_id": "x", "valid": True}
        audit_log("any-token", "delete", "removed item")

        mock_validate_token.assert_called_once_with("any-token")

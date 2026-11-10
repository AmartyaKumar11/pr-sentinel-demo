"""Tests for src.admin — admin dashboard and audit log helpers."""

import base64
import json
import time
from unittest.mock import patch

import src.admin 


def _make_valid_token(exp_offset=3600):
    """Helper to create a valid token with proper exp claim."""
    payload = {"exp": time.time() + exp_offset}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    return f"header.{payload_b64}.signature"


def test_dashboard_returns_expected_metrics():
    token = _make_valid_token()
    result = src.admin.dashboard(token)
    assert result["total_users"] == 1000
    assert result["total_orders"] == 5000
    assert result["revenue"] == 250000.00


def test_dashboard_validates_token_and_permissions():
    token = _make_valid_token()
    with patch("src.admin.validate_token") as mock_validate, patch(
        "src.admin.check_permissions"
    ) as mock_check:
        src.admin.dashboard(token)
        mock_validate.assert_called_once_with(token)
        mock_check.assert_called_once_with("admin", "dashboard:read")


def test_dashboard_rejects_invalid_token():
    try:
        src.admin.dashboard("")
        assert False, "Expected ValueError for invalid token"
    except ValueError as e:
        assert "invalid" in str(e).lower()


def test_audit_log_returns_action_record():
    token = _make_valid_token()
    result = src.admin.audit_log(token, "order.refund", "refunded order #99")
    assert result["action"] == "order.refund"
    assert result["details"] == "refunded order #99"
    assert result["timestamp"] == "2026-08-20T00:00:00Z"


def test_audit_log_validates_token():
    token = _make_valid_token()
    with patch("src.admin.validate_token") as mock_validate:
        src.admin.audit_log(token, "user.view", "viewed profile")
        mock_validate.assert_called_once_with(token)


def test_audit_log_rejects_invalid_token():
    try:
        src.admin.audit_log("short", "user.view", "x")
        assert False, "Expected ValueError for invalid token"
    except ValueError as e:
        assert "invalid" in str(e).lower()

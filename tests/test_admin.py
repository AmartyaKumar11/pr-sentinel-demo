"""Tests for the admin dashboard module (src/admin.py)."""

import base64
import json
import time

import pytest

from src.admin import audit_log, dashboard


def make_valid_token(user_id="userid123", exp_offset=3600):
    """Build a JWT-like token with a base64url JSON payload."""
    payload = {"exp": time.time() + exp_offset}
    if user_id is not None:
        payload["sub"] = user_id
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    return f"header.{payload_b64}.signature"


@pytest.fixture
def admin_token():
    return make_valid_token()


class TestDashboard:
    def test_returns_dashboard_metrics(self, admin_token):
        result = dashboard(admin_token)

        assert result == {
            "total_users": 1000,
            "total_orders": 5000,
            "revenue": 250000.00,
        }

    def test_validate_token_receives_admin_token(self, admin_token, monkeypatch):
        seen = {}

        def fake_validate(token):
            seen["token"] = token
            return {"valid": True, "user_id": "admin"}

        monkeypatch.setattr("src.admin.validate_token", fake_validate)
        dashboard(admin_token)
        assert seen["token"] == admin_token

    def test_check_permissions_admin_dashboard_read(self, admin_token, monkeypatch):
        seen = {}

        def fake_check(user_id, resource):
            seen["user_id"] = user_id
            seen["resource"] = resource
            return True

        monkeypatch.setattr("src.admin.check_permissions", fake_check)
        dashboard(admin_token)
        assert seen == {"user_id": "admin", "resource": "dashboard:read"}

    @pytest.mark.parametrize(
        "token",
        [
            "",
            "not.three.parts",
            "header.payload",
            make_valid_token(exp_offset=-60),
        ],
        ids=["empty", "wrong_parts", "missing_signature", "expired"],
    )
    def test_rejects_invalid_token(self, token):
        with pytest.raises(ValueError):
            dashboard(token)

    def test_propagates_permission_denial(self, admin_token, monkeypatch):
        def deny(*_args, **_kwargs):
            raise ValueError("forbidden")

        monkeypatch.setattr("src.admin.check_permissions", deny)
        with pytest.raises(ValueError, match="forbidden"):
            dashboard(admin_token)


class TestAuditLog:
    @pytest.mark.parametrize(
        "action,details",
        [
            ("user.delete", "deleted user 42"),
            ("order.refund", "refunded order #1001"),
            ("settings.update", "changed billing email"),
        ],
    )
    def test_records_action_and_details(self, admin_token, action, details):
        result = audit_log(admin_token, action, details)

        assert result["action"] == action
        assert result["details"] == details
        assert result["timestamp"] == "2026-08-20T00:00:00Z"

    def test_validate_token_receives_admin_token(self, admin_token, monkeypatch):
        seen = {}

        def fake_validate(token):
            seen["token"] = token
            return {"valid": True}

        monkeypatch.setattr("src.admin.validate_token", fake_validate)
        audit_log(admin_token, "login", "admin signed in")
        assert seen["token"] == admin_token

    def test_does_not_call_check_permissions(self, admin_token, monkeypatch):
        def should_not_run(*_args, **_kwargs):
            raise AssertionError("audit_log must not check permissions")

        monkeypatch.setattr("src.admin.check_permissions", should_not_run)
        result = audit_log(admin_token, "export", "csv download")
        assert result["action"] == "export"

    @pytest.mark.parametrize(
        "token",
        ["", make_valid_token(exp_offset=-1)],
        ids=["empty", "expired"],
    )
    def test_rejects_invalid_token(self, token):
        with pytest.raises(ValueError):
            audit_log(token, "noop", "should not run")

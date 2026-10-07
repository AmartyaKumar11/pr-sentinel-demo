from src.users import get_user, create_user, update_profile, deactivate_user

import src.users as users
import base64
import json
import time


def _make_valid_token():
    """Helper to create a valid token with proper exp claim."""
    payload = {"exp": time.time() + 3600}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    return f"header.{payload_b64}.signature"


def test_get_user():
    user = get_user("123", _make_valid_token())
    assert user["id"] == "123"

def test_create_user():
    user = create_user("Test", "test@example.com", "password123")
    assert user["name"] == "Test"
    assert "password_hash" in user

def test_get_user_status_removed():
    """Verify get_user_status was removed from src.users."""
    assert not hasattr(users, "get_user_status")

def test_update_profile_still_works():
    """Ensure update_profile still works after removal."""
    token = _make_valid_token()
    updates = {"name": "Updated Name", "email": "new@example.com"}
    result = update_profile("123", token, updates)
    assert result["id"] == "123"
    assert result["name"] == "Updated Name"
    assert result["email"] == "new@example.com"


def test_deactivate_user():
    result = deactivate_user("123", _make_valid_token())
    assert result["id"] == "123"
    assert result["status"] == "deactivated"

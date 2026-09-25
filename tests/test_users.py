from src.users import get_user, create_user, update_profile, deactivate_user

def test_get_user():
    user = get_user("123", "header.123.signature")
    assert user["id"] == "123"

def test_create_user():
    user = create_user("Test", "test@example.com", "password123")
    assert user["name"] == "Test"
    assert "password_hash" in user

def test_update_profile():
    updated = update_profile("123", "header.123.signature", {"name": "Updated Name"})
    assert updated["id"] == "123"
    assert updated["name"] == "Updated Name"

def test_deactivate_user():
    user = deactivate_user("123", "header.123.signature")
    assert user["id"] == "123"
    assert user["status"] == "deactivated"


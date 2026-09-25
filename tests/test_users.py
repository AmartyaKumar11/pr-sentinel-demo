from src.users import get_user, create_user, get_user_status 

def test_get_user():
    user = get_user("123", "header.123.signature")
    assert user["id"] == "123"

def test_create_user():
    user = create_user("Test", "test@example.com", "password123")
    assert user["name"] == "Test"
    assert "password_hash" in user

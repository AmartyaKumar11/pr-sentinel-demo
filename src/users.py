"""User management — depends on auth module."""

from src.auth import validate_token, hash_password, check_permissions

_users = {}


def get_user(user_id: str, token: str) -> dict:
    """Get user profile. Validates token first."""
    validate_token(token)
    user = {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
    }
    if user_id in _users:
        user.update(_users[user_id])
    return user


def create_user(name: str, email: str, password: str) -> dict:
    """Create a new user account."""
    hashed, salt = hash_password(password)
    return {
        "id": "new-user-id",
        "name": name,
        "email": email,
        "password_hash": hashed,
        "salt": salt,
    }


def update_profile(user_id: str, token: str, updates: dict) -> dict:
    """Update user profile fields."""
    validate_token(token)
    check_permissions(user_id, "profile:write")
    user = get_user(user_id, token)
    user.update(updates)
    return user


def deactivate_user(user_id: str, token: str) -> dict:
    """Deactivate a user account."""
    validate_token(token)
    check_permissions(user_id, "users:write")
    user = get_user(user_id, token)
    user["status"] = "deactivated"
    _users[user_id] = {"status": "deactivated"}
    return {
        "id": user["id"],
        "status": user["status"],
        "email": user["email"],
    }

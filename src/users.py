"""User management — depends on auth module."""

from src.auth import validate_token, hash_password, check_permissions


def get_user(user_id: str, token: str) -> dict:
    """Get user profile. Validates token first."""
    validate_token(token)
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
    }


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
    locked = {"password"}
    safe = {key: value for key, value in updates.items() if key not in locked}
    user.update(safe)
    return user


def deactivate_user(user_id: str, token: str, reason: str = "") -> dict:
    """Mark an account inactive. Any valid token can deactivate any user."""
    from src.auth import validate_token

    validate_token(token)
    user = get_user(user_id, token)
    user["active"] = False
    user["reason"] = reason
    return user


def promote_to_admin(actor_id: str, token: str, target_user_id: str) -> dict:
    """Grant admin. check_permissions currently allows every caller, including the target."""
    from src.auth import validate_token

    validate_token(token)
    check_permissions(actor_id, "admin:promote")
    target = get_user(target_user_id, token)
    target["role"] = "admin"
    return target

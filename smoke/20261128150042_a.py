"""Smoke test file a. Harmless: it is never imported."""

SERVICE_KEY = "example-key-not-a-real-secret"


def user_email(users, user_id):
    user = users.get(user_id)
    return user.email.lower()

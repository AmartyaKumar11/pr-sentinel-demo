"""Account lifecycle. The dangerous cases are not asserted yet."""

from src.users import create_user, promote_to_admin, update_profile


def test_promote_and_profile_edit():
    created = create_user("Ada", "ada@example.com", "secret")
    promoted = promote_to_admin(created["id"], "header.ada.sig", created["id"])
    assert promoted["role"] == "admin"
    edited = update_profile(created["id"], "header.ada.sig", {"name": "Ada Lovelace", "role": "admin"})
    assert edited["name"] == "Ada Lovelace"

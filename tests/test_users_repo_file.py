# tests/test_users_repo_file.py
from pathlib import Path

from users_repo_file import (
    ensure_auth_store,
    load_users,
    list_users,
    get_user_by_email,
    create_user,
    update_user,
    delete_user,
)


def test_ensure_auth_store_creates_files(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    ensure_auth_store()

    assert (tmp_path / "data" / "auth" / "users.json").exists()
    assert (tmp_path / "data" / "auth" / "roles.json").exists()

    payload = load_users()
    assert payload["version"] == 1
    assert payload["users"] == []


def test_create_and_get_user(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_auth_store()

    u = create_user(
        email="ANA.RRHH@empresa.com",
        password_hash="$2b$12$FAKE_HASH",
        roles=["employee"],
        department="rrhh",
    )

    assert u["id"]
    assert u["email"] == "ana.rrhh@empresa.com"

    got = get_user_by_email("ana.rrhh@empresa.com")
    assert got is not None
    assert got["id"] == u["id"]


def test_duplicate_email_raises(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_auth_store()

    create_user(
        email="admin@empresa.com",
        password_hash="$2b$12$FAKE_HASH",
        roles=["admin"],
        department="it",
    )

    try:
        create_user(
            email="ADMIN@empresa.com",
            password_hash="$2b$12$FAKE_HASH",
            roles=["admin"],
            department="it",
        )
        assert False, "Expected ValueError for duplicate email"
    except ValueError:
        assert True


def test_update_user(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_auth_store()

    u = create_user(
        email="user@empresa.com",
        password_hash="$2b$12$FAKE_HASH",
        roles=["employee"],
        department="comercial",
    )

    u2 = update_user(u["id"], {"roles": ["power_user"], "department": "comercial", "is_active": False})
    assert u2["roles"] == ["power_user"]
    assert u2["is_active"] is False


def test_list_users_sorted(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_auth_store()

    create_user("b@empresa.com", "$2b$12$FAKE", ["employee"], "it")
    create_user("a@empresa.com", "$2b$12$FAKE", ["employee"], "it")

    users = list_users()
    assert [u["email"] for u in users] == ["a@empresa.com", "b@empresa.com"]


def test_delete_user(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_auth_store()

    u = create_user("del@empresa.com", "$2b$12$FAKE", ["employee"], "it")
    delete_user(u["id"])

    assert get_user_by_email("del@empresa.com") is None

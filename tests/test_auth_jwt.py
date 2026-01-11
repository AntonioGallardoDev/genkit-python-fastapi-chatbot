# tests/test_auth_jwt.py
import os
import json
import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from auth_passwords import hash_password


def _headers():
    return {"X-API-Key": os.environ["API_KEY"]}


def _write_runtime_auth_store(tmp_path: Path):
    auth_dir = tmp_path / "data" / "auth"
    auth_dir.mkdir(parents=True, exist_ok=True)

    # roles runtime
    (auth_dir / "roles.json").write_text(
        json.dumps(
            {
                "version": 1,
                "roles": {
                    "admin": {"description": "Admin", "permissions": ["*"]},
                    "employee": {"description": "Employee", "permissions": ["chat:write", "rag:query"]},
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # users runtime
    pwd_hash = hash_password("Password123!")
    (auth_dir / "users.json").write_text(
        json.dumps(
            {
                "version": 1,
                "users": [
                    {
                        "id": "u1" * 16,  # 32 chars
                        "email": "admin@empresa.com",
                        "password_hash": pwd_hash,
                        "roles": ["admin"],
                        "department": "it",
                        "is_active": True,
                        "created_at": "2025-01-01T00:00:00Z",
                        "updated_at": "2025-01-01T00:00:00Z",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_login_and_me(tmp_path: Path, monkeypatch):
    # variables antes de importar api.py
    os.environ["API_KEY"] = "test-key-123"
    os.environ["JWT_SECRET"] = "super-secret-for-tests"
    os.environ["JWT_TTL_MINUTES"] = "60"

    monkeypatch.chdir(tmp_path)
    _write_runtime_auth_store(tmp_path)

    # Import dinámico para que lea env vars
    import api
    importlib.reload(api)

    client = TestClient(api.app)

    # login
    r = client.post(
        "/auth/login",
        headers=_headers(),
        json={"email": "admin@empresa.com", "password": "Password123!"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token

    # me
    r2 = client.get("/me", headers={**_headers(), "Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    me = r2.json()
    assert me["email"] == "admin@empresa.com"
    assert "password_hash" not in me
    assert me["roles"] == ["admin"]


def test_login_rejects_wrong_password(tmp_path: Path, monkeypatch):
    os.environ["API_KEY"] = "test-key-123"
    os.environ["JWT_SECRET"] = "super-secret-for-tests"
    monkeypatch.chdir(tmp_path)
    _write_runtime_auth_store(tmp_path)

    import api
    importlib.reload(api)

    client = TestClient(api.app)
    r = client.post(
        "/auth/login",
        headers=_headers(),
        json={"email": "admin@empresa.com", "password": "wrong"},
    )
    assert r.status_code == 401

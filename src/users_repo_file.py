# src/users_repo_file.py
from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ----------------------------
# Helpers
# ----------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_user_id() -> str:
    # UUID hex (consistente con tu estilo de session_id)
    return uuid.uuid4().hex


def _project_root() -> Path:
    # Igual que en memory_json: basado en cwd del proceso/test
    return Path.cwd()


def _default_auth_dir() -> Path:
    return _project_root() / "data" / "auth"


def _users_file(auth_dir: Optional[Path] = None) -> Path:
    d = auth_dir or _default_auth_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "users.json"


def _roles_file(auth_dir: Optional[Path] = None) -> Path:
    d = auth_dir or _default_auth_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "roles.json"


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # atómico en Windows


# Locks por ruta de fichero (thread-safe en FastAPI)
_LOCKS: Dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.RLock()


def _get_lock(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _LOCKS_GUARD:
        lock = _LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _LOCKS[key] = lock
        return lock


# ----------------------------
# Validación ligera (MVP)
# ----------------------------

_ALLOWED_DEPARTMENTS = {"rrhh", "finanzas", "operaciones", "comercial", "it", "global"}


def _validate_user_record(user: Dict[str, Any]) -> None:
    # Validación mínima para no romper el runtime.
    for k in ("id", "email", "password_hash", "roles", "department", "is_active"):
        if k not in user:
            raise ValueError(f"Missing field '{k}' in user record")

    if not isinstance(user["roles"], list) or not all(isinstance(r, str) for r in user["roles"]):
        raise ValueError("Field 'roles' must be a list[str]")

    dept = user["department"]
    if dept not in _ALLOWED_DEPARTMENTS:
        raise ValueError(f"Invalid department '{dept}'. Allowed: {sorted(_ALLOWED_DEPARTMENTS)}")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _load_or_init_json(path: Path, default_payload: Dict[str, Any]) -> Dict[str, Any]:
    lock = _get_lock(path)
    with lock:
        if not path.exists():
            _atomic_write_json(path, default_payload)
            return default_payload

        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            # Si el fichero existe pero está vacío, lo inicializamos (te pasó con example.json vacíos)
            _atomic_write_json(path, default_payload)
            return default_payload

        return json.loads(raw)


# ----------------------------
# Public API (repo)
# ----------------------------

def ensure_auth_store(auth_dir: Optional[Path] = None) -> None:
    """
    Garantiza que existen users.json y roles.json (mínimos).
    No pisa contenido existente (salvo ficheros vacíos).
    """
    u = _users_file(auth_dir)
    r = _roles_file(auth_dir)

    _load_or_init_json(u, {"version": 1, "users": []})
    _load_or_init_json(r, {"version": 1, "roles": {}})


def load_users(auth_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Devuelve el payload completo: {"version": 1, "users": [...]}
    """
    path = _users_file(auth_dir)
    payload = _load_or_init_json(path, {"version": 1, "users": []})
    if "users" not in payload or not isinstance(payload["users"], list):
        raise ValueError("Invalid users.json format: missing 'users' list")
    return payload


def save_users(payload: Dict[str, Any], auth_dir: Optional[Path] = None) -> None:
    """
    Guarda el payload completo de usuarios de forma atómica.
    """
    path = _users_file(auth_dir)
    lock = _get_lock(path)
    with lock:
        _atomic_write_json(path, payload)


def list_users(auth_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    payload = load_users(auth_dir)
    # orden estable por email
    return sorted(payload["users"], key=lambda u: _normalize_email(u.get("email", "")))


def get_user_by_email(email: str, auth_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    email_n = _normalize_email(email)
    payload = load_users(auth_dir)
    for u in payload["users"]:
        if _normalize_email(u.get("email", "")) == email_n:
            return u
    return None


def get_user_by_id(user_id: str, auth_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    payload = load_users(auth_dir)
    for u in payload["users"]:
        if u.get("id") == user_id:
            return u
    return None


def create_user(
    email: str,
    password_hash: str,
    roles: List[str],
    department: str,
    is_active: bool = True,
    auth_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crea usuario con validación mínima y persistencia atómica.
    OJO: aquí recibimos password_hash ya calculado (hashing vendrá en Paso 3).
    """
    path = _users_file(auth_dir)
    lock = _get_lock(path)

    with lock:
        payload = _load_or_init_json(path, {"version": 1, "users": []})

        email_n = _normalize_email(email)
        if any(_normalize_email(u.get("email", "")) == email_n for u in payload["users"]):
            raise ValueError(f"User with email '{email_n}' already exists")

        user = {
            "id": new_user_id(),
            "email": email_n,
            "password_hash": password_hash,
            "roles": roles,
            "department": department,
            "is_active": is_active,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }

        _validate_user_record(user)
        payload["users"].append(user)
        _atomic_write_json(path, payload)
        return user


def update_user(
    user_id: str,
    patch: Dict[str, Any],
    auth_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Actualiza campos permitidos. Persistencia atómica.
    Campos típicos: roles, department, is_active, password_hash
    """
    allowed = {"email", "password_hash", "roles", "department", "is_active"}

    path = _users_file(auth_dir)
    lock = _get_lock(path)

    with lock:
        payload = _load_or_init_json(path, {"version": 1, "users": []})
        users = payload["users"]

        idx = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        if idx is None:
            raise ValueError(f"User '{user_id}' not found")

        user = dict(users[idx])

        for k, v in patch.items():
            if k not in allowed:
                raise ValueError(f"Field '{k}' cannot be updated")
            if k == "email":
                v = _normalize_email(str(v))
            user[k] = v

        user["updated_at"] = _now_iso()
        _validate_user_record(user)

        users[idx] = user
        _atomic_write_json(path, payload)
        return user


def delete_user(user_id: str, auth_dir: Optional[Path] = None) -> None:
    path = _users_file(auth_dir)
    lock = _get_lock(path)

    with lock:
        payload = _load_or_init_json(path, {"version": 1, "users": []})
        before = len(payload["users"])
        payload["users"] = [u for u in payload["users"] if u.get("id") != user_id]
        after = len(payload["users"])
        if before == after:
            raise ValueError(f"User '{user_id}' not found")
        _atomic_write_json(path, payload)

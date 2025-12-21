# src/memory_json.py
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_memory_dir() -> Path:
    return Path(os.getcwd()) / "data" / "memory"


# Locks por sesión (reentrantes -> evitan deadlocks)
_LOCKS: Dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


def _get_lock(session_id: str) -> threading.RLock:
    with _LOCKS_GUARD:
        lock = _LOCKS.get(session_id)
        if lock is None:
            lock = threading.RLock()
            _LOCKS[session_id] = lock
        return lock


def _session_file(session_id: str, memory_dir: Optional[Path] = None) -> Path:
    d = memory_dir or _default_memory_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / f"session_{session_id}.json"


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # atómico en Windows


def new_session_id() -> str:
    return uuid.uuid4().hex


def _default_structured_memory() -> Dict[str, Any]:
    """
    Memoria estructurada (simple y extensible).
    - profile: datos persistentes del usuario
    - preferences: preferencias (idioma, tono, formato, etc.)
    - facts: hechos relevantes (lista corta)
    - todos: recordatorios/tareas detectadas (lista corta)
    """
    return {
        "profile": {
            "name": None,
            "role": None,
        },
        "preferences": {
            "language": "es",
            "tone": "neutral",
        },
        "facts": [],
        "todos": [],
    }


def create_session(session_id: Optional[str] = None, memory_dir: Optional[Path] = None) -> str:
    sid = session_id or new_session_id()
    path = _session_file(sid, memory_dir)

    lock = _get_lock(sid)
    with lock:
        if path.exists():
            return sid

        payload = {
            "session_id": sid,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "summary": "",
            "structured_memory": _default_structured_memory(),
            "messages": [],
        }
        _atomic_write_json(path, payload)

    return sid


def load_session(session_id: str, memory_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Carga la sesión; si no existe, la crea.
    """
    path = _session_file(session_id, memory_dir)

    lock = _get_lock(session_id)
    with lock:
        if not path.exists():
            payload = {
                "session_id": session_id,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "summary": "",
                "structured_memory": _default_structured_memory(),
                "messages": [],
            }
            _atomic_write_json(path, payload)

        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("session_id", session_id)
        data.setdefault("summary", "")
        data.setdefault("structured_memory", _default_structured_memory())
        data.setdefault("messages", [])
        return data


def save_session(data: Dict[str, Any], memory_dir: Optional[Path] = None) -> Dict[str, Any]:
    session_id = data["session_id"]
    path = _session_file(session_id, memory_dir)

    lock = _get_lock(session_id)
    with lock:
        data["updated_at"] = _now_iso()
        data.setdefault("summary", "")
        data.setdefault("structured_memory", _default_structured_memory())
        data.setdefault("messages", [])
        _atomic_write_json(path, data)
        return data


def append_messages(
    session_id: str,
    user_text: str,
    assistant_text: str,
    memory_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    lock = _get_lock(session_id)
    with lock:
        data = load_session(session_id, memory_dir=memory_dir)
        msgs: List[Dict[str, str]] = data.get("messages", [])

        now = _now_iso()
        msgs.append({"role": "user", "content": user_text, "ts": now})
        msgs.append({"role": "assistant", "content": assistant_text, "ts": now})

        data["messages"] = msgs
        return save_session(data, memory_dir=memory_dir)


# -------------------------
# Summary memory (texto)
# -------------------------
def get_summary(session_id: str, memory_dir: Optional[Path] = None) -> str:
    data = load_session(session_id, memory_dir=memory_dir)
    return (data.get("summary") or "").strip()


def set_summary(session_id: str, summary: str, memory_dir: Optional[Path] = None) -> Dict[str, Any]:
    lock = _get_lock(session_id)
    with lock:
        data = load_session(session_id, memory_dir=memory_dir)
        data["summary"] = (summary or "").strip()
        return save_session(data, memory_dir=memory_dir)


def reset_summary(session_id: str, memory_dir: Optional[Path] = None) -> Dict[str, Any]:
    return set_summary(session_id, "", memory_dir=memory_dir)


# -------------------------
# Structured memory (JSON)
# -------------------------
def get_structured_memory(session_id: str, memory_dir: Optional[Path] = None) -> Dict[str, Any]:
    data = load_session(session_id, memory_dir=memory_dir)
    sm = data.get("structured_memory") or _default_structured_memory()
    # normalizar por si faltan claves
    base = _default_structured_memory()
    base["profile"].update(sm.get("profile", {}) if isinstance(sm.get("profile", {}), dict) else {})
    base["preferences"].update(sm.get("preferences", {}) if isinstance(sm.get("preferences", {}), dict) else {})
    base["facts"] = sm.get("facts", []) if isinstance(sm.get("facts", []), list) else []
    base["todos"] = sm.get("todos", []) if isinstance(sm.get("todos", []), list) else []
    return base


def set_structured_memory(
    session_id: str,
    structured_memory: Dict[str, Any],
    memory_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    lock = _get_lock(session_id)
    with lock:
        data = load_session(session_id, memory_dir=memory_dir)
        data["structured_memory"] = structured_memory or _default_structured_memory()
        return save_session(data, memory_dir=memory_dir)


def reset_structured_memory(session_id: str, memory_dir: Optional[Path] = None) -> Dict[str, Any]:
    return set_structured_memory(session_id, _default_structured_memory(), memory_dir=memory_dir)


def merge_structured_memory(
    current: Dict[str, Any],
    update: Dict[str, Any],
    max_list_items: int = 20,
) -> Dict[str, Any]:
    """
    Merge controlado:
    - profile/preference: merge de dicts
    - facts/todos: merge de listas (sin duplicados exactos), con límite
    """
    cur = current or _default_structured_memory()
    upd = update or {}

    out = _default_structured_memory()
    out["profile"].update(cur.get("profile", {}) if isinstance(cur.get("profile", {}), dict) else {})
    out["preferences"].update(cur.get("preferences", {}) if isinstance(cur.get("preferences", {}), dict) else {})
    out["facts"] = list(cur.get("facts", []) if isinstance(cur.get("facts", []), list) else [])
    out["todos"] = list(cur.get("todos", []) if isinstance(cur.get("todos", []), list) else [])

    if isinstance(upd.get("profile"), dict):
        out["profile"].update(upd["profile"])
    if isinstance(upd.get("preferences"), dict):
        out["preferences"].update(upd["preferences"])

    def _merge_list(key: str):
        if not isinstance(upd.get(key), list):
            return
        existing = out[key]
        for item in upd[key]:
            if not isinstance(item, str):
                continue
            item = item.strip()
            if not item:
                continue
            if item not in existing:
                existing.append(item)
        out[key] = existing[-max_list_items:]

    _merge_list("facts")
    _merge_list("todos")

    return out


def update_structured_memory(
    session_id: str,
    update: Dict[str, Any],
    memory_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    lock = _get_lock(session_id)
    with lock:
        data = load_session(session_id, memory_dir=memory_dir)
        cur = get_structured_memory(session_id, memory_dir=memory_dir)
        data["structured_memory"] = merge_structured_memory(cur, update)
        return save_session(data, memory_dir=memory_dir)


# -------------------------
# Ventana / poda
# -------------------------
def prune_messages(session_id: str, keep_last: int = 12, memory_dir: Optional[Path] = None) -> Dict[str, Any]:
    lock = _get_lock(session_id)
    with lock:
        data = load_session(session_id, memory_dir=memory_dir)
        msgs = data.get("messages", [])
        if keep_last > 0 and len(msgs) > keep_last:
            data["messages"] = msgs[-keep_last:]
        return save_session(data, memory_dir=memory_dir)


# -------------------------
# Gestión sesión
# -------------------------
def reset_session(session_id: str, memory_dir: Optional[Path] = None) -> Dict[str, Any]:
    path = _session_file(session_id, memory_dir)

    lock = _get_lock(session_id)
    with lock:
        payload = {
            "session_id": session_id,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "summary": "",
            "structured_memory": _default_structured_memory(),
            "messages": [],
        }
        _atomic_write_json(path, payload)
        return payload


def delete_session(session_id: str, memory_dir: Optional[Path] = None) -> bool:
    path = _session_file(session_id, memory_dir)

    lock = _get_lock(session_id)
    with lock:
        if path.exists():
            path.unlink()
            return True
        return False


def list_sessions(memory_dir: Optional[Path] = None) -> List[str]:
    d = memory_dir or _default_memory_dir()
    if not d.exists():
        return []
    out: List[str] = []
    for p in d.glob("session_*.json"):
        out.append(p.stem.replace("session_", "", 1))
    return sorted(out)


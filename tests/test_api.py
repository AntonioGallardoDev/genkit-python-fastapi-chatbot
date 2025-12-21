# tests/test_api.py
import os
import importlib
from fastapi.testclient import TestClient

# Forzamos API_KEY para tests (antes de importar api)
os.environ.setdefault("API_KEY", "test-key-123")

import api
import flows


_TEST_MEMORY = {}  # session_id -> {"name": str | None}


async def _fake_chat_flow(session_id: str, prompt: str) -> str:
    state = _TEST_MEMORY.setdefault(session_id, {"name": None})
    p = prompt.lower().strip()

    if "cómo me llamo" in p or "como me llamo" in p:
        return (state["name"] or "No me lo has dicho.").strip().lower()

    if "me llamo" in p:
        name = prompt.split("me llamo", 1)[1].strip().strip(".")
        state["name"] = name
        return f"Encantado, {name}."

    return "OK"


def _patch_chat_flow(monkeypatch):
    monkeypatch.setattr(api, "chat_flow", _fake_chat_flow, raising=True)
    monkeypatch.setattr(flows, "chat_flow", _fake_chat_flow, raising=True)


def _headers():
    return {"X-API-Key": os.environ["API_KEY"]}


def test_health_public_no_key_needed():
    client = TestClient(api.app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_missing_api_key_rejected():
    client = TestClient(api.app)
    r = client.post("/sessions/new")
    assert r.status_code == 401


def test_sessions_new_and_get():
    client = TestClient(api.app)

    r = client.post("/sessions/new", headers=_headers())
    assert r.status_code == 200
    sid = r.json()["session_id"]
    assert sid

    r2 = client.get(f"/sessions/{sid}", headers=_headers())
    assert r2.status_code == 200
    assert r2.json()["session_id"] == sid


def test_chat_creates_session_if_missing(monkeypatch):
    _patch_chat_flow(monkeypatch)
    client = TestClient(api.app)

    r = client.post("/chat", headers=_headers(), json={"prompt": "Hola"})
    assert r.status_code == 200
    data = r.json()
    assert data["text"] == "OK"
    assert "session_id" in data


def test_chat_memory_same_session(monkeypatch):
    _patch_chat_flow(monkeypatch)
    client = TestClient(api.app)

    sid = client.post("/sessions/new", headers=_headers()).json()["session_id"]

    r1 = client.post("/chat", headers=_headers(), json={"session_id": sid, "prompt": "me llamo Antonio"})
    assert r1.status_code == 200
    assert "Antonio" in r1.json()["text"]

    r2 = client.post("/chat", headers=_headers(), json={"session_id": sid, "prompt": "¿Cómo me llamo?"})
    assert r2.status_code == 200
    assert r2.json()["text"].strip() == "antonio"


def test_sessions_reset():
    client = TestClient(api.app)
    sid = client.post("/sessions/new", headers=_headers()).json()["session_id"]

    r = client.post(f"/sessions/{sid}/reset", headers=_headers())
    assert r.status_code == 200
    assert r.json()["messages"] == []


def test_sessions_delete():
    client = TestClient(api.app)
    sid = client.post("/sessions/new", headers=_headers()).json()["session_id"]

    r = client.delete(f"/sessions/{sid}", headers=_headers())
    assert r.status_code == 200
    assert r.json()["deleted"] is True


def test_invalid_session_id_rejected():
    client = TestClient(api.app)
    bad = "not-a-valid-session"
    r = client.get(f"/sessions/{bad}", headers=_headers())
    assert r.status_code == 400


def test_prompt_too_large_rejected(monkeypatch):
    _patch_chat_flow(monkeypatch)
    client = TestClient(api.app)

    huge = "a" * (api.MAX_PROMPT_CHARS + 1)
    r = client.post("/chat", headers=_headers(), json={"prompt": huge})
    assert r.status_code == 413


def test_summary_endpoints():
    client = TestClient(api.app)
    sid = client.post("/sessions/new", headers=_headers()).json()["session_id"]

    g1 = client.get(f"/sessions/{sid}/summary", headers=_headers())
    assert g1.status_code == 200
    assert g1.json()["summary"] == ""

    u = client.put(f"/sessions/{sid}/summary", headers=_headers(), json={"summary": "Resumen de prueba"})
    assert u.status_code == 200
    assert u.json()["summary"] == "Resumen de prueba"

    rr = client.post(f"/sessions/{sid}/summary/reset", headers=_headers())
    assert rr.status_code == 200
    assert rr.json()["summary"] == ""


def test_structured_memory_endpoints():
    client = TestClient(api.app)
    sid = client.post("/sessions/new", headers=_headers()).json()["session_id"]

    g1 = client.get(f"/sessions/{sid}/memory", headers=_headers())
    assert g1.status_code == 200
    sm = g1.json()["structured_memory"]
    assert "profile" in sm and "preferences" in sm and "facts" in sm and "todos" in sm

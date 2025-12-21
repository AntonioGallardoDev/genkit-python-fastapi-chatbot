# tests/test_memory_json.py
from pathlib import Path

from memory_json import (
    create_session,
    load_session,
    append_messages,
    reset_session,
    delete_session,
    list_sessions,
    get_summary,
    set_summary,
    reset_summary,
    get_structured_memory,
    set_structured_memory,
    reset_structured_memory,
    update_structured_memory,
)


def test_create_and_load_session(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    sid = create_session()
    data = load_session(sid)

    assert data["session_id"] == sid
    assert data["messages"] == []
    assert "summary" in data
    assert "structured_memory" in data


def test_append_messages_persists(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    sid = create_session()
    append_messages(sid, "hola", "qué tal")

    data = load_session(sid)
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "assistant"


def test_reset_session(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    sid = create_session()
    append_messages(sid, "hola", "ok")

    data = reset_session(sid)
    assert data["messages"] == []
    assert data["summary"] == ""
    assert "structured_memory" in data


def test_delete_session(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    sid = create_session()
    assert delete_session(sid) is True
    assert delete_session(sid) is False


def test_list_sessions(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    a = create_session()
    b = create_session()
    sessions = list_sessions()

    assert a in sessions
    assert b in sessions


def test_summary_get_set_reset(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    sid = create_session()
    assert get_summary(sid) == ""

    set_summary(sid, "Resumen corto")
    assert get_summary(sid) == "Resumen corto"

    reset_summary(sid)
    assert get_summary(sid) == ""


def test_structured_memory_get_set_reset(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    sid = create_session()
    sm = get_structured_memory(sid)
    assert "profile" in sm and "preferences" in sm and "facts" in sm and "todos" in sm

    custom = {
        "profile": {"name": "Antonio", "role": "Analista"},
        "preferences": {"language": "es", "tone": "amigable"},
        "facts": ["Vive en España"],
        "todos": ["Preparar demo"],
    }
    set_structured_memory(sid, custom)
    sm2 = get_structured_memory(sid)
    assert sm2["profile"]["name"] == "Antonio"
    assert sm2["preferences"]["tone"] == "amigable"
    assert "Vive en España" in sm2["facts"]

    reset_structured_memory(sid)
    sm3 = get_structured_memory(sid)
    assert sm3["profile"]["name"] is None
    assert sm3["facts"] == []


def test_structured_memory_update_merge(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    sid = create_session()
    update_structured_memory(sid, {"profile": {"name": "Antonio"}})
    update_structured_memory(sid, {"facts": ["Le interesa Genkit"]})
    update_structured_memory(sid, {"facts": ["Le interesa Genkit", "Usa Windows 11"]})  # dedupe parcial

    sm = get_structured_memory(sid)
    assert sm["profile"]["name"] == "Antonio"
    assert "Le interesa Genkit" in sm["facts"]
    assert "Usa Windows 11" in sm["facts"]

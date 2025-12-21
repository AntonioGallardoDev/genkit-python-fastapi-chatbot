# src/api.py
import os
import re

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field


from flows import chat_flow
from memory_json import (
    create_session,
    delete_session,
    list_sessions,
    load_session,
    reset_session,
    get_summary,
    set_summary,
    reset_summary,
    get_structured_memory,
    set_structured_memory,
    reset_structured_memory,
)

app = FastAPI(title="Genkit + FastAPI", version="0.5.0")

# -----------------------------
# Seguridad básica (API Key)
# -----------------------------
# OBLIGATORIA: si no está configurada, el servidor no arranca.
API_KEY = os.getenv("API_KEY", "").strip()
API_KEY_HEADER = "X-API-Key"

if not API_KEY:
    raise RuntimeError(
        "API_KEY is required. Set it in your environment or .env file (e.g. API_KEY=... )."
    )

# Rutas públicas (sin API key)
PUBLIC_PATHS = ("/health", "/docs", "/redoc", "/openapi.json")

# 32 hex (uuid4().hex)
SESSION_ID_RE = re.compile(r"^[a-f0-9]{32}$")

# Límite de input
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "4000"))


def _is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or any(path.startswith(p + "/") for p in ("/docs", "/redoc"))


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Permitir rutas públicas
    if _is_public_path(request.url.path):
        return await call_next(request)

    provided = request.headers.get(API_KEY_HEADER, "").strip()

    # En middleware: NO lanzar HTTPException -> devolver JSONResponse
    if not provided or provided != API_KEY:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing or invalid API key (X-API-Key)."},
        )

    return await call_next(request)

def _validate_session_id(session_id: str) -> None:
    if not SESSION_ID_RE.match(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format. Expected 32 lowercase hex characters.",
        )


def _validate_prompt(prompt: str) -> None:
    if prompt is None:
        raise HTTPException(status_code=400, detail="Prompt is required.")
    if len(prompt) == 0:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Prompt too large. Max {MAX_PROMPT_CHARS} chars.",
        )


# -----------------------------
# Modelos
# -----------------------------
class ChatRequest(BaseModel):
    prompt: str = Field(..., description="User prompt")
    session_id: str | None = Field(None, description="Optional session id (uuid hex)")


class ChatResponse(BaseModel):
    session_id: str
    text: str


class NewSessionResponse(BaseModel):
    session_id: str


class SummaryPayload(BaseModel):
    summary: str


class StructuredMemoryPayload(BaseModel):
    structured_memory: dict


# -----------------------------
# Endpoints
# -----------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    _validate_prompt(req.prompt)

    if req.session_id:
        _validate_session_id(req.session_id)
        session_id = req.session_id
        create_session(session_id=session_id)
    else:
        session_id = create_session()

    text = await chat_flow(session_id, req.prompt)
    return ChatResponse(session_id=session_id, text=text)


@app.post("/sessions/new", response_model=NewSessionResponse)
async def sessions_new():
    sid = create_session()
    return NewSessionResponse(session_id=sid)


@app.get("/sessions")
async def sessions_list():
    return {"sessions": list_sessions()}


@app.get("/sessions/{session_id}")
async def sessions_get(session_id: str):
    _validate_session_id(session_id)
    return load_session(session_id)


@app.post("/sessions/{session_id}/reset")
async def sessions_reset(session_id: str):
    _validate_session_id(session_id)
    return reset_session(session_id)


@app.delete("/sessions/{session_id}")
async def sessions_delete(session_id: str):
    _validate_session_id(session_id)
    deleted = delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True, "session_id": session_id}


# -----------------------------
# Summary endpoints
# -----------------------------
@app.get("/sessions/{session_id}/summary")
async def summary_get(session_id: str):
    _validate_session_id(session_id)
    create_session(session_id=session_id)
    return {"session_id": session_id, "summary": get_summary(session_id)}


@app.put("/sessions/{session_id}/summary")
async def summary_put(session_id: str, payload: SummaryPayload):
    _validate_session_id(session_id)
    create_session(session_id=session_id)
    set_summary(session_id, payload.summary)
    return {"session_id": session_id, "summary": get_summary(session_id)}


@app.post("/sessions/{session_id}/summary/reset")
async def summary_post_reset(session_id: str):
    _validate_session_id(session_id)
    create_session(session_id=session_id)
    reset_summary(session_id)
    return {"session_id": session_id, "summary": ""}


# -----------------------------
# Structured memory endpoints
# -----------------------------
@app.get("/sessions/{session_id}/memory")
async def memory_get(session_id: str):
    _validate_session_id(session_id)
    create_session(session_id=session_id)
    return {"session_id": session_id, "structured_memory": get_structured_memory(session_id)}


@app.put("/sessions/{session_id}/memory")
async def memory_put(session_id: str, payload: StructuredMemoryPayload):
    _validate_session_id(session_id)
    create_session(session_id=session_id)
    set_structured_memory(session_id, payload.structured_memory)
    return {"session_id": session_id, "structured_memory": get_structured_memory(session_id)}


@app.post("/sessions/{session_id}/memory/reset")
async def memory_post_reset(session_id: str):
    _validate_session_id(session_id)
    create_session(session_id=session_id)
    reset_structured_memory(session_id)
    return {"session_id": session_id, "structured_memory": get_structured_memory(session_id)}

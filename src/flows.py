# src/flows.py
import os
from dotenv import load_dotenv

from genkit.ai import Genkit
from genkit.plugins.compat_oai import OpenAI

from memory_json import (
    create_session,
    load_session,
    append_messages,
    get_summary,
    set_summary,
    prune_messages,
    get_structured_memory,
    update_structured_memory,
)

load_dotenv()

MODEL = os.getenv("GENKIT_MODEL", "openai/gpt-4o")

# Ajustes memoria
WINDOW_MESSAGES = int(os.getenv("MEM_WINDOW_MESSAGES", "12"))          # mensajes individuales
SUMMARIZE_THRESHOLD = int(os.getenv("MEM_SUMMARIZE_THRESHOLD", "20"))  # mensajes individuales
SUMMARY_MAX_WORDS = int(os.getenv("MEM_SUMMARY_MAX_WORDS", "140"))

# Memoria estructurada
STRUCTURED_ENABLE = os.getenv("MEM_STRUCTURED_ENABLE", "true").lower() in ("1", "true", "yes", "y")
STRUCTURED_MAX_LIST_ITEMS = int(os.getenv("MEM_STRUCTURED_MAX_ITEMS", "20"))


_ai_instance: Genkit | None = None


def get_ai() -> Genkit:
    global _ai_instance
    if _ai_instance is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Falta OPENAI_API_KEY. Crea un .env a partir de .env.example.")
        _ai_instance = Genkit(plugins=[OpenAI()])
    return _ai_instance


def _format_history(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "user":
            lines.append(f"Usuario: {content}")
        elif role == "assistant":
            lines.append(f"Asistente: {content}")
    return "\n".join(lines)


def _format_structured_memory(sm: dict) -> str:
    profile = sm.get("profile", {}) if isinstance(sm.get("profile", {}), dict) else {}
    prefs = sm.get("preferences", {}) if isinstance(sm.get("preferences", {}), dict) else {}
    facts = sm.get("facts", []) if isinstance(sm.get("facts", []), list) else []
    todos = sm.get("todos", []) if isinstance(sm.get("todos", []), list) else []

    lines = []
    lines.append("Perfil:")
    lines.append(f"- nombre: {profile.get('name')}")
    lines.append(f"- rol: {profile.get('role')}")
    lines.append("Preferencias:")
    for k, v in prefs.items():
        lines.append(f"- {k}: {v}")
    lines.append("Hechos relevantes (si existen):")
    if facts:
        for f in facts[-10:]:
            lines.append(f"- {f}")
    else:
        lines.append("- (vacío)")
    lines.append("Tareas/recordatorios (si existen):")
    if todos:
        for t in todos[-10:]:
            lines.append(f"- {t}")
    else:
        lines.append("- (vacío)")
    return "\n".join(lines)


def _build_prompt(summary: str, structured: dict, recent_messages: list[dict], user_prompt: str) -> str:
    parts = []
    parts.append("Eres un asistente útil, preciso y conciso.")
    parts.append("Responde en español salvo que el usuario pida otro idioma.")
    parts.append("")

    if structured:
        parts.append("Memoria estructurada (persistente):")
        parts.append(_format_structured_memory(structured))
        parts.append("")

    if summary.strip():
        parts.append("Resumen de la conversación hasta ahora (memoria a largo plazo):")
        parts.append(summary.strip())
        parts.append("")

    parts.append("Contexto reciente (memoria a corto plazo):")
    if recent_messages:
        parts.append(_format_history(recent_messages))
    else:
        parts.append("(sin contexto reciente)")
    parts.append("")

    parts.append(f"Usuario: {user_prompt}")
    parts.append("Asistente:")
    return "\n".join(parts)


async def _summarize_incremental(ai: Genkit, prev_summary: str, messages: list[dict]) -> str:
    convo = _format_history(messages)

    prompt = f"""
Tu tarea: actualizar un resumen acumulativo de una conversación.

Resumen actual:
{prev_summary.strip() if prev_summary.strip() else "(vacío)"}

Nuevos mensajes para incorporar al resumen:
{convo}

Devuelve SOLO el nuevo resumen final:
- Máximo {SUMMARY_MAX_WORDS} palabras.
- Incluye hechos persistentes y preferencias del usuario.
- No incluyas detalles efímeros ni listas largas.
- Mantén tono neutro y en español.
""".strip()

    resp = await ai.generate(model=MODEL, prompt=prompt)
    return (resp.text or "").strip()


async def _extract_structured_update(ai: Genkit, messages: list[dict]) -> dict:
    """
    Extrae una actualización incremental de memoria estructurada.
    Devuelve un JSON (dict) con campos opcionales:
      - profile: {name?, role?}
      - preferences: {...}
      - facts: [..]
      - todos: [..]
    """
    convo = _format_history(messages)

    prompt = f"""
Extrae una actualización de memoria estructurada a partir de una conversación.

Devuelve SOLO un JSON válido (sin Markdown) con ESTE esquema (campos opcionales):
{{
  "profile": {{"name": string|null, "role": string|null}},
  "preferences": {{"language": "es"|"en"|string, "tone": string}},
  "facts": [string],
  "todos": [string]
}}

Reglas:
- No inventes datos.
- facts/todos: frases cortas.
- Si no hay nada nuevo, devuelve {{}}.

Conversación:
{convo}
""".strip()

    resp = await ai.generate(model=MODEL, prompt=prompt)
    text = (resp.text or "").strip()

    # Parse robusto: si falla, no actualizamos
    import json
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


async def chat_flow(session_id: str, prompt: str) -> str:
    create_session(session_id=session_id)

    data = load_session(session_id)
    summary = get_summary(session_id)
    structured = get_structured_memory(session_id)
    messages = data.get("messages", [])

    recent = messages[-WINDOW_MESSAGES:] if WINDOW_MESSAGES > 0 else messages

    ai = get_ai()

    final_prompt = _build_prompt(summary, structured, recent, prompt)
    resp = await ai.generate(model=MODEL, prompt=final_prompt)
    answer = resp.text or ""

    append_messages(session_id=session_id, user_text=prompt, assistant_text=answer)

    data_after = load_session(session_id)
    msgs_after = data_after.get("messages", [])

    if SUMMARIZE_THRESHOLD > 0 and len(msgs_after) > SUMMARIZE_THRESHOLD:
        # 1) Actualizar resumen
        new_summary = await _summarize_incremental(ai, summary, msgs_after)
        set_summary(session_id, new_summary)

        # 2) Actualizar memoria estructurada (opcional)
        if STRUCTURED_ENABLE:
            upd = await _extract_structured_update(ai, msgs_after)
            if upd:
                update_structured_memory(session_id, upd)

        # 3) Podar mensajes para ventana
        prune_messages(session_id, keep_last=WINDOW_MESSAGES)

    return answer


def register_flows() -> Genkit:
    ai = get_ai()

    @ai.flow()
    async def chat_flow_registered(session_id: str, prompt: str) -> str:
        return await chat_flow(session_id, prompt)

    return ai

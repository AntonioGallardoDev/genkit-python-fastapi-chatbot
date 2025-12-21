# AGENTS - Guía para IA desarrolladora (Copilot/Codex/ChatGPT)

## Contexto del proyecto
API de chatbot en **Python** con:
- Genkit (OpenAI compatible)
- FastAPI (endpoints HTTP)
- Memoria JSON persistente:
  - summary (texto)
  - structured_memory (perfil/preferencias/hechos/tareas)
  - messages (historial)
- Tests con pytest

Objetivo: código simple, claro, reproducible en Windows 11 + VS Code.

---

## Estructura
- `src/api.py`: endpoints FastAPI
- `src/flows.py`: `chat_flow` (Genkit/OpenAI) + prompt con memoria
- `src/memory_json.py`: persistencia en JSON + locks + merge structured
- `src/run_api.py`: arranque uvicorn
- `tests/test_api.py`: tests API (mock de chat_flow)
- `tests/test_memory_json.py`: tests de persistencia real
- `data/memory/`: sesiones JSON (no versionar)

---

## Principios
- No introducir dependencias innecesarias.
- No guardar secretos en repo.
- Mantener tests deterministas y sin red.
- Mantener compatibilidad Windows (paths + nombres de fichero).

---

## Reglas de testing
- Los tests de API **NO** deben llamar a OpenAI:
  - Se debe parchear/mockear `chat_flow` siempre.
- Los tests de persistencia deben usar `tmp_path` y `monkeypatch.chdir(tmp_path)`.

Comandos:
- `pytest`
- `pytest tests/test_api.py -vv`
- `pytest tests/test_memory_json.py -vv`

---

## Reglas de memoria
- `summary` debe ser corto y estable (hechos persistentes, preferencias).
- `structured_memory`:
  - `profile` y `preferences`: merge de dicts
  - `facts` y `todos`: listas limitadas, sin duplicados exactos
- `messages`: mantener ventana reciente cuando el historial crezca
- Evitar deadlocks: locks reentrantes por sesión (RLock)

---

## Checklist al entregar cambios
- [ ] `python src/run_api.py` funciona
- [ ] `pytest` pasa
- [ ] No hay secretos en commits
- [ ] README/REQUIREMENTS actualizados si cambia el comportamiento
- [ ] `.gitignore` cubre `.env`, `.venv`, `.genkit`, `data/memory`, caches

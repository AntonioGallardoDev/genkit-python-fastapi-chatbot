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
- `data/auth/`: usuarios/roles (NO versionar)
  - `roles.json`: catálogo de roles/permisos
  - `users.json`: usuarios con `password_hash` y metadatos
- `data/audit/`: auditoría (JSONL)


---

## Principios
- No introducir dependencias innecesarias.
- No guardar secretos en repo.
- Mantener tests deterministas y sin red.
- Mantener compatibilidad Windows (paths + nombres de fichero).

## Reglas de auth (MVP fichero)
- Nunca guardar passwords en claro. Solo `password_hash` (bcrypt/argon2).
- No exponer `password_hash` en respuestas de API.
- Validar roles y departamentos contra catálogo.
- Persistencia robusta: lock + escritura atómica (mismo patrón que `memory_json.py`).
- Añadir auditoría mínima (append-only JSONL) para acciones sensibles (login/admin).

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

## Plantillas opcionales (si quieres versionar “ejemplos” sin secretos)
- data/auth/roles.example.json
- data/auth/users.example.json

## Checklist al entregar cambios
- [ ] `python src/run_api.py` funciona
- [ ] `pytest` pasa
- [ ] No hay secretos en commits
- [ ] README/REQUIREMENTS actualizados si cambia el comportamiento
- [ ] `.gitignore` cubre `.env`, `.venv`, `.genkit`, `data/memory`, caches
- [ ] `.gitignore` cubre `data/auth/` y `data/audit/`
- [ ] Tests de auth/repo no usan red y son deterministas (tmp_path)

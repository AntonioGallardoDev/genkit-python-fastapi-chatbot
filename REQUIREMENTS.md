# REQUIREMENTS - Genkit Python + FastAPI (memoria JSON avanzada)

## Objetivo
API de chatbot en Python con:
- **Genkit** (OpenAI compatible)
- **FastAPI** para exponer endpoints HTTP
- **Memoria persistente** en JSON por sesión
  - `summary` (texto de resumen acumulativo)
  - `structured_memory` (perfil/preferencias/hechos/tareas)
  - `messages` (historial)
- **Tests** automatizados con `pytest`

---

## Alcance (estado actual)

### API (FastAPI)
- Health: `GET /health`
- Sesiones:
  - `POST /sessions/new`
  - `GET /sessions`
  - `GET /sessions/{session_id}`
  - `POST /sessions/{session_id}/reset`
  - `DELETE /sessions/{session_id}`
- Chat:
  - `POST /chat` (crea sesión si no existe `session_id`)
- Memoria:
  - Summary:
    - `GET /sessions/{session_id}/summary`
    - `PUT /sessions/{session_id}/summary`
    - `POST /sessions/{session_id}/summary/reset`
  - Structured memory:
    - `GET /sessions/{session_id}/memory`
    - `PUT /sessions/{session_id}/memory`
    - `POST /sessions/{session_id}/memory/reset`

### Memoria persistente (JSON)
- Persistencia por sesión en `data/memory/session_<id>.json`
- Campos:
  - `summary`: string
  - `structured_memory`: dict con `profile`, `preferences`, `facts`, `todos`
  - `messages`: lista de mensajes (role/content/ts)
- Ventana reciente de contexto para el LLM
- Resumen incremental + (opcional) extracción estructurada cuando se supera umbral

### Tests
- Unit tests: `tests/test_memory_json.py`
- API tests: `tests/test_api.py`
- Los tests de API no llaman a OpenAI (mock de `chat_flow`)

---

## No incluido (por ahora)
- Autenticación/roles/permisos
- RAG/embeddings
- Tool calling (tools) en producción
- Persistencia en DB (SQLite/Postgres)

---

## Requisitos no funcionales
- Compatible con Windows 11
- Python recomendado: 3.11.x
- Sin secretos en repo (`.env` fuera de git)
- Tests reproducibles y rápidos (sin red)

---

## Criterios de aceptación
- `python src/run_api.py` levanta API en `http://127.0.0.1:8000`
- `pytest` ejecuta la suite completa sin errores
- `genkit start -- python src/run_api.py` levanta Dev UI (si Node+CLI están instalados)

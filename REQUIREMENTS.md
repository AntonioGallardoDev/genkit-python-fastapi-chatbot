# REQUIREMENTS - Genkit Python + FastAPI (memoria JSON avanzada)

## Objetivo
API de chatbot en Python con:
- **Genkit** (OpenAI compatible)
- **FastAPI** para exponer endpoints HTTP
- **Memoria persistente** en JSON por sesión
  - `summary` (texto de resumen acumulativo)
  - `structured_memory` (perfil/preferencias/hechos/tareas)
  - `messages` (historial)
- **Autenticación corporativa básica**:
  - Hash de contraseña **Argon2id**
  - Tokens **JWT** (Bearer)
  - Store de usuarios/roles en fichero (MVP)
- **Tests** automatizados con `pytest`

---

## Alcance (estado actual)

### Autenticación corporativa (MVP en fichero + JWT)
- **Store de identidad en ficheros** (runtime):
  - `data/auth/roles.json` → catálogo de roles/permisos
  - `data/auth/users.json` → usuarios con `password_hash`, roles y departamento
- **Plantillas versionables** (en Git):
  - `data/auth/roles.example.json`
  - `data/auth/users.example.json` (con `password_hash` ficticio)
- **Hashing**: Argon2id (no se guardan passwords en claro)
- **JWT**:
  - firma HS256 con `JWT_SECRET`
  - claims mínimos: `sub` (user_id), `roles`, `department`, expiración
- **Nota de seguridad (fase MVP)**:
  - Los endpoints siguen protegidos por `X-API-Key` (capa adicional temporal) además del Bearer token.

### API (FastAPI)

#### Health
- `GET /health`

#### Autenticación
- `POST /auth/login`
  - input: `{ "email": "...", "password": "..." }`
  - output: `{ "access_token": "...", "token_type": "bearer" }`
- `GET /me`
  - requiere `Authorization: Bearer <token>`
  - devuelve datos del usuario (sin `password_hash`)

#### Sesiones
- `POST /sessions/new`
- `GET /sessions`
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/reset`
- `DELETE /sessions/{session_id}`

#### Chat
- `POST /chat` (crea sesión si no existe `session_id`)

#### Memoria
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
- Unit tests:
  - memoria: `tests/test_memory_json.py`
  - repo usuarios: `tests/test_users_repo_file.py`
  - hashing/JWT: `tests/test_auth_jwt.py`
- API tests: `tests/test_api.py`
- Los tests de API no llaman a OpenAI (mock de `chat_flow`)

---

## No incluido (por ahora)
- Gestión de usuarios/roles vía API (CRUD admin)
- Bootstrap seguro del primer usuario admin (script/endpoint protegido)
- Refresh tokens / rotación de tokens / revocación (blacklist)
- OAuth/OIDC/SSO corporativo
- Rate limiting por IP/usuario
- RAG/embeddings + vector store + políticas de acceso por rol/departamento
- Observabilidad completa (OpenTelemetry + backend de trazas/logs)
- Persistencia en DB (SQLite/Postgres)

---

## Requisitos no funcionales
- Compatible con Windows 11
- Python recomendado: 3.11.x
- Sin secretos en repo (`.env` fuera de git)
- Tests reproducibles y rápidos (sin red)
- Node.js (20 LTS) recomendado si se usa Genkit Dev UI / CLI

---

## Variables de entorno requeridas
- `API_KEY`: clave para proteger la API (header `X-API-Key`)
- `OPENAI_API_KEY`: clave del proveedor LLM (si aplica al runtime)
- `JWT_SECRET`: secreto para firmar JWT
- `JWT_TTL_MINUTES` (opcional): duración del token (default 60)
- `MAX_PROMPT_CHARS` (opcional): límite de caracteres del prompt (default 4000)

---

## Criterios de aceptación
- `python src/run_api.py` levanta API en `http://127.0.0.1:8000`
- `pytest` ejecuta la suite completa sin errores
- Login funciona:
  - `POST /auth/login` devuelve `access_token` con credenciales válidas
  - `GET /me` devuelve el usuario cuando se envía `Authorization: Bearer <token>`
- `genkit start -- python src/run_api.py` levanta Dev UI (si Node+CLI están instalados)

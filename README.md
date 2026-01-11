# Genkit (Python beta) + FastAPI — Chatbot corporativo con memoria persistente + Auth (Argon2id + JWT)

Backend de chatbot en **Python** con **Genkit (plugin OpenAI compatible)** y **FastAPI**, diseñado como **base de un chatbot corporativo** seguro, extensible y testeado.

Incluye:
- **Memoria persistente en JSON** por sesión
  - historial de mensajes
  - summary (resumen acumulativo)
  - structured_memory (perfil, preferencias, hechos, tareas)
- **Seguridad básica por API Key**
- **Autenticación corporativa (MVP)**:
  - Hash de contraseñas **Argon2id**
  - Tokens **JWT Bearer**
  - Usuarios y roles en fichero (runtime en `data/auth/*.json`)
- **Batería completa de tests** (`pytest`)
- Compatible con **Genkit Developer UI**

---

## Características principales

- Chat con memoria persistente y control explícito de estado.
- Persistencia local en JSON (ideal para MVP y prototipos corporativos).
- **API Key obligatoria** como primera capa de seguridad.
- **Login real de usuarios**:
  - `POST /auth/login`
  - `GET /me`
- Arquitectura preparada para evolucionar a:
  - CRUD admin de usuarios y roles
  - rate limiting
  - observabilidad (OpenTelemetry)
  - RAG corporativo con control de acceso
  - persistencia en base de datos (SQLite/Postgres)

---

## Requisitos

- Python **3.11.x** (recomendado)
- Windows 11 (compatible)
- Node.js **20 LTS** (recomendado si se usa Genkit Dev UI / CLI)

---

## Estructura del proyecto

```
src/
 ├─ api.py                 # FastAPI + middleware + auth
 ├─ flows.py               # Flujos Genkit
 ├─ memory_json.py         # Memoria persistente por sesión
 ├─ users_repo_file.py     # Repositorio de usuarios (JSON)
 ├─ auth_passwords.py      # Hashing Argon2id
 ├─ auth_jwt.py            # JWT
 └─ run_api.py             # Arranque Uvicorn

tests/
 └─ ...                    # Tests unitarios y de API

data/                      # NO versionado
 ├─ memory/
 ├─ auth/
 │   ├─ users.json         # runtime
 │   └─ roles.json
 └─ audit/                 # reservado

Plantillas versionadas:
 └─ data/auth/*.example.json
```

---

## Variables de entorno

Crear un `.env` (no versionado):

```env
API_KEY=changeme
OPENAI_API_KEY=...
JWT_SECRET=very-long-secret
JWT_TTL_MINUTES=60
MAX_PROMPT_CHARS=4000
```

---

## Ejecución

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src/run_api.py
```

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

---

## Nota sobre Windows + Genkit

Para usar **Genkit Developer UI**:

```powershell
genkit start -- python src/run_api.py
```

(Node.js 20 LTS recomendado)

---

## Seguridad

### API Key
- Header obligatorio: `X-API-Key`
- Protege todas las rutas salvo `/health` y documentación.

### Autenticación (MVP)
- Hash Argon2id
- JWT firmado con `JWT_SECRET`
- Claims: `sub`, `roles`, `department`, expiración
- Doble capa temporal: API Key + JWT

---

## Endpoints principales

### Health
- `GET /health` (público)

### Auth
- `POST /auth/login`
- `GET /me`

### Chat y sesiones
- `POST /chat`
- `POST /sessions/new`
- `GET /sessions`
- `GET /sessions/{id}`
- `POST /sessions/{id}/reset`
- `DELETE /sessions/{id}`

### Memoria
- Summary y structured memory (get / put / reset)

---

## Tests

```bash
python -m pytest
```

La suite:
- no llama a OpenAI
- usa ficheros temporales
- valida auth, memoria y API

---

## Roadmap

### ✅ Hecho
- Memoria persistente JSON avanzada
- API Key middleware
- Repositorio de usuarios en fichero
- Autenticación Argon2id + JWT (`/auth/login`, `/me`)

### ⏭️ Próximo
- Bootstrap seguro del primer admin
- CRUD admin de usuarios/roles
- Rate limiting
- Auditoría de acciones sensibles
- Observabilidad (OpenTelemetry)
- RAG corporativo con control por rol/departamento
- Persistencia en DB

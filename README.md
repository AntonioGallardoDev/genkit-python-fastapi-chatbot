# Genkit (Python beta) + FastAPI — Chatbot con memoria persistente (JSON) + resumen

Proyecto de **chatbot en Python** construido con **Genkit** (plugin **OpenAI compatible**) y **FastAPI**, expuesto como **API HTTP** y con **memoria persistente por sesión** en archivos **JSON**.

Está pensado para ser **simple, auditable y extensible**, incorporando:
- memoria híbrida (contexto reciente + resumen + memoria estructurada)
- seguridad básica por API Key (sin usuarios aún)
- batería de tests con `pytest`
- checks básicos de seguridad (pip-audit, bandit, semgrep)

---

## Características principales

- API REST con FastAPI
- Integración con Genkit (Python **beta**) + plugin OpenAI compatible
- Memoria persistente por sesión en JSON (carpeta `data/`)
- Memoria híbrida:
  - **ventana de contexto reciente** (últimos N mensajes)
  - **resumen acumulativo** (long-term memory)
  - **memoria estructurada** (profile / preferences / facts / todos, etc.)
- Endpoints para ver / editar / resetear memoria (resumen y estructurada)
- **API Key obligatoria** para casi todos los endpoints
- Tests con `pytest` (sin llamadas reales a OpenAI)
- Compatible con Genkit Developer UI (`genkit start ...`)

---

## Requisitos

- Windows 11 (probado)
- Python **3.11.x** (recomendado 3.11.9)
- Node.js **20 LTS** (recomendado) — solo para `genkit-cli` y Dev UI
- VS Code + extensión Python (Microsoft)

---

## Estructura de proyecto (orientativa)

> En tu repo lo normal es que el código viva en `src/` y los tests en `tests/`.

- `src/api.py` → FastAPI (endpoints + seguridad + validaciones)
- `src/flows.py` → Flow de Genkit (chat_flow)
- `src/memory_json.py` → Persistencia de memoria por sesión (JSON)
- `src/run_api.py` → Arranque de Uvicorn
- `tests/` → tests unitarios e integración (TestClient)
- `data/` → **archivos JSON de memoria persistente** (se crea automáticamente)
- `.env` / `.env.example` → variables de entorno
- `requirements.txt` → dependencias
- `README.md`, `REQUIREMENTS.md`, `AGENTS.md`, `.gitignore`

---

## Variables de entorno

Crea un `.env` (o exporta variables) con:

- `OPENAI_API_KEY` → clave real de OpenAI (solo necesaria si llamas al modelo de verdad)
- `API_KEY` → **API Key interna** para proteger endpoints (cabecera `X-API-Key`)
- (opcional) `DATA_DIR` → carpeta donde guardar JSON de memoria (por defecto `data`)

Ejemplo `.env`:

```env
OPENAI_API_KEY="sk-..."
API_KEY="change-me"
DATA_DIR="data"
```

---

## Cómo ejecutar la API

### 1) Crear entorno e instalar dependencias

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Ejecutar con Uvicorn (modo simple)

```powershell
python src/run_api.py
# Uvicorn: http://127.0.0.1:8000
```

### 3) Ejecutar con Genkit Dev UI (opcional)

Con Node 20 LTS instalado y `genkit-cli` disponible:

```powershell
genkit start -- python src/run_api.py
# Dev UI: http://localhost:4000 (puede variar el puerto)
```

---

## Nota importante (Windows + Genkit)

En algunos entornos, Genkit puede intentar escribir archivos de runtime con timestamps tipo ISO que incluyen `:`.
En Windows esto puede provocar `OSError: [Errno 22] Invalid argument` porque `:` no es válido en nombres de archivo.

La solución típica es **sanear el nombre** del archivo runtime reemplazando `:` por `-` (o similar) en el código que lo genera (o en la capa que lo envuelve), tal como hiciste al parchear el `_server.py`.

---

## Seguridad básica (API Key obligatoria)

- La API exige la cabecera: `X-API-Key: <API_KEY>`
- Se suele permitir **sin key** un endpoint “público” de health (por ejemplo `/health`) para monitorización.

---

## Mini-guía: cómo funciona la memoria

La memoria se guarda **por sesión** en JSON dentro de `data/` (o `DATA_DIR`):

- Cada sesión tiene un `session_id`.
- En el JSON se suelen mantener:
  - `messages`: historial (o últimos N mensajes para contexto)
  - `summary`: resumen acumulativo
  - `structured`: memoria estructurada (diccionario)

Flujo típico:
1. El cliente crea una sesión (`/sessions/new`) o envía un `session_id`.
2. En `/chat`, se carga memoria desde `data/<session_id>.json`.
3. Se envía al flow el contexto reciente + `summary` + `structured`.
4. Tras responder, se persiste:
   - mensajes recientes
   - actualización del resumen (si aplica)
   - cambios en memoria estructurada

---

## Endpoints principales (resumen)

> Los nombres exactos pueden variar según tu `src/api.py`, pero la idea es esta.

- `GET /health` → healthcheck (público)
- `POST /sessions/new` → crea sesión
- `GET /sessions/{session_id}` → recupera estado/metadata de sesión
- `POST /sessions/{session_id}/reset` → resetea la sesión
- `DELETE /sessions/{session_id}` → borra la sesión
- `POST /chat` → chat (usa memoria persistente)

### Endpoints de resumen (summary)
- `GET /sessions/{session_id}/summary`
- `PUT /sessions/{session_id}/summary`
- `POST /sessions/{session_id}/summary/reset`

### Endpoints de memoria estructurada
- `GET /sessions/{session_id}/memory`
- `PUT /sessions/{session_id}/memory` (set completo)
- `PATCH /sessions/{session_id}/memory` (merge/update parcial)
- `POST /sessions/{session_id}/memory/reset`

---

## Ejemplos con curl

> En Windows puedes usar curl (o PowerShell `Invoke-RestMethod`). Aquí van ejemplos con curl.

Define:

- `API_KEY="change-me"`
- `BASE="http://127.0.0.1:8000"`

### Crear sesión

```bash
curl -s -X POST "$BASE/sessions/new" \
  -H "X-API-Key: $API_KEY"
```

### Chat (con sesión)

```bash
curl -s -X POST "$BASE/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"session_id":"<SESSION_ID>","prompt":"Hola, me llamo Antonio"}'
```

### Ver resumen

```bash
curl -s -X GET "$BASE/sessions/<SESSION_ID>/summary" \
  -H "X-API-Key: $API_KEY"
```

### Editar resumen

```bash
curl -s -X PUT "$BASE/sessions/<SESSION_ID>/summary" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"summary":"El usuario se llama Antonio. Le interesa Genkit y FastAPI."}'
```

### Ver memoria estructurada

```bash
curl -s -X GET "$BASE/sessions/<SESSION_ID>/memory" \
  -H "X-API-Key: $API_KEY"
```

### Merge/update parcial de memoria estructurada

```bash
curl -s -X PATCH "$BASE/sessions/<SESSION_ID>/memory" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"profile":{"name":"Antonio"}, "preferences":{"lang":"es"}}'
```

---

## Tests (pytest)

### Opción A (rápida)

```powershell
$env:API_KEY="test-key"
pytest
```

### Opción B (recomendada en Windows / PowerShell)

En Windows (PowerShell) recomendamos fijar `PYTHONPATH=src` para que los imports funcionen igual que en ejecución:

```powershell
$env:PYTHONPATH="src"
$env:API_KEY="test-key"
pytest -q
```

> Tip: si usas un comando tipo `test-all`, asegúrate de que exporta también `PYTHONPATH=src`.

---

## Checks básicos de seguridad

### Dependencias Python (CVE)
```powershell
pip-audit
```

### Análisis estático (Python)
```powershell
bandit -r src -ll
```

### Semgrep (con encoding UTF-8 en Windows)
```powershell
$env:PYTHONIOENCODING="utf-8"
chcp 65001
semgrep --config=p/security-audit src
```

---

## Licencia

Si lo publicas en GitHub y quieres máxima adopción, lo más común es:
- **MIT** (muy permisiva)
- **Apache-2.0** (permisiva + explícita en patentes)

Si no tienes una preferencia clara, MIT suele ser la opción más sencilla para proyectos demo/plantilla.

---

## Roadmap (siguiente fase)

- Autenticación por usuarios (JWT/OAuth)
- Rate limiting por IP/usuario
- Observabilidad (OpenTelemetry + backend de trazas/logs)
- Persistencia en DB (SQLite/Postgres) en lugar de JSON si crece
- RAG (vector store) y políticas de acceso por rol

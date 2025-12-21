# Genkit Python + FastAPI — Chatbot con memoria persistente (JSON)

Proyecto de **chatbot en Python** construido con **Genkit** (plugin OpenAI compatible) y **FastAPI**, expuesto como API HTTP y con **memoria persistente por sesión** en archivos JSON.

El sistema está diseñado para ser **simple, auditable y extensible**, incorporando buenas prácticas de:
- arquitectura conversacional
- testing automatizado
- seguridad básica (sin usuarios aún)

---

## Características principales

- API REST con FastAPI  
- Integración con Genkit (OpenAI compatible)  
- Memoria persistente por sesión en JSON  
- Memoria híbrida:
  - ventana de contexto reciente
  - resumen acumulativo (long-term memory)
  - memoria estructurada (profile, preferences, facts, todos)
- Endpoints para ver / editar / resetear memoria
- API Key obligatoria para todos los endpoints
- Tests con pytest (sin llamadas reales a OpenAI)
- Compatible con Genkit Developer UI

---

## Requisitos

- Windows 11
- Python **3.11.x** (recomendado 3.11.9)
- VS Code + extensión Python (Microsoft)
- Node.js 20+ (solo para `genkit-cli` y Dev UI)

---

## Nota importante (Windows + Genkit)

Genkit Python puede generar nombres de archivo con timestamps ISO que incluyen `:`.  
En Windows esto provoca:

```
OSError: [Errno 22] Invalid argument
```

### Solución aplicada

Parche local en:

```
.venv/Lib/site-packages/genkit/ai/_server.py
```

Sustituir:

```python
current_datetime.isoformat()
```

por:

```python
current_datetime.isoformat().replace(":", "-")
```

---

## Estructura del proyecto

```
.
├─ src/
│  ├─ api.py
│  ├─ flows.py
│  ├─ memory_json.py
│  └─ run_api.py
├─ tests/
│  ├─ test_api.py
│  ├─ test_memory_json.py
│  └─ pytest.ini
├─ data/
│  └─ memory/
├─ .env.example
├─ .gitignore
├─ README.md
├─ REQUIREMENTS.md
├─ AGENTS.md
└─ requirements.txt
```

---

## Variables de entorno

```env
OPENAI_API_KEY=tu_api_key
API_KEY=mi-clave-api-privada
MAX_PROMPT_CHARS=4000
```

---

## Ejecutar la API

```powershell
$env:API_KEY="mi-clave-api-privada"
python src/run_api.py
```

Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## 🧠 Cómo funciona la memoria

El chatbot usa **memoria híbrida persistente en JSON**:

### 1) Memoria a corto plazo
- Últimos N mensajes
- Contexto inmediato
- Optimiza tokens

### 2) Memoria a largo plazo (summary)
- Resumen acumulativo
- Información estable del usuario
- Editable por endpoint

### 3) Memoria estructurada

```json
{
  "profile": {},
  "preferences": {},
  "facts": [],
  "todos": []
}
```

---

## Seguridad básica

- API Key obligatoria (`X-API-Key`)
- Validación de `session_id`
- Límite de tamaño de prompt
- Sin secretos en código

---

## Endpoints principales

### Chat
```
POST /chat
```

### Sesiones
```
POST   /sessions/new
GET    /sessions
GET    /sessions/{id}
POST   /sessions/{id}/reset
DELETE /sessions/{id}
```

### Summary
```
GET  /sessions/{id}/summary
PUT  /sessions/{id}/summary
POST /sessions/{id}/summary/reset
```

### Memoria estructurada
```
GET  /sessions/{id}/memory
PUT  /sessions/{id}/memory
POST /sessions/{id}/memory/reset
```

---

## Ejemplo curl

```bash
curl -X POST http://127.0.0.1:8000/chat   -H "Content-Type: application/json"   -H "X-API-Key: mi-clave-api-privada"   -d '{"prompt":"Hola, me llamo Antonio"}'
```

---

## Tests

```powershell
$env:API_KEY="test-key"
pytest
```


## Tests (pytest)

En Windows (PowerShell) recomendamos fijar `PYTHONPATH=src` para que los imports funcionen igual que en ejecución:

```powershell

$env:API_KEY="test-key"
$env:PYTHONPATH="src"
pytest -q

## Chequeos de seguridad

```powershell
pip-audit
bandit -r src -ll
$env:PYTHONIOENCODING="utf-8"
chcp 65001
semgrep --config=p/security-audit src
```

---

## Roadmap

- Usuarios + JWT
- Rate limiting
- RAG
- Persistencia en DB
- Agentes

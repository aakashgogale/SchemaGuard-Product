# SchemaGuard

**API Schema Registry & Breaking Change Detector**

Know before you ship. SchemaGuard detects breaking API changes
before they reach your consumers.

---

## What it does

Teams register their REST APIs, upload schema versions as JSON,
and SchemaGuard instantly classifies every change as breaking or safe.
A breaking change means existing consumers will break. A safe change
means it is backward compatible.

---

## Architecture

```
React (Vite) → REST API (Flask) → Service Layer → PostgreSQL
                    ↑
                Middleware
        (logger + error handler + auth guard)
```

**Request lifecycle:**
1. React sends request with JWT via Axios interceptor
2. Middleware logs request, validates JWT, sets request_id
3. Route receives request, delegates to service immediately
4. Service runs Pydantic validation, executes business logic
5. For version uploads: diff_engine.py runs pure comparison
6. Result persisted to PostgreSQL, returned as Pydantic response model

---

## Key technical decisions

### 1. Diff engine as a pure module
diff_engine.py has zero dependencies on Flask or SQLAlchemy.
It takes two dicts and returns a DiffResult dataclass.
This makes it trivially testable and easy to extract into a
separate package later. It also means it can run in CI without
a database.

### 2. Pydantic v2 for all input validation
All inputs are validated before touching the service layer.
Invalid data never reaches business logic or the database.
This prevents an entire class of bugs and makes error messages
consistent across all endpoints.

### 3. Status as an enum with enforced transitions
SchemaVersion status is not a free string. It is an enum
(PENDING → ACTIVE → DEPRECATED) enforced in the service layer.
Invalid transitions raise InvalidStatusTransitionError, preventing
the DB from ever holding an inconsistent state.

### 4. Middleware layer for cross-cutting concerns
Logging, error formatting, and auth token extraction are not
scattered across routes. They live in middleware/ and are
registered once on the app. Adding a new route gets all of
this for free.

### 5. API client layer in frontend
React components never call axios directly. They call typed
functions from api/client.js. This means the backend URL,
auth headers, and error handling logic exist in exactly one place.

---

## AI usage

Claude (claude-sonnet) was used to:
- Generate initial boilerplate for models, routes, and Pydantic schemas
- Suggest test cases for the diff engine
- Write the docker-compose configuration

All AI-generated code was reviewed line by line before committing.
The diff engine logic was manually verified against the test suite.
No AI output was committed without understanding what it does.

---

## Running locally

### With Docker (recommended)
```bash
cp .env.example .env
docker-compose up --build
```
Frontend: http://localhost:3000
Backend: http://localhost:5000
Health: http://localhost:5000/health

### Without Docker
```bash
# Backend
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql://localhost/schemaguard
flask db upgrade
python run.py

# Frontend
cd frontend
npm install
npm run dev
```

---

## Running tests
```bash
cd backend
pytest app/tests/ -v --tb=short
```

---

## Known tradeoffs and risks

1. **JWT in localStorage** — vulnerable to XSS. In production, use httpOnly cookies.
2. **No rate limiting** — auth endpoints can be brute-forced. Would add Flask-Limiter.
3. **Schema comparison is property-level** — does not validate full JSON Schema spec. Would integrate jsonschema library for production.
4. **No refresh tokens** — users must re-login when token expires.

---

## Extension approach

**Team workspaces:** Add an Organization model, move APIRegistry ownership from User to Organization, add a membership table with roles.

**Webhook notifications:** Add a Webhook model per registry. When a breaking change is detected in the upload version service, fire an async HTTP POST to registered URLs using Celery.

**CI/CD integration:** The diff endpoint is already a REST API. Teams can call it from GitHub Actions with two version IDs and fail the pipeline if `is_breaking: true`.

**Full JSON Schema validation:** Replace property-level diff with jsonschema library comparison for RFC-compliant analysis.

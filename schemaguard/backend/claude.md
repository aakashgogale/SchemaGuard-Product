# claude.md — SchemaGuard Backend AI Guidance

## Purpose
This file defines rules for AI agents working on the backend codebase.
It protects system integrity and enforces boundaries during AI-assisted development.

## Architecture invariants (never violate)
- Flask app uses application factory pattern — never use app global directly
- Routes are thin — zero business logic allowed in route handlers
- All input enters the system through Pydantic schemas — no raw request.json in services
- diff_engine.py is a pure module — no Flask, no SQLAlchemy, no side effects
- Middleware registers hooks on the app — never inline before_request logic in routes
- Status transitions are enforced in service layer only — not in routes or models

## What AI must never do
- Never skip Pydantic validation and write directly to models
- Never add logic inside route handlers — always move to services/
- Never change DiffResult or Change dataclass fields without updating all callers and tests
- Never hardcode secrets, URLs, or environment-specific values
- Never delete or modify existing tests — only add new ones
- Never use raw SQL in application code — SQLAlchemy ORM only
- Never return different error shapes from different endpoints — always use error_handler.py formats
- Never store passwords in plaintext — bcrypt only via werkzeug.security

## Code standards
- All Python functions: type hints + one-line docstring
- All service functions return typed dataclasses or Pydantic models, never raw dicts
- Max function length 40 lines — extract helpers beyond that
- snake_case Python
- No commented-out code in committed files

## Testing rules
- diff_engine.py must maintain 100% test coverage
- Every route must have success + at least one failure test
- Tests use SQLite in-memory — never connect to dev or prod DB
- All fixtures live in conftest.py

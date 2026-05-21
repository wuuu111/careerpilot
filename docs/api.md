# CareerPilot API

CareerPilot exposes a FastAPI application on `http://localhost:8000` by default.

## OpenAPI and Swagger

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- Health probe: `GET /health`

Swagger is the quickest way to inspect request and response shapes while Phase 3-4 is still moving.
Use a local login token from `/api/auth/login` and authorize with `Bearer <token>` for protected routes.

## Authentication

Authentication is JWT-based.

1. `POST /api/auth/register`
2. `POST /api/auth/login`
3. Pass `Authorization: Bearer <access_token>` on protected endpoints
4. Verify the session with `GET /api/auth/me`

The JWT secret must be set explicitly outside development. Do not reuse the example value from
`.env.example` in a shared or deployed environment.

## Core resource flow

### Resumes

- `POST /api/resumes/upload`
  - Multipart upload with a PDF or supported resume file
  - Extracts raw text and stores structured resume data plus embedding-ready text
- `GET /api/resumes`
- `GET /api/resumes/{resume_id}`

### Applications

- `POST /api/applications`
  - Accepts `resume_id`, `company_name`, `job_title`, and `job_description`
  - Persists the application plus JD analysis output
- `GET /api/applications`
- `GET /api/applications/{application_id}`
- `GET /api/applications/{application_id}/matching-report`

### Agent runs

- `POST /api/agent-runs`
  - Queues or executes the workflow depending on `CAREERPILOT_CELERY_TASK_ALWAYS_EAGER`
- `GET /api/agent-runs/{run_id}`
- `GET /api/agent-runs/{run_id}/steps`

### Generated outputs

- `POST /api/applications/{application_id}/cover-letter`
- `GET /api/applications/{application_id}/generated-outputs?type=<output_type>`

## Async execution model

CareerPilot supports two workflow modes:

- Development/test mode: `CAREERPILOT_CELERY_TASK_ALWAYS_EAGER=true`
  - The API executes the workflow inline and returns completed runs immediately
  - This is what the current smoke test uses with SQLite
- Real async mode: `CAREERPILOT_CELERY_TASK_ALWAYS_EAGER=false`
  - The API enqueues work on Redis and the Celery worker processes it separately
  - This is the expected mode for Docker Compose demos and deployment-style runs

In async mode, `POST /api/agent-runs` returns a queued run first. Poll `GET /api/agent-runs/{run_id}`
and `GET /api/agent-runs/{run_id}/steps` until the workflow completes.

## Storage notes

Phase 3-4 introduces a pgvector-ready Postgres path for knowledge retrieval. The API already stores
embedding-oriented text and metadata for resumes, job descriptions, and generated outputs. Compose
now provisions a pgvector-capable Postgres image so migrations can enable vector storage without
changing the local orchestration contract.

Current test and smoke coverage still use SQLite for determinism. That keeps CI lightweight while the
application-level vector features and database driver setup continue to mature.

## Provenance and data exposure

Generated output metadata and trace endpoints are useful for observability, but they can expose user
content or model context if handled carelessly.

- Do not expose raw private documents in response metadata unless the endpoint explicitly requires it.
- Prefer compact provenance fields such as source type, source id, and version markers.
- Keep Swagger and OpenAPI reachable only on trusted internal/demo environments if deployment policy
  requires it.

## Typical local sequence

Host-native:

```bash
uv sync --dev
uv run alembic upgrade head
uv run uvicorn careerpilot.api.main:app --reload
```

Compose-oriented async path:

```bash
docker compose -f infra/docker/docker-compose.yml up -d db redis
docker compose -f infra/docker/docker-compose.yml run --rm migrate
docker compose -f infra/docker/docker-compose.yml up api worker
```

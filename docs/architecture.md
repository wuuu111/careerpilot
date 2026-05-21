# CareerPilot Architecture

## Runtime shape

- `apps/web`: React + Vite frontend
- `apps/api`: FastAPI API with Swagger/OpenAPI and workflow orchestration endpoints
- `apps/worker`: Celery worker entrypoint for real async workflow execution
- `packages/shared`: TypeScript API contracts
- `infra/docker`: local orchestration for Postgres + pgvector, Redis, API, worker, and migrations

## Core flows

1. User authenticates with JWT.
2. Resume upload extracts raw text and structured resume data.
3. Application creation persists JD analysis and RAG-ready text fields.
4. Agent run either executes inline for tests or dispatches to Celery through Redis for async mode.
5. Generated outputs are stored by `output_type` and queried by latest version.

## Knowledge and retrieval boundary

- `resumes`, `job_descriptions`, and `generated_outputs` store `embedding_text` and `embedding_metadata`.
- `KnowledgeIngestionService` owns document normalization.
- Phase 3-4 adds a Postgres + pgvector deployment target so chunked/vector retrieval has a stable
  database boundary instead of remaining SQLite-only.

## Deployment shape

- Postgres is the system of record and the target home for pgvector-backed knowledge data.
- Redis is the Celery broker/backend and is required when `CAREERPILOT_CELERY_TASK_ALWAYS_EAGER=false`.
- The API serves `/docs`, `/openapi.json`, `/health`, auth routes, resume upload, application CRUD,
  workflow launch, and generated output retrieval.
- The worker consumes queued workflow jobs and updates run status/steps asynchronously.

## Security baseline

- JWT secrets must be set per environment; the example secret is only a placeholder.
- Default CORS behavior is local-development oriented through explicit localhost origins or regex.
- Provenance and trace payloads should favor IDs, source types, and summary metadata over raw user
  content when exposing retrieval context.

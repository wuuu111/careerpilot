FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY apps/api/src ./apps/api/src
COPY apps/worker ./apps/worker
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-cache-dir uv && uv pip install --system .

CMD ["python", "apps/worker/run_worker.py"]

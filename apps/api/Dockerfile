FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY apps/api/src ./apps/api/src
COPY apps/worker ./apps/worker
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-cache-dir uv && uv pip install --system .

EXPOSE 8000

CMD ["uvicorn", "careerpilot.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

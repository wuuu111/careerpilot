from __future__ import annotations

from careerpilot.config import settings
from careerpilot.db import SessionLocal
from careerpilot.models.run import AgentRun
from careerpilot.services.workflow import execute_full_application_workflow
from celery import Celery

celery_app = Celery("careerpilot", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_always_eager = settings.celery_task_always_eager


@celery_app.task(name="careerpilot.run_full_application")
def run_full_application(run_id: str) -> None:
    with SessionLocal() as session:
        run = session.get(AgentRun, run_id)
        if run:
            execute_full_application_workflow(session, run)

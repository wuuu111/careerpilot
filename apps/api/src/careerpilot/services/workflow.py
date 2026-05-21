from __future__ import annotations

from time import perf_counter
from typing import TypedDict

from careerpilot.errors import AppError
from careerpilot.models.application import Application
from careerpilot.models.company_profile import CompanyProfile
from careerpilot.models.generated_output import GeneratedOutput
from careerpilot.models.job_description import JobDescription
from careerpilot.models.resume import Resume
from careerpilot.models.run import AgentRun, AgentStep
from careerpilot.schemas.generated_outputs import GeneratedOutputContent
from careerpilot.schemas.jobs import JobDescriptionAnalysis
from careerpilot.schemas.resumes import ResumeParseResult
from careerpilot.services.generation import (
    build_cover_letter,
    build_evaluation,
    build_interview_prep,
    build_matching_report,
    build_rewritten_resume,
)
from careerpilot.services.knowledge import KnowledgeIngestionService, KnowledgeRetrievalService
from careerpilot.services.provider import DeepSeekProvider
from careerpilot.utils import utcnow
from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

AGENT_SEQUENCE = [
    "ResumeParserAgent",
    "JDAnalyzerAgent",
    "MatchingAgent",
    "PlannerAgent",
    "ResumeRewriteAgent",
    "CoverLetterAgent",
    "InterviewPrepAgent",
    "EvaluationAgent",
]


class WorkflowState(TypedDict):
    application_id: str
    user_id: str
    resume_parsed: ResumeParseResult
    jd_parsed: JobDescriptionAnalysis
    generated_outputs: list[GeneratedOutputContent]
    retrieved_context: list[dict[str, object]]


def _record_step(
    session: Session,
    *,
    run_id: str,
    agent_name: str,
    input_json: dict[str, object],
    output_json: dict[str, object] | None,
    status: str,
    error_message: str | None = None,
    latency_ms: int = 0,
) -> None:
    session.add(
        AgentStep(
            run_id=run_id,
            agent_name=agent_name,
            input_json=input_json,
            output_json=output_json,
            status=status,
            error_message=error_message,
            latency_ms=latency_ms,
        )
    )
    session.commit()


def _persist_output(
    session: Session,
    *,
    user_id: str,
    application_id: str,
    content: GeneratedOutputContent,
    knowledge_service: KnowledgeIngestionService,
) -> GeneratedOutput:
    created_at = utcnow()
    output = GeneratedOutput(
        application_id=application_id,
        output_type=content.output_type,
        content=content.content,
        output_metadata=content.metadata,
        embedding_text="",
        embedding_metadata={},
        created_at=created_at,
    )
    session.add(output)
    session.flush()
    document = knowledge_service.output_payload(
        user_id=user_id,
        application_id=application_id,
        output_id=output.id,
        generated=content,
        created_at=created_at,
    )
    output.embedding_text = document.embedding_text
    output.embedding_metadata = document.metadata
    knowledge_service.ingest_generated_output(
        session,
        user_id=user_id,
        application_id=application_id,
        output_id=output.id,
        generated=content,
        created_at=created_at,
    )
    session.commit()
    session.refresh(output)
    return output


def execute_full_application_workflow(session: Session, run: AgentRun) -> AgentRun:
    provider = DeepSeekProvider()
    knowledge_service = KnowledgeIngestionService()
    retrieval_service = KnowledgeRetrievalService()
    application = session.get(Application, run.application_id)
    if not application:
        raise AppError(
            "APPLICATION_NOT_FOUND",
            "Application not found.",
            404,
            {"application_id": run.application_id},
        )
    resume = session.get(Resume, application.resume_id)
    jd = session.get(JobDescription, application.jd_id)
    if not resume or not jd:
        raise AppError(
            "WORKFLOW_INPUT_MISSING",
            "Workflow inputs are incomplete.",
            400,
            {"application_id": application.id},
        )

    run.status = "running"
    session.commit()

    resume_parsed = ResumeParseResult.model_validate(resume.parsed_json)
    jd_parsed = JobDescriptionAnalysis.model_validate(jd.parsed_json)
    last_agent = "ResumeParserAgent"
    try:
        company_profile = session.scalar(
            select(CompanyProfile.content)
            .where(CompanyProfile.application_id == application.id)
            .limit(1)
        )

        def retrieve_context(query: str) -> list[dict[str, object]]:
            return retrieval_service.search(
                session,
                application_id=application.id,
                user_id=application.user_id,
                query=query,
                limit=6,
            )

        def safe_citations(items: list[dict[str, object]]) -> list[dict[str, object]]:
            safe_items: list[dict[str, object]] = []
            for item in items:
                metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
                metadata = metadata if isinstance(metadata, dict) else {}
                safe_items.append(
                    {
                        "source_type": metadata.get("source_type", "unknown"),
                        "source_subtype": metadata.get("source_subtype", "unknown"),
                        "created_at": metadata.get("created_at"),
                        "version": metadata.get("version"),
                        "excerpt": item.get("excerpt") or item.get("chunk_text") or "",
                    }
                )
            return safe_items

        def context_text(items: list[dict[str, object]]) -> str:
            lines: list[str] = []
            for item in safe_citations(items):
                lines.append(
                    f"[{item['source_type']}/{item['source_subtype']}] {item['excerpt']}"
                )
            return "\n".join(lines)

        def run_agent(agent_name: str, handler):
            def node(state: WorkflowState) -> WorkflowState:
                nonlocal last_agent
                last_agent = agent_name
                started = perf_counter()
                updates = handler(state)
                output_json = updates.get("output_json")
                latency_ms = int((perf_counter() - started) * 1000)
                _record_step(
                    session,
                    run_id=run.id,
                    agent_name=agent_name,
                    input_json={"application_id": application.id},
                    output_json=output_json,
                    status="success",
                    latency_ms=latency_ms,
                )
                next_state = dict(state)
                for key, value in updates.items():
                    if key != "output_json":
                        next_state[key] = value
                return next_state

            return node

        def persist_and_append(
            state: WorkflowState, generated: GeneratedOutputContent
        ) -> WorkflowState:
            generated.metadata.setdefault("citations", safe_citations(state["retrieved_context"]))
            persisted = _persist_output(
                session,
                user_id=application.user_id,
                application_id=application.id,
                content=generated,
                knowledge_service=knowledge_service,
            )
            return {
                **state,
                "generated_outputs": [*state["generated_outputs"], generated],
                "output_json": {"output_id": persisted.id, **generated.metadata},
            }

        graph = StateGraph(WorkflowState)
        graph.add_node(
            "ResumeParserAgent",
            run_agent(
                "ResumeParserAgent",
                lambda state: {"output_json": state["resume_parsed"].model_dump()},
            ),
        )
        graph.add_node(
            "JDAnalyzerAgent",
            run_agent(
                "JDAnalyzerAgent",
                lambda state: {"output_json": state["jd_parsed"].model_dump()},
            ),
        )
        graph.add_node(
            "MatchingAgent",
            run_agent(
                "MatchingAgent",
                lambda state: persist_and_append(
                    state,
                    build_matching_report(
                        state["resume_parsed"],
                        state["jd_parsed"],
                        context_text(state["retrieved_context"]),
                    ),
                ),
            ),
        )
        graph.add_node(
            "PlannerAgent",
            run_agent(
                "PlannerAgent",
                lambda state: {
                    "output_json": {
                        "priorities": state["jd_parsed"].required_skills[:3],
                        "strategy": "Rewrite bullets before generating application materials.",
                    }
                },
            ),
        )
        graph.add_node(
            "ResumeRewriteAgent",
            run_agent(
                "ResumeRewriteAgent",
                lambda state: persist_and_append(
                    state,
                    build_rewritten_resume(
                        state["resume_parsed"],
                        state["jd_parsed"],
                        context_text(state["retrieved_context"]),
                    ),
                ),
            ),
        )
        graph.add_node(
            "CoverLetterAgent",
            run_agent(
                "CoverLetterAgent",
                lambda state: persist_and_append(
                    state,
                    build_cover_letter(
                        state["resume_parsed"],
                        state["jd_parsed"],
                        provider,
                        style="technical",
                        language="en",
                        retrieved_context=state["retrieved_context"],
                    ),
                ),
            ),
        )
        graph.add_node(
            "InterviewPrepAgent",
            run_agent(
                "InterviewPrepAgent",
                lambda state: persist_and_append(
                    state,
                    build_interview_prep(
                        state["resume_parsed"],
                        state["jd_parsed"],
                        context_text(state["retrieved_context"]),
                    ),
                ),
            ),
        )
        graph.add_node(
            "EvaluationAgent",
            run_agent(
                "EvaluationAgent",
                lambda state: persist_and_append(
                    state,
                    build_evaluation(
                        state["generated_outputs"],
                        state["resume_parsed"],
                        state["jd_parsed"],
                        provider,
                        context_text(state["retrieved_context"]),
                    ),
                ),
            ),
        )

        graph.add_edge(START, AGENT_SEQUENCE[0])
        for current_agent, next_agent in zip(AGENT_SEQUENCE, AGENT_SEQUENCE[1:], strict=False):
            graph.add_edge(current_agent, next_agent)
        graph.add_edge(AGENT_SEQUENCE[-1], END)

        compiled = graph.compile()
        compiled.invoke(
            WorkflowState(
                application_id=application.id,
                user_id=application.user_id,
                resume_parsed=resume_parsed,
                jd_parsed=jd_parsed,
                generated_outputs=[],
                retrieved_context=retrieve_context(
                    " ".join(
                        [
                            jd.company_name,
                            jd.job_title,
                            jd.raw_text,
                            resume.raw_text,
                            company_profile or "",
                        ]
                    )
                ),
            )
        )

        run.status = "success"
        run.finished_at = utcnow()
        application.status = "completed"
        session.commit()
        session.refresh(run)
        return run
    except Exception as exc:
        run.status = "failed"
        run.finished_at = utcnow()
        application.status = "failed"
        session.commit()
        error_message = str(exc)
        _record_step(
            session,
            run_id=run.id,
            agent_name=last_agent,
            input_json={"application_id": application.id},
            output_json=None,
            status="failed",
            error_message=error_message,
            latency_ms=0,
        )
        raise AppError(
            "AGENT_STEP_FAILED",
            f"The workflow failed during {last_agent}.",
            500,
            {"agent_name": last_agent, "run_id": run.id},
        ) from exc

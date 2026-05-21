from __future__ import annotations

import json
from collections.abc import Iterable

from careerpilot.errors import AppError, not_found
from careerpilot.models.generated_output import GeneratedOutput
from careerpilot.schemas.generated_outputs import (
    GeneratedOutputCompareResponse,
    GeneratedOutputContent,
    GeneratedOutputHistoryItem,
    GeneratedOutputHistoryResponse,
    OutputType,
)
from sqlalchemy import desc, select
from sqlalchemy.orm import Session


def select_latest_output(
    output_type: OutputType, outputs: Iterable[GeneratedOutputContent]
) -> GeneratedOutputContent:
    candidates = [item for item in outputs if item.output_type == output_type]
    if not candidates:
        raise not_found(
            "GENERATED_OUTPUT_NOT_FOUND",
            f"No generated output found for type {output_type}.",
            output_type=output_type,
        )
    return sorted(candidates, key=lambda item: item.created_at or 0)[-1]


def fetch_latest_output_for_application(
    session: Session, application_id: str, output_type: OutputType
) -> GeneratedOutput:
    statement = (
        select(GeneratedOutput)
        .where(
            GeneratedOutput.application_id == application_id,
            GeneratedOutput.output_type == output_type,
        )
        .order_by(desc(GeneratedOutput.created_at))
    )
    output = session.scalar(statement)
    if not output:
        raise AppError(
            "GENERATED_OUTPUT_NOT_FOUND",
            f"No generated output found for type {output_type}.",
            404,
            {"application_id": application_id, "output_type": output_type},
        )
    return output


def fetch_output_history_for_application(
    session: Session, application_id: str, output_type: OutputType
) -> list[GeneratedOutput]:
    outputs = session.scalars(
        select(GeneratedOutput)
        .where(
            GeneratedOutput.application_id == application_id,
            GeneratedOutput.output_type == output_type,
        )
        .order_by(GeneratedOutput.created_at.asc())
    ).all()
    if not outputs:
        raise AppError(
            "GENERATED_OUTPUT_NOT_FOUND",
            f"No generated output found for type {output_type}.",
            404,
            {"application_id": application_id, "output_type": output_type},
        )
    return outputs


def _history_item(output: GeneratedOutput, version_index: int) -> GeneratedOutputHistoryItem:
    return GeneratedOutputHistoryItem(
        output_id=output.id,
        output_type=output.output_type,
        content=output.content,
        metadata=output.output_metadata,
        created_at=output.created_at,
        version=f"v{version_index}",
    )


def build_output_history_response(
    session: Session, application_id: str, output_type: OutputType
) -> GeneratedOutputHistoryResponse:
    outputs = fetch_output_history_for_application(session, application_id, output_type)
    items = [_history_item(output, index) for index, output in enumerate(outputs, start=1)]
    items.reverse()
    return GeneratedOutputHistoryResponse(output_type=output_type, items=items)


def build_output_compare_response(
    session: Session, application_id: str, output_type: OutputType
) -> GeneratedOutputCompareResponse:
    history = build_output_history_response(session, application_id, output_type)
    current = history.items[0]
    previous = history.items[1] if len(history.items) > 1 else None
    diff: dict[str, object] = {"changed_fields": []}
    if previous:
        current_json = _parse_output_json(current.content)
        previous_json = _parse_output_json(previous.content)
        changed_fields = sorted(
            {
                key
                for key in set(current_json) | set(previous_json)
                if current_json.get(key) != previous_json.get(key)
            }
        )
        diff = {
            "changed_fields": changed_fields,
            "current_created_at": current.created_at.isoformat(),
            "previous_created_at": previous.created_at.isoformat(),
        }
    return GeneratedOutputCompareResponse(
        output_type=output_type,
        current=current,
        previous=previous,
        diff=diff,
    )


def _parse_output_json(content: str) -> dict[str, object]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {"raw_content": content}
    return data if isinstance(data, dict) else {"value": data}

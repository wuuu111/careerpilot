from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from careerpilot.errors import AppError
from careerpilot.schemas.generated_outputs import GeneratedOutputContent
from careerpilot.services.generated_outputs import select_latest_output


def test_select_latest_output_returns_newest_item_for_type() -> None:
    older = GeneratedOutputContent(
        output_type="cover_letter",
        content="v1",
        metadata={},
        created_at=datetime(2026, 5, 20, tzinfo=UTC),
    )
    newer = GeneratedOutputContent(
        output_type="cover_letter",
        content="v2",
        metadata={},
        created_at=datetime(2026, 5, 20, tzinfo=UTC) + timedelta(minutes=5),
    )

    result = select_latest_output("cover_letter", [older, newer])

    assert result.content == "v2"


def test_select_latest_output_raises_standard_error_when_missing() -> None:
    with pytest.raises(AppError) as exc:
        select_latest_output("evaluation", [])

    assert exc.value.error_code == "GENERATED_OUTPUT_NOT_FOUND"
    assert exc.value.details["output_type"] == "evaluation"

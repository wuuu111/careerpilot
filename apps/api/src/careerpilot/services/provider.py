from __future__ import annotations

import json
import time
from dataclasses import dataclass

import httpx
from careerpilot.config import settings
from careerpilot.schemas.generated_outputs import GeneratedOutputContent
from careerpilot.schemas.jobs import JobDescriptionAnalysis
from careerpilot.schemas.resumes import ResumeParseResult
from careerpilot.schemas.workflow_outputs import (
    CoverLetterPayload,
    EvaluationPayload,
    InterviewPrepPayload,
    MatchingReportPayload,
    RewrittenResumePayload,
)


@dataclass(slots=True)
class DeepSeekProvider:
    model: str = "deepseek-chat"

    def _chat_json(self, prompt: str, schema_name: str) -> dict[str, object]:
        if not settings.deepseek_api_key:
            return {}
        for attempt in range(3):
            try:
                response = httpx.post(
                    f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.deepseek_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {
                                "role": "system",
                                "content": f"Return valid JSON for schema {schema_name}.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            except (httpx.HTTPError, json.JSONDecodeError):
                if attempt == 2:
                    raise
                time.sleep(0.5 * (attempt + 1))
        return {}

    def extract_resume_structured(self, raw_text: str) -> ResumeParseResult | None:
        data = self._chat_json(raw_text, "ResumeParseResult")
        return ResumeParseResult.model_validate(data) if data else None

    def analyze_job_description(
        self, company_name: str, job_title: str, job_description: str
    ) -> JobDescriptionAnalysis | None:
        data = self._chat_json(
            f"Company: {company_name}\nJob title: {job_title}\nDescription: {job_description}",
            "JobDescriptionAnalysis",
        )
        return JobDescriptionAnalysis.model_validate(data) if data else None

    def generate_text_output(
        self, output_type: str, prompt: str, metadata: dict[str, object] | None = None
    ) -> GeneratedOutputContent | None:
        data = self._chat_json(prompt, "GeneratedOutputContent")
        if data:
            data["output_type"] = output_type
            return GeneratedOutputContent.model_validate(data)
        return None

    def generate_matching_report(self, prompt: str) -> MatchingReportPayload | None:
        data = self._chat_json(prompt, "MatchingReportPayload")
        return MatchingReportPayload.model_validate(data) if data else None

    def generate_rewrite(self, prompt: str) -> RewrittenResumePayload | None:
        data = self._chat_json(prompt, "RewrittenResumePayload")
        return RewrittenResumePayload.model_validate(data) if data else None

    def generate_cover_letter_payload(self, prompt: str) -> CoverLetterPayload | None:
        data = self._chat_json(prompt, "CoverLetterPayload")
        return CoverLetterPayload.model_validate(data) if data else None

    def generate_interview_prep(self, prompt: str) -> InterviewPrepPayload | None:
        data = self._chat_json(prompt, "InterviewPrepPayload")
        return InterviewPrepPayload.model_validate(data) if data else None

    def generate_evaluation(self, prompt: str) -> EvaluationPayload | None:
        data = self._chat_json(prompt, "EvaluationPayload")
        return EvaluationPayload.model_validate(data) if data else None

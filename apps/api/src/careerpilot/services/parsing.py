from __future__ import annotations

import io
from pathlib import Path

import fitz
from careerpilot.errors import bad_request
from careerpilot.schemas.resumes import BasicInfo, ResumeParseResult
from docx import Document


def extract_text(file_name: str, content: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(content)
    if suffix == ".docx":
        return _extract_docx_text(content)
    raise bad_request("UNSUPPORTED_FILE_TYPE", "Only PDF and DOCX resumes are supported.")


def _extract_pdf_text(content: bytes) -> str:
    pdf = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text("text") for page in pdf)


def _extract_docx_text(content: bytes) -> str:
    document = Document(io.BytesIO(content))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def heuristic_resume_parse(raw_text: str) -> ResumeParseResult:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    skills = [
        line
        for line in lines
        if any(keyword in line.lower() for keyword in ["python", "fastapi", "sql", "react", "llm"])
    ]
    basic_name = lines[0] if lines else ""
    return ResumeParseResult(
        basic_info=BasicInfo(name=basic_name),
        education=[],
        skills=skills[:8],
        projects=[line for line in lines if "project" in line.lower()][:5],
        experience=[
            line for line in lines if "experience" in line.lower() or "intern" in line.lower()
        ][:5],
        awards=[],
    )

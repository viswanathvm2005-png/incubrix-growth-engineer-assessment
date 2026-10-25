"""Structured source intake workflow.

Validates candidate-provided text and Markdown files.
Does not generate content or call external services.
"""
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .source_documents import SourceDocumentError
from .source_workflow import validate_source


class SourceIntakeResult(BaseModel):
    """Machine-readable result of one source intake attempt."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ACCEPTED", "REJECTED"]
    source_id: str
    message: str
    input_path: str
    file_type: str | None = None
    sha256: str | None = None
    character_count: int | None = None
    normalized_text: str | None = None


def intake_source(
    path: str | Path,
    *,
    source_id: str,
    max_bytes: int = 5 * 1024 * 1024,
) -> SourceIntakeResult:
    """Validate a source and return a structured outcome.

    Rejected results intentionally avoid exposing raw exception details.
    """
    input_path = str(path)

    try:
        metadata, normalized_text = validate_source(
            path,
            source_id=source_id,
            max_bytes=max_bytes,
        )
    except (SourceDocumentError, OSError, ValueError):
        safe_source_id = (
            source_id.strip()
            if isinstance(source_id, str) and source_id.strip()
            else "UNKNOWN"
        )
        return SourceIntakeResult(
            status="REJECTED",
            source_id=safe_source_id,
            message=(
                "Source rejected. Check that the file exists, uses "
                ".txt or .md, is valid UTF-8, contains text, and is "
                "within the configured size limit."
            ),
            input_path=input_path,
        )

    return SourceIntakeResult(
        status="ACCEPTED",
        source_id=metadata.source_id,
        message=(
            "Source accepted for downstream processing. "
            "Acceptance does not verify the truth of its contents."
        ),
        input_path=metadata.input_path,
        file_type=metadata.file_type,
        sha256=metadata.sha256,
        character_count=len(normalized_text),
        normalized_text=normalized_text,
    )

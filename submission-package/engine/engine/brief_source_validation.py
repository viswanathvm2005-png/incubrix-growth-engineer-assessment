"""Validate source files referenced by a content brief.

This module checks file availability and technical validity only.
It does not prove that a source is accurate or supports a product claim.
"""
from pathlib import Path
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict

from .content_brief import ContentBrief
from .source_documents import SourceDocumentError
from .source_workflow import validate_source


class ValidatedSourceSummary(BaseModel):
    """Minimal metadata for a technically validated source."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    file_type: str
    sha256: str
    character_count: int


class BriefSourceValidationResult(BaseModel):
    """Validation outcome for the sources referenced by a brief."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ACCEPTED", "REJECTED"]
    brief_id: str
    message: str
    validated_sources: list[ValidatedSourceSummary]
    errors: list[str]


def validate_brief_sources(
    brief: ContentBrief,
    source_paths: Mapping[str, str | Path],
    *,
    max_bytes: int = 5 * 1024 * 1024,
) -> BriefSourceValidationResult:
    """Require every brief source ID to map to a valid source document."""
    validated: list[ValidatedSourceSummary] = []
    errors: list[str] = []

    for source_id in brief.source_ids:
        if source_id not in source_paths:
            errors.append(
                f"Source ID '{source_id}' has no registered file path."
            )
            continue

        try:
            metadata, text = validate_source(
                source_paths[source_id],
                source_id=source_id,
                max_bytes=max_bytes,
            )
        except (SourceDocumentError, OSError, ValueError):
            errors.append(
                f"Source ID '{source_id}' points to a missing, unsupported, "
                "unreadable, or invalid source file."
            )
            continue

        validated.append(
            ValidatedSourceSummary(
                source_id=metadata.source_id,
                file_type=metadata.file_type,
                sha256=metadata.sha256,
                character_count=len(text),
            )
        )

    if errors:
        return BriefSourceValidationResult(
            status="REJECTED",
            brief_id=brief.brief_id,
            message=(
                "Brief rejected because one or more source references "
                "could not be validated."
            ),
            validated_sources=validated,
            errors=errors,
        )

    return BriefSourceValidationResult(
        status="ACCEPTED",
        brief_id=brief.brief_id,
        message=(
            "All referenced source files passed technical validation. "
            "Factual accuracy and claim support still require review."
        ),
        validated_sources=validated,
        errors=[],
    )

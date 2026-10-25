"""Deterministic source intake workflow.

This module validates candidate-provided source documents only.
It does not generate content, infer product facts, or call external APIs.
"""
from pathlib import Path

from pydantic import ValidationError

from .schemas import SourceDocument
from .source_documents import SourceDocumentError, load_source_document


def validate_source(
    path: str | Path,
    *,
    source_id: str,
    max_bytes: int = 5 * 1024 * 1024,
) -> tuple[SourceDocument, str]:
    """Return validated source metadata and normalized source text.

    Raises SourceDocumentError when the source cannot be accepted.
    """
    if not source_id or not source_id.strip():
        raise SourceDocumentError("source_id must not be empty.")

    try:
        metadata, text = load_source_document(
            path,
            source_id=source_id.strip(),
            max_bytes=max_bytes,
        )
    except SourceDocumentError:
        raise
    except (OSError, ValueError, ValidationError) as exc:
        raise SourceDocumentError(
            f"Source validation failed: {exc}"
        ) from exc

    return metadata, text

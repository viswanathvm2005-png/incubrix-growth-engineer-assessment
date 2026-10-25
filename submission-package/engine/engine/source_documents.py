"""Safe, deterministic loading and validation of candidate-provided source documents.

Only UTF-8 .txt and .md files are accepted. This module does not infer product
facts or call external services.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from .schemas import SourceDocument


class SourceDocumentError(ValueError):
    """A source file is missing, unsupported, unreadable, or invalid."""


def load_source_document(
    path: str | Path,
    *,
    source_id: str,
    max_bytes: int = 5 * 1024 * 1024,
) -> tuple[SourceDocument, str]:
    """Validate and read a .txt/.md file, returning metadata and decoded text.

    The default 5 MiB limit is a safety guard, not a claim about the assessment's
    official limit. Pass a different positive max_bytes explicitly if needed.
    """
    file_path = Path(path)
    if max_bytes < 1:
        raise ValueError("max_bytes must be a positive integer.")
    suffix = file_path.suffix.lower()
    if suffix not in {".txt", ".md"}:
        raise SourceDocumentError("Unsupported file extension. Only .txt and .md are accepted.")
    try:
        if not file_path.exists():
            raise SourceDocumentError(f"Source file does not exist: {file_path}")
        if not file_path.is_file():
            raise SourceDocumentError("Source path must point to a regular file.")
        size = file_path.stat().st_size
        if size > max_bytes:
            raise SourceDocumentError(f"Source file exceeds the configured size limit ({max_bytes} bytes).")
        raw = file_path.read_bytes()
    except OSError as exc:
        raise SourceDocumentError(f"Could not read source file: {exc}") from exc

    if not raw:
        raise SourceDocumentError("Source file is empty.")
    try:
        text = raw.decode("utf-8-sig", errors="strict")
        # Normalize Windows (CRLF) and legacy Mac (CR) newlines to LF so
        # returned text is consistent across operating systems. The SHA-256
        # digest above intentionally remains over the original source bytes.
        text = text.replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise SourceDocumentError("Source file must be valid UTF-8 text.") from exc
    if not text.strip():
        raise SourceDocumentError("Source file contains only whitespace.")

    digest = hashlib.sha256(raw).hexdigest()
    try:
        metadata = SourceDocument(
            source_id=source_id,
            input_path=str(file_path.resolve()),
            file_type=suffix[1:],
            sha256=digest,
            received_at=datetime.now(timezone.utc),
        )
    except (ValidationError, OSError) as exc:
        raise SourceDocumentError(f"Source metadata is invalid: {exc}") from exc
    return metadata, text

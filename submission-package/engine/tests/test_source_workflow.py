from pathlib import Path

import pytest

from engine.source_workflow import validate_source
from engine.source_documents import SourceDocumentError


def test_valid_markdown_returns_metadata_and_text(tmp_path: Path):
    source = tmp_path / "source.md"
    source.write_text("# Candidate notes\n\nObserved details.\n", encoding="utf-8")

    metadata, text = validate_source(source, source_id="source-001")

    assert metadata.source_id == "source-001"
    assert metadata.file_type == "md"
    assert len(metadata.sha256) == 64
    assert "Observed details." in text


def test_valid_text_file_returns_txt_type(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("Candidate-provided source text.", encoding="utf-8")

    metadata, text = validate_source(source, source_id="source-002")

    assert metadata.file_type == "txt"
    assert text == "Candidate-provided source text."


def test_empty_source_id_is_rejected(tmp_path: Path):
    source = tmp_path / "source.md"
    source.write_text("Valid source text.", encoding="utf-8")

    with pytest.raises(SourceDocumentError, match="source_id"):
        validate_source(source, source_id="  ")


def test_missing_source_is_rejected(tmp_path: Path):
    with pytest.raises(SourceDocumentError, match="does not exist"):
        validate_source(
            tmp_path / "missing.md",
            source_id="source-003",
        )


def test_unsupported_extension_is_rejected(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text('{"text": "not supported"}', encoding="utf-8")

    with pytest.raises(SourceDocumentError, match="Unsupported file extension"):
        validate_source(source, source_id="source-004")


def test_source_size_limit_is_applied(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("1234567890", encoding="utf-8")

    with pytest.raises(SourceDocumentError, match="size limit"):
        validate_source(
            source,
            source_id="source-005",
            max_bytes=5,
        )


def test_whitespace_only_source_is_rejected(tmp_path: Path):
    source = tmp_path / "source.md"
    source.write_text("  \n\t ", encoding="utf-8")

    with pytest.raises(SourceDocumentError, match="only whitespace"):
        validate_source(source, source_id="source-006")


def test_newlines_are_normalized(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_bytes(b"first line\r\nsecond line\rthird line")

    metadata, text = validate_source(source, source_id="source-007")

    assert text == "first line\nsecond line\nthird line"
    assert len(metadata.sha256) == 64


def test_source_hash_represents_original_file_bytes(tmp_path: Path):
    import hashlib

    source = tmp_path / "source.txt"
    raw = b"first line\r\nsecond line"
    source.write_bytes(raw)

    metadata, text = validate_source(source, source_id="source-008")

    assert metadata.sha256 == hashlib.sha256(raw).hexdigest()
    assert text == "first line\nsecond line"

from pathlib import Path

import pytest

from engine.source_documents import SourceDocumentError, load_source_document


def test_loads_valid_utf8_txt_and_returns_sha256(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_text("Observed feature notes.\n", encoding="utf-8")
    metadata, text = load_source_document(source, source_id="source-001")
    assert text == "Observed feature notes.\n"
    assert metadata.file_type == "txt"
    assert len(metadata.sha256) == 64
    assert metadata.source_id == "source-001"


def test_loads_markdown_case_insensitive_extension(tmp_path: Path):
    source = tmp_path / "PRODUCT.MD"
    source.write_text("# Candidate observations\n", encoding="utf-8")
    metadata, text = load_source_document(source, source_id="md-1")
    assert metadata.file_type == "md"
    assert text.startswith("# Candidate")


def test_rejects_unsupported_extension_before_reading(tmp_path: Path):
    source = tmp_path / "notes.pdf"
    source.write_bytes(b"not read")
    with pytest.raises(SourceDocumentError, match="Only .txt and .md"):
        load_source_document(source, source_id="pdf-1")


def test_rejects_missing_file(tmp_path: Path):
    with pytest.raises(SourceDocumentError, match="does not exist"):
        load_source_document(tmp_path / "missing.txt", source_id="missing-1")


def test_rejects_empty_file(tmp_path: Path):
    source = tmp_path / "empty.txt"
    source.write_bytes(b"")
    with pytest.raises(SourceDocumentError, match="empty"):
        load_source_document(source, source_id="empty-1")


def test_rejects_whitespace_only_file(tmp_path: Path):
    source = tmp_path / "spaces.md"
    source.write_text("  \n\t", encoding="utf-8")
    with pytest.raises(SourceDocumentError, match="only whitespace"):
        load_source_document(source, source_id="spaces-1")


def test_rejects_invalid_utf8(tmp_path: Path):
    source = tmp_path / "bad.txt"
    source.write_bytes(b"hello\xffworld")
    with pytest.raises(SourceDocumentError, match="valid UTF-8"):
        load_source_document(source, source_id="bad-1")


def test_rejects_file_over_configured_size_limit(tmp_path: Path):
    source = tmp_path / "large.txt"
    source.write_text("123456789", encoding="utf-8")
    with pytest.raises(SourceDocumentError, match="size limit"):
        load_source_document(source, source_id="large-1", max_bytes=8)


def test_rejects_nonpositive_size_limit(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_text("ok", encoding="utf-8")
    with pytest.raises(ValueError, match="positive"):
        load_source_document(source, source_id="bad-limit", max_bytes=0)

from pathlib import Path

from engine.source_intake import intake_source


def test_valid_source_returns_structured_acceptance(tmp_path: Path):
    source = tmp_path / "notes.md"
    source.write_text("# Notes\nObserved feature.\n", encoding="utf-8")

    result = intake_source(source, source_id="source-101")

    assert result.status == "ACCEPTED"
    assert result.source_id == "source-101"
    assert result.file_type == "md"
    assert result.sha256 is not None
    assert len(result.sha256) == 64
    assert result.character_count == len(result.normalized_text)
    assert "Observed feature." in result.normalized_text
    assert "does not verify the truth" in result.message


def test_missing_file_returns_structured_rejection(tmp_path: Path):
    result = intake_source(
        tmp_path / "missing.txt",
        source_id="source-102",
    )

    assert result.status == "REJECTED"
    assert result.source_id == "source-102"
    assert result.sha256 is None
    assert result.normalized_text is None
    assert "Source rejected" in result.message


def test_unsupported_file_returns_rejection(tmp_path: Path):
    source = tmp_path / "notes.json"
    source.write_text('{"claim": "example"}', encoding="utf-8")

    result = intake_source(source, source_id="source-103")

    assert result.status == "REJECTED"
    assert result.file_type is None
    assert result.normalized_text is None


def test_whitespace_only_file_returns_rejection(tmp_path: Path):
    source = tmp_path / "blank.txt"
    source.write_text("   \n\t", encoding="utf-8")

    result = intake_source(source, source_id="source-104")

    assert result.status == "REJECTED"


def test_blank_source_id_returns_rejection(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_text("Candidate notes.", encoding="utf-8")

    result = intake_source(source, source_id="   ")

    assert result.status == "REJECTED"
    assert result.source_id == "UNKNOWN"


def test_size_limit_failure_returns_rejection(tmp_path: Path):
    source = tmp_path / "large.txt"
    source.write_text("1234567890", encoding="utf-8")

    result = intake_source(
        source,
        source_id="source-105",
        max_bytes=5,
    )

    assert result.status == "REJECTED"


def test_newlines_are_normalized_in_result(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_bytes(b"first\r\nsecond\rthird")

    result = intake_source(source, source_id="source-106")

    assert result.status == "ACCEPTED"
    assert result.normalized_text == "first\nsecond\nthird"


def test_result_can_be_serialized_to_json(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_text("Candidate-provided text.", encoding="utf-8")

    result = intake_source(source, source_id="source-107")
    payload = result.model_dump(mode="json")

    assert payload["status"] == "ACCEPTED"
    assert payload["source_id"] == "source-107"
    assert isinstance(payload["character_count"], int)

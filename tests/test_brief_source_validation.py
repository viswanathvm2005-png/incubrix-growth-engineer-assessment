from pathlib import Path

from engine.brief_source_validation import validate_brief_sources
from engine.content_brief import ContentBrief


def make_brief(**overrides):
    data = {
        "brief_id": "brief-201",
        "campaign_objective": "Explain a verified product feature",
        "target_audience": "Prospective customers",
        "platform": "linkedin",
        "content_format": "text_post",
        "source_ids": ["source-201"],
    }
    data.update(overrides)
    return ContentBrief(**data)


def test_registered_valid_source_is_accepted(tmp_path: Path):
    source = tmp_path / "source.md"
    source.write_text("Candidate-provided notes.", encoding="utf-8")

    result = validate_brief_sources(
        make_brief(),
        {"source-201": source},
    )

    assert result.status == "ACCEPTED"
    assert result.brief_id == "brief-201"
    assert result.errors == []
    assert len(result.validated_sources) == 1
    assert result.validated_sources[0].source_id == "source-201"
    assert len(result.validated_sources[0].sha256) == 64


def test_unregistered_source_id_is_rejected():
    result = validate_brief_sources(make_brief(), {})

    assert result.status == "REJECTED"
    assert result.validated_sources == []
    assert any("no registered file path" in error for error in result.errors)


def test_missing_file_is_rejected(tmp_path: Path):
    result = validate_brief_sources(
        make_brief(),
        {"source-201": tmp_path / "missing.md"},
    )

    assert result.status == "REJECTED"
    assert result.validated_sources == []
    assert len(result.errors) == 1


def test_unsupported_file_type_is_rejected(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text('{"notes": "example"}', encoding="utf-8")

    result = validate_brief_sources(
        make_brief(),
        {"source-201": source},
    )

    assert result.status == "REJECTED"


def test_empty_source_is_rejected(tmp_path: Path):
    source = tmp_path / "source.md"
    source.write_text("   \n", encoding="utf-8")

    result = validate_brief_sources(
        make_brief(),
        {"source-201": source},
    )

    assert result.status == "REJECTED"


def test_all_sources_must_be_valid(tmp_path: Path):
    first = tmp_path / "first.md"
    first.write_text("First source.", encoding="utf-8")

    brief = make_brief(source_ids=["source-a", "source-b"])

    result = validate_brief_sources(
        brief,
        {"source-a": first},
    )

    assert result.status == "REJECTED"
    assert len(result.validated_sources) == 1
    assert len(result.errors) == 1
    assert "source-b" in result.errors[0]


def test_size_limit_is_applied(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("This source is too large.", encoding="utf-8")

    result = validate_brief_sources(
        make_brief(),
        {"source-201": source},
        max_bytes=5,
    )

    assert result.status == "REJECTED"


def test_multiple_valid_sources_are_accepted(tmp_path: Path):
    first = tmp_path / "first.md"
    first.write_text("First source.", encoding="utf-8")
    second = tmp_path / "second.txt"
    second.write_text("Second source.", encoding="utf-8")

    brief = make_brief(source_ids=["source-a", "source-b"])

    result = validate_brief_sources(
        brief,
        {"source-a": first, "source-b": second},
    )

    assert result.status == "ACCEPTED"
    assert len(result.validated_sources) == 2
    assert {item.source_id for item in result.validated_sources} == {
        "source-a", "source-b"
    }


def test_result_can_be_serialized_to_json(tmp_path: Path):
    source = tmp_path / "source.md"
    source.write_text("Source notes.", encoding="utf-8")

    result = validate_brief_sources(
        make_brief(),
        {"source-201": source},
    )

    payload = result.model_dump(mode="json")

    assert payload["status"] == "ACCEPTED"
    assert payload["brief_id"] == "brief-201"
    assert payload["validated_sources"][0]["file_type"] == "md"


def test_rejected_result_does_not_expose_raw_exception(tmp_path: Path):
    result = validate_brief_sources(
        make_brief(),
        {"source-201": tmp_path / "missing.md"},
    )

    assert result.status == "REJECTED"
    assert str(tmp_path) not in " ".join(result.errors)

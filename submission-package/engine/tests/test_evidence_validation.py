from datetime import datetime, timezone
from pathlib import Path

from engine.evidence_validation import validate_capability_evidence
from engine.schemas import CapabilityEntry, CapabilityRegister


def make_entry(evidence_file: str) -> CapabilityEntry:
    return CapabilityEntry(
        capability_id="CAP-001",
        feature_name="Observed feature",
        what_I_observed="Candidate recorded an observation.",
        how_to_reproduce="Repeat the documented steps.",
        date_observed=datetime(2026, 10, 19, tzinfo=timezone.utc),
        evidence_file=evidence_file,
        confidence="candidate-confirmed",
        limitations="Only the documented scenario was observed.",
        allowed_claim_wording=["documented workflow"],
        forbidden_wording=["guaranteed results"],
    )


def make_register(evidence_file: str) -> CapabilityRegister:
    return CapabilityRegister(capabilities=[make_entry(evidence_file)])


def test_existing_markdown_evidence_passes(tmp_path: Path):
    evidence = tmp_path / "evidence" / "observation.md"
    evidence.parent.mkdir()
    evidence.write_text("# Observation\n\nCandidate-recorded evidence.\n", encoding="utf-8")

    result = validate_capability_evidence(
        make_register("evidence/observation.md"), tmp_path
    )[0]

    assert result.passed is True
    assert result.capability_id == "CAP-001"
    assert result.sha256 is not None
    assert "Human assessment" in result.message


def test_missing_evidence_fails(tmp_path: Path):
    result = validate_capability_evidence(
        make_register("evidence/missing.md"), tmp_path
    )[0]
    assert result.passed is False
    assert result.message == "Evidence file does not exist."


def test_absolute_evidence_path_fails(tmp_path: Path):
    absolute = str((tmp_path / "observation.md").resolve())
    result = validate_capability_evidence(make_register(absolute), tmp_path)[0]
    assert result.passed is False
    assert "relative" in result.message


def test_path_traversal_outside_project_fails(tmp_path: Path):
    result = validate_capability_evidence(
        make_register("../outside.md"), tmp_path
    )[0]
    assert result.passed is False
    assert "escapes" in result.message


def test_unsupported_extension_fails(tmp_path: Path):
    (tmp_path / "evidence.json").write_text('{"example": true}', encoding="utf-8")
    result = validate_capability_evidence(
        make_register("evidence.json"), tmp_path
    )[0]
    assert result.passed is False
    assert ".txt or .md" in result.message


def test_empty_evidence_file_fails(tmp_path: Path):
    (tmp_path / "evidence.md").write_bytes(b"")
    result = validate_capability_evidence(
        make_register("evidence.md"), tmp_path
    )[0]
    assert result.passed is False
    assert result.message == "Evidence file is empty."


def test_whitespace_only_evidence_fails(tmp_path: Path):
    (tmp_path / "evidence.md").write_text(" \n\t  ", encoding="utf-8")
    result = validate_capability_evidence(
        make_register("evidence.md"), tmp_path
    )[0]
    assert result.passed is False
    assert "only whitespace" in result.message


def test_invalid_utf8_evidence_fails(tmp_path: Path):
    (tmp_path / "evidence.txt").write_bytes(b"\xff\xfe\xfa")
    result = validate_capability_evidence(
        make_register("evidence.txt"), tmp_path
    )[0]
    assert result.passed is False
    assert "valid UTF-8" in result.message


def test_evidence_hash_changes_when_file_changes(tmp_path: Path):
    evidence = tmp_path / "evidence.md"
    evidence.write_text("First observation.", encoding="utf-8")
    first = validate_capability_evidence(
        make_register("evidence.md"), tmp_path
    )[0]

    evidence.write_text("Updated observation.", encoding="utf-8")
    second = validate_capability_evidence(
        make_register("evidence.md"), tmp_path
    )[0]

    assert first.passed is True
    assert second.passed is True
    assert first.sha256 != second.sha256


def test_empty_register_returns_no_evidence_checks(tmp_path: Path):
    result = validate_capability_evidence(CapabilityRegister(), tmp_path)
    assert result == []

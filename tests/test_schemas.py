from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from engine.schemas import (
    AssetFormat, AssetValidationReport, CapabilityEntry, CapabilityRegister,
    CapabilityReference, CheckKind, CheckStatus, ContentAsset, Platform,
    ReviewStatus, RunRecord, SourceDocument, ValidationCheck,
)

NOW = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
FAKE_HASH = "a" * 64


def make_asset(**overrides):
    values = {
        "asset_id": "test-asset-001", "source_id": "test-source-001",
        "platform": Platform.LINKEDIN, "format": AssetFormat.TEXT,
        "angle": "Test angle", "hook": "Test hook", "caption": "Test caption",
        "hashtags": ["ExampleTag"], "cta": "Learn more",
        "utm_url": "https://example.com/?utm_source=test",
        "target_metric": "link_clicks", "created_by_run_id": "test-run-001",
    }
    values.update(overrides)
    return values


def test_source_accepts_markdown():
    source = SourceDocument(source_id="s1", input_path="inputs/sample.md",
                            file_type="md", sha256=FAKE_HASH, received_at=NOW)
    assert source.file_type == "md"


def test_source_rejects_pdf():
    with pytest.raises(ValidationError):
        SourceDocument(source_id="s1", input_path="inputs/sample.pdf",
                       file_type="pdf", sha256=FAKE_HASH, received_at=NOW)


def test_claim_requires_capability_id():
    with pytest.raises(ValidationError):
        CapabilityReference(claim_text="A claim", capability_ids=[])


def test_duplicate_capability_ids_rejected():
    with pytest.raises(ValidationError):
        CapabilityReference(claim_text="A claim",
                            capability_ids=["CAP-001", "CAP-001"])


def test_video_requires_duration_and_ratio():
    with pytest.raises(ValidationError):
        ContentAsset(**make_asset(format=AssetFormat.VIDEO))


def test_video_over_sixty_seconds_rejected():
    with pytest.raises(ValidationError):
        ContentAsset(**make_asset(format=AssetFormat.VIDEO,
                                  video_duration_seconds=61, aspect_ratio="9:16"))


def test_valid_video_accepts_required_fields():
    asset = ContentAsset(**make_asset(format=AssetFormat.VIDEO,
                                      video_duration_seconds=30, aspect_ratio="9:16"))
    assert asset.video_duration_seconds == 30


def test_non_video_rejects_video_duration():
    with pytest.raises(ValidationError):
        ContentAsset(**make_asset(video_duration_seconds=30))


def test_reviews_start_pending():
    asset = ContentAsset(**make_asset())
    assert asset.usefulness_review == ReviewStatus.PENDING
    assert asset.accuracy_review == ReviewStatus.PENDING
    assert asset.rights_review == ReviewStatus.PENDING


def test_passing_human_check_requires_reviewer_and_timestamp():
    with pytest.raises(ValidationError):
        AssetValidationReport(asset_id="a1", version=1, checks=[
            ValidationCheck(check_id="rights", kind=CheckKind.HUMAN,
                            status=CheckStatus.PASS, description="Rights review")
        ])


def test_human_review_pending_is_not_passed():
    report = AssetValidationReport(asset_id="a1", version=1, checks=[
        ValidationCheck(check_id="rights", kind=CheckKind.HUMAN,
                        status=CheckStatus.NEEDS_HUMAN_REVIEW,
                        description="Rights review")
    ])
    assert report.all_checks_passed is False


def test_empty_capability_register_is_valid():
    assert CapabilityRegister(capabilities=[]).capabilities == []


def test_duplicate_capability_ids_in_register_rejected():
    entry = CapabilityEntry(
        capability_id="CAP-001", feature_name="Test-only fixture",
        what_I_observed="Fictional test observation.",
        how_to_reproduce="Test fixture steps.", date_observed=NOW,
        evidence_file="tests/fixtures/not-real.png", confidence="test only",
        limitations="Not product evidence.",
        allowed_claim_wording=["Test-only wording."],
        forbidden_wording=["Unsupported guarantee."]
    )
    with pytest.raises(ValidationError):
        CapabilityRegister(capabilities=[entry, entry])


def test_negative_runtime_rejected():
    with pytest.raises(ValidationError):
        RunRecord(run_id="r1", input_path="inputs/sample.md",
                  source_sha256=FAKE_HASH, started_at=NOW, runtime_seconds=-1)


def test_finish_before_start_rejected():
    with pytest.raises(ValidationError):
        RunRecord(run_id="r1", input_path="inputs/sample.md",
                  source_sha256=FAKE_HASH, started_at=NOW,
                  finished_at=datetime(2026, 10, 19, 11, 0, tzinfo=timezone.utc))

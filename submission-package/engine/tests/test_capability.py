
from datetime import datetime, timezone
from pathlib import Path

import pytest

from engine.capability import (
    CapabilityRegisterLoadError,
    build_validation_report,
    load_capability_register,
)
from engine.schemas import (
    AssetFormat,
    CapabilityEntry,
    CapabilityRegister,
    CapabilityReference,
    CheckKind,
    CheckStatus,
    ContentAsset,
    Platform,
    ReadinessStatus,
    ReviewStatus,
)


def make_asset(*, claims=None, format=AssetFormat.TEXT, duration=None, ratio=None):
    return ContentAsset(
        asset_id="asset-001",
        source_id="source-001",
        platform=Platform.LINKEDIN,
        format=format,
        angle="educational overview",
        hook="A sample hook",
        caption="A sample caption",
        cta="Learn more",
        utm_url="https://example.com/?utm_source=test",
        target_metric="engagement",
        product_claims=claims or [],
        video_duration_seconds=duration,
        aspect_ratio=ratio,
        created_by_run_id="run-001",
    )


def make_entry(**overrides):
    values = dict(
        capability_id="CAP-001",
        feature_name="Observed feature",
        what_I_observed="Candidate recorded an observation.",
        how_to_reproduce="Repeat the candidate's documented steps.",
        date_observed=datetime(2026, 10, 19, tzinfo=timezone.utc),
        evidence_file="evidence/observation.md",
        confidence="candidate-confirmed",
        limitations="Only the documented scenario was observed.",
        allowed_claim_wording=["documented workflow"],
        forbidden_wording=["guaranteed results", "100% accurate"],
    )
    values.update(overrides)
    return CapabilityEntry(**values)


def test_load_empty_register(tmp_path: Path):
    path = tmp_path / "capabilities.yaml"
    path.write_text("# intentionally empty\ncapabilities: []\n", encoding="utf-8")
    register = load_capability_register(path)
    assert register.capabilities == []


def test_load_valid_register(tmp_path: Path):
    path = tmp_path / "capabilities.yaml"
    path.write_text(
        "capabilities:\n"
        "  - capability_id: CAP-001\n"
        "    feature_name: Observed feature\n"
        "    what_I_observed: Candidate recorded an observation.\n"
        "    how_to_reproduce: Repeat documented steps.\n"
        "    date_observed: '2026-10-19T00:00:00Z'\n"
        "    evidence_file: evidence/observation.md\n"
        "    confidence: candidate-confirmed\n"
        "    limitations: Only the documented scenario was observed.\n"
        "    allowed_claim_wording: ['documented workflow']\n"
        "    forbidden_wording: ['guaranteed results']\n",
        encoding="utf-8",
    )
    assert load_capability_register(path).capabilities[0].capability_id == "CAP-001"


def test_missing_register_raises_clear_error(tmp_path: Path):
    with pytest.raises(CapabilityRegisterLoadError, match="Could not read"):
        load_capability_register(tmp_path / "missing.yaml")


def test_invalid_yaml_shape_is_rejected(tmp_path: Path):
    path = tmp_path / "capabilities.yaml"
    path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(CapabilityRegisterLoadError, match="mapping"):
        load_capability_register(path)


def test_duplicate_capability_ids_are_rejected_by_model():
    entry = make_entry()
    with pytest.raises(ValueError, match="unique"):
        CapabilityRegister(capabilities=[entry, entry])


def test_empty_register_blocks_any_product_claim():
    asset = make_asset(claims=[CapabilityReference(
        claim_text="This product supports a documented workflow.",
        capability_ids=["CAP-001"],
    )])
    report = build_validation_report(asset, CapabilityRegister())
    assert any(
        c.status == CheckStatus.FAIL and "unknown" in c.description
        for c in report.checks
    )
    assert asset.readiness_status == ReadinessStatus.BLOCKED


def test_no_claims_do_not_invent_product_claims_and_still_need_human_review():
    asset = make_asset()
    report = build_validation_report(asset, CapabilityRegister())
    assert any(
        c.check_id == "product_claims.none_present"
        and c.status == CheckStatus.PASS
        for c in report.checks
    )
    assert any(
        c.kind == CheckKind.HUMAN
        and c.status == CheckStatus.NEEDS_HUMAN_REVIEW
        for c in report.checks
    )
    assert asset.readiness_status == ReadinessStatus.DRAFT


def test_known_id_passes_reference_check_but_not_claim_truth():
    asset = make_asset(claims=[CapabilityReference(
        claim_text="This feature provides a documented workflow.",
        capability_ids=["CAP-001"],
    )])
    report = build_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
    )
    claim_checks = [
        c for c in report.checks
        if c.check_id.startswith("product_claims")
    ]
    assert len(claim_checks) == 1
    assert claim_checks[0].status == CheckStatus.PASS
    assert "not prove" in claim_checks[0].description
    assert asset.readiness_status == ReadinessStatus.DRAFT

def test_forbidden_wording_is_flagged_case_insensitively():
    asset = make_asset(claims=[CapabilityReference(
        claim_text="We provide GUARANTEED RESULTS.",
        capability_ids=["CAP-001"],
    )])
    report = build_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
    )
    assert any(
        c.status == CheckStatus.FAIL and "forbidden" in c.description
        for c in report.checks
    )
    assert asset.readiness_status == ReadinessStatus.BLOCKED


def test_unknown_id_is_not_hidden_by_another_known_id():
    asset = make_asset(claims=[CapabilityReference(
        claim_text="A documented workflow.",
        capability_ids=["CAP-001", "CAP-UNKNOWN"],
    )])
    report = build_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
    )
    assert any(
        c.status == CheckStatus.FAIL and "CAP-UNKNOWN" in c.description
        for c in report.checks
    )


def test_report_includes_three_distinct_human_review_gates():
    report = build_validation_report(make_asset(), CapabilityRegister())
    human_ids = {
        c.check_id for c in report.checks if c.kind == CheckKind.HUMAN
    }
    assert human_ids == {
        "human_review.usefulness",
        "human_review.accuracy",
        "human_review.rights",
    }


def test_claim_with_configured_allowed_phrase_passes_wording_check():
    asset = make_asset(claims=[CapabilityReference(
        claim_text="Explore our documented workflow today.",
        capability_ids=["CAP-001"],
    )])
    report = build_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
    )
    claim_checks = [
        check for check in report.checks
        if check.check_id.startswith("product_claims")
    ]
    assert len(claim_checks) == 1
    assert claim_checks[0].status == CheckStatus.PASS
    assert "not prove" in claim_checks[0].description


def test_known_capability_with_unsupported_wording_fails():
    asset = make_asset(claims=[CapabilityReference(
        claim_text="Our platform transforms every business.",
        capability_ids=["CAP-001"],
    )])
    report = build_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
    )
    assert any(
        check.check_id == "product_claims.claim_1.allowed_wording"
        and check.status == CheckStatus.FAIL
        for check in report.checks
    )
    assert asset.readiness_status == ReadinessStatus.BLOCKED


def test_forbidden_wording_check_normalizes_case_and_whitespace():
    asset = make_asset(claims=[CapabilityReference(
        claim_text="We offer GUARANTEED   RESULTS to everyone.",
        capability_ids=["CAP-001"],
    )])
    report = build_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
    )
    assert any(
        check.status == CheckStatus.FAIL
        and "forbidden wording" in check.description
        for check in report.checks
    )
    assert asset.readiness_status == ReadinessStatus.BLOCKED


def test_missing_capabilities_key_is_rejected(tmp_path: Path):
    path = tmp_path / "capabilities.yaml"
    path.write_text("other_key: []\n", encoding="utf-8")
    with pytest.raises(
        CapabilityRegisterLoadError,
        match="missing the 'capabilities' key",
    ):
        load_capability_register(path)


def test_human_approval_does_not_make_asset_ready():
    asset = make_asset()
    asset.usefulness_review = ReviewStatus.APPROVED
    asset.accuracy_review = ReviewStatus.APPROVED
    asset.rights_review = ReviewStatus.APPROVED

    report = build_validation_report(asset, CapabilityRegister())

    assert asset.readiness_status == ReadinessStatus.DRAFT
    assert not report.all_checks_passed
    assert all(
        check.status == CheckStatus.NEEDS_HUMAN_REVIEW
        for check in report.checks
        if check.kind == CheckKind.HUMAN
    )

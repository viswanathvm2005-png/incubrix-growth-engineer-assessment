from datetime import datetime, timezone
from pathlib import Path

from engine.asset_validation import build_asset_validation_report
from engine.schemas import (
    AssetFormat,
    CapabilityEntry,
    CapabilityReference,
    CapabilityRegister,
    CheckKind,
    CheckStatus,
    ContentAsset,
    Platform,
    ReadinessStatus,
)


def make_entry(evidence_file: str = "evidence/observation.md") -> CapabilityEntry:
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


def make_asset(claims=None) -> ContentAsset:
    return ContentAsset(
        asset_id="asset-001",
        source_id="source-001",
        platform=Platform.LINKEDIN,
        format=AssetFormat.TEXT,
        angle="educational overview",
        hook="A sample hook",
        caption="A sample caption",
        cta="Learn more",
        utm_url="https://example.com/?utm_source=test",
        target_metric="engagement",
        product_claims=claims or [],
        created_by_run_id="run-001",
    )


def test_missing_evidence_blocks_asset(tmp_path: Path):
    asset = make_asset([
        CapabilityReference(
            claim_text="Explore our documented workflow.",
            capability_ids=["CAP-001"],
        )
    ])

    report = build_asset_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
        tmp_path,
    )

    evidence_checks = [
        check for check in report.checks
        if check.check_id == "product_claims.evidence.CAP-001"
    ]
    assert len(evidence_checks) == 1
    assert evidence_checks[0].status == CheckStatus.FAIL
    assert asset.readiness_status == ReadinessStatus.BLOCKED


def test_valid_evidence_adds_pass_but_does_not_mark_asset_ready(tmp_path: Path):
    evidence = tmp_path / "evidence" / "observation.md"
    evidence.parent.mkdir()
    evidence.write_text(
        "# Candidate observation\n\nRecorded test steps and result.\n",
        encoding="utf-8",
    )
    asset = make_asset([
        CapabilityReference(
            claim_text="Explore our documented workflow.",
            capability_ids=["CAP-001"],
        )
    ])

    report = build_asset_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
        tmp_path,
    )

    evidence_checks = [
        check for check in report.checks
        if check.check_id == "product_claims.evidence.CAP-001"
    ]
    assert len(evidence_checks) == 1
    assert evidence_checks[0].status == CheckStatus.PASS
    assert "SHA-256" in evidence_checks[0].description
    assert asset.readiness_status == ReadinessStatus.DRAFT
    assert any(
        check.kind == CheckKind.HUMAN
        and check.status == CheckStatus.NEEDS_HUMAN_REVIEW
        for check in report.checks
    )


def test_evidence_for_unreferenced_capability_does_not_block_asset(
    tmp_path: Path,
):
    asset = make_asset()
    register = CapabilityRegister(capabilities=[make_entry()])

    report = build_asset_validation_report(asset, register, tmp_path)

    assert not any(
        check.check_id.startswith("product_claims.evidence.")
        for check in report.checks
    )
    assert asset.readiness_status == ReadinessStatus.DRAFT


def test_unknown_capability_id_still_blocks_asset(tmp_path: Path):
    asset = make_asset([
        CapabilityReference(
            claim_text="A documented workflow.",
            capability_ids=["CAP-UNKNOWN"],
        )
    ])

    report = build_asset_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
        tmp_path,
    )

    assert any(
        check.status == CheckStatus.FAIL
        and "CAP-UNKNOWN" in check.description
        for check in report.checks
    )
    assert asset.readiness_status == ReadinessStatus.BLOCKED


def test_valid_evidence_does_not_hide_unsupported_claim_wording(
    tmp_path: Path,
):
    evidence = tmp_path / "evidence" / "observation.md"
    evidence.parent.mkdir()
    evidence.write_text("Candidate-recorded observation.", encoding="utf-8")

    asset = make_asset([
        CapabilityReference(
            claim_text="Our platform transforms every business.",
            capability_ids=["CAP-001"],
        )
    ])

    report = build_asset_validation_report(
        asset,
        CapabilityRegister(capabilities=[make_entry()]),
        tmp_path,
    )

    assert any(
        check.check_id == "product_claims.claim_1.allowed_wording"
        and check.status == CheckStatus.FAIL
        for check in report.checks
    )
    assert any(
        check.check_id == "product_claims.evidence.CAP-001"
        and check.status == CheckStatus.PASS
        for check in report.checks
    )
    assert asset.readiness_status == ReadinessStatus.BLOCKED

from pathlib import Path

from engine.capability import build_validation_report
from engine.evidence_validation import validate_capability_evidence
from engine.schemas import (
    CapabilityRegister,
    CheckKind,
    CheckStatus,
    ContentAsset,
    ReadinessStatus,
    ValidationCheck,
)


def build_asset_validation_report(
    asset: ContentAsset,
    register: CapabilityRegister,
    project_root: str | Path,
):
    """Combine claim validation and evidence-file checks.

    Evidence-file checks establish only that referenced files are readable.
    They do not prove that the contents substantiate a product claim.
    Human review gates remain separate.
    """
    report = build_validation_report(asset, register)

    known_capabilities = {
        entry.capability_id: entry
        for entry in register.capabilities
    }

    referenced_ids = {
        capability_id
        for claim in asset.product_claims
        for capability_id in claim.capability_ids
        if capability_id in known_capabilities
    }

    # Do not let unrelated capabilities block this asset.
    if not referenced_ids:
        return report

    relevant_register = CapabilityRegister(
        capabilities=[
            entry
            for entry in register.capabilities
            if entry.capability_id in referenced_ids
        ]
    )

    evidence_results = validate_capability_evidence(
        relevant_register,
        project_root,
    )

    for result in evidence_results:
        description = (
            f"{result.capability_id}: {result.message}"
        )
        if result.sha256:
            description += f" SHA-256: {result.sha256}."

        report.checks.append(
            ValidationCheck(
                check_id=(
                    f"product_claims.evidence.{result.capability_id}"
                ),
                kind=CheckKind.AUTOMATED,
                status=(
                    CheckStatus.PASS
                    if result.passed
                    else CheckStatus.FAIL
                ),
                description=description,
                evidence_path=(
                    str(result.resolved_path)
                    if result.resolved_path is not None
                    else None
                ),
            )
        )

    if any(not result.passed for result in evidence_results):
        asset.readiness_status = ReadinessStatus.BLOCKED

    return report


"""Deterministic capability-register loading and product-claim checks.

Automated checks validate capability references and configured wording.
They do not establish factual truth; human accuracy review remains required.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .schemas import (
    AssetValidationReport,
    CapabilityRegister,
    CheckKind,
    CheckStatus,
    ContentAsset,
    ReadinessStatus,
    ReviewStatus,
    ValidationCheck,
)


class CapabilityRegisterLoadError(ValueError):
    """Raised when the YAML register cannot be safely loaded or validated."""


def load_capability_register(path: str | Path) -> CapabilityRegister:
    """Load a YAML capability register. An explicit empty register is valid."""
    register_path = Path(path)

    try:
        with register_path.open("r", encoding="utf-8") as handle:
            data: Any = yaml.safe_load(handle)
    except OSError as exc:
        raise CapabilityRegisterLoadError(
            f"Could not read capability register '{register_path}': {exc}"
        ) from exc
    except yaml.YAMLError as exc:
        raise CapabilityRegisterLoadError(
            f"Capability register YAML is invalid: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise CapabilityRegisterLoadError(
            "Capability register must be a YAML mapping with a 'capabilities' key."
        )

    if "capabilities" not in data:
        raise CapabilityRegisterLoadError(
            "Capability register is missing the 'capabilities' key."
        )

    try:
        return CapabilityRegister.model_validate(data)
    except ValidationError as exc:
        raise CapabilityRegisterLoadError(
            f"Capability register failed schema validation: {exc}"
        ) from exc


def _normalize_wording(text: str) -> str:
    """Normalize case and repeated whitespace for conservative phrase matching."""
    return re.sub(r"\s+", " ", text).strip().casefold()


def _contains_forbidden_wording(
    claim_text: str,
    forbidden_phrases: list[str],
) -> list[str]:
    """Return configured forbidden phrases found in the claim."""
    normalized_claim = _normalize_wording(claim_text)
    return [
        phrase
        for phrase in forbidden_phrases
        if _normalize_wording(phrase) in normalized_claim
    ]


def _has_allowed_wording(
    claim_text: str,
    allowed_phrases: list[str],
) -> bool:
    """Require at least one configured allowed phrase for each referenced capability.

    This is literal phrase matching, not semantic verification or proof of truth.
    """
    normalized_claim = _normalize_wording(claim_text)
    return any(
        _normalize_wording(phrase) in normalized_claim
        for phrase in allowed_phrases
        if phrase.strip()
    )


def build_validation_report(
    asset: ContentAsset,
    register: CapabilityRegister,
) -> AssetValidationReport:
    """Build automated claim checks plus explicit human-review gates."""
    checks: list[ValidationCheck] = []
    entries = {
        entry.capability_id: entry
        for entry in register.capabilities
    }

    if not asset.product_claims:
        checks.append(
            ValidationCheck(
                check_id="product_claims.none_present",
                kind=CheckKind.AUTOMATED,
                status=CheckStatus.PASS,
                description=(
                    "No product claims were supplied; no product claim "
                    "was authorized or inferred."
                ),
            )
        )
    else:
        for claim_index, claim in enumerate(asset.product_claims, start=1):
            check_prefix = f"product_claims.claim_{claim_index}"
            unknown_ids = [
                cap_id
                for cap_id in claim.capability_ids
                if cap_id not in entries
            ]

            if unknown_ids:
                checks.append(
                    ValidationCheck(
                        check_id=f"{check_prefix}.capability_ids",
                        kind=CheckKind.AUTOMATED,
                        status=CheckStatus.FAIL,
                        description=(
                            "Claim references unknown or unauthorized "
                            "capability ID(s): " + ", ".join(unknown_ids)
                        ),
                    )
                )
                continue

            if not claim.capability_ids:
                checks.append(
                    ValidationCheck(
                        check_id=f"{check_prefix}.capability_ids",
                        kind=CheckKind.AUTOMATED,
                        status=CheckStatus.FAIL,
                        description=(
                            "Claim has no capability ID and therefore "
                            "cannot be authorized."
                        ),
                    )
                )
                continue

            forbidden_hits: list[str] = []
            for cap_id in claim.capability_ids:
                forbidden_hits.extend(
                    f"{cap_id}: {phrase}"
                    for phrase in _contains_forbidden_wording(
                        claim.claim_text,
                        entries[cap_id].forbidden_wording,
                    )
                )

            if forbidden_hits:
                checks.append(
                    ValidationCheck(
                        check_id=f"{check_prefix}.forbidden_wording",
                        kind=CheckKind.AUTOMATED,
                        status=CheckStatus.FAIL,
                        description=(
                            "Configured forbidden wording detected: "
                            + "; ".join(forbidden_hits)
                        ),
                    )
                )
                continue

            unsupported_ids = [
                cap_id
                for cap_id in claim.capability_ids
                if not _has_allowed_wording(
                    claim.claim_text,
                    entries[cap_id].allowed_claim_wording,
                )
            ]

            if unsupported_ids:
                checks.append(
                    ValidationCheck(
                        check_id=f"{check_prefix}.allowed_wording",
                        kind=CheckKind.AUTOMATED,
                        status=CheckStatus.FAIL,
                        description=(
                            "Claim does not contain configured allowed "
                            "wording for capability ID(s): "
                            + ", ".join(unsupported_ids)
                        ),
                    )
                )
                continue

            checks.append(
                ValidationCheck(
                    check_id=f"{check_prefix}.reference_and_wording",
                    kind=CheckKind.AUTOMATED,
                    status=CheckStatus.PASS,
                    description=(
                        "Capability IDs exist and configured allowed "
                        "wording was found; no configured forbidden phrase "
                        "was detected. Literal phrase matching does not "
                        "prove that the claim is true. Human accuracy "
                        "review is still required."
                    ),
                )
            )

    # Automated code cannot approve these human-owned review gates.
    for review_name, review_status in (
        ("usefulness", asset.usefulness_review),
        ("accuracy", asset.accuracy_review),
        ("rights", asset.rights_review),
    ):
        if review_status == ReviewStatus.APPROVED:
            status = CheckStatus.NEEDS_HUMAN_REVIEW
            description = (
                f"{review_name.capitalize()} review is marked approved, "
                "but auditable reviewer and timestamp evidence is not "
                "represented in this schema."
            )
        elif review_status == ReviewStatus.REJECTED:
            status = CheckStatus.FAIL
            description = f"{review_name.capitalize()} review is marked rejected."
        else:
            status = CheckStatus.NEEDS_HUMAN_REVIEW
            description = (
                f"{review_name.capitalize()} review is pending and must "
                "be completed by a human."
            )

        checks.append(
            ValidationCheck(
                check_id=f"human_review.{review_name}",
                kind=CheckKind.HUMAN,
                status=status,
                description=description,
            )
        )

    report = AssetValidationReport(
        asset_id=asset.asset_id,
        version=asset.version,
        checks=checks,
    )

    has_failure = any(
        check.status == CheckStatus.FAIL
        for check in checks
    )
    has_pending_human = any(
        check.status == CheckStatus.NEEDS_HUMAN_REVIEW
        for check in checks
    )

    if has_failure:
        asset.readiness_status = ReadinessStatus.BLOCKED
    elif has_pending_human:
        asset.readiness_status = ReadinessStatus.DRAFT
    else:
        # READY remains unavailable until auditable human-review evidence
        # is represented and validated by the schema.
        asset.readiness_status = ReadinessStatus.DRAFT

    return report

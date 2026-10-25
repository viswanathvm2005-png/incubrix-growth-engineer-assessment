"""Validate capability evidence files without claiming they prove a product claim."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .schemas import CapabilityRegister


@dataclass(frozen=True)
class EvidenceFileCheck:
    capability_id: str
    evidence_file: str
    passed: bool
    message: str
    resolved_path: str | None = None
    sha256: str | None = None


def validate_capability_evidence(
    register: CapabilityRegister,
    project_root: str | Path,
) -> list[EvidenceFileCheck]:
    """Check evidence paths, supported file types, readability and content."""
    root = Path(project_root).resolve()
    results: list[EvidenceFileCheck] = []

    for entry in register.capabilities:
        reference = entry.evidence_file
        relative_path = Path(reference)

        if relative_path.is_absolute():
            results.append(EvidenceFileCheck(
                entry.capability_id, reference, False,
                "Evidence path must be relative to the project root.",
            ))
            continue

        try:
            candidate = (root / relative_path).resolve()
            candidate.relative_to(root)
        except (OSError, ValueError, RuntimeError):
            results.append(EvidenceFileCheck(
                entry.capability_id, reference, False,
                "Evidence path is invalid or escapes the project root.",
            ))
            continue

        if candidate.suffix.lower() not in {".txt", ".md"}:
            results.append(EvidenceFileCheck(
                entry.capability_id, reference, False,
                "Evidence must be a .txt or .md file.",
                str(candidate),
            ))
            continue

        try:
            if not candidate.exists():
                results.append(EvidenceFileCheck(
                    entry.capability_id, reference, False,
                    "Evidence file does not exist.", str(candidate),
                ))
                continue

            if not candidate.is_file():
                results.append(EvidenceFileCheck(
                    entry.capability_id, reference, False,
                    "Evidence path must point to a regular file.",
                    str(candidate),
                ))
                continue

            raw = candidate.read_bytes()
        except OSError as exc:
            results.append(EvidenceFileCheck(
                entry.capability_id, reference, False,
                f"Could not read evidence file: {exc}", str(candidate),
            ))
            continue

        digest = hashlib.sha256(raw).hexdigest()

        if not raw:
            results.append(EvidenceFileCheck(
                entry.capability_id, reference, False,
                "Evidence file is empty.", str(candidate), digest,
            ))
            continue

        try:
            text = raw.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError:
            results.append(EvidenceFileCheck(
                entry.capability_id, reference, False,
                "Evidence file must contain valid UTF-8 text.",
                str(candidate), digest,
            ))
            continue

        if not text.strip():
            results.append(EvidenceFileCheck(
                entry.capability_id, reference, False,
                "Evidence file contains only whitespace.",
                str(candidate), digest,
            ))
            continue

        results.append(EvidenceFileCheck(
            entry.capability_id, reference, True,
            "Evidence file exists and is readable. Human assessment is still "
            "required to determine whether it supports the claim.",
            str(candidate), digest,
        ))

    return results

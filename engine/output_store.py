"""Validated JSON persistence for content generation results."""

import json
import re
from pathlib import Path

from pydantic import ValidationError

from .generation_contract import GenerationResult, GenerationStatus


def _safe_filename_part(value: str) -> str:
    """Convert an identifier into a conservative filename component."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    cleaned = cleaned.strip(".-_")
    return cleaned[:80] or "unnamed"


def save_generation_result(
    result: dict,
    output_dir: str | Path = "outputs",
) -> dict:
    """Validate and save a successful generation result without overwriting."""
    if not isinstance(result, dict):
        raise ValueError("Generation result must be a JSON object.")

    # Validate the entire structure using the existing project schema.
    validated = GenerationResult.model_validate(result)

    if validated.status != GenerationStatus.SUCCESS:
        raise ValueError("Only successful generation results can be saved.")

    # Save normalized JSON produced by the validated model.
    result_data = validated.model_dump(mode="json")
    brief_id = validated.brief_id
    provider = validated.provider_name or "unknown-provider"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_name = (
        f"{_safe_filename_part(brief_id)}-"
        f"{_safe_filename_part(provider)}"
    )

    # Exclusive creation prevents silently overwriting an existing result.
    for version in range(1, 10000):
        suffix = "" if version == 1 else f"-{version}"
        destination = output_path / f"{base_name}{suffix}.json"

        try:
            with destination.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as handle:
                json.dump(
                    result_data,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
                handle.write("\n")

            return {
                "saved": True,
                "path": str(destination),
                "brief_id": brief_id,
                "provider_name": provider,
            }

        except FileExistsError:
            continue

    raise FileExistsError(
        "Could not find an unused output filename after 9999 attempts."
    )

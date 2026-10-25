"""CLI helpers for local asset history."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .asset_history import AssetHistory
from .schemas import ContentAsset


def _read_asset(path: str | Path) -> ContentAsset:
    """Read and validate one JSON ContentAsset."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Asset JSON could not be read or parsed.") from exc

    try:
        return ContentAsset.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(
            "Asset JSON does not match the ContentAsset schema."
        ) from exc


def save_asset(
    asset_path: str | Path,
    database_path: str | Path,
) -> dict[str, object]:
    asset = _read_asset(asset_path)
    return AssetHistory(database_path).save(asset)


def show_asset_history(
    asset_id: str,
    database_path: str | Path,
) -> dict[str, object]:
    if not asset_id.strip():
        raise ValueError("asset_id must not be empty.")
    history = AssetHistory(database_path).get_history(asset_id)
    return {
        "status": "FOUND" if history else "NOT_FOUND",
        "asset_id": asset_id,
        "versions": history,
    }


def revise_asset(
    asset_path: str | Path,
    database_path: str | Path,
) -> dict[str, object]:
    """Save the next version; enforce same identity and consecutive version."""
    asset = _read_asset(asset_path)
    history = AssetHistory(database_path)
    prior = history.get_history(asset.asset_id)

    if not prior:
        raise ValueError(
            "Cannot revise an asset with no saved history. Save version 1 first."
        )

    expected_version = int(prior[-1]["version"]) + 1
    if asset.version != expected_version:
        raise ValueError(
            f"Revision must be version {expected_version}; "
            f"received version {asset.version}."
        )

    return history.save(asset)


def find_asset_duplicates(
    asset_path: str | Path,
    database_path: str | Path,
    threshold: float,
) -> dict[str, object]:
    asset = _read_asset(asset_path)
    report = AssetHistory(database_path).check_duplicates(
        asset,
        threshold=threshold,
    )
    return {
        "status": report.status,
        "asset_id": asset.asset_id,
        "threshold": report.threshold,
        "message": report.message,
        "matches": [
            {
                "asset_id": match.asset_id,
                "version": match.version,
                "score": match.score,
                "reason": match.reason,
            }
            for match in report.matches
        ],
    }

"""Export the latest saved asset-history versions to the assessment calendar."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pydantic import ValidationError

from .asset_history import AssetHistory
from .calendar_adapter import asset_to_calendar_row
from .calendar_export import export_calendar_csv
from .schemas import ContentAsset


def export_latest_history_to_calendar(
    *,
    database_path: str | Path,
    schema_path: str | Path,
    output_path: str | Path,
    asset_ids: Iterable[str] | None = None,
) -> dict[str, object]:
    """Export the latest version of each selected saved asset.

    This operation does not approve, publish, or change any asset.
    Unknown candidate metadata is not invented.
    """
    history = AssetHistory(database_path)
    latest_records = history.latest_assets()

    if asset_ids is not None:
        requested_ids = list(dict.fromkeys(asset_ids))
        if any(not item.strip() for item in requested_ids):
            raise ValueError("Asset IDs must not be empty.")

        latest_by_id = {
            str(record["asset_id"]): record for record in latest_records
        }
        missing = [
            asset_id for asset_id in requested_ids
            if asset_id not in latest_by_id
        ]
        if missing:
            raise ValueError(
                "No saved asset history found for: " + ", ".join(missing)
            )
        selected = [latest_by_id[asset_id] for asset_id in requested_ids]
    else:
        selected = latest_records

    rows: list[dict[str, str]] = []
    exported_versions: list[dict[str, object]] = []

    for record in selected:
        asset_id = str(record["asset_id"])
        versions = history.get_history(asset_id)
        if not versions:
            raise ValueError(
                f"History disappeared while exporting asset {asset_id!r}."
            )

        latest = versions[-1]
        snapshot = latest.get("snapshot")
        if not isinstance(snapshot, dict):
            raise ValueError(
                f"Saved snapshot for {asset_id!r} is not a JSON object."
            )

        try:
            asset = ContentAsset.model_validate(snapshot)
        except ValidationError as exc:
            raise ValueError(
                f"Saved snapshot for {asset_id!r} failed asset validation."
            ) from exc

        if asset.asset_id != asset_id or asset.version != latest["version"]:
            raise ValueError(
                f"Saved snapshot identity/version mismatch for {asset_id!r}."
            )

        row = asset_to_calendar_row(
            asset,
            schema_path=schema_path,
            notes=f"asset_history_version: {asset.version}",
        )
        rows.append(row)
        exported_versions.append({
            "asset_id": asset.asset_id,
            "version": asset.version,
            "readiness_status": asset.readiness_status.value,
            "calendar_status": row["status"],
        })

    export_result = export_calendar_csv(
        rows,
        schema_path=schema_path,
        output_path=output_path,
    )

    return {
        "status": export_result["status"],
        "row_count": export_result["row_count"],
        "column_count": export_result["column_count"],
        "output_path": str(output_path),
        "selection": "latest saved version per asset",
        "assets": exported_versions,
        "message": (
            "Calendar CSV exported. No assets were approved or published. "
            "Review the CSV and fill candidate-owned metadata before use."
        ),
    }

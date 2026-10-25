"""Map validated ContentAsset records to the assessment calendar schema.

This adapter does not generate content, publish posts, or approve assets.
Unknown workbook fields remain blank and are explained in the notes field.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import AssetFormat, ContentAsset, Platform, ReadinessStatus, ReviewStatus


PLATFORM_LABELS = {
    Platform.LINKEDIN: "LinkedIn",
    Platform.INSTAGRAM: "Instagram",
    Platform.YOUTUBE_SHORTS: "YouTube Shorts",
    Platform.TIKTOK: "TikTok",
    Platform.X: "X",
    Platform.THREADS: "Threads",
    Platform.FACEBOOK: "Facebook",
    Platform.REDDIT: "Reddit",
}

FORMAT_LABELS = {
    AssetFormat.VIDEO: "Short video",
    AssetFormat.CAROUSEL: "Carousel",
    AssetFormat.GRAPHIC: "Graphic",
    AssetFormat.TEXT: "Text post",
}


class CalendarAdapterError(ValueError):
    """Raised when an asset cannot be mapped safely."""


def _read_schema(schema_path: str | Path) -> dict[str, Any]:
    path = Path(schema_path)
    try:
        schema = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CalendarAdapterError("Could not read workbook schema.") from exc

    columns = schema.get("columns")
    if (
        not isinstance(columns, list)
        or not columns
        or not all(isinstance(column, str) and column for column in columns)
        or len(columns) != len(set(columns))
    ):
        raise CalendarAdapterError("Workbook schema has invalid columns.")

    return schema


def asset_to_calendar_row(
    asset: ContentAsset,
    *,
    schema_path: str | Path,
    source_input: str | None = None,
    tools_used: str | None = None,
    final_file_url: str | None = None,
    source_file_url: str | None = None,
    ai_label_needed: str | None = None,
    test_published_url: str | None = None,
    notes: str | None = None,
    duplicate_check: str | None = None,
    completeness_check: str | None = None,
) -> dict[str, str]:
    """Convert one asset to the configured workbook columns.

    Values that cannot be established from the asset or explicit arguments
    are left blank. This function never infers metrics or human approvals.
    """
    schema = _read_schema(schema_path)
    columns = schema["columns"]
    allowed = schema.get("allowed_values", {})

    row = {column: "" for column in columns}

    platform = PLATFORM_LABELS.get(asset.platform)
    content_format = FORMAT_LABELS.get(asset.format)

    if platform is None:
        raise CalendarAdapterError("Asset platform has no workbook mapping.")
    if content_format is None:
        raise CalendarAdapterError("Asset format has no workbook mapping.")

    row.update({
        "asset_id": asset.asset_id,
        "platform": platform,
        "format": content_format,
        # angle is not assumed to be the content pillar.
        "content_pillar": "",
        "hook": asset.hook,
        "caption": asset.caption,
        "cta": asset.cta,
        "utm_link": str(asset.utm_url),
        "final_file_url": final_file_url or "",
        "source_file_url": source_file_url or "",
        "source_input": source_input or asset.source_id,
        "tools_used": tools_used or "",
        "rights_checked": (
            "Yes" if asset.rights_review == ReviewStatus.APPROVED else
            "No" if asset.rights_review == ReviewStatus.REJECTED else ""
        ),
        "ai_label_needed": ai_label_needed or "",
        "scheduled_date": (
            asset.scheduled_slot.isoformat()
            if asset.scheduled_slot is not None else ""
        ),
        "test_published_url": test_published_url or "",
        # No performance metrics are inferred.
        "impressions_or_views": "",
        "engagement_rate": "",
        "clicks": "",
        # Human review approval alone is not auditable evidence of readiness.
        "status": (
            "Ready"
            if asset.readiness_status == ReadinessStatus.READY
            and all(
                review == ReviewStatus.APPROVED
                for review in (
                    asset.usefulness_review,
                    asset.accuracy_review,
                    asset.rights_review,
                )
            )
            and bool(final_file_url)
            else "Draft"
        ),
        "notes": notes or "",
        "duplicate_check": duplicate_check or "",
        "completeness_check": completeness_check or "",
    })

    # Make uncertainty visible without inventing official product facts.
    warnings = []
    if not row["content_pillar"]:
        warnings.append("content_pillar: UNKNOWN - needs input from candidate")
    if not row["final_file_url"]:
        warnings.append("final_file_url: UNKNOWN - needs input from candidate")
    if not row["source_file_url"]:
        warnings.append("source_file_url: UNKNOWN - needs input from candidate")
    if not row["tools_used"]:
        warnings.append("tools_used: UNKNOWN - needs input from candidate")
    if not row["ai_label_needed"]:
        warnings.append("ai_label_needed: UNKNOWN - needs input from candidate")
    if not row["duplicate_check"]:
        warnings.append("duplicate_check: UNKNOWN - needs input from candidate")
    if not row["completeness_check"]:
        warnings.append("completeness_check: UNKNOWN - needs input from candidate")
    if not row["status"] == "Ready":
        warnings.append("Human review/readiness evidence does not establish Ready status")

    if warnings:
        existing_notes = row["notes"].strip()
        combined = "; ".join(warnings)
        row["notes"] = f"{existing_notes}; {combined}" if existing_notes else combined

    # Enforce workbook accepted values when a value is present.
    for column, choices in allowed.items():
        value = row.get(column, "")
        if value and isinstance(choices, list) and value not in choices:
            raise CalendarAdapterError(
                f"Mapped value for '{column}' is not accepted by the workbook schema."
            )

    # Return exactly the schema columns, in configured order.
    return {column: row.get(column, "") for column in columns}

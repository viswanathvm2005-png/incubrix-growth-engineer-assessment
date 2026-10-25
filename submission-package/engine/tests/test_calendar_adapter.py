import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from engine.calendar_adapter import (
    CalendarAdapterError,
    asset_to_calendar_row,
)
from engine.schemas import (
    AssetFormat,
    ContentAsset,
    Platform,
    ReadinessStatus,
    ReviewStatus,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "config" / "workbook-schema.json"


def make_asset(**overrides):
    values = {
        "asset_id": "asset-001",
        "source_id": "source-001",
        "platform": Platform.LINKEDIN,
        "format": AssetFormat.TEXT,
        "angle": "educational explanation",
        "hook": "A sample hook",
        "caption": "A sample caption",
        "cta": "Learn more",
        "utm_url": "https://example.com/?utm_source=test",
        "target_metric": "clicks",
        "created_by_run_id": "run-001",
    }
    values.update(overrides)
    return ContentAsset(**values)


def test_maps_core_fields_and_exact_workbook_columns():
    asset = make_asset()
    row = asset_to_calendar_row(asset, schema_path=SCHEMA_PATH)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))

    assert list(row) == schema["columns"]
    assert len(row) == 23
    assert row["asset_id"] == "asset-001"
    assert row["platform"] == "LinkedIn"
    assert row["format"] == "Text post"
    assert row["hook"] == "A sample hook"
    assert row["caption"] == "A sample caption"
    assert row["cta"] == "Learn more"
    assert row["utm_link"].startswith("https://example.com/")


def test_does_not_assume_angle_is_content_pillar():
    row = asset_to_calendar_row(make_asset(), schema_path=SCHEMA_PATH)
    assert row["content_pillar"] == ""
    assert "content_pillar: UNKNOWN - needs input from candidate" in row["notes"]


@pytest.mark.parametrize(
    ("platform", "expected"),
    [
        (Platform.LINKEDIN, "LinkedIn"),
        (Platform.INSTAGRAM, "Instagram"),
        (Platform.YOUTUBE_SHORTS, "YouTube Shorts"),
        (Platform.TIKTOK, "TikTok"),
        (Platform.X, "X"),
        (Platform.THREADS, "Threads"),
        (Platform.FACEBOOK, "Facebook"),
        (Platform.REDDIT, "Reddit"),
    ],
)
def test_maps_supported_platforms(platform, expected):
    row = asset_to_calendar_row(
        make_asset(platform=platform),
        schema_path=SCHEMA_PATH,
    )
    assert row["platform"] == expected


@pytest.mark.parametrize(
    ("asset_format", "expected"),
    [
        (AssetFormat.TEXT, "Text post"),
        (AssetFormat.GRAPHIC, "Graphic"),
        (AssetFormat.CAROUSEL, "Carousel"),
        (
            AssetFormat.VIDEO,
            "Short video",
        ),
    ],
)
def test_maps_supported_formats(asset_format, expected):
    extra = {}
    if asset_format == AssetFormat.VIDEO:
        extra = {"video_duration_seconds": 30, "aspect_ratio": "9:16"}
    row = asset_to_calendar_row(
        make_asset(format=asset_format, **extra),
        schema_path=SCHEMA_PATH,
    )
    assert row["format"] == expected


def test_unknown_metrics_remain_empty():
    row = asset_to_calendar_row(make_asset(), schema_path=SCHEMA_PATH)
    assert row["impressions_or_views"] == ""
    assert row["engagement_rate"] == ""
    assert row["clicks"] == ""


def test_draft_is_not_marked_ready():
    row = asset_to_calendar_row(
        make_asset(),
        schema_path=SCHEMA_PATH,
        final_file_url="https://example.com/final.mp4",
        ai_label_needed="No",
        tools_used="Manually entered",
        source_file_url="https://example.com/source.md",
        duplicate_check="Passed",
        completeness_check="Passed",
    )
    assert row["status"] == "Draft"


def test_approved_fields_without_ready_status_remain_draft():
    asset = make_asset(
        usefulness_review=ReviewStatus.APPROVED,
        accuracy_review=ReviewStatus.APPROVED,
        rights_review=ReviewStatus.APPROVED,
    )
    row = asset_to_calendar_row(
        asset,
        schema_path=SCHEMA_PATH,
        final_file_url="https://example.com/final.png",
    )
    assert row["status"] == "Draft"


def test_ready_status_still_requires_file_and_approvals():
    asset = make_asset(
        readiness_status=ReadinessStatus.READY,
        usefulness_review=ReviewStatus.APPROVED,
        accuracy_review=ReviewStatus.APPROVED,
        rights_review=ReviewStatus.APPROVED,
    )
    without_file = asset_to_calendar_row(asset, schema_path=SCHEMA_PATH)
    with_file = asset_to_calendar_row(
        asset,
        schema_path=SCHEMA_PATH,
        final_file_url="https://example.com/final.png",
    )
    assert without_file["status"] == "Draft"
    assert with_file["status"] == "Ready"


def test_supplied_candidate_values_are_preserved():
    row = asset_to_calendar_row(
        make_asset(),
        schema_path=SCHEMA_PATH,
        source_input="notes/source.md",
        tools_used="Python, Canva",
        final_file_url="https://example.com/final.png",
        source_file_url="https://example.com/editable",
        ai_label_needed="No",
        test_published_url="https://example.com/post",
        notes="Reviewed manually",
        duplicate_check="Passed",
        completeness_check="Passed",
    )
    assert row["source_input"] == "notes/source.md"
    assert row["tools_used"] == "Python, Canva"
    assert row["final_file_url"] == "https://example.com/final.png"
    assert row["source_file_url"] == "https://example.com/editable"
    assert row["ai_label_needed"] == "No"
    assert row["test_published_url"] == "https://example.com/post"
    assert row["notes"].startswith("Reviewed manually;")
    assert row["duplicate_check"] == "Passed"
    assert row["completeness_check"] == "Passed"


def test_rejects_invalid_workbook_schema(tmp_path):
    bad_schema = tmp_path / "bad.json"
    bad_schema.write_text(
        json.dumps({"columns": ["asset_id", "asset_id"]}),
        encoding="utf-8",
    )
    with pytest.raises(CalendarAdapterError, match="invalid columns"):
        asset_to_calendar_row(make_asset(), schema_path=bad_schema)


def test_scheduled_datetime_is_serialized():
    scheduled = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)
    row = asset_to_calendar_row(
        make_asset(scheduled_slot=scheduled),
        schema_path=SCHEMA_PATH,
    )
    assert row["scheduled_date"] == scheduled.isoformat()


import csv
import json
from pathlib import Path

import pytest

from engine.asset_history import AssetHistory
from engine.calendar_history_export import export_latest_history_to_calendar
from engine.schemas import AssetFormat, ContentAsset, Platform, ReadinessStatus


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "config" / "workbook-schema.json"


def make_asset(**overrides):
    values = {
        "asset_id": "calendar-history-001",
        "version": 1,
        "source_id": "source-calendar-001",
        "platform": Platform.LINKEDIN,
        "format": AssetFormat.TEXT,
        "angle": "educational explanation",
        "hook": "A sample hook",
        "caption": "A sample caption",
        "cta": "Learn more",
        "utm_url": "https://example.com/?utm_source=test",
        "target_metric": "clicks",
        "created_by_run_id": "calendar-export-test",
    }
    values.update(overrides)
    return ContentAsset(**values)


def test_exports_latest_version_only_and_preserves_draft(tmp_path):
    database = tmp_path / "history.sqlite3"
    output = tmp_path / "calendar.csv"
    history = AssetHistory(database)

    history.save(make_asset())
    history.save(make_asset(
        version=2,
        caption="Updated sample caption",
    ))

    result = export_latest_history_to_calendar(
        database_path=database,
        schema_path=SCHEMA_PATH,
        output_path=output,
    )

    assert result["status"] == "EXPORTED"
    assert result["row_count"] == 1
    assert result["assets"][0]["version"] == 2
    assert result["assets"][0]["calendar_status"] == "Draft"

    with output.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
    assert reader.fieldnames == schema["columns"]
    assert len(rows) == 1
    assert rows[0]["caption"] == "Updated sample caption"
    assert "asset_history_version: 2" in rows[0]["notes"]
    assert rows[0]["content_pillar"] == ""
    assert rows[0]["impressions_or_views"] == ""


def test_can_export_only_requested_asset_ids(tmp_path):
    database = tmp_path / "history.sqlite3"
    output = tmp_path / "selected.csv"
    history = AssetHistory(database)

    history.save(make_asset())
    history.save(make_asset(
        asset_id="calendar-history-002",
        source_id="source-calendar-002",
    ))

    result = export_latest_history_to_calendar(
        database_path=database,
        schema_path=SCHEMA_PATH,
        output_path=output,
        asset_ids=["calendar-history-002"],
    )

    assert result["row_count"] == 1
    assert [item["asset_id"] for item in result["assets"]] == [
        "calendar-history-002"
    ]


def test_unknown_asset_id_is_rejected(tmp_path):
    database = tmp_path / "history.sqlite3"

    with pytest.raises(ValueError, match="No saved asset history"):
        export_latest_history_to_calendar(
            database_path=database,
            schema_path=SCHEMA_PATH,
            output_path=tmp_path / "missing.csv",
            asset_ids=["does-not-exist"],
        )


def test_empty_history_exports_header_only_csv(tmp_path):
    database = tmp_path / "empty.sqlite3"
    output = tmp_path / "empty-calendar.csv"

    result = export_latest_history_to_calendar(
        database_path=database,
        schema_path=SCHEMA_PATH,
        output_path=output,
    )

    assert result["row_count"] == 0
    with output.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        assert len(header) == 23
        assert list(reader) == []


def test_ready_asset_without_final_file_url_is_still_draft(tmp_path):
    database = tmp_path / "history.sqlite3"
    output = tmp_path / "ready-check.csv"
    history = AssetHistory(database)

    history.save(make_asset(
        readiness_status=ReadinessStatus.READY,
    ))

    result = export_latest_history_to_calendar(
        database_path=database,
        schema_path=SCHEMA_PATH,
        output_path=output,
    )

    assert result["assets"][0]["calendar_status"] == "Draft"

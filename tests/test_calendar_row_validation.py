import csv
import json
from pathlib import Path

from engine.asset_history import AssetHistory
from engine.calendar_history_export import export_latest_history_to_calendar
from engine.schemas import AssetFormat, ContentAsset, Platform


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "config" / "workbook-schema.json"


def make_asset():
    return ContentAsset(
        asset_id="row-validation-001",
        version=1,
        source_id="source-row-validation-001",
        platform=Platform.LINKEDIN,
        format=AssetFormat.TEXT,
        angle="educational explanation",
        hook="A sample hook",
        caption="A sample caption",
        cta="Learn more",
        utm_url="https://example.com/?utm_source=test",
        target_metric="clicks",
        created_by_run_id="row-validation-test",
    )


def export_one_row(tmp_path):
    database = tmp_path / "history.sqlite3"
    output = tmp_path / "calendar.csv"

    AssetHistory(database).save(make_asset())

    result = export_latest_history_to_calendar(
        database_path=database,
        schema_path=SCHEMA_PATH,
        output_path=output,
        asset_ids=["row-validation-001"],
    )

    with output.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        headers = reader.fieldnames

    return result, headers, rows


def test_exported_headers_match_schema_in_exact_order(tmp_path):
    _, headers, rows = export_one_row(tmp_path)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))

    assert headers == schema["columns"]
    assert len(headers) == 23
    assert len(rows) == 1


def test_exported_platform_format_and_status_are_allowed(tmp_path):
    _, _, rows = export_one_row(tmp_path)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
    row = rows[0]

    for field in ("platform", "format", "status"):
        assert row[field] in schema["allowed_values"][field]


def test_exported_asset_id_is_not_empty(tmp_path):
    _, _, rows = export_one_row(tmp_path)

    assert rows[0]["asset_id"] == "row-validation-001"


def test_missing_candidate_file_urls_are_disclosed_in_notes(tmp_path):
    _, _, rows = export_one_row(tmp_path)
    notes = rows[0]["notes"]

    assert "final_file_url: UNKNOWN - needs input from candidate" in notes
    assert "source_file_url: UNKNOWN - needs input from candidate" in notes


def test_unprovided_metadata_is_not_fabricated(tmp_path):
    _, _, rows = export_one_row(tmp_path)
    row = rows[0]

    assert row["content_pillar"] == ""
    assert row["final_file_url"] == ""
    assert row["source_file_url"] == ""
    assert row["impressions_or_views"] == ""
    assert row["engagement_rate"] == ""
    assert row["clicks"] == ""


def test_exported_test_asset_remains_draft(tmp_path):
    result, _, rows = export_one_row(tmp_path)

    assert result["status"] == "EXPORTED"
    assert rows[0]["status"] == "Draft"
    assert result["assets"][0]["readiness_status"] == "draft"
    assert result["assets"][0]["calendar_status"] == "Draft"

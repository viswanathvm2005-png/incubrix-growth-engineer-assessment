import csv
import json
from pathlib import Path

from engine.calendar_adapter import asset_to_calendar_row
from engine.calendar_export import export_calendar_csv
from engine.schemas import AssetFormat, ContentAsset, Platform


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "config" / "workbook-schema.json"


def make_asset():
    return ContentAsset(
        asset_id="integration-asset-001",
        source_id="integration-source-001",
        platform=Platform.LINKEDIN,
        format=AssetFormat.TEXT,
        angle="educational explanation",
        hook="A verified sample hook",
        caption="A sample caption for integration testing.",
        cta="Learn more",
        utm_url="https://example.com/?utm_source=integration_test",
        target_metric="clicks",
        created_by_run_id="integration-run-001",
    )


def test_adapter_and_exporter_create_valid_csv(tmp_path):
    asset = make_asset()
    row = asset_to_calendar_row(asset, schema_path=SCHEMA_PATH)
    destination = tmp_path / "integration-calendar.csv"

    result = export_calendar_csv(
        [row],
        schema_path=SCHEMA_PATH,
        output_path=destination,
    )

    assert result["status"] == "EXPORTED"
    assert result["row_count"] == 1
    assert result["column_count"] == 23
    assert destination.exists()

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
    with destination.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == schema["columns"]
        rows = list(reader)

    assert len(rows) == 1
    exported = rows[0]
    assert exported["asset_id"] == "integration-asset-001"
    assert exported["platform"] == "LinkedIn"
    assert exported["format"] == "Text post"
    assert exported["hook"] == "A verified sample hook"
    assert exported["content_pillar"] == ""
    assert exported["impressions_or_views"] == ""
    assert exported["engagement_rate"] == ""
    assert exported["clicks"] == ""
    assert exported["status"] == "Draft"


def test_exported_csv_preserves_explicit_unknown_notes(tmp_path):
    row = asset_to_calendar_row(make_asset(), schema_path=SCHEMA_PATH)
    destination = tmp_path / "unknowns-calendar.csv"

    export_calendar_csv(
        [row],
        schema_path=SCHEMA_PATH,
        output_path=destination,
    )

    with destination.open("r", encoding="utf-8", newline="") as handle:
        exported = next(csv.DictReader(handle))

    assert (
        "content_pillar: UNKNOWN - needs input from candidate"
        in exported["notes"]
    )

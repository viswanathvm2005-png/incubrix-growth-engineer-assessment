import csv
import json
from pathlib import Path

import pytest

from engine.calendar_export import (
    CalendarExportError,
    export_calendar_csv,
    load_calendar_schema,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "config" / "workbook-schema.json"


def make_row():
    schema = load_calendar_schema(SCHEMA_PATH)
    return {column: "" for column in schema["columns"]}


def test_export_writes_exact_official_headers(tmp_path: Path):
    output = tmp_path / "calendar.csv"

    result = export_calendar_csv(
        [make_row()],
        schema_path=SCHEMA_PATH,
        output_path=output,
    )

    with output.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    schema = load_calendar_schema(SCHEMA_PATH)
    assert result["status"] == "EXPORTED"
    assert result["row_count"] == 1
    assert result["column_count"] == 23
    assert reader.fieldnames == schema["columns"]
    assert len(rows) == 1


def test_empty_rows_create_header_only_csv(tmp_path: Path):
    output = tmp_path / "calendar.csv"

    result = export_calendar_csv(
        [],
        schema_path=SCHEMA_PATH,
        output_path=output,
    )

    with output.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        remaining = list(reader)

    assert result["row_count"] == 0
    assert len(header) == 23
    assert remaining == []


def test_missing_column_is_rejected(tmp_path: Path):
    row = make_row()
    row.pop("caption")

    with pytest.raises(CalendarExportError, match="missing columns"):
        export_calendar_csv(
            [row],
            schema_path=SCHEMA_PATH,
            output_path=tmp_path / "calendar.csv",
        )


def test_unexpected_column_is_rejected(tmp_path: Path):
    row = make_row()
    row["invented_column"] = "not allowed"

    with pytest.raises(CalendarExportError, match="unexpected columns"):
        export_calendar_csv(
            [row],
            schema_path=SCHEMA_PATH,
            output_path=tmp_path / "calendar.csv",
        )


def test_invalid_platform_is_rejected(tmp_path: Path):
    row = make_row()
    row["platform"] = "UnknownPlatform"

    with pytest.raises(CalendarExportError, match="unsupported value"):
        export_calendar_csv(
            [row],
            schema_path=SCHEMA_PATH,
            output_path=tmp_path / "calendar.csv",
        )


def test_empty_metrics_remain_empty(tmp_path: Path):
    row = make_row()
    row["impressions_or_views"] = None
    row["engagement_rate"] = ""
    row["clicks"] = None
    output = tmp_path / "calendar.csv"

    export_calendar_csv(
        [row],
        schema_path=SCHEMA_PATH,
        output_path=output,
    )

    with output.open("r", encoding="utf-8", newline="") as handle:
        exported = next(csv.DictReader(handle))

    assert exported["impressions_or_views"] == ""
    assert exported["engagement_rate"] == ""
    assert exported["clicks"] == ""


def test_csv_escapes_commas_and_newlines(tmp_path: Path):
    row = make_row()
    row["caption"] = "First line, with comma\nSecond line"
    output = tmp_path / "calendar.csv"

    export_calendar_csv(
        [row],
        schema_path=SCHEMA_PATH,
        output_path=output,
    )

    with output.open("r", encoding="utf-8", newline="") as handle:
        exported = next(csv.DictReader(handle))

    assert exported["caption"] == "First line, with comma\nSecond line"


def test_non_csv_output_path_is_rejected(tmp_path: Path):
    with pytest.raises(CalendarExportError, match="end in .csv"):
        export_calendar_csv(
            [],
            schema_path=SCHEMA_PATH,
            output_path=tmp_path / "calendar.json",
        )


def test_invalid_schema_is_rejected(tmp_path: Path):
    bad_schema = tmp_path / "bad-schema.json"
    bad_schema.write_text(
        json.dumps({"columns": ["asset_id", "asset_id"]}),
        encoding="utf-8",
    )

    with pytest.raises(CalendarExportError, match="unique column names"):
        load_calendar_schema(bad_schema)


def test_multiple_rows_keep_their_order(tmp_path: Path):
    first = make_row()
    first["asset_id"] = "asset-001"
    second = make_row()
    second["asset_id"] = "asset-002"
    output = tmp_path / "calendar.csv"

    result = export_calendar_csv(
        [first, second],
        schema_path=SCHEMA_PATH,
        output_path=output,
    )

    with output.open("r", encoding="utf-8", newline="") as handle:
        exported = list(csv.DictReader(handle))

    assert result["row_count"] == 2
    assert [row["asset_id"] for row in exported] == [
        "asset-001", "asset-002"
    ]

import json
from pathlib import Path

import pytest

from engine.calendar_export import (
    CalendarExportError,
    export_calendar_csv,
    load_calendar_schema,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_SCHEMA = PROJECT_ROOT / "config" / "workbook-schema.json"


def read_schema():
    return json.loads(OFFICIAL_SCHEMA.read_text(encoding="utf-8-sig"))


def make_row(schema):
    return {column: "" for column in schema["columns"]} | {
        "asset_id": "safety-test-001",
        "platform": "LinkedIn",
        "format": "Text post",
        "status": "Draft",
    }


def write_schema(tmp_path, schema):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    return path


def test_export_rejects_row_with_missing_column(tmp_path):
    schema = read_schema()
    row = make_row(schema)
    del row["caption"]

    with pytest.raises(CalendarExportError, match="missing columns"):
        export_calendar_csv(
            [row],
            schema_path=OFFICIAL_SCHEMA,
            output_path=tmp_path / "calendar.csv",
        )


def test_export_rejects_row_with_extra_column(tmp_path):
    schema = read_schema()
    row = make_row(schema)
    row["invented_column"] = "unexpected"

    with pytest.raises(CalendarExportError, match="unexpected columns"):
        export_calendar_csv(
            [row],
            schema_path=OFFICIAL_SCHEMA,
            output_path=tmp_path / "calendar.csv",
        )


def test_export_rejects_unsupported_platform(tmp_path):
    schema = read_schema()
    row = make_row(schema)
    row["platform"] = "MadeUpPlatform"

    with pytest.raises(CalendarExportError, match="unsupported value"):
        export_calendar_csv(
            [row],
            schema_path=OFFICIAL_SCHEMA,
            output_path=tmp_path / "calendar.csv",
        )


def test_export_rejects_non_mapping_row(tmp_path):
    with pytest.raises(CalendarExportError, match="must be a mapping"):
        export_calendar_csv(
            ["not-a-row"],
            schema_path=OFFICIAL_SCHEMA,
            output_path=tmp_path / "calendar.csv",
        )


def test_export_rejects_non_scalar_field_value(tmp_path):
    schema = read_schema()
    row = make_row(schema)
    row["caption"] = {"unexpected": "object"}

    with pytest.raises(CalendarExportError, match="must be a scalar"):
        export_calendar_csv(
            [row],
            schema_path=OFFICIAL_SCHEMA,
            output_path=tmp_path / "calendar.csv",
        )


def test_export_rejects_non_csv_output_path(tmp_path):
    schema = read_schema()

    with pytest.raises(CalendarExportError, match="must end in .csv"):
        export_calendar_csv(
            [make_row(schema)],
            schema_path=OFFICIAL_SCHEMA,
            output_path=tmp_path / "calendar.json",
        )


def test_schema_loader_rejects_duplicate_columns(tmp_path):
    schema = read_schema()
    schema["columns"] = ["asset_id", "asset_id"]
    path = write_schema(tmp_path, schema)

    with pytest.raises(CalendarExportError, match="unique column names"):
        load_calendar_schema(path)


def test_schema_loader_rejects_empty_columns(tmp_path):
    schema = read_schema()
    schema["columns"] = []
    path = write_schema(tmp_path, schema)

    with pytest.raises(CalendarExportError, match="unique column names"):
        load_calendar_schema(path)


def test_schema_loader_rejects_missing_schema_file(tmp_path):
    with pytest.raises(CalendarExportError, match="Could not read"):
        load_calendar_schema(tmp_path / "missing-schema.json")

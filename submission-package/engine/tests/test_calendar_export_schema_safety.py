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


def write_schema(tmp_path, schema):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    return path


def make_row(schema):
    return {column: "" for column in schema["columns"]} | {
        "asset_id": "schema-safety-001",
        "platform": "LinkedIn",
        "format": "Text post",
        "status": "Draft",
    }


def test_schema_loader_rejects_non_object_json(tmp_path):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(["asset_id", "platform"]), encoding="utf-8")

    with pytest.raises(CalendarExportError):
        load_calendar_schema(path)


def test_export_rejects_non_mapping_allowed_values(tmp_path):
    schema = read_schema()
    schema["allowed_values"] = ["LinkedIn"]
    path = write_schema(tmp_path, schema)

    with pytest.raises(CalendarExportError):
        export_calendar_csv(
            [make_row(schema)],
            schema_path=path,
            output_path=tmp_path / "calendar.csv",
        )


def test_export_rejects_non_list_allowed_values(tmp_path):
    schema = read_schema()
    schema["allowed_values"]["platform"] = "LinkedIn"
    path = write_schema(tmp_path, schema)

    with pytest.raises(CalendarExportError):
        export_calendar_csv(
            [make_row(schema) | {"platform": "LinkedIn"}],
            schema_path=path,
            output_path=tmp_path / "calendar.csv",
        )


def test_export_rejects_invalid_delimiter_type(tmp_path):
    schema = read_schema()
    schema["csv_delimiter"] = 123
    path = write_schema(tmp_path, schema)

    with pytest.raises(CalendarExportError):
        export_calendar_csv(
            [make_row(schema)],
            schema_path=path,
            output_path=tmp_path / "calendar.csv",
        )


def test_export_rejects_multi_character_delimiter(tmp_path):
    schema = read_schema()
    schema["csv_delimiter"] = "||"
    path = write_schema(tmp_path, schema)

    with pytest.raises(CalendarExportError):
        export_calendar_csv(
            [make_row(schema)],
            schema_path=path,
            output_path=tmp_path / "calendar.csv",
        )

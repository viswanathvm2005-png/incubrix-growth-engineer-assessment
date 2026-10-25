"""Export asset rows to the official workbook-compatible calendar CSV."""
import csv
import json
from pathlib import Path
from typing import Mapping, Sequence


class CalendarExportError(ValueError):
    """Raised when asset rows do not match the official CSV schema."""


def load_calendar_schema(schema_path: str | Path) -> dict:
    """Load and validate the calendar schema configuration."""
    path = Path(schema_path)

    try:
        schema = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CalendarExportError(
            "Could not read the calendar schema."
        ) from exc

    if not isinstance(schema, dict):
        raise CalendarExportError(
            "Calendar schema must be a JSON object."
        )

    columns = schema.get("columns")
    if (
        not isinstance(columns, list)
        or not columns
        or not all(
            isinstance(column, str) and column.strip()
            for column in columns
        )
        or len(columns) != len(set(columns))
    ):
        raise CalendarExportError(
            "Schema must contain a non-empty list of unique column names."
        )

    allowed_values = schema.get("allowed_values", {})
    if not isinstance(allowed_values, dict):
        raise CalendarExportError(
            "Schema allowed_values must be an object."
        )

    for column, values in allowed_values.items():
        if column not in columns:
            raise CalendarExportError(
                f"Schema allowed_values contains unknown column '{column}'."
            )
        if not isinstance(values, list) or not all(
            isinstance(value, str) for value in values
        ):
            raise CalendarExportError(
                f"Schema allowed_values for '{column}' must be a list of strings."
            )

    delimiter = schema.get("csv_delimiter", ",")
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise CalendarExportError(
            "Schema csv_delimiter must be a single character."
        )

    return schema


def export_calendar_csv(
    rows: Sequence[Mapping[str, object]],
    *,
    schema_path: str | Path,
    output_path: str | Path,
) -> dict:
    """Export rows with the exact configured columns and column order.

    Empty values remain empty. This function does not generate content,
    infer metrics, or certify that assets are ready to publish.
    """
    schema = load_calendar_schema(schema_path)
    columns = schema["columns"]
    allowed_values = schema.get("allowed_values", {})
    delimiter = schema.get("csv_delimiter", ",")

    normalized_rows: list[dict[str, str]] = []

    for row_number, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise CalendarExportError(
                f"Row {row_number} must be a mapping of column names to values."
            )

        missing = [column for column in columns if column not in row]
        extra = [column for column in row if column not in columns]
        if missing or extra:
            details = []
            if missing:
                details.append("missing columns: " + ", ".join(missing))
            if extra:
                details.append(
                    "unexpected columns: " + ", ".join(map(str, extra))
                )
            raise CalendarExportError(
                f"Row {row_number} does not match the schema "
                f"({'; '.join(details)})."
            )

        normalized: dict[str, str] = {}
        for column in columns:
            value = row[column]
            if value is None:
                text = ""
            elif isinstance(value, (str, int, float, bool)):
                text = str(value)
            else:
                raise CalendarExportError(
                    f"Row {row_number}, column '{column}' "
                    "must be a scalar value."
                )

            allowed = allowed_values.get(column)
            if allowed is not None and text and text not in allowed:
                raise CalendarExportError(
                    f"Row {row_number}, column '{column}' "
                    "has an unsupported value."
                )

            normalized[column] = text

        normalized_rows.append(normalized)

    destination = Path(output_path)
    if destination.suffix.lower() != ".csv":
        raise CalendarExportError("Output path must end in .csv.")

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=columns,
                extrasaction="raise",
                delimiter=delimiter,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(normalized_rows)
    except (OSError, csv.Error) as exc:
        raise CalendarExportError(
            "Could not write the calendar CSV."
        ) from exc

    return {
        "status": "EXPORTED",
        "output_path": str(destination.resolve()),
        "row_count": len(normalized_rows),
        "column_count": len(columns),
        "columns": columns,
    }

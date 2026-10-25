"""Command-line entry point for exporting saved asset history to CSV."""
import argparse
import json
import sys

from .calendar_history_export import export_latest_history_to_calendar


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calendar-export",
        description=(
            "Export latest saved asset-history versions to the calendar CSV."
        ),
    )
    parser.add_argument(
        "--database",
        default="data/asset-history.sqlite3",
        help="SQLite asset-history database path.",
    )
    parser.add_argument(
        "--schema",
        default="config/workbook-schema.json",
        help="Configured workbook schema JSON path.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination CSV path.",
    )
    parser.add_argument(
        "--asset-id",
        action="append",
        dest="asset_ids",
        help=(
            "Optional asset ID to export. Repeat to select multiple assets. "
            "If omitted, exports the latest version of every saved asset."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = export_latest_history_to_calendar(
            database_path=args.database,
            schema_path=args.schema,
            output_path=args.output,
            asset_ids=args.asset_ids,
        )
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps({
            "status": "ERROR",
            "message": str(exc),
        }, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

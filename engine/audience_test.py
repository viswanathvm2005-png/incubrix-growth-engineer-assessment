"""Summarize real audience-test responses (launch-kit/audience-test-responses.csv).

Reads only what a human typed into the response sheet. It never creates or
estimates responses: an empty sheet reports 0 participants and "NOT COMPLETED".
Run: py -3.12 -m engine.audience_test --responses launch-kit/audience-test-responses.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

REQUIRED_PARTICIPANTS = 20
SCORE_FIELDS = ("clarity_1to5", "usefulness_1to5", "credibility_1to5")
COLUMNS = [
    "participant_id", "test_date", "consent_recorded", "audience_segment", "region",
    "pair_id", "asset_shown", "position_shown", "preferred_in_pair",
    "clarity_1to5", "usefulness_1to5", "credibility_1to5", "would_save_or_share", "feedback",
]


def _score(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    number = int(value)  # ValueError surfaces as a data problem below
    if not 1 <= number <= 5:
        raise ValueError(f"score {number} outside 1-5")
    return number


def summarize(path: str | Path) -> dict:
    problems: list[str] = []
    rows = []
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("Response sheet is missing columns: " + ", ".join(missing))
        for number, row in enumerate(reader, start=2):
            if not any((row.get(c) or "").strip() for c in COLUMNS):
                continue  # untouched template row
            rows.append((number, row))

    valid = []
    for number, row in rows:
        pid = (row["participant_id"] or "").strip()
        if not pid or not (row["asset_shown"] or "").strip():
            problems.append(f"row {number}: participant_id and asset_shown are required")
            continue
        if (row["consent_recorded"] or "").strip().lower() != "yes":
            problems.append(f"row {number}: consent_recorded is not 'yes' - excluded")
            continue
        try:
            scores = {f: _score(row[f]) for f in SCORE_FIELDS}
        except ValueError as exc:
            problems.append(f"row {number}: {exc}")
            continue
        valid.append((row, scores))

    participants = {r["participant_id"].strip() for r, _ in valid}
    per_asset: dict[str, dict] = {}
    by_asset = defaultdict(list)
    for row, scores in valid:
        by_asset[row["asset_shown"].strip()].append(scores)
    for asset, items in sorted(by_asset.items()):
        per_asset[asset] = {"n_ratings": len(items)}
        for field in SCORE_FIELDS:
            vals = [i[field] for i in items if i[field] is not None]
            per_asset[asset][field] = round(mean(vals), 2) if vals else None

    pairs = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # pair -> asset -> [preferred, shown]
    for row, _ in valid:
        pair = (row["pair_id"] or "").strip()
        flag = (row["preferred_in_pair"] or "").strip().upper()
        if not pair or flag not in {"Y", "N"}:
            continue
        counts = pairs[pair][row["asset_shown"].strip()]
        counts[1] += 1
        counts[0] += flag == "Y"
    preference = {
        pair: {a: {"preferred": c[0], "of": c[1], "share": round(c[0] / c[1], 2) if c[1] else None}
               for a, c in assets.items()}
        for pair, assets in pairs.items()
    }

    n = len(participants)
    return {
        "participants_with_consent": n,
        "required_participants": REQUIRED_PARTICIPANTS,
        "status": "NOT STARTED - no responses recorded" if n == 0 else
                  ("COMPLETE (minimum count reached)" if n >= REQUIRED_PARTICIPANTS
                   else f"INCOMPLETE - {n} of {REQUIRED_PARTICIPANTS} participants"),
        "per_asset_mean_scores": per_asset,
        "preference_by_pair": preference,
        "data_problems": problems,
        "limitations": "Small, non-random sample; results are indicative only and not "
                       "evidence of real-world engagement or conversion.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine.audience_test")
    parser.add_argument("--responses", default="launch-kit/audience-test-responses.csv")
    args = parser.parse_args(argv)
    try:
        result = summarize(args.responses)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "ERROR", "message": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

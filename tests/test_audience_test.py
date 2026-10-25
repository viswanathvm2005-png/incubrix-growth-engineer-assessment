"""Tests for the audience-test summarizer. Uses synthetic rows ONLY to test code;
they are never written to the real response sheet."""
import csv

from engine.audience_test import COLUMNS, main, summarize


def _write(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in COLUMNS})


def test_empty_template_reports_not_started(tmp_path):
    _write(tmp_path / "r.csv", [{}, {}])
    result = summarize(tmp_path / "r.csv")
    assert result["participants_with_consent"] == 0
    assert result["status"].startswith("NOT STARTED")


def test_shipped_template_is_empty(tmp_path):
    p = tmp_path / "empty_template.csv"
    _write(p, [])
    result = summarize(p)
    assert result["participants_with_consent"] == 0


def test_scores_preference_and_exclusions(tmp_path):
    rows = [
        {"participant_id": "P01", "consent_recorded": "yes", "pair_id": "A", "asset_shown": "X",
         "preferred_in_pair": "Y", "clarity_1to5": "5", "usefulness_1to5": "4", "credibility_1to5": "3"},
        {"participant_id": "P01", "consent_recorded": "yes", "pair_id": "A", "asset_shown": "Y",
         "preferred_in_pair": "N", "clarity_1to5": "3", "usefulness_1to5": "2", "credibility_1to5": "3"},
        {"participant_id": "P02", "consent_recorded": "no", "pair_id": "A", "asset_shown": "X",
         "preferred_in_pair": "Y", "clarity_1to5": "5"},
        {"participant_id": "P03", "consent_recorded": "yes", "pair_id": "A", "asset_shown": "X",
         "clarity_1to5": "9"},
    ]
    _write(tmp_path / "r.csv", rows)
    result = summarize(tmp_path / "r.csv")
    assert result["participants_with_consent"] == 1
    assert "INCOMPLETE" in result["status"]
    assert result["per_asset_mean_scores"]["X"]["clarity_1to5"] == 5
    assert result["preference_by_pair"]["A"]["X"] == {"preferred": 1, "of": 1, "share": 1.0}
    assert len(result["data_problems"]) == 2


def test_twenty_consenting_participants_reaches_minimum(tmp_path):
    rows = [{"participant_id": f"P{i:02d}", "consent_recorded": "yes", "asset_shown": "X"}
            for i in range(20)]
    _write(tmp_path / "r.csv", rows)
    assert summarize(tmp_path / "r.csv")["status"].startswith("COMPLETE")


def test_cli_reports_missing_file(tmp_path, capsys):
    assert main(["--responses", str(tmp_path / "none.csv")]) == 1

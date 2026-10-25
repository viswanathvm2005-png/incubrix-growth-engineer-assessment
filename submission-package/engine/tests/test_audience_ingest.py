"""Unit tests for engine.audience_ingest.

All test inputs use synthetic fixture data marked strictly as FAKE-TEST-DATA.
These fixtures run inside pytest's isolated tmp_path and are never copied to
launch-kit/ or submission-package/.
"""
import csv
from pathlib import Path
from engine.audience_ingest import ingest_workflow, match_hook_pick, parse_export_file


def test_hook_text_matching_and_inconsistency_detection():
    # 1. Normal match for Hook 1
    m1, inc1 = match_hook_pick("Hook 1: Posting feels chaotic? Build a repeatable content workflow.")
    assert m1 == "Hook 1"
    assert inc1 is None

    # 2. Conflicting label: Hook 2 prefix but Hook 1 text
    m2, inc2 = match_hook_pick("Hook 2: Posting feels chaotic? Build a repeatable content workflow.")
    assert m2 == "Hook 1"
    assert inc2 is not None
    assert "conflicted" in inc2

    # 3. Normal match for Hook 2
    m3, inc3 = match_hook_pick("Hook 2: One useful idea. Multiple content formats.")
    assert m3 == "Hook 2"
    assert inc3 is None


def test_screener_and_consent_exclusions_with_multiline_headers(tmp_path):
    raw_file = tmp_path / "FAKE-TEST-DATA-form.csv"
    headers = [
        "Timestamp",
        "Do you agree to take part, on the terms above?",
        "Which best describes you?",
        "Where are you mainly based?",
        "How long have you been creating or editing content?",
        'Hook 1: "Posting feels chaotic? Build a repeatable content workflow."\nHow likely are you to stop and read a post that opens like this?',
        'Hook 2: "One useful idea. Multiple content formats."\nHow likely are you to stop and read a post that opens like this?',
        "Which of these opening lines would you most likely save or share?",
        "For learning a practical content tip, which format do you prefer?",
        "What would make a post like these more useful to you? (optional, please don't include names)",
    ]

    rows = [
        # 1. Valid creator (consent Yes, valid role)
        [
            "2026/10/25 10:00:00 AM GMT+5:30",
            "Yes",
            "Creator (podcaster, YouTuber, expert-led creator)",
            "United States",
            "1-3 years",
            "4",
            "5",
            "Hook 1: Posting feels chaotic? Build a repeatable content workflow.",
            "Short video (under 60 seconds)",
            "Clear advice FAKE-TEST-DATA",
        ],
        # 2. Excluded by Screener: "None of these"
        [
            "2026/10/25 10:05:00 AM GMT+5:30",
            "Yes",
            "None of these",
            "India",
            "Less than 1 year",
            "5",
            "4",
            "Hook 2: Posting feels chaotic? Build a repeatable content workflow.",
            "Short video (under 60 seconds)",
            "",
        ],
        # 3. Excluded by Consent: "No"
        [
            "2026/10/25 10:10:00 AM GMT+5:30",
            "No",
            "Editor or someone who helps creators",
            "United Kingdom",
            "More than 3 years",
            "3",
            "3",
            "Hook 2: One useful idea. Multiple content formats.",
            "Swipe carousel (LinkedIn or Instagram)",
            "",
        ],
        # 4. Valid editor
        [
            "2026/10/25 10:15:00 AM GMT+5:30",
            "Yes",
            "Editor or someone who helps creators",
            "India",
            "Less than 1 year",
            "4",
            "4",
            "Hook 2: One useful idea. Multiple content formats.",
            "Short video (under 60 seconds)",
            "",
        ],
    ]

    with raw_file.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    out_resp = tmp_path / "FAKE-TEST-DATA-responses.csv"
    out_rep = tmp_path / "FAKE-TEST-DATA-report.md"

    res = ingest_workflow(raw_path=raw_file, responses_path=out_resp, report_path=out_rep)
    assert res["status"] == "INCOMPLETE"
    assert res["total_rows"] == 4
    assert res["excluded_count"] == 2  # 1 screener + 1 consent
    assert res["valid_n"] == 2

    report_text = out_rep.read_text(encoding="utf-8")
    assert "INCOMPLETE: n=2 of 20 required" in report_text
    assert "Screener Disqualifications" in report_text or "Disqualified via Screener" in report_text

    # Read responses CSV
    with out_resp.open(encoding="utf-8") as f:
        r_rows = list(csv.DictReader(f))
    assert len(r_rows) == 2
    assert [r["participant_id"] for r in r_rows] == ["P01", "P02"]
    # Check that timestamps were anonymised out
    assert "Timestamp" not in r_rows[0]

"""Tests for the one-command content pipeline (mock provider, no network)."""
import csv
import json
from pathlib import Path

import yaml

from engine.__main__ import main
from engine.calendar_export import load_calendar_schema
from engine.generation_contract import GeneratedDraft, GenerationResult, GenerationStatus
from engine.mock_provider import MockGenerationProvider
from engine.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
SOURCE_A = (
    "# Clips\n\nPodcasters record one long episode and must choose which moments become short clips for social platforms.\n\n"
    "Listen for specific examples, clear advice, and numbers that stand alone without any context at all.\n\n"
    "Captions help viewers who watch without sound because short lines match the spoken words on a phone.\n"
)
SOURCE_B = (
    "# Webinar\n\nA long webinar hides several ideas that could each become a post if written as single sentences.\n\n"
    "Pick a format for each idea such as a carousel checklist, a short demonstration video, or a text opinion.\n\n"
    "Read every caption aloud and remove any promise that you cannot support with evidence at publication time.\n"
)


def _config(tmp_path: Path, **overrides) -> Path:
    config = yaml.safe_load((ROOT / "config" / "pipeline-config.yaml").read_text(encoding="utf-8"))
    config["schema_path"] = str(ROOT / "config" / "workbook-schema.json")
    config["ledger_path"] = str(tmp_path / "ledger.json")
    config.update(overrides)
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def _run(tmp_path, text=SOURCE_A, source_id="src", provider=None, name="in.md", **kwargs):
    source = tmp_path / name
    source.write_text(text, encoding="utf-8")
    return run_pipeline(
        input_path=str(source), source_id=source_id,
        provider=provider or MockGenerationProvider(), provider_name="mock",
        config_path=str(kwargs.pop("config_path", _config(tmp_path))),
        out_dir=str(tmp_path / "out"), **kwargs,
    )


def _rows(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_new_input_produces_ten_plus_schema_exact_rows(tmp_path):
    record = _run(tmp_path, per_platform=4, start_date="2026-11-02")
    columns = load_calendar_schema(ROOT / "config" / "workbook-schema.json")["columns"]
    rows = _rows(record["run_calendar"])
    assert record["status"] == "succeeded"
    assert record["meets_10_asset_minimum"] is True
    assert len(rows) == record["items_exported"] == 12
    assert list(rows[0].keys()) == columns
    assert {r["platform"] for r in rows} == {"LinkedIn", "Instagram", "YouTube Shorts"}
    assert {r["status"] for r in rows} == {"Draft"}
    assert {r["rights_checked"] for r in rows} == {"No"}
    assert all(r["hook"] and r["caption"] and r["cta"] and "#" in r["caption"] for r in rows)
    assert all(r["scheduled_date"] for r in rows)
    assert record["runtime_seconds"] >= 0 and record["actual_cost_usd"] == 0.0


def test_tracking_url_is_unknown_unless_base_supplied(tmp_path):
    rows = _rows(_run(tmp_path)["run_calendar"])
    assert {r["utm_link"] for r in rows} == {"UNKNOWN - needs input from candidate"}

    rows = _rows(_run(tmp_path, text=SOURCE_B, source_id="b", name="b.md",
                      utm_base="https://example.test/start")["run_calendar"])
    first = next(r for r in rows if r["platform"] == "LinkedIn" or r["platform"] == "Instagram")
    source = "linkedin" if first["platform"] == "LinkedIn" else "instagram"
    assert first["utm_link"].startswith(f"https://example.test/start?utm_source={source}")
    assert f"utm_content={first['asset_id']}" in first["utm_link"]
    assert "utm_medium=organic_social" in first["utm_link"]


def test_repeat_run_is_idempotent_and_new_input_appends(tmp_path):
    first = _run(tmp_path)
    repeat = _run(tmp_path)
    assert repeat["duplicates_removed"] == 12 and repeat["items_exported"] == 0
    assert repeat["cumulative_rows"] == 12

    refresh = _run(tmp_path, text=SOURCE_B, source_id="b", name="b.md")
    assert refresh["items_exported"] == 12 and refresh["cumulative_rows"] == 24
    ids = [r["asset_id"] for r in _rows(refresh["cumulative_calendar"])]
    assert len(ids) == len(set(ids))
    assert first["source_sha256"] != refresh["source_sha256"]


def test_near_duplicates_in_a_batch_are_removed(tmp_path):
    class SameTwice:
        def generate(self, request):
            draft = lambda n: GeneratedDraft(
                draft_id=f"d{n}", content_format=request.brief.content_format,
                angle=f"angle {n}", hook=f"Plan your week of clips {'!' * n}",
                caption="Pick three moments with a clear example and add captions" + "." * n,
                call_to_action="Save this.", video_script=(["Line one", "Line two"]
                    if request.brief.content_format.value == "short_video" else None))
            return GenerationResult(brief_id=request.brief.brief_id,
                                    status=GenerationStatus.SUCCESS,
                                    drafts=[draft(1), draft(2)][: request.requested_draft_count])
    record = _run(tmp_path, provider=SameTwice(), per_platform=2)
    assert record["items_exported"] == 3
    assert record["duplicates_removed"] == 3


def test_brand_check_rejects_banned_phrase_and_missing_hashtags_get_defaults(tmp_path):
    class Banned:
        def generate(self, request):
            ok = request.brief.content_format.value != "short_video"
            return GenerationResult(
                brief_id=request.brief.brief_id, status=GenerationStatus.SUCCESS,
                drafts=[GeneratedDraft(
                    draft_id="x", content_format=request.brief.content_format, angle="a",
                    hook="Guaranteed growth in a week", caption="Short caption.",
                    call_to_action="Save.",
                    video_script=None if ok else ["one two three"])])
    record = _run(tmp_path, provider=Banned(), per_platform=1)
    assert record["items_exported"] == 0 and record["items_rejected"] == 3
    assert "banned phrase" in record["rejections"][0]["reasons"][0]


def test_rejected_source_is_logged_and_returns_failure(tmp_path, capsys):
    code = main(["pipeline", "--input", str(tmp_path / "missing.pdf"), "--source-id", "x",
                 "--config", str(_config(tmp_path)), "--out-dir", str(tmp_path / "out")])
    assert code == 1
    assert json.loads(capsys.readouterr().out)["error_codes"] == ["SOURCE_REJECTED"]
    log = (tmp_path / "out" / "pipeline.log").read_text(encoding="utf-8")
    assert "SOURCE_REJECTED" in log


def test_provider_failure_is_logged_retried_and_recovers(tmp_path):
    record = _run(tmp_path, simulate_failure_once=True)
    assert record["status"] == "succeeded" and record["items_exported"] == 12
    assert record["error_codes"] == ["PROVIDER_ERROR"]
    log = (tmp_path / "out" / "pipeline.log").read_text(encoding="utf-8")
    assert "batch_attempt_failed" in log and "batch_recovered" in log


def test_persistent_provider_failure_gives_partial_status(tmp_path):
    class Broken:
        def generate(self, request):
            if request.brief.platform.value == "instagram":
                raise RuntimeError("boom")
            return MockGenerationProvider().generate(request)
    record = _run(tmp_path, provider=Broken())
    assert record["status"] == "partial" and record["failed_batches"] == 1
    assert record["items_exported"] == 8


def test_corrupt_ledger_stops_the_run_instead_of_resetting(tmp_path):
    cfg = _config(tmp_path)
    (tmp_path / "ledger.json").write_text("{not json", encoding="utf-8")
    record = _run(tmp_path, config_path=cfg)
    assert record["status"] == "failed" and record["error_codes"] == ["CONFIG_ERROR"]
    assert "unreadable" in record["message"]
    assert (tmp_path / "ledger.json").read_text(encoding="utf-8") == "{not json"


def test_mock_run_record_is_labelled_not_a_real_measurement(tmp_path):
    record = _run(tmp_path)
    assert record["provider_kind"].startswith("MOCK")
    assert "NOT real-model measurements" in record["measurement_scope"]
    saved = json.loads(Path(record["run_calendar"]).parent.joinpath("run-record.json").read_text(encoding="utf-8"))
    assert saved["provider_kind"] == record["provider_kind"]


def test_pipeline_does_not_touch_official_workbook(tmp_path):
    import hashlib
    official = ROOT / "inputs" / "official_submission_workbook.xlsx"
    if not official.exists():
        return
    before = hashlib.sha256(official.read_bytes()).hexdigest()
    _run(tmp_path)
    assert hashlib.sha256(official.read_bytes()).hexdigest() == before


def test_refresh_flag_updates_existing_items_in_place(tmp_path):
    first = _run(tmp_path, text=SOURCE_A, source_id="src-1", name="a.md")
    first_ids = [r["asset_id"] for r in _rows(first["cumulative_calendar"])]
    refreshed = _run(tmp_path, text=SOURCE_B, source_id="src-1", name="b.md", refresh=True)
    assert refreshed["items_updated"] == 12
    assert refreshed["items_exported"] == 12
    assert refreshed["cumulative_rows"] == 12
    refreshed_rows = _rows(refreshed["cumulative_calendar"])
    assert [r["asset_id"] for r in refreshed_rows] == first_ids
    assert refreshed_rows[0]["caption"] != _rows(first["run_calendar"])[0]["caption"]

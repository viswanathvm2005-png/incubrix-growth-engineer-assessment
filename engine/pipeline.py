"""End-to-end content pipeline: one long input -> scheduler-ready calendar CSV.

Stages: source intake -> per-platform generation (with retry) -> brand checks ->
duplicate checks (within the run and against a persistent ledger) -> export in
the official 23-column workbook format -> run record with runtime and cost.

The pipeline writes drafts only. Every exported row is ``Draft`` with rights
unchecked: human review of accuracy, rights, and approval is still required, and
no final media files are produced here. Nothing is published or scheduled
externally. Unknown values (tracking URL, cost) stay explicitly unknown.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit

import yaml

from .calendar_export import export_calendar_csv, load_calendar_schema
from .content_brief import ContentBrief
from .factual_language_review import find_factual_language_flags
from .generation_contract import GenerationRequest
from .generation_workflow import GenerationWorkflow
from .source_intake import intake_source

UNKNOWN = "UNKNOWN - needs input from candidate"
_ID_PREFIX = {"linkedin": "LI", "instagram": "IG", "youtube_shorts": "YT"}


class PipelineError(RuntimeError):
    """Raised for configuration problems that make a run impossible."""


def load_config(path: str | Path) -> dict:
    try:
        config = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError) as exc:
        raise PipelineError(f"Could not read pipeline config: {path}") from exc
    if not isinstance(config, dict) or not config.get("platforms"):
        raise PipelineError("Pipeline config needs a non-empty 'platforms' map.")
    return config


def _normalize(text: str) -> str:
    text = re.sub(r"\[mock content[^\]]*\]", " ", text, flags=re.IGNORECASE)
    return " ".join(re.sub(r"[^\w\s]", " ", text.casefold()).split())


def _fingerprint(platform: str, hook: str, caption: str) -> str:
    return hashlib.sha256(
        f"{platform}|{_normalize(hook)}|{_normalize(caption)}".encode("utf-8")
    ).hexdigest()


def _paragraphs(text: str) -> list[str]:
    parts = [re.sub(r"^#+\s*", "", p.strip()) for p in re.split(r"\n\s*\n", text)]
    parts = [" ".join(p.split()) for p in parts if len(p.strip()) >= 40]
    return parts or [" ".join(text.split())[:1000]]


def _build_utm(base: str | None, platform_key: str, campaign: str, asset_id: str) -> str:
    if not base:
        return UNKNOWN
    parts = urlsplit(base)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise PipelineError("--utm-base must be an absolute http(s) URL.")
    source = {"youtube_shorts": "youtube"}.get(platform_key, platform_key)
    query = urlencode({
        "utm_source": source,
        "utm_medium": "organic_social",
        "utm_campaign": campaign,
        "utm_content": asset_id,
    })
    existing = f"{parts.query}&" if parts.query else ""
    return urlunsplit((parts.scheme, parts.netloc, parts.path, existing + query, ""))


class _Logger:
    """Append-only JSON-lines log. Never records secrets or raw API responses."""

    def __init__(self, path: Path, run_id: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path, self.run_id = path, run_id

    def log(self, level: str, event: str, **fields) -> None:
        record = {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": self.run_id, "level": level, "event": event, **fields,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def brand_check(draft, platform_cfg: dict, brand_cfg: dict, hashtags: list[str]) -> tuple[list[str], list[str]]:
    """Return (rejection_reasons, review_warnings) for one draft."""
    reasons: list[str] = []
    scripts = " ".join(draft.video_script or [])
    haystack = f"{draft.hook} {draft.caption} {scripts}".casefold()
    for phrase in brand_cfg.get("banned_phrases", []):
        if phrase.casefold() in haystack:
            reasons.append(f"banned phrase: {phrase!r}")
    if len(draft.hook) > platform_cfg.get("max_hook_chars", 150):
        reasons.append(f"hook longer than {platform_cfg.get('max_hook_chars', 150)} characters")
    full_caption = f"{draft.caption}\n\n{' '.join(hashtags)}"
    if len(full_caption) > platform_cfg.get("max_caption_chars", 3000):
        reasons.append("caption longer than platform limit")
    if brand_cfg.get("require_cta", True) and not draft.call_to_action.strip():
        reasons.append("missing call to action")
    if not hashtags:
        reasons.append("no hashtags")
    return reasons, find_factual_language_flags(draft.hook, draft.caption, scripts)


def _estimated_seconds(script: list[str] | None, words_per_second: float) -> float | None:
    if not script:
        return None
    return round(sum(len(line.split()) for line in script) / words_per_second, 1)


def _load_ledger(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        # A corrupt ledger must not silently reset duplicate protection.
        raise PipelineError(f"Ledger {path} is unreadable; fix or move it before running.")


def _save_ledger(path: Path, ledger: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def _merge_cumulative(path: Path, rows: list[dict], columns: list[str]) -> int:
    """Upsert rows by asset_id into the cumulative CSV; returns total row count."""
    import csv
    existing: dict[str, dict] = {}
    if path.exists():
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                existing[row["asset_id"]] = row
    for row in rows:
        existing[row["asset_id"]] = row
    return len(existing), list(existing.values())


def run_pipeline(
    *,
    input_path: str,
    source_id: str,
    provider,
    provider_name: str,
    config_path: str = "config/pipeline-config.yaml",
    out_dir: str = "outputs/pipeline-runs",
    per_platform: int = 4,
    utm_base: str | None = None,
    campaign: str = "incubrix_content_engine",
    start_date: str | None = None,
    cta: str = "Save this for your next content-planning session.",
    similarity_threshold: float | None = None,
    simulate_failure_once: bool = False,
    ledger_path: str | None = None,
    refresh: bool = False,
) -> dict:
    """Run the pipeline once and return a JSON-serializable run record."""
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc)
    config = load_config(config_path)
    threshold = similarity_threshold if similarity_threshold is not None else config.get("similarity_threshold", 0.85)
    out_root = Path(out_dir)
    stamp = started_at.strftime("%Y%m%dT%H%M%SZ")
    run_id = f"run-{stamp}"
    suffix = 1
    while (out_root / run_id).exists():  # never overwrite an earlier run's record
        suffix += 1
        run_id = f"run-{stamp}-{suffix}"
    run_dir = out_root / run_id
    logger = _Logger(out_root / "pipeline.log", run_id)
    record: dict = {
        "run_id": run_id, "input_path": str(input_path), "source_id": source_id,
        "provider": provider_name, "started_at": started_at.isoformat(timespec="seconds"),
        "status": "failed", "error_codes": [],
    }

    def finish(status: str) -> dict:
        record["status"] = status
        record["runtime_seconds"] = round(time.perf_counter() - started, 3)
        record["runtime_minutes"] = round(record["runtime_seconds"] / 60, 4)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run-record.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.log("INFO" if status != "failed" else "ERROR", "run_finished",
                   status=status, runtime_seconds=record["runtime_seconds"])
        return record

    logger.log("INFO", "run_started", input=str(input_path), provider=provider_name)

    intake = intake_source(input_path, source_id=source_id)
    if intake.status != "ACCEPTED":
        record["error_codes"].append("SOURCE_REJECTED")
        record["message"] = intake.message
        logger.log("ERROR", "source_rejected", code="SOURCE_REJECTED", input=str(input_path))
        return finish("failed")
    sha8 = intake.sha256[:8]
    record.update(source_sha256=intake.sha256, source_characters=intake.character_count)

    try:
        schema = load_calendar_schema(config.get("schema_path", "config/workbook-schema.json"))
        columns = schema["columns"]
        ledger_file = Path(ledger_path or config.get("ledger_path", "data/pipeline-ledger.json"))
        ledger = _load_ledger(ledger_file)
    except (PipelineError, ValueError) as exc:
        record["error_codes"].append("CONFIG_ERROR")
        record["message"] = str(exc)
        logger.log("ERROR", "config_error", code="CONFIG_ERROR", message=str(exc))
        return finish("failed")

    paragraphs = _paragraphs(intake.normalized_text or "")
    platforms = config["platforms"]
    brand_cfg = config.get("brand", {})
    max_attempts = int(config.get("max_attempts_per_batch", 2))
    wps = float(config.get("speaking_words_per_second", 2.5))
    first_day = date.fromisoformat(start_date) if start_date else None

    produced = rejected = duplicates = updated = failed_batches = 0
    rows: list[dict] = []
    rejections: list[dict] = []
    duplicate_log: list[dict] = []
    accepted_texts: dict[str, list[tuple[str, str]]] = {}  # platform -> [(asset_id, text)]
    prior_slots: dict[tuple[str, str, int], str] = {}
    for entry_id, entry in ledger.items():
        if entry.get("source_id") and entry.get("slot") is not None:
            prior_slots[(entry["source_id"], entry["platform"], int(entry["slot"]))] = entry_id
        if refresh and entry.get("source_id") == source_id:
            continue
        accepted_texts.setdefault(entry["platform"], []).append((entry_id, entry["text"]))
    simulated = simulate_failure_once

    for batch_no, (platform_key, cfg) in enumerate(platforms.items()):
        brief_data = {
            "brief_id": f"{source_id}-{platform_key}"[:100],
            "campaign_objective": "Turn one long input into platform-specific creator education",
            "target_audience": "Creators, podcasters, YouTubers and the editors and small teams who support them",
            "platform": cfg["brief_platform"], "content_format": cfg["brief_format"],
            "source_ids": [source_id], "capability_ids": [],
            "key_message": paragraphs[batch_no % len(paragraphs)][:1000],
            "tone": "clear, practical, no hype", "call_to_action": cta,
        }
        if cfg["brief_format"] == "short_video":
            brief_data["requested_duration_seconds"] = int(cfg.get("video_seconds", 30))
            brief_data["aspect_ratio"] = cfg.get("aspect_ratio", "9:16")
        result = None
        for attempt in range(1, max_attempts + 1):
            try:
                if simulated:
                    simulated = False
                    raise RuntimeError("Simulated provider failure (demo flag).")
                request = GenerationRequest(
                    request_id=f"{run_id}-{platform_key}"[:100],
                    brief=ContentBrief.model_validate(brief_data),
                    requested_draft_count=per_platform,
                )
                result = GenerationWorkflow(provider).run(request)
                break
            except Exception as exc:  # provider/network/validation: log and retry
                logger.log("ERROR", "batch_attempt_failed", code="PROVIDER_ERROR",
                           platform=platform_key, attempt=attempt, message=str(exc)[:300])
                if "PROVIDER_ERROR" not in record["error_codes"]:
                    record["error_codes"].append("PROVIDER_ERROR")
        if result is None:
            failed_batches += 1
            logger.log("ERROR", "batch_failed", code="BATCH_FAILED", platform=platform_key)
            continue
        if attempt > 1:
            logger.log("INFO", "batch_recovered", platform=platform_key, attempts=attempt)
        for warning in result.warnings:
            logger.log("WARN", "generation_warning", platform=platform_key, message=warning[:200])

        for index, draft in enumerate(result.drafts, start=1):
            produced += 1
            default_id = f"{_ID_PREFIX.get(platform_key, platform_key[:2].upper())}-{sha8}-{index:02d}"
            asset_id = prior_slots.get((source_id, platform_key, index), default_id) if refresh else default_id
            hashtags = list(draft.hashtags) or list(cfg.get("default_hashtags", []))
            reasons, warnings = brand_check(draft, cfg, brand_cfg, hashtags)
            est = _estimated_seconds(draft.video_script, wps)
            if est is not None and est > cfg.get("max_video_seconds", 60):
                reasons.append(f"estimated video length {est}s exceeds limit")
            if reasons:
                rejected += 1
                rejections.append({"asset_id": asset_id, "reasons": reasons})
                logger.log("WARN", "draft_rejected", asset_id=asset_id, reasons=reasons)
                continue

            text = f"{_normalize(draft.hook)} {_normalize(draft.caption)}"
            fp = _fingerprint(platform_key, draft.hook, draft.caption)
            prior = ledger.get(asset_id)
            if prior and prior["fingerprint"] == fp:
                duplicates += 1
                duplicate_log.append({"asset_id": asset_id, "reason": "exact repeat of exported asset"})
                logger.log("INFO", "duplicate_removed", asset_id=asset_id, reason="exact repeat")
                continue
            peers = [(i, t) for i, t in accepted_texts.get(platform_key, []) if i != asset_id]
            match = next(((i, r) for i, t in peers
                          if (r := SequenceMatcher(None, text, t).ratio()) >= threshold), None)
            if match:
                duplicates += 1
                duplicate_log.append({"asset_id": asset_id, "reason": f"{match[1]:.2f} similar to {match[0]}"})
                logger.log("INFO", "duplicate_removed", asset_id=asset_id,
                           similar_to=match[0], similarity=round(match[1], 3))
                continue
            if prior:
                updated += 1
            accepted_texts[platform_key] = [(i, t) for i, t in accepted_texts.get(platform_key, []) if i != asset_id]
            accepted_texts[platform_key].append((asset_id, text))
            ledger[asset_id] = {"fingerprint": fp, "text": text, "platform": platform_key, "run_id": run_id, "source_id": source_id, "slot": index}

            slot = ""
            if first_day:
                slot = (first_day + timedelta(days=index - 1)).isoformat()
            notes = ["DRAFT ONLY - NOT APPROVED FOR PUBLICATION", "Human review required.",
                     "Engine drafts copy only; no final media file exists for this row."]
            if provider_name == "mock":
                notes.append("MOCK PROVIDER OUTPUT - TEST ONLY, NOT REAL AI COPY.")
            if not draft.hashtags:
                notes.append("Hashtags are platform defaults from config, not model-chosen.")
            notes += [f"Review flag: {w}" for w in warnings]
            if est is not None:
                notes.append(f"Estimated spoken length {est}s from script (estimate, not measured).")
            rows.append({
                "asset_id": asset_id, "platform": cfg["workbook_platform"],
                "format": cfg["workbook_format"], "content_pillar": draft.angle,
                "hook": draft.hook, "caption": f"{draft.caption}\n\n{' '.join(hashtags)}",
                "cta": draft.call_to_action,
                "utm_link": _build_utm(utm_base, platform_key, campaign, asset_id),
                "final_file_url": "", "source_file_url": str(run_dir / "drafts.json"),
                "source_input": f"{input_path} (sha256 {intake.sha256[:12]})",
                "tools_used": f"{result.provider_name or provider_name}"
                              f"/{result.model_name or 'unknown model'}; engine pipeline",
                "rights_checked": "No", "ai_label_needed": "Yes", "scheduled_date": slot,
                "test_published_url": "", "impressions_or_views": "", "engagement_rate": "",
                "clicks": "", "status": "Draft", "notes": " | ".join(notes),
                "duplicate_check": "", "completeness_check": "",
            })
        # Persist after every batch so an interrupted run never loses dedupe state.
        _save_ledger(ledger_file, ledger)

    run_dir.mkdir(parents=True, exist_ok=True)
    try:
        export = export_calendar_csv(
            rows, schema_path=config.get("schema_path", "config/workbook-schema.json"),
            output_path=run_dir / "calendar.csv")
        cumulative_path = out_root / "calendar-all.csv"
        total, merged = _merge_cumulative(cumulative_path, rows, columns)
        export_calendar_csv(merged, schema_path=config.get("schema_path", "config/workbook-schema.json"),
                            output_path=cumulative_path)
    except ValueError as exc:
        record["error_codes"].append("EXPORT_ERROR")
        record["message"] = str(exc)
        logger.log("ERROR", "export_error", code="EXPORT_ERROR", message=str(exc))
        return finish("failed")

    (run_dir / "drafts.json").write_text(
        json.dumps({"run_id": run_id, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    record.update(
        items_produced=produced, items_rejected=rejected, duplicates_removed=duplicates,
        items_updated=updated, items_exported=len(rows), failed_batches=failed_batches,
        rejections=rejections, duplicate_details=duplicate_log,
        run_calendar=export["output_path"], cumulative_calendar=str(cumulative_path.resolve()),
        cumulative_rows=total,
        meets_10_asset_minimum=len(rows) >= 10,
        input_tokens=None, output_tokens=None,
    )
    if provider_name == "mock":
        record.update(
            provider_kind="MOCK - offline test provider, not an AI model",
            measurement_scope="Runtime and cost are NOT real-model measurements; "
                              "they must not be cited for the 30-minute or cost requirements.",
            actual_cost_usd=0.0, cost_basis="mock provider; no external calls made")
    else:
        record.update(
            provider_kind="REAL provider (external model call)",
            measurement_scope="Runtime is wall-clock for this run including network calls.",
            actual_cost_usd=None,
                      cost_basis="UNKNOWN - engine does not read billing data; check provider dashboard")
    status = "succeeded" if failed_batches == 0 else "partial"
    if not rows and produced == 0:
        status = "failed"
    return finish(status)

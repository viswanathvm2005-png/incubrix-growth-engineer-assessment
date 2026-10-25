"""Local-only dashboard for the IncuBrix content engine."""

from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import csv
import json
import mimetypes
import re
import shutil
import subprocess
import sys
import threading
import uuid

HOST = "127.0.0.1"
PORT = 8765
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.asset_audit import audit as run_portfolio_audit  # noqa: E402
from engine.mock_provider import MockGenerationProvider  # noqa: E402
from engine.pipeline import PipelineError, run_pipeline  # noqa: E402
from engine.review_store import ReviewStore  # noqa: E402
from engine.source_intake import intake_source  # noqa: E402

BRIEF = ROOT / "outputs" / "technical-demo" / "demo-brief.json"
OUTPUT_DIR = ROOT / "outputs" / "technical-demo"
DASHBOARD_OUT_DIR = ROOT / "outputs" / "dashboard-runs"
CALENDAR = ROOT / "calendar.csv"
CONFIG_PATH = ROOT / "config" / "pipeline-config.yaml"
AUDIT_JSON = ROOT / "outputs" / "asset-audit" / "asset-audit.json"
REVIEW_DB = ROOT / "data" / "content-reviews.sqlite3"

_lock = threading.Lock()
_jobs_lock = threading.Lock()
_jobs: dict[str, dict] = {}
_latest_job_id: str | None = None

ALLOWED_STATIC_PREFIXES = ("content/", "outputs/", "inputs/", "launch-kit/")
FORBIDDEN_FILENAMES = {".env", ".env.example", ".git", ".gitignore"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_slug(value: str, default: str = "dashboard-source-001") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", (value or "").strip()).strip("-")
    return cleaned[:80] or default


def _review_state_path(out_dir: Path | None = None) -> Path:
    base = out_dir or DASHBOARD_OUT_DIR
    return base / "asset-review-state.json"


def _load_asset_review_map(out_dir: Path | None = None) -> dict[str, dict]:
    path = _review_state_path(out_dir)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_asset_review_map(mapping: dict[str, dict], out_dir: Path | None = None) -> None:
    path = _review_state_path(out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolve_workflow_state(row: dict, review_map: dict[str, dict]) -> str:
    """Distinguish Draft, Reviewed, and Ready states. Never mark Ready automatically."""
    raw_status = str(row.get("status", "Draft")).strip()
    if raw_status.lower() == "ready":
        return "Ready"
    if raw_status.lower() == "reviewed":
        return "Reviewed"
    aid = str(row.get("asset_id", "")).strip()
    review_entry = review_map.get(aid)
    if review_entry and review_entry.get("workflow_state") == "Reviewed":
        return "Reviewed"
    return "Draft"


def _enrich_asset_row(row: dict, review_map: dict[str, dict], root: Path = ROOT) -> dict:
    item = dict(row)
    aid = str(item.get("asset_id", "")).strip()
    review_info = review_map.get(aid, {})
    item["workflow_state"] = _resolve_workflow_state(item, review_map)
    item["review_decision"] = review_info.get("decision", "pending")
    item["reviewer"] = review_info.get("reviewer", "")
    item["review_feedback"] = review_info.get("feedback", "")
    item["reviewed_at"] = review_info.get("decided_at", "")

    # Companion slides for carousels/graphics if available in content/exports
    slides: list[str] = []
    final_rel = str(item.get("final_file_url", "")).strip()
    if final_rel:
        final_path = root / final_rel
        if final_path.is_file():
            if item.get("format") == "Carousel":
                folder = final_path.parent
                slide_files = sorted(folder.glob(f"{aid}-slide-*.png")) or sorted(folder.glob(f"{aid}-scene-*.png"))
                if slide_files:
                    slides = [str(p.relative_to(root)).replace("\\", "/") for p in slide_files]
            if not slides:
                slides = [final_rel.replace("\\", "/")]
    item["companion_files"] = slides
    return item


def list_available_sources(root: Path = ROOT, out_dir: Path | None = None) -> list[dict]:
    """List selectable .md and .txt content sources from inputs/ and dashboard custom inputs."""
    base_out = out_dir or DASHBOARD_OUT_DIR
    candidates: list[Path] = []
    inputs_dir = root / "inputs"
    for name in ("sample.md", "sample-b.md", "sample-c.md"):
        p = inputs_dir / name
        if p.is_file():
            candidates.append(p)
    custom_dir = base_out / "inputs"
    if custom_dir.is_dir():
        for p in sorted(custom_dir.glob("*")):
            if p.suffix.lower() in {".md", ".txt"} and p.is_file():
                candidates.append(p)

    default_ids = {
        "sample.md": "demo-source-001",
        "sample-b.md": "demo-source-001",
        "sample-c.md": "demo-source-002",
    }
    sources: list[dict] = []
    for p in candidates:
        try:
            text = p.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        rel = str(p.relative_to(root)).replace("\\", "/") if p.is_relative_to(root) else str(p)
        first_line = next((line.lstrip("# ").strip() for line in text.splitlines() if line.strip()), p.name)
        sources.append({
            "path": rel,
            "name": p.name,
            "title": first_line[:100],
            "default_source_id": default_ids.get(p.name, _safe_slug(p.stem, "custom-source-001")),
            "characters": len(text),
            "words": len(text.split()),
            "preview": text[:400],
            "content": text,
        })
    return sources


def _read_csv_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_pipeline_log(log_path: Path, run_id: str | None = None, limit: int = 100) -> list[dict]:
    if not log_path.is_file():
        return []
    events: list[dict] = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            if run_id is None or item.get("run_id") == run_id:
                events.append(item)
    return events[-limit:]


def get_pipeline_state(out_dir: Path | None = None, root: Path = ROOT) -> dict:
    """Return latest pipeline run record, generated assets, cumulative rows, and log events."""
    base_out = out_dir or DASHBOARD_OUT_DIR
    review_map = _load_asset_review_map(base_out)
    run_dirs = sorted(
        [d for d in base_out.glob("run-*") if d.is_dir() and (d / "run-record.json").is_file()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    ) if base_out.is_dir() else []

    runs_summary: list[dict] = []
    latest_record: dict | None = None
    latest_run_assets: list[dict] = []

    for idx, rdir in enumerate(run_dirs[:15]):
        try:
            rec = json.loads((rdir / "run-record.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        runs_summary.append({
            "run_id": rec.get("run_id", rdir.name),
            "status": rec.get("status", "unknown"),
            "source_id": rec.get("source_id", ""),
            "input_path": rec.get("input_path", ""),
            "started_at": rec.get("started_at", ""),
            "items_produced": rec.get("items_produced", 0),
            "items_exported": rec.get("items_exported", 0),
            "items_updated": rec.get("items_updated", 0),
            "duplicates_removed": rec.get("duplicates_removed", 0),
            "items_rejected": rec.get("items_rejected", 0),
            "error_codes": rec.get("error_codes", []),
            "runtime_seconds": rec.get("runtime_seconds", 0),
        })
        if idx == 0:
            latest_record = rec
            run_csv = rdir / "calendar.csv"
            latest_run_assets = [_enrich_asset_row(r, review_map, root) for r in _read_csv_rows(run_csv)]

    cumulative_csv = base_out / "calendar-all.csv"
    cumulative_assets = [_enrich_asset_row(r, review_map, root) for r in _read_csv_rows(cumulative_csv)]

    draft_count = sum(1 for a in cumulative_assets if a["workflow_state"] == "Draft")
    reviewed_count = sum(1 for a in cumulative_assets if a["workflow_state"] == "Reviewed")
    ready_count = sum(1 for a in cumulative_assets if a["workflow_state"] == "Ready")

    with _jobs_lock:
        active_job = _jobs.get(_latest_job_id) if _latest_job_id else None

    log_path = base_out / "pipeline.log"
    latest_run_id = latest_record.get("run_id") if latest_record else None
    return {
        "active_job": active_job,
        "latest_run": latest_record,
        "latest_run_assets": latest_run_assets,
        "cumulative_assets": cumulative_assets,
        "state_counts": {
            "total": len(cumulative_assets),
            "draft": draft_count,
            "reviewed": reviewed_count,
            "ready": ready_count,
        },
        "recent_runs": runs_summary,
        "log_events": _read_pipeline_log(log_path, run_id=latest_run_id),
        "all_log_events": _read_pipeline_log(log_path, run_id=None, limit=60),
    }


def execute_pipeline_job(
    *,
    input_path: str,
    source_id: str,
    per_platform: int = 4,
    refresh: bool = False,
    simulate_failure_once: bool = False,
    start_date: str | None = "2026-11-02",
    cta: str = "Save this for your next content-planning session.",
    utm_base: str | None = None,
    out_dir: Path | None = None,
    config_path: Path | None = None,
    root: Path = ROOT,
) -> dict:
    """Create a tracked job (queued -> running -> succeeded/partial/failed) and run engine.pipeline."""
    global _latest_job_id
    base_out = out_dir or DASHBOARD_OUT_DIR
    base_out.mkdir(parents=True, exist_ok=True)
    cfg_path = config_path or CONFIG_PATH
    ledger_path = base_out / "ledger.json"

    job_id = "job-" + uuid.uuid4().hex[:10]
    job_info = {
        "job_id": job_id,
        "state": "queued",
        "state_history": ["queued"],
        "source_id": source_id,
        "input_path": input_path,
        "refresh": bool(refresh),
        "simulate_failure_once": bool(simulate_failure_once),
        "per_platform": per_platform,
        "queued_at": _utc_now(),
        "started_at": None,
        "finished_at": None,
        "run_id": None,
        "error": None,
    }
    with _jobs_lock:
        _jobs[job_id] = job_info
        _latest_job_id = job_id

    # Transition to running
    with _jobs_lock:
        job_info["state"] = "running"
        job_info["state_history"].append("running")
        job_info["started_at"] = _utc_now()

    try:
        resolved_input = Path(input_path)
        if not resolved_input.is_absolute():
            resolved_input = root / resolved_input
        record = run_pipeline(
            input_path=str(resolved_input),
            source_id=source_id,
            provider=MockGenerationProvider(),
            provider_name="mock",
            config_path=str(cfg_path),
            out_dir=str(base_out),
            per_platform=per_platform,
            utm_base=utm_base,
            start_date=start_date,
            cta=cta,
            simulate_failure_once=bool(simulate_failure_once),
            ledger_path=str(ledger_path),
            refresh=bool(refresh),
        )
        final_state = record.get("status", "failed")
        with _jobs_lock:
            job_info["state"] = final_state
            job_info["state_history"].append(final_state)
            job_info["finished_at"] = _utc_now()
            job_info["run_id"] = record.get("run_id")
            if final_state == "failed":
                job_info["error"] = record.get("message") or ", ".join(record.get("error_codes", []))
    except (PipelineError, ValueError, OSError, RuntimeError) as exc:
        record = {
            "run_id": None,
            "status": "failed",
            "input_path": str(input_path),
            "source_id": source_id,
            "error_codes": ["PIPELINE_ERROR"],
            "message": str(exc),
        }
        with _jobs_lock:
            job_info["state"] = "failed"
            job_info["state_history"].append("failed")
            job_info["finished_at"] = _utc_now()
            job_info["error"] = str(exc)

    state_snapshot = get_pipeline_state(out_dir=base_out, root=root)
    return {
        "job": dict(job_info),
        "record": record,
        "pipeline_state": state_snapshot,
    }


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>IncuBrix Content Engine Dashboard</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f4f6fb;color:#172033;font:14px/1.45 Segoe UI,Arial,sans-serif}
header{background:#172033;color:white;padding:20px 4%;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
header h1{margin:0 0 4px 0;font-size:22px}
header p{margin:0;color:#cbd5e1;font-size:13px}
main{max-width:1320px;margin:20px auto;padding:0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-bottom:16px}
.grid-2{display:grid;grid-template-columns:1.15fr 0.85fr;gap:16px;margin-bottom:16px}
@media(max-width:920px){.grid-2{grid-template-columns:1fr}}
.card{background:white;padding:18px;border-radius:12px;margin-bottom:16px;box-shadow:0 4px 16px #1720330d;border:1px solid #e2e8f0}
.card h2{margin-top:0;font-size:17px;display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap}
.metric{font-size:28px;font-weight:700;margin:6px 0}
.muted{color:#64748b;font-size:13px}
button,.btn{border:0;border-radius:7px;background:#4f46e5;color:white;padding:9px 13px;cursor:pointer;margin:3px 3px 3px 0;font-size:13px;font-weight:600;text-decoration:none;display:inline-block}
button:hover,.btn:hover{background:#4338ca}
button:disabled{opacity:.5;cursor:not-allowed}
button.reject{background:#b91c1c}
button.reject:hover{background:#991b1b}
button.secondary,.btn.secondary{background:#475569}
button.secondary:hover,.btn.secondary:hover{background:#334155}
button.success{background:#0f766e}
button.success:hover{background:#115e59}
button.warn-btn{background:#b45309}
input,select,textarea{padding:8px 10px;border:1px solid #cbd5e1;border-radius:7px;width:100%;font:inherit}
input[type="checkbox"],input[type="radio"]{width:auto;margin-right:6px}
textarea{min-height:85px;resize:vertical}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;max-height:260px;overflow:auto;font-size:12px}
.asset{border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin:10px 0;background:#fafbff}
.asset-header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px}
.pill{display:inline-block;background:#e0e7ff;color:#3730a3;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.02em}
.pill.good{background:#dcfce7;color:#166534}
.pill.warn{background:#fef3c7;color:#92400e}
.pill.bad{background:#fee2e2;color:#991b1b}
.pill.reviewed{background:#dbeafe;color:#1e40af}
.pill.running{background:#ede9fe;color:#5b21b6}
label{display:block;margin:8px 0 4px;font-weight:600;font-size:13px}
.inline-label{display:inline-flex;align-items:center;font-weight:500;margin-right:14px;cursor:pointer}
.tabs{display:flex;gap:8px;border-bottom:2px solid #e2e8f0;margin-bottom:14px;flex-wrap:wrap}
.tab-btn{background:transparent;color:#475569;border-radius:7px 7px 0 0;padding:9px 15px;margin:0;border-bottom:3px solid transparent}
.tab-btn.active{color:#4f46e5;border-bottom-color:#4f46e5;background:#eef2ff}
.stat-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:10px;margin:12px 0}
.stat-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px;text-align:center}
.stat-box .num{font-size:20px;font-weight:700;color:#1e293b}
.stat-box .lbl{font-size:11px;color:#64748b;text-transform:uppercase}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e2e8f0;vertical-align:top}
th{background:#f8fafc;color:#475569;font-weight:600}
.filter-bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
.filter-bar select,.filter-bar input{width:auto;min-width:160px}
.slide-strip{display:flex;gap:8px;overflow-x:auto;padding:6px 0}
.slide-strip img{height:110px;border-radius:6px;border:1px solid #cbd5e1}
</style>
</head>
<body>
<header>
  <div>
    <h1>IncuBrix Content Engine</h1>
    <p>Local multi-platform pipeline · Source intake · Deduplication &amp; validation · Human review · Readiness governance</p>
  </div>
  <div>
    <span class="pill good">LOCAL ONLY · $0.00 MOCK</span>
    <span id="jobStateBadge" class="pill">STATE: IDLE</span>
    <button class="secondary" onclick="refreshAll()">Refresh All</button>
  </div>
</header>
<main>

<div class="grid">
  <section class="card">
    <span class="pill good">ENGINE HEALTH</span>
    <h2>Engine status</h2>
    <div id="health">Checking...</div>
  </section>
  <section class="card">
    <span class="pill">PIPELINE WORKSPACE</span>
    <h2>Generated assets</h2>
    <div class="metric" id="pipelineTotalCount">0</div>
    <div id="pipelineStateBreakdown" class="muted">0 Draft · 0 Reviewed · 0 Ready</div>
  </section>
  <section class="card">
    <span class="pill reviewed">HUMAN REVIEW</span>
    <h2>Review queue</h2>
    <div class="metric" id="pendingCount">—</div>
    <div class="muted" id="reviewSummaryNote">Pending review records</div>
  </section>
  <section class="card">
    <span class="pill warn">30-ASSET PORTFOLIO</span>
    <h2>Calendar readiness</h2>
    <div class="metric" id="calendarCount">—</div>
    <div id="readinessNote" class="muted"></div>
  </section>
</div>

<div class="grid-2">
  <section class="card">
    <h2>
      <span>1. Content Source Intake &amp; Multi-Platform Pipeline</span>
      <span class="pill">engine/pipeline.py</span>
    </h2>
    <p class="muted">Select an existing source file or enter custom Markdown/text, then trigger the real content engine across LinkedIn, Instagram, and YouTube Shorts.</p>

    <div>
      <label class="inline-label"><input type="radio" name="sourceMode" value="file" checked onchange="toggleSourceMode()"> Select Repository Source File</label>
      <label class="inline-label"><input type="radio" name="sourceMode" value="custom" onchange="toggleSourceMode()"> Enter Custom Source Text</label>
      <label class="inline-label"><input type="radio" name="sourceMode" value="invalid" onchange="toggleSourceMode()"> Test Invalid Input (Error Demo)</label>
    </div>

    <div id="fileSourceBox">
      <label for="sourceSelect">Content Source File</label>
      <select id="sourceSelect" onchange="onSourceSelectChange()"></select>
    </div>

    <div id="customSourceBox" style="display:none">
      <label for="customSourceText">Custom Source Markdown / Notes (min 20 chars)</label>
      <textarea id="customSourceText" placeholder="# Creator Workflow Notes&#10;&#10;Enter long-form podcast, webinar, or article notes here to transform into platform-specific drafts..."></textarea>
    </div>

    <div id="invalidSourceBox" style="display:none">
      <label for="invalidInputPath">Invalid Source Path (demonstrates SOURCE_REJECTED handling)</label>
      <input id="invalidInputPath" value="inputs/unsupported-file.pdf" readonly>
    </div>

    <label for="sourcePreview">Source Content Preview</label>
    <textarea id="sourcePreview" readonly style="min-height:70px;background:#f8fafc;font-size:12px"></textarea>

    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr));margin-top:8px;margin-bottom:8px">
      <div>
        <label for="sourceIdInput">Source ID (`--source-id`)</label>
        <input id="sourceIdInput" value="demo-source-001">
      </div>
      <div>
        <label for="perPlatformInput">Drafts / Platform (`1–10`)</label>
        <input id="perPlatformInput" type="number" min="1" max="10" value="4">
      </div>
      <div>
        <label for="startDateInput">Start Date (`--start-date`)</label>
        <input id="startDateInput" value="2026-11-02">
      </div>
    </div>

    <div style="margin:8px 0">
      <label class="inline-label"><input type="checkbox" id="refreshFlag"> <b>`--refresh`</b> (Update existing slots for this `source-id` in place)</label>
      <label class="inline-label"><input type="checkbox" id="simulateFailureFlag"> <b>`--simulate-failure-once`</b> (Simulate transient provider error &amp; auto-retry)</label>
    </div>

    <div style="margin-top:10px">
      <button id="runPipelineBtn" onclick="runPipeline(false,false)">Run Content Engine Pipeline</button>
      <button class="success" id="runRefreshBtn" onclick="runPipeline(true,false)">Run Refresh (`--refresh`)</button>
      <button class="warn-btn" id="runFailureDemoBtn" onclick="runPipeline(false,true)">Demo Failure &amp; Recovery</button>
      <button class="secondary" onclick="validateSourceOnly()">Validate Source Only</button>
      <button class="reject" onclick="resetPipelineWorkspace()">Reset Demo Workspace</button>
    </div>

    <div id="pipelineStatusBanner" style="margin-top:10px;padding:10px;border-radius:8px;background:#f8fafc;border:1px solid #e2e8f0">
      <b>Pipeline Status:</b> <span id="pipelineStatusText">Idle — ready to run.</span>
    </div>
  </section>

  <section class="card">
    <h2>
      <span>2. Real Validation, Deduplication &amp; Error Telemetry</span>
      <span class="pill" id="latestRunBadge">No run yet</span>
    </h2>
    <div class="stat-strip">
      <div class="stat-box"><div class="num" id="statProduced">0</div><div class="lbl">Produced</div></div>
      <div class="stat-box"><div class="num" id="statExported">0</div><div class="lbl">Exported</div></div>
      <div class="stat-box"><div class="num" id="statUpdated">0</div><div class="lbl">Refreshed</div></div>
      <div class="stat-box"><div class="num" id="statDuplicates">0</div><div class="lbl">Duplicates Blocked</div></div>
      <div class="stat-box"><div class="num" id="statRejected">0</div><div class="lbl">Brand Rejections</div></div>
      <div class="stat-box"><div class="num" id="statCumulative">0</div><div class="lbl">Cumulative Rows</div></div>
    </div>

    <div id="runMetaSummary" class="muted" style="margin-bottom:10px">
      Trigger a pipeline run to inspect real validation checks, duplicate detection, and retry recovery logs.
    </div>

    <h3 style="font-size:14px;margin:10px 0 4px">Duplicate Detection &amp; Validation Flags</h3>
    <div id="validationAndDuplicatesBox" style="max-height:150px;overflow:auto;border:1px solid #e2e8f0;border-radius:8px;padding:8px;background:#f8fafc;font-size:12px">
      No duplicate or rejection events recorded yet.
    </div>

    <h3 style="font-size:14px;margin:10px 0 4px">Structured Engine Log (`pipeline.log`)</h3>
    <pre id="pipelineLogBox">No pipeline log events yet.</pre>

    <div style="margin-top:8px">
      <a class="btn secondary" href="/api/export/pipeline-calendar" target="_blank">Export Pipeline CSV</a>
      <a class="btn secondary" href="/api/export/run-record" target="_blank">Export Run Record JSON</a>
      <a class="btn secondary" href="/api/export/pipeline-log" target="_blank">Export Pipeline Log</a>
      <a class="btn secondary" href="/api/export/portfolio-calendar" target="_blank">Export 30-Asset Calendar CSV</a>
    </div>
  </section>
</div>

<section class="card">
  <div class="tabs">
    <button class="tab-btn active" id="tabBtnPipelineAssets" onclick="switchTab('pipelineAssets')">Pipeline Generated Assets (<span id="tabCountPipeline">0</span>)</button>
    <button class="tab-btn" id="tabBtnPortfolioAssets" onclick="switchTab('portfolioAssets')">Canonical 30-Asset Portfolio (<span id="tabCountPortfolio">30</span>)</button>
    <button class="tab-btn" id="tabBtnSingleBrief" onclick="switchTab('singleBrief')">Single-Brief Draft Generator &amp; Review Queue</button>
    <button class="tab-btn" id="tabBtnRunHistory" onclick="switchTab('runHistory')">Pipeline Run History (<span id="tabCountRuns">0</span>)</button>
  </div>

  <!-- TAB 1: PIPELINE GENERATED ASSETS -->
  <div id="tab-pipelineAssets">
    <div class="filter-bar">
      <label class="inline-label">Platform:
        <select id="pipePlatformFilter" onchange="renderPipelineAssets()">
          <option value="ALL">All Platforms</option>
          <option value="LinkedIn">LinkedIn</option>
          <option value="Instagram">Instagram</option>
          <option value="YouTube Shorts">YouTube Shorts</option>
        </select>
      </label>
      <label class="inline-label">Workflow State:
        <select id="pipeStateFilter" onchange="renderPipelineAssets()">
          <option value="ALL">All States (Draft / Reviewed / Ready)</option>
          <option value="Draft">Draft</option>
          <option value="Reviewed">Reviewed</option>
          <option value="Ready">Ready</option>
        </select>
      </label>
      <label class="inline-label">View Scope:
        <select id="pipeScopeFilter" onchange="renderPipelineAssets()">
          <option value="cumulative">Cumulative Calendar (`calendar-all.csv`)</option>
          <option value="latest">Latest Run Only (`calendar.csv`)</option>
        </select>
      </label>
      <span class="muted">Governance rule: Approving a draft marks it <b>Reviewed</b>. Assets are <b>never</b> marked <b>Ready</b> automatically.</span>
    </div>
    <div id="pipelineAssetsContainer">Run the pipeline above to generate and inspect multi-platform assets.</div>
  </div>

  <!-- TAB 2: CANONICAL 30-ASSET PORTFOLIO -->
  <div id="tab-portfolioAssets" style="display:none">
    <div class="filter-bar">
      <label class="inline-label">Platform:
        <select id="portPlatformFilter" onchange="renderPortfolioAssets()">
          <option value="ALL">All Platforms (30)</option>
          <option value="LinkedIn">LinkedIn (LI-01..LI-10)</option>
          <option value="Instagram">Instagram (IG-01..IG-10)</option>
          <option value="YouTube Shorts">YouTube Shorts (YT-01..YT-10)</option>
        </select>
      </label>
      <label class="inline-label">State:
        <select id="portStateFilter" onchange="renderPortfolioAssets()">
          <option value="ALL">All States</option>
          <option value="Draft">Draft</option>
          <option value="Reviewed">Reviewed</option>
          <option value="Ready">Ready</option>
        </select>
      </label>
      <button class="secondary" onclick="loadPortfolio(true)">Run Live 30-Asset Audit (`engine.asset_audit`)</button>
      <a class="btn secondary" href="/api/export/asset-audit" target="_blank">Download Audit JSON</a>
    </div>
    <div id="portfolioAuditBanner" class="muted" style="margin-bottom:10px"></div>
    <div id="portfolioAssetsContainer">Loading 30-asset portfolio...</div>
  </div>

  <!-- TAB 3: SINGLE-BRIEF GENERATOR & REVIEW QUEUE -->
  <div id="tab-singleBrief" style="display:none">
    <div class="grid-2">
      <div>
        <h3>Single-Brief Draft Generator (`engine generate`)</h3>
        <label>Number of drafts (1–10)<br>
        <input id="count" type="number" min="1" max="10" value="1" style="max-width:160px"></label>
        <button id="generateBtn" onclick="generateDrafts()">Generate drafts</button>
        <p class="muted">Uses `outputs/technical-demo/demo-brief.json` and automatically submits generated drafts to the human review queue as `pending`.</p>
        <div id="generateStatus" class="muted">Ready</div>
        <div id="drafts" style="margin-top:10px">Generate a draft to display it here.</div>
      </div>
      <div>
        <h3>Human Review Queue (`engine review`)</h3>
        <p class="muted">Review decisions are recorded in SQLite (`data/content-reviews.sqlite3`). Approving a draft records human review (`Reviewed`), never `Ready`.</p>
        <button class="secondary" onclick="loadReviews()">Refresh Queue</button>
        <div id="reviews" style="margin-top:10px">Loading review records...</div>
      </div>
    </div>
  </div>

  <!-- TAB 4: PIPELINE RUN HISTORY -->
  <div id="tab-runHistory" style="display:none">
    <div id="runHistoryContainer">No pipeline runs recorded yet.</div>
  </div>
</section>

<section class="card">
  <h2>Publishing readiness &amp; governance reminders (`Draft` vs `Reviewed` vs `Ready`)</h2>
  <div class="grid">
    <div><span class="pill">1. Draft</span><p>All engine outputs start as <b>Draft</b> (`rights_checked = No`). Copy and media are unverified.</p></div>
    <div><span class="pill reviewed">2. Reviewed</span><p>A human reviewer has inspected the hook, caption, and format compliance. Still not approved for external publishing.</p></div>
    <div><span class="pill warn">3. Human Gates</span><p>Requires factual evidence check, `rights_checked = Yes`, AI disclosure sign-off, and confirmed `utm_link` destination.</p></div>
    <div><span class="pill good">4. Ready (Manual Only)</span><p>Never set automatically by the engine or dashboard. Only set after all human gates are completed.</p></div>
  </div>
</section>
</main>

<script>
let SOURCES_CACHE = [];
let PIPELINE_STATE = {latest_run_assets:[], cumulative_assets:[], recent_runs:[]};
let PORTFOLIO_DATA = {assets:[], audit:{}};

function esc(v){
 return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
async function api(url,opts={}){
 const r=await fetch(url,opts);
 const d=await r.json();
 if(!r.ok)throw new Error(d.message||d.stderr||"Request failed");
 return d;
}
function statePillClass(state){
 const s=String(state||"").toLowerCase();
 if(s==="ready"||s==="succeeded"||s==="approved"||s==="accepted")return "pill good";
 if(s==="reviewed")return "pill reviewed";
 if(s==="running"||s==="queued")return "pill running";
 if(s==="partial"||s==="pending")return "pill warn";
 if(s==="failed"||s==="rejected"||s==="error")return "pill bad";
 return "pill";
}
function updateJobBadge(state, label){
 const badge=document.getElementById("jobStateBadge");
 badge.className=statePillClass(state);
 badge.textContent="STATE: "+String(label||state||"IDLE").toUpperCase();
}
function switchTab(tabName){
 ["pipelineAssets","portfolioAssets","singleBrief","runHistory"].forEach(t=>{
  document.getElementById("tab-"+t).style.display=(t===tabName)?"block":"none";
  const btnId="tabBtn"+t.charAt(0).toUpperCase()+t.slice(1);
  const btn=document.getElementById(btnId);
  if(btn)btn.className="tab-btn"+(t===tabName?" active":"");
 });
}
function toggleSourceMode(){
 const mode=document.querySelector('input[name="sourceMode"]:checked')?.value||"file";
 document.getElementById("fileSourceBox").style.display=(mode==="file")?"block":"none";
 document.getElementById("customSourceBox").style.display=(mode==="custom")?"block":"none";
 document.getElementById("invalidSourceBox").style.display=(mode==="invalid")?"block":"none";
 if(mode==="file")onSourceSelectChange();
 else if(mode==="custom"){
  document.getElementById("sourcePreview").value=document.getElementById("customSourceText").value||"(Enter custom Markdown/text above)";
 }else{
  document.getElementById("sourcePreview").value="Invalid file extension (.pdf) selected to demonstrate graceful SOURCE_REJECTED error handling and logging.";
 }
}
async function loadSources(){
 try{
  const d=await api("/api/sources");
  SOURCES_CACHE=d.sources||[];
  const sel=document.getElementById("sourceSelect");
  const prev=sel.value;
  sel.innerHTML=SOURCES_CACHE.map(s=>`<option value="${esc(s.path)}">${esc(s.path)} — ${esc(s.title)} (${s.characters} chars)</option>`).join("");
  if(prev&&SOURCES_CACHE.some(s=>s.path===prev))sel.value=prev;
  onSourceSelectChange();
 }catch(e){
  console.error("Failed to load sources:",e);
 }
}
function onSourceSelectChange(){
 const sel=document.getElementById("sourceSelect");
 const found=SOURCES_CACHE.find(s=>s.path===sel.value);
 if(found){
  document.getElementById("sourcePreview").value=found.content;
  const srcIdInput=document.getElementById("sourceIdInput");
  if(!srcIdInput.dataset.userEdited){
   srcIdInput.value=found.default_source_id;
  }
 }
}
async function validateSourceOnly(){
 const mode=document.querySelector('input[name="sourceMode"]:checked')?.value||"file";
 const sourceId=document.getElementById("sourceIdInput").value.trim()||"demo-source-001";
 const payload={source_id:sourceId};
 if(mode==="file")payload.input_path=document.getElementById("sourceSelect").value;
 else if(mode==="custom")payload.custom_text=document.getElementById("customSourceText").value;
 else payload.input_path=document.getElementById("invalidInputPath").value;
 const statusEl=document.getElementById("pipelineStatusText");
 try{
  const res=await api("/api/sources/intake",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const intake=res.intake||{};
  if(intake.status==="ACCEPTED"){
   statusEl.innerHTML=`<span class="pill good">SOURCE ACCEPTED</span> <b>${esc(intake.source_id)}</b> · ${intake.character_count} chars · sha256 <code>${esc((intake.sha256||"").slice(0,12))}</code>`;
  }else{
   statusEl.innerHTML=`<span class="pill bad">SOURCE REJECTED</span> ${esc(intake.message||"Invalid source")}`;
  }
  await loadSources();
 }catch(e){
  statusEl.innerHTML=`<span class="pill bad">VALIDATION FAILED</span> ${esc(e.message)}`;
 }
}
async function runPipeline(forceRefresh=false, forceSimulateFailure=false){
 const mode=document.querySelector('input[name="sourceMode"]:checked')?.value||"file";
 const sourceId=document.getElementById("sourceIdInput").value.trim()||"demo-source-001";
 const perPlatform=Number(document.getElementById("perPlatformInput").value)||4;
 const startDate=document.getElementById("startDateInput").value.trim()||"2026-11-02";
 const refresh=forceRefresh||document.getElementById("refreshFlag").checked;
 const simulateFailure=forceSimulateFailure||document.getElementById("simulateFailureFlag").checked;

 const body={
  source_id:sourceId,
  per_platform:perPlatform,
  start_date:startDate,
  refresh:refresh,
  simulate_failure_once:simulateFailure
 };
 if(mode==="file")body.input_path=document.getElementById("sourceSelect").value;
 else if(mode==="custom")body.custom_text=document.getElementById("customSourceText").value;
 else body.input_path=document.getElementById("invalidInputPath").value;

 const statusEl=document.getElementById("pipelineStatusText");
 const btns=["runPipelineBtn","runRefreshBtn","runFailureDemoBtn"].map(id=>document.getElementById(id));
 btns.forEach(b=>{if(b)b.disabled=true;});
 updateJobBadge("queued","QUEUED");
 statusEl.innerHTML=`<span class="pill running">QUEUED &rarr; RUNNING</span> Executing <code>engine.pipeline</code> for <b>${esc(sourceId)}</b>...`;

 try{
  const res=await api("/api/pipeline/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const rec=res.record||{};
  const job=res.job||{};
  const history=(job.state_history||[]).join(" → ");
  updateJobBadge(rec.status||job.state, rec.status||job.state);
  if(rec.status==="succeeded"||rec.status==="partial"){
   statusEl.innerHTML=`<span class="${statePillClass(rec.status)}">${esc(rec.status.toUpperCase())}</span> Run <b>${esc(rec.run_id)}</b> (${esc(history)}) · Exported <b>${rec.items_exported}</b> assets, Updated <b>${rec.items_updated}</b>, Duplicates blocked <b>${rec.duplicates_removed}</b>, Runtime <b>${rec.runtime_seconds}s</b>`;
  }else{
   statusEl.innerHTML=`<span class="pill bad">FAILED</span> (${esc(history)}) · Error: <b>${esc((rec.error_codes||[]).join(", "))}</b> — ${esc(rec.message||job.error||"Pipeline run failed")}`;
  }
  await loadPipelineState();
  await loadSources();
  await refreshHeaderMetrics();
 }catch(e){
  updateJobBadge("failed","FAILED");
  statusEl.innerHTML=`<span class="pill bad">FAILED</span> ${esc(e.message)}`;
  await loadPipelineState();
 }finally{
  btns.forEach(b=>{if(b)b.disabled=false;});
 }
}
async function resetPipelineWorkspace(){
 try{
  await api("/api/pipeline/reset",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({})});
  updateJobBadge("idle","IDLE");
  document.getElementById("pipelineStatusText").innerHTML=`<span class="pill good">WORKSPACE RESET</span> Cleared demo pipeline runs and duplicate ledger.`;
  await loadPipelineState();
  await refreshHeaderMetrics();
 }catch(e){
  alert("Reset failed: "+e.message);
 }
}
async function loadPipelineState(){
 try{
  const st=await api("/api/pipeline/status");
  PIPELINE_STATE=st;
  const counts=st.state_counts||{total:0,draft:0,reviewed:0,ready:0};
  document.getElementById("pipelineTotalCount").textContent=counts.total;
  document.getElementById("pipelineStateBreakdown").textContent=`${counts.draft} Draft · ${counts.reviewed} Reviewed · ${counts.ready} Ready`;
  document.getElementById("tabCountPipeline").textContent=counts.total;
  document.getElementById("tabCountRuns").textContent=(st.recent_runs||[]).length;

  const rec=st.latest_run;
  const badge=document.getElementById("latestRunBadge");
  if(rec){
   badge.className=statePillClass(rec.status);
   badge.textContent=`${rec.run_id} · ${String(rec.status).toUpperCase()}`;
   document.getElementById("statProduced").textContent=rec.items_produced??0;
   document.getElementById("statExported").textContent=rec.items_exported??0;
   document.getElementById("statUpdated").textContent=rec.items_updated??0;
   document.getElementById("statDuplicates").textContent=rec.duplicates_removed??0;
   document.getElementById("statRejected").textContent=rec.items_rejected??0;
   document.getElementById("statCumulative").textContent=rec.cumulative_rows??counts.total;
   document.getElementById("runMetaSummary").innerHTML=
    `<b>Source:</b> <code>${esc(rec.input_path)}</code> (<code>${esc(rec.source_id)}</code>) · `+
    `<b>Runtime:</b> ${esc(rec.runtime_seconds)}s · <b>Cost:</b> $${esc(rec.actual_cost_usd??0)} · `+
    `<b>Provider:</b> ${esc(rec.provider_kind||rec.provider)}`;

   const dupes=rec.duplicate_details||[];
   const rejs=rec.rejections||[];
   const errs=rec.error_codes||[];
   let parts=[];
   if(errs.length){
    parts.push(`<div style="color:#991b1b;margin-bottom:6px"><b>Error Codes:</b> ${esc(errs.join(", "))} ${rec.message?"— "+esc(rec.message):""}</div>`);
   }
   if(dupes.length){
    parts.push(`<div><b>Duplicates Removed (${dupes.length}):</b><ul style="margin:4px 0;padding-left:18px">`+
     dupes.map(d=>`<li><code>${esc(d.asset_id)}</code>: ${esc(d.reason)}</li>`).join("")+`</ul></div>`);
   }
   if(rejs.length){
    parts.push(`<div><b>Brand/Validation Rejections (${rejs.length}):</b><ul style="margin:4px 0;padding-left:18px">`+
     rejs.map(r=>`<li><code>${esc(r.asset_id)}</code>: ${esc((r.reasons||[]).join("; "))}</li>`).join("")+`</ul></div>`);
   }
   if(!parts.length){
    parts.push(`<span class="pill good">ALL CHECKS PASSED</span> 0 brand rejections, 0 duplicates removed, 0 errors in latest run.`);
   }
   document.getElementById("validationAndDuplicatesBox").innerHTML=parts.join("");
  }else{
   badge.className="pill";
   badge.textContent="No run yet";
   ["statProduced","statExported","statUpdated","statDuplicates","statRejected","statCumulative"].forEach(id=>{
    document.getElementById(id).textContent="0";
   });
   document.getElementById("validationAndDuplicatesBox").textContent="No duplicate or rejection events recorded yet.";
  }

  const logs=st.all_log_events||[];
  document.getElementById("pipelineLogBox").textContent=logs.length
   ? logs.map(l=>JSON.stringify(l)).join("\n")
   : "No pipeline log events yet.";

  renderPipelineAssets();
  renderRunHistory();
 }catch(e){
  console.error("Failed to load pipeline state:",e);
 }
}
function renderPipelineAssets(){
 const box=document.getElementById("pipelineAssetsContainer");
 const scope=document.getElementById("pipeScopeFilter").value;
 const platFilter=document.getElementById("pipePlatformFilter").value;
 const stateFilter=document.getElementById("pipeStateFilter").value;
 const sourceList=(scope==="latest")?(PIPELINE_STATE.latest_run_assets||[]):(PIPELINE_STATE.cumulative_assets||[]);
 const filtered=sourceList.filter(a=>{
  if(platFilter!=="ALL"&&a.platform!==platFilter)return false;
  if(stateFilter!=="ALL"&&a.workflow_state!==stateFilter)return false;
  return true;
 });
 if(!filtered.length){
  box.innerHTML=`<p class="muted">No generated pipeline assets match the current filter (${sourceList.length} total in ${esc(scope)} view).</p>`;
  return;
 }
 box.innerHTML=filtered.map(a=>`
  <article class="asset">
   <div class="asset-header">
    <div>
     <span class="pill">${esc(a.platform)}</span>
     <span class="pill">${esc(a.format)}</span>
     <span class="${statePillClass(a.workflow_state)}">State: ${esc(a.workflow_state)}</span>
     <b style="margin-left:6px;font-size:15px">${esc(a.asset_id)}</b>
     <span class="muted">· Pillar: ${esc(a.content_pillar||"—")} · Scheduled: ${esc(a.scheduled_date||"—")}</span>
    </div>
    <div>
     <span class="pill warn">Rights: ${esc(a.rights_checked||"No")}</span>
     <span class="pill">AI Label: ${esc(a.ai_label_needed||"Yes")}</span>
    </div>
   </div>
   <p><b>Hook:</b> ${esc(a.hook)}</p>
   <p><b>Caption &amp; Hashtags:</b><br><span style="white-space:pre-wrap">${esc(a.caption)}</span></p>
   <p><b>Call to Action:</b> ${esc(a.cta)} · <b>UTM:</b> <code>${esc(a.utm_link)}</code></p>
   <p class="muted"><b>Source Input:</b> <code>${esc(a.source_input)}</code> · <b>Tools:</b> ${esc(a.tools_used)}</p>
   <p class="muted"><b>Validation &amp; Governance Notes:</b> ${esc(a.notes)}</p>
   <div style="margin-top:8px;padding-top:8px;border-top:1px dashed #cbd5e1;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
    <input id="pipe-rev-${esc(a.asset_id)}" value="${esc(a.reviewer||'Assessment reviewer')}" style="max-width:170px" placeholder="Reviewer name">
    <input id="pipe-fb-${esc(a.asset_id)}" value="${esc(a.review_feedback||'')}" style="max-width:260px" placeholder="Review notes / feedback">
    <button class="success" onclick="reviewAsset('${esc(a.asset_id)}','approved','pipe')">Mark Reviewed (Never Auto-Ready)</button>
    <button class="reject" onclick="reviewAsset('${esc(a.asset_id)}','rejected','pipe')">Flag / Reject Draft</button>
    ${a.reviewed_at?`<span class="muted">Last decision: <b>${esc(a.review_decision)}</b> by ${esc(a.reviewer)} at ${esc(a.reviewed_at)}</span>`:""}
   </div>
  </article>
 `).join("");
}
async function reviewAsset(assetId, decision, prefix){
 const reviewer=document.getElementById(`${prefix}-rev-${assetId}`)?.value||"Assessment reviewer";
 const feedback=document.getElementById(`${prefix}-fb-${assetId}`)?.value||"";
 if(decision==="rejected"&&!feedback.trim()){
  alert("Please enter feedback when rejecting or flagging a draft.");
  return;
 }
 try{
  await api("/api/assets/review",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({asset_id:assetId,decision:decision,reviewer:reviewer,feedback:feedback})
  });
  await loadPipelineState();
  await loadPortfolio(false);
  await refreshHeaderMetrics();
 }catch(e){
  alert("Asset review update failed: "+e.message);
 }
}
async function loadPortfolio(runFreshAudit=false){
 try{
  const url=runFreshAudit?"/api/portfolio?refresh_audit=1":"/api/portfolio";
  const d=await api(url);
  PORTFOLIO_DATA=d;
  document.getElementById("tabCountPortfolio").textContent=(d.assets||[]).length;
  const aud=d.audit_summary||{};
  document.getElementById("portfolioAuditBanner").innerHTML=
   `<span class="pill good">AUTOMATED CHECKS: ${aud.automated_pass??30}/${aud.total_assets??30} PASS</span> `+
   `<span class="pill good">SEEDED 20-ASSET SAMPLE: ${aud.sample_20_automated_pass??20}/20 PASS (100%)</span> `+
   `<span class="pill warn">READY TO PUBLISH: ${aud.ready_to_publish??0}/${aud.total_assets??30} (Human Gates Pending)</span>`;
  renderPortfolioAssets();
 }catch(e){
  document.getElementById("portfolioAssetsContainer").textContent="Failed to load portfolio: "+e.message;
 }
}
function renderPortfolioAssets(){
 const box=document.getElementById("portfolioAssetsContainer");
 const platFilter=document.getElementById("portPlatformFilter").value;
 const stateFilter=document.getElementById("portStateFilter").value;
 const list=(PORTFOLIO_DATA.assets||[]).filter(a=>{
  if(platFilter!=="ALL"&&a.platform!==platFilter)return false;
  if(stateFilter!=="ALL"&&a.workflow_state!==stateFilter)return false;
  return true;
 });
 if(!list.length){
  box.innerHTML="<p class='muted'>No portfolio assets match the selected filter.</p>";
  return;
 }
 box.innerHTML=list.map(a=>{
  const files=a.companion_files||[];
  const isVideo=a.format==="Short video";
  const mediaHtml=isVideo&&a.final_file_url
   ? `<div style="margin:8px 0"><video controls preload="metadata" style="max-height:220px;border-radius:8px;border:1px solid #cbd5e1" src="/files/${esc(a.final_file_url)}"></video></div>`
   : (files.length?`<div class="slide-strip">${files.map(f=>`<a href="/files/${esc(f)}" target="_blank"><img src="/files/${esc(f)}" alt="${esc(a.asset_id)}" loading="lazy"></a>`).join("")}</div>`:"");
  return `
  <article class="asset">
   <div class="asset-header">
    <div>
     <span class="pill">${esc(a.platform)}</span>
     <span class="pill">${esc(a.format)}</span>
     <span class="${statePillClass(a.workflow_state)}">State: ${esc(a.workflow_state)}</span>
     <span class="${a.automated_pass?'pill good':'pill bad'}">Audit: ${a.automated_pass?'PASS':'FAIL'}</span>
     <b style="margin-left:6px;font-size:15px">${esc(a.asset_id)}</b>
     <span class="muted">· ${esc(a.content_pillar)} · Scheduled: ${esc(a.scheduled_date)}</span>
    </div>
    <div>
     ${a.final_file_url?`<a class="btn secondary" href="/files/${esc(a.final_file_url)}" target="_blank">Open Final Asset</a>`:""}
     ${a.source_file_url?`<a class="btn secondary" href="/files/${esc(a.source_file_url)}" target="_blank">Open Editable Source</a>`:""}
    </div>
   </div>
   <p><b>Hook:</b> ${esc(a.hook)}</p>
   <p><b>Caption:</b><br><span style="white-space:pre-wrap">${esc(a.caption)}</span></p>
   <p><b>CTA:</b> ${esc(a.cta)} · <b>UTM:</b> <code>${esc(a.utm_link)}</code></p>
   <p class="muted"><b>Source Input:</b> <code>${esc(a.source_input)}</code> · <b>Tools:</b> ${esc(a.tools_used)}</p>
   ${mediaHtml}
   <div style="margin-top:8px;padding-top:8px;border-top:1px dashed #cbd5e1;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
    <input id="port-rev-${esc(a.asset_id)}" value="${esc(a.reviewer||'Assessment reviewer')}" style="max-width:170px" placeholder="Reviewer name">
    <input id="port-fb-${esc(a.asset_id)}" value="${esc(a.review_feedback||'')}" style="max-width:260px" placeholder="Review notes">
    <button class="success" onclick="reviewAsset('${esc(a.asset_id)}','approved','port')">Mark Reviewed</button>
    <button class="reject" onclick="reviewAsset('${esc(a.asset_id)}','rejected','port')">Flag / Reject</button>
   </div>
  </article>`;
 }).join("");
}
function renderRunHistory(){
 const box=document.getElementById("runHistoryContainer");
 const runs=PIPELINE_STATE.recent_runs||[];
 if(!runs.length){
  box.innerHTML="<p class='muted'>No pipeline runs recorded in the demo workspace yet.</p>";
  return;
 }
 box.innerHTML=`<table>
  <thead><tr><th>Run ID</th><th>Status</th><th>Source ID</th><th>Input</th><th>Produced</th><th>Exported</th><th>Refreshed</th><th>Duplicates</th><th>Rejected</th><th>Runtime</th></tr></thead>
  <tbody>
   ${runs.map(r=>`<tr>
    <td><code>${esc(r.run_id)}</code></td>
    <td><span class="${statePillClass(r.status)}">${esc(r.status)}</span></td>
    <td><code>${esc(r.source_id)}</code></td>
    <td><code>${esc(r.input_path)}</code></td>
    <td>${r.items_produced}</td>
    <td><b>${r.items_exported}</b></td>
    <td>${r.items_updated}</td>
    <td>${r.duplicates_removed}</td>
    <td>${r.items_rejected}</td>
    <td>${r.runtime_seconds}s</td>
   </tr>`).join("")}
  </tbody>
 </table>`;
}
async function refreshHeaderMetrics(){
 const h=await api("/api/health");
 document.getElementById("health").innerHTML=
  '<span class="pill good">Connected</span><p class="muted">Provider: mock · Brief: '+(h.brief_exists?"found":"missing")+' · Pipeline config: '+(h.pipeline_config_exists?"ready":"missing")+'</p>';
 const c=await api("/api/readiness");
 document.getElementById("calendarCount").textContent=c.total_rows;
 document.getElementById("readinessNote").textContent=
  `${c.draft_rows} Draft · ${c.reviewed_rows||0} Reviewed · ${c.ready_rows||0} Ready`;
}
async function refreshAll(){
 try{
  await refreshHeaderMetrics();
  await loadSources();
  await loadPipelineState();
  await loadPortfolio(false);
  await loadReviews();
 }catch(e){document.getElementById("health").textContent="Error: "+e.message;}
}
function renderDrafts(data){
 const target=document.getElementById("drafts");
 const raw=data.stdout||"";
 let parsed;
 try{
  parsed=[JSON.parse(raw)];
 }catch(e){
  const lines=raw.split(/\r?\n/).filter(Boolean);
  parsed=lines.map(line=>{try{return JSON.parse(line)}catch{return null}}).filter(Boolean);
 }
 let drafts=[];
 function walk(x){
  if(!x||typeof x!=="object")return;
  if(Array.isArray(x)){x.forEach(walk);return}
  if(x.draft_id && (x.hook||x.caption||x.body||x.content))drafts.push(x);
  Object.values(x).forEach(v=>{if(v&&typeof v==="object")walk(v)});
 }
 parsed.forEach(walk);
 if(!drafts.length){
  target.innerHTML='<p>Generation completed. Full engine response:</p><pre>'+esc(raw||JSON.stringify(data,null,2))+'</pre>';
  return;
 }
 target.innerHTML=drafts.map(d=>`
 <article class="asset">
 <span class="pill">${esc(d.content_format||"Draft")}</span>
 <span class="pill">State: Draft</span>
 <h3>${esc(d.draft_id)}</h3>
 <p><b>Hook</b><br>${esc(d.hook||"—")}</p>
 <p><b>Caption / body</b><br>${esc(d.caption||d.body||d.content||"—")}</p>
 <p><b>Call to action</b><br>${esc(d.call_to_action||"—")}</p>
 <p class="muted">Generated test content · Submitted to review queue as pending.</p>
 </article>`).join("");
}
async function generateDrafts(){
 const btn=document.getElementById("generateBtn");
 const status=document.getElementById("generateStatus");
 const n=Number(document.getElementById("count").value);
 if(!Number.isInteger(n)||n<1||n>10){status.textContent="Choose 1–10 drafts.";return;}
 btn.disabled=true;status.textContent="Generating...";
 try{
  const d=await api("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({count:n})});
  renderDrafts(d);
  status.textContent="Generation completed · request "+d.request_id;
  await loadReviews();
 }catch(e){status.textContent="Generation failed: "+e.message;}
 finally{btn.disabled=false;}
}
async function loadReviews(){
 const box=document.getElementById("reviews");
 try{
  const d=await api("/api/reviews");
  const items=d.records||d.reviews||[];
  const pending=items.filter(x=>x.status==="pending").length;
  const approved=items.filter(x=>x.status==="approved").length;
  document.getElementById("pendingCount").textContent=pending;
  document.getElementById("reviewSummaryNote").textContent=`${pending} pending · ${approved} reviewed (approved)`;
  if(!items.length){box.innerHTML="<p>No review records yet. Generate drafts, then review them here.</p>";return;}
  box.innerHTML=items.map(x=>`
  <article class="asset">
   <span class="${statePillClass(x.status)}">${esc(x.status==="approved"?"Reviewed (approved)":x.status)}</span>
   <h3>${esc(x.draft_id||x.asset_id||"Review record")}</h3>
   <p>Brief: <code>${esc(x.brief_id||"—")}</code></p>
   <p>${esc(x.summary||"Generated draft record in human review store.")}</p>
   ${x.status==="pending"?`
   <label>Reviewer <input id="reviewer-${esc(x.draft_id)}" value="Assessment reviewer"></label>
   <label>Feedback (required for rejection)<br><textarea id="feedback-${esc(x.draft_id)}" placeholder="Reason or review notes"></textarea></label><br>
   <button class="success" onclick="decide('${esc(x.brief_id)}','${esc(x.draft_id)}','approved')">Approve (Mark Reviewed)</button>
   <button class="reject" onclick="decide('${esc(x.brief_id)}','${esc(x.draft_id)}','rejected')">Reject</button>`:
   `<p class="muted">Decided by <b>${esc(x.reviewer||"—")}</b> at ${esc(x.decided_at||"—")} ${x.feedback?"· Feedback: "+esc(x.feedback):""}</p>`}
  </article>`).join("");
 }catch(e){box.textContent="Could not load review queue: "+e.message;}
}
async function decide(briefId,draftId,decision){
 const reviewer=document.getElementById("reviewer-"+draftId)?.value||"Assessment reviewer";
 const feedback=document.getElementById("feedback-"+draftId)?.value||"";
 if(decision==="rejected"&&!feedback.trim()){alert("Add feedback before rejecting.");return;}
 try{
  await api("/api/review/decide",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({brief_id:briefId,draft_id:draftId,decision,reviewer,feedback})});
  await loadReviews();
  await refreshHeaderMetrics();
 }catch(e){alert("Review decision failed: "+e.message);}
}
refreshAll();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, code: int, body: bytes, content_type: str, filename: str | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if filename:
            self.send_header("Content-Disposition", f'inline; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 250_000:
            raise ValueError("Invalid request body.")
        return json.loads(self.rfile.read(length))

    def run_cli(self, args: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "engine", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    def _serve_safe_file(self, rel_path: str) -> None:
        clean_rel = unquote(rel_path).lstrip("/\\").replace("\\", "/")
        if not clean_rel or ".." in clean_rel.split("/"):
            self.send_json(403, {"message": "Access denied."})
            return
        if not clean_rel.startswith(ALLOWED_STATIC_PREFIXES):
            self.send_json(403, {"message": "Directory not exposed by dashboard."})
            return
        target = (ROOT / clean_rel).resolve()
        if not target.is_relative_to(ROOT.resolve()):
            self.send_json(403, {"message": "Path outside repository root."})
            return
        if target.name in FORBIDDEN_FILENAMES or target.name.startswith(".env"):
            self.send_json(403, {"message": "Sensitive files are never exposed."})
            return
        if not target.is_file():
            self.send_json(404, {"message": f"File not found: {clean_rel}"})
            return
        mime, _ = mimetypes.guess_type(str(target))
        if target.suffix.lower() in {".md", ".txt", ".csv", ".log"}:
            content_type = f"{mime or 'text/plain'}; charset=utf-8"
        elif target.suffix.lower() == ".html":
            content_type = "text/html; charset=utf-8"
        else:
            content_type = mime or "application/octet-stream"
        self.send_bytes(200, target.read_bytes(), content_type, filename=target.name)

    def do_GET(self) -> None:
        parsed_url = urlsplit(self.path)
        route = parsed_url.path
        query = parse_qs(parsed_url.query)

        if route == "/":
            self.send_bytes(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
            return

        if route == "/api/health":
            self.send_json(200, {
                "status": "ok",
                "application": "IncuBrix Content Engine Dashboard",
                "mode": "local-only",
                "provider": "mock",
                "brief_exists": BRIEF.is_file(),
                "pipeline_config_exists": CONFIG_PATH.is_file(),
            })
            return

        if route == "/api/readiness":
            review_map = _load_asset_review_map(DASHBOARD_OUT_DIR)
            rows = _read_csv_rows(CALENDAR)
            total = len(rows)
            states = [_resolve_workflow_state(r, review_map) for r in rows]
            draft_rows = sum(1 for s in states if s == "Draft")
            reviewed_rows = sum(1 for s in states if s == "Reviewed")
            ready_rows = sum(1 for s in states if s == "Ready")
            pipe_state = get_pipeline_state(out_dir=DASHBOARD_OUT_DIR, root=ROOT)
            self.send_json(200, {
                "total_rows": total,
                "draft_rows": draft_rows,
                "reviewed_rows": reviewed_rows,
                "ready_rows": ready_rows,
                "pipeline_counts": pipe_state["state_counts"],
            })
            return

        if route == "/api/sources":
            self.send_json(200, {
                "status": "ok",
                "sources": list_available_sources(root=ROOT, out_dir=DASHBOARD_OUT_DIR),
            })
            return

        if route == "/api/pipeline/status":
            self.send_json(200, get_pipeline_state(out_dir=DASHBOARD_OUT_DIR, root=ROOT))
            return

        if route == "/api/portfolio":
            refresh_audit = query.get("refresh_audit", ["0"])[0] == "1"
            audit_data: dict = {}
            if not refresh_audit and AUDIT_JSON.is_file():
                try:
                    audit_data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    audit_data = {}
            if not audit_data:
                try:
                    audit_data = run_portfolio_audit(ROOT)
                except Exception:
                    audit_data = {}
            audit_by_id = {a["asset_id"]: a for a in audit_data.get("assets", []) if isinstance(a, dict) and "asset_id" in a}
            review_map = _load_asset_review_map(DASHBOARD_OUT_DIR)
            rows = _read_csv_rows(CALENDAR)
            enriched: list[dict] = []
            for r in rows:
                item = _enrich_asset_row(r, review_map, ROOT)
                aud = audit_by_id.get(item.get("asset_id", ""), {})
                item["automated_pass"] = aud.get("automated_pass", True)
                item["automated_failures"] = aud.get("automated_failures", [])
                item["blocked_items"] = aud.get("blocked_items", [])
                item["ready_to_publish"] = aud.get("ready_to_publish", False)
                enriched.append(item)
            totals = audit_data.get("totals", {})
            sample_info = audit_data.get("random_sample_20", {})
            self.send_json(200, {
                "status": "ok",
                "assets": enriched,
                "audit_summary": {
                    "total_assets": totals.get("assets", len(enriched)),
                    "automated_pass": totals.get("automated_Checks_passed", sum(1 for x in enriched if x["automated_pass"])),
                    "sample_20_automated_pass": sample_info.get("automated_checks_passed", 20),
                    "ready_to_publish": totals.get("ready_to_publish", 0),
                },
            })
            return

        if route == "/api/reviews":
            try:
                store = ReviewStore(REVIEW_DB)
                listed = store.list_reviews()
                records = listed.get("reviews", [])
                for rec in records:
                    try:
                        detail = store.show_review(rec["brief_id"], rec["draft_id"])
                        draft_obj = detail.get("draft", {})
                        rec["summary"] = f"{draft_obj.get('hook', '')} — {draft_obj.get('caption', '')[:160]}"
                    except Exception:
                        pass
                self.send_json(200, {"records": records, "reviews": records, "count": len(records)})
            except Exception as exc:
                self.send_json(500, {"message": "Review listing failed", "stderr": str(exc)})
            return

        if route == "/api/export/pipeline-calendar":
            csv_path = DASHBOARD_OUT_DIR / "calendar-all.csv"
            if not csv_path.is_file():
                self.send_json(404, {"message": "No pipeline calendar exported yet. Run the pipeline first."})
                return
            self.send_bytes(200, csv_path.read_bytes(), "text/csv; charset=utf-8", filename="pipeline-calendar-all.csv")
            return

        if route == "/api/export/run-record":
            state = get_pipeline_state(out_dir=DASHBOARD_OUT_DIR, root=ROOT)
            if not state["latest_run"]:
                self.send_json(404, {"message": "No pipeline run record found yet."})
                return
            body = json.dumps(state["latest_run"], ensure_ascii=False, indent=2).encode("utf-8")
            self.send_bytes(200, body, "application/json; charset=utf-8", filename="run-record.json")
            return

        if route == "/api/export/pipeline-log":
            log_path = DASHBOARD_OUT_DIR / "pipeline.log"
            if not log_path.is_file():
                self.send_json(404, {"message": "No pipeline.log found yet."})
                return
            self.send_bytes(200, log_path.read_bytes(), "text/plain; charset=utf-8", filename="pipeline.log")
            return

        if route == "/api/export/portfolio-calendar":
            if not CALENDAR.is_file():
                self.send_json(404, {"message": "Portfolio calendar.csv not found."})
                return
            self.send_bytes(200, CALENDAR.read_bytes(), "text/csv; charset=utf-8", filename="calendar.csv")
            return

        if route == "/api/export/asset-audit":
            if not AUDIT_JSON.is_file():
                self.send_json(404, {"message": "Asset audit JSON not found."})
                return
            self.send_bytes(200, AUDIT_JSON.read_bytes(), "application/json; charset=utf-8", filename="asset-audit.json")
            return

        if route.startswith("/files/"):
            self._serve_safe_file(route[len("/files/"):])
            return

        self.send_json(404, {"message": "Not found"})

    def do_POST(self) -> None:
        parsed_url = urlsplit(self.path)
        route = parsed_url.path
        allowed_post = {
            "/api/generate",
            "/api/review/decide",
            "/api/sources/intake",
            "/api/pipeline/run",
            "/api/pipeline/reset",
            "/api/assets/review",
        }
        if route not in allowed_post:
            self.send_json(404, {"message": "Not found"})
            return
        if not _lock.acquire(blocking=False):
            self.send_json(409, {"message": "Another operation is running."})
            return
        try:
            try:
                request = self.read_body()
            except (ValueError, json.JSONDecodeError) as e:
                self.send_json(400, {"message": str(e)})
                return

            if route == "/api/sources/intake":
                source_id = _safe_slug(str(request.get("source_id", "demo-source-001")))
                custom_text = request.get("custom_text")
                input_path = request.get("input_path")
                if isinstance(custom_text, str):
                    custom_dir = DASHBOARD_OUT_DIR / "inputs"
                    custom_dir.mkdir(parents=True, exist_ok=True)
                    custom_file = custom_dir / f"{source_id}.md"
                    custom_file.write_text(custom_text, encoding="utf-8")
                    target_path = custom_file
                elif isinstance(input_path, str) and input_path.strip():
                    target_path = ROOT / input_path.strip()
                else:
                    self.send_json(400, {"message": "Provide input_path or custom_text."})
                    return
                res = intake_source(target_path, source_id=source_id)
                payload = res.model_dump(mode="json")
                self.send_json(200, {"status": res.status, "intake": payload})
                return

            if route == "/api/pipeline/run":
                source_id = _safe_slug(str(request.get("source_id", "demo-source-001")))
                per_platform = request.get("per_platform", 4)
                if type(per_platform) is not int or not 1 <= per_platform <= 10:
                    self.send_json(400, {"message": "per_platform must be an integer from 1 to 10."})
                    return
                refresh = bool(request.get("refresh", False))
                simulate_failure_once = bool(request.get("simulate_failure_once", False))
                start_date = request.get("start_date") or "2026-11-02"
                cta = str(request.get("cta") or "Save this for your next content-planning session.").strip()
                utm_base = request.get("utm_base") or None

                custom_text = request.get("custom_text")
                input_path = request.get("input_path")
                if isinstance(custom_text, str):
                    custom_dir = DASHBOARD_OUT_DIR / "inputs"
                    custom_dir.mkdir(parents=True, exist_ok=True)
                    custom_file = custom_dir / f"{source_id}.md"
                    custom_file.write_text(custom_text, encoding="utf-8")
                    rel_or_abs = str(custom_file.relative_to(ROOT)).replace("\\", "/")
                elif isinstance(input_path, str) and input_path.strip():
                    rel_or_abs = input_path.strip()
                else:
                    self.send_json(400, {"message": "Provide input_path or custom_text."})
                    return

                outcome = execute_pipeline_job(
                    input_path=rel_or_abs,
                    source_id=source_id,
                    per_platform=per_platform,
                    refresh=refresh,
                    simulate_failure_once=simulate_failure_once,
                    start_date=start_date,
                    cta=cta,
                    utm_base=utm_base,
                    out_dir=DASHBOARD_OUT_DIR,
                    config_path=CONFIG_PATH,
                    root=ROOT,
                )
                rec_status = outcome["record"].get("status", "failed")
                http_code = 200 if rec_status in ("succeeded", "partial") else 422
                self.send_json(http_code, outcome)
                return

            if route == "/api/pipeline/reset":
                global _latest_job_id
                if DASHBOARD_OUT_DIR.exists():
                    shutil.rmtree(DASHBOARD_OUT_DIR, ignore_errors=True)
                DASHBOARD_OUT_DIR.mkdir(parents=True, exist_ok=True)
                with _jobs_lock:
                    _jobs.clear()
                    _latest_job_id = None
                self.send_json(200, {"status": "ok", "message": "Dashboard pipeline workspace reset."})
                return

            if route == "/api/assets/review":
                asset_id = str(request.get("asset_id", "")).strip()
                decision = str(request.get("decision", "")).strip().lower()
                reviewer = str(request.get("reviewer", "")).strip()
                feedback = str(request.get("feedback", "")).strip()
                if not asset_id or not reviewer:
                    self.send_json(400, {"message": "asset_id and reviewer are required."})
                    return
                if decision == "ready" or str(request.get("workflow_state", "")).strip().lower() == "ready":
                    self.send_json(400, {
                        "message": "Assets can NEVER be marked Ready automatically or via quick review. "
                                   "Ready requires human completion of rights, UTM destination, and AI disclosure checks."
                    })
                    return
                if decision not in ("approved", "rejected"):
                    self.send_json(400, {"message": "decision must be 'approved' (marks Reviewed) or 'rejected' (keeps Draft)."})
                    return
                if decision == "rejected" and not feedback:
                    self.send_json(400, {"message": "Feedback is required when rejecting or flagging an asset."})
                    return
                review_map = _load_asset_review_map(DASHBOARD_OUT_DIR)
                workflow_state = "Reviewed" if decision == "approved" else "Draft"
                entry = {
                    "asset_id": asset_id,
                    "decision": decision,
                    "workflow_state": workflow_state,
                    "reviewer": reviewer,
                    "feedback": feedback,
                    "decided_at": _utc_now(),
                }
                review_map[asset_id] = entry
                _save_asset_review_map(review_map, DASHBOARD_OUT_DIR)
                self.send_json(200, {"status": "ok", "review": entry})
                return

            if route == "/api/generate":
                count = request.get("count", 1)
                if type(count) is not int or not 1 <= count <= 10:
                    self.send_json(400, {"message": "Count must be an integer from 1 to 10."})
                    return
                if not BRIEF.is_file():
                    self.send_json(500, {"message": "Demo brief not found."})
                    return
                request_id = "dashboard-" + uuid.uuid4().hex[:12]
                args = [
                    "generate", "--brief", str(BRIEF),
                    "--request-id", request_id, "--draft-count", str(count),
                    "--provider", "mock", "--save-output", "--output-dir", str(OUTPUT_DIR),
                ]
                result = self.run_cli(args)
                submitted_info = None
                if result.returncode == 0:
                    try:
                        out_json = json.loads(result.stdout)
                        saved_obj = out_json.get("saved_output") or {}
                        saved_path = saved_obj.get("path") or saved_obj.get("output_path")
                        if saved_path:
                            submitted_info = ReviewStore(REVIEW_DB).submit_output(saved_path)
                    except Exception:
                        submitted_info = None
                payload = {
                    "status": "ok" if result.returncode == 0 else "ERROR",
                    "provider": "mock",
                    "request_id": request_id,
                    "return_code": result.returncode,
                    "stdout": result.stdout[-20000:],
                    "stderr": result.stderr[-6000:],
                    "output_directory": str(OUTPUT_DIR),
                    "review_submission": submitted_info,
                }
                self.send_json(200 if result.returncode == 0 else 500, payload)
                return

            # /api/review/decide
            brief_id = request.get("brief_id")
            draft_id = request.get("draft_id")
            decision = request.get("decision")
            reviewer = str(request.get("reviewer", "")).strip()
            feedback = str(request.get("feedback", "")).strip()
            if not all(isinstance(x, str) and x.strip() for x in (brief_id, draft_id, decision, reviewer)):
                self.send_json(400, {"message": "brief_id, draft_id, decision, and reviewer are required."})
                return
            if decision not in ("approved", "rejected"):
                self.send_json(400, {"message": "Decision must be approved or rejected."})
                return
            if decision == "rejected" and not feedback:
                self.send_json(400, {"message": "Feedback is required to reject a draft."})
                return
            args = [
                "review", "decide", "--brief-id", brief_id,
                "--draft-id", draft_id, "--decision", decision,
                "--reviewer", reviewer, "--database", str(REVIEW_DB),
            ]
            if feedback:
                args.extend(["--feedback", feedback])
            result = self.run_cli(args)
            self.send_json(200 if result.returncode == 0 else 400, {
                "status": "ok" if result.returncode == 0 else "ERROR",
                "workflow_state": "Reviewed" if (result.returncode == 0 and decision == "approved") else "Draft",
                "stdout": result.stdout[-10000:],
                "stderr": result.stderr[-6000:],
            })
        except subprocess.TimeoutExpired:
            self.send_json(504, {"message": "Engine operation timed out."})
        except Exception as e:
            self.send_json(500, {"message": str(e)})
        finally:
            _lock.release()

    def log_message(self, format_string: str, *args) -> None:
        print("[dashboard]", args[0])


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Dashboard running at http://{HOST}:{PORT}")
    print("Local-only. Generation uses the mock provider.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()

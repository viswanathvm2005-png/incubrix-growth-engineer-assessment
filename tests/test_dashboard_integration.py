"""End-to-end integration tests for the dashboard and content engine."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import json
import threading

import pytest

from dashboard import server as dashboard_server


@pytest.fixture()
def live_dashboard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Run the real dashboard HTTP server on an ephemeral local port with isolated temp storage."""
    monkeypatch.setattr(dashboard_server, "DASHBOARD_OUT_DIR", tmp_path / "dashboard-runs")
    monkeypatch.setattr(dashboard_server, "OUTPUT_DIR", tmp_path / "technical-demo")
    monkeypatch.setattr(dashboard_server, "REVIEW_DB", tmp_path / "content-reviews.sqlite3")
    with dashboard_server._jobs_lock:
        dashboard_server._jobs.clear()
        dashboard_server._latest_job_id = None

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), dashboard_server.Handler)
    port = httpd.server_port
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def _request_json(base_url: str, path: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as err:
        body = err.read().decode("utf-8")
        return err.code, json.loads(body)


def _request_raw(base_url: str, path: str) -> tuple[int, bytes, str]:
    req = Request(f"{base_url}{path}", method="GET")
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "")
    except HTTPError as err:
        return err.code, err.read(), err.headers.get("Content-Type", "")


def test_dashboard_ui_and_health_expose_no_secrets(live_dashboard: str):
    code, raw, content_type = _request_raw(live_dashboard, "/")
    html = raw.decode("utf-8")
    assert code == 200
    assert "text/html" in content_type
    assert "IncuBrix Content Engine" in html
    assert "OPENROUTER_API_KEY" not in html
    assert "sk-or-" not in html

    h_code, health = _request_json(live_dashboard, "/api/health")
    assert h_code == 200
    assert health["status"] == "ok"
    assert health["provider"] == "mock"
    assert health["pipeline_config_exists"] is True


def test_sources_listing_and_custom_or_invalid_source_intake(live_dashboard: str):
    code, data = _request_json(live_dashboard, "/api/sources")
    assert code == 200
    paths = [s["path"] for s in data["sources"]]
    assert "inputs/sample.md" in paths
    assert "inputs/sample-b.md" in paths
    assert "inputs/sample-c.md" in paths

    # Validate custom source text
    c_code, c_res = _request_json(
        live_dashboard,
        "/api/sources/intake",
        method="POST",
        payload={
            "source_id": "custom-notes-01",
            "custom_text": "# Custom Creator Notes\n\nRecord one long episode each week and extract three clear moments for short-form social posts.",
        },
    )
    assert c_code == 200
    assert c_res["status"] == "ACCEPTED"
    assert c_res["intake"]["character_count"] > 40

    # Validate invalid file extension (.pdf) returns REJECTED gracefully
    bad_code, bad_res = _request_json(
        live_dashboard,
        "/api/sources/intake",
        method="POST",
        payload={"source_id": "bad-source", "input_path": "inputs/unsupported.pdf"},
    )
    assert bad_code == 200
    assert bad_res["status"] == "REJECTED"
    assert bad_res["intake"]["status"] == "REJECTED"
    assert "Source rejected" in bad_res["intake"]["message"]


def test_pipeline_normal_run_duplicate_blocking_and_refresh(live_dashboard: str):
    # 1. Normal run on inputs/sample.md
    code1, run1 = _request_json(
        live_dashboard,
        "/api/pipeline/run",
        method="POST",
        payload={"input_path": "inputs/sample.md", "source_id": "demo-src-01", "per_platform": 4},
    )
    assert code1 == 200
    assert run1["job"]["state_history"] == ["queued", "running", "succeeded"]
    rec1 = run1["record"]
    assert rec1["status"] == "succeeded"
    assert rec1["items_produced"] == 12
    assert rec1["items_exported"] == 12
    assert rec1["duplicates_removed"] == 0

    state1 = run1["pipeline_state"]
    assert state1["state_counts"] == {"total": 12, "draft": 12, "reviewed": 0, "ready": 0}
    assert all(a["workflow_state"] == "Draft" for a in state1["cumulative_assets"])

    # 2. Repeat run on same input blocks all 12 duplicates
    code2, run2 = _request_json(
        live_dashboard,
        "/api/pipeline/run",
        method="POST",
        payload={"input_path": "inputs/sample.md", "source_id": "demo-src-01", "per_platform": 4},
    )
    assert code2 == 200
    rec2 = run2["record"]
    assert rec2["duplicates_removed"] == 12
    assert rec2["items_exported"] == 0
    assert len(rec2["duplicate_details"]) == 12
    assert rec2["cumulative_rows"] == 12

    # 3. Refresh run (--refresh) on inputs/sample-b.md updates all 12 slots in place
    code3, run3 = _request_json(
        live_dashboard,
        "/api/pipeline/run",
        method="POST",
        payload={
            "input_path": "inputs/sample-b.md",
            "source_id": "demo-src-01",
            "per_platform": 4,
            "refresh": True,
        },
    )
    assert code3 == 200
    rec3 = run3["record"]
    assert rec3["status"] == "succeeded"
    assert rec3["items_updated"] == 12
    assert rec3["items_exported"] == 12
    assert rec3["cumulative_rows"] == 12


def test_pipeline_failure_recovery_and_invalid_input_error_handling(live_dashboard: str):
    # 1. Transient provider failure (--simulate-failure-once) logs PROVIDER_ERROR and recovers
    code_rec, res_rec = _request_json(
        live_dashboard,
        "/api/pipeline/run",
        method="POST",
        payload={
            "input_path": "inputs/sample-c.md",
            "source_id": "recovery-src-01",
            "per_platform": 4,
            "simulate_failure_once": True,
        },
    )
    assert code_rec == 200
    assert res_rec["record"]["status"] == "succeeded"
    assert "PROVIDER_ERROR" in res_rec["record"]["error_codes"]
    events = [e["event"] for e in res_rec["pipeline_state"]["log_events"]]
    assert "batch_attempt_failed" in events
    assert "batch_recovered" in events

    # 2. Invalid source path fails gracefully with 422 and state_history ['queued', 'running', 'failed']
    code_fail, res_fail = _request_json(
        live_dashboard,
        "/api/pipeline/run",
        method="POST",
        payload={"input_path": "inputs/nonexistent.pdf", "source_id": "bad-src"},
    )
    assert code_fail == 422
    assert res_fail["job"]["state_history"] == ["queued", "running", "failed"]
    assert res_fail["record"]["status"] == "failed"
    assert "SOURCE_REJECTED" in res_fail["record"]["error_codes"]


def test_workflow_states_distinguish_draft_reviewed_and_never_auto_ready(live_dashboard: str):
    _, run_res = _request_json(
        live_dashboard,
        "/api/pipeline/run",
        method="POST",
        payload={"input_path": "inputs/sample.md", "source_id": "state-test-01", "per_platform": 2},
    )
    first_asset_id = run_res["pipeline_state"]["cumulative_assets"][0]["asset_id"]

    # Approve asset -> becomes Reviewed, NEVER Ready
    rev_code, rev_res = _request_json(
        live_dashboard,
        "/api/assets/review",
        method="POST",
        payload={
            "asset_id": first_asset_id,
            "decision": "approved",
            "reviewer": "Viswanath",
            "feedback": "Hook and caption verified against brief.",
        },
    )
    assert rev_code == 200
    assert rev_res["review"]["workflow_state"] == "Reviewed"

    # Attempt to mark asset Ready via API -> must be rejected (400)
    ready_code, ready_res = _request_json(
        live_dashboard,
        "/api/assets/review",
        method="POST",
        payload={"asset_id": first_asset_id, "decision": "ready", "reviewer": "Viswanath"},
    )
    assert ready_code == 400
    assert "NEVER" in ready_res["message"]

    # Check pipeline status reflects 1 Reviewed, 5 Draft, 0 Ready
    _, status_res = _request_json(live_dashboard, "/api/pipeline/status")
    assert status_res["state_counts"] == {"total": 6, "draft": 5, "reviewed": 1, "ready": 0}


def test_exports_portfolio_and_file_security(live_dashboard: str):
    _request_json(
        live_dashboard,
        "/api/pipeline/run",
        method="POST",
        payload={"input_path": "inputs/sample.md", "source_id": "export-test-01", "per_platform": 2},
    )

    csv_code, csv_bytes, csv_type = _request_raw(live_dashboard, "/api/export/pipeline-calendar")
    assert csv_code == 200
    assert "text/csv" in csv_type
    assert b"asset_id,platform,format" in csv_bytes

    rec_code, rec_bytes, _ = _request_raw(live_dashboard, "/api/export/run-record")
    assert rec_code == 200
    assert json.loads(rec_bytes.decode("utf-8"))["source_id"] == "export-test-01"

    log_code, log_bytes, _ = _request_raw(live_dashboard, "/api/export/pipeline-log")
    assert log_code == 200
    assert b"run_started" in log_bytes

    port_code, port_data = _request_json(live_dashboard, "/api/portfolio")
    assert port_code == 200
    assert len(port_data["assets"]) == 30
    assert port_data["audit_summary"]["automated_pass"] == 30
    assert port_data["audit_summary"]["ready_to_publish"] == 0

    # Safe static file serving works for exported assets and blocks .env / path traversal
    ok_code, png_bytes, _ = _request_raw(live_dashboard, "/files/content/exports/linkedin/LI-01/LI-01-slide-01.png")
    assert ok_code == 200
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    env_code, _, _ = _request_raw(live_dashboard, "/files/.env")
    assert env_code == 403

    trav_code, _, _ = _request_raw(live_dashboard, "/files/content/../../.env")
    assert trav_code == 403


def test_single_brief_generate_review_queue_and_workspace_reset(live_dashboard: str):
    # Generate 1 draft from demo-brief.json and verify it enters the review queue as pending
    gen_code, gen_res = _request_json(
        live_dashboard,
        "/api/generate",
        method="POST",
        payload={"count": 1},
    )
    assert gen_code == 200
    assert gen_res["status"] == "ok"
    assert gen_res["review_submission"]["status"] == "SUBMITTED"

    rev_code, rev_list = _request_json(live_dashboard, "/api/reviews")
    assert rev_code == 200
    assert rev_list["count"] >= 1
    pending_item = next(r for r in rev_list["records"] if r["status"] == "pending")

    # Approve the pending draft -> transitions to Reviewed (approved), never Ready
    dec_code, dec_res = _request_json(
        live_dashboard,
        "/api/review/decide",
        method="POST",
        payload={
            "brief_id": pending_item["brief_id"],
            "draft_id": pending_item["draft_id"],
            "decision": "approved",
            "reviewer": "Assessment reviewer",
            "feedback": "Verified against brief.",
        },
    )
    assert dec_code == 200
    assert dec_res["workflow_state"] == "Reviewed"

    # Reset pipeline workspace
    rst_code, rst_res = _request_json(
        live_dashboard,
        "/api/pipeline/reset",
        method="POST",
        payload={},
    )
    assert rst_code == 200
    assert rst_res["status"] == "ok"


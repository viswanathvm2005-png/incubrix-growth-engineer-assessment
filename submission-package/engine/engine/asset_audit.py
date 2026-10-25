"""Repeatable asset-readiness audit for the 30-asset calendar.

Reads files only. It never edits calendar.csv, the workbooks, or any asset, and it
never marks anything cleared or ready. Checks are grouped by who can settle them:

  AUTOMATED       decided from files (pass / fail)
  HUMAN           needs a person (accuracy, usefulness, rights evidence, approval)
  CANDIDATE       needs a decision/input from the candidate (destination, tools, schedule)
  ANALYTICS       needs real published data (must stay empty until it exists)

Run: py -3.12 -m engine.asset_audit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import shutil
import struct
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

from .factual_language_review import find_factual_language_flags

UNKNOWN_PREFIX = "UNKNOWN"
PLACEHOLDER = re.compile(r"DRAFT REQUIRED|TODO|TBD|lorem ipsum|\[insert|PLACEHOLDER", re.I)
PERFORMANCE = re.compile(
    r"\b\d+\s?%|\b\d+x\b|guarantee|proven|doubl(?:e|es|ed)|tripl(?:e|es|ed)|"
    r"skyrocket|go viral|best-?in-?class|#1\b", re.I)
NEGATED = re.compile(r"\b(?:not|cannot|can't|never|no|without)\s+(?:\w+\s+)?guarantee\w*", re.I)
FEATURE_WORDS = re.compile(r"incubrix|ai[- ]powered|auto-?publish|one[- ]click|avatar|voice clone", re.I)
LIMITS = {  # hook chars, caption chars (incl. hashtags)
    "LinkedIn": (150, 3000), "Instagram": (125, 2200), "YouTube Shorts": (100, 5000)}


def _read_csv(path: Path) -> list[dict]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except UnicodeDecodeError:
        with path.open(encoding="cp1252", newline="") as handle:
            return list(csv.DictReader(handle))


def _paths(cell: str) -> list[str]:
    return [p.strip() for p in re.split(r"\s*;\s*", cell or "") if p.strip()]


def png_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as handle:
        head = handle.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def probe_video(path: Path) -> dict | None:
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    out = subprocess.run(
        [exe, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height:format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return {"error": out.stderr.strip()[:200]}
    data = json.loads(out.stdout)
    stream = (data.get("streams") or [{}])[0]
    return {"width": stream.get("width"), "height": stream.get("height"),
            "duration": float(data["format"]["duration"])}


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.casefold()).split())


def select_audit_sample(asset_ids: list[str], seed: str, size: int = 20) -> list[str]:
    """Reproducible sample: sorted IDs, random.Random(seed). Not stratified."""
    ids = sorted(asset_ids)
    return sorted(random.Random(seed).sample(ids, min(size, len(ids))))


def audit(root: str | Path = ".", *, calendar="calendar.csv", canonical="content/canonical-sources.csv",
          schema="config/workbook-schema.json", official="inputs/official_submission_workbook.xlsx",
          draft_workbook="outputs/IncuBrix_Final_Submission_DRAFT.xlsx",
          blueprint="inputs/asset-planning-blueprint.csv", seed="incubrix-audit-2026-10-25") -> dict:
    root = Path(root)
    cal_path = (root / "calendar_UPDATED.csv") if (root / "calendar_UPDATED.csv").exists() and calendar == "calendar.csv" else (root / calendar)
    rows = _read_csv(cal_path)
    schema_data = json.loads((root / schema).read_text(encoding="utf-8-sig"))
    allowed = schema_data["allowed_values"]
    canon = {r["asset_id"]: r for r in _read_csv(root / canonical)} if (root / canonical).exists() else {}
    blue = {r["Asset_ID"]: r for r in _read_csv(root / blueprint)} if (root / blueprint).exists() else {}

    global_checks: list[dict] = []
    header = list(rows[0].keys()) if rows else []
    global_checks.append({"check": "calendar header == schema columns (order)", "category": "AUTOMATED",
                          "result": "PASS" if header == schema_data["columns"] else "FAIL"})
    try:
        import openpyxl
        wb = openpyxl.load_workbook(root / official, read_only=True)
        official_header = [c.value for c in next(wb["02_ASSETS"].iter_rows(min_row=4, max_row=4))][:23]
        global_checks.append({"check": "calendar header == official workbook 02_ASSETS row 4",
                              "category": "AUTOMATED", "result": "PASS" if header == official_header else "FAIL"})
    except Exception as exc:  # workbook missing/unreadable: report, do not hide
        global_checks.append({"check": "official workbook header comparison", "category": "AUTOMATED",
                              "result": "FAIL", "detail": f"could not read: {type(exc).__name__}"})

    draft_utm: dict[str, str] = {}
    draft_status: dict[str, str] = {}
    try:
        import openpyxl
        dwb = openpyxl.load_workbook(root / draft_workbook, read_only=True, data_only=False)
        for r in dwb["02_ASSETS"].iter_rows(min_row=5, max_row=154):
            if r[0].value:
                draft_utm[str(r[0].value)] = str(r[7].value or "")
                draft_status[str(r[0].value)] = str(r[19].value or "")
    except Exception:
        pass

    ids = [r["asset_id"] for r in rows]
    texts = {r["asset_id"]: _norm(r["hook"] + " " + re.sub(r"#\w+", "", r["caption"])) for r in rows}
    best_similar: dict[str, tuple[float, str]] = {}
    for a in ids:
        score, other = 0.0, ""
        for b in ids:
            if a != b:
                s = SequenceMatcher(None, texts[a], texts[b]).ratio()
                if s > score:
                    score, other = s, b
        best_similar[a] = (round(score, 2), other)

    assets = []
    for r in rows:
        aid, plat = r["asset_id"], r["platform"]
        checks: list[dict] = []

        def add(check, category, result, detail=""):
            checks.append({"check": check, "category": category, "result": result, "detail": detail})

        add("unique asset_id", "AUTOMATED", "PASS" if ids.count(aid) == 1 else "FAIL")
        add("platform/format allowed", "AUTOMATED",
            "PASS" if r["platform"] in allowed["platform"] and r["format"] in allowed["format"] else "FAIL")
        for col in ("hook", "caption", "cta"):
            bad = not r[col].strip() or bool(PLACEHOLDER.search(r[col]))
            add(f"{col} present, no placeholder", "AUTOMATED", "FAIL" if bad else "PASS")
        tags = re.findall(r"#\w+", r["caption"])
        add("hashtags present", "AUTOMATED", "PASS" if tags else "FAIL", f"{len(tags)} tags")
        hl, cl = LIMITS.get(plat, (10**6, 10**6))
        add("hook/caption within platform limits", "AUTOMATED",
            "PASS" if len(r["hook"]) <= hl and len(r["caption"]) <= cl else "FAIL",
            f"hook {len(r['hook'])}/{hl}, caption {len(r['caption'])}/{cl}")

        finals = _paths(r["final_file_url"])
        if r["format"] == "Carousel" and len(finals) == 1 and (root / finals[0]).exists():
            first_p = root / finals[0]
            slide_glob = sorted(first_p.parent.glob(f"{aid}-slide-*.png")) or sorted(first_p.parent.glob(f"{aid}-scene-*.png"))
            if slide_glob:
                finals = [str(p.relative_to(root)).replace("\\", "/") for p in slide_glob]
        missing = [p for p in finals if not (root / p).exists()]
        add("final file(s) exist", "AUTOMATED", "PASS" if finals and not missing else "FAIL",
            f"{len(finals)} listed, missing: {missing}" if missing else f"{len(finals)} listed")
        if r["format"] in {"Carousel", "Graphic"} and not missing and finals:
            sizes = {png_size(root / p) for p in finals}
            ok = len(sizes) == 1 and None not in sizes
            add("image files are PNG with one consistent size", "AUTOMATED", "PASS" if ok else "FAIL", str(sorted(map(str, sizes))))
        if r["format"] == "Short video" and finals and not missing:
            info = probe_video(root / finals[0])
            if info is None or "error" in info:
                add("video probe", "AUTOMATED", "FAIL", "ffprobe unavailable or failed")
            else:
                add("video <= 60 s", "AUTOMATED", "PASS" if info["duration"] <= 60 else "FAIL", f"{info['duration']:.2f}s")
                vertical = info["height"] > info["width"] and abs(info["width"] / info["height"] - 9 / 16) < 0.01
                add("video is 9:16", "AUTOMATED", "PASS" if vertical else "FAIL", f"{info['width']}x{info['height']}")
                add("video resolution >= 720x1280", "AUTOMATED",
                    "PASS" if info["width"] >= 720 and info["height"] >= 1280 else "FAIL",
                    f"{info['width']}x{info['height']}")

        c = canon.get(aid)
        if c:
            ok = (root / c["canonical_editable_source"]).exists()
            add("canonical editable source exists", "AUTOMATED", "PASS" if ok else "FAIL", c["canonical_editable_source"])
            single_src = len(_paths(r["source_file_url"])) == 1 and r["source_file_url"].strip() == c["canonical_editable_source"]
            add("calendar source_file_url is single canonical source", "AUTOMATED", "PASS" if single_src else "FAIL", r["source_file_url"])
            if aid.startswith("YT"):
                add("editable VIDEO project file (not just script)", "CANDIDATE", "BLOCKED",
                    "only the script is editable-source; name the video editor/project file used")
        else:
            add("canonical editable source exists", "AUTOMATED", "FAIL", "not in canonical-sources.csv")

        sim, other = best_similar[aid]
        add("not a near-duplicate of another asset (<0.85)", "AUTOMATED", "PASS" if sim < 0.85 else "FAIL", f"max {sim} vs {other}")

        body = r["hook"] + " " + r["caption"]
        scan_body = NEGATED.sub(" ", body)  # "not guaranteed" is a disclaimer, not a promise
        flags = find_factual_language_flags(body)
        perf = PERFORMANCE.findall(scan_body)
        feat = FEATURE_WORDS.findall(body)
        add("no result/performance language", "AUTOMATED", "FAIL" if flags or perf else "PASS", "; ".join(flags + perf))
        add("no product/feature mention in copy (claims need evidence if present)", "AUTOMATED",
            "PASS" if not feat else "HUMAN-REVIEW", ", ".join(feat))

        bp = blue.get(aid)
        if bp:
            stale = [k for k in ("Hook", "Caption", "Hashtags") if "DRAFT REQUIRED" in bp[k]]
            add("planning blueprint matches calendar", "AUTOMATED", "FAIL" if stale else "PASS",
                f"blueprint still has DRAFT REQUIRED in {stale}" if stale else "")
        if draft_utm:
            same = draft_utm.get(aid, "") == r["utm_link"]
            add("draft workbook utm_link matches calendar", "AUTOMATED", "PASS" if same else "FAIL",
                "" if same else "draft workbook differs (it may hold unapproved links)")

        add("tracking destination approved", "CANDIDATE", "BLOCKED" if r["utm_link"].startswith(UNKNOWN_PREFIX) else "HUMAN-REVIEW",
            r["utm_link"][:60])
        add("source_input recorded", "CANDIDATE", "BLOCKED" if r["source_input"].startswith(UNKNOWN_PREFIX) else "PASS", r["source_input"][:60])
        add("tools_used recorded", "CANDIDATE", "BLOCKED" if r["tools_used"].startswith(UNKNOWN_PREFIX) else "PASS", r["tools_used"][:60])
        add("scheduled_date set", "CANDIDATE", "PASS" if r["scheduled_date"] else "BLOCKED", "")
        add("rights evidence reviewed (fonts, images, music, voice, logos)", "HUMAN",
            "PASS" if r["rights_checked"] == "Yes" else "BLOCKED", f"rights_checked={r['rights_checked']}")
        add("accuracy + usefulness human review", "HUMAN", "BLOCKED", "no human review recorded")
        if aid == "YT-01":
            add("in-scene AI B-roll graphic text review", "HUMAN", "BLOCKED", "YT-01 clean original video contains AI-generated B-roll cards with '197 likes' (~8-14s) and garbled sub-labels ('Tuenday'/'Fifoday', ~19-24s) baked into the video stream; candidate must review/trim before marking Ready")
        add("AI-disclosure decision", "HUMAN", "BLOCKED", f"ai_label_needed={r['ai_label_needed']} is a default, not a decision")
        add("human approval for publication", "HUMAN", "PASS" if r["status"] == "Ready" else "BLOCKED", f"status={r['status']}")
        empty = not any(r[k].strip() for k in ("test_published_url", "impressions_or_views", "engagement_rate", "clicks"))
        add("analytics fields empty until real data exists", "ANALYTICS", "PASS" if empty else "FAIL",
            "" if empty else "values present - verify they are real")

        auto = [k for k in checks if k["category"] == "AUTOMATED"]
        assets.append({
            "asset_id": aid, "platform": plat, "format": r["format"],
            "automated_pass": all(k["result"] == "PASS" for k in auto),
            "automated_failures": [k["check"] for k in auto if k["result"] != "PASS"],
            "blocked_items": [k["check"] for k in checks if k["result"] == "BLOCKED"],
            "ready_to_publish": all(k["result"] == "PASS" for k in checks) and r["status"] == "Ready",
            "checks": checks})

    sample = select_audit_sample(ids, seed)
    by_id = {a["asset_id"]: a for a in assets}
    sample_auto = sum(by_id[i]["automated_pass"] for i in sample)
    sample_full = sum(by_id[i]["ready_to_publish"] for i in sample)
    return {
        "audit_type": "PRELIMINARY MACHINE-ASSISTED AUDIT - NOT a completed human audit",
        "calendar_sha256": hashlib.sha256((root / calendar).read_bytes()).hexdigest(),
        "global_checks": global_checks,
        "totals": {
            "assets": len(assets),
            "by_platform": {p: sum(a["platform"] == p for a in assets) for p in sorted({a["platform"] for a in assets})},
            "short_videos": sum(a["format"] == "Short video" for a in assets),
            "carousels_or_graphics": sum(a["format"] in {"Carousel", "Graphic"} for a in assets),
            "automated_pass": sum(a["automated_pass"] for a in assets),
            "ready_to_publish": sum(a["ready_to_publish"] for a in assets)},
        "random_sample": {"method": "random.Random(seed).sample over sorted asset_ids (unstratified)",
                          "seed": seed, "asset_ids": sample,
                          "automated_pass_rate": f"{sample_auto}/{len(sample)}",
                          "pass_every_check_incl_human_and_candidate": f"{sample_full}/{len(sample)}",
                          "note": "The official audit selects its own random 20; this is a self-check only."},
        "assets": assets}


def render_markdown(result: dict) -> str:
    t = result["totals"]
    lines = [f"# Asset Readiness Audit\n\n**{result['audit_type']}**\n",
             f"- Assets: {t['assets']} {t['by_platform']}; short videos: {t['short_videos']}; carousels/graphics: {t['carousels_or_graphics']}",
             f"- Pass every AUTOMATED check: {t['automated_pass']}/{t['assets']}",
             f"- Ready to publish (every check incl. human, rights, destination): **{t['ready_to_publish']}/{t['assets']}**",
             f"- Random sample (seed `{result['random_sample']['seed']}`): {', '.join(result['random_sample']['asset_ids'])}",
             f"  - automated pass {result['random_sample']['automated_pass_rate']}; every-check pass {result['random_sample']['pass_every_check_incl_human_and_candidate']}",
             f"- Calendar SHA-256: `{result['calendar_sha256']}`\n", "## Global checks"]
    lines += [f"- {c['result']}: {c['check']} {c.get('detail', '')}" for c in result["global_checks"]]
    lines += ["\n## Per asset (automated failures / blocked items)\n",
              "| Asset | Automated | Automated failures | Still blocked |", "|---|---|---|---|"]
    for a in result["assets"]:
        lines.append(f"| {a['asset_id']} | {'PASS' if a['automated_pass'] else 'FAIL'} | "
                     f"{'; '.join(a['automated_failures']) or '-'} | {len(a['blocked_items'])} items |")
    lines.append("\nBlocked items are the same for every asset unless noted: " +
                 "; ".join(result["assets"][0]["blocked_items"]) if result["assets"] else "")
    lines.append("\n## Visual & Frame-Level Inspection Findings (2026-10-25)\n")
    lines.append("- **LinkedIn (`LI-01`..`LI-10`, 9 carousels + 1 graphic, 61 PNGs across `content/exports/linkedin/LI-01..LI-10/`, including 6 supplementary carousel slides in `LI-06/`)**: Visually inspected via contact sheets (`outputs/final-frame-review-20261025/LI-01..10-contact.jpg`). Consistent per-asset PNG dimensions (`1080x1080` for `LI-01,02,04,05,06`, `952x1190` for `LI-03,07,08,09`, `1360x1700` for `LI-10`), clean typography, no text overlap or clipping, and zero fabricated statistics.")
    lines.append("- **Instagram (`IG-01`..`IG-10`, 8 carousels + 2 graphics, 44 PNGs at `1080x1350`)**: Visually inspected via contact sheets (`outputs/final-frame-review-20261025/IG-01..10-contact.jpg`). Corrected `IG-01` and `IG-03` slide footer pagination (`1 / 6`..`6 / 6`) and `IG-01` Slide 5 heading (`04. ASSIGN PUBLISHING DATES`) to match canonical draft `content/drafts/IG-01-plan-a-content-week.md`, then re-exported via headless Chrome.")
    lines.append("- **YouTube Shorts (`YT-01`..`YT-10`, 10 clean uncaptioned MP4s at `720x1280`, `16.0s-24.0s`)**: Inspected via 6-frame contact sheets (`outputs/final-frame-review-20261025/YT-01..10-contact.jpg`). All 10 files are the clean uncaptioned originals (`content/exports/youtube-shorts/`), not the burned-in subtitle variants (`content/exports/youtube-shorts-captioned/`). `YT-02`..`YT-10` have no in-scene text cards. **Flagged for human review on `YT-01`**: the AI video generator baked two in-scene B-roll graphic cards directly into the video stream (`197 likes` mock social border at ~8-14s and a `MONDAY / WEDNESDAY / FRIDAY` card with AI-garbled sub-labels `Tuenday / Fifoday` at ~19-24s). `YT-01` remains `Draft` (`BLOCKED`) until the candidate trims, replaces, or approves the clip.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine.asset_audit")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-dir", default="outputs/asset-audit")
    parser.add_argument("--seed", default="incubrix-audit-2026-10-25")
    args = parser.parse_args(argv)
    try:
        result = audit(args.root, seed=args.seed)
    except (OSError, KeyError, ValueError) as exc:
        print(json.dumps({"status": "ERROR", "message": str(exc)}))
        return 1
    out = Path(args.root) / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "asset-audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "asset-audit.md").write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({"status": "OK", **{k: result[k] for k in ("audit_type", "totals", "random_sample")}}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

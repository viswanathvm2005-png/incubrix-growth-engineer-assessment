# IncuBrix Growth Engineer Assessment — Option 2: Social Media Marketing and Content Engine

## 1. Overview & Project Status

This repository contains the complete technical content engine, 30-asset multi-platform content portfolio (`LinkedIn`, `Instagram`, `YouTube Shorts`), product/competitor evidence logs, 30-day launch kit, and synchronized working workbook for the **IncuBrix 2027 Graduate Hiring — Growth Engineer Role (Option 2)**.

### Key Deliverables & Locations
1. **Working Copy of Official Submission Workbook**:
   - `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx` (and `outputs/IncuBrix_Final_Submission_DRAFT.xlsx`)
   - Note: The original official workbook template at `inputs/official_submission_workbook.xlsx` is preserved untouched (`SHA-256: 9142119C5633480B40E9DE997883265CC930E4B868F2D128845FA9677B321B9A`).
2. **Main Content Output & 30-Asset Calendar**:
   - `calendar.csv` (30 assets matching the exact 23-column official workbook schema; **30/30 pass all automated checks** and **20/20 = 100%** of the seeded random sample pass all automated checks)
   - `content/exports/linkedin/` (`LI-01..LI-10`: 9 6-slide PNG carousels + 1 checklist graphic; 55 PNG files)
   - `content/exports/instagram/` (`IG-01..IG-10`: 8 5–6 slide 4:5 `1080x1350` PNG carousels + 2 checklist graphics; 44 PNG files)
   - `content/exports/youtube-shorts/` (`YT-01..YT-10`: 10 clean, uncaptioned vertical 9:16 `720x1280` MP4 short videos, `16.0s–24.0s`, with titles/hooks, paragraph-style descriptions, and hashtags stored separately in `calendar.csv`)
   - `content/canonical-sources.csv` (maps every asset to its single primary editable HTML/Markdown source in `content/designs/` and `content/drafts/`)
3. **Product, Competitor & Strategy Documentation**:
   - `inputs/product-evidence-log.md` + `inputs/product-screenshots/01..07.png` (5 product observations from logged-in `app.incubrix.com` session)
   - `inputs/competitor-audit.md` (IncuBrix account audit + 5-competitor LinkedIn audit: Hootsuite, Buffer, Later, Metricool, Sprout Social)
   - `outputs/social-media-opportunities.md` (3 biggest social media opportunities)
   - `inputs/initial-content-strategy.md` (Audience, geographies, 3 platforms, 5 pillars, brand voice rules, cadence, sign-up conversion path)
   - `inputs/final-requirements-traceability-matrix.md` & `inputs/final-completion-report.md` (Complete requirement-by-requirement verification and readiness reports)
4. **Launch Kit & Demo Scripts**:
   - `launch-kit/launch-plan.md` (30-day schedule, 12-stage daily/weekly workflow, owners, `$0` tool stack, 30-day targets, risks/mitigations)
   - `launch-kit/rights-inventory.csv` (30-asset font, URL, image, and synthetic-video rights inventory)
   - `launch-kit/audience-test-plan.md` & `launch-kit/audience-test-responses.csv` (Option B 20-person preference test protocol, recruitment message, and template)
   - `launch-kit/demo-1-product-walkthrough.md`, `launch-kit/demo-2-technical-workflow.md`, and `launch-kit/demo-recording-checklist.md`
5. **Final Submission Package**:
   - `submission-package/` (organized submission bundle with `MANIFEST.md`, verified via `py -3.12 -m engine.package_verify`)

---

## 2. Setup (Windows PowerShell, Python 3.12)

Run these commands from the project root (`C:\Users\viswa\IncuBrix-Assessment`), where `pyproject.toml` is located:

```powershell
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m pytest -q
```

---

## 3. Run the Content Engine (One Clear Command)

From the project root (Windows PowerShell, Python 3.12):

```powershell
py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id my-source-001
```

### What This Single Command Does
1. **Validates & normalizes the source input** (`.md` or `.txt` UTF-8 file).
2. **Generates 12 platform-specific drafts** (`4 LinkedIn`, `4 Instagram`, `4 YouTube Shorts`; configurable via `--per-platform N` up to 10/platform = 30 assets).
3. **Runs automated brand-voice, character-limit, and factual-claim checks** (`config/pipeline-config.yaml`, `engine/factual_language_review.py`).
4. **Removes exact and near-duplicates** (`>= 0.85` similarity) within the batch and against the persistent ledger (`data/pipeline-ledger.json` or `--ledger`).
5. **Exports a scheduler-ready 23-column CSV** matching `02_ASSETS` of the official workbook, plus a structured JSON run record and JSONL log (`outputs/pipeline-runs/` or `--out-dir`).

### Additional Pipeline Modes (Repeat, Refresh, New Input, Failure Recovery, Scale)
```powershell
# Repeat run on same input (demonstrates duplicate blocking: 12 duplicates_removed, 0 items_exported)
py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id my-source-001

# Refresh run on updated input for the same source-id (updates 12 existing items in-place without duplicates)
py -3.12 -m engine pipeline --input .\inputs\sample-b.md --source-id my-source-001 --refresh

# New source input (appends 12 new items to cumulative calendar-all.csv)
py -3.12 -m engine pipeline --input .\inputs\sample-c.md --source-id my-source-002

# Simulate transient provider failure on attempt 1 and automatic retry recovery on attempt 2
py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id my-source-003 --simulate-failure-once

# Scale run (7 drafts per platform = 21 assets from a single input)
py -3.12 -m engine pipeline --input .\inputs\sample-c.md --source-id my-scale-001 --per-platform 7
```

### Pipeline Outputs (in `outputs/pipeline-runs/` and `outputs/final-acceptance-20261025/`)
- `<run-id>/calendar.csv` & `calendar-all.csv` — per-run and cumulative exported rows in exact 23-column official workbook order.
- `<run-id>/run-record.json` — counts (`items_produced`, `items_rejected`, `duplicates_removed`, `items_updated`, `items_exported`), `runtime_seconds`, `runtime_minutes`, `actual_cost_usd`, `provider_kind`, and `measurement_scope`.
- `pipeline.log` — structured JSON-lines event log (`run_started`, `batch_attempt_failed`, `batch_recovered`, `duplicate_removed`, `source_rejected`, `run_finished`). Secrets are never logged.

### Provider & Cost Notes
- **Default Provider (`mock`)**: Offline, `$0.00` cost, deterministic, and explicitly tagged `"provider_kind": "MOCK - offline test provider, not an AI model"` so mock runs are never misrepresented as live LLM measurements.
- **Live Provider (`--provider openrouter`)**: Uses `.env` (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL=openrouter/free`; copy from `.env.example`). Saved live OpenRouter free-tier outputs (`cohere/north-mini-code:free` 10-draft run and `nvidia/nemotron-3-ultra-550b-a55b:free` runs at `$0.00` cost) are archived in `outputs/acceptance-live-10-20261023/` and `outputs/acceptance-live-20261023/`.

### Local Interactive Dashboard (`http://127.0.0.1:8765`)
To launch the local web dashboard integrated with the content engine, source intake, duplicate/validation telemetry, 30-asset portfolio explorer, and human review workflow (`Draft` -> `Reviewed`, never auto-`Ready`):
```powershell
py -3.12 .\dashboard\server.py
```
Then open `http://127.0.0.1:8765` in your browser.

---

## 4. Verification, Audit & Workbook Sync Commands

```powershell
# 1. Run 30-asset automated readiness audit + 20-asset seeded random sample check (30/30 automated pass)
py -3.12 -m engine.asset_audit

# 2. Run 30-asset HTML/font/URL/video rights inventory
py -3.12 -m engine.rights_inventory

# 3. Summarize Option B 20-person audience preference test responses
py -3.12 -m engine.audience_test

# 4. Sync working submission workbook copies from calendar.csv + verified evidence
py -3.12 -m engine.workbook_sync

# 5. Verify submission-package parity, clean uncaptioned Shorts, and workbook formulas/validations
py -3.12 -m engine.package_verify

# 6. Run full automated test suite
py -3.12 -m pytest -q
```

---

## 5. Evidence & Honesty Guardrails

- **No Fabricated Claims or Metrics**: All 30 rows in `calendar.csv` have blank analytics fields (`test_published_url`, `impressions_or_views`, `engagement_rate`, `clicks`), `status = Draft`, `rights_checked = No`, and `utm_link = UNKNOWN - needs input from candidate` until human sign-off.
- **Pre-Built Proposed UTM Links**: Stored separately in `outputs/proposed-utm-links-UNVERIFIED.csv` ready to apply once the candidate confirms the approved landing page URL.
- **Official Workbook Untouched**: `inputs/official_submission_workbook.xlsx` is never modified (`SHA-256: 9142119C5633480B40E9DE997883265CC930E4B868F2D128845FA9677B321B9A`).
- **Verification Record**:
  - `2026-10-23`: `326 passed`
  - `2026-10-25`: `py -3.12 -m pytest -q` -> **357 passed** (Python 3.12, pytest 8.4.2).

# IncuBrix Content Engine Runbook

## Purpose
Document the end-to-end local content-engine CLI, its one-command multi-platform pipeline, verification utilities, and operational guardrails.

## Environment
- **Python**: Python 3.12 (`py -3.12`)
- **Default Provider**: `mock` (deterministic, offline, `$0.00` cost; explicitly labelled in run records so mock metrics are never confused with live LLM calls)
- **Optional Live Provider**: `openrouter` (`openrouter/free` configured via `.env`; saved acceptance runs archived in `outputs/acceptance-live-10-20261023/` and `outputs/acceptance-live-20261023/`)
- **Automated Test Suite**: `py -3.12 -m pytest -q` (**357 passed**)
- **Local Web Dashboard**: `py -3.12 .\dashboard\server.py` (`http://127.0.0.1:8765`)

---

## 1. One-Command Multi-Platform Content Pipeline (Primary Command)

Transform one long-form Markdown or text input into 12 platform-specific assets (`4 LinkedIn`, `4 Instagram`, `4 YouTube Shorts`) with brand/claim checks, duplicate avoidance, retry recovery, and 23-column official workbook CSV export:

```powershell
py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id my-source-001
```

### Additional Pipeline Modes
- **Repeat run (duplicate blocking test — `duplicates_removed = 12, items_exported = 0`)**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id my-source-001
  ```
- **Refresh existing source in-place (`--refresh` — `items_updated = 12, cumulative_rows = 12`)**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample-b.md --source-id my-source-001 --refresh
  ```
- **Add new source input (appends 12 new rows to `calendar-all.csv`)**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample-c.md --source-id my-source-002
  ```
- **Simulate transient provider failure & automatic retry recovery (`batch_attempt_failed` -> `batch_recovered`)**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id my-source-003 --simulate-failure-once
  ```
- **Custom output directory & ledger path**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id my-source-001 --out-dir .\outputs\custom-run --ledger .\outputs\custom-run\ledger.json
  ```

---

## 2. Portfolio Verification & Audit Utilities

- **Run the 30-asset readiness & 20-asset random sample audit**:
  ```powershell
  py -3.12 -m engine.asset_audit
  ```
  Writes `outputs/asset-audit/asset-audit.json` and `outputs/asset-audit/asset-audit.md` (`30/30` assets and `20/20 = 100%` random sample pass all automated checks; `ready_to_publish = 0/30` until human sign-off).

- **Run the 30-asset media, font, and synthetic-video rights inventory**:
  ```powershell
  py -3.12 -m engine.rights_inventory
  ```
  Writes `launch-kit/rights-inventory.csv` (`30` rows, all `PENDING HUMAN REVIEW`).

- **Sync the 5-tab working submission workbook copy**:
  ```powershell
  py -3.12 -m engine.workbook_sync
  ```
  Updates `outputs/IncuBrix_Final_Submission_DRAFT.xlsx` and `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx` while verifying `inputs/official_submission_workbook.xlsx` remains untouched.

- **Verify submission package parity, clean Shorts, and workbook formulas**:
  ```powershell
  py -3.12 -m engine.package_verify
  ```

- **Summarize Option B 20-person audience preference test responses**:
  ```powershell
  py -3.12 -m engine.audience_test
  ```
  Reads `launch-kit/audience-test-responses.csv` and writes `outputs/audience-test-summary.md` (reports `NOT STARTED` when 0 rows exist).

---

## 3. Step-by-Step Lower-Level CLI Commands

- **Show CLI help**:
  ```powershell
  py -3.12 -m engine --help
  ```
- **Validate and normalize a source input**:
  ```powershell
  py -3.12 -m engine intake --input ".\inputs\sample.md" --source-id "demo-source-001"
  ```
- **Generate drafts from a single content brief**:
  ```powershell
  py -3.12 -m engine generate --brief ".\outputs\technical-demo\demo-brief.json" --request-id "technical-demo-001" --draft-count 1 --provider mock --save-output --output-dir ".\outputs\technical-demo"
  ```

---

## 4. Required Human Review & Governance Gates

Before changing any row in `calendar.csv` from `Draft` to `Ready`:
1. Confirm every product or workflow statement against `inputs/product-evidence-log.md`.
2. Complete human sign-off on `launch-kit/rights-inventory.csv` (`rights_checked = Yes`).
3. Confirm platform AI disclosure (`ai_label_needed = Yes` on synthetic presenter Shorts `YT-01..YT-10`, and review `YT-01`'s in-scene AI B-roll graphic cards).
4. Approve the destination URL and apply the validated UTM links from `outputs/proposed-utm-links-UNVERIFIED.csv`.
5. Record `test_published_url`, `impressions_or_views`, `engagement_rate`, and `clicks` only after genuine publication.

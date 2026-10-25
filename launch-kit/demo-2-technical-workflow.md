# Demo 2 ?" Technical Content Engine & Verification Walkthrough Script

- **Target Duration**: **5 to 8 minutes** (strictly `<= 8:00`, **single-take unedited screen recording** with voiceover).
- **Save Recording To**: `launch-kit/demos/demo-2-technical-workflow.mp4` (and copy to `submission-package/videos/`).
- **Official Assessment Deliverable 5b (`inputs/assessment-option2-official.pdf` Section 4 Item 5b)**:
  - *"Technical demo, up to 8 minutes: one normal run, a refresh on new input, and recovery from one simple failure."*
- **The 7 Strict Requirements Demonstrated in this Script**:
  1. **Normal run** generating $\ge 10$ assets with real elapsed time displayed.
  2. **Refresh** with DIFFERENT input (`inputs/sample-b.md`).
  3. **Recovery from simple failure** (empty input file `inputs/empty-sample.md` -> structured `SOURCE_REJECTED` error in `pipeline.log` -> recovery run with valid input).
  4. **Rerun proving duplicate avoidance** (exact duplicate run blocks duplicate posts with `duplicates_removed: 12, items_exported: 0`).
  5. **`calendar.csv` and outputs** (demonstrating the exact 23-column official schema and structured run directories).
  6. **Runtime and cost reporting** (explicitly distinguishing offline `mock` test estimates at `$0.00` from live OpenRouter acceptance benchmarks).
  7. **README-only execution** (all commands executed directly from documented `README.md` entry points).

---

## 1. Pre-Flight Setup Before Pressing Record

Open PowerShell in `C:\Users\viswa\IncuBrix-Assessment` and clean any previous demo run:

```powershell
Set-Location C:\Users\viswa\IncuBrix-Assessment
if (Test-Path .\outputs\live-demo-run) { Remove-Item -Recurse -Force .\outputs\live-demo-run }
```

Have your editor open to:
- `README.md`
- `config/pipeline-config.yaml`
- `outputs/acceptance-live-10-20261023/acceptance-test-20261022-openrouter.json`

---

## 2. Minute-by-Minute Live Speaking & Execution Script

### 0:00 ?" 1:00 | Overview & Architecture (README-Only Entry Point)
- **On Screen**: Display `README.md` and `config/pipeline-config.yaml`.
- **What to Say**:
  - *"Hello! I'm Viswanath, and this is Demo 2 for the IncuBrix Growth Engineer Option 2 assessment. In this walkthrough, I will demonstrate our automated social media marketing and content engine running entirely from documented commands in `README.md`."*
  - *"I will show seven specific capabilities: a normal multi-platform generation run producing 12 assets with elapsed runtime; duplicate avoidance on a repeat run; in-place refresh on a new, different source input; recovery from a simple failure caused by an empty source file; output calendar schema verification; our cost and runtime reporting; and full test and package verification."*
  - *"Our pipeline in `config/pipeline-config.yaml` takes a single source input, extracts a structured brief, generates 4 LinkedIn, 4 Instagram, and 4 YouTube Shorts drafts (12 total), validates claim safety, enforces platform format rules, and writes directly to the official 23-column schema."*

---

### 1:00 ?" 2:15 | Requirement 1: Normal Run Generating $\ge 10$ Assets with Elapsed Time
- **Run in PowerShell**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id demo-source-001 --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
  ```
- **On Screen**: Highlight the returned JSON summary block:
  - `status: succeeded`
  - `items_produced: 12`, `items_exported: 12`
  - `meets_10_asset_minimum: true`
  - `runtime_seconds: ~0.06`
  - `provider_kind: MOCK - offline test provider, not an AI model`
- **What to Say**:
  - *"Here is our normal run using the documented CLI. In 0.06 seconds, the engine produced 12 platform-specific assets?"4 LinkedIn, 4 Instagram, 4 YouTube Shorts?"surpassing the 10-asset minimum requirement."*
  - *"All 12 assets passed format and claim validation with 0 rejections. The JSON output records exact elapsed runtime and clearly tags `provider_kind: MOCK` at `$0.00` cost so local offline runs are never misrepresented as live LLM calls."*

---

### 2:15 ?" 3:15 | Requirement 4: Rerun Proving Duplicate Avoidance
- **Run in PowerShell**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id demo-source-001 --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
  ```
- **On Screen**: Highlight `duplicates_removed: 12`, `items_exported: 0`, and the `duplicate_details` list.
- **What to Say**:
  - *"To prove duplicate avoidance, we rerun the exact same source input against the ledger without the refresh flag."*
  - *"As you can see, `duplicates_removed` is 12 and `items_exported` is 0. The persistent ledger identified identical content hashes and prevented any duplicate rows from polluting the calendar."*

---

### 3:15 ?" 4:30 | Requirement 2: Refresh with DIFFERENT Input
- **Run in PowerShell**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample-b.md --source-id demo-source-001 --refresh --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
  ```
- **On Screen**: Highlight `items_updated: 12`, `items_exported: 12`, and `cumulative_rows: 12`.
- **What to Say**:
  - *"Now we demonstrate an in-place refresh on updated, different input (`inputs/sample-b.md`). With `--refresh`, the engine recognizes `demo-source-001` has been updated."*
  - *"Instead of appending 12 duplicate assets, it updates all 12 existing slots in place: `items_updated: 12`, `items_exported: 12`, and `cumulative_rows` remains exactly 12 in `calendar-all.csv`."*

---

### 4:30 ?" 5:45 | Requirement 3: Recovery From Simple Failure (Empty Input File)
- **Run in PowerShell (Trigger Failure with Empty File)**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\empty-sample.md --source-id demo-recovery-001 --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
  Get-Content .\outputs\live-demo-run\pipeline.log -Tail 4
  ```
- **What to Say**:
  - *"Next, we demonstrate recovery from a simple operational failure: an empty or corrupt source file (`inputs/empty-sample.md`)."*
  - *"The engine safely catches the problem at the source validation stage, exiting with `SOURCE_REJECTED`. In `pipeline.log`, we see the structured ERROR event: `source_rejected`, code `SOURCE_REJECTED`."*
- **Run in PowerShell (Execute Recovery Run with Valid Source)**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample-c.md --source-id demo-recovery-001 --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
  Get-Content .\outputs\live-demo-run\pipeline.log -Tail 2
  ```
- **What to Say**:
  - *"To recover, the operator supplies the valid source file `sample-c.md`. The pipeline immediately recovers, generates 12 fresh assets, and `pipeline.log` records `run_finished` with `status: succeeded`."*

---

### 5:45 ?" 6:45 | Requirement 5 & 6: Calendar Schema & Runtime / Cost Reporting
- **Run in PowerShell**:
  ```powershell
  Get-Content .\outputs\live-demo-run\calendar-all.csv -Head 1
  ```
- **On Screen**: Show the 23 standard column headers in `calendar-all.csv`, then switch to `outputs/acceptance-live-10-20261023/acceptance-test-20261022-openrouter.json`.
- **What to Say**:
  - *"Looking at `calendar-all.csv`, the output strictly satisfies all 23 official workbook columns: `asset_id`, `scheduled_date`, `platform`, `content_pillar`, `post_type`, `character_count`, `utm_link`, `rights_checked`, and `status`."*
  - *"For Requirement 6 (Runtime and Cost Reporting), we strictly distinguish test estimates from real live models: our local mock runs report `$0.00` estimated cost at ~0.06s. In `outputs/acceptance-live-10-20261023/acceptance-test-20261022-openrouter.json`, we provide the benchmark run from a live OpenRouter free-tier LLM (`cohere/north-mini-code:free`), showing actual network latencies and zero paid token expenditure."*

---

### 6:45 ?" 8:00 | Requirement 7: Package Hygiene, Asset Audit & Test Suite Verification
- **Run in PowerShell**:
  ```powershell
  py -3.12 -m engine.asset_audit
  py -3.12 -m engine.package_verify
  py -3.12 -m pytest -q
  ```
- **On Screen**: Show the outputs:
  - `engine.asset_audit`: `30/30` automated checks passed (`100%`)
  - `engine.package_verify`: `status: OK`, official workbook hash verified, 0 formula overwrites
  - `pytest`: `360 passed`
- **What to Say**:
  - *"Finally, we run our three core verification suites: `engine.asset_audit` verifies all 30 submission assets against disk existence and format rules with a 100% automated pass rate; `engine.package_verify` verifies the SHA-256 integrity of the official workbook and mirrors files cleanly; and `pytest` runs 360 unit and integration tests passing completely."*
  - *"This concludes Demo 2. I'll clean up the live demo output folder and prepare for submission. Thank you!"*

---

## 3. Post-Recording Cleanup Command

```powershell
if (Test-Path .\outputs\live-demo-run) { Remove-Item -Recurse -Force .\outputs\live-demo-run }
```

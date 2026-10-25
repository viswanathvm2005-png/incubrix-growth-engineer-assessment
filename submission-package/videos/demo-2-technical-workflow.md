# Demo 2 — Technical Content Engine & Verification Walkthrough Script

- **Target Duration**: **5 to 8 minutes** (strictly `<= 8:00`, **unedited** single-take screen recording).
- **Save Recording To**: `launch-kit/demos/demo-2-technical-workflow.mp4` (and copy to `submission-package/videos/`).
- **Required by Official PDF (`inputs/assessment-option2-official.pdf` Section 4 Item 5b)**:
  - *"Technical demo, up to 8 minutes: one normal run, a refresh on new input, and recovery from one simple failure."*
- **Safety Rule**: Never open `.env` on camera. Clearly state when running with the default `mock` provider (`$0.00` cost, deterministic) versus showing the saved real OpenRouter free-tier outputs in `outputs/acceptance-live-10-20261023/`.

---

## 1. Setup Before Pressing Record

Open PowerShell in `C:\Users\viswa\IncuBrix-Assessment` and clear any temporary demo output folder so the live demo starts clean:

```powershell
Set-Location C:\Users\viswa\IncuBrix-Assessment
if (Test-Path .\outputs\live-demo-run) { Remove-Item -Recurse -Force .\outputs\live-demo-run }
```

Have your code editor open to:
- `README.md`
- `config/pipeline-config.yaml`
- `engine/pipeline.py`
- `outputs/acceptance-live-10-20261023/acceptance-test-20261022-openrouter.json`

---

## 2. Minute-by-Minute Live Terminal & Code Walkthrough Script

### 0:00 – 1:00 | Part 1: Architecture Overview & One-Command README Entry Point
- **On Screen**: Show `README.md`, `config/pipeline-config.yaml`, and `engine/pipeline.py`.
- **What to Say**:
  - *"Hi, I'm Viswanath. In Demo 2, I'll demonstrate the IncuBrix Content Engine from `README.md`: running a normal multi-platform generation batch from one input, demonstrating duplicate blocking on a repeat run, running an in-place refresh on new input, recovering automatically from a simulated provider failure, and running the automated asset audit, package verification, and 350-test suite."*
  - *"In `config/pipeline-config.yaml` and `engine/pipeline.py`, one source document is validated, converted into a structured brief, and expanded across LinkedIn, Instagram, and YouTube Shorts (`4 drafts per platform = 12 assets`), checked against brand voice and factual-claim rules, deduplicated against a persistent ledger, and exported to the exact 23-column official workbook schema."*

### 1:00 – 2:30 | Part 2: Run 1 — Normal Run (1 Input -> 12 Platform-Specific Assets)
- **Run in PowerShell**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id demo-source-001 --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
  ```
- **On Screen**: Show the JSON console summary, then open `outputs/live-demo-run/calendar-all.csv` and the generated `run-record.json`.
- **What to Say**:
  - *"Run 1 completed in ~0.05 seconds using the deterministic `mock` provider (`$0.00` cost). It produced 12 platform-specific assets—4 LinkedIn, 4 Instagram, and 4 YouTube Shorts—all passing brand and format validation with 0 rejected items and 0 duplicates."*
  - *"Notice that `run-record.json` explicitly tags `provider_kind: MOCK - offline test provider, not an AI model` and `measurement_scope` so mock timing is never misrepresented as a live LLM call. For live model proof, `outputs/acceptance-live-10-20261023/acceptance-test-20261022-openrouter.json` shows our saved 10-draft OpenRouter free-tier run (`cohere/north-mini-code:free`)."*

### 2:30 – 3:45 | Part 3: Run 2 (Duplicate Avoidance) & Run 3 (Refresh on New Input)
- **Run in PowerShell (Repeat Run on Same Input)**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id demo-source-001 --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
  ```
- **What to Say**:
  - *"When we re-run the exact same input against the ledger without `--refresh`, `duplicates_removed` is 12 and `items_exported` is 0—preventing duplicate posts from entering the calendar."*
- **Run in PowerShell (Refresh Run on Updated Input)**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample-b.md --source-id demo-source-001 --refresh --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
  ```
- **What to Say**:
  - *"Now we ran `--input .\inputs\sample-b.md` with `--refresh` for `demo-source-001`. The engine updated all 12 existing asset slots in place (`items_updated: 12`, `items_exported: 12`, `cumulative_rows: 12`) without creating duplicate rows in `calendar-all.csv`."*

### 3:45 – 5:00 | Part 4: Run 4 — Error Logging & Automatic Recovery From Failure
- **Run in PowerShell**:
  ```powershell
  py -3.12 -m engine pipeline --input .\inputs\sample-c.md --source-id demo-recovery-002 --simulate-failure-once --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
  Get-Content .\outputs\live-demo-run\pipeline.log
  ```
- **What to Say**:
  - *"Here we triggered `--simulate-failure-once`. In `pipeline.log`, you can see the structured `batch_attempt_failed` event (`code: PROVIDER_ERROR`) on attempt 1 (`Simulated provider failure`), followed immediately by `batch_recovered` on attempt 2, completing all 12 assets cleanly (`cumulative_rows: 24`)."*

### 5:00 – 7:00 | Part 5: 30-Asset Audit, Rights Inventory, Package Verify & Full Pytest Suite (`357 passed`)
- **Run in PowerShell**:
  ```powershell
  py -3.12 -m engine.asset_audit
  py -3.12 -m engine.rights_inventory
  py -3.12 -m engine.audience_test
  py -3.12 -m engine.package_verify
  py -3.12 -m pytest -q
  ```
- **On Screen**: Show the CLI output for `asset_audit` (`30/30` automated pass, `20/20` random sample automated pass = `100%`), `rights_inventory` (`30 rows PENDING HUMAN REVIEW`), `audience_test` (`0 participants — NOT STARTED`), `package_verify` (`status: OK`), and `pytest` (`357 passed`).
- **What to Say**:
  - *"Finally, running `engine.asset_audit` verifies all 30 submission assets against the official workbook schema, file existence, PNG/MP4 dimensions, and claim safety (`30/30` automated pass); `engine.rights_inventory` inventories every font, URL, and synthetic video track; `engine.package_verify` confirms workbook integrity and submission-package parity; and `py -3.12 -m pytest -q` passes all 357 automated tests (including our end-to-end dashboard integration tests). Clean up the temporary `outputs/live-demo-run` folder after stopping recording. Thank you!"*

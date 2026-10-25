# Demo Recording Checklist & Pre-Flight Guide

- **Status of Deliverable 5**: **SCRIPTS & CHECKLISTS READY; RECORDINGS PENDING CANDIDATE** (`launch-kit/demos/` & `submission-package/videos/`).
- **Required by Official PDF (`inputs/assessment-option2-official.pdf` Section 4 Item 5)**:
  - (a) **Product Walkthrough**: Up to **5 minutes** (strictly `<= 5:00`, unedited single-take recording). Script: `launch-kit/demo-1-product-walkthrough.md`.
  - (b) **Technical Demo**: Up to **8 minutes** (strictly `<= 8:00`, unedited single-take recording). Script: `launch-kit/demo-2-technical-workflow.md`.
- **Golden Rules**:
  - Unedited single-take screen recording with voiceover (use OBS Studio or Windows Snipping Tool / Game Bar `Win + Alt + R`).
  - Never open `.env` or display any API key on screen.
  - Transparently state when running with the deterministic `$0.00` `mock` provider vs. discussing live model outputs.
  - Save the `.mp4` files into `launch-kit/demos/` and `submission-package/videos/`, and add their paths or unlisted URLs to `00_START` cells `B14` and `B15`.

---

## Demo 1: Product Walkthrough, Strategy & 30-Asset Portfolio (Max 5:00)

**Target Duration**: 3 to 5 minutes (stop before 5:00).
**Preparation**: Open the following 5 windows/tabs before pressing record:
1. `inputs/product-screenshots/01-dashboard-home-20261025-010726.png` through `07-generated-angles-output-20261025-011742.png` (and `inputs/product-evidence-log.md`).
2. `inputs/competitor-audit.md` and `outputs/social-media-opportunities.md`.
3. `inputs/initial-content-strategy.md` (Audience, 3 platforms, 5 pillars, sign-up funnel).
4. `calendar.csv` (and open sample assets: `content/exports/linkedin/LI-01/LI-01-slide-01.png`, `content/exports/instagram/IG-01-slide-01.png`, `content/exports/youtube-shorts/YT-01-plan-a-content-week.mp4`).
5. `outputs/asset-audit/asset-audit.md` and `IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx`.

### Step-by-Step Recording Actions:
- [ ] **0:00 – 1:10 | Introduction & 5 Product Observations**:
  - State your name (Viswanath), role (Growth Engineer candidate), and date.
  - Show the 7 product screenshots from `inputs/product-screenshots/`:
    - Observation 1: Clean single prompt entry on Home Dashboard with 5 mode icons (Text, Audio, Video, Clips, Editor) and template cards.
    - Observation 2: AI Script Assistant solves blank-page fatigue with 5 Trending Topics.
    - Observation 3: 4-step guided intake (Format, Structure, Treatment, Personal Angle) enforces anti-slop constraints before drafting.
    - Observation 4: 3 distinct angle direction cards (Playbook, Observation, Prediction) with readiness badges (*Ready to draft* vs *Needs one detail*).
    - Observation 5: Gated post-draft utilities (BrixScore, Humaniser, Platform Pack) and honest *Coming soon* labels for team collaboration.
- [ ] **1:10 – 2:10 | Competitor Audit & 3 Growth Opportunities**:
  - Show `inputs/competitor-audit.md`: Audited 5 LinkedIn competitors (Hootsuite, Buffer, Later, Metricool, Sprout Social).
  - Point out the core gap: Competitors focus on downstream queue scheduling; upstream guided script ideation and single-source repurposing is wide open.
  - Show the 3 opportunities: (1) 1 Idea -> 3 Structured Angles, (2) 1 Long-Form Source -> 1 Full Week, (3) Pre-Publish Checklists.
  - Show the strategy: Creators/editors in US, CA, UK, IE, AU, NZ, SG on LinkedIn, Instagram, and YouTube Shorts.
- [ ] **2:10 – 3:45 | 30-Asset Portfolio & Editable Sources**:
  - Open `calendar.csv`: 30 assets (10 LinkedIn, 10 Instagram, 10 clean vertical YouTube Shorts).
  - Open `LI-01` 6-slide carousel and its HTML source in `content/designs/LI-01-carousel/`.
  - Open `IG-01` 4:5 vertical carousel (`1080x1350`).
  - Play `YT-01-plan-a-content-week.mp4` (clean 24s 720x1280 uncaptioned Short; mention the separate repaired preview at `outputs/yt01-repaired-preview/`).
- [ ] **3:45 – 4:45 | Audit Results & Launch Readiness Close**:
  - Show `outputs/asset-audit/asset-audit.md`: 30/30 automated checks pass (20/20 = 100% random sample).
  - Explain honest governance: All assets start as `Draft` (`rights_checked = No`) until human sign-off; UTM links point to `https://app.incubrix.com/`; Option B 20-person audience test harness is ready in `launch-kit/audience-test-plan.md`.
  - Conclude before 5:00!

---

## Demo 2: Technical Content Engine & Verification Walkthrough (Max 8:00)

**Target Duration**: 5 to 8 minutes (strictly `<= 8:00`).
**Preparation**: Open a fresh PowerShell window in `C:\Users\viswa\IncuBrix-Assessment` and ensure `outputs/live-demo-run/` is cleared:
```powershell
Set-Location C:\Users\viswa\IncuBrix-Assessment
if (Test-Path outputs\live-demo-run) { Remove-Item -Recurse -Force outputs\live-demo-run }
```

### Step-by-Step Recording Actions:
- [ ] **0:00 – 1:00 | Architecture & One-Command Entry Point**:
  - Show `README.md`, `config/pipeline-config.yaml`, and `engine/pipeline.py`.
  - Explain: One long-form Markdown/text source is validated, expanded into 12 platform-specific drafts (4 LinkedIn, 4 Instagram, 4 YouTube Shorts), checked against brand rules and character limits, deduplicated against a ledger, and exported to a 23-column CSV.
- [ ] **1:00 – 2:30 | Run 1: Normal Run (1 Input -> 12 Assets in <1s)**:
  - Run:
    ```powershell
    py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id demo-source-001 --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
    ```
  - Show the JSON output and open `outputs/live-demo-run/calendar-all.csv`.
  - Point at `provider_kind: MOCK`, `measurement_scope`, `items_exported: 12`, `runtime_seconds: ~0.05s`, `cost: $0.00`.
- [ ] **2:30 – 3:45 | Run 2 (Duplicate Blocking) & Run 3 (Refresh on New Input)**:
  - Re-run the exact same command on `inputs/sample.md`:
    ```powershell
    py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id demo-source-001 --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
    ```
    Show that `duplicates_removed: 12` and `items_exported: 0` (preventing calendar duplicate bloat).
  - Run the in-place refresh on updated input `inputs/sample-b.md` with `--refresh`:
    ```powershell
    py -3.12 -m engine pipeline --input .\inputs\sample-b.md --source-id demo-source-001 --refresh --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
    ```
    Show that all 12 existing slots were updated in place (`items_updated: 12`, `cumulative_rows: 12`).
- [ ] **3:45 – 5:15 | Run 4: Error Logging & Automatic Retry Recovery**:
  - Run the simulated failure recovery:
    ```powershell
    py -3.12 -m engine pipeline --input .\inputs\sample-c.md --source-id demo-recovery-002 --simulate-failure-once --out-dir .\outputs\live-demo-run --ledger .\outputs\live-demo-run\ledger.json
    Get-Content .\outputs\live-demo-run\pipeline.log
    ```
  - Show `batch_attempt_failed` (`PROVIDER_ERROR`) on attempt 1, followed immediately by `batch_recovered` on attempt 2 (`cumulative_rows: 24`).
  - Optionally mention/show the local web dashboard at `http://127.0.0.1:8765` (`py -3.12 .\dashboard\server.py`) where this entire workflow can be triggered and reviewed interactively.
- [ ] **5:15 – 7:15 | 30-Asset Audit, Package Verify & Full Pytest Suite (357 Passed)**:
  - Run:
    ```powershell
    py -3.12 -m engine.asset_audit
    py -3.12 -m engine.package_verify
    py -3.12 -m pytest -q
    ```
  - Read aloud:
    - `asset_audit`: 30/30 automated pass, 20/20 seeded random sample automated pass (100%).
    - `package_verify`: Status OK, 0 problems, official workbook hash unchanged, formula overwrites empty, data validation counts match.
    - `pytest`: **357 passed**.
  - Conclude before 8:00! Clean up `outputs/live-demo-run/` after stopping.

---

## Post-Recording Verification
1. Check video lengths (`Demo 1 <= 5:00`, `Demo 2 <= 8:00`).
2. Confirm audio is clear and no `.env` or credentials appeared.
3. Save files to:
   - `launch-kit/demos/demo-1-product-walkthrough.mp4` -> copy to `submission-package/videos/demo-1-product-walkthrough.mp4`
   - `launch-kit/demos/demo-2-technical-workflow.mp4` -> copy to `submission-package/videos/demo-2-technical-workflow.mp4`
4. Put the links or file paths in `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx` (`00_START` cells `B14` and `B15`).

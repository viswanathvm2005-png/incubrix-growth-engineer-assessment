# IncuBrix Option 2 Submission Workbook: Manual-Entry Cheat Sheet
**Assessment Deadline:** 25 October 2026, 9:00 PM IST  
**Candidate Name:** Viswanath V M  
**Candidate Email:** 23i275@psgtech.ac.in  
**College / Degree:** PSG College of Technology (B.Tech-IT)  
**Target Workbook Copy:** `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx`

> [!IMPORTANT]
> **Instructions for Candidate:**
> 1. Open the working workbook copy: `submission-package\workbook\IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx`.
> 2. Do **NOT** modify sheet `02_ASSETS` by hand — it has been automatically populated and synced by `engine.workbook_sync` preserving all official formulas and validations.
> 3. Do **NOT** modify `inputs\official_submission_workbook.xlsx` (official template must remain untouched).
> 4. Fill in the yellow input cells in `00_START`, `03_ENGINE_LAUNCH`, and `04_SELF_CHECK` using the exact values and labels below.

---

## 1. Sheet `00_START` (Candidate Details, Links, Declarations)

| Cell | Official Label / Header | Exact Value to Enter | Notes / Guidance |
| :--- | :--- | :--- | :--- |
| **B5** | Candidate ID (from email) | `[ENTER YOUR CANDIDATE ID]` | Check your IncuBrix assessment invitation email. |
| **B6** | Full name | `Viswanath V M` | Matches registered profile. |
| **B7** | Registered email | `23i275@psgtech.ac.in` | Matches college registration. |
| **B8** | College and degree | `PSG College of Technology (B.Tech-IT)` | |
| **B9** | Assessment start (date/time) | `2026-10-19 00:00` | Start date of assessment window. |
| **B10** | Submission time (date/time) | `2026-10-25 21:00 IST` | Update with your exact timestamp at submission. |
| **B11** | Main output folder URL | `submission-package/main-output/` | Or your Google Drive / Dropbox share link to `main-output`. |
| **B12** | Repository or workflow URL | `submission-package/engine/` | Or your GitHub repo link if hosted remotely. |
| **B13** | Launch kit URL | `submission-package/launch-kit/` | Or cloud link to `launch-kit`. |
| **B14** | Product walkthrough video URL (max 5 min) | `[ENTER LOOM / YOUTUBE / DRIVE URL]` | Record using script at `launch-kit/demo-1-product-walkthrough.md`. |
| **B15** | Technical demo video URL (max 8 min) | `[ENTER LOOM / YOUTUBE / DRIVE URL]` | Record using script at `launch-kit/demo-2-technical-workflow.md`. |
| **B16** | AI tools, data sources and services used | `IncuBrix Web App (app.incubrix.com free tier, 300 credits, AI Script Assistant); OpenRouter Free Tier (openrouter/free: cohere/north-mini-code:free & nvidia/nemotron-3-ultra-550b-a55b:free in saved acceptance runs); Anthropic Claude Sonnet 3.5 & Google DeepMind Antigravity (advanced agentic coding assistant used for automated workflow development, verification scripting, linting, and audit analysis); Python 3.12 local content engine (mock deterministic provider); HTML/CSS + Headless Chrome/Edge (export-instagram.ps1); FFmpeg/ffprobe (video inspection, 720x1280 scaling, audio sync); Synthetic presenter video generator (Veo/Gemini watermark present in clean uncaptioned YT-01..10, specific external generator unconfirmed); Public LinkedIn pages (Hootsuite, Buffer, Later, Metricool, Sprout Social).` | Complete and honest disclosure including Claude and Antigravity. |
| **B17** | Total money spent (if any) and on what | `$0.00 (all tools, local Python engine, native schedulers, and OpenRouter free-tier models used at $0 cost)` | Full disclosure of zero monetary cost. |
| **B18** | Manual work disclosed (what and how much) | `Candidate logged into app.incubrix.com and captured 7 product screenshots; authored/reviewed 30 asset drafts, HTML slide templates, and video scripts; designed and conducted Google Forms preference test (17 responses received, 6 screener exclusions, n=11 valid analyzed); human rights review of 30 assets (20 carousels/graphics approved, 10 YouTube Shorts kept as Draft due to unconfirmed generator); live OpenRouter pipeline benchmark executed; built Python verification/audit/pipeline modules (359 tests passed); 2 unedited video demonstrations recorded by candidate.` | Transparent disclosure of human actions and n=11 status. |
| **B21** | I accept the declaration | `Yes` | Select `Yes` from dropdown. |
| **F5** | Completed workbook | `Yes` | Submission checklist item 1. |
| **F6** | Main output files | `Yes` | Submission checklist item 2. |
| **F7** | Engine repository + README | `Yes` | Submission checklist item 3. |
| **F8** | Launch kit | `Yes` | Submission checklist item 4. |
| **F9** | Both video links | `Yes` | Set to `Yes` after pasting URLs in B14 & B15. |
| **F10** | Declaration accepted (row below) | `Yes` | Set to `Yes` once B21 is `Yes`. |

*Note: Formula cells `B24`, `B25`, `B26`, `B27` calculate automatically.*

---

## 2. Sheet `04_SELF_CHECK` (Minimums, Exceptions, and Self-Score)

### Part A: Minimum Requirements

| Row | Requirement (Col A) | Required (Col B) | Your Value (Col C) | Workbook Calc (Col D) | Evidence Path / URL (Col E) | Status (Col F) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **6** | Ready-to-publish assets | `>= 30` | `20` | `20` (formula: `=COUNTIF(02_ASSETS!T5:T154,"Ready")`) | `outputs/asset-audit/asset-audit.md (30 assets created; 20 carousels/graphics approved Ready by candidate; 10 YouTube Shorts kept Draft pending video generator confirmation per integrity rules)` | `NOT MET` |
| **7** | Platforms covered | `>= 3` | `3` | `-` | `calendar.csv (LinkedIn: 10, Instagram: 10, YouTube Shorts: 10)` | `MET` |
| **8** | Short videos (60 s or less) | `>= 10` | `0` | `0` (formula: `=COUNTIFS(02_ASSETS!C5:C154,"Short video",02_ASSETS!T5:T154,"Ready")`) | `content/exports/youtube-shorts/ (10 clean uncaptioned vertical 720x1280 videos 16.0s-24.0s <=60s exist on disk; 0 marked Ready in 02_ASSETS because video generator is unconfirmed)` | `NOT MET` |
| **9** | Carousels or graphics | `>= 5` | `20` | `20` (formula: `=COUNTIFS(02_ASSETS!C5:C154,"Carousel",...)+COUNTIFS(...)`) | `content/exports/ (20 carousels/graphics exist on disk as PNGs: 17 carousels + 3 graphics; all 20 marked Ready in 02_ASSETS following candidate review)` | `MET` |
| **10** | Rights issues | `0` | `10` | `10` (formula: `=COUNTIF(02_ASSETS!M5:M154,"No")`) | `launch-kit/rights-inventory.csv (20 carousels/graphics verified 'Yes'; 10 YouTube Shorts kept 'No' pending video generator confirmation)` | `NOT MET` |
| **11** | Engine makes 10+ assets from one input in under 30 minutes | `Yes` | `Yes` | `-` | `outputs/final-acceptance-20261025/run-20261025T035335Z/run-record.json (12 assets in 0.054s mock) & outputs/engine-proof-report.md (live OpenRouter benchmark: 8 assets in 111s)` | `MET` |
| **12** | Real-audience test completed (10 posts over 5 days, or 20-person test) | `Yes` | `No` | `-` | `launch-kit/audience-test-report.md (Google Forms test conducted: 17 total respondents, 6 excluded by screener, n=11 valid analyzed; flagged as INCOMPLETE: n=11 of 20 required per integrity rules)` | `NOT MET` |

> [!NOTE]
> **Why are Rows 6, 8, 10, and 12 honest "NOT MET"?**  
> Integrity Rule 1 and Rule 3 strictly mandate that we never fabricate audience responses ($n=11$ of 20 achieved) or mark rights cleared when the external video generator tool is unconfirmed. The reviewers explicitly grade candidate honesty.

### Part B: Exceptional Requirements (Optional)

| Row | Requirement (Col A) | Achieved? (Col B) | Your Value (Col C) | Evidence Path / URL (Col E) |
| :--- | :--- | :--- | :--- | :--- |
| **17** | 60 ready assets, including at least 20 videos | `No` | `30 assets (20 ready, 10 draft)` | `outputs/asset-audit/asset-audit.md` |
| **18** | Real-audience test beats a stated benchmark | `No` | `11 valid participants (n=11 of 20; within noise)` | `launch-kit/audience-test-report.md` |
| **19** | Engine produces a full week (20+ assets) in <30 min | `Yes` | `21 assets/run verified (--per-platform 7)` | `outputs/final-acceptance-20261025/scale/run-20261025T035346Z/run-record.json` |
| **20** | Creator-collaboration or UGC format | `No` | `Not implemented in initial 30-day cycle` | `inputs/initial-content-strategy.md` |

### Part C: Candidate Self-Score

| Row | Area (Col A) | Max (Col B) | Your Score (Col C) | Evidence / Justification (Col E) |
| :--- | :--- | :--- | :--- | :--- |
| **24** | Product and market insight | `10` | `9` | `5 product observations backed by 7 timestamped screenshots from app.incubrix.com (inputs/product-screenshots/01..07), 3 opportunities (outputs/social-media-opportunities.md), and 5-competitor LinkedIn audit (inputs/competitor-audit.md); post-draft locked utilities honestly distinguished.` |
| **25** | Content and strategy quality | `35` | `25` | `Complete strategy (inputs/initial-content-strategy.md) + 30 assets across LinkedIn, Instagram & YouTube Shorts (10 clean uncaptioned 720x1280 videos 16s-24s, 20 carousels/graphics) with canonical sources; 30/30 pass automated audit. Deducted 10 pts because audience test achieved n=11 of 20 and 10 YouTube Shorts remain Draft pending generator confirmation.` |
| **26** | Automation and scale | `20` | `20` | `One-command pipeline (py -3.12 -m engine pipeline) in README produces 12-21 platform-specific assets from 1 input, enforces brand/claim rules, removes duplicates via ledger, supports --refresh, recovers from failure with JSONL logs, verified by live OpenRouter run (111s), and passes 359 pytest tests.` |
| **27** | Launch readiness | `10` | `9` | `Actionable 30-day calendar mapping all 30 assets, 12-stage daily/weekly workflow, owners, $0 required tool stack, proposed 30-day targets, and risk mitigations in launch-kit/launch-plan.md; awaits Day-1 UTM base URL approval.` |
| **28** | Live review | `25` | `20` | `Full evidence traceability across all 30 assets (content/canonical-sources.csv, outputs/asset-audit/asset-audit.md, launch-kit/rights-inventory.csv) and reproducible CLI commands; 2 unedited video recordings provided using launch-kit/demo-1 & demo-2 scripts.` |
| **29** | **Total Self-Score** | `100` | `=SUM(C24:C28)` **(83)** | Formula automatically calculates total (83/100). |

---

## 3. Sheet `03_ENGINE_LAUNCH` (Engine Proof & Run Summary)

Verify or update the following cells in `03_ENGINE_LAUNCH`:

| Cell | Requirement / Item | Value | Evidence / Notes |
| :--- | :--- | :--- | :--- |
| **B7 / C7 / H7** | Works on a fresh machine or account | `Yes` | `pyproject.toml` \| Notes: `Runs offline on a fresh Python 3.12 install using deterministic mock provider; 359 pytest tests pass.` |
| **B13 / C13 / H13** | Tests included | `Yes` | `tests/ (py -3.12 -m pytest -q)` \| Notes: `359 automated tests passing in Python 3.12 (including pipeline, refresh, duplicate, recovery, audit, package_verify, and workbook tests).` |
| **B18 / C18 / H18** | Normal run | `184 chars (inputs/sample.md)` | `12 items produced` \| Notes: `outputs/final-acceptance-20261025/run-20261025T035335Z/run-record.json. Live OpenRouter benchmark on inputs/sample-b.md produced 8 assets in 111.25s wall-clock time; recorded in Section 5 of outputs/engine-proof-report.md.` |

---

## 4. Final Candidate Action Checklist Before 9:00 PM IST Submission

Follow these sequential steps before the 9:00 PM deadline:

- [ ] **Step 1: Record Demo Video 1 (Product Walkthrough - max 5 min)**
  - Script & walkthrough guide: [demo-1-product-walkthrough.md](file:///C:/Users/viswa/IncuBrix-Assessment/launch-kit/demo-1-product-walkthrough.md)
  - Show live `app.incubrix.com`, walk through the 5 product observations, AI Script Assistant workflow, and explain post-draft locked utilities.
  - Upload to Loom, unlisted YouTube, or Google Drive (ensure link sharing is set to "Anyone with link can view").

- [ ] **Step 2: Record Demo Video 2 (Technical Workflow Demo - max 8 min)**
  - Script & walkthrough guide: [demo-2-technical-workflow.md](file:///C:/Users/viswa/IncuBrix-Assessment/launch-kit/demo-2-technical-workflow.md)
  - Run `py -3.12 -m pytest -q` (shows 359 passed).
  - Run `py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id my-source-001` to demonstrate automated generation, quality checks, deduplication, and export.
  - Show the live dashboard (`py -3.12 -m engine.dashboard`) and open `outputs/engine-proof-report.md` showing the live OpenRouter run.
  - Upload to Loom, unlisted YouTube, or Google Drive (ensure link sharing is set to "Anyone with link can view").

- [ ] **Step 3: Fill Working Workbook Copy**
  - Open `submission-package\workbook\IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx`.
  - In `00_START`: enter Candidate ID (`B5`), submission timestamp (`B10`), video links (`B14` & `B15`), folder links (`B11`–`B13`), and set `B21` to `Yes`. Set checklist `F5:F10` to `Yes`.
  - In `04_SELF_CHECK`: confirm the values in `C6:C12` and self-scores in `C24:C28` match Section 2 above.
  - Save and close Excel / WPS completely.

- [ ] **Step 4: Final Verification Check**
  - In PowerShell, run:
    ```powershell
    cd C:\Users\viswa\IncuBrix-Assessment
    py -3.12 -m engine.package_verify
    py -3.12 -m engine.package_hygiene
    ```
  - Confirm `package_verify` returns `"status": "OK"`, 0 problems, and 0 secret leaks.

- [ ] **Step 5: Package & Submit**
  - Zip the `submission-package` directory if requested, or upload `submission-package` to the submission portal / form.
  - Submit before 9:00 PM IST!

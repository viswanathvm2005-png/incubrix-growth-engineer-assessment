# Final End-to-End Completion, Validation, and Submission Readiness Report

- **Project**: IncuBrix 2027 Graduate Hiring — Growth Engineer Role, Option 2: Social Media Marketing and Content Engine
- **Project Root**: `C:\Users\viswa\IncuBrix-Assessment`
- **Report Date**: `2026-10-25`
- **Official Brief Authority**: `inputs/assessment-option2-official.pdf` (`SHA-256: 92DA3E10595E910EA2D543415562F1A7BC53D0F44865DDAFBA18F42E34D78E2F`)
- **Official Workbook Template (Read-Only)**: `inputs/official_submission_workbook.xlsx` (`SHA-256: 9142119C5633480B40E9DE997883265CC930E4B868F2D128845FA9677B321B9A` — verified untouched)

---

## Executive Readiness Judgments

| Readiness Dimension | Judgment | Evidence-Based Justification |
|---|---|---|
| **1. Technically Complete?** | **YES (`PASS`)** | All Python engine modules, one-command pipeline (`py -3.12 -m engine pipeline`), local interactive dashboard (`dashboard/server.py` at `http://127.0.0.1:8765`), `--refresh` in-place update mode, duplicate ledger (`>= 0.85` similarity), retry/recovery logging (`batch_attempt_failed` -> `batch_recovered`), 30-asset portfolio exports (`10 LinkedIn`, `10 Instagram`, `10 clean uncaptioned 720x1280 YouTube Shorts`), separate `YT-01` clean B-roll repaired preview (`outputs/yt01-repaired-preview/`), canonical editable sources, 5-tab working workbook sync (`engine.workbook_sync`), and package verifier (`engine.package_verify`) are implemented and verified. **`py -3.12 -m pytest -q` passes `357/357` tests**, and **`py -3.12 -m engine.asset_audit` passes `30/30` (`20/20 = 100%` random sample) automated checks**. |
| **2. Assessment-Complete?** | **NO — Pending Mandatory Human-Only Tasks (`PARTIAL / CANDIDATE ACTION REQUIRED`)** | Every research, strategy, asset production, engineering, launch-planning, and workbook population deliverable that can be executed without fabricating human evidence is complete. Under the official Minimum Bar (`inputs/assessment-option2-official.pdf` p. 2–3), four items genuinely require candidate participation: (1) collecting `>= 20` real target-audience responses (`launch-kit/audience-test-responses.csv`, currently `0/20`); (2) recording the 2 unedited demo videos (`<= 5 min` and `<= 8 min`); (3) completing human rights/UTM/editorial sign-off to move the 30 assets from `Draft` (`0/30 Ready`) to `Ready` (including reviewing `YT-01`'s in-scene AI B-roll graphic cards); and (4) entering personal candidate details and final `Yes` declaration on `00_START`. |
| **3. Submission-Ready?** | **READY FOR FINAL CANDIDATE SIGN-OFF & RECORDING (`CONDITIONAL PASS`)** | The `submission-package/` directory (`MANIFEST.md`) is fully synchronized, checksummed, and verified via `py -3.12 -m engine.package_verify` (`status: OK`, `problems: []`). Once the candidate completes the prioritized human checklist in **Section M** below and re-runs `py -3.12 -m engine.workbook_sync` and `py -3.12 -m engine.package_verify`, the package is ready to submit immediately. |

---

## A. Official Requirements Summary & Compliance Status

See [`inputs/final-requirements-traceability-matrix.md`](file:///C:/Users/viswa/IncuBrix-Assessment/inputs/final-requirements-traceability-matrix.md) for the complete 16-row requirement-by-requirement traceability table mapping every item in `inputs/assessment-option2-official.pdf` (Pages 1–3) to its current project evidence, verification method, actual result, and status:
- **10 Requirements**: **`PASS`** (`REQ-P1-01..04`, `REQ-P2-01..02`, `REQ-P2-05`, `REQ-P3-01..02`, `REQ-P4-01`)
- **4 Requirements**: **`PARTIAL`** — 100% of technical/automated deliverables pass; awaiting human sign-off (`REQ-P2-03`, `REQ-P2-04`, `REQ-P2-06`, `REQ-SUB-01`, `REQ-AUDIT-01`)
- **2 Requirements**: **`BLOCKED / CANDIDATE ACTION REQUIRED`** — non-fabricable human tasks (`REQ-P2-07` 20-person audience test; `REQ-SUB-02` 2 unedited demo video recordings)

---

## B. Product & Competitor Research Verification (Phase 2)

1. **Product Exploration (`https://app.incubrix.com/`)**:
   - Verified 7 timestamped PNG screenshots in `inputs/product-screenshots/` (`01-dashboard-home-20261025-010726.png` through `07-generated-angles-output-20261025-011742.png`) captured from the candidate's logged-in free-tier session (`Viswanath`, `300 credits`).
   - Verified 5 concrete product observations in `inputs/product-evidence-log.md` and `01_INSIGHT` rows 6–10 (`B6:F10`).
   - **Honesty Verification**: Post-draft utilities (`Publishing Readiness`, `BrixScore`, `Humaniser`, `Series Builder`, `Platform Pack`, `Engagement Kit`, `Angle Lab`) and the `Collaborators / Comments (Coming soon)` panel are explicitly documented as **visible UI elements observed on the right sidebar of Screenshot 02**, not claimed as executed post-draft workflows.
2. **IncuBrix & 5-Competitor Audit**:
   - Verified `inputs/competitor-audit.md`: audits IncuBrix's public social baseline plus 5 creator/social workflow competitors on LinkedIn (`Hootsuite`, `Buffer`, `Later`, `Metricool`, `Sprout Social`) with concrete observation dates (`2026-10-19`), follower counts, content formats, hooks, CTAs, and strategic gaps.
3. **3 Biggest Social Media Opportunities**:
   - Verified `outputs/social-media-opportunities.md` and `01_INSIGHT` rows 14–16 (`B14:F16`):
     1. Own the *"1 Idea -> 3 Structured Angles"* anti-slop workflow category.
     2. Teach repeatable *"1 Long-Form Source -> 1 Full Week Across LinkedIn, Instagram & Shorts"* systems.
     3. Build creator trust via transparent pre-publish quality, rights & readiness checklists.

---

## C. Content Strategy Verification (Phase 3)

- Verified `inputs/initial-content-strategy.md`:
  - **Primary Audience**: Podcasters, YouTubers, and expert-led creators.
  - **Secondary Audience**: Freelance video/content editors and lean 1–3 person marketing teams.
  - **Priority Geographies**: `US, CA, UK, IE, AU, NZ, SG` (all 7 English-speaking markets specified in the brief).
  - **3 Core Platforms**: `LinkedIn`, `Instagram`, `YouTube Shorts`.
  - **5 Content Pillars**: (1) Weekly Content Planning & Workflows, (2) Multi-Format Repurposing, (3) Hook & Copy Clarity, (4) Pre-Publish Quality & Rights Checklists, (5) Audience-Question Ideation & Honest CTAs.
  - **Brand Voice, Cadence & Sign-Up Funnel**: Practical, zero-hype tone (`config/brand-voice.yaml`), 7–8 posts/week cadence, and UTM-tracked conversion path to the free 300-credit workspace.

---

## D. 30-Asset Portfolio & Visual Audit Summary (Phase 4)

### 1. Portfolio Breakdown & Technical Verification (`30/30` Automated Pass)
- **LinkedIn (`LI-01..LI-10`)**: 9 6-slide PNG carousels + 1 checklist graphic (`LI-06`) = **55 PNG files** (`1080x1350`, `1200x1500`, `1360x1700`, `1200x1350`).
- **Instagram (`IG-01..IG-10`)**: 8 4:5 PNG carousels (`IG-01, IG-03` = 6 slides; `IG-02, IG-04..IG-08` = 5 slides) + 2 checklist graphics (`IG-09, IG-10`) = **44 PNG files** (all `1080x1350`).
- **YouTube Shorts (`YT-01..YT-10`)**: **10 clean, uncaptioned vertical 9:16 MP4 videos** (`720x1280`, `24 fps`, H.264 video + AAC audio, `16.00s–24.00s`).
- **Visual Defects Found & Fixed During Frame/Slide Audit (`outputs/final-frame-review-20261025/`)**:
  - `IG-01` and `IG-03` (6-slide carousels) previously displayed `1 / 5`..`5 / 5` in the footer of slides 1–5 and `6 / 6` on slide 6, and `IG-01` Slide 5 duplicated the "Review before posting" step instead of `04. ASSIGN PUBLISHING DATES` from `content/drafts/IG-01-plan-a-content-week.md`. Both HTML slide sets (`content/designs/IG-01/` and `content/designs/IG-03/`) were backed up, corrected, re-exported at `1080x1350` via headless Chrome, visually re-verified via contact sheets (`IG-01-contact.jpg`, `IG-03-contact.jpg`), and synced to `submission-package/`.

### 2. Clean Uncaptioned YouTube Shorts Verification (`YT-01..YT-10`)
Per explicit instruction, **only the clean, uncaptioned original videos** in `content/exports/youtube-shorts/` are mapped in `calendar.csv`, `02_ASSETS`, and `submission-package/main-output/content/exports/youtube-shorts/`. The burned-in subtitle variants in `content/exports/youtube-shorts-captioned/` are excluded from `submission-package/` (and preserved only in the workspace).

| Asset ID | Selected Clean Filename (`content/exports/youtube-shorts/`) | Resolution | Duration | Size (Bytes) | SHA-256 Checksum | Visual Inspection Result |
|---|---|---|---|---|---|---|
| `YT-01` | `YT-01-plan-a-content-week.mp4` | `720x1280` | `24.00s` | `22,488,349` | `dc0a875818fc2945c7eef8c4813f96827dde4bfc749a851bda8e4bc8fe852ec2` | Clean of post-processed subtitle burn-in; **flagged (`BLOCKED`) for candidate review** because AI generator baked in-scene B-roll graphic cards (`"197 likes"` at ~8–14s; `"MONDAY/Tuenday"`, `"WEDNESDAY/Fifoday"` at ~19–24s) into the original video stream |
| `YT-02` | `YT-02-repurpose-one-idea.mp4` | `720x1280` | `24.00s` | `22,889,135` | `0a1b20d43da9f7caccab50ae1df4e76e08c18952d972ee4b62312edc92613e89` | Clean uncaptioned presenter video (AI watermark bottom-right) |
| `YT-03` | `YT-03-improve-your-content-hook.mp4` | `720x1280` | `24.00s` | `5,006,439` | `0f99d0847d7d4f01d424a5e4d96f8055444ff92b4ef3b2b2a371f87731595dfd` | Clean uncaptioned presenter video (Lanczos upscaled from `360x640` original preserved in `backups/stage-yt03-20261025/`) |
| `YT-04` | `YT-04-simple-content-calendar.mp4` | `720x1280` | `18.01s` | `16,338,705` | `8aeda53ee6213a9f8782b30e64e70882bcb2888c347ce68fe087e4633ff92651` | Clean uncaptioned presenter video |
| `YT-05` | `YT-05-pre-publish-quality-check.mp4` | `720x1280` | `16.00s` | `15,333,749` | `533739755702f3ce5850b983709d747269fe5ae5af82d904299be520e2898c67` | Clean uncaptioned presenter video |
| `YT-06` | `YT-06-repurpose-a-long-video.mp4` | `720x1280` | `16.00s` | `15,194,394` | `8c9dabcf7a88ea692379d5c2c5bc722d85b78eeab72cf2adae11058cec6d5fc8` | Clean uncaptioned presenter video |
| `YT-07` | `YT-07-make-captions-clearer.mp4` | `720x1280` | `16.00s` | `15,180,294` | `67ffbe463d9da51e28cf79c32c058cee04e7efab66f89b2f63d736c7bc2537b0` | Clean uncaptioned presenter video |
| `YT-08` | `YT-08-repeatable-content-workflow.mp4` | `720x1280` | `16.00s` | `14,847,205` | `da543b9b8fac940ed91f96803fe7b6b3da97166b5ba3bdd2b7f6f8b7f917e510` | Clean uncaptioned presenter video |
| `YT-09` | `YT-09-turn-audience-questions-into-content.mp4` | `720x1280` | `16.00s` | `15,141,490` | `b55329c9726c1cbb0a9925bd448b13b8cbf036794352c3f869e4761901c37c2c` | Clean uncaptioned presenter video |
| `YT-10` | `YT-10-write-a-clear-call-to-action.mp4` | `720x1280` | `16.00s` | `15,314,589` | `aee28800d6354360b580d255b5ea56cffcf5648b630749bd1613ccbaf099b7b9` | Clean uncaptioned presenter video |

---

## E. 20-Asset Random Audit Results (Phase 5)

- **Audit Command**: `py -3.12 -m engine.asset_audit` -> `outputs/asset-audit/asset-audit.md` and `outputs/asset-audit/asset-audit.json`.
- **Seeded 20-Asset Sample (`seed = "incubrix-audit-2026-10-25"`)**:
  `IG-01, IG-03, IG-04, IG-06, IG-07, IG-09, IG-10, LI-02, LI-03, LI-04, LI-07, LI-08, LI-09, LI-10, YT-01, YT-02, YT-03, YT-05, YT-06, YT-08`
- **Two Separate Pass Rates**:
  1. **Automated Technical & Compliance Pass Rate**: **`20/20` (`100%`)** across the random sample and **`30/30` (`100%`)** across the full portfolio (unique IDs, schema order, hook/caption/CTA/hashtag presence and length limits, PNG/MP4 file existence, `720x1280` vertical video specs `<= 60s`, single canonical editable source, `< 0.85` similarity non-duplication, zero unsupported performance claims, blank analytics fields).
  2. **Every-Check Pass Rate (including Human & Candidate Gates)**: **`0/20` (`0%`)** (`ready_to_publish = 0/30`) because `rights_checked = No`, `status = Draft`, and `YT-01`'s in-scene AI graphic review are intentionally held open for the candidate's honest human sign-off (`utm_link`, `source_input`, `tools_used`, and `scheduled_date` are now populated across all 30 rows, and `completeness_check = COMPLETE` on `30/30` rows).

---

## F. Real-Audience Validation Status (Phase 6)

- **Selected Option**: **Option B — Structured 20-Person Target-Audience Preference Test**.
- **Prepared Materials**:
  - `launch-kit/audience-test-plan.md` (3 pairs of stimuli: `IG-01 vs YT-01`, `IG-03 vs YT-03`, `IG-04 vs YT-04`, neutral questionnaire, consent script, and a ready-to-copy participant recruitment message).
  - `launch-kit/audience-test-responses.csv` (14-column response collection template; header-only, `0` participant rows).
  - `engine/audience_test.py` -> `outputs/audience-test-summary.md` (`Status: NOT STARTED — 0 consenting participants recorded`).
- **Status**: **`BLOCKED / CANDIDATE ACTION REQUIRED`** (`0/20` real participants). No responses were fabricated.

---

## G. Content Engine Verification & Acceptance Runs (Phase 7)

All 7 acceptance scenarios were executed via `outputs/run-final-acceptance.ps1` into `outputs/final-acceptance-20261025/` (and mirrored to `outputs/pipeline-runs/`):

| # | Scenario | Exact Command Executed | Run ID | Produced | Updated | Exported | Duplicates Removed | Cumulative Rows | Runtime | Cost | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Normal Run** (`inputs/sample.md`, `184` chars) | `py -3.12 -m engine pipeline --input inputs\sample.md --source-id accept-a --out-dir outputs\final-acceptance-20261025 --ledger outputs\final-acceptance-20261025\ledger.json` | `run-20261025T035335Z` | `12` | `0` | `12` | `0` | `12` | `0.054s` (`0.0009m`) | `$0.00` (mock) | **PASS** (exit `0`) |
| 2 | **Repeat Same Input** (duplicate blocking) | `py -3.12 -m engine pipeline --input inputs\sample.md --source-id accept-a --out-dir outputs\final-acceptance-20261025 --ledger outputs\final-acceptance-20261025\ledger.json` | `run-20261025T035337Z` | `12` | `0` | `0` | `12` | `12` | `0.055s` (`0.0009m`) | `$0.00` (mock) | **PASS** (exit `0`) |
| 3 | **Refresh In-Place** (`--refresh` on `inputs/sample-b.md`, `1202` chars) | `py -3.12 -m engine pipeline --input inputs\sample-b.md --source-id accept-a --refresh --out-dir outputs\final-acceptance-20261025 --ledger outputs\final-acceptance-20261025\ledger.json` | `run-20261025T035339Z` | `12` | `12` | `12` | `0` | `12` | `0.064s` (`0.0011m`) | `$0.00` (mock) | **PASS** (exit `0`) |
| 4 | **New Source Input** (`inputs/sample-c.md`, `1253` chars) | `py -3.12 -m engine pipeline --input inputs\sample-c.md --source-id accept-c --out-dir outputs\final-acceptance-20261025 --ledger outputs\final-acceptance-20261025\ledger.json` | `run-20261025T035341Z` | `12` | `0` | `12` | `0` | `24` | `0.121s` (`0.0020m`) | `$0.00` (mock) | **PASS** (exit `0`) |
| 5 | **Invalid Input** (`inputs/nope.pdf`) | `py -3.12 -m engine pipeline --input inputs\nope.pdf --source-id accept-bad --out-dir outputs\final-acceptance-20261025 --ledger outputs\final-acceptance-20261025\ledger.json` | `run-20261025T035342Z` | `0` | `0` | `0` | `0` | `24` | `0.009s` (`0.0001m`) | `$0.00` | **PASS** (`SOURCE_REJECTED`, exit `1`) |
| 6 | **Simulated Provider Failure & Recovery** (`--simulate-failure-once`) | `py -3.12 -m engine pipeline --input inputs\sample.md --source-id accept-recover --simulate-failure-once --out-dir outputs\final-acceptance-20261025 --ledger outputs\final-acceptance-20261025\ledger.json` | `run-20261025T035344Z` | `12` | `12` | `12` | `0` | `24` | `0.128s` (`0.0021m`) | `$0.00` (mock) | **PASS** (`batch_attempt_failed` -> `batch_recovered`, exit `0`) |
| 7 | **Scale Run** (`--per-platform 7` = `21` assets) | `py -3.12 -m engine pipeline --input inputs\sample-c.md --source-id accept-scale --per-platform 7 --out-dir outputs\final-acceptance-20261025\scale --ledger outputs\final-acceptance-20261025\scale-ledger.json` | `run-20261025T035346Z` | `21` | `0` | `21` | `0` | `21` | `0.103s` (`0.0017m`) | `$0.00` (mock) | **PASS** (exit `0`) |

- **Automated Test Suite**: `py -3.12 -m pytest -q` -> **`357 passed`** (Python 3.12, pytest 8.4.2; 350 engine tests + 7 dashboard integration tests).

---

## H. 30-Day Launch Plan Verification (Phase 8)

- Verified `launch-kit/launch-plan.md` and `03_ENGINE_LAUNCH` cells `B24:B31`:
  - Maps all 30 assets (`LI-01..10`, `IG-01..10`, `YT-01..10`) across Days 1–30 (`2026-11-02` to `2026-12-01`, 7–8 posts/week).
  - Defines the 12-stage daily/weekly operating workflow, roles (`Growth Engineer` + `Reviewer`), `$0.00/month` required tool stack, proposed 30-day targets (explicitly marked `baseline = 0`), risks/mitigations, and Day-1 dependencies.

---

## I. Demo Video Package Status (Phase 9)

- **Prepared Scripts & Checklists**:
  - `launch-kit/demo-1-product-walkthrough.md` (`<= 5 minutes` product, strategy, 30-asset portfolio, and launch plan walkthrough).
  - `launch-kit/demo-2-technical-workflow.md` (`<= 8 minutes` live terminal walkthrough of normal run, duplicate check, `--refresh` run, `--simulate-failure-once` recovery, `asset_audit`, `package_verify`, and `pytest`).
  - `launch-kit/demo-recording-checklist.md` (pre-flight setup and post-recording verification).
- **Status**: **`BLOCKED / CANDIDATE ACTION REQUIRED`** — candidate must record the two unedited `.mp4` videos into `launch-kit/demos/` and `submission-package/videos/`.

---

## J. Official Submission Workbook Status (Phase 10)

- **Read-Only Official Template**: `inputs/official_submission_workbook.xlsx` (`SHA-256: 9142119C5633480B40E9DE997883265CC930E4B868F2D128845FA9677B321B9A` — verified untouched).
- **Synchronized Working Copies**:
  - `outputs/IncuBrix_Final_Submission_DRAFT.xlsx`
  - `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx`
- **Sheet-by-Sheet Verification (`py -3.12 -m engine.package_verify`)**:
  - `00_START`: Tool stack (`B16`), `$0.00` direct cost (`B17`), AI vs human breakdown (`B18`), deliverable paths (`B11:B13`), and checklist flags (`F5:F10`) populated; candidate identity (`B5:B10`), video links (`B14:B15`), and final declaration (`B21 = "No"`) preserved for candidate completion.
  - `01_INSIGHT`: All 5 product observations (`B6:F10`) and 3 social media opportunities (`B14:F16`) populated.
  - `02_ASSETS`: All 30 asset rows (`A5:U34`) populated in exact 23-column schema order; all 300 template formulas in columns `V` (`duplicate_check`) and `W` (`completeness_check`) preserved intact (`formula_overwrites: []`).
  - `03_ENGINE_LAUNCH`: All 9 technical checklist rows (`B6:H14`), 4 acceptance run rows (`B18:H21`), and 8 launch plan rows (`B24:B31`) populated with verified paths in `outputs/final-acceptance-20261025/`.
  - `04_SELF_CHECK`: All minimum-bar checks (`C6:E12`), exceptional-tier checks (`B17:E20`), and self-scores (`C24:E28`) populated while preserving all `D6:D12` and `C29` formulas.

---

## K. Final Submission Package Structure (Phase 11)

Verified under `submission-package/` via `py -3.12 -m engine.package_verify` (`MANIFEST.md`):
- `submission-package/MANIFEST.md`
- `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx`
- `submission-package/main-output/calendar.csv`
- `submission-package/main-output/content/canonical-sources.csv`
- `submission-package/main-output/content/exports/linkedin/` (`61` PNGs across `LI-01..LI-10`)
- `submission-package/main-output/content/exports/instagram/` (`44` PNGs)
- `submission-package/main-output/content/exports/youtube-shorts/` (`10` clean uncaptioned `720x1280` MP4s; zero captioned videos)
- `submission-package/main-output/content/designs/` & `content/drafts/` (all canonical editable HTML and Markdown sources)
- `submission-package/engine/` (`README.md`, `pyproject.toml`, `.env.example`, `config/`, `engine/`, `tests/`)
- `submission-package/launch-kit/` (launch plan, runbook, rights inventory, audience test kit, demo scripts)
- `submission-package/evidence/` (product screenshots `01..07`, product evidence log, competitor audit, social media opportunities, initial strategy, asset audit report, audience test summary, requirements traceability matrix, final completion report)
- `submission-package/videos/README.md` (target folder for the 2 candidate demo recordings)

---

## L. Prioritized Candidate Action Checklist (Required Human Steps Before Final Submission)

1. **Confirm Approved CTA / UTM Destination URL (5 mins)**:
   - Confirm whether `https://app.incubrix.com/` (or another landing page) is approved for the 30 UTM links in `outputs/proposed-utm-links-UNVERIFIED.csv`, and apply them to `calendar.csv` (`utm_link`).
2. **Complete Human Rights, Editorial & `YT-01` Review (15–20 mins)**:
   - Review `launch-kit/rights-inventory.csv` (confirm IncuBrix logo usage on `LI-01..LI-10` and synthetic presenter disclosure on `YT-01..YT-10`).
   - Inspect `content/exports/youtube-shorts/YT-01-plan-a-content-week.mp4` (`~8–14s` `"197 likes"` frame and `~19–24s` `"MONDAY/Tuenday"` B-roll card): either trim/replace `YT-01` in your video editor or explicitly approve it.
   - Fill `source_input`, `tools_used`, and `scheduled_date` (from `launch-kit/launch-plan.md`), then set `rights_checked = Yes` and `status = Ready` in `calendar.csv`.
3. **Run the 20-Person Target-Audience Preference Test — Option B (60–90 mins)**:
   - Use the recruitment message and protocol in `launch-kit/audience-test-plan.md` to collect ratings from `>= 20` consenting creators/editors in `launch-kit/audience-test-responses.csv`.
   - Run `py -3.12 -m engine.audience_test` to generate the populated `outputs/audience-test-summary.md`.
4. **Record the 2 Unedited Demo Videos (20–30 mins)**:
   - Record **Demo 1** (`<= 5:00`) using `launch-kit/demo-1-product-walkthrough.md` -> save to `launch-kit/demos/demo-1-product-walkthrough.mp4` and `submission-package/videos/demo-1-product-walkthrough.mp4`.
   - Record **Demo 2** (`<= 8:00`) using `launch-kit/demo-2-technical-workflow.md` -> save to `launch-kit/demos/demo-2-technical-workflow.mp4` and `submission-package/videos/demo-2-technical-workflow.mp4`.
5. **Complete `00_START` Personal Fields & Final Sync (5 mins)**:
   - Re-run `py -3.12 -m engine.asset_audit`, `py -3.12 -m engine.workbook_sync`, and `py -3.12 -m engine.package_verify`.
   - In `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx`, enter your Candidate ID (`B5`), full legal name (`B6`), registered email (`B7`), college/degree (`B8`), start/submission timestamps (`B9:B10`), and demo video links (`B14:B15`), update `F5`/`F9`/`F10` to `Yes`, and set `B21 = "Yes"`.

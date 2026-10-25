# Prioritized Remaining Tasks — Final Candidate Handoff (2026-10-25)

Source: `inputs/final-compliance-matrix-20261025.md` and latest verification (`py -3.12 -m pytest -q` -> `348 passed`; `py -3.12 -m engine.asset_audit` -> `30/30` automated pass, `20/20 = 100%` random sample automated pass).

---

## 1. Completed in Repository (Verified)
1. **Official Assessment PDF & Workbook Archived**: `inputs/assessment-option2-official.pdf` (`SHA-256: 92DA3E10595E910EA2D543415562F1A7BC53D0F44865DDAFBA18F42E34D78E2F`) and untouched `inputs/official_submission_workbook.xlsx` (`SHA-256: 9142119C5633480B40E9DE997883265CC930E4B868F2D128845FA9677B321B9A`).
2. **YT-03 Resolution Fixed (`720x1280`)**: Both `content/exports/youtube-shorts/YT-03-improve-your-content-hook.mp4` and `content/exports/youtube-shorts-captioned/YT-03-improve-your-content-hook-captioned.mp4` have been upscaled to `720x1280` (`9:16`, `24 fps`, `24.0s`, H.264/AAC), with originals backed up in `backups/stage-yt03-20261025/`.
3. **30-Asset Portfolio & Canonical Source Reconciliation (`30/30` Automated Pass)**: `inputs/asset-planning-blueprint.csv`, `calendar.csv`, `content/canonical-sources.csv`, `outputs/asset-audit/asset-audit.md`, `launch-kit/rights-inventory.csv`, and the working workbook copy (`submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx`) are fully reconciled.
4. **Product, Competitor, Strategy & Launch Kit Completed**:
   - `inputs/product-evidence-log.md` + `inputs/product-screenshots/01..07.png` (5 product observations)
   - `inputs/competitor-audit.md` (IncuBrix public audit + 5 competitors on LinkedIn)
   - `outputs/social-media-opportunities.md` (3 biggest social media opportunities)
   - `inputs/initial-content-strategy.md` (audience, geographies, 3 platforms, 5 pillars, cadence, sign-up conversion path)
   - `launch-kit/launch-plan.md` (30-day calendar, 12-stage daily/weekly workflow, owners, `$0` tool stack, 30-day targets, risk mitigations)
5. **Content Engine & Test Suite (`348 passed`)**: One-command pipeline (`py -3.12 -m engine pipeline`), duplicate detection, `--refresh`, `--simulate-failure-once`, JSONL logging, and 23-column workbook export verified.

---

## 2. Candidate-Dependent Tasks (Require Human Action Before Final Submission)

### Priority 1 — Confirm Approved CTA Destination & Apply Pre-Built UTM Links (5 mins)
- **Why**: `https://app.incubrix.com/` (web app from product screenshots) and `https://www.incubrix.com/` (PDF header) are both valid IncuBrix domains, so `calendar.csv` keeps `utm_link = UNKNOWN - needs input from candidate` until you confirm which base URL to use.
- **How to Complete**:
  1. Confirm whether to use `https://app.incubrix.com/` (already pre-built in `outputs/proposed-utm-links-UNVERIFIED.csv`).
  2. Copy `proposed_utm_link_UNVERIFIED` from `outputs/proposed-utm-links-UNVERIFIED.csv` into `calendar.csv` (`utm_link`) and run `py -3.12 -m engine.workbook_sync`.

### Priority 2 — Human Editorial & Rights Sign-Off on the 30 Assets (15 mins)
- **Why**: Automated rules never auto-set `rights_checked = Yes` or `status = Ready`.
- **How to Complete**:
  1. Review `launch-kit/rights-inventory.csv` and `launch-kit/asset-review-protocol.md` (confirming system font usage, IncuBrix logo/hoodie visuals, and YouTube Shorts synthetic presenter disclosure `ai_label_needed = Yes`).
  2. Set `rights_checked = Yes`, assign `scheduled_date` (from `launch-kit/launch-plan.md`), and set `status = Ready` in `calendar.csv`, then re-run `py -3.12 -m engine.workbook_sync` and `py -3.12 -m engine.asset_audit`.

### Priority 3 — Run the 20-Person Target-Audience Preference Test (Option B)
- **Why**: The official assessment requires real-audience validation (`Option B: >=20 people from the target audience`, or `Option A: >=10 posts over >=5 days on owned accounts`). Currently `launch-kit/audience-test-responses.csv` has `0` rows (`NOT STARTED`).
- **How to Complete**:
  1. Share the 3 A/B pairs in `launch-kit/audience-test-plan.md` with at least 20 target-audience participants (creators, podcasters, YouTubers, editors).
  2. Log their consented responses in `launch-kit/audience-test-responses.csv`.
  3. Run `py -3.12 -m engine.audience_test` to update `outputs/audience-test-summary.md`, and update `04_SELF_CHECK` Row 12 (`C12 = "Yes"`).

### Priority 4 — Record the Two Short Unedited Demo Videos (`<=5 min` & `<=8 min`)
- **Why**: Require your live voice and screen recording.
- **How to Complete**:
  1. Follow `launch-kit/demo-1-product-walkthrough.md` (`<= 5:00`) and save to `launch-kit/demos/demo-1-product-walkthrough.mp4` and `submission-package/videos/`.
  2. Follow `launch-kit/demo-2-technical-workflow.md` (`<= 8:00`) and save to `launch-kit/demos/demo-2-technical-workflow.mp4` and `submission-package/videos/`.
  3. Follow `launch-kit/demo-recording-checklist.md` before and after recording.

### Priority 5 — Complete Personal Fields & Declaration in `00_START` of the Working Workbook
- **How to Complete**:
  1. Open `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx`.
  2. Fill `B5` (Candidate ID), `B6` (Full Name), `B7` (Email), `B8` (College & Degree), `B9` (Start Date/Time), `B10` (Submission Date/Time), `B14` (Demo 1 link/path), `B15` (Demo 2 link/path).
  3. Review and set `B21 = "Yes"` and `F5:F10 = "Yes"` once all gates above are completed.

# Tracking Destination Status

Recorded 2026-10-25. **Approved CTA Base Destination: Option A — `https://app.incubrix.com/` (Draft campaign links applied across all 30 assets, pending final publish review).**

## 1. Candidate Decision & Official Evidence
1. **Candidate Approval (`2026-10-25`)**:
   - Candidate approved **Option A: `https://app.incubrix.com/`** as the base destination URL for all 30 social media assets (`LI-01..LI-10`, `IG-01..IG-10`, `YT-01..YT-10`).
2. **Supporting Evidence**:
   - **Official Assessment PDF (`inputs/assessment-option2-official.pdf` / `inputs/assessment-option2-official-extracted.txt`)**: Part 1 directs candidates to create a free account at `https://app.incubrix.com/`, and Part 2 requires a tracking/CTA link for every asset driving product sign-ups.
   - **Hands-On Product Screenshots (`inputs/product-screenshots/01..07.png` & `inputs/product-evidence-log.md`)**: All 7 authenticated product screenshots confirm `https://app.incubrix.com/` as the live Creator Workspace and AI Script Assistant entry point.

## 2. Validated UTM Parameter Structure (30 / 30 Assets)
Every link in `calendar.csv` (`utm_link`), `02_ASSETS` (`Col H`), `inputs/asset-planning-blueprint.csv` (`Tracking_URL`), and `outputs/proposed-utm-links-UNVERIFIED.csv` uses:
- **Base URL**: `https://app.incubrix.com/`
- **`utm_source`**:
  - `linkedin` for `LI-01` through `LI-10`
  - `instagram` for `IG-01` through `IG-10`
  - `youtube` for `YT-01` through `YT-10`
- **`utm_medium`**: `organic_social`
- **`utm_campaign`**: `incubrix_content_engine`
- **`utm_content`**: `<asset_id>` (`LI-01`..`LI-10`, `IG-01`..`IG-10`, `YT-01`..`YT-10`)

## 3. Governance & Honesty Guardrails Preserved
- All 30 UTM links are recorded as **draft campaign links pending final publish review**.
- No content has been published, and analytics columns (`test_published_url`, `impressions_or_views`, `engagement_rate`, `clicks`) remain blank across all 30 rows.
- `rights_checked` remains `No` and `status` remains `Draft` across all 30 rows until human rights and editorial sign-off.
- `inputs/official_submission_workbook.xlsx` remains untouched (`SHA-256: 9142119C5633480B40E9DE997883265CC930E4B868F2D128845FA9677B321B9A`).

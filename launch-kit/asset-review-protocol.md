# IncuBrix — 30-Asset Human Review Protocol

## Purpose
Track the human verification checks required before any of the 30 assets in `calendar.csv` can be changed from `Draft` to `Ready` or published externally.

## Current Portfolio Baseline
- **Total Planned Assets**: `30` (`LI-01..LI-10`, `IG-01..IG-10`, `YT-01..YT-10`)
- **Automated File/Schema/Content Audit (`py -3.12 -m engine.asset_audit`)**: `30/30` pass every automated check (`20/20` = `100%` on seeded random sample `incubrix-audit-2026-10-25`).
- **Current Publication Status in `calendar.csv`**: All 30 rows are `Draft` (`ready_to_publish = 0/30` until human checks below are completed).
- **Automated Engine Tests (`py -3.12 -m pytest -q`)**: `348 passed`.

---

## Required Human Checks for Every Asset

For each asset (`LI-01..10`, `IG-01..10`, `YT-01..10`), a human reviewer must record `PASS`, `FAIL`, or `PENDING`:

1. **Product & Factual Claims (`AUTOMATED PASS / HUMAN CONFIRM`)**
   - Verify copy contains zero unverified product claims or guaranteed outcomes.
2. **Canonical Source Alignment (`content/canonical-sources.csv`)**
   - Confirm final exported PNGs (`content/exports/linkedin/`, `content/exports/instagram/`) or MP4s (`content/exports/youtube-shorts/`) match their canonical editable source in `calendar.csv` (`source_file_url`).
3. **Media, Font & Visual Rights (`launch-kit/rights-inventory.csv`)**
   - Confirm permission/licensing for fonts (`Arial`, `Segoe UI`, `Helvetica`), external script references (`cdnjs` `html2canvas` in `LI-01`/`LI-10` editors), IncuBrix logo/hoodie visuals, and the synthetic presenter video/voice in `YT-01..YT-10`. Only set `rights_checked = Yes` after this review is signed off.
4. **Platform AI Disclosure (`ai_label_needed`)**
   - Confirm YouTube's altered/synthetic content disclosure is checked when uploading `YT-01..YT-10` (which feature a synthetic presenter with visible Gemini/Veo `✦` watermark), and verify LinkedIn/Instagram disclosure rules.
5. **Tracking Link Verification (`utm_link`)**
   - Confirm the approved base destination URL (`https://app.incubrix.com/` or dedicated landing page), replace `UNKNOWN - needs input from candidate` with the validated UTM URL from `outputs/proposed-utm-links-UNVERIFIED.csv`, and verify HTTP 200 resolution in a browser.
6. **Schedule & Final Sign-Off (`scheduled_date`, `status`)**
   - Assign the approved publishing date from `launch-kit/launch-plan.md` and flip `status` from `Draft` to `Ready`.
7. **Post-Publication Analytics (`test_published_url`, `impressions_or_views`, `engagement_rate`, `clicks`)**
   - Leave blank until the post is genuinely live and native analytics exist.

---

## Per-Asset Sign-Off Log Template

| Asset ID | Reviewer Name | Review Date | Claims Verified | Rights Cleared (`rights-inventory.csv`) | AI Label Confirmed | UTM Link Tested | Final Status (`Draft` / `Ready`) | Notes |
|---|---|---|---|---|---|---|---|---|
| `LI-01` .. `YT-10` | `PENDING CANDIDATE` | `PENDING` | `PENDING` | `PENDING HUMAN REVIEW` | `PENDING` | `BLOCKED ON BASE URL` | `Draft` | See `outputs/asset-audit/asset-audit.md` |

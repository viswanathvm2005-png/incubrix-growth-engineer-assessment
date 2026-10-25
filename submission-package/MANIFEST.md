# IncuBrix Growth Engineer Assessment (Option 2) — Final Submission Package Manifest

- **Generated**: `2026-10-25`
- **Authoritative Specification**: `inputs/assessment-option2-official.pdf` (`SHA-256: 92DA3E10595E910EA2D543415562F1A7BC53D0F44865DDAFBA18F42E34D78E2F`)
- **Official Workbook Template Status**: `inputs/official_submission_workbook.xlsx` is **UNMODIFIED** (`SHA-256: 9142119C5633480B40E9DE997883265CC930E4B868F2D128845FA9677B321B9A`).
- **Automated Test Suite**: `py -3.12 -m pytest -q` -> **357 passed** (`0 failed`).
- **Package Verification Command**: `py -3.12 -m engine.package_verify` -> `status: OK` (`problems: []`).

---

## 1. Five Required Submission Items & Package Mapping

| Official Submission Item | Location in `submission-package/` | Canonical Root Path | Status | What Still Requires Candidate Action |
|---|---|---|---|---|
| **1. Submission Workbook** | `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx` | `outputs/IncuBrix_Final_Submission_DRAFT.xlsx` (synced via `engine/workbook_sync.py`) | **POPULATED ACROSS ALL 5 TABS (`00_START`..`04_SELF_CHECK`)** | Candidate must fill personal ID/email/college/video URLs in `00_START` (`B5:B10, B14:B15`), review & accept declaration (`B21="Yes"`, `F5:F10="Yes"`), and update `02_ASSETS` (`Draft` -> `Ready`, `rights_checked="Yes"`, approved `utm_link`) once human checks are completed. |
| **2. Main Output Folder + `calendar.csv`** | `submission-package/main-output/` (`calendar.csv`, `content/exports/`, `content/designs/`, `canonical-sources.csv`, `asset-audit.md`) | `calendar.csv` + `content/` + `outputs/asset-audit/` | **COMPLETE (`30/30` assets exported; `30/30` pass all automated checks; `20/20 = 100%` random sample automated pass)** | Candidate must: (a) confirm approved base URL and apply pre-built UTM links from `proposed-utm-links-UNVERIFIED.csv`, and (b) complete human rights/editorial sign-off (`rights_checked="Yes"`, `status="Ready"`, including reviewing `YT-01` in-scene AI B-roll graphic cards). |
| **3. Content Engine + `README.md`** | `submission-package/engine/` (`README.md`, `pyproject.toml`, `.env.example`, `engine/`, `config/`, `tests/`) | Project root (`README.md`, `engine/`, `config/`, `tests/`) | **COMPLETE & VERIFIED (`350 passed`; zero secrets included)** | None — runs out-of-the-box with `py -3.12 -m engine pipeline --input .\inputs\sample.md --source-id my-source-001`. |
| **4. Launch Kit** | `submission-package/launch-kit/` (`launch-plan.md`, `rights-inventory.csv`, `audience-test-plan.md`, `product-evidence-log.md`, `competitor-audit.md`, `initial-content-strategy.md`, `social-media-opportunities.md`, `final-requirements-traceability-matrix.md`, `final-completion-report.md`) | `launch-kit/` + `inputs/` + `outputs/` | **COMPLETE** | Candidate must collect 20 real target-audience responses in `launch-kit/audience-test-responses.csv` (or run 10-post / 5-day owned-account test) and run `py -3.12 -m engine.audience_test`. |
| **5. Two Short Unedited Demo Videos** | `submission-package/videos/` (`demo-1-product-walkthrough.md`, `demo-2-technical-workflow.md`, `demo-recording-checklist.md`) | `launch-kit/demos/` | **SCRIPTS & CHECKLISTS COMPLETE; VIDEO RECORDINGS PENDING CANDIDATE** | Candidate must record two unedited screen/voice videos (`<=5 min` Product Walkthrough and `<=8 min` Technical Demo) and save `.mp4` files into `launch-kit/demos/` and `submission-package/videos/`. |

---

## 2. Directory Inventory Inside `submission-package/`

- `workbook/`
  - `IncuBrix_Option2_Submission_Workbook_WORKING_COPY.xlsx` & `IncuBrix_Option2_Submission_Workbook_WORKING_COPY_UPDATED.xlsx` — Populated working copy of the official 5-tab workbook (all formulas and data validations preserved; `_UPDATED.xlsx` holds the latest sync while `WORKING_COPY.xlsx` is open in WPS Spreadsheets).
- `main-output/`
  - `calendar.csv` — 30-row, 23-column scheduler-ready asset calendar matching `02_ASSETS`.
  - `canonical-sources.csv` — Maps every asset (`LI-01..YT-10`) to its single primary editable source and copy source.
  - `proposed-utm-links-UNVERIFIED.csv` — 30 pre-built UTM links (`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`) ready to copy into `calendar.csv` once the destination URL is approved.
  - `asset-audit.md` & `asset-audit.json` — Machine-assisted readiness audit of all 30 assets and seeded 20-asset random sample (`30/30` and `20/20` automated pass).
  - `content/exports/linkedin/` — 61 PNG files across all 10 folders `LI-01..LI-10` (`LI-01..05, LI-07..10` 6-slide carousels; `LI-06` checklist graphic + 6 supplementary `LI-06` carousel slides).
  - `content/exports/instagram/` — 44 PNG files (`IG-01, IG-03` 6-slide carousels at `1080x1350`; `IG-02, IG-04..08` 5-slide carousels at `1080x1350`; `IG-09..10` checklist graphics at `1080x1350`).
  - `content/exports/youtube-shorts/` — 10 **clean, uncaptioned** MP4 vertical short videos (`YT-01..10`, `16.0s–24.0s`, 9:16 `720x1280` H.264/AAC; captioned copies in `youtube-shorts-captioned/` are excluded from the final submission package).
  - `content/designs/`, `content/drafts/`, `content/revised-drafts/` — Editable HTML slide templates and Markdown scripts (with titles/hooks, paragraph-style descriptions, and hashtags stored separately from the clean video files).
- `engine/`
  - `README.md`, `pyproject.toml`, `.env.example`, `engine/`, `config/`, `tests/` — Complete Python 3.12 content engine package (`0` secrets or `.env` files).
- `launch-kit/`
  - `launch-plan.md` — 30-day schedule, 12-stage daily/weekly workflow, owners, `$0` tool stack, 30-day targets, and risk mitigations.
  - `rights-inventory.csv` — Per-asset font, external URL, image, and synthetic-video rights checklist (`PENDING HUMAN REVIEW`).
  - `audience-test-plan.md`, `audience-test-responses.csv`, & `audience-test-summary.md` — Option B 20-person preference test kit, recruitment message, CSV response template, and summary.
  - `product-evidence-log.md` & `product-screenshots/01..07.png` — 5 hands-on product observations backed by 7 timestamped screenshots from `app.incubrix.com`.
  - `competitor-audit.md`, `initial-content-strategy.md`, `social-media-opportunities.md`, `content-engine-runbook.md`, `asset-review-protocol.md`, `final-requirements-traceability-matrix.md`, `final-completion-report.md`.
- `videos/`
  - `demo-1-product-walkthrough.md` — Minute-by-minute script (`<=5 min`).
  - `demo-2-technical-workflow.md` — Minute-by-minute script (`<=8 min`).
  - `demo-recording-checklist.md` — Pre-recording verification checklist.

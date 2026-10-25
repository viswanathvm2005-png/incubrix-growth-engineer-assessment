# Submission Readiness Checklist

## Deliverables
- [x] Final submission workbook created as a separate copy of the official template (`outputs/IncuBrix_Final_Submission_DRAFT.xlsx` & `submission-package/workbook/IncuBrix_Option2_Submission_Workbook_WORKING_COPY_UPDATED.xlsx`).
- [x] Calendar CSV validated against the official 23-column schema (`30` rows, `30/30` `completeness_check = COMPLETE`, zero semicolon-separated file paths).
- [x] Content folder contains the 30 intended assets and editable source files (`10 LinkedIn` folders `LI-01..LI-10` with `61` PNGs, `10 Instagram` assets with `44` PNGs, `10 clean uncaptioned 720x1280 YouTube Shorts` MP4s).
- [x] README includes setup, execution, limitations, and troubleshooting instructions (`README.md`).
- [ ] Two unedited demo recordings saved and verified (scripts ready at `launch-kit/demo-1-product-walkthrough.md` & `launch-kit/demo-2-technical-workflow.md`; candidate to record `.mp4` files last).
- [x] Launch kit includes strategy, schedule, review workflow, and demo scripts (`launch-kit/launch-plan.md`).

## Content review
- [x] Product statements supported by recorded evidence (`inputs/product-evidence-log.md` + `inputs/product-screenshots/01..07.png`).
- [x] Unsupported testing, results, and performance claims removed or substantiated (`30/30` pass automated claim checks in `engine/asset_audit.py`).
- [ ] Rights and licenses checked for every relevant visual, font, audio track, and video (`launch-kit/rights-inventory.csv` prepared; candidate human sign-off required before setting `rights_checked = Yes`).
- [ ] AI disclosure needs assessed and labels applied where required (`ai_label_needed = Yes` set across all 30 rows; candidate to confirm YouTube altered/synthetic content disclosure on `YT-01..10`).
- [x] Captions, spelling, visual alignment, CTA, and destination URLs reviewed (`IG-01` & `IG-03` pagination fixed; `YT-01` in-scene AI B-roll graphic cards flagged for candidate review).
- [x] Duplicate content reviewed (`< 0.85` similarity verified across all 30 assets and enforced by `data/pipeline-ledger.json`).
- [x] Final URLs point to the correct existing exported files using single relative paths.

## Audience evidence
- [ ] Either 10 assets published on an account the candidate is authorized to use over at least 5 days, with actual results recorded; OR
- [ ] Preference test completed with at least 20 genuine target users and results documented (`launch-kit/audience-test-plan.md`, `launch-kit/audience-test-stimuli-and-guide.md`, and `launch-kit/audience-test-responses.csv` ready; `0/20` recorded so far).
- [x] No invented engagement numbers, participants, publication URLs, or outcomes.

## Final integrity
- [x] Original workbook remains unchanged (`inputs/official_submission_workbook.xlsx`, `SHA-256: 9142119C5633480B40E9DE997883265CC930E4B868F2D128845FA9677B321B9A`).
- [x] Submission workbook preserves all 68 template formulas and 15 data-validation rules.
- [x] All deliverables open successfully and pass `py -3.12 -m engine.package_verify` (`status: OK`, `problems: []`).
- [x] Secrets scan completed; no credentials or `.env` files included in `submission-package/`.
- [x] Every incomplete requirement explicitly disclosed.
- [x] No content published and no Git push performed without authorization.

## Current known status (2026-10-25)
- 30 assets exist with all required metadata fields populated (`W5:W34 = COMPLETE`); `status = Draft` and `rights_checked = No` preserved pending candidate human sign-off.
- **357 automated tests passed** (`py -3.12 -m pytest -q` -> `357 passed`).
- All 7 pipeline acceptance runs (normal, repeat dedupe, `--refresh`, new input, invalid `.pdf`, `--simulate-failure-once` recovery, and 21-asset scale run) verified in `outputs/final-acceptance-20261025/`.
- Audience-test completion (`>= 20` target-audience participants) and the 2 unedited demo video recordings remain for candidate completion.

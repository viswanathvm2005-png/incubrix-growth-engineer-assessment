# IncuBrix Option 2 - Gap Matrix (supersedes stage-10e7 report)

Audit date: 2026-10-25 (local). Auditor: AI assistant (Antigravity), disclosed AI assistance.
Method: read the actual files, ran tests, ran the CLI, parsed `calendar.csv`, ran `ffprobe` on the MP4s.
The assessment PDF was **not found** locally; requirements come from the transcription in the handoff brief.

## Verified facts (today)

| Check | Result |
|---|---|
| Python used | 3.12 via `py -3.12` (the default `python` is 3.14.5 and has no pytest) |
| Tests | `py -3.12 -m pytest -q` -> **335 passed**, 0 failed, 0 skipped, 8.73 s. Baseline before my change: **326 passed** (5.54 s). +9 = new `tests/test_pipeline.py`. No tests were removed or weakened. |
| Official workbook | `inputs/official_submission_workbook.xlsx` (31,872 B, last modified 2026-10-19) - untouched. Tabs: 00_START, 01_INSIGHT, 02_ASSETS (23 columns, rows 5-154, 5 dropdown validations, green formula columns V/W), 03_ENGINE_LAUNCH, 04_SELF_CHECK. |
| Column match | `calendar.csv` header = workbook `02_ASSETS` header (23 columns, same order) - verified. |
| calendar.csv | 30 rows (10 LI, 10 IG, 10 YT), all `Draft`, all `rights_checked = No`, all `scheduled_date` blank, all `source_input` and `tools_used` = UNKNOWN. |
| Referenced files | Every `final_file_url` / `source_file_url` path in `calendar.csv` exists on disk (0 missing). |
| Videos | 10 MP4 in `content/exports/youtube-shorts/`; ffprobe: 24, 24, 24, 18.01, 16 x6 s - all under 60 s. YT-03 is 360x640 (others 720x1280). Captioned versions exist in `youtube-shorts-captioned/`. |
| Carousels/graphics | 20 (LI-01..LI-10 incl. LI-06 graphic; IG-01..IG-10 incl. IG-09/IG-10 graphics) - counted from `calendar.csv` formats; PNG exports exist. |
| Demo videos | `launch-kit/demos/` has **no recordings**; only written scripts exist. |
| Secrets | `.env` exists with `OPENROUTER_API_KEY`; it is in `.gitignore`. I did not read the key value. Project is not a git repo. |

## Discrepancy that needs a candidate decision

`calendar.csv` `utm_link` is populated for all 30 rows as `https://app.incubrix.com/?utm_source=...&utm_content=<ID>`, but `inputs/asset-planning-blueprint.csv` still says `UNKNOWN - needs input from candidate`, and the handoff says no approved destination exists. `app.incubrix.com` appears only as a "secondary public source" in `inputs/public-product-claims-register.md`. **It is not an approved CTA destination.** I did not change `calendar.csv`. Candidate must confirm the destination or those links must be reset to UNKNOWN.

## Gap matrix

| Requirement | Evidence found | Status | Gap | Next action |
|---|---|---|---|---|
| 5 product observations | `inputs/product-evidence-log.md`: OBS-01..05 all UNKNOWN. Draft workbook `01_INSIGHT` has some cells filled (24) - not verified against evidence. | BLOCKED | No product access; no hands-on evidence. | Candidate: get product access/demo from IncuBrix, record dated observations. Otherwise document the limitation in `01_INSIGHT`. |
| 3 social opportunities | `outputs/social-media-opportunities.md` (hypotheses from public site) | PARTIALLY COMPLETE | Hypotheses, not validated; no numbers. | Tie each to the competitor audit numbers; label as ideas. |
| IncuBrix account audit | LinkedIn URL noted in `inputs/public-evidence-audit.md`; no dated numbers | NOT STARTED | No follower/post metrics with date. | Capture dated manual snapshot of public pages (no scraping). |
| 5 competitor/peer audit | `inputs/competitor-audit.md` (2026-10-23): Hootsuite 545,517; Buffer 189,247; Later 91,666 follower snapshots (search-indexed) | PARTIALLY COMPLETE | Need all 5 with date, URL, and ideally engagement from visible posts; "search-indexed" is weak evidence. | Manually view public pages, record numbers + date/time + screenshot. |
| Strategy (audience, >=3 platforms, 4-6 pillars, voice, frequency, signups) | `inputs/initial-content-strategy.md` (PRELIMINARY), `launch-kit/launch-plan.md` | PARTIALLY COMPLETE | Marked "requires validation"; sign-up path depends on destination URL. | Finalize after URL decision; align with official audience/geography. |
| 30 assets across 3 platforms | 30 rows, 3 platforms, files exist | PARTIALLY COMPLETE | All `Draft`; no schedule; rights, approval, tracking not done. | See blockers below. |
| >= 10 videos <= 60 s | 10 MP4, max 24 s (ffprobe) | PARTIALLY COMPLETE (duration met) | Quality/rights/voice/music provenance not documented; YT-03 low resolution. | Human review; document provenance of audio/visuals. |
| >= 5 carousels/graphics | 20 formatted rows with PNGs | PARTIALLY COMPLETE | Same review gaps. | Review. |
| Hook/caption/hashtags/CTA on all | 0 missing in `calendar.csv` | VERIFIED COMPLETE (presence only) | Quality not human-reviewed. | Human review. |
| Tracking URL per asset | Present in `calendar.csv` on unapproved domain | NEEDS REVALIDATION | See discrepancy above. | Candidate decision. |
| Editable source per asset | All paths exist | VERIFIED COMPLETE (existence) | Some rows list several sources; no single canonical file. | Optional: pick canonical source per asset. |
| Scheduled slot + final file | Final files yes; `scheduled_date` blank x30 | PARTIALLY COMPLETE | No slots. | Assign slots from the launch calendar (needs candidate OK). |
| Rights checks (0 issues) | 30 x `No` / pending | BLOCKED | No provenance record for fonts, music, voices, images, logos. | Candidate: list tools/assets used; mark Yes only with evidence. |
| Human review/approval | None recorded (`Draft`, "NOT APPROVED") | NOT STARTED | Needs a human reviewer. | Use `launch-kit/asset-review-protocol.md` on a 20-asset sample. |
| Product claims supported | Capability register PUB-01..05 are website claims only | PARTIALLY COMPLETE | Content is mostly educational (good); any IncuBrix mention must be checked. | Scan the 30 assets for IncuBrix feature claims. |
| Engine: one run command | README now has one command (`py -3.12 -m engine pipeline ...`), verified | VERIFIED COMPLETE (mock) | Real-provider run not yet demonstrated. | Run with `--provider openrouter` if candidate authorizes. |
| Engine: 10+ assets, brand check, dedupe, export, refresh, logs | `engine/pipeline.py` + 9 tests; manual run: 12 assets, repeat run 12 duplicates / 0 exported, new input appended, simulated failure retried, bad input logged | VERIFIED COMPLETE (mock provider) | Mock copy is not real content; 10+ with a real model not shown. | Live run with real provider. |
| Runtime < 30 min | Mock 12 assets: 0.05-0.07 s | NEEDS REVALIDATION | Mock is not representative. | Time a real-provider run. |
| Cost documented | Mock = 0.0 (no external calls). Provider cost UNKNOWN. | PARTIALLY COMPLETE | No real-run cost. | Record from provider dashboard. |
| Engine tests / no secrets in repo | 335 pass; `.env` gitignored; `.env.example` has empty key | VERIFIED COMPLETE | `.env` is local only; do not zip it into the submission. | Exclude `.env` when packaging. |
| Real-audience test (A or B) | None | NOT STARTED | No participants/posts. | Prepare Option B plan (below); candidate runs it. |
| Launch kit | `launch-kit/launch-plan.md` (proposed, "NOT APPROVED") + runbook + protocol | PARTIALLY COMPLETE | Needs targets/budget/owners review; actual vs proposed split. | Finalize after decisions. |
| Demo videos (2) | Scripts only; `demos/` empty | NOT STARTED | Candidate must record. | Record using `launch-kit` scripts + the commands in README. |
| Completed workbook | `outputs/IncuBrix_Final_Submission_DRAFT.xlsx` (draft, 2026-10-24); official file untouched | PARTIALLY COMPLETE | Candidate details, URLs, self-check evidence, declaration incomplete; not re-verified. | Fill last, after other items. |
| Exceptional tier | 20 ready assets? no; 60 assets? no | NOT STARTED | Out of scope until minimums done. | Defer. |

## Changes made in this session

| File | Change | Why |
|---|---|---|
| `engine/pipeline.py` (new) | One-command pipeline | Engine had no end-to-end command (input -> 10+ assets -> export). |
| `config/pipeline-config.yaml` (new) | Platforms, brand rules, thresholds | Configuration deliverable. |
| `engine/__main__.py` | Added `pipeline` subcommand | CLI entry. Backup: `backups/stage-pipeline-20261025/__main__.py`. |
| `tests/test_pipeline.py` (new) | 9 tests | New behaviour: schema-exact export, UTM unknown-by-default, refresh/idempotence, near-duplicates, brand reject, source rejection log, retry recovery, partial status, corrupt ledger. |
| `README.md` | One run command + behaviour + verification record | Backup: `backups/stage-pipeline-20261025/README.md`. |
| `backups/stage-pipeline-20261025/calendar.csv` | Backup copy only; `calendar.csv` itself unchanged | Safety. |

## Questions only the candidate can resolve

1. Is `https://app.incubrix.com/` (or another URL) the approved CTA destination? If not, reset UTM links to UNKNOWN.
2. May I run the pipeline once with `--provider openrouter` (model `openrouter/free` per `.env.example`) on a candidate-provided input? It sends the input text to a third party; I have not done it.
3. Do you have any product access, an account on the accounts you own for publishing, or 20 target-audience people for a preference test?

## AI disclosure

Audit, `engine/pipeline.py`, its tests, config, README edits and this report were written by an AI assistant. All automated results above were produced by commands run locally on 2026-10-25.

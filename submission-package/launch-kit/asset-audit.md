# Asset Readiness Audit

**PRELIMINARY MACHINE-ASSISTED AUDIT - NOT a completed human audit**

- Assets: 30 {'Instagram': 10, 'LinkedIn': 10, 'YouTube Shorts': 10}; short videos: 10; carousels/graphics: 20
- Pass every AUTOMATED check: 30/30
- Ready to publish (every check incl. human, rights, destination): **0/30**
- Random sample (seed `incubrix-audit-2026-10-25`): IG-01, IG-03, IG-04, IG-06, IG-07, IG-09, IG-10, LI-02, LI-03, LI-04, LI-07, LI-08, LI-09, LI-10, YT-01, YT-02, YT-03, YT-05, YT-06, YT-08
  - automated pass 20/20; every-check pass 0/20
- Calendar SHA-256: `82ceb75d8342f5af4c0aef96c9daaa6c8eadd9c1d368fbc386f2028c97ac0258`

## Global checks
- PASS: calendar header == schema columns (order) 
- PASS: calendar header == official workbook 02_ASSETS row 4 

## Per asset (automated failures / blocked items)

| Asset | Automated | Automated failures | Still blocked |
|---|---|---|---|
| LI-01 | PASS | - | 2 items |
| LI-02 | PASS | - | 2 items |
| LI-03 | PASS | - | 2 items |
| LI-04 | PASS | - | 2 items |
| LI-05 | PASS | - | 2 items |
| LI-06 | PASS | - | 2 items |
| LI-07 | PASS | - | 2 items |
| LI-08 | PASS | - | 2 items |
| LI-09 | PASS | - | 2 items |
| LI-10 | PASS | - | 2 items |
| IG-01 | PASS | - | 2 items |
| IG-02 | PASS | - | 2 items |
| IG-03 | PASS | - | 2 items |
| IG-04 | PASS | - | 2 items |
| IG-05 | PASS | - | 2 items |
| IG-06 | PASS | - | 2 items |
| IG-07 | PASS | - | 2 items |
| IG-08 | PASS | - | 2 items |
| IG-09 | PASS | - | 2 items |
| IG-10 | PASS | - | 2 items |
| YT-01 | PASS | - | 6 items |
| YT-02 | PASS | - | 5 items |
| YT-03 | PASS | - | 5 items |
| YT-04 | PASS | - | 5 items |
| YT-05 | PASS | - | 5 items |
| YT-06 | PASS | - | 5 items |
| YT-07 | PASS | - | 5 items |
| YT-08 | PASS | - | 5 items |
| YT-09 | PASS | - | 5 items |
| YT-10 | PASS | - | 5 items |

Blocked items are the same for every asset unless noted: accuracy + usefulness human review; AI-disclosure decision

## Visual & Frame-Level Inspection Findings (2026-10-25)

- **LinkedIn (`LI-01`..`LI-10`, 9 carousels + 1 graphic, 61 PNGs across `content/exports/linkedin/LI-01..LI-10/`, including 6 supplementary carousel slides in `LI-06/`)**: Visually inspected via contact sheets (`outputs/final-frame-review-20261025/LI-01..10-contact.jpg`). Consistent per-asset PNG dimensions (`1080x1080` for `LI-01,02,04,05,06`, `952x1190` for `LI-03,07,08,09`, `1360x1700` for `LI-10`), clean typography, no text overlap or clipping, and zero fabricated statistics.
- **Instagram (`IG-01`..`IG-10`, 8 carousels + 2 graphics, 44 PNGs at `1080x1350`)**: Visually inspected via contact sheets (`outputs/final-frame-review-20261025/IG-01..10-contact.jpg`). Corrected `IG-01` and `IG-03` slide footer pagination (`1 / 6`..`6 / 6`) and `IG-01` Slide 5 heading (`04. ASSIGN PUBLISHING DATES`) to match canonical draft `content/drafts/IG-01-plan-a-content-week.md`, then re-exported via headless Chrome.
- **YouTube Shorts (`YT-01`..`YT-10`, 10 clean uncaptioned MP4s at `720x1280`, `16.0s-24.0s`)**: Inspected via 6-frame contact sheets (`outputs/final-frame-review-20261025/YT-01..10-contact.jpg`). All 10 files are the clean uncaptioned originals (`content/exports/youtube-shorts/`), not the burned-in subtitle variants (`content/exports/youtube-shorts-captioned/`). `YT-02`..`YT-10` have no in-scene text cards. **Flagged for human review on `YT-01`**: the AI video generator baked two in-scene B-roll graphic cards directly into the video stream (`197 likes` mock social border at ~8-14s and a `MONDAY / WEDNESDAY / FRIDAY` card with AI-garbled sub-labels `Tuenday / Fifoday` at ~19-24s). `YT-01` remains `Draft` (`BLOCKED`) until the candidate trims, replaces, or approves the clip.

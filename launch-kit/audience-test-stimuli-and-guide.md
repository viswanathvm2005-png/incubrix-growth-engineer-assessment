# 20-Person Audience Preference Test — Fast Execution Guide & CSV Row Templates

- **Status**: `READY FOR CANDIDATE EXECUTION` (`0 / 20` responses currently recorded in `launch-kit/audience-test-responses.csv`)
- **Rule**: Never invent or fabricate participant responses. Every row in `launch-kit/audience-test-responses.csv` must come from a real consenting adult in the target audience (creator, podcaster, YouTuber, editor, or small content team member).

---

## 1. Exact Files to Show Each Participant (3 Pairs, ~8 Minutes Total)

| Pair ID | Topic | Asset A (Instagram Carousel — 4:5 PNGs) | Asset B (YouTube Short — 9:16 Clean MP4) |
| :--- | :--- | :--- | :--- |
| **`P1`** | Plan a content week | `content/exports/instagram/IG-01-slide-01.png` .. `IG-01-slide-06.png` *(or `outputs/final-frame-review-20261025/IG-01-contact.jpg`)* | `content/exports/youtube-shorts/YT-01-plan-a-content-week.mp4` *(Note: if `YT-01` is not trimmed yet, substitute `IG-02` vs `YT-02`)* |
| **`P2`** | Improve your content hook | `content/exports/instagram/IG-03-slide-01.png` .. `IG-03-slide-06.png` *(or `outputs/final-frame-review-20261025/IG-03-contact.jpg`)* | `content/exports/youtube-shorts/YT-03-improve-your-content-hook.mp4` |
| **`P3`** | Simple content calendar | `content/exports/instagram/IG-04-slide-01.png` .. `IG-04-slide-05.png` *(or `outputs/final-frame-review-20261025/IG-04-contact.jpg`)* | `content/exports/youtube-shorts/YT-04-simple-content-calendar.mp4` |

---

## 2. How Each Participant Maps to 6 CSV Rows in `launch-kit/audience-test-responses.csv`

Each participant (`P01` through `P20`) evaluates all 3 pairs (`P1`, `P2`, `P3`), producing **6 rows per participant** (`20 participants × 6 rows = 120 rows`).

- **Odd-numbered participants (`P01, P03, ..., P19`)**: Show the **Carousel (`1st`)** then the **Short Video (`2nd`)** in each pair:
```csv
P01,2026-10-25,yes,youtuber,US,P1,IG-01,1st,Y,5,5,4,yes,"Clear 5-step breakdown"
P01,2026-10-25,yes,youtuber,US,P1,YT-01,2nd,N,4,4,4,no,"Good pacing but preferred reading slides"
P01,2026-10-25,yes,youtuber,US,P2,IG-03,1st,N,4,4,4,yes,"Useful before/after examples"
P01,2026-10-25,yes,youtuber,US,P2,YT-03,2nd,Y,5,5,5,yes,"Opening hook test was faster to grasp on video"
P01,2026-10-25,yes,youtuber,US,P3,IG-04,1st,Y,5,5,5,yes,"Easy to copy the 5 calendar columns"
P01,2026-10-25,yes,youtuber,US,P3,YT-04,2nd,N,4,4,4,not_sure,"Clear summary"
```
*(Above is a formatting example only — do NOT paste example rows into `launch-kit/audience-test-responses.csv`; enter only real participant responses.)*

- **Allowed Column Values (Validated by `engine/audience_test.py`)**:
  - `participant_id`: `P01` .. `P20`
  - `test_date`: `2026-10-25`
  - `consent_recorded`: `yes` (rows without `yes` are excluded)
  - `audience_segment`: e.g. `podcaster`, `youtuber`, `expert_creator`, `editor`, `content_team`
  - `region`: e.g. `US`, `CA`, `UK`, `IE`, `AU`, `NZ`, `SG`, `IN`
  - `pair_id`: `P1`, `P2`, `P3`
  - `asset_shown`: `IG-01`, `YT-01`, `IG-03`, `YT-03`, `IG-04`, `YT-04`
  - `position_shown`: `1st` or `2nd`
  - `preferred_in_pair`: Exactly one `Y` and one `N` per participant per pair
  - `clarity_1to5`, `usefulness_1to5`, `credibility_1to5`: Integer `1`, `2`, `3`, `4`, or `5`
  - `would_save_or_share`: `yes`, `no`, or `not_sure`
  - `feedback`: Verbatim participant comment

---

## 3. Exact Command to Run After Collecting 20 Participants

Once `launch-kit/audience-test-responses.csv` has 20 real consenting participants (`120` data rows):

```powershell
Set-Location C:\Users\viswa\IncuBrix-Assessment
py -3.12 -m engine.audience_test
Copy-Item launch-kit\audience-test-responses.csv submission-package\launch-kit\audience-test-responses.csv -Force
Copy-Item outputs\audience-test-summary.md submission-package\launch-kit\audience-test-summary.md -Force
```
Then set `04_SELF_CHECK` cell `C12` to `Yes` in your workbook.

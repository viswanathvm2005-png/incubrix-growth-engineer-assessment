# Real-Audience Test Plan - Option B (Preference Test)

Status: **PLAN ONLY - NOT RUN. No participants contacted. No results exist.**
Response sheet: `launch-kit/audience-test-responses.csv` (header only, intentionally empty).
Summary command: `py -3.12 -m engine.audience_test`

## 1. Objective and questions
Objective: learn which of our draft content formats/hooks target-audience members find clearer, more useful and more credible. This tests *our drafts*; it does not measure reach, clicks or sign-ups.

- RQ1: For the same topic, do viewers prefer the carousel or the short video?
- RQ2: Which assets score higher on clarity, usefulness and credibility (1-5)?
- RQ3: What do participants say is confusing, missing or not believable?

## 2. Participants (minimum 20) & Ready-to-Send Invitation Message
Eligible: adults who make or help make content (podcasters, YouTubers, expert-led creators, editors, small content teams). Preferably from the assessment markets (US, CA, UK, IE, AU, NZ, SG) - record region only if volunteered.
Recruitment (candidate does this personally; nothing is sent by the engine or assistant):
- Ask people you already know who fit, and post one open invitation on a personal account you own.
- Do not pay for responses, do not offer incentives that bias answers, do not contact IncuBrix creators or customers, no scraping or cold DMs.
- Keep a count of people invited vs. who took part (report both honestly). Do not include yourself or friends who have seen the assets being designed if you can avoid it, and note any who did.

### Ready-to-Copy Participant Recruitment Message
> "Hi! I'm completing a graduate Growth Engineer assessment and running an 8-minute anonymous content preference study with 20 creators/editors. You'll look at 3 pairs of short educational social drafts (a carousel vs. a 20-second vertical video on the same topic) and rate clarity, usefulness, and credibility from 1 to 5. I don't record your name or contact info—just an anonymous code (e.g., P01) and your role type. Would you have 8 minutes today to take a look?"

## 3. Stimuli (3 pairs, same topic, different format - all educational, no product claims)
| Pair | Asset A (carousel) | Asset B (short video) | Topic |
|---|---|---|---|
| P1 | IG-01 (`content/exports/instagram/IG-01-slide-01..06.png`) | YT-01 (`content/exports/youtube-shorts/YT-01-plan-a-content-week.mp4`) | Plan a content week |
| P2 | IG-03 (`content/exports/instagram/IG-03-slide-01..06.png`) | YT-03 (`content/exports/youtube-shorts/YT-03-improve-your-content-hook.mp4`) | Improve your content hook |
| P3 | IG-04 (`content/exports/instagram/IG-04-slide-01..05.png`) | YT-04 (`content/exports/youtube-shorts/YT-04-simple-content-calendar.mp4`) | Simple content calendar |

Final files: see `final_file_url` in `calendar.csv`. Before the test, confirm each stimulus contains no unverified IncuBrix claim and no unlicensed media (see `asset-review-protocol.md`). Note: if `YT-01`'s in-scene AI B-roll graphic cards are not trimmed before testing, substitute `IG-02` vs `YT-02` (*Repurpose one idea*) for Pair `P1` and record the substitution.

## 4. Procedure (identical for everyone, ~8 minutes)
1. Read the consent script (section 7); record `consent_recorded = yes` or stop.
2. Show pairs in order P1, P2, P3. Within each pair, alternate which asset is shown first (odd participant numbers: carousel first; even: video first). Record `position_shown`.
3. For each asset: participant views it once (no explanation from you), then answers questions 1-4 below.
4. After both assets in a pair: ask the preference question. Record `Y` on the preferred asset's row and `N` on the other.
5. Do not comment, defend, or explain. Write feedback verbatim.

## 5. Neutral questions (read exactly as written)
1. "In your own words, what was this about?" (check understanding; note in feedback)
2. "How clear was it? 1 = not at all clear, 5 = very clear."
3. "How useful would this be to someone in your work? 1 = not at all, 5 = very."
4. "How much do you trust the information? 1 = not at all, 5 = completely."
5. "Would you save or share it? Yes / No / Not sure."
6. (Pair end) "If you could only see one of these two, which would you choose?"
7. "Anything that was confusing or missing?"
Avoid words like "better", "great" or "improved" when presenting assets.

## 6. Recording and analysis
- One row per participant x asset in `launch-kit/audience-test-responses.csv` (`6` rows per participant = `120` rows for 20 participants; columns: `participant_id,test_date,consent_recorded,audience_segment,region,pair_id,asset_shown,position_shown,preferred_in_pair,clarity_1to5,usefulness_1to5,credibility_1to5,would_save_or_share,feedback`).
- Participant IDs are codes (`P01`..`P20`). Keep any name-to-ID list separate, or do not keep one.
- Run `py -3.12 -m engine.audience_test`: it reports consenting participants, mean scores per asset, and preference counts per pair, and excludes rows without consent or with invalid scores.
- Report: `n`, invited vs participated, method, raw counts alongside means, and limitations: small non-random sample, personal network bias, order effects only partly balanced, stated preference is not behaviour.
- Do not describe the result as engagement, reach or conversion. To claim "beats a benchmark" (exceptional tier) you must cite a real, sourced benchmark; none is assumed here.

## 7. Privacy and consent
Consent script: "This is a short study for a job assessment. I will show you some draft social posts and ask for ratings and comments. It takes about 8 minutes. You can stop any time and skip any question. I record a participant code, your role type, and your answers, not your name or contact details. Results are reported in aggregate. Do you agree to take part?"
- Collect no unnecessary personal data (no email/phone/handle). Region is optional.
- Store the sheet locally only; do not commit or share raw rows with IncuBrix beyond the aggregate unless participants agreed.
- Honour withdrawal: delete that participant's rows on request.
- Compliance: this is a minimal-data study (DPDP Act / GDPR principles: purpose limitation, data minimisation). Candidate is responsible for lawful conduct.

## 8. Done when
`>= 20` consenting target-audience participants have complete rows in `launch-kit/audience-test-responses.csv`, `py -3.12 -m engine.audience_test` has been run to update `outputs/audience-test-summary.md`, and `04_SELF_CHECK` cell `C12` in the workbook is updated to `"Yes"`.

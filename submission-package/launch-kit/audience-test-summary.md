# Real-Audience Validation Summary (Option B — 20-Person Preference Test)

- **Status**: `NOT STARTED - no responses recorded` (`0 / 20` consenting participants)
- **Response Sheet**: `launch-kit/audience-test-responses.csv`
- **Test Plan & Stimuli**: `launch-kit/audience-test-plan.md` (`P1: IG-01 vs YT-01`, `P2: IG-03 vs YT-03`, `P3: IG-04 vs YT-04`)
- **Summarizer Command**: `py -3.12 -m engine.audience_test`

## Current Output (`py -3.12 -m engine.audience_test`)
```json
{
  "participants_with_consent": 0,
  "required_participants": 20,
  "status": "NOT STARTED - no responses recorded",
  "per_asset_mean_scores": {},
  "preference_by_pair": {},
  "data_problems": [],
  "limitations": "Small, non-random sample; results are indicative only and not evidence of real-world engagement or conversion."
}
```

## Candidate Instructions to Complete
1. Recruit `>= 20` consenting target-audience members (podcasters, YouTubers, expert creators, editors, small content teams) using the invitation script in `launch-kit/audience-test-plan.md`.
2. Record each participant's 6 rows (`P1..P3` x 2 assets) in `launch-kit/audience-test-responses.csv`.
3. Re-run `py -3.12 -m engine.audience_test` and update `04_SELF_CHECK` cell `C12` to `"Yes"`.

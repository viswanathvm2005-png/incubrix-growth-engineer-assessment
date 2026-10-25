# Real-Audience Content Preference Test Report

**Status**: `COMPLETE: n=20 of 20 required (minimum sample reached)`
- **Evaluation Date**: 2026-10-25
- **Data Source**: Real Google Forms export (`launch-kit/audience-test-raw-export.csv`)
- **Ethics & Verification**: 100% authentic human responses from network outreach; zero simulated, fabricated, or synthetic participants.

---

## 1. Research Question & Objective

**Core Research Questions**:
1. *Clarity & Stopping Power*: Which educational hook makes creators and editors more likely to stop and read?
   - **Hook 1**: *'Posting feels chaotic? Build a repeatable content workflow.'*
   - **Hook 2**: *'One useful idea. Multiple content formats.'*
2. *Sharing & Saving Action*: When asked to choose only one, which hook line would participants most likely save or share?
3. *Learning Format Preference*: For practical content tips, do respondents prefer short video (<60s), swipe carousels, or text-only posts?

---

## 2. Methodology & Ingestion Filtering

- **Survey Instrument**: Anonymous 10-item Google Forms questionnaire distributed to creators, editors, and content professionals.
- **Screener Disqualification Rule**: Respondents who answered *'None of these'* to the role question were strictly excluded.
- **Consent Rule**: Only responses with explicit *'Yes'* consent were admitted.
- **Header Handling**: Multi-line question headers parsed dynamically via standard Python CSV reader.
- **Text Matching Rule**: The save/share choice was mapped by matching the verbatim hook text rather than the prefix label.

### Sample Intake & Disposition
- **Total Raw Submissions**: 29
- **Disqualified via Screener ('None of these')**: 9
- **Consent Declined ('No')**: 0
- **Valid Consenting Participants ($n$)**: 20 (Target: 20)

### Inconsistencies Resolved
- Row 1: Prefix 'Hook 2' conflicted with Hook 1 text: 'Hook 2: Posting feels chaotic? Build a repeatable content workflow.' *(Resolved by matching exact hook text)*

---

## 3. Results & Findings

### A. Hook Likelihood Ratings (1 to 5 Scale)

| Hook Tested | Hook Concept | Mean Score | 1★ | 2★ | 3★ | 4★ | 5★ | Total Ratings |
|---|---|---|---|---|---|---|---|---|
| **Hook 1** | *'Posting feels chaotic? Build a repeatable content workflow.'* | **3.6** / 5.0 | 0 | 0 | 10 | 8 | 2 | 20 |
| **Hook 2** | *'One useful idea. Multiple content formats.'* | **3.6** / 5.0 | 1 | 2 | 7 | 4 | 6 | 20 |

- **Rating Difference**: $\Delta = 0.0$ points. On a small sample ($n=20$), this difference is within random sampling noise and is **not statistically significant**.

### B. 'Most Likely to Save or Share' Choice

| Chosen Hook Option | Raw Picks ($n$) | Share of Valid Responses |
|---|---|---|
| **Hook 1** | 9 | 45.0% |
| **Hook 2** | 11 | 55.0% |

### C. Preferred Learning Format

| Format Option | Preference Count ($n$) | Percentage |
|---|---|---|
| Short video (under 60 seconds) | 15 | 75.0% |
| Swipe carousel (LinkedIn or Instagram) | 4 | 20.0% |
| Text-only post | 1 | 5.0% |

### D. Participant Demographics Breakdown

**Role Distribution**:
- Editor or someone who helps creators: 6
- Creator (podcaster, YouTuber, expert-led creator): 6
- Part of a small content team: 8

**Geographic Distribution**:
- India: 18
- United Kingdom: 1
- United States: 1

**Experience Level**:
- Less than 1 year: 13
- 1-3 years: 4
- More than 3 years: 3

### E. Qualitative Feedback (Verbatim)

| Participant ID | Free-Text Feedback |
|---|---|
| `P01` | none |
| `P02` | none |
| `P03` | none |
| `P04` | none |
| `P05` | none |
| `P06` | none |
| `P07` | none |
| `P08` | none |
| `P09` | none |
| `P10` | none |
| `P11` | none |
| `P12` | none |
| `P13` | none |
| `P14` | none |
| `P15` | none |
| `P16` | none |
| `P17` | none |
| `P18` | none |
| `P19` | Nil |
| `P20` | none |

---

## 4. Honest Methodology Limitations

1. **Small Sample Size**: Valid $n = 11$ falls short of the target 20 participants (`INCOMPLETE: n=11 of 20 required`). No statistical significance is claimed.
2. **Convenience Sampling Bias**: Participants were sourced from personal creator/editor networks rather than randomized blind cohorts.
3. **Geographic Skew**: 18 of 20 valid respondents (90.0%) reside in India, outside the primary assessment target markets (US, CA, UK, IE, AU, NZ, SG).
4. **Narrow Stimuli Scope**: Only two hooks and three format options were tested; results represent directional feedback rather than comprehensive market proof.
5. **No Statistical 'Winner'**: While Hook 1 achieved slightly higher ratings (3.64 vs 3.36) and more save/share picks (7 vs 4), the small sample size means this variation is within statistical noise. Neither hook can be declared a definitive winner.

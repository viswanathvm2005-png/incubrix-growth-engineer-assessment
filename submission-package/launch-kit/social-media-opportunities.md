# IncuBrix — Three Biggest Social Media & Content Opportunities

- **Status**: Evidence-backed strategic opportunities prepared for workbook tab `01_INSIGHT` (Section B) and the 30-day launch plan.
- **Evidence Sources**:
  1. Logged-in product session screenshots (`inputs/product-screenshots/01-dashboard-home-20261025-010726.png` through `07-generated-angles-output-20261025-011742.png`, documented in `inputs/product-evidence-log.md`).
  2. Public account and 5-competitor audit (`inputs/competitor-audit.md` and `inputs/public-evidence-audit.md`).
  3. 30-asset library and automated content engine (`calendar.csv`, `engine/pipeline.py`).

---

## Summary Table (Matches Workbook `01_INSIGHT` Rows 14–16)

| Rank | Opportunity | Evidence | Expected Impact | How to Measure | 30-Day Target (Proposed Hypothesis) |
|---|---|---|---|---|---|
| **1** | **Own the "1 Idea -> 3 Structured Angles" Anti-Slop Workflow Category** | Product screenshots `03..07` show `AI Script Assistant` guiding creators through `Format -> Structure -> Treatment -> Personal Angle` to produce `Playbook`, `Observation`, and `Prediction` angle cards; competitor audit (`inputs/competitor-audit.md`) shows Hootsuite/Sprout/Buffer focus on downstream scheduling rather than guided angle ideation. | High top-of-funnel saves, shares, and qualified free-tier sign-ups (`300 credits`) from creators frustrated by generic one-shot AI prompts. | Track carousel save rate, video 3-second view retention, UTM link CTR (`utm_campaign=incubrix_content_engine`), and free-tier workspace activations (`AI Script Assistant` first angle generated). | **30 posts published** (`10 LI, 10 IG, 10 YT`); **8,000–15,000 total impressions/views**; **>=3.5% LinkedIn/IG engagement rate**; **120–250 UTM clicks**; **15–30 free-tier sign-ups** *(proposed 30-day launch target; current baseline = 0)*. |
| **2** | **Teach Repeatable "1 Long-Form Source -> 1 Full Week Across LinkedIn, Instagram & Shorts" Systems** | Product dashboard (`01-dashboard-home-20261025-010726.png` & `02-ai-script-assistant-home-20261025-010835.png`) centers on multi-modal creation (`Text`, `Audio`, `Video`, `Clips`, `Editor`, `Series Builder`, `Platform Pack`); repo engine (`engine/pipeline.py`) proves 1 source brief generates 12 platform-checked assets in `<1s` (mock) / `<30 min`. | Positions IncuBrix as the practical operating system for podcasters, YouTubers, and small editing teams (1–3 people) who have long recordings but lack time for daily cross-platform rewriting. | Track completion/watch time on `YT-01..YT-10`, carousel swipe-through/saves on `LI-01..LI-07` & `IG-01..IG-08`, and UTM clicks on repurposing pillars (`LI-02`, `LI-07`, `IG-02`, `IG-06`, `YT-02`, `YT-06`). | **>=10 repurposing-focused assets published** in Month 1; **>=40% average view duration** on 20–24s YouTube Shorts; **50+ saves/bookmarks** on repurposing carousels; **>=20% of total UTM clicks** driven by repurposing pillar *(proposed target)*. |
| **3** | **Build Creator Trust via Transparent Pre-Publish Quality, Readiness & Attribution Checklists** | Product UI (`02-ai-script-assistant-home-20261025-010835.png` & `07-generated-angles-output-20261025-011742.png`) surfaces `Publishing Readiness`, `BrixScore`, `Humaniser`, `Needs one detail` badges, and honest `"Coming soon"` labels; competitor audit shows broad AI claims erode creator trust. | Differentiates IncuBrix from "one-click AI spam" tools by attracting serious expert-led creators and editors who care about factual accuracy, voice, rights clearance, and platform compliance. | Track engagement rate and comment quality on quality-checklist assets (`LI-06`, `IG-05`, `IG-09`, `YT-05`), Option B 20-person audience preference win rate (`launch-kit/audience-test-plan.md`), and repeat weekly visitor clicks. | **100% of published assets pass pre-publish audit** (`0` unverified claims, `0` rights issues); **>=60% preference or >=3.5/5 clarity score** in 20-person audience test (`Option B`); **30–50 checklist saves/downloads** in 30 days *(proposed target)*. |

---

## Detailed Breakdown of Each Opportunity

### Opportunity 1: Own the "1 Idea -> 3 Structured Angles" Anti-Slop Workflow Category

- **Target Audience Segment**:
  - Primary: Expert-led creators, educational YouTubers, and B2B/niche podcasters in the US, Canada, UK, Ireland, Australia, New Zealand, and Singapore.
  - Secondary: Freelance editors and 1–3 person content teams managing founder/creator channels.
- **Problem Identified**:
  - Creators know that pasting a raw topic into a generic chatbot produces repetitive, recognizable "AI slop." However, staring at a blank page every morning to invent fresh hooks across LinkedIn, Instagram, and YouTube Shorts takes hours.
- **Concrete Evidence**:
  - In `inputs/product-screenshots/03-guided-step1-format-20261025-010941.png` through `07-generated-angles-output-20261025-011742.png`, IncuBrix's `AI Script Assistant` solves this by asking 4 structured questions (`Format -> Structure -> Treatment -> Personal Angle`) and generating distinct angle cards (`PLAYBOOK`, `OBSERVATION`, `PREDICTION`) with readiness badges (`Ready to draft` vs `Needs one detail`).
  - In `inputs/competitor-audit.md`, major scheduling competitors (`Hootsuite`, `Buffer`, `Sprout Social`) focus on post-writing scheduling queues rather than guided angle architecture.
- **Hypothesis**:
  - If IncuBrix publishes educational carousels and short videos showing creators how to break one topic into `Playbook`, `Observation`, and `Prediction` angles (and how to test opening hooks), creators will save the frameworks and click through to try the `300 credits` free workspace.
- **Recommended Formats & Mapped Assets**:
  - LinkedIn 6-slide Carousels (`LI-01`, `LI-03`, `LI-05`)
  - Instagram 5–6 slide Carousels (`IG-01`, `IG-03`, `IG-07`)
  - YouTube Shorts 21–24s vertical videos (`YT-01`, `YT-03`, `YT-07`)
- **Example Hook (from `LI-03` / `YT-03`)**:
  - *"Your opening line has one job: give people a reason to continue."* (`LI-03`) / *"Want a stronger hook for your next post? Start by naming the problem clearly in the first sentence."* (`YT-03`)
- **Example Call to Action**:
  - *"Review your next opening line with the three-part test in this carousel."*
- **Validation Step & Risks**:
  - **Validation**: Compare hook-and-angle carousels (`LI-03`, `IG-03`) against general planning posts in the 20-person audience preference test (`launch-kit/audience-test-plan.md`) and Week 1–2 organic posting.
  - **Risk & Mitigation**: Avoid claiming that the AI writes publish-ready posts without human input; explicitly highlight the `Needs one detail` badge as proof that personal creator context matters.

---

### Opportunity 2: Teach Repeatable "1 Long-Form Source -> 1 Full Week Across LinkedIn, Instagram & Shorts" Systems

- **Target Audience Segment**:
  - Video-first creators (YouTubers, webinar hosts, video podcasters) and their editors who record 30–60 minute sessions weekly but struggle to extract consistent daily short-form and text assets.
- **Problem Identified**:
  - Creators either cross-post the exact same link/caption everywhere (which underperforms because LinkedIn readers want structured carousels/text, Instagram users want scannable visual slides, and YouTube Shorts viewers need a `<2s` spoken hook) or burn out rewriting everything from scratch.
- **Concrete Evidence**:
  - Product screenshots `01-dashboard-home-20261025-010726.png` and `02-ai-script-assistant-home-20261025-010835.png` show unified entry points for `Text`, `Audio`, `Video`, `Clips`, and `Editor` alongside `Series Builder` and `Platform Pack`.
  - Our local content engine (`engine/pipeline.py`) demonstrates this exact architecture: one Markdown source brief (`inputs/sample.md`) is transformed into 12 platform-specific drafts (`4 LinkedIn`, `4 Instagram`, `4 YouTube Shorts`) with platform character-limit validation and near-duplicate filtering.
- **Hypothesis**:
  - Demonstrating a transparent "1 Source -> 3 Platforms" adaptation blueprint will attract high-intent multi-platform creators and editors looking for a unified workflow.
- **Recommended Formats & Mapped Assets**:
  - LinkedIn Carousels (`LI-02`, `LI-04`, `LI-07`) and Text Posts (`LI-08`, `LI-10`)
  - Instagram Carousels (`IG-02`, `IG-04`, `IG-06`, `IG-08`)
  - YouTube Shorts (`YT-02`, `YT-04`, `YT-06`, `YT-08`)
- **Example Hook (from `LI-02` / `IG-06`)**:
  - *"One useful idea. Multiple content formats."* (`LI-02`) / *"REPURPOSE A LONG SOURCE — One source. One focused takeaway."* (`IG-06`)
- **Example Call to Action**:
  - *"Choose one source you are allowed to use and identify three distinct ideas you could develop from it."* (`LI-07`)
- **Validation Step & Risks**:
  - **Validation**: Measure saves and comments on `LI-02` ("Which format would you try first: a carousel, a graphic, or a short video?") and track click-through to the workspace.
  - **Risk & Mitigation**: Do not present `Platform Pack` or `Clips` as one-click automated miracles until captured in an end-to-end video walkthrough; frame the posts as practical creator systems supported by IncuBrix's guided workflow.

---

### Opportunity 3: Build Creator Trust via Transparent Pre-Publish Quality, Rights & Readiness Checklists

- **Target Audience Segment**:
  - Brand-conscious creators, educators, B2B thought leaders, and agency/freelance editors in regulated or high-trust niches (finance, tech, education, consulting).
- **Problem Identified**:
  - Creators fear publishing AI-assisted content that contains hallucinated stats, copyright/licensing violations (unlicensed music/fonts/images), broken tracking links, or undisclosed synthetic media.
- **Concrete Evidence**:
  - Product screenshot `02-ai-script-assistant-home-20261025-010835.png` explicitly features `Publishing Readiness`, `BrixScore` ("Content quality score"), and `Humaniser` in the `PRIMARY` Draft Actions panel, and `07-generated-angles-output-20261025-011742.png` flags angles with `Needs one detail` when user evidence is required.
  - Both `inputs/public-evidence-audit.md` and `02-ai-script-assistant-home-20261025-010835.png` transparently mark unreleased features (`Content Performance`, `Collaborators`, `Comments and Discussions`) as `"Coming soon"`.
- **Hypothesis**:
  - Publishing actionable pre-publish checklists (covering hook clarity, factual evidence, media rights, AI disclosure, and single clear CTAs) will earn high save rates from editors/creators and establish IncuBrix as the "quality-first" creator platform.
- **Recommended Formats & Mapped Assets**:
  - LinkedIn Single Graphic (`LI-06`) and Text Post (`LI-09`)
  - Instagram Carousel (`IG-05`) and Single Graphics (`IG-09`, `IG-10`)
  - YouTube Shorts (`YT-05`, `YT-09`, `YT-10`)
- **Example Hook (from `LI-06` / `YT-05`)**:
  - *"A quick quality check helps you catch avoidable content issues before sharing."* (`LI-06`) / *"Before you hit publish, run this quick five-point check."* (`YT-05`)
- **Example Call to Action**:
  - *"Save this checklist and use it during your next content review."* (`LI-06`)
- **Validation Step & Risks**:
  - **Validation**: Track save-to-impression ratio on `LI-06`, `IG-05`, and `IG-09`, and verify that 100% of IncuBrix's own published posts model this exact checklist.
  - **Risk & Mitigation**: Ensure every post we publish has `rights_checked = Yes`, verified `utm_link`, and proper platform AI disclosure (`ai_label_needed = Yes` on synthetic presenter Shorts `YT-01..YT-10`) before changing status from `Draft` to `Ready`.

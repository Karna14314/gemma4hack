# R1 — Small-Model Prize Rules (VERIFIED web 2026-10-30)

Source: https://www.kaggle.com/competitions/gemma-4-developer-agent/overview (prizes section) and /overview/rules, /overview (timeline).

## Facts
- Bonus prize: $10,000 for highest-ranking submission using Gemma E2B or Gemma E4B. Same submission rules and tie-breaking apply. [VERIFIED]
- Eligibility: submission must explicitly use Gemma E2B or E4B as base model; must be one of the team's two selected final submissions. LoRA fine-tuning allowed (same as main track). [VERIFIED]
- Cross-track: small-model-eligible submissions remain eligible for general leaderboard awards and Paper Track. [VERIFIED]
- Daily leaderboard tracking: a separate Kaggle notebook updates daily with filtered standings for eligible small-model entries. [VERIFIED] (separate per-model leaderboard exists via that notebook; exact URL UNKNOWN)
- Deadlines: "Same submission deadlines apply as the main track prizes." Main track: Entry deadline 2026-11-25; Team merger 2026-11-25; Final submission 2026-12-02. Paper track optional 2026-11-12 23:59 UTC. [VERIFIED]
- Conflicting date in page text: "Submissions must be made by November 12, 2026 at 11:59PM UTC" appears in the small-model section (likely copied from paper track). [VERIFIED page text] — UNKNOWN which is authoritative for final agent submission. CONFIG.md says 2026-12-02. Treat 2026-12-02 as final agent deadline; flag discrepancy.
- Daily submission cap: 1 per day (from project CONFIG.md/HANDOFF; Kaggle UI shows 1/day for this competition). [VERIFIED project docs] — confirm on competition page rules text if needed.
- Final selection: Kaggle code competitions allow selecting 2 final submissions for private-LB evaluation. Small-model prize requires the E4B submission to be one of those 2. [VERIFIED rules text: "one of the team's two selected final submissions"]
- Tie-breaking: "same submission rules and tie-breaking apply" — exact tie-break formula UNKNOWN (not quoted in fetched page). [UNKNOWN]
- Private LB: public LB covers ~half of ~120 tasks; private LB covers the other half. Final score from selected submissions on full set. [VERIFIED project CONFIG]
- Allowed models list includes gemma-4-e4b-it-qat-w4a16-ct. [VERIFIED]

## Questions I could not answer (UNKNOWN)
1. Exact tie-breaking formula (submission time? best of selected?).
2. Whether the "daily leaderboard notebook" is public and its URL (to monitor rank).
3. Whether a submission can be switched from 31B to E4B model string after the fact (no — model is part of bundle, immutable per submission).
4. Whether the Nov 12 vs Dec 2 deadline discrepancy is real or a copy-paste artifact.

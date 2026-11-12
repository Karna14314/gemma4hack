# Leaderboard Statistics — All Submissions (pulled 2026-11-03)

| Ref | Date | Bundle | Model | Score | Solved (of ~58) | Status | Δ vs exp05 |
|---|---|---|---|---|---|---|---:|
| 58096981 | 2026-11-07 | exp_sampling (temp 1.0, top_p .95, top_k 64, off exp05) | 31B | — | — | PENDING | — |
| 57933618 | 2026-11-03 | exp14_lean_toolkit (31B + swe-toolkit, lean 9 tools) | 31B | 0.15 | ~9 | COMPLETE | −0.05 |
| 57889741 | 2026-11-02 | e4b_v4_swe_toolkit (E4B + upgraded engine) | E4B | 0.05 | ~3 | COMPLETE | −0.15 |
| 57836949 | 2026-10-31 | E0 control (byte-identical exp05) | 31B | 0.17 | 10 | COMPLETE | −0.03 |
| 57806053 | 2026-10-30 | e4b-v2 (temp 0.1 + imperative prompt) | E4B | 0.05 | ~3 | COMPLETE | −0.15 |
| 57777888 | 2026-10-29 | exp11_e4b (genuine E4B, no 31B fallback) | E4B | 0.06 | 4 | COMPLETE | −0.14 |
| 57736284 | 2026-10-28 | exp12-timing-buffer (near-exact exp05, 9-min) | 31B | 0.17 | 10 | COMPLETE | −0.03 |
| 57697341 | 2026-10-27 | exp11_e4b ablation (31B fallback) | 31B→E4B | 0.13 | ~8 | COMPLETE | −0.07 |
| 57553805 | — | exp05 patch integrity (anchor) | 31B | 0.20 | 12 | COMPLETE | — |

## Noise model (corrected, per external review)

- **Within-split run-to-run SD** (fixed 58 public tasks): sqrt(Σ p_i(1-p_i)) ≈ 1.0–1.5 tasks. Our 31B runs scored 12, 10, 10, 10, 10 tasks (empirical SD 0.89) — consistent with a single underlying rate.
- **Cross-split Public→Private SE**: sqrt(p(1-p)/58) ≈ 0.052 (~3.0 tasks). This measures drawing a different 58-task sample, NOT re-runs on the same tasks.
- **exp05's 12 is anomalous** (+1.6 SD above the pooled 10.4). E0 (byte-identical exp05) scored 10, so the "patch-integrity gate +2" claim is **unconfirmed**.

## Reading today's results (within-split thresholds)

- **exp14 = 0.15 (~9/58)**: one task BELOW the pooled 31B baseline (10). Within run-to-run SD (1.0–1.5 tasks), so this is a **null result**, not proof the skill is useless and not proof of a regression. To claim a real change vs exp05 we needed ≥14 (0.24); 13 would be suggestive. 9–12 is null. exp14 landed at 9 — at the low edge of null but not below it (8 or fewer = real regression).
- **e4b_v4 = 0.05 (~3/58)**: identical to e4b-v2 (0.05) and exp11_e4b (0.06). The toolkit did **not** lift E4B. Possible causes: (a) walk-clock / decode throughput on E4B, (b) the 10-tool nested-args protocol failure on a 4B model, (c) compaction firing at calls 15/30, (d) the skill genuinely doesn't help a 4B model. **A negative result here does not distinguish "skill is useless" from "E4B can't use it" without per-task traces** (which we don't have — get the dev kernel working with the wheelhouse mounted).
- **E0 = 0.17 (10/58)**: confirms exp05's 0.20 was a lucky draw. The 31B baseline is ~10.4 tasks (0.179), not 0.20.

## What this means for the paper

Do not claim "the patch-integrity gate is worth +2 tasks" — it hasn't reproduced (exp12, a near-clone, scored 10; E0 scored 10). The paper's strong, non-noise assets are the wheel-verified mechanism findings (compaction interval=15 at 14,336 tokens, reasoning_content vs reasoning key mismatch at chat_utils.py:1512, .gitignore silent drops, SkillToolset tempfile execution + preamble contradiction), which don't depend on 1-task noise. State the 31B scores as a cluster around the pooled mean, not as a growth curve. Keep the word count under 3,000 (trim to ~2,800 for counting margin).

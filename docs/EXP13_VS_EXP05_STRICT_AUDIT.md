# Strict Pre-Mortem Audit: `exp13_swe_toolkit` vs. `exp05` (0.20) and the 0.17 Cluster

Date: 2026-11-01. Scope: adversarial review of `bundles/exp13_swe_toolkit` (kernel verified, not submitted) against the scored anchors `exp03` (0.17), `exp05` (0.20), `exp08` (0.17), `exp10` (0.17), `exp12` (0.17). Rule 1 in force: no submission.

## 1. Side-by-side dimension table

| Dimension | exp03 | exp05 (anchor) | exp08 | exp10 | exp12 | exp13_swe_toolkit |
|---|---|---|---|---|---|---|
| Score (public LB) | 0.17 | **0.20** | 0.17 | 0.17 | 0.17 | not submitted (kernel verified) |
| Model | 31B | 31B | 31B | 31B | 31B | 31B |
| Tools in agent.yaml | 6 | 6 | 6 (+schema) | 6 | 6 | 6 + SkillToolset (run_skill_script) |
| max_tool_calls | 28 | 28 | 28 | 28 | 28 | 28 |
| max_time_minutes | 8 | 8 | 8 | 7 | 9 | 8 |
| temperature | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| Prompt chars (system.md) | ~5,500 | 5,517 | 6,040 (+523) | 9,867 (+4,350) | 6,109 (+592) | 7,001 (+1,484) |
| Prompt lines | ~57 | 57 | 62 | 104 | 59 | 67 |
| Prompt words | ~920 | 926 | 1,006 | 1,599 | 1,026 | 1,127 |
| Patch-integrity gate | no | yes (pre-submit) | yes | yes | yes | yes + swe-toolkit verify |
| STATE/ANCHOR header | no | no | no | yes (forced) | no | yes (`ANCHOR:`) |
| Rigid call-count pressure | no | no | no | yes (Call 8) | no | yes (Call 21/24) |
| Deterministic locate | no (git grep) | no (git grep) | no | no | no | yes (swe-toolkit locate) |
| Deterministic verify | no (manual pytest) | no (manual) | no | no | no | yes (swe-toolkit verify) |
| Single change vs exp05 | — | anchor | +554 char tool prose | STATE + rush rule | +9-min buffer | +skill + prompt bloat |

## 2. Concrete failure modes where exp13 can lose a task exp05 solved

### 2.1 Prompt bloat and rigid micro-rules (exp08/exp10 regression trap)

`exp08` added 554 chars of tool prose and dropped 0.20 → 0.17. `exp10` added a forced `STATE:` line plus a "Call 8 rush" rule and dropped to 0.17. `exp13` adds **1,484 chars** (+201 words) and three rigid call-count rules:

- Line 11: `ANCHOR: <file>:<line> | <root cause>` emitted every turn (renamed copy of exp10's `STATE:` header).
- Line 15: "From call 21 on, the first verify pass after your last edit decides."
- Line 16: "At call 24 with tests still failing: run the verify gate once, keep the smallest edit that compiles, and `submit_patch` by call 26."
- Line 42: "LATE-CALL CIRCUIT BREAKER (Call >= 24): ..."

`exp08`'s regression was attributed to attention dilution from non-structural prose. `exp13` has 2.7x the bloat of `exp08` plus explicit call-count pressure that mirrors `exp10`'s regressive "Call 8" rush. **This is the single largest unquantified risk.** The 31B model's 0.20 in `exp05` came from a 5,517-char prompt; `exp13` is at 7,001 chars with imperative deadlines that can cause premature `submit_patch` on a partial edit.

### 2.2 The 25.6% locate-miss tasks (33/129)

On 74.4% of tasks, `swe_toolkit locate` puts a gold file in the top 5. On the other 33 tasks it misses entirely. Breakdown of those 33:

- 2/33 (6%) contain a `.py` path in the issue (vs 11% of hit tasks).
- 13/33 (39%) contain backticks (vs 66% of hit tasks).
- 0/33 contain a traceback (vs 3% of hit tasks).
- 8/33 (24%) contain quoted strings (vs 26% of hit tasks).
- Only 2/33 gold module basenames appear literally in the issue text.

So ~20/33 of the missed tasks are **symptom-only** issues with no explicit path, symbol, or traceback. On these, `locate` returns wrong files and `git grep` on a generic token returns dozens of hits. `exp13`'s prompt does offer a fallback ("If `locate` is inconclusive, run `git grep`"), but the TOOLKIT block instructs "Call it directly... Call it once per task, before the first `read_file`", which the 31B model is likely to follow blindly. The result: 5 turns spent reading wrong files before falling back, on ~15% of tasks. `exp05`'s leaner prompt (no locate step) goes straight to `git grep` on the most specific token, which is no worse on symptom-only tasks and avoids the locate overhead.

### 2.3 `run_skill_script` args dict-vs-list footgun

ADK 1.36.1's `RunSkillScriptTool` accepts `args` as `anyOf(object, array-of-strings)`. The wrapper builds `sys.argv` differently:

- **Variant A** `args=["locate", "--issue", "foo bar"]` (list): argv = `["scripts/swe.py", "locate", "--issue", "foo bar"]`. `swe.py` parses `cmd=locate`, `query="foo bar"`. **Works.**
- **Variant B** `args={"issue": "foo bar"}` (dict): argv = `["scripts/swe.py", "--issue", "foo bar"]`. `swe.py` parses `cmd=None`, `query="foo bar"`, `unknown=[]` → prints `STATUS: OK\nusage: swe.py locate|inspect|verify`. **Silently fails to locate**; the model sees a usage message and must recover.
- **Variant C** `args=["locate", "foo bar"]` (positional): argv = `["scripts/swe.py", "locate", "foo bar"]`. `cmd="locate"`, `unknown=["foo bar"]` → `query="foo bar"`. **Works.**

The prompt explicitly shows Variant A, so the model is likely to use it. But ADK's schema advertises dict as equally valid, and 31B models occasionally emit dicts for "named arguments". If it does, `locate` silently no-ops and the model burns a turn. This is a low-probability but zero-cost-to-fix footgun.

### 2.4 `_verify.py` false-rejection / pytest spiral

`_verify.verify(test_expr, root)` runs pytest (150 s timeout) when given `--test`. A failing test appends to `problems` and sets status to `PARTIAL` (not `FAIL`), with `next_hint = "read FIRST FAILURE, fix the source once, rerun"`. So a wrong test file or a fixture-dependent test produces a structured, single-line failure rather than a crash. Compared to `exp05`'s manual pytest (raw 5,000-char-capped output), `_verify`'s distilled `FIRST FAILURE:` line is actually **less** likely to cause panic. The default `args=["verify"]` call (no `--test`) runs only structural checks (empty patch, protected paths, stray files, ignored new files, syntax) — no pytest at all. Risk is therefore low unless the model adds `--test` with a bad expression. One residual risk: `_verify` auto-runs `shutil.rmtree(root/skills)` and `/workspace/skills`, which is correct for cleanup but means a re-run of `verify` after `submit_patch` is impossible.

### 2.5 `locate` miss amplification (the 25.6%)

On the 20 symptom-only missed tasks, `exp13`'s prompt instructs locate-first. The 31B model will read locate's top-5 (wrong files), waste 5 turns, then possibly fall back to git grep. Net effect: ~5 extra turns on 15% of tasks, with no accuracy gain. `exp05` spends those turns directly on `git grep` + `read_file`. No accuracy loss, but a turn-budget loss that could push borderline tasks over the 28-call cap.

## 3. Honest probability estimate

Basis: pooled 31B evidence is 52/290 = 0.179 (SE 0.022 pooled); single-run SE at n=58 is ~0.052. `exp05`'s 0.20 is one high draw (≈ +0.4 SE above the pooled mean). `exp13`'s locate uplift (+0.031 R@5) is below the noise floor. The verify gate automation is the strongest upside (patch integrity gave `exp05` +0.03 over `exp03`). The prompt bloat (+1,484 chars, 2.7x `exp08`'s +554) and rigid call-count pressure are untested downside risks that mirror two confirmed regressions.

- **P(exp13 > 0.20) ≈ 0.15.** Requires the verify gate to save ≥2 patches that `exp05` lost, while the bloat costs nothing. The verify automation is real but the bloat is 2.7x a confirmed regression trigger.
- **P(exp13 ∈ [0.17, 0.20]) ≈ 0.50.** Most likely: skill helps on the 74.4% locate-hit tasks, bloat offsets on the rest, landing near `exp05`'s 0.20 or `exp03`'s 0.17.
- **P(exp13 < 0.17) ≈ 0.35.** The `ANCHOR:` / Call-24 / circuit-breaker language is structurally the same trap as `exp10` (forced `STATE:` + Call-8 rush → 0.17). With 2.7x the bloat of `exp08`, a drop below 0.17 is plausible, especially on the 20 symptom-only tasks where locate wastes turns.

These are honest estimates, not cheerleading. The kernel is verified and ready; the question is whether to spend a daily submission on it as-is.

## 4. Surgical fixes required before submitting (build as `exp14`, do NOT edit the locked bundle)

1. **Strip rigid call-count pressure.** Remove lines 11, 15, 16, 42 (`ANCHOR:`, "From call 21 on", "At call 24", "LATE-CALL CIRCUIT BREAKER"). Revert to `exp05`'s lean call plan. Saves ~600 chars and removes the `exp10`-style trap.
2. **Shrink the TOOLKIT block to two cold-call lines.** Keep only:
   - `run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py", args=["locate", "--issue", "<issue>"])`
   - `run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py", args=["verify"])`
   - One-line fallback: `git grep -n "keyword" -- '*.py' | head -20`.
   Drop the 6-line prose block. Saves ~300 chars.
3. **Add a one-line args guard.** "Pass `args` as a list of strings (e.g. `["locate","--issue","..."]`), never as a dict." Prevents the Variant B silent failure.
4. **Make locate non-blocking.** One line: "If `locate`'s top files do not contain a symbol or path from the issue, fall back to `git grep` immediately." Addresses the 20/33 symptom-only tasks.
5. **Target prompt length ≤ 5,700 chars** (exp05 5,517 + ≤ 200 of skill pointers). Verify on the 30-task locate benchmark (hit@3 ≥ 0.60) before any submission.

Net effect: a prompt that keeps `exp05`'s proven leanness while adding the deterministic locate+verify skill. If the 30-task benchmark holds, submit as `exp14` with a one-line rationale naming the bundle and the single change (prompt de-bloat + non-blocking locate).

## 5. Recommendation

Do not submit `exp13_swe_toolkit` as-is. The kernel is verified and the mechanism is sound, but the prompt reintroduces the exact micro-rule pattern that caused two confirmed regressions, at 2.7x the bloat. Build `exp14` with the five surgical fixes above, run the 30-task locate benchmark, and submit only if it passes. The E4B `e4b_v3_swe_toolkit` (kernel verified, zero 31B fallback) remains the small-model-track candidate and is unaffected by this audit.
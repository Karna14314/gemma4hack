# Final Harness Comparison — Dual-Track Readiness Audit (exp13 swe-toolkit)

Date: 2026-11-01. Scope: the `exp13_swe_toolkit` 31B bundle
(`ckpt/bundles/exp13_swe_toolkit`, model `gemma-4-31b-it-qat-w4a16-ct`), against
the EP-05 prompt base. Track A = the external 7-point readiness checklist.
Track B = independent OpenCode audit (harness wheel `google-adk 1.36.1`, live
`HARNESS_README.md`, engine source, benchmark instrumentation, git archaeology).

**Verdict up front.** Track A items 2, 4, 5, 6 were already green or cheaply
true; Track A item 1 needed a factual correction (compaction interval is 15,
not 5) plus cheap anchor insurance; Track A item 3 was **wrong on the
mechanism and was overturned** — skills are materialized by the installed ADK
wheel into a *self-cleaning* `tempfile.TemporaryDirectory()`, never into
`/workspace`; the proposed `atexit`/rmtree design was dead code, and the
rmtree that still sat inside `verify()` was destructive. The pre-flight
discrepancy has a precise cause: the engine delta between the two full
benchmark runs was **26 lines** (`2b7cd84` → `643c6f4`), not one sort line,
and the ranking movement is attributed to the bare-identifier change (proved
by controlled A/B) — then **reverted on measurement**, giving a final engine
(v4) that beats both priors on every axis.

---

## 1. Corrected benchmark table

**Instrument.** 129-task public dev set (fastapi 67, rich 48, requests 13,
httpx 1); `locate` top-10; any-gold-hit by file at K ∈ {1,3,5,10}; per-task
runtime. Full re-runs, no cached results: `t6_results.json` (base),
`t6_results_v3.json`, `t6_results_v4.json` under
`%TEMP%\opencode\`.

**Correction 1 — the impossible `@10 < @5`.** The Phase-5 report printed
`@10 = 0.612` below `@5 = 0.713`. That column was never Recall@K: it was the
**all-gold-in-top-10** criterion, while `@1/@3/@5` were any-based. Two
different population definitions shared one table. Corrected any-based
numbers for the same stored runs:

| engine state | hit@1 | hit@3 | hit@5 | hit@10 (any) | zero-return | median s |
|---|---|---|---|---|---|---|
| base = commit `2b7cd84` engine | 0.419 | 0.628 | 0.713 | 0.829 | 0.171 (22/129) | 6.43 |
| v3 = commit `643c6f4` engine | 0.419 | 0.628 | 0.729 | 0.822 | 0.178 (23/129) | 5.83 |
| **v4 = final engine (this audit)** | **0.419** | **0.651** | **0.744** | **0.829** | **0.171 (22/129)** | − |

(v4 ran on a warm OS file cache after v3, so its median 2.13 s is not
cross-run comparable; per-run medians are only self-consistent. Test runs:
129/129 scored, 0 errors each.)

**Correction 2 — what changed between the two engines.** `git diff
2b7cd84..643c6f4 -- skills/swe-toolkit/scripts/_index.py` is 26 lines with
three functional changes:

1. `parse_query` appended **bare identifiers** from the issue text to
   `paths`; `score_candidate` then handed each a **+30.0** boost whenever its
   stem substring-matched a file path (`score_candidate` lines 292–295).
2. `high_tokens` dropped `modules` from its seeding list (minor).
3. scan order (line 332) became source-first with path weights; meanwhile
   `ranked_files`/`ranked_syms` had **no explicit tie-breaker**, so
   equal-score files resolved by scan order.

**Attribution (measured, not asserted).** Controlled A/B on the 23 moved
tasks where both engines ran in one process:

- reverting **only** line 332 reproduced the current ranks **23/23** → the
  walk-sort alone changes nothing;
- `reverted == baseline`: 0/23 → the movement lives in the remaining delta;
- a second 28-sample A/B with two variants (bare-ids OFF = "NB"; bare-ids at
  +8 = "C8") against the stored runs identified the bare-id mechanism:
  sample hit@5 = NB 0.750 > base 0.679 > C8 0.643 > +30 variant 0.571; the
  +30 rule displaced gold on fastapi's generic-word issues while helping
  rich, whose short issue texts carry distinctive module-name words.

Decision: **remove the bare-identifier rule** (explicit `.py` names, dotted
modules, backticks and quoted strings keep their boosts) **and add explicit
deterministic tie-breakers** to both ranking sorts (ties now resolve by
`(filepath, start_line, qualname)` instead of scan order). The 28-sample
showed tie-breakers are behavior-preserving where scores differ distinctively
(current == stored-v3 on 20/20 before the revert; v4-vs-base movement is the
intended bare-id revert plus the tie-break normalization).

**Final v4 aggregates vs priors:** @3 +0.023 and @5 +0.031 over base (84 and
96 hits vs 81 and 92), @10 matches the best (107), zero-return matches the
best (22). Against base: 22 tasks changed rank (16 better, 6 worse) — a
mechanism-backed net gain roughly 4× the noise bar used for GPU runs, and
this is an offline instrument, not a leaderboard read.

| repo | v4 @1 | v4 @3 | v4 @5 | v4 @10 |
|---|---|---|---|---|
| fastapi (n=67) | 0.403 | 0.657 | 0.731 | 0.836 |
| rich (n=48) | 0.354 | 0.562 | 0.708 | 0.771 |
| requests (n=13) | 0.692 | 0.923 | 0.923 | 1.000 |
| httpx (n=1) | 1.000 | 1.000 | 1.000 | 1.000 |

---

## 2. Track A vs Track B matrix

Legend: ✅ already green (no change) · 🔧 improved/fixed in this audit ·
❌ rejected (mechanism wrong). Evidence in parentheses.

| dimension | Track A claim / proposal | Track B finding | resolution |
|---|---|---|---|
| **Compaction survival (item 1)** | "compaction every 5 turns over 14,336 tokens" | live `HARNESS_README.md:571-574`: `compaction_interval = 15`, `token_threshold = 14,336`, `overlap_size = 2`, `event_retention_size = 5` — every **15** turns; the last 5 events survive | 🔧 premise corrected + cheap insurance kept: prompt emits a plain-text `ANCHOR: <file>:<line> <root cause>` line after `locate` and after each edit (~150 chars). With 28 calls a session can cross 2 compaction walls only late, so the anchors + retained tail are proportional defense |
| **Output ceiling ≤ 3,500 (item 1)** | cap every skill-script output | `swe.py` cap was 4,800, end-truncating — long outputs lost the `NEXT:`/`TEST:`/`FALLBACK:` contract lines. Harness facts: built-in tools truncate stdout at `max_stdout_chars` 5,000 (`HARNESS_README.md:330,561`); ADK `run_skill_script` returns `_r.stdout` **raw, untruncated** (`skill_toolset.py:689`) | 🔧 `OUT_CAP = 3500`, `CAP_HEAD = 1400`, **middle truncation** (cap now removes the middle and preserves head + contract tail). Test: 15,447 → 3,490 chars with `STATUS:` head and `NEXT:` tail intact |
| **Output token budget (item 2)** | keep 8192/4096, do not lower to 6144 | `configs/sampling.yaml` = `max_output_tokens: 8192`, `thinking_budget: 4096`, `include_thoughts: true` | ✅ unchanged |
| **Zero-leak skills (item 3)** | `atexit` rmtree of `/workspace/skills` on every `swe.py` invocation | **Wrong target**: installed ADK 1.36.1 materializes skills into `tempfile.TemporaryDirectory()` + `os.chdir(td)` + runpy (`skill_toolset.py:617-709`); `/workspace/skills` is never created. Worse, `_verify.verify()` still rmtree'd `<root>/skills` — editing the task tree (contract violation) and silently deleting a leak it should report | ❌ atexit rejected · 🔧 rmtree deleted from `verify()` (read-only restored) · 🔧 real guard instead: `stray_files()` flags any `skills/` path in the changed set; agent deletes it after an explicit report |
| **Verifier blindness (Track B find)** | not on the checklist | `untracked_files()` filtered `skills/` untracked files out of the changed set, but the grader's `git add -N .` recurses every untracked directory — a leak walked straight past the gate | 🔧 filter removed. `ignored_new_files()` keeps its filter deliberately: a `git add -N -f skills/…` suggestion would force ignored files into the patch (harmful). The asymmetry is intentional and docstringed |
| **Bounded reads (item 6)** | 60–100-line `read_file` windows | prompt file instructed this throughout; 150-line/10,000-char harness dual cap (`HARNESS_README.md:444,562-563`) | ✅ verified both sides |
| **4 verify traps in one shot (item 6)** | AST, protected, ignore-trap, targeted pytest | all present + JUnit first-failure line; `verify()` fixture: protected/syntax/stray/ignored each correctly reported (18/18 audit asserts) | ✅ + the two fixes above |
| **Early exit + call-24 breaker (item 5)** | add the two rules | consistent with budgets: `eval_config.yaml` 28 calls / 8 min / 80 turns / 240 s — unchanged by design (35-call rule measured no effect earlier; 12-min per-task caps score 0 — AGENTS.md §5) | 🔧 ~300 chars added to CALL PLAN (rules from call 21 and call 24) |
| **Cold-call signature (item 4)** | exact `run_skill_script` argument names, zero discovery turns | prompt already carries the up-to-date signature block from commit `2b7cd84` | ✅ verified |
| **`git grep` fallback (item 4)** | required fallback | already present ("FALLBACK: … git grep -n …") | ✅ verified |
| **Argument-parsing edge cases (Track B)** | not on checklist | nasty argv test (quote, backtick, single quotes, embedded newline, ANSI): `locate` exits 0, no traceback, 2,626-byte output, `STATUS:` + `NEXT:` intact | ✅ tested 18/18 incl. this |
| **Timeout hierarchy (Track B)** | pytest hang risk | `_guard.run` daemon-thread watchdog; `_run_pytest` subprocess `timeout=150s`; on timeout returns `TEST: TIMEOUT` with `rerun with a narrower -k filter` — bounded, and a verification (Phase-2) pytest also caps at 300 s (`HARNESS_README.md:560`) | ✅ double-bounded |
| **Encoding oddities (Track B)** | not on checklist | reads use `errors="replace"`; path separators normalized (`\\` ↔ `/`) in stray/protected/stray checks; Windows-style `posix.startswith("skills\\")` branch covers mixed separators | ✅ covered |
| **Tool-call ceiling 28 vs 30/35 (item 5)** | compare | no measurement ever favored 30/35 (prior attempt), kept 28 with breaker rules beyond call 21 | ✅ unchanged |
| **Engine determinism (Track B)** | not on checklist | pre-v4 sorts resolved equal scores by scan order (stable-sort insertion) — engine-version-dependent ordering | 🔧 explicit tie-breakers on both sorts |

---

## 3. Merged "best-of-both" configuration

Applied and made byte-identical across all four copies (repo `skills/`,
`ckpt/bundles/exp13_swe_toolkit`, `kaggle_work/.../bundles/exp13_swe_toolkit`,
`bundles/exp13_swe_toolkit`) via `tools/sync_exp13.py`:

**`skills/swe-toolkit/scripts/_index.py`**
- bare-identifier → `paths` rule **removed** (measured regression; §1);
- explicit tie-breakers on `ranked_files` `(test, -score, path)` and
  `ranked_syms` `(-score, filepath, start_line, qualname)`.

**`skills/swe-toolkit/scripts/swe.py`**
- `OUT_CAP 4800 → 3500`, `CAP_HEAD = 1400`, middle-truncating `cap()` — the
  `NEXT:`/`TEST:`/`FALLBACK:` contract lines can no longer be truncated away.

**`skills/swe-toolkit/scripts/_verify.py`**
- `verify()` rmtree **removed** (read-only contract restored);
- `stray_files()` flags `.orig`/`.rej`/`.adk_exec_*` **and any `skills/` path**;
- `untracked_files()` stops hiding `skills/` untracked files;
- `ignored_new_files()` unchanged (harmful-suggestion guard kept).

**`prompts/system.md`** (+1,484 chars total vs the exp05 base 5,517 → 7,001;
+~370 tokens under a 14,336 threshold)
- compaction-corrected anchor discipline (`ANCHOR:` after `locate`, after
  edits; interval=15 stated correctly), early-exit from call 21, the call-24
  circuit-breaker, explicit "verify once, then submit" rule.

**Unchanged:** `agent.yaml` (10 tools incl. 3 harness neighbors), `sampling.yaml` (0.2 / 0.95 / 8192 / 4096), `eval_config.yaml` (28 / 8 / 80 / 240).

### Diff summary since commit `643c6f4`

```
 skills/swe-toolkit/scripts/_index.py             | 40 +++++-----
 skills/swe-toolkit/scripts/_verify.py            | 47 +++++++---
 skills/swe-toolkit/scripts/swe.py                | 43 +++++---
 ckpt/bundles/exp13_swe_toolkit/prompts/system.md | 24 +++---
 docs/TASKLIST.md                                 | 17 ++++
 (+ untracked, now committed: docs/FINAL_HARNESS_COMPARISON.md,
    tools/sync_exp13.py, tools/test_verify_8_scenarios.py [scenario 9
    expectation updated to the report-don't-delete contract],
    tools/benchmark_locate_129.py)
```

### Test results on the final state

| gate / suite | result |
|---|---|
| Gate 1 `check_resources.py` (system python) | exit 0 — `all required resources present` (E0 `57836949` PENDING) |
| Gate 2 `verify_bundle.py --bundle ckpt\bundles\exp13_swe_toolkit` | exit 0 — `ALL CHECKS PASSED` |
| Gate 3 `build_notebook.py --bundle … → verify_notebook.py --notebook …` | exit 0 — `ALL CHECKS PASSED`; artifact **sha256 `c9135bcb969f91c20ada77f999c12b05c603ceaaeda4d85f6d5c155ba543c415`**, 21,285 B |
| empirical suite (argv/cap/verify fixture) | 18/18 asserts |
| adversarial suite `tools/test_verify_8_scenarios.py` | 9/9 (scenario 9 contract updated: leak is reported, not silently deleted) |
| byte-identity of the 3 engine files × 4 dirs | all identical |
| full locate benchmark (129 tasks) | v4: 0.419 / 0.651 / 0.744 / 0.829, zero 0.171 (§1) |

---

## 4. Gate-4 closure issue (carried from `docs/TASKLIST.md` T7)

The kernel `narisettichaitanya/gemma4-devagent-exp13-swe-toolkit-v2` is
`COMPLETE`, `DONE_OK`, no traceback, sha256 `f30e84b3…` — but its artifact is
from an **older bundle revision**: 16 members, skill dirs in both spellings
(`skills/swe-toolkit/` + `skills/swe_toolkit/`), a `bootstrap.py`, and no
script hash matching any on-disk copy. The bundle that now passes Gates 2/3
(sha256 `c9135bcb…`, above) **has never been pushed**. Gate 4 closes only after:

1. refresh the kernel dir's notebook: re-splice `build/exp13_swe_toolkit.ipynb`
   into `kaggle_work/.../experiments/exp13_swe_toolkit/`;
2. `kaggle kernels push -p …`, then confirm the **real slug** via
   `kaggle kernels list --mine` (slug ≠ requested id trap);
3. wait for the CPU run (minutes), `kaggle kernels output -p runs/…`;
4. assert status `COMPLETE`, no traceback, and pulled-zip sha256 byte-equal to
   `c9135bcb969f91c20ada77f999c12b05c603ceaaeda4d85f6d5c155ba543c415`.

Steps 1–4 are kernel-only and are **not** a submission. Submission remains
blocked by pending E0 `57836949` (`maxPendingSubmissionsPerTeam: 1`) and by
rule 1 (explicit user "yes" required).

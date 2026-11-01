# Score Prediction & Roadmap — exp13 v4, E0, e4b line

Date: 2026-11-01. Written while `57836949` (E0 control, exp05 byte-identical) is
PENDING; meanwhile this doc fixes expectations for the exp13 v4 submission
(`c9135bcb…`, kernel g…exp13-swe-toolkit-v2 v2, hash-locked) and the E4B small
track. **Locked artifacts: `bundles/exp13_swe_toolkit` and
`build/exp13_swe_toolkit.ipynb` — untouched.** No submissions while E0 is
pending.

## 1. Conversion-chain model for `exp13_swe_toolkit` (31B)

Measured on the 129-task offline instrument (v4 engine, any-gold criterion,
`docs/FINAL_HARNESS_COMPARISON.md` §1):

| file-locate stage | R@1 | R@3 | R@5 | R@10 | zero-return |
|---|---|---|---|---|---|
| exp05-era engine (`2b7cd84`) | 0.419 | 0.628 | 0.713 | 0.829 | 0.171 |
| **exp13 v4 (shipped)** | 0.419 | 0.651 | **0.744** | 0.829 | 0.171 |

The pipeline score decomposes as
`P(solve) ≈ P(locate gold file) × P(edit correct | located) × P(patch preparation | edited)`.
Using the exp05 anchor to calibrate the unmeasured stages: exp05 scored 0.20
on a locate base of R@5 = 0.713, i.e. the located-to-passed multiplier is
`0.20 / 0.713 ≈ 0.28` (0.97 success on patch preparation is subsumed here).

Applying that multiplier to the v4 locate stage:

- `0.744 × 0.28 ≈ 0.208` from the locate uplift alone;
- verify-gate improvements (syntax/protected/stray/ignore traps, untracked
  visibility) and early-exit/breaker prompt rules are worth a conservative
  **+1–2 tasks out of 129 ≈ +0.008–0.016** on the conversion rate: a failure-
  free patch just submits; a broken patch at call 24+ now degrades to a
  minimal parseable edit instead of a zero.

**Point prediction: ≈ 0.21 (≈ 12.2 / 58 tasks) on the public LB**, versus the
exp05 anchor 0.20 and exp12 0.17.

**90% interval (binomial, n = 58):** at p = 0.21 the standard error is
√(0.21·0.79/58) = 0.054, so ±1.645·SE ⇒ **[0.12, 0.30]**. The historical
pooled 31B evidence (52/290 = 0.179, SE 0.022 per pooled estimate) reinforces
that any single-run difference below ≈ 0.06 against exp05 is not resolvable —
the locate uplift (+0.031 R@5) by itself is under that bar; only the combined
locate + verify + prompt effect (~+2 tasks) is worth submitting on the
mechanism, which is why exp13 v4 exists and E0 is measuring exp05 reproducibility
in parallel.

**Where the ceiling is.** If nothing above locate changes, the model cannot
predict a mean above ≈ 0.24 (the edit multiplier 0.28→0.31 is the maximum
supportable claim from this instrument, cf. §3 symbol-recall work). The big
levers, in order: symbol-level targeting (read the right 100 lines instead of
the right file), edit fidelity at 31B, and the 22 zero-return tasks
(all gold_n ≤ 2 — their issue text carries no path/symbol to grep; 11 fastapi
+ 11 rich) which currently score ~0 unless the model solves them from issue
semantics alone.

Segment detail worth keeping pinned:

| segment | n | hit@3 | hit@5 | hit@10 |
|---|---|---|---|---|
| gold files = 1 (91 tasks) | 0.604 | 0.714 | 0.802 | |
| gold files > 1 (38 tasks) | 0.763 | 0.816 | — | |
| zero-return (22 tasks) | 0 | 0 | 0 | |

(Reading depth matters: 11 of 129 tasks first contain gold at @10 — the
agent's fallback / iteration over locate's top-10 is the mechanism that turns
those into candidates, hence the expanded `FALLBACK` line in the exp13 prompt.)

## 2. Why `e4b-v2` = 0.05 (ref `57806053`) and `exp11_e4b` = 0.06 were flat

Baseline: `57777888` (`exp11_e4b`, exp05 prompt/tools/budgets verbatim, model
swapped) = **0.06**; `57806053` (`e4b-v2`, temperature 0.1, imperative prompt
≤ 2,500 chars, no skills) = **0.05**. Both are ≈ 3/58 — the two interventions
changed nothing because neither touched E4B's binding constraints.

Mechanism diagnosis (each maps to a measured harness fact):

1. **Edit fidelity, not exploration votes, is the bottleneck at 4B.**
   `edit_file` requires restoring `old_string` exactly; a 4B model
   mis-copies anchors (indentation, multi-line headers) far more often, and
   each failed retry burns one of 35 calls and one of 8 minutes. Prompt
   compression and lower temperature change vocabulary, not copying accuracy.
2. **`run_command`-based exploration is low-precision at 4B.** The v2 prompt
   delegates searching to grep one-liners the model composes; without the
   toolkit's deterministic BM25/trace scoring, the file gold lands in the
   explored window ~0.5–0.6 at best, and each wasted grep costs calls.
3. **Context pressure eats the plan.** Compaction (`interval=15`,
   threshold 14,336) discards tool outputs; a 4B model holding its plan in
   plain text has to re-derive state each time. The exp05 line's own anchors
   do not exist without plain-text emission discipline, which the e4b-v2
   prompt cut first.
4. **Compile-time failure modes.** A 4B-authored patch with a syntax error
   scores 0; no update in v2 addressed that failure mode.

**Expected value of giving E4B the verified `swe-toolkit` v4 skill
(`locate` + `verify`):** the deterministic locate stage replaces (2) with the
31B-line file rates (R@5 0.744 on identical snapshots; same Python, no model
inference needed) and one tool call instead of 2–4 grep calls; verify gates (4)
so a partial patch is at least parseable before submission. Rough conversion
chain for E4B: locate 0.5–0.6 → ~0.74 (`+0.2` on the first factor) times an
edit multiplier that stays weak (`0.13–0.18`) and time-caps → **predicted
0.09–0.13**, i.e. roughly double the current 0.05, with an honest interval of
[0.04, 0.16] at n = 58 (SE ≈ 0.04). The E4B line only re-enters the
$10 k small-model track if a verified run beats 0.06 — which is what
`e4b_v3_swe_toolkit` (Task 3) is staged to measure.

## 3. Intra-file symbol recall (Task 2 summary)

Current shipped engine v4, same instrument, 121/129 tasks with identifiable
gold symbols:

| symbol metric | hidden@1 | hidden@3 | hidden@5 | hidden@10 |
|---|---|---|---|---|
| locate's shipped symbol ranking | 0.157 | 0.231 | 0.306 | 0.364 |

(Web reference: `top_syms` comes from `_index.rank_syms`.) The R&D prototype
(`%TEMP%/opencode/symrank_v5.py`, outside the repo; the locked bundle is not
touched) re-ranks symbol spans inside the top-8 returned files with span-level
scoring (signature+body token overlap, exact/trace boosts, x1/rank file prior).

Measured v5 outcomes — full 129-task run, 2026-11-01, same instrument; per-task
JSON `%TEMP%/opencode/symrank_v5_results.json` (607 s total; read-only import of
the locked engine, bundle untouched). 121/129 tasks have gold symbols:

| symbol metric | shipped v4 `locate` syms | v5 span re-rank | delta |
|---|---|---|---|
| hit@1 | 0.157 (19) | 0.190 (23) | +0.033 |
| hit@3 | 0.231 (28) | 0.322 (39) | +0.091 |
| hit@5 | 0.306 (37) | 0.388 (47) | +0.082 |
| hit@10 | 0.364 (44) | 0.488 (59) | +0.124 |

- **File ranking unchanged.** Fresh v4 `locate()` ranks matched the stored v4 run
  exactly — 0/129 mismatches — so File R@3 = 0.651 and R@5 = 0.744 carry over
  intact.
- **Cost inside the 20 s locate budget.** v5 adds +0.235 s median / +0.534 s max
  (warm cache) on top of locate's own 4.61 s median / 10.78 s max. Cold-start in
  the container is the shipped engine's cost and is unchanged by v5.
- **Scope ceiling, measured.** v5 re-ranks spans only inside the top-8 files:
  101/121 gold-symbol tasks have a gold file there (0.835); the other 20 are
  structurally unreachable. Within that in-scope set v5 hits
  @1/3/5/10 = 0.208/0.366/0.446/0.564. All 359 gold qualifiers are bare names
  (no dotted paths), so the gold criterion itself has no class-path ambiguity.
- **Target check.** Lifting hit@3 to ≥ 0.50 was not reached (0.322 overall,
  0.366 in-scope). Next levers, to be tested only as a separate prototype:
  container-vs-member weight rebalance (the +3.0 member bias was a guess), a
  `gold-symbol-context` term (issue text immediately around the symbol mention),
  and top-12 file scope for the 20 out-of-scope tasks.
- **Prototype spec** (reproducible): `score(span) = 5.0·|high_tokens∩span| +
  1.5·|general∩span| + 80·exact-name + 40·trace-func + 40·trace-file + 3.0·member`
  multiplied by `1/file_rank`, over the top-8 files; deterministic sort key
  `(-score, filepath, start_line, qualname)`. Implementation lives in
  `%TEMP%/opencode/symrank_v5.py` outside the repo; an engine change lands only
  as its own isolated experiment (exp14) after user approval and a
  benchmark-equality rerun.

## 4. Roadmap while E0 is pending

1. ~~Gate 4 kernel push~~ closed (v2, DONE_OK, hash-locked `c9135bcb…`).
2. ~~Symbol-recall prototype~~ measured (§3). Engine change awaits review.
3. `e4b_v3_swe_toolkit` staged + bundle-verified (§2); only proceeds to kernel
   if allowed after the submission-quota frees up.
4. On E0 scoring: pooled comparison E0 vs 57553805 (0.20 anchor) → decide
   whether the daily submission goes to exp13 v4 (`c9135bcb…`) unchanged or
   after the symbol upgrade lands in a v5 build.

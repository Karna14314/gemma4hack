# Audit — E4B v2 (0.05), the 0.20 anchor, and what is actually measurable

Run 2026-10-31, after `57806053` (e4b-v2) returned **0.05** and before the E0 control
(`57836949`) resolves. Every claim below is either a number computed from the submission
history, a hash from a file in this repo, or an explicitly labelled model.

## 0. The one-paragraph version

The public LB has about 58 tasks. One task is 0.017 and the standard error at our score
level is **0.050**. That is the same size as every "difference" we have been chasing. The
31B line has four runs at 0.17 and one at 0.20; pooled, that is **0.179**, not 0.20. The
E4B line has 0.06 and 0.05, which is 3.5 versus 3 tasks — less than one task apart. And the
"byte-exact 0.20 anchor" in `ckpt/bundles/exp05_patch_integrity` is **not** the artifact that
scored 0.20: it carries 36 extra characters that were added after the submission. So the
control we just submitted was rebuilt from `ckpt/exp05/submission.zip`, not from the frozen
bundle, and it is byte-identical to the original (`2ba7f9b1…`).

---

## Audit A — What the LB can resolve

**Question.** Is 0.17 versus 0.20 a real difference?

**Method.** Binomial with n = 58 (the LB exposes 50% of ~120 hidden tasks;
`leaderboardPercentage: 50`). One task = 1/58 = 0.0172.

| quantity | value |
|---|---|
| standard error at p = 0.18 | **0.0504** |
| 95% CI for 10/58 (0.172) | 0.096 – 0.289 |
| 95% CI for 12/58 (0.207) | 0.123 – 0.328 |
| P(observe 12/58 given true p = 0.172) | **0.102** |
| P(observe 10/58 given true p = 0.200) | **0.119** |

**Conclusion.** The two observations are equally likely under either hypothesis. The data
cannot distinguish a 17% solve rate from a 20% solve rate. Any experiment whose expected
effect is 2–3 tasks is unmeasurable on one LB run.

**Implication.** This is why the paired dev-set instrument (T1) gates the ladder. It is not
a nice-to-have; it is the only way to resolve the effects we are now chasing.

---

## Audit B — The 31B anchor is 0.179, not 0.20

**Question.** What is the anchor's true value?

**Evidence.** Every 31B submission to date:

| ref | bundle | score | tasks (of 58) |
|---|---|---:|---:|
| 57037122 | exp03 baseline | 0.17 | 10 |
| 57553805 | exp05 patch integrity | **0.20** | 12 |
| 57618114 | exp08 tool contract | 0.17 | 10 |
| 57654236 | exp10 consolidated | 0.17 | 10 |
| 57736284 | exp12 timing buffer | 0.17 | 10 |

Pooled: (10 + 12 + 10 + 10 + 10) / (5 × 58) = **52/290 = 0.179**.

**Conclusion.** 0.20 is one high draw in five. The mode is 0.17, the pooled estimate is
0.179, and exp05's +0.03 "gain" over exp03 is 2 tasks — 0.6 standard errors.

**Implication.** Three prompt experiments (exp08, exp10, exp12) each changed one thing and
each landed on the same number. That is not three failures; it is one measurement repeated.
The correct reading is that **prompt-level changes of this size do nothing measurable**, and
the next change has to be structural (tooling), not textual.

---

## Audit C — e4b-v2 is not a regression, and it was not an isolated experiment

**Question.** Why did e4b-v2 score 0.05, below exp11_e4b's 0.06?

**Evidence 1 — the difference is smaller than one task.** 0.06 ≈ 3.5/58, 0.05 ≈ 3/58.
The gap is 0.6 tasks. It cannot be resolved at n = 58.

**Evidence 2 — three things changed at once.**

| field | exp11_e4b (0.06) | e4b_v2 (0.05) | e4b_v3 (not submitted) |
|---|---|---|---|
| model | E4B | E4B | E4B |
| temperature | 0.2 | **0.1** | 0.1 |
| `max_tool_calls` | 28 | **35** | 28 |
| `thinking_budget` | 4096 | 4096 | **1024** |
| prompt chars | 5,353 | **1,746** | 2,440 |
| `max_time_minutes` | 8 | 8 | 8 |
| tools | 6 | 6 | 6 |

The submission message itself lists two changes ("temperature 0.1 + imperative prompt") and
the config contains a third (35 calls). Under AGENTS.md rule 4 this is not an experiment; it
is a new bundle.

**Evidence 3 — the prompt lost the procedure.** The 5,353-char prompt was the exp05 prompt
minus one line (the graph-tool warning). The 1,746-char replacement removed:

- the specification-extraction step (exact names, messages, types, edge cases),
- "fix the cause, not the symptom" and the backward-compatibility rule,
- the `docs_src/` instruction for documentation-code tasks,
- the decision rules for ambiguous issues and failed searches.

It kept the hard limits and replaced the rest with a six-step imperative workflow and a
final-gate shell snippet. For a 4B model, the removed material is the scaffolding.

**Conclusion.** e4b-v2's score is **uninterpretable**: the effect is below resolution and the
treatment is confounded three ways. The defensible statement is "E4B sits at 0.05–0.06,
about 3 tasks in 58".

---

## Audit D — Is "tool calls too low" the E4B failure mode?

**Question.** E4B generates more tokens per turn; should we raise `max_tool_calls`?

**What we can observe.** Nothing per task. A competition submission exposes one number: the
LB score. The scoring run happens on the organizers' side and its logs are not returned. We
have **zero traces** — no call counts, no elapsed times, no patch sizes — for any of the ten
submissions. Every statement about tool-call counts is inference.

**What the arithmetic says.** With `max_time_minutes: 8` and `thinking_budget: 4096`:

```
turns_reachable = 480 s / (t_think + t_out + t_prefill)
t_think ≈ 4096 / throughput
```

To reach 35 calls in 480 s, the average turn must be ≤ 13.7 s, which requires ≥ 299 tok/s
sustained *if* the full 4,096-token thinking budget is used. If thinking is actually a few
hundred tokens, 35 calls is easy. The two regimes predict opposite failures, and we cannot
tell them apart without a trace.

**What the experiment already told us.** e4b-v2 raised the cap from 28 to 35 and did not
improve. That is the one direct test of the "raise the cap" hypothesis, and it came back
negative. Raising it again is not supported by evidence.

**Three hypotheses and what each predicts:**

| hypothesis | signature in a trace | fix | does raising calls help? |
|---|---|---|---|
| **time-bound** — turns are slow, wall clock expires | calls_used ≪ 35, elapsed ≈ 480 s | cut `thinking_budget`, shorten outputs, fewer turns needed | no |
| **call-bound** — model uses every call and still fails | calls_used ≈ 35, patch_size > 0 | raise cap, or cut calls needed per task | yes |
| **capability-bound** — finds the file, writes the wrong fix | calls_used moderate, patch_size > 0, test fails | better model, or a stronger spec-reading scaffold | no |

**Conclusion.** The hypothesis is plausible but untested, and the one test we ran (28 → 35)
did not support it. The discriminating measurement is a trace, which only the paired
dev-set kernel produces.

---

## Audit E — The "byte-exact 0.20 anchor" was not byte-exact

**Question.** Is `ckpt/bundles/exp05_patch_integrity` the artifact that scored 0.20?

**Evidence.** Extract the submitted archive and compare member by member:

| member | submitted `ckpt/exp05/submission.zip` | frozen bundle (LF-normalised) |
|---|---:|---:|
| `agent.yaml` | 314 B | 314 B |
| `configs/sampling.yaml` | 119 B | 119 B |
| `eval_config.yaml` | 94 B | 94 B |
| `prompts/system.md` | **5,425 B** | **5,461 B** |

The prompt diff is exactly three lines appended after the submission:

```
+
+## The issue
+{problem_description}
```

So the frozen bundle is the 0.20 artifact **plus an issue trailer**. Its zip hash is
`ccc70f3b…`; the submitted artifact is `2ba7f9b118ea1837…`.

**Why it matters.** Two reasons.

1. A control built from the frozen bundle would not have been a control. It would have been
   "exp05 + 36 chars", i.e. a new experiment.
2. Our own `verify_bundle.py` **rejects** the true 0.20 artifact with two failures
   (`prompt has problem_description`, `prompt ends cleanly`). The official harness
   (`adk_submission.validate_directory`, `compile_submission`) accepts and compiles it. So
   the repo's prompt-hygiene rule is stricter than the harness — it is a convention added
   after 2026-10-23, not a platform requirement.

**Resolution.** E0 was rebuilt from `ckpt/exp05/submission.zip`, verified with
`verify_notebook.py` (ALL CHECKS PASSED, including the real harness), pushed as
`narisettichaitanya/g4-e0-exp05-control-resubmit`, and the pulled artifact is byte-identical:

```
kernel output   2ba7f9b118ea1837d1950038894cc856d1d33fe98c333d216afe6aaac1661774
submitted 0.20  2ba7f9b118ea1837d1950038894cc856d1d33fe98c333d216afe6aaac1661774
```

**Implication.** The anchor must be described as "the artifact in `ckpt/exp05/submission.zip`",
not as the frozen bundle. The frozen bundle should be renamed or annotated; it is a *variant*,
not the anchor.

---

## Audit F — What is missing from every 31B run

The 31B prompt is 5,461 chars and instructs the model to grep, read, edit, test, submit. What
it does not do, against the measured task distribution:

| gap | evidence | why it costs tasks |
|---|---|---|
| no localization aid | 43% of issues are template/title-only; 7% share no token with the gold patch | the model must guess from a title; 4–8 calls of grep and reading |
| no multi-file completion | 29% of gold patches touch 2+ files | a correct edit to one file leaves the call sites stale |
| no reproduce-first rule | 25% of issues carry a traceback | running the snippet yields the exact file:line in one call; the prompt only says "may run it once" |
| no verification that survives truncation | `run_command` keeps the first 5,000 chars; pytest's verdict is last | the model cannot see PASS/FAIL on a real suite |
| context pressure | 32,768 total; 8,192 output + 4,096 thinking + 5,461 prompt ≈ 17.7k reserved | 3–4 `read_file` calls can exhaust the history and force compaction or a 400 |

These are the five things the toolkit addresses, in the order they cost tasks.

---

## Conditional next steps

### If E0 (`57836949`) returns ≈ 0.20

- The anchor is real at 0.20; the four 0.17 runs are the low tail.
- exp05's patch-integrity change is worth ~2 tasks, which is real but at the edge of
  resolution.
- E1 must beat **0.20**, not 0.17. Keep the paired instrument as the primary judge; use the
  LB only as confirmation.
- Do **not** conclude that prompt changes work — exp08/exp10/exp12 still failed to reproduce
  the gain.

### If E0 returns ≈ 0.17

- The anchor is **0.179** pooled; 0.20 was noise.
- Every 31B configuration we have tried is one distribution. The prompt line is exhausted.
- E1 is measured against 0.18. A +0.03 result is still unmeasurable on the LB; require the
  paired instrument or a ≥ 0.06 delta.
- This branch is not less likely than the 0.20 branch: 10/58 is the single most probable
  count under both hypotheses (P = 0.137 at p = 0.172, P = 0.119 at p = 0.20).

### If E0 returns ≤ 0.13

- Something changed outside the bundle: model serving, harness version, or task sampling.
- Stop the ladder. Re-run `check_resources.py`, confirm the wheelhouse hashes, and compare
  the pulled artifact to `ckpt/exp05/submission.zip` again before spending another slot.
- A drop of that size cannot be caused by a byte-identical artifact.

### If E0 returns ≥ 0.24

- Upside variance is larger than modelled. One run cannot confirm it; a repeat is required
  before any conclusion.

---

## What to add to the 31B line

Ordered by expected value per call, not by novelty:

1. **`locate`** — one call returns the top 5 files with excerpts and the test command.
   Replaces 4–8 grep/read calls. Offline evidence: hit@3 6/7, 7/7 with test demotion.
2. **`verify`** — runs the targeted test and parses JUnit XML, so the verdict survives the
   5,000-char cap. Also gates empty patches and protected-file edits.
3. **`inspect`** — callers, overrides, and sync/async twins. Covers the 29% multi-file and
   9% async tasks.
4. **Reproduce-first rule** in the prompt — if the issue contains a traceback, run the
   snippet once before searching. One call, exact file:line.
5. **Context rule** in the prompt — never read more than 60 lines at once; after two reads,
   edit. Protects the 32,768 ceiling.

Do **not** add: more tool calls (tested, no effect), a knowledge book (32.6% precision), a
second skill (one language), or early `submit_patch` (the working tree is graded anyway, so
it is not insurance).

---

## E4B decision

**Close the line.** Genuine E4B is 0.05–0.06, about 3 tasks in 58 (95% CI 1.8%–14.1%). To
reach the 31B's 0.179 it would need 3.4× more solved tasks. No single budget knob produces
3.4×, and the two E4B submissions we have are already statistically identical. The E4B
track's remaining value is as a paper-track scale ablation, not as a competition entry.

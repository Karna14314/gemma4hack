# RESULTS — gemma-4-developer-agent

Append-only ledger. One row per experiment, including failures.

## Status

| exp | date | change vs base | metric | status | notes |
|---|---|---|---|---|---|
| exp01 SUBMITTED | 2026-10-03 | kernel v3 | public 0.05 | scored | ref 56793672 |
| exp02 v2 | 2026-10-03 | thinking on, 6 min/60 calls/120 turns, prompt rewrite | public ~0.08 | scored | four changes bundled; see `ckpt/STATE.md` history |
| **exp03 baseline replica** | 2026-10-10 | replaced by the public **0.17** SuperAgent bundle (identical config to the public 0.18 Budget-Fit bundle) | target 0.17+ | built, validated | full analysis in `research/BASELINE_017.md` |
| exp04 A1 | 2026-10-10 | baseline + mandatory `py_compile` after every edit | pending kernel | built, validated | single change; attacks non-applying patches |
| exp05 A2 | 2026-10-10 | baseline + pre-submit patch integrity (`git status --short`, `git add -N -f`) | pending kernel | built, validated | single change; attacks empty patches |

**The public baseline replaced our own bundle on 2026-10-10.** Our v2 scored ~0.08;
three public notebooks score 0.17-0.18 and converge on one configuration
(single agent, thinking on at 4096, `max_output_tokens` 8192, 240 s commands,
28 tool calls, 8 minutes, 80 turns). `src/agent_package/` is now a byte-exact
replica of that configuration; the diff and the ablation plan are in
`research/BASELINE_017.md`. Everything below is
offline engineering and validation plus clean Kaggle kernel runs, not measurement. There is
no local way to measure resolution rate: the real evaluator needs 4x L4 GPUs, the 31B QAT
weights, and the container image.

| exp | date | change vs base | metric | status | notes |
|---|---|---|---|---|---|
| setup | 2026-10-03 | research + harness audit | n/a | PASS | 30/30 offline checks pass, including the real `adk_submission.compile_submission` |
| notebook | 2026-10-03 | sections + builder + end-to-end verifier | n/a | PASS | notebook executes offline; artifact passes the real compiler |
| exp01 v1 | 2026-10-03 | kernel push, version 1 | kernel run | PASS | COMPLETE, no traceback, `submission.zip` byte-identical to the local build |
| exp01 v2 | 2026-10-03 | added explicit `DONE_OK` sentinel | kernel run | PASS | COMPLETE, `DONE_OK` once, no traceback, same digest |
| exp01 v3 | 2026-10-03 | competition attached as a source | kernel run | PASS | COMPLETE, `DONE_OK` once, no traceback, same digest — **this version was submitted** |
| **exp01 SUBMITTED** | 2026-10-03 | kernel v3, file `submission.zip` | resolution rate | **pending** | submission ref `56793672`, submitted 2026-10-03T08:34:41Z, digest `d0c8959d…` |

**exp01 is submitted** (submission ref `56793672`, status `pending`) and is the first
scored entry for this account. Kernel `narisettichaitanya/gemma4-devagent-exp01`
version 3, file `submission.zip`, digest
`d0c8959dfb3951756872ac49a46ff0aaaf163d7a9f4596db78fb463f2badeb95`.

### Two competition facts that contradict HANDOFF.md

| Documented | Actual | Consequence |
|---|---|---|
| the notebook must attach **no** competition source ("the notebook must need no inputs") | `submit-notebook` rejects it: *"Submission not allowed: Your Notebook must include this competition as a data source"* | `competition_sources: ["gemma-4-developer-agent"]` is mandatory. The notebook still reads nothing from it, so it remains functionally input-free |
| deadline 2026-12-02 | the competition API reports `2026-11-12T23:59:00.807Z` | ~40 days, not ~60. Worth re-checking on the competition page |

### The multipart trap

`ApiCreateCodeSubmissionRequest` is one of the requests `kagglesdk` marks as
form-encoded (`REQUESTS_REQUIRING_FORMS`). Posting the same body as JSON is accepted by the
route, has every field **silently ignored**, and returns
`"This competition requires an output FileName for Notebook Submissions"` regardless of what
was sent — an error that reads like a payload problem when it is an encoding problem. The
field name was correct all along.

## Verification layers that DO exist offline

Run with `python tools/verify_bundle.py` (auto re-execs into `.venv-harness`).

| Layer | What it proves | Result |
|---|---|---|
| 1. Project static validator | `src/notebook_lib/validator.py` accepts both bundles, packing is deterministic | PASS |
| 2. Real harness | `validate_directory`, `validate_single_declared_model` and `compile_submission` accept both bundles; our transcribed constants equal `build_submission_limits()`; our model alias is in the harness registry; empty-suffix files are rejected by the competition allowlist | PASS |
| 3. Negative tests | 16 known-bad bundles are each rejected with a precise `SubmissionInvalid` | PASS |

Compiled primary bundle, straight from the real compiler:

```
root 'swe_coder'  model=LiteLlm(model='gemma-4-31b-it-qat-w4a16-ct')  tools=10  output_tokens=8192
```

`tools=10` is the 9 harness tools plus the `code_analyzer` exposed as an `AgentTool`, which is
why it appears in `tools` rather than in `sub_agents`.

## Corrections made after the harness source audit

The public write-ups were used as the starting brief, then every load-bearing claim was checked
against the actual `swegemma` 0.2.7 / `adk_submission` 0.2.12 / `adk_eval_core` 0.1.0 source.
Four assumptions were wrong and were fixed:

| Claim from the write-ups | Reality in the source | Consequence |
|---|---|---|
| `search_similar_code` returns uncapped source, over 100 000 chars, and overflows the context, discarding the patch | capped at `max_stdout_chars` = 5 000 chars **shared across all ten results**, each head-truncated (`graph.py:260-277`) | prompt still bans the call, but for the honest reason: it burns a tool call for worse results than `git grep`, not because it overflows |
| `timeout_seconds: 120` is a good way to bound the agent | it also bounds the **Phase 2 pytest run** (`verification.py:502`), so it can time out verification of an already-correct patch | set to the 300 s default; `max_time_minutes` alone controls agent time, since the effective command timeout is `min(command_timeout, remaining_session_time)` |
| compaction summaries the original task message, so repeat `{problem_description}` | compaction is active in the scoring path at `token_threshold=14336` (README §7.2); only the model's own text survives | state-card instruction kept and strengthened; also added "keep tool results small" |
| 80 turns is enough | sub-agent LLM calls count against the same `llm_calls_used`, and `budget.turns` defaults to a hard-coded 500 | raised to `max_turns: 120`, `max_tool_calls: 80` |

Two new instructions came out of the audit that no public write-up mentions:

- **`.gitignore` can silently eat a new file.** `git add -N .` respects the repo's own
  `.gitignore`, so a file created on an ignored path never reaches the patch. The prompt now
  requires confirming the file in `git status --short` and forcing it with `git add -N -f`.
- **`pyproject.toml` is a protected path**, so it is reverted in Container B. A task whose fix is
  purely a config change is unwinnable by design; the prompt explicitly forbids touching it.

## Bugs found and fixed in our own validator

Building the negative tests first was worth it; each of these was a validator that silently
passed a broken bundle.

| Bug | Fix |
|---|---|
| `!include` targets were rejected because the official sample itself uses `../prompts/analyzer.md` from a sub-agent | test the **resolved** path stays inside the root, not the literal `..` |
| The YAML loader consumes the `!include` tag, so included values arrive as bare path strings — the resolver never matched and instructions were never inspected | recognise a value as an include when it names a file that exists in the package |
| Included `.yaml` files were returned as raw **text**, so `generate_content_config` was never a dict and its field allowlist never ran | parse included `.yaml`/`.yml` structurally |
| `search_similar_code` and graph-tool truncation were described from a write-up rather than the source | corrected against `graph.py` / `execution.py` / `workspace.py` |

## Environment problems found on this machine, and their fixes

These cost real time and are recorded so a future run does not rediscover them.

| Problem | Cause | Fix |
|---|---|---|
| `adk_eval_core` refuses to install | it requires Python >= 3.11, and only 3.10.12 is present | installed CPython 3.12.15 via `uv` and rebuilt `.venv-harness` on it |
| `uv venv` has no `pip` | uv does not seed pip | use `uv pip install --python .venv-harness/bin/python` |
| `tools/verify_bundle.py` never re-execs into the venv | `VENV_PYTHON` was hardcoded to `Scripts\python.exe`, the Windows layout | made it platform-aware |
| `kaggle` CLI returns **401 on every authenticated call** | the installed CLI (1.7.4.5, the newest on this box's index) authenticates with HTTP Basic, and the account's `KGAT_` token is only accepted as a `Bearer` token | added `tools/kaggle_rest.py`, which calls the same endpoints directly with bearer auth |
| the CLI still *appears* to work | public dataset downloads are anonymous, so they succeed while authenticated calls silently fail | always confirm with an authenticated endpoint before trusting the CLI |
| `kaggle kernels push` rejects the kernel | `kagglesdk` serialises POST bodies as **camelCase**; sending snake_case drops fields and surfaces as `Invalid kernel type ''` | send `kernelType`, `newTitle`, `userName`, ... |
| `kernels/status`, `kernels/pull`, `kernels/output` return 404 as POST | those routes are **GET** with query parameters, not POST | issue them as GET |

## The notebook-to-artifact equivalence result

The strongest evidence that the deliverable is correct: the `submission.zip` produced by the
kernel run on Kaggle is **byte-identical** to the archive built and validated locally,
`d0c8959dfb3951756872ac49a46ff0aaaf163d7a9f4596db78fb463f2badeb95`. So the artifact the
organizers receive is exactly the one that `adk_submission.compile_submission` was run
against, and no packaging step can have altered it.

## Next steps

1. exp01 is submitted and pending. Poll `tools/kaggle_rest.py submissions
   gemma-4-developer-agent`; the scoring rerun must finish inside 12 h for all ~120
   tasks, so expect hours.
2. Do not spend a second submission on an unverified bundle; one submission per day.
3. After the first score, test exactly one isolated change per submission, ranked in
   `HANDOFF.md`.

## 2026-10-10 — the public 0.17 baseline

- Kaggle auth fixed: the KAGGLE_API_TOKEN bearer flow works with CLI 1.7.4.5
  (`KAGGLE_API_TOKEN="$KAGGLE_KEY"`); plain `KAGGLE_KEY` still 401s on every
  authenticated call.
- The wheelhouse moved again: swegemma 0.2.7 -> **0.2.11**, adk_submission
  0.2.12 -> **0.2.13**. Every mechanism cited in the old notes was re-verified
  against the current wheels: `submit_patch`'s `git add -N .` + baseline diff
  (`tools/execution.py:77-127`), protected-file stripping
  (`harness/verification.py:62-85`), the working-tree fallback
  (`agent_runner.py:1054-1075`). `validate_single_declared_model` and
  `setup_gemma_model_registry` no longer exist; both verifiers now use
  `adk_submission.discovery.discover_declared_models` and the
  `adk_eval_core/budget/models.yaml` registry.
- Baseline replica: content-identical to the public bundle; `verify_bundle.py`
  and `verify_notebook.py` both ALL CHECKS PASSED for all three bundles, with
  `compile_submission` reporting `root 'swe_agent' tools=9 output_tokens=8192`.

## exp03 submission — result record

| field | value |
|---|---|
| submission ref | **57037122** |
| submitted | 2026-10-10T08:45:36Z |
| message | "exp03 baseline replica of public 0.17" |
| kernel | `narisettichaitanya/gemma4-devagent-exp03-baseline-017-replica` version 1, scriptVersionId 356964911 |
| file | `submission.zip`, sha256 `e3be904ca4823b9d6603360e2f34a43208c96ddc17db77c4d25f82218c4b0a68` |
| pre-flight | hash byte-identical to the checkpoint copy and to the local deterministic build; all four members match `submission_manifest.json`; no earlier submission from 2026-10-10 |
| status at handoff | **pending** (scoring rerun, hours-scale; poll command in `ckpt/STATE.md` and `EXPECTATIONS.md`) |
| not submitted | exp04 (py_compile) and exp05 (patch integrity) — both await an explicit decision |

## 2026-10-10 — exp03 SUBMITTED (ref 57037122, pending)

Baseline replica submitted with message "exp03 baseline replica of public 0.17".
Pre-flight checks passed: the kernel output zip sha256 `e3be904ca4823b9d…` is
byte-identical to the checkpoint copy and every member matches the manifest, and
`kaggle competitions submissions` showed no submission from 2026-10-10 beforehand
(previous: exp02 on 2026-10-04 at 0.08, exp01 on 2026-10-03 at 0.05).
Status at submission: PENDING. exp04/exp05 not submitted.

## 2026-10-31 — the measurement audit (read this before the next experiment)

Ten submissions, one table. The score column is the whole observable; there are no
per-task traces from any run.

| ref | date | bundle | model | score | tasks/58 |
|---|---|---|---|---:|---:|
| 56793672 | 10-03 | exp01 | 31B | 0.05 | 3 |
| 56812498 | 10-04 | exp02 v2 | 31B | 0.08 | 5 |
| 57037122 | 10-10 | exp03 baseline | 31B | 0.17 | 10 |
| 57553805 | 10-23 | exp05 patch integrity | 31B | **0.20** | 12 |
| 57618114 | 10-25 | exp08 tool contract | 31B | 0.17 | 10 |
| 57654236 | 10-26 | exp10 consolidated | 31B | 0.17 | 10 |
| 57697341 | 10-27 | exp11 E4B-as-31B | 31B | 0.13 | 8 |
| 57736284 | 10-28 | exp12 timing buffer | 31B | 0.17 | 10 |
| 57777888 | 10-29 | exp11 genuine E4B | E4B | 0.06 | 3.5 |
| 57806053 | 10-30 | e4b-v2 | E4B | 0.05 | 3 |
| 57836949 | 10-31 | **E0 control (byte-identical exp05)** | 31B | pending | — |

**Findings.** Full evidence in `docs/AUDIT_E4B_AND_ANCHOR.md`.

1. n ≈ 58, one task = 0.017, standard error = **0.050**. 0.17 vs 0.20 is 0.6 SE:
   indistinguishable.
2. Pooled 31B = 52/290 = **0.179**. 0.20 is one high draw in five; exp08/exp10/exp12 are
   the same measurement repeated, not three failures.
3. Genuine E4B = 0.05–0.06 = ~3 tasks (95% CI 1.8%–14.1%). **Line closed.**
4. e4b-v2 changed three things at once (temperature, call cap, prompt rewrite) and its
   0.05 vs 0.06 is 0.6 tasks. Uninterpretable.
5. **The "byte-exact 0.20 anchor" was not byte-exact.** `ckpt/bundles/exp05_patch_integrity`
   has 36 extra chars appended after the submission. The scored artifact is
   `ckpt/exp05/submission.zip`, sha256 `2ba7f9b118ea1837…`.

**E0 control (`57836949`).** Rebuilt from `ckpt/exp05/submission.zip`, kernel
`narisettichaitanya/g4-e0-exp05-control-resubmit` v1, pulled artifact hash
`2ba7f9b118ea1837d1950038894cc856d1d33fe98c333d216afe6aaac1661774` — byte-identical to the
0.20 submission. Submitted 2026-10-31T11:22:30Z. Note: `verify_bundle.py` rejects this
artifact on two prompt-hygiene checks; the official harness accepts and compiles it, which
is why the control was allowed through.

**Decision rule.** ≈0.20 → anchor real, E1 must beat 0.20. ≈0.17 → anchor is 0.179, prompt
line exhausted, E1 measured against 0.18 with the paired instrument. ≤0.13 → environment
drift, stop the ladder. ≥0.24 → repeat before concluding.

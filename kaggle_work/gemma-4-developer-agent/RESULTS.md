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

## 2026-10-31 — public-research audit: 0.24 is a tail, and the loss is localization

Full evidence: `docs/AUDIT_PUBLIC_RESEARCH.md`. No submission was made; this is analysis
over the public board, the public notebooks, and Dmitrii Gluzdov's 692-run task-level
dataset.

1. **Anchor = 0.179.** Five runs: 12, 10, 10, 10, 10 tasks. SD 0.89. 0.24 needs 14 tasks,
   which is 4.0 SD above the mean and 2 above the best draw. Identical bytes have scored
   0.12–0.22 across runs, so any single score is one draw.
2. **The public board is a smooth tail.** 4,261 teams: 0.24 = 6 teams, 0.22 = 58 teams at a
   median of 16 submissions each. No 0.24 recipe exists in the public work.
3. **Union ceiling.** All 8 public configs together solve 50/114 tasks (43.9%); our config
   solves 39/114 (34.1%) and scores 0.179. Scaled, the union is ~0.23.
4. **The 64 never-solved tasks are not a capability wall.** 30 of them are single-file
   patches of ≤30 lines, and 21 of those have issues ≤300 chars. Reaching 0.24 needs ~7 of
   those 30 — a localization problem, not a patch-construction problem.
5. **The built lever is not ready.** `exp13_swe_toolkit` passes `verify_bundle` but:
   `swe.py locate` takes 13.5–25.7 s on fastapi and the 25 s watchdog returns `DEGRADED`
   with no output; the prompt shells out to `find /`; the skill is named `swe_toolkit`
   instead of `swe-toolkit`; `SKILL.md` omits `locate`; and the prompt appends
   `{problem_description}`, making it two changes off the anchor. Not submitted.
6. **Next, no submission required.** Fix T2 items 1/2/7, expand the snapshot set from 7 to
   the 30 single-file never-solved tasks, and measure `locate` hit@3. Gate at 60%: pass →
   build and submit E1; fail → hold the anchor and spend the remaining days on draws.

## 2026-11-01 — T2 toolkit fixes + exp13 prompt repair (no submission)

E0 (`57836949`) is still `pending` at ~24 h, so no submission was possible. This entry
records the code work only.

**What changed in `skills/swe-toolkit/`** (the E1 lever):

| # | change | mechanism |
|---|---|---|
| 1 | `_index.walk` visits only `.py` and skips the per-file NUL probe; `MAX_FILES=4000` | fastapi has 2,418 files but 1,279 `.py`; the probe was 40% of the scan |
| 2 | `_guard.py`: `deadline_after` / `expired` / `run(seconds, fn)` thread watchdog | a partial ranking is always produced; `DEGRADED` with no body is a wasted call |
| 3 | `_index.locate` takes a `deadline`, sorts source-first, and reports `files_indexed/files_found/truncated/seconds` | a cut scan must not have spent its budget on `tests/` |
| 4 | test paths are zeroed, not penalised; `docs_src` ×0.5, vendored ×0.3; traceback ×6, error-string ×4 | protected paths cannot be gold |
| 5 | `swe.py` output contract: `STATUS` + `TOP FILES` + `NEXT:` + `TEST:` + `FALLBACK:` + excerpts (40 lines for #1, 8 for #2–5) | the model needs an action, not a ranked list |
| 6 | `_verify` rewritten: untracked files count as changes, empty diff is `FAIL`, stray `.orig/.rej/.adk_exec_*` and gitignored new `.py` are flagged, JUnit first-failure line, `STATUS`/`NEXT` | `git add -N .` skips gitignored files, so a new source file can silently miss the patch |
| 7 | `SKILL.md` names `swe-toolkit` and documents `run_skill_script(skill_name=..., file_path=..., args=[...])` | the old text used `skill_name="swe_toolkit"` and `script_path=`, which do not exist |
| 8 | `bootstrap.py` deleted | it `rglob`ed `/` and was unreferenced |

**Measured.**

- `locate` on `audit_snapshots/fastapi_14371` (1,279 `.py`): **3.0–3.9 s warm**, 10.9 s cold
  (was 13.5–25.7 s). `--budget 1` returns `STATUS: PARTIAL (indexed 732/1279 files in 1.3s)`
  with `fastapi/_compat/v2.py` still rank 1 — no more empty `DEGRADED`.
- `tools/audit_locate.py` over the 7 snapshots: **hit@1 5/7, hit@3 7/7, hit@5 7/7**,
  median 3.19 s, max 6.87 s. `rich_3470` moved from rank 10 to rank 2 and `fastapi_15280`
  holds rank 2. Tests occupy 0 of the top 3 in every task.
- `TEST:` suggestion is correct on 7/7: `test_schema_compat_pydantic_v2`, `test_fastapi_cli`,
  `test_parsers`, `test_adapters`, `test_requests`, `test_text`, `test_progress`.
- `verify` was exercised on 8 fixtures: clean tree → `FAIL empty`; untracked source → `OK`;
  `.orig` → `FAIL stray`; protected edit → `FAIL protected`; gitignored new `.py` →
  `PARTIAL ignored` with the `git add -N -f` hint; after `add -N -f` → `OK`; pytest green →
  `OK`; pytest red → `FIRST FAILURE: tests.test_core::test_a: assert 1 == 2`.
- The ADK execution path was emulated exactly (materialize `scripts/*.py` into a temp dir,
  `chdir`, `sys.argv`, `runpy.run_path`): `locate` and `verify` both return their contract.

**exp13 prompt.** The `## TOOLKIT` block is replaced by 418 chars: one `run_skill_script`
call with `skill_name="swe-toolkit"`, `file_path="scripts/swe.py"`,
`args=["locate","--issue",...]`; no `find /`, no `script_path`, no `--root`, and the text
says to obey `NEXT:` and never call `locate` twice. Everything above the block is exp05
verbatim; the trailing `## The issue` + `{problem_description}` stays because
`tools/verify_bundle.py:107-116` requires it, so E1's baseline is
`ckpt/bundles/exp05_patch_integrity`, not the scored zip. The first draft of the block was
1,034 chars; it was cut to 418 after measuring the hidden cost below.

**The skill toolset is not free, and that is the main risk in E1.**
`SkillToolset.process_llm_request` (`skill_toolset.py:1061-1083`) appends
`_DEFAULT_SKILL_SYSTEM_INSTRUCTION` (~1,250 chars) plus an `<available_skills>` XML block to
the system instruction on **every** request, and adds four tool declarations
(`list_skills`, `load_skill`, `load_skill_resource`, `run_skill_script`). So E1's real prompt
delta is ~1,800 chars (~450 tokens) plus four JSON tool schemas — not 418 chars. `exp08`
added 554 chars of prose with no new tool and scored 0.17 vs 0.20, which is within noise but
the direction is consistent. E1 therefore trades ~450 tokens of context and 4 tool
declarations for one localization call. That trade has to show up per task, not on the LB
alone.

The ADK preamble also tells the model it "MUST use `load_skill`" before proceeding, and it
is appended *after* our instruction. The prompt now works with that instead of fighting it:
`load_skill` returns `SKILL.md`, which carries the exact call shape and the status codes.
The old "do not call `load_skill` first" line was removed for that reason.

**Gates.** `verify_bundle.py --bundle ckpt/bundles/exp13_swe_toolkit` → `ALL CHECKS PASSED`;
`build_notebook.py` + `verify_notebook.py` → `ALL CHECKS PASSED`; artifact sha256
`31de5b898d72d2455abe7d8d8668bed0a0cf883492b08684222fb430365b3fb0`, 19,716 bytes, 10 members.
The four copies (`skills/swe-toolkit/`, `ckpt/bundles/exp13_swe_toolkit/`,
`bundles/exp13_swe_toolkit/`, `kaggle_work/.../bundles/exp13_swe_toolkit/`) are
hash-identical.

**Still open before E1.** The T7 gate wants hit@3 ≥ 60% on the 30 single-file never-solved
tasks. Only 7 snapshots are extracted, so 7/7 is the available evidence, not the gate. The
competition dataset holds 129 snapshots (21.5 GB); downloading the 30 costs roughly 2–4 GB
and is the next step. No E1 submission until that number exists.

## 2026-11-01 — exp13 readiness check: gate regression found and cleared, engine wired (no submission)

A submission-readiness pass over `ckpt/bundles/exp13_swe_toolkit` found the bundle **not ready**.

**Regression: Gate 2 failed with 2 checks.** `[FAIL] prompt has problem_description` and
`[FAIL] prompt ends cleanly` — the T2 prompt-hygiene change had removed the trailing
`## The issue` + `{problem_description}` tail, but `tools/verify_bundle.py:106-116` requires
the placeholder to be present and to be the last thing in the file. The removal is
competition-safe in isolation (`agent_runner.py:379` sends the problem statement as the first
user message; the scored exp05 artifact carries no placeholder), but it breaks this repo's own
non-negotiable gate, so the tail was restored (git checkout) in the ckpt and kaggle_work
copies. All three exp13 bundle copies (`bundles/`, `ckpt/bundles/`, `kaggle_work/.../bundles/`)
are now byte-identical (system.md sha256 a4d62ab4..., 5,941 raw bytes).

**Discovery: the upgraded locate engine was never in any bundle.** The T2/T6 edits to
`_index.py` / `_verify.py` existed only in the repo-root `skills/swe-toolkit/scripts/`; all
three bundle copies still carried the pre-session engine. On top of that, the claimed
walk-sort demotion had silently never been written (an inline replace printed success but
never saved the file), and one explanatory comment above `error_strings` had been deleted as
an edit side effect. Fixes, all in the repo copy and then synced byte-identically into the
three bundle copies (`_index.py` sha256 9e1b65f4..., `_verify.py` 37a08024..., `swe.py`
582aaa06..., SKILL.md 5f4bde90...):

- `_index.py:330` scan sort is now
  `files.sort(key=lambda f: (0 if not is_test_path(str(f)) else 1, -path_weight(str(f)), str(f)))`,
  i.e. source files are always visited before test modules and vendor paths inside one
  priority class. Note the `str()` wrappers: `walk()` yields `Path` objects and the old key
  relied on them too; a bare `is_test_path(f)` raises AttributeError.
- the `error_strings` comment was restored.

**Kernel V2 artifact is not Gate 4 material for any current bundle.** The pushed kernel
`narisettichaitanya/gemma4-devagent-exp13-swe-toolkit-v2` is COMPLETE, DONE_OK, no traceback,
sha256 f30e84b34d8997df... — but it was built from an older bundle revision: 16 members with
skill dirs in BOTH spellings (`skills/swe-toolkit/` and `skills/swe_toolkit/`), a
`bootstrap.py`, and no script hash matching any on-disk copy. Any future submission needs a
fresh kernel push, and Gate 4 (hash equality against the local build) can only be closed
against that new push.

**Gates after the fix.** `verify_bundle.py --bundle ckpt/bundles/exp13_swe_toolkit` —
`ALL CHECKS PASSED`, pack digest `0ece5e7ec92bf049`; `build_notebook.py` +
`verify_notebook.py` on `build/exp13_swe_toolkit.ipynb` — `ALL CHECKS PASSED`, artifact
sha256 `0ece5e7ec92bf049c478bc8f6ea0fcd12438d02455f665c5f0f1d428d2fd2451`, 20,159 bytes,
10 members, single kebab-case skill, tools=10 (compile_submission), model 31B. The
notebook-built archive reproduces the pack byte-for-byte, so Gate 2 and Gate 3 agree.

**Empirical check in flight.** A 5-snapshot smoke test of the upgraded engine ran clean
(no exceptions); ranks moved within local noise (rich_2943 3 -> 2, fastapi_11194 3 -> 5).
A full 129-task re-benchmark against the exact engine shipped in the bundle is running and
will be recorded when it lands (`%TEMP%/opencode/t6_results_v3.json`).

**Submission state.** No submit, no kernel push. E0 57836949 (2026-10-31) is still PENDING,
which blocks the next submission (maxPendingSubmissionsPerTeam: 1). Next submission requires
an explicit yes from the user, after the fresh kernel push passes Gate 4.


## exp13 dual-track readiness audit (2026-11-01; offline instrument; no submit, no push)

**Trigger.** User checklist + pre-flight discrepancy: the Phase-5 report was byte-identical
to the baseline, and one column was the all-gold-in-top-10 metric mislabeled as `@10`
(making `@10 < @5`, which is impossible for any-based Recall@K).

**Engine attribution (measured).** `git diff 2b7cd84..643c6f4 -- _index.py` is 26 lines, not
"line 332 + a comment": (1) bare issue identifiers appended to `paths`, each worth +30.0 on
a path-substring match in score_candidate; (2) high_tokens dropped `modules`; (3) scan sort
source-first, while ranked_files/ranked_syms had no explicit tie-breaker (equal scores
resolved by scan order). Controlled A/B on the 23 moved tasks: reverting only line 332
reproduces current ranks 23/23 (walk-sort moves nothing). Second 28-sample A/B: no-bare-ids
hit@5 = 0.750 > base 0.679 > +8 variant 0.643 > +30 variant 0.571. The bare-id rule helps
rich and displaces gold on fastapi generic-word issues.

**Full 129-task locate runs** (see docs/FINAL_HARNESS_COMPARISON.md, section 1):
- base 2b7cd84:  @1 0.419  @3 0.628  @5 0.713  @10 0.829  zero .171
- v3 (643c6f4):  0.419  0.628  0.729  0.822  zero .178 (55 ranks moved vs base)
- **v4, shipped (bare-id rule removed + deterministic tie-breakers on both sorts):
  0.419  0.651  0.744  0.829  zero .171; vs base 16 tasks better, 6 worse (16+6=22 moved).**

**Track fixes shipped in `_verify.py` / `swe.py` / `_index.py` / `prompts/system.md`.**
verify() rmtree(<root>/skills) removed (Track A item 3 overturned by wheel evidence
google-adk 1.36.1 skill_toolset.py:617-709: skills materialize into a self-cleaning
tempfile.TemporaryDirectory, never /workspace; run_skill_script returns untruncated stdout
- so the only real guard is swe.py). untracked_files() stops hiding skills/ untracked
files; stray_files() flags skills/ paths; cap() OUT_CAP 4800 to 3500 with middle truncation
so STATUS/NEXT/TEST/FALLBACK contract lines survive; prompt gains ANCHOR-after-locate/edit
lines, call-21 early exit, call-24 circuit breaker.

**Gates on the final state.** Gate 1 check_resources: exit 0, all required resources
present (E0 57836949 still PENDING, which blocks any submission). Gate 2
verify_bundle --bundle ckpt/bundles/exp13_swe_toolkit: exit 0, ALL CHECKS PASSED. Gate 3
build_notebook + verify_notebook: exit 0, ALL CHECKS PASSED, artifact
sha256 c9135bcb969f91c20ada77f999c12b05c603ceaaeda4d85f6d5c155ba543c415, 21,285 bytes
(replaces the stale 0ece5e7ec92bf049-era record). Empirical suite 18/18 asserts;
adversarial suite 9/9 (tools/test_verify_8_scenarios.py scenario 9 expectation updated to
the report-dont-delete contract); all 3 engine files byte-identical across the 4 bundle
copies via tools/sync_exp13.py.

**No submission; no kernel push.** Gate 4 kernel refresh is now unblocked and awaits
explicit approval (kernel-only, not a submission): re-splice build/exp13_swe_toolkit.ipynb
into the kernel dir, push, confirm real slug, pull output, assert sha256 == c9135bcb...
(docs/TASKLIST.md T7).

**Gate 4 closed (2026-11-01, kernel-only).** `run_skill_script` schema re-verified against
ADK 1.36.1 from the compiled `swe_agent` (properties args/file_path/positional_args/
short_options/skill_name, required [skill_name, file_path]; prompt + SKILL.md use exactly
skill_name/file_path/args-as-list - 100% match, no INVALID_ARGUMENTS risk). Kernel
narisettichaitanya/gemma4-devagent-exp13-swe-toolkit-v2 version 2 pushed; run COMPLETE with
DONE_OK at 14.4 s, no traceback; 10 members, single kebab-case skill, no adapters. Pulled
submission.zip sha256 c9135bcb969f91c20ada77f999c12b05c603ceaaeda4d85f6d5c155ba543c415 ==
local Gate 3 build (docs/TASKLIST.md T7). The audit rows "no kernel push" line is superseded
by this postscript. No competition submission was made; E0 57836949 still PENDING and rule 1
requires an explicit yes anyway.

**Gate 4 closed for e4b_v3 (2026-11-01, kernel-only, no submission).** Bundle
`tracks/e4b_small/bundles/e4b_v3_swe_toolkit` pushed as kernel
`narisettichaitanya/g4-e4b-small-agent-submit` version 7. Run COMPLETE with DONE_OK at 11.8 s,
0 tracebacks, 0 errors. Declared model strictly `gemma-4-e4b-it-qat-w4a16-ct` (zero 31B
fallback, confirmed in the kernel log). Pulled `submission.zip` sha256
`97c25136ca305a79e8e5ee3b559a67bfe91c3ba15dee9267ab6bd93f51adcc67` == local Gate-3
artifact byte-for-byte (19,095 B, 10 members). Gate-3 notebook verification: ALL CHECKS PASSED
(single base model E4B, real harness compile, unpacked 48,425 B). Pulled artifacts live under
the gitignored `tracks/e4b_small/runs/`. No competition submission (rule 1; E0 57836949
still PENDING).

**Task 2 v6 measured (2026-11-01, no engine change).** `%TEMP%/opencode/symrank_v6.py` over
129 tasks: file-rank regressions 0 (107 unchanged, 2 newly captured at rank 12, none
worsened). Symbol hit@1/3/5/10: v4 0.157/0.231/0.306/0.364 -> v6 0.215/0.331/0.405/0.463
(+0.058/+0.100/+0.099/+0.099). Ablation: v5A (top-12) 0.190/0.322/0.397/0.488; v5AB
(+member boost) 0.215/0.322/0.388/0.455; v6 (+call-site) 0.215/0.331/0.405/0.463. Re-rank
cost 1.310 s median / 2.589 s max (vs 0.235/0.534 for v5), still inside the 20 s locate
budget. Gold-file-in-top-12 scope 106/121 (0.876). Strict all-gold on multi-file tasks:
0.079/0.079/0.158 at @3/5/10 (vs any-gold 0.763/0.816/0.895) - the central limitation of
single-pass retrieval. Per-task JSON: symrank_v6_results.json.

**Paper track draft updated (2026-11-01).** `docs/PAPER_TRACK_DRAFT.md` now carries the
file-recall ablation (base/v3/v4), the any-gold vs strict all-gold paradox, the intra-file
symbol progression (v4/v5/v5A/v5AB/v6), the verified ADK 1.36.1 runtime mechanics, the
cross-scale binomial SE model (SE ~0.052-0.054 at N=58) and the skill-offloading
rationale, plus verified kernel artifact hashes. Word count ~2,900 (under the 3,000 limit).

**Score-prediction doc written (2026-11-01, no submission).**
`docs/SCORE_PREDICTION_AND_ROADMAP.md`: exp13 v4 (`c9135bcb...`) public-LB point
prediction ~0.21, 90% CI [0.12, 0.30] at n=58 (locate R@5 0.744 x the exp05-anchor
located-to-passed multiplier 0.20/0.713=0.28; SE=0.054, so deltas < ~0.06 stay
unresolved). e4b 0.05 flat-line diagnosed (edit fidelity, low-precision run_command
exploration, compaction state loss); skill-chain prediction for
`e4b_v3_swe_toolkit`: 0.09-0.13, CI [0.04, 0.16]. Every number in the doc is
measured on the 129-task instrument or pinned to a scored anchor.

**Task 2 measured - v5 intra-file symbol re-ranker prototype (2026-11-01, no engine
change, no submission).** `%TEMP%/opencode/symrank_v5.py` imported the locked
`swe-toolkit/scripts/_index.py` read-only and re-ranked symbol spans over the top-8
locate files on all 129 tasks (607 s): file-rank equality 0/129 mismatches, so
File R@3 0.651 / R@5 0.744 carry over intact. Symbol hit@1/3/5/10 on the 121
gold-symbol tasks: v4 shipped 0.157/0.231/0.306/0.364 -> v5 span ranker
0.190/0.322/0.388/0.488 (+0.033/+0.091/+0.082/+0.124). Scope ceiling measured: only
101/121 gold-symbol tasks have a gold file within top-8; v5 in-scope hits are
0.208/0.366/0.446/0.564; all 359 gold qualifiers are bare names. Re-rank cost
+0.235 s median / +0.534 s max (warm cache) inside the 20 s locate budget. The
0.50 hit@3 target was not reached (0.322); follow-up levers are member-over-container
weight rebalance, a gold-symbol-context term, and top-12 file scope. Any engine
change lands only as exp14 (one isolated diff) after user approval plus a
benchmark-equality rerun; per-task JSON kept in the temp dir.

**Task 3 done - e4b_v3_swe_toolkit staged and fully verified (2026-11-01, no
submission).** `tracks/e4b_small/bundles/e4b_v3_swe_toolkit`: 10 files, 48,425 B;
model `gemma-4-e4b-it-qat-w4a16-ct` only; sampling 0.1/0.95/8192/4096/true;
eval 240/35/8/80; prompt 2,104 chars derived from e4b_v2 by exactly three workflow
replacements (locate cold-call first, grep demoted to fallback, verify cold-call +
fast exit); `{problem_description}` clean tail, exactly one brace pair; skill files
hash-pinned byte-identical to the locked v4 engine (exp13 artifact AND repo
source). Verification stack: `tracks/e4b_small/verify_bundle_e4b_v3.py` ALL CHECKS
PASSED; real harness `tools/verify_bundle.py --bundle ...` ALL CHECKS PASSED
(exit 0; declared model exactly ['gemma-4-e4b-it-qat-w4a16-ct'] - zero 31B
fallback; compile root swe_agent tools=7 = 6 harness + SkillToolset; E4B
wheelhouse-registry [WARN] is the documented non-blocker); compiled
`run_skill_script` declaration PASS (required [skill_name, file_path], args list,
no command). Kernel push deliberately deferred while E0 57836949 is PENDING; a
kernel run is not needed for this task per user scoping.

## 2026-11-09 — leaderboard catch-up + exp_think1024 submitted (ref 58149803)

First, four scored entries that landed after 2026-11-01 without a ledger row (recorded now,
from the live API; also in docs/LEADERBOARD_STATS.md and commit 1f6ca99):

| ref | date (UTC) | bundle / artifact | score | interpretation |
|---|---|---|---|---|
| 57836949 | 2026-10-31 | E0 control: byte-identical exp05 resubmission (sha256 2ba7f9b1…) | 0.17 | **exp05's 0.20 did not reproduce** — the identical artifact scored 0.17, so exp05's 0.20 was a high draw of pooled 31B noise |
| 57889741 | 2026-11-02 | e4b_v4_swe_toolkit (E4B + swe-toolkit v4 engine, 7 tools) | 0.05 | E4B flat-line persists even with the deterministic skill offload → the skill-offload prediction (0.09–0.13) is falsified; E4B line closed at 0.05–0.06 (four submissions) |
| 57933618 | 2026-11-03 | exp14_lean_toolkit (31B + swe-toolkit skill, 9 tools, lean prompt) | 0.15 | −1 task vs the 0.17 cluster → within noise |
| 58096981 | 2026-11-07 | exp_sampling: temp 1.0 / top_p .95 / top_k 64 off exp05 | 0.13 | −2 tasks → within noise; decoding change unresolved |

Converged-config 31B pool is now eight scored runs (0.20, 0.17×5, 0.15, 0.13 ⇒
≈77/464 = 0.166; pooled SE ≈ 0.05/√8 ≈ 0.018). No scoring loop exists locally; public-LB
deltas ≤2 tasks remain statistically unresolvable (docs/AUDIT_E4B_AND_ANCHOR.md).

## exp_think1024 — thinking_budget 4096 → 1024 (single change off exp05 anchor) — SUBMITTED

- **Origin.** Kilo Code branch `kilo/steep-blossom-hio` (commit `54c63bf`);
  `git diff --no-index` vs `kaggle_work/.../bundles/exp05_patch_integrity`: exactly
  1 file, 1 insertion, 1 deletion — `configs/sampling.yaml`
  `thinking_budget: 4096 → 1024`. Synced to
  `kaggle_work/gemma-4-developer-agent/bundles/exp_think1024` and root-`bundles/exp_think1024`.
- **Hypothesis (mechanism).** The thinking budget is engine-enforced per vLLM call
  (`ThinkingTokenBudgetLogitsProcessor`), not prompt text: 1024 caps thought tokens
  per call, leaving more of the 8192-token response for action text, and (with
  `include_thoughts: true`) grows the per-turn history less → fewer compaction events
  at the 14,336-token threshold. Risk: less deliberation on hard tasks.
- **Payload proof (STOP GATE: not triggered — positive).**
  `scripts/probe_thinking_budget.py` (artifacts `build/probe_payloads/*.json`,
  sha256 exp_think1024 `7BEAE700…`, exp05 `060503DF…`): the outgoing vLLM request
  carries top-level `extra_body.thinking_token_budget = 1024` (`enable_thinking: true`),
  identical to exp05's payload except that field. vLLM 0.19.1 enforces it
  (`protocol.py:183/519`, `builtin.py:294/494-552`) independently of max_tokens.
- **Gates.** Gate 1 (2026-11-09) all required resources present, docs hashes unchanged.
  Gate 2 `verify_bundle.py --bundle bundles\exp_think1024` ALL CHECKS PASSED
  (pack digest `5d80bac751b9ae22`, compile root swe_agent, model 31B, tools=9).
  Gate 3 `verify_notebook.py` ALL CHECKS PASSED; `submission.zip` sha256
  `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082` (3,403 B).
  Gate 4: kernel `narisettichaitanya/gemma4-devagent-exp-think1024` v1 pushed 2026-11-09,
  status COMPLETE, log ends `DONE_OK`, no traceback; pulled output
  (`kaggle_work/.../runs/exp_think1024/`) byte-identical to the local build.
- **Submission.** User pre-authorized a conditional submission (payload proof positive +
  Gates 2–3 pass); conditions verified: nothing PENDING, nothing submitted
  2026-11-09 UTC before the call. **Ref 58149803**, 2026-11-09T03:27:31Z, status pending,
  message "exp_think1024: single change off exp05 …", artifact sha256 `5d80bac7…`.
- Tool note: `kaggle competitions submit` (CLI 2.2.4) → HTTP 400 (the JSON-vs-multipart
  trap documented in `tools/kaggle_rest.py`; field-by-field body silently ignored);
  submitted successfully via `tools/kaggle_rest.py submit --competition ... --kernel ... --version 1 --filename submission.zip`.
- **Pre-registered interpretation** (public LB = ~58 tasks; 1 task ≈ 0.017; SE ≈ 0.05;
  pooled 31B anchor ≈ 0.166): score ≥13/58 (≈0.22+) real win; 9–12 (0.155–0.207) null;
  ≤8 (≤0.138) regression.
- **Docs.** Phase 1+2 audit: `docs/ENV_AUDIT.md` (wheel inventory, `--sandbox subprocess`
  runner, 5/5 harness-trap repros, payload proof). Handover: `docs/SESSION_FINAL.md`.
  Paper: `docs/PAPER_TRACK_DRAFT.md` §2.2 now carries the engine-enforcement finding and
  the E0-control statistical update (2,997 words, under the 3,000 limit).


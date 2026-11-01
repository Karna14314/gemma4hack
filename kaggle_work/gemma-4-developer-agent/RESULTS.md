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

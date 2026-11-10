# LEDGER — e4b-v2

## Baseline bundle (57777888)
- Bundle: tracks/e4b_small/bundles/exp11_e4b
- Model: gemma-4-e4b-it-qat-w4a16-ct
- Score: 0.06 (ref 57777888, complete)
- File hashes:
  - agent.yaml: 2d25f715647c996542528d843cc6c9fdb7938aee86bcf559143d47ada20128fd
  - configs/sampling.yaml: 571a934e89911734927533f1d36cbcc7b8d493592febe63b217e911cf7ed4926
  - eval_config.yaml: 916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531
  - prompts/system.md: ab4fda662643c26f920b106986ac9858f9e041e8c6d0a25f74255aff635c663d

## e4b-v2 bundle
- Bundle: tracks/e4b_small/bundles/e4b_v2
- Diff vs baseline (57777888): only configs/sampling.yaml (temperature 0.2 -> 0.1) and prompts/system.md (rewritten, 2440 chars). agent.yaml and eval_config.yaml byte-identical.
- Unified diff recorded in commit/PR.

## Submission
- Ref: 57806053
- Kernel: narisettichaitanya/g4-e4b-v2-small-agent-submit v1
- Bundle sha256 (submission.zip): 5881be16cb3ba6761b4b2d724510ffbb44c37a47c9b5a5f66d1701fc0a5b312d
- Time: 2026-10-30 (pending scoring)
- Status: pending

## Gate results
- verify_bundle_e4b_v2.py: ALL CHECKS PASSED (prompt 2440 chars)
- verify_notebook_e4b_v2.py: LOCAL E4B NOTEBOOK VERIFICATION ALL CHECKS PASSED
- Final gate one-liner: tested in scratch repo covering no changes, changed .py, new untracked file, new ignored file, syntax error, filename with spaces, zero .py changes, only test/config files changed. All passed.

## e4b-v4 submission (57889741)
- Bundle: tracks/e4b_small/bundles/e4b_v4_swe_toolkit
- Kernel: narisettichaitanya/g4-e4b-v4-small-agent-submit v1
- Submission ref: 57889741
- Time: 2026-11-02T00:50:17Z
- Status: PENDING (polled once)
- submission.zip sha256: 8a179b8af032ca97dbc64f54f0dbd3721434a10765e5c01167f36250822329a0
- submission_notebook.ipynb sha256: 0b1a0a7217cb2eb5cd20ed7bdfc13e11470f54db99bc20ac5741b9085ce971f9
- Bundle file hashes: see docs/SUBMISSION_RUN_e4b_v4.md

## exp_think1024 submission (58149803) — 2026-11-09

- Bundle: `kaggle_work/gemma-4-developer-agent/bundles/exp_think1024` (= root `bundles/exp_think1024`), synced from `origin/kilo/steep-blossom-hio` (commit `54c63bf`); single change vs exp05 (2ba7f9b1…): `configs/sampling.yaml` `thinking_budget: 4096 → 1024` (git diff --no-index: 1 file, 1+/1−)
- Kernel: `narisettichaitanya/gemma4-devagent-exp-think1024` v1 (scriptVersionId 367147645), CPU-only, status COMPLETE, DONE_OK, no traceback
- Submission ref: **58149803**, 2026-11-09T03:27:31Z, status pending (submitted via `tools/kaggle_rest.py submit` — the `kaggle` CLI path returned HTTP 400, see multipart trap)
- submission.zip sha256: `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082` (3,403 B)
- Gates: Gate 1 pass (2026-11-09); Gate 2 ALL CHECKS PASSED; Gate 3 ALL CHECKS PASSED; Gate 4 COMPLETE + pulled hash == local build
- Payload proof: `extra_body.thinking_token_budget=1024` reaches the outgoing vLLM request (`scripts/probe_thinking_budget.py`, artifacts `build/probe_payloads/`); enforcement verified in vLLM 0.19.1 (`ThinkingTokenBudgetLogitsProcessor`)
- Hypothesis + pre-registered rule recorded in `kaggle_work/gemma-4-developer-agent/RESULTS.md` (2026-11-09 section): ≥13/58 real win, 9–12 null, ≤8 regression vs pooled 31B ≈ 0.166
- Session summary: `docs/SESSION_FINAL.md`; phase audit: `docs/ENV_AUDIT.md`

## exp_think1024 root cause — Kaggle-side ERROR, not a bundle defect (2026-11-10)

Re-checked after the submission flipped from `pending` to **`error`**. The failure is **not** in the
notebook, the bundle, `adk_submission`, or `thinking_budget: 1024`.

| check | observed |
|---|---|
| submission `58149803` | `status=error`, `publicScore` empty, **`totalBytes=0`** |
| error text | `A system error. Please try resubmitting to resolve the error and contact Kaggle Support if it persists.` |
| kernel status (`kaggle_rest.py status`) | `complete`, `failureMessage` empty |
| kernel log tail | `all independent checks passed` → `wrote /kaggle/working/submission.zip (3,403 bytes)` → `submission.zip is written and verified` → **`DONE_OK`** |
| tracebacks in log | **0** (scanned all 65 log entries for `Traceback`/`Error`) |
| pulled `submission.zip` sha256 | `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082` |
| local Gate-3 build sha256 | `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082` — **byte-identical** |
| `adk_submission` involvement | **none at kernel time** — the notebook only writes the zip; the harness compiles it later |

**Conclusion.** The artifact the organizers received is byte-for-byte the one Gate 3 validated. The
scorer's own ingestion/scoring pipeline failed (`totalBytes=0` means it never registered the file).
There is no bug in the notebook to fix and nothing to change in the bundle before resubmitting the
same configuration. The `thinking_budget: 1024` hypothesis is **untested**, not falsified.

**Operational consequence.** An `error` submission is not `pending`, so it does not consume the
`maxPendingSubmissionsPerTeam: 1` slot. The daily quota (`maxDailySubmissions: 1`) is still spent
for 2026-11-09. The fix is to resubmit, not to rebuild.

**Process bug found while diagnosing.** `tools/kaggle_rest.py cmd_submissions` printed
`json.dumps(result)[:4000]`, which silently truncated the queue at the 5th entry and is why the
`error` status went unnoticed for a day. Raised to `[:400000]`; the full queue is now visible
(`research/public_intel/show_subs.py`).

## exp15_zero_schema_hybrid (bundles/exp15_zero_schema_hybrid) — Gate 2+3 passed, unscored
- Bundle: bundles/exp15_zero_schema_hybrid
- Model: gemma-4-31b-it-qat-w4a16-ct
- Clone of: kaggle_work/gemma-4-developer-agent/bundles/exp05_patch_integrity (single change: drop 3 graph tools get_code_neighbors/search_similar_code/get_code_subgraph -> strictly 6 base tools: run_command, read_file, edit_file, write_file, get_status, submit_patch)
- Sampling: temperature 0.2, top_p 0.95, max_output_tokens 8192, thinking_budget 4096, include_thoughts true
- Eval: max_time_minutes 8, max_tool_calls 28, max_turns 80, timeout_seconds 240
- Prompt: exp05 core trimmed to 4792 chars (<= 4800); adds 1-line Loop-Breaker & Anti-Compaction rule (`STATE: <file>:<line>` before tool calls; never repeat identical run_command/read_file); upgraded pre-submit stdlib verification one-liner (ast.parse() all modified .py + git status --short + git add -N -f untracked .py; ignores missing inline_snapshot/dirty_equals)
- Rationale: exp05 (6-tool-equivalent, no SkillToolset) scored 0.20/0.17 while exp14 (31B + swe-toolkit skill, 9 tools) scored 0.15 — SkillToolset injects 4 extra schemas per turn and burns 2-4 turns on skill invocation; schema tax + edit fidelity dominate.
- File hashes:
  - agent.yaml: 6ad913b0c0cb67d669116a4074d7b520b3a69c8d5aa960b6abe51f9850b45227
  - configs/sampling.yaml: 571a934e89911734927533f1d36cbcc7b8d493592febe63b217e911cf7ed4926
  - eval_config.yaml: 916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531
  - prompts/system.md: ea5670175035217906bbf73c91e58f5360d07d32c042f3cdf1d01bbc0621d7c5
- Gate 2 (verify_bundle --bundle bundles/exp15_zero_schema_hybrid): ALL CHECKS PASSED
- Gate 3 (build_notebook --bundle ... --out build/exp15_zero_schema_hybrid.ipynb + verify_notebook): ALL CHECKS PASSED
- submission.zip sha256: 7219eb5c85446df4eae29fc0f5d4003691b43d82aba9450dc3fff8b66a8e153b (3,199 bytes)
- Notebook: build/exp15_zero_schema_hybrid.ipynb

# RESULTS — gemma-4-developer-agent

Append-only ledger. One row per experiment, including failures.

## Status

**Nothing submitted yet.** No leaderboard score exists for this entry. Everything below is
offline engineering and validation plus clean Kaggle kernel runs, not measurement. There is
no local way to measure resolution rate: the real evaluator needs 4x L4 GPUs, the 31B QAT
weights, and the container image.

| exp | date | change vs base | metric | status | notes |
|---|---|---|---|---|---|
| setup | 2026-10-03 | research + harness audit | n/a | PASS | 30/30 offline checks pass, including the real `adk_submission.compile_submission` |
| notebook | 2026-10-03 | sections + builder + end-to-end verifier | n/a | PASS | notebook executes offline; artifact passes the real compiler |
| exp01 v1 | 2026-10-03 | kernel push, version 1 | kernel run | PASS | COMPLETE, no traceback, `submission.zip` byte-identical to the local build |
| exp01 v2 | 2026-10-03 | added explicit `DONE_OK` sentinel | kernel run | PASS | COMPLETE, `DONE_OK` once, no traceback, same digest |

**exp01 is ready to submit** and is waiting on an explicit go-ahead. Kernel
`narisettichaitanya/gemma4-devagent-exp01` version 2, file `submission.zip`, digest
`d0c8959dfb3951756872ac49a46ff0aaaf163d7a9f4596db78fb463f2badeb95`.

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

1. Submit exp01 (kernel version 2) once approved, then wait out the scoring rerun.
2. Do not spend a second submission on an unverified bundle; one submission per day.
3. After the first score, test exactly one isolated change per submission, ranked in
   `HANDOFF.md`.
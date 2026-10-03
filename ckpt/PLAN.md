# PLAN — gemma-4-developer-agent

## The one-sentence strategy

The model is fixed (`gemma-4-31b-it-qat-w4a16-ct`, no adapters, no fine-tuning), the tasks come
from unseen repositories, and the whole run must fit in 12 h for ~120 sequential tasks. So the only
levers are **structural hygiene** (do not waste the context window, do not waste wall clock, never
lose the patch) and **prompt-level method** (a disciplined grep → read → edit → verify → submit
loop with an explicit time budget). Everything else is noise-fitting.

## Ranked design decisions, each with its mechanism

| # | Decision | Mechanism / evidence | Expected effect |
|---|---|---|---|
| 1 | **Zero LoRA adapters, no `adapter:` keys** | any adapter forces vLLM to reserve 8 LoRA slots @ r128, collapsing KV cache from ~46k to ~7.6k tokens; the starter kit's two adapters are also all-zero no-ops | large: removes the main context-starvation failure mode |
| 2 | **`eval_config.yaml` with `max_time_minutes: 4`, `max_turns: 80`, `timeout_seconds: 120`, no `max_tool_calls`** | 12 min/task → *Notebook Exceeded Allowed Compute*; 4-5 min/task completes. `max_time_minutes` measures only agent-loop time, so a 4 min cap still allows ~6.5 min wall per task → ~13 h worst case, and far less in practice since most agents finish early | large: avoids a hard zero from exceeding compute |
| 3 | **`include_thoughts: false`** (thinking off), `max_output_tokens: 8192`, `temperature: 0.2`, `top_p: 0.95`, `top_k: 40` | every published scoring notebook runs thinking-off; thoughts were not preserved between tool calls in the shipped vLLM, so the model re-derived them and burned output tokens; `max_output_tokens` > ~35% of the 32 768 context is flagged as harmful | medium-large: more prompt room and more turns per minute |
| 4 | **Prompt forbids `search_similar_code`; tool left declared** | one call can return >100k chars of un-truncated source, overflow the context, raise an uncaught error and **discard an already-submitted patch**; declaring it costs nothing and avoids "model called a tool it does not have" if the harness's task prompt names it | large: removes the single most likely way to lose a finished task |
| 5 | **Coder root agent + read-only `code_analyzer` sub-agent via `agent_tool`, `skip_summarization: false`** | exploration reads stay out of the coder's context; `true` was measured to end the coder's turn every call and burn a nudge, `false` does not | medium: context hygiene, but contested (0.06 single vs 0.12 coder+analyzer is ~4 vs 7 tasks = noise) |
| 6 | **Prompt repeats the issue at the end of both instructions via `{problem_description}`** | ADK resends the instruction every turn; context compaction (threshold 14 336) drops tool outputs and summarises the original task message, so the issue would otherwise fade | medium: keeps the target alive through compaction |
| 7 | **Prompt mandates log-to-`/tmp` + `tail`** | `run_command` keeps only the first 5 000 chars and pytest's verdict is last | medium-high: makes verification actually usable |
| 8 | **Prompt mandates a "state card" of ≤100 words after localisation and after each verification** | compaction retains model text, not tool output; a plain-text card is the only thing guaranteed to survive | medium |
| 9 | **Prompt gives an explicit `run_command` python fallback for `edit_file` failures** | `edit_file` is a 3-tier matcher that fails on non-unique or reformatted `old_string`; an exact `str.replace` in a python heredoc never fails for that reason | medium |
| 10 | **Prompt forbids bare `pytest`, forbids touching test files, and requires a `git status --short` cleanup before submit** | bare suites eat the whole budget; test/runner files are reset anyway; untracked scratch files in `/workspace` land in the patch | medium |
| 11 | **Prompt forbids `edge_type`, and treats graph tools as a weak hint only** | the shipped graphs contain only lowercase `calls` edges and **no async functions**, and the embeddings rank unrelated code highly | small but free |
| 12 | **No `skills/` directory** | skills are progressive disclosure of *content*; with unseen target repositories there is no repo-specific content worth disclosing, and `SKILL.md` only adds context | avoids risk, no expected loss |
| 13 | **Notebook is CPU-only, offline, and self-contained**, with a static validator and an automatic rollback to a minimal known-good package | the unmodified starter kit **errored** on submission; a code-competition notebook that fails yields 0. A rerun must not depend on pip, the wheelhouse, or any attached dataset | large: removes catastrophic failure modes |

## Validation plan (no local scoring possible)

Local scoring is impossible: the real evaluator needs 4x L4 GPUs, the 31B QAT weights, and Docker
images. So validation is layered:

1. **Real harness schema validation** — `adk_submission.validate_directory`,
   `swegemma.config.build_submission_limits`, `swegemma.models.discovery.validate_single_declared_model`
   and `adk_submission.compile_submission` are importable from the downloaded wheels on this
   machine. Run them against the built bundle. This is the authoritative check.
2. **Strict static validator inside the notebook** — mirrors the checks the published top notebooks
   use: exactly one root config, allowed extensions only, no symlinks, < 3 GiB, every `!include`
   target present, exactly one base model, root agent owns `submit_patch`, sub-agents own no
   writer tools, `{placeholder}` interpolation limited to `problem_description`.
3. **Notebook self-test** — execute the generated notebook end to end on Kaggle (Save & Run All)
   and confirm `/kaggle/working/submission.zip` exists, contains `agent.yaml` at the root, has no
   directory entries, and round-trips byte-identically.
4. **Fail-safe rollback** — if the strict validator rejects the challenger, the notebook emits the
   minimal fallback package instead of erroring. A 0.10-class package beats a 0.00 crash.

## Explicitly rejected

- **Fine-tuning a LoRA adapter.** No way to train and validate within this workflow, and any adapter
  costs ~38k tokens of KV cache. Strictly negative EV.
- **`max_time_minutes` above ~5.** Directly measured to exceed the 12 h compute cap.
- **Bare `pytest` discipline / full-suite sweeps.** Prompt-level ban instead.
- **Chasing LB deltas below 0.05.** 1 public task ≈ 0.017 and sampling is stochastic; per-submission
  comparison cannot resolve differences that size. Design choices must be justified by mechanism.
- **Attaching the wheelhouse to the submission notebook.** It would let the notebook call the real
  compiler, but it adds a multi-gigabyte input, a `pip install` that can fail, and minutes of
  runtime to a notebook whose only job is to emit a zip. The same validation runs offline here.

## Iteration order after the first submission

1. Submit the mechanism-justified package. Record the score.
2. Only if time remains, test **one** isolated change per submission (1/day): the highest-value
   candidates are (a) `include_thoughts: true` + `thinking_budget`, now that the hosts patched the
   scorer to preserve thoughts between tool calls; (b) dropping the analyzer sub-agent for a single
   agent; (c) raising `max_time_minutes` to 5.
3. Keep a scored anchor bundle in git so any regression can be reverted byte-for-byte.

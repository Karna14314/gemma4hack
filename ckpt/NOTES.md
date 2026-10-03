# NOTES — checkpoint 2 (v2 candidate)

## What changed vs checkpoint 1

| file | change | mechanism |
|---|---|---|
| `configs/sampling.yaml` | `include_thoughts: false` -> **`true`**, added `thinking_budget: 4096`, `max_output_tokens` 8192 -> **16384** | the reason thinking was disabled is fixed in the shipped harness |
| `eval_config.yaml` | `max_time_minutes` 4 -> **6**, `max_tool_calls` 80 -> **60** | `max_time_minutes` is a ceiling, not a cost |
| `prompts/system.md` | rewritten, 141 -> ~150 lines but far denser | research-backed mechanisms (below) |
| `package_source.py` fallback | thinking and budgets aligned with the primary | a rollback must not silently revert to thinking-off |
| `validator.py` | `max_time_minutes` ceiling 5 -> **10** | the 5 was our own guess, not a harness rule |

Built artifact: `submission.zip`, sha256 `57c9919f…`, 8,559 bytes, 6 members, `agent.yaml`
at the root. `tools/verify_bundle.py` 30/30 and `tools/verify_notebook.py` both
**ALL CHECKS PASSED**, including the real `adk_submission.compile_submission`.

## The four changes, and why each one is justified by the harness source

### 1. Thinking ON — the single largest untested lever

Checkpoint 1 ran with `include_thoughts: false`. That flag is not a soft default:
`adk_submission/resolvers/generation.py:292-300` checks it **first**, emits
`enable_thinking=false`, and strips both `thinking_budget` and `reasoning_effort`. So the
previous bundle was unambiguously, totally thinking-off on a reasoning model.

The original justification for turning it off was that vLLM discarded thoughts between
tool calls, so the model re-derived its reasoning every step and burned output tokens for
nothing. **That bug is fixed in the wheel we ship against.** `generation.py:66-74` now
mirrors `reasoning_content` into `reasoning` on assistant messages, installed by
`install_litellm_reasoning_patch()` at line 129, whose own docstring states it exists so
"vLLM<=0.21.x preserves prior thoughts across multi-step tool calls". The hosts' public
walkthrough confirms they patched the scorer for this.

Verified end to end, not assumed. Compiling a probe bundle through the genuine
`adk_submission.compile_submission` produces on the model object:

```
_additional_args = {'extra_body': {'chat_template_kwargs': {'enable_thinking': True},
                                  'thinking_token_budget': 4096}}
thinking_config=ThinkingConfig(include_thoughts=True, thinking_budget=4096)
```

`max_output_tokens` goes 8192 -> 16384 to make room. Against the 32768 window that still
leaves ~16k of prompt room, above the 14336 compaction threshold, so compaction still
engages rather than the run dying on a context-overflow HTTP 400.

### 2. `max_time_minutes` 4 -> 6

The previous setting was defended by "4 and 5 both completed in ~80 minutes total". That
argument conflated two clocks. From `swegemma/harness/agent_runner.py:435-442` the field is
applied as a single `asyncio.timeout` around the agent loop, and at line 635 the loop
`break`s the instant `context.patch_submitted` is set. So it is a **ceiling, not a target**:
a task the agent solves in two minutes never reaches it and costs nothing extra. Wall clock
is only spent on tasks that would otherwise be cut off mid-debug.

That matters because scoring is binary. A task killed by the timeout with a half-finished
edit scores exactly zero, the same as no patch. The ceiling therefore controls where the run
risks the 12 h total, not where it loses points.

The evidence that 4 was too tight: the published 0.12-scoring anchor in
`notes/pulled_txt/black-cat-swe-agent-pack-instinct.txt` asserts
`budget['evaluation']['max_time_minutes'] == 10`. Every published scoring configuration in
our notes is 5 or 10 minutes. Ours was the only one at 4, and we scored 0.05 against a
leaderboard floor of 0.15.

6 rather than 10 deliberately: it doubles the agent's working time while keeping a wide
margin under the 12 h cap, which also has to cover ~120 container setups and Phase 2
verifications. `swegemma/config.py` imposes **no** ceiling on this field — the 5-minute cap
was our own prior guess, and the validator now encodes 10, the value actually measured to
score.

### 3. Prompt rewritten around six researched mechanisms

Sources: SWE-agent (arXiv 2405.15793) ACI ablations, Agentless (arXiv 2407.01489), Moatless /
SWE-Search (2410.20285), OpenHands (ICLR 2025) microagents, and an empirical study of
harness design for coding agents (arXiv 2609.20804).

1. **Scratchpad at `/tmp/plan.md`.** The single highest-value change. Compaction is active in
   the scoring path at `token_threshold=14336`, `event_retention_size=5`, and **only the
   model's own text survives** — tool output is discarded. So the previous prompt's "write a
   100-word state card" instruction put the state somewhere that reliably gets dropped. A
   file in `/tmp` is immune to compaction, is never part of the patch, and costs no extra LLM
   call. The prompt now mandates creating it, re-reading it when lost, and updating it after
   each edit and test.

2. **`py_compile` after every single edit, stated as non-optional.** SWE-agent's ablation
   prices their lint guardrail at **-3.0 pp** without it. We cannot reject a bad edit the
   way their tool does, only detect one, but detection is what matters: a file that does not
   import is a guaranteed zero under binary scoring.

3. **"Never edit from memory of an old tool result."** SWE-agent's error analysis found their
   dominant edit bug is generating edits against *stale* file content from a more recent
   turn. With compaction dropping tool output, staleness is worse for us than for them, so
   the prompt now forbids it explicitly rather than leaving it implicit.

4. **Repository's own tests as the guard signal, not self-authored ones.** Agentless filters
   candidate patches with the repo's existing `PASS_TO_PASS` tests. A self-written proxy is
   trivially satisfiable and Goodharts. Reproducers are now scoped to confirming the bug
   *reproduced before* the fix, and explicitly given a `RESULT:` print marker so "printed
   nothing" is never ambiguous (SWE-agent lists that as failure mode #1).

5. **"Never page through search results."** SWE-agent's ACI ablation prices iterative
   `next`/`prev` search paging at **-6.0**, worse than having no search tool at all (15.7).
   The previous prompt said "never `find . -name '*.py' | head -500`" but did not forbid
   re-running searches with different arguments. Now it does, and prescribes `-l` then
   direct reads.

6. **The binary-scoring asymmetry, stated up front.** A wrong patch scores identically to no
   patch, so there is no downside to shipping a speculative fix. The prompt opens with this
   and closes with "never end without a change in the tree and without calling
   `submit_patch()`". SWE-Protégé's analysis identifies degenerative action looping as the
   dominant small-model failure, so this is paired with an explicit "two failed calls means
   change method, and at most two repair attempts, then ship the better one" rule rather
   than an open-ended retry loop.

Kept unchanged, because the harness source justifies each: no LoRA adapter (KV cache 46k ->
7.6k with any adapter present), `timeout_seconds: 300` (it also bounds the Phase 2 pytest
run, so lowering it can time out verification of a correct patch), the ban on
`search_similar_code` (5,000 chars shared across ten head-truncated results for a whole tool
call), the ban on `edge_type` (stored lowercase `calls`), the `git add -N -f` instruction for
`.gitignore`-swallowed new files, and `{problem_description}` as the only brace in either
prompt (ADK interpolates every `{token}` from session state).

## Deliberately NOT done, and why

These came out of the research and were rejected on mechanism, not taste:

- **`SequentialAgent` / `LoopAgent` pipeline** (Agentless hierarchical localisation, SWE-Search
  style loop). Genuinely the strongest structural idea available, and the research rates it
  high. Rejected because it changes the *root* agent class, and the harness builds the task
  prompt, budget gating and nudge loop around a root `LlmAgent` — `agent_runner.py` inspects
  `agent.instruction` and drives `runner.run_async` per turn. A non-LlmAgent root is exactly
  the kind of change that can only be validated by spending a submission, and we have one per
  day. Keep as the next experiment once a v2 score is known.
- **`ParallelAgent` fan-out for candidate patches.** Two agents editing one `/workspace`
  concurrently clobber each other, and the evaluator grades a single tree.
- **Patch majority voting / self-consistency.** Needs an AST-normalisation pipeline and 10-40
  candidates; impossible declaratively, and the one study that measured it found execution-
  grounded selection beats voting by 19-52 pp.
- **Higher `temperature` for diversity.** Heterogeneous prompting strictly outperformed
  temperature sweeps in the one study that compared them; diversity is better bought with a
  second written hypothesis, which the prompt now asks for.
- **`skills/` directory.** Unchanged from checkpoint 1: with unseen repositories there is no
  repo-specific content worth progressive disclosure, and `SKILL.md` would only add context.

## Local evaluation
Still impossible: the evaluator needs 4x L4 GPUs, the 31B QAT weights and the sandbox image.
What was verified offline:

| check | result |
|---|---|
| `tools/verify_bundle.py`, 30 checks incl. real `compile_submission` on both bundles | ALL CHECKS PASSED |
| probe bundle through genuine `compile_submission`, thinking flags read off the model object | `enable_thinking=True`, `thinking_token_budget=4096` |
| `tools/build_notebook.py` | 20 cells |
| `tools/verify_notebook.py`, notebook executed end to end offline | ALL CHECKS PASSED |
| `submission.zip` inspected: root `agent.yaml`, 6 members, no empty suffixes | OK, sha256 `57c9919f…` |
| brace audit of both prompts | only `problem_description` |

## Risk
One submission per day and no local scoring, so v2 is a **bundle** of changes rather than one
isolated variable. That is a deliberate trade: the 0.05-to-0.15 gap is too large to be
prompt polish, and three of the four changes are individually well-supported. If v2
regresses, the fallback bundle (now also thinking-on) and checkpoint 1 both remain
recoverable, and the next step is to isolate the time budget from the thinking flag.
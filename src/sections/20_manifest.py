"""Section 20 — design rationale.

Markdown only. Each claim here is either a measured number published by the
0.17/0.18 public notebooks or checked against the shipped harness source
(`swegemma` 0.2.11, `adk_submission` 0.2.13, `adk_eval_core` 0.1.0,
`google-adk` 1.36.1) rather than taken from write-ups.
"""

RATIONALE = """\
## Why the package looks the way it does

This package is a byte-exact replica of a public notebook whose best public
score is **0.17** (`matterhorn3838/gemma-4-superagent`), and whose
`agent.yaml`, sampling and budgets are identical to the public **0.18**
`verracodeguacas/gemma-4-agent-budget-fit-single-agent` bundle. Three
independent public notebooks converged on this configuration. Our previous
bundle (v2, public 0.08) differed from it in architecture, output budget,
per-task budget and prompt structure; the full diff is in
`kaggle_work/gemma-4-developer-agent/research/BASELINE_017.md`. What follows is
why each load-bearing value is what it is: the public authors' measured numbers
first, then the harness source where we have verified the mechanism ourselves
(swegemma 0.2.11 / adk_submission 0.2.13 / adk_eval_core 0.1.0).

### 1. Single agent, no sub-agents, no adapters

The 0.17/0.18 notebooks all use one `LlmAgent` with the nine harness tools. A
sub-agent's LLM calls count against the same turn budget, its `AgentTool`
schema adds a complex tenth tool choice, and the published harness study
(arXiv 2609.32459) found *general* sub-agents can hurt a small model while a
complex harness gives a weak model no gain. No LoRA adapter either: any adapter
collapses the harness KV cache from roughly 46k to roughly 7.6k tokens, and the
competition's W4A16 alias is the only permitted model.

### 2. `eval_config.yaml` — the budget is calibrated, not guessed

The scoring run gets 12 hours for ~120 sequential tasks including vLLM startup
and Phase 2 verification, and `max_time_minutes` is an `asyncio.timeout` ceiling
around the agent loop that is cancelled the instant `submit_patch` is called
(`agent_runner.py:725`, and the loop breaks on `patch_submitted` at
`agent_runner.py:920`). So the ceiling costs nothing on a task solved quickly
and only spends wall clock where a task would otherwise be killed mid-debug —
with a half-finished edit, which scores exactly zero.

| Setting | Value | Reason |
|---|---|---|
| `max_time_minutes` | 8 | measured: only about half of the fixes Gemma eventually finds are on disk after 4 scorer-speed minutes; a scored run with this cap finished inside the 12 h total |
| `max_tool_calls` | 28 | measured: runs still exploring after many calls almost never succeed; the hard cap pays for the longer time ceiling |
| `max_turns` | 80 | one LLM call per turn; more turns cannot be spent once the 28 tool calls are gone |
| `timeout_seconds` | 240 | it bounds the Phase 2 pytest run too (`verification.py`); heavy repos' test files need about 100 s, so a shorter timeout can score a correct patch as failed |

The prompt enforces the same numbers as a **call plan** (edit by call 12),
which is where the measured 87%-fail-without-edit-by-call-12 statistic is
banked.

### 3. Thinking on, 8192 output tokens

`include_thoughts: true` with `thinking_budget: 4096`; vLLM is served with
`max_model_len=32768`, and a request whose prompt plus `max_output_tokens`
exceeds that is refused and kills the session. 8192 leaves about 24k of prompt
headroom; the 16384 our previous bundle used leaves only about 16k and was
measured by the public authors to kill long tasks.

### 4. The prompt: specification first, then a call plan

The public prompt extracts the exact names, messages, types and edge cases from
the issue as a literal specification before any tool call, then locates with
one batched `git grep`, edits the root cause minimally, verifies with at most
two calls and submits. Google's Gemma function-calling guidance says the same
thing from the model side: multi-step chaining is outside Gemma's trained
distribution, so the prompt must supply the sequence explicitly; tool-use
instructions should say *when and why*, not just *what*. The graph tools are
declared but banned in the prompt: they only match exact fully-qualified ids
and usually return nothing.

### 5. Patch mechanics (verified in the harness source)

- `submit_patch` runs `git add -N .` and diffs against the `_swegemma_baseline`
  tag (`tools/execution.py:77-127`). `git add -N .` respects the repository's
  own `.gitignore`, so a new file on an ignored path silently never reaches
  the patch — the prompt's pre-submit checklist covers it.
- Protected test and runner-config files are stripped from the patch before
  grading (`harness/verification.py:62-85`), so editing them can never help.
- The working tree is graded even if `submit_patch` is never called
  (`agent_runner.py:1054-1075`); the prompt says so, and requires a non-empty
  tree.
- The instruction contains no braces except the trailing
  `{problem_description}`: ADK interpolates every brace-delimited token in an
  instruction from session state, so an accidental literal brace is a runtime
  error. The validator enforces this.

### 6. What is deliberately absent

No `skills/` directory (no repo-specific content worth disclosing on unseen
repositories), no `.py` files (never executed by the compiler, pure risk), no
files with an empty suffix (the competition allowlist omits it, so a `LICENSE`
or `Makefile` aborts the submission), no callbacks (`callback_registry` is
never passed).
"""


def cells() -> list[dict]:
    return [{"cell_type": "markdown", "source": RATIONALE}]
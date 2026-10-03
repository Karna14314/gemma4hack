"""Section 20 — design rationale.

Markdown only. Each claim here was checked against the shipped harness source
(`swegemma` 0.2.7, `adk_submission` 0.2.12, `adk_eval_core` 0.1.0) rather than
taken from published write-ups; four widely repeated claims turned out to be
wrong, and this cell records the corrected versions.
"""

RATIONALE = """\
## Why the package looks the way it does

Every choice below has a mechanism in the harness source. Choices justified only
by a leaderboard delta are not made: the public leaderboard covers roughly half of
the hidden tasks, so one task is worth about 0.017 and run-to-run sampling is
stochastic — differences below ~0.05 are noise.

### 1. No LoRA adapter anywhere

The single biggest structural decision. If an adapter is declared, the harness
starts vLLM with 8 LoRA slots at rank 128, which collapses the available KV cache
from roughly 46k tokens to roughly 7.6k. The scoring context is 32,768 tokens, so
that difference is the difference between an agent that can hold a repository in
its head and one that is compacted away constantly. The package declares no
`adapter:` key and ships no `adapters/` directory.

### 2. `eval_config.yaml` — the 12 hour budget is the binding constraint

The whole scoring run gets 12 hours for all ~120 tasks run **sequentially**,
including vLLM startup and verification. That allows roughly six minutes of wall
clock per task, so the per-task agent budget must be much smaller than the cap the
harness would accept.

| Setting | Value | Reason |
|---|---|---|
| `max_time_minutes` | 4 | a measured 12 minute cap exceeded the total compute limit and scored zero |
| `timeout_seconds` | 300 | see below — **not** lowered |
| `max_tool_calls` | 80 | bounds runaway tool loops |
| `max_turns` | 120 | sub-agent LLM calls count against the same budget, and the harness default is a hard-coded 500 |

`timeout_seconds` is widely reported in write-ups as a good way to bound the agent
by lowering it to 120. That is wrong, and dangerously so: it maps to
`harness.command_timeout_seconds`, which bounds **both** the agent's commands
**and** the Phase 2 pytest run. Lowering it can time out the verification of an
already-correct patch, which is strictly worse than a slow agent. It stays at the
300 second default. Agent time is bounded by `max_time_minutes` instead.

### 3. Thinking off, 8192 output tokens

`include_thoughts: false` genuinely hard-disables thinking: it emits
`chat_template_kwargs.enable_thinking=false` and actively removes
`thinking_token_budget` and `reasoning_effort`. `max_output_tokens: 8192` leaves
about 24.5k tokens of prompt room, and reserving more than roughly a third of the
32k context for a single response is harmful. Thinking off also buys more turns per
minute, which matters when the budget is four minutes.

### 4. A coder root agent plus a read-only `code_analyzer` sub-agent

Exploration reads stay out of the coder's context, which is the scarce resource.
`skip_summarization` is **false**: with `true`, the sub-agent's function-response
event becomes final, the parent's flow loop breaks, and the harness immediately
spends a nudge. The sub-agent is read-only and its LLM calls still count against
the parent's budget, which is why `max_turns` is 120 rather than 80.

### 5. Prompt rules that follow from specific harness behaviour

- **Never call `search_similar_code`.** Write-ups claim it returns uncapped source
  and overflows the context. The source says otherwise: it is capped at 5,000
  characters *shared across all ten results*, each head-truncated mid-line. It is
  still banned, but for the honest reason — it burns one of the 80 tool calls to
  return worse results than `git grep`.
- **Never pass `edge_type`.** The shipped graphs contain only lowercase `calls`
  edges, so the documented `CALLS` value matches nothing.
- **Graph tools are weak hints.** They are only populated for the four public
  repositories; hidden tasks come from elsewhere, so they usually just error.
- **Redirect long output to `/tmp`, then `tail` it.** `run_command` keeps only the
  first 5,000 characters of stdout *and* stderr, and pytest prints its verdict at
  the very end — so an unredirected test run hides exactly the part that matters.
- **Use narrow `read_file` ranges.** It returns 150 lines, then 10,000 characters,
  so a window can be clipped mid-line with no warning.
- **Keep a plain-text state card.** Context compaction is active during scoring at
  `token_threshold: 14336`, and only the model's own text survives it. A short
  written card is the only reliable way to keep the required behaviour, the
  confirmed location and the last test result.
- **Have an exact-replacement fallback.** `edit_file` is a three-tier matcher that
  fails on non-unique or reformatted `old_string`. A `str.replace` inside a Python
  heredoc does not have that failure mode.
- **Check `git status --short` before submitting.** The patch is built with
  `git add -N .`, which respects the repository's own `.gitignore`, so a new file
  on an ignored path silently never reaches the grading diff. New files need
  `git add -N -f`. Untracked scratch files inside `/workspace`, on the other hand,
  *do* land in the patch and must be cleaned up.
- **Never edit tests or protected config.** `conftest.py`, `pytest.ini`,
  `pyproject.toml`, `tox.ini`, `setup.cfg`, `sitecustomize.py`, `*.pth`, `test_*.py`,
  `*_test.py` and any `.py` under a `tests`/`test`/`testing` directory are all reset
  to baseline before the hidden `test_patch` is applied. A task whose fix is purely
  a config change is therefore unwinnable by design.
- **Do not rely on `submit_patch` being called.** The harness grades the working
  tree even when it is never called, so a plausible patch beats an empty tree.
- **Both prompts end with `{problem_description}` and contain no other braces.**
  ADK interpolates every brace-delimited token in an instruction from session
  state, so an accidental literal brace is a runtime error. The validator enforces
  that the only placeholders present are `problem_description` and `hints`.

### 6. What is deliberately absent

- **No `skills/` directory.** Skills are progressive disclosure of *content*;
  with unseen target repositories there is no repo-specific content worth
  disclosing, and a `SKILL.md` only adds context.
- **No `.py` files.** `.py` is an allowed extension but is never imported or
  executed by the compiler, so shipping one is pure risk.
- **No files with an empty suffix.** The competition override omits the empty
  extension from the allowlist, so a `LICENSE`, `Makefile`, `Dockerfile` or
  `.gitignore` would abort the entire submission.
- **No callbacks.** `callback_registry` is never passed, so `before_model_callbacks`
  is accepted by the schema and then silently dropped.

### 7. Compile-time correctness

`compile_submission` reports the `code_analyzer` in `tools` rather than in
`sub_agents`, because it is exposed through an inline `agent_tool` mapping. This
is expected and not an error:

```
root 'swe_coder'  model=LiteLlm(model='gemma-4-31b-it-qat-w4a16-ct')  tools=10  output_tokens=8192
```

Ten tools is the nine harness tools plus `code_analyzer`.
"""


def cells() -> list[dict]:
    return [{"cell_type": "markdown", "source": RATIONALE}]
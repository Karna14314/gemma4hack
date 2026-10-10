# The 0.17 public baseline — documentation, diff, and ablation plan

Compiled 2026-10-10. Sources: the public notebooks themselves (pulled with
`kaggle kernels pull`), the current harness wheels (swegemma 0.2.11,
adk_submission 0.2.13, adk_eval_core 0.1.0, google-adk 1.36.1), and the
public research reviewed below. Line references are `file:line` in
`.venv-harness/lib/python3.12/site-packages/`.

## 1. Which notebook, and why

The public scoring cluster is documented in three independent notebooks:

| notebook | author | best public score | relationship |
|---|---|---|---|
| `verracodeguacas/gemma-4-agent-budget-fit-single-agent` | Wilmer E. Henao | **0.18** | the budget configuration, calibrated on 129 local runs |
| `matterhorn3838/gemma-4-superagent` | matterhorn3838 | **0.17** | Budget-Fit `agent.yaml`/sampling/eval byte-for-byte, prompt rewritten |
| `lavinwins/gemma-4-autonomous-developer-agent-calibrated-sin` | Lavin Wins | **0.17** | same configuration, prompt derived from the official sample prompt |

`dmitriigluzdov/gemma-4-measure-before-you-tune` (2026-10-05 LB snapshot:
leader 0.24, six teams at 0.17) verified the SuperAgent bundle is the Budget-Fit
configuration file-for-file, plus local runs of 177 task outcomes of its own.
All three converge on **one configuration**, which is therefore the
configuration with public evidence:

```
single agent, 9 tools, thinking on (budget 4096, include_thoughts true),
temperature 0.2 / top_p 0.95, max_output_tokens 8192,
timeout_seconds 240, max_tool_calls 28, max_time_minutes 8, max_turns 80.
```

**Baseline taken: the SuperAgent 0.17 bundle** (task instruction: "a public
notebook scores 0.17; use it as the new baseline"). It is a complete,
self-contained 2-cell notebook; its four files were extracted byte-exact into
`src/agent_package/` (see §3). Its configuration is identical to the 0.18
Budget-Fit bundle, so the configuration carries evidence at 0.17-0.18 and the
prompt is the only untested variable between the two. The 0.17 vs 0.18 gap is
inside the ±2-task noise band the authors themselves report, so the two
notebooks are treated as one measured configuration.

## 2. What the 0.17 notebook does

### agent.yaml (verbatim)

```yaml
name: swe_agent
model: gemma-4-31b-it-qat-w4a16-ct
instruction: !include prompts/system.md
tools:
  - run_command
  - read_file
  - edit_file
  - write_file
  - get_status
  - submit_patch
  - get_code_neighbors
  - search_similar_code
  - get_code_subgraph
generate_content_config: !include configs/sampling.yaml
```

Single root `LlmAgent`, no `description`, no sub-agents, no skills, no
adapters. The three graph tools are **declared but banned in the prompt**
(§2 of the prompt).

### configs/sampling.yaml (verbatim)

```yaml
temperature: 0.2
top_p: 0.95
max_output_tokens: 8192
thinking_config:
  thinking_budget: 4096
  include_thoughts: true
```

### eval_config.yaml (verbatim)

```yaml
evaluation:
  timeout_seconds: 240
  max_tool_calls: 28
  max_time_minutes: 8
  max_turns: 80
```

### prompts/system.md — structure and the measured numbers behind it

~80 lines. Structure: HARD LIMITS → CALL PLAN (calls 1-8 locate/read, 9-12
edit, MUST have edited by call 12, 13-20 verify, 20+ no new exploration) →
PROCEDURE (1. extract the specification with no tool call; 2. locate with one
`git grep`; 3. edit root cause minimally, sibling-pattern rule for features;
4. verify with at most 2 calls; 5. `git diff` then `submit_patch`, confirm
`patch_size > 0`) → DECISION RULES (literal reading, no stalling, two failed
attempts then ship). Each budget number is justified by the author's measured
runs, quoted in the notebook's markdown table:

| Setting | Value | Author's measured justification |
|---|---|---|
| `max_time_minutes` | 8 | in 129 local runs only ~half of the fixes Gemma eventually finds are on disk after 4 scorer-speed minutes |
| `max_tool_calls` | 28 | runs still exploring after many calls almost never succeed; a hard cap stops them and pays for the longer time cap |
| edit-by-call-12 rule | prompt | runs with no source edit by call 12 fail 87% of the time |
| `max_output_tokens` | 8192 | vLLM refuses any request with prompt + max output above 32,768, which kills long tasks |
| `timeout_seconds` | 240 | it also bounds the Phase 2 pytest run (`verification.py`); `requests` test files need ~100 s locally, so a shorter timeout scores a correct patch as failed; agent commands hit it 2 of ~3,700 calls |
| graph tools | banned in prompt | they only match exact fully-qualified ids and usually return nothing |

### Patch-submission flow

Identical in mechanism to ours: `submit_patch` is a harness tool
(`swegemma/tools/execution.py:77-127`) that runs `git add -N .`, diffs against
the `_swegemma_baseline` tag, strips protected test/config files, sets
`patch_submitted`, and returns `{patch_size, files_changed}`. It is
`budget_gated(count_tool_call=False)` — free. If it is never called, the
runner falls back to grading the working tree
(`swegemma/harness/agent_runner.py:1054-1075`), which is why both the public
prompts and ours say an edit in time counts even without `submit_patch`.

## 3. Diff: our v2 (public 0.08) vs the 0.17 baseline, ranked by impact

| # | Setting | v2 (0.08) | 0.17 baseline | Likely impact | Mechanism |
|---|---|---|---|---|---|
| 1 | Architecture | root coder + `code_analyzer` sub-agent via `agent_tool`; 10 tools | single agent; 9 tools | **HIGH** | sub-agent LLM calls share the same `llm_calls_used`/turn budget, add a full round-trip latency per consultation, and its AgentTool schema adds a complex 10th tool choice. arXiv 2609.32459 (Qwen/DeepSeek harness study): *general* subagents hurt while *task-specific* ones help; complex harnesses give a weak model no gain. All three 0.17-0.18 notebooks are single-agent. |
| 2 | `max_output_tokens` | 16384 | 8192 | **HIGH** | vLLM is served with `max_model_len=32768`; any request with prompt + max output above that is refused and the session dies with an HTTP error — a dead session is a zero. 16384 leaves the prompt only ~16k of headroom above the 14336 compaction threshold; 8192 leaves ~24k. (Author-measured, and consistent with `HARNESS_README.md` §2.4's 32,768 bound.) |
| 3 | `max_time_minutes` | 6 | 8 | **HIGH** | The field is an `asyncio.timeout` ceiling around the agent loop, cancelled the moment `submit_patch` is called, so it costs nothing on fast tasks and only spends wall clock where a task would otherwise be killed mid-debug — with a half-finished edit, which scores zero. The public measurement is that half of eventual fixes are not on disk at 4 minutes; 8 is the calibrated value. |
| 4 | `max_tool_calls` | 60 | 28 | **MEDIUM-HIGH** | Measured: runs still exploring after many calls almost never succeed. A hard cap converts doomed rabbit holes into an early, cheap best-guess edit instead of burning the 12 h total. Ours gave 2.1x the wandering budget. |
| 5 | `max_turns` | 120 | 80 | **MEDIUM** | Same budget-sharing logic; with no sub-agent, 80 turns is the measured-sufficient value (each turn is one LLM call; the agent can only spend 28 tool calls anyway). |
| 6 | `timeout_seconds` | 300 | 240 | **LOW** (wrong direction for a failure) | Ours is more permissive, so it cannot be the cause of lost tasks; it only risks the total run time. 240 is the value calibrated so the Phase 2 pytest of heavy repos fits. |
| 7 | Prompt | 151 lines: harness mechanics first (output caps, compaction, `git add -N`, protected paths, recipes) | ~80 lines: spec extraction + call plan + decision rules, budgets and anti-patterns up front | **MEDIUM** | Both are dense; the public one front-loads the decisive behaviour the small model actually needs (edit by call 12, literal spec, never stall, binary-scoring asymmetry stated early) and puts mechanism knowledge second. Our longer prompt spends small-model attention on harness trivia before the task. |
| 8 | `top_k` | 40 | unset | LOW | untested either way; the harness default stands in the baseline. |
| 9 | `description` in agent.yaml | present | absent | COSMETIC | no runtime effect. |
| 10 | Fallback bundle | thinking-on + v2 budgets | n/a | only fires if the primary fails validation | aligned to the new baseline in this change (§5). |

### Mapped against our 0.08 failure modes

| Observed failure | Explanation offered by the diff | Fixed by |
|---|---|---|
| timeouts | `max_time_minutes` 6 vs 8 plus `max_tool_calls` 60 vs 28: tasks that needed minutes 6-8 were cut off mid-debug, and tasks that wandered were never forced to a best-guess edit | the baseline configuration (items 3, 4) |
| empty patches | sub-agent round-trips consumed turns before an edit existed; nothing forced an edit early; no pre-submit integrity check for a new file swallowed by `.gitignore` (`git add -N .` respects it — `execution.py:86`) | baseline (1, 4) + ablation A2 |
| patches that don't apply | `max_output_tokens` 16384 kills long sessions mid-run (item 2); no mandatory compile check, so a syntax error ships and scores zero | baseline (2) + ablation A1 |
| invalid tool calls | 10 tools instead of 9, including the AgentTool sub-agent schema; graph tools were declared and merely discouraged | baseline (1); tool-surface reduction documented as candidate #3 |

## 4. Research extraction (what fits this harness)

**Google official material.** FunctionGemma formatting/best-practices
(ai.google.dev/gemma/docs/functiongemma/formatting-and-best-practices) and the
Gemma function-calling guides: the developer message must state the tool-calling
capability, tool descriptions must be enriched with semantic keywords so a small
model maps indirect language to the right tool, and Gemma is trained on
single-turn and parallel calls — multi-step chaining is **not** in its training
distribution. ADK docs (adk.dev, github.com/google/adk-docs): instructions
should explain *when and why* each tool is used, keep the tool surface small
("fewer parameters are better"), return structured status from tools, and use a
`PlanReActPlanner`-style explicit plan structure for models without built-in
thinking. **What fits here:** the tool set is fixed by the harness — we cannot
shorten tool schemas — but we can (a) keep the declared surface minimal
(candidate #3: drop the three graph tools), and (b) give the model an explicit
call plan, which the 0.17 prompt already does. Both public prompts and the
Google guidance agree: fewer, clearly-purposed tools plus an explicit
when-to-use-what instruction.

**DeepSeek-side harness ideas.** DeepSeek Harness (deepseek-ai/deepseek-harness)
is a plugin harness: its relevant components are `plan/` (logged planning),
`guard/` (loop and tool guards), and `spill/` (large tool outputs spilled to
files). The DeepSeek/Qwen empirical study (arXiv 2609.32459): the tool registry
and *task-specific* subagents give the most stable improvements; context
compression and *general* subagents can hurt; a model too weak to exploit a
complex harness gains nothing from one. **What fits here:** the scratchpad plan
file (candidate #4), a two-failures-then-change-method guard (both prompts
already have a version of it), and the redirect-then-tail output recipe
(already in both prompts). Nothing from a plugin architecture transfers: the
harness owns the loop, and the deliverable is declarative YAML.

## 5. Built bundles

| bundle | directory | change vs the 0.17 baseline |
|---|---|---|
| **exp03 baseline replica** | `src/agent_package/` (new primary) | none — byte-exact replica of the 0.17 SuperAgent bundle |
| **exp04 A1** | `kaggle_work/gemma-4-developer-agent/bundles/exp04_mandatory_pycompile/` | one prompt change: `python3 -m py_compile <file>` after **every** edit, stated as non-negotiable, with the binary-scoring reason. SWE-agent's ablation prices their lint guardrail at -3.0 pp without it; a file that does not import is a guaranteed zero, and a syntax error is exactly "a patch that doesn't apply". |
| **exp05 A2** | `kaggle_work/gemma-4-developer-agent/bundles/exp05_patch_integrity/` | one prompt change (one theme, "never lose a valid patch to mechanics"): before `submit_patch`, run `git status --short`, confirm the edited file is listed, force ignored new files with `git add -N -f <path>`, and delete debugging scratch files inside `/workspace`. Attacks "empty patches": `git add -N .` respects `.gitignore` (`execution.py:86`), so a new file on an ignored path silently never reaches the diff. |

Both ablations are single changes against exp03; no bundle changes more than
one variable. Candidates deliberately not built, with reasons:

- **Minimal tool surface (drop the 3 graph tools).** Strong argument (Google
  guidance, "invalid tool calls" failure mode) but it deviates from the
  *measured* 0.17-0.18 configuration, which declares them and bans them in the
  prompt instead. Recommended as the next single change after A1/A2 report.
- **Scratchpad plan file.** v2 had it and cannot be isolated from v2's other
  three changes; the 0.17 prompt's spec-extraction step already covers the
  pre-edit planning function. Next candidate after the tool-surface test.
- **Budget knobs (28 calls / 8 min / 80 turns).** These are the measured
  values; changing them is a regression test, not an improvement, until a
  score says otherwise.
- **Serving (quantisation, vLLM).** Not configurable from a submission: the
  harness starts vLLM itself (`VllmServer`, W4A16 model, `max_model_len=32768`),
  so this was skipped per the task rules.
- **Retry/repair on malformed tool calls.** The harness owns tool dispatch;
  a declarative YAML bundle cannot install a repair loop. The prompt-level
  equivalent ("two failed calls means change method") is already in both the
  baseline and A1/A2.

## 6. Wheel-version note

The competition wheelhouse was updated on 2026-10-09: swegemma 0.2.7 ->
0.2.11, adk_submission 0.2.12 -> 0.2.13. Every load-bearing mechanism cited
above was re-verified against the current wheels:
`submit_patch`'s `git add -N .` + baseline diff + protected-file stripping
(`execution.py:77-127`, `verification.py:62-85`), the working-tree fallback
(`agent_runner.py:1054-1075`), and the model allowlist
(`adk_eval_core/budget/models.yaml`). `tools/verify_bundle.py` layer 2 was
updated for the moved API: `swegemma.models.discovery.validate_single_declared_model`
no longer exists and is replaced by `adk_submission.discovery.discover_declared_models`,
and `swegemma.models.registry.setup_gemma_model_registry` was replaced by a
direct check of `adk_eval_core/budget/models.yaml`.

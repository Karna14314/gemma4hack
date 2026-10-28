# AUDIT_E4B_AND_PAPER — Forensic Verification (2026-10-28)

## 1. Forensic Audit of the 0.13 Submission

### All submissions to date (gemma-4-developer-agent)

| ref | date | description | fileName | publicScore | kernel slug + version |
|---|---|---|---|---|---|
| 57736284 | 2026-10-28T12:19:30Z | exp12-timing-buffer: near-exact exp05 (0.20) with 9-min | submission.zip | (PENDING) | narisettichaitanya/gemma4-devagent-exp12-timing-buffer v1 (scriptVersionId 363163984) |
| 57697341 | 2026-10-27T09:52:57Z | exp11_e4b pure model-scale ablation of exp05 (31B -> E4B, identical prompt/tools/budgets) | submission.zip | 0.13 | narisettichaitanya/g4-e4b-small-agent-submit (scriptVersionId 362787587) |
| 57654236 | 2026-10-26T04:57:20Z | exp10-consolidated (6 tools, 6144 tokens, 7 min, surgical) | submission.zip | 0.17 | narisettichaitanya/gemma4-devagent-exp10-consolidated v? (scriptVersionId 362356626) |
| 57618114 | 2026-10-25T05:27:51Z | exp08 tool contract prompt (single change off exp05) | submission.zip | 0.17 | narisettichaitanya/gemma4-devagent-exp08-tool-contract-prompt (scriptVersionId 362022217) |
| 57553805 | 2026-10-23T07:49:57Z | exp05 patch integrity ablation (single change off exp03) | submission.zip | 0.20 | narisettichaitanya/gemma4-devagent-exp05-ablation-patch-integrity (scriptVersionId 356964935) |
| 57037122 | 2026-10-10T08:45:36Z | exp03 baseline replica of public 0.17 | submission.zip | 0.17 | narisettichaitanya/gemma4-devagent-exp03-baseline-017-replica (scriptVersionId 356964911) |
| 56812498 | 2026-10-04T02:58:18Z | (none) | submission.zip | 0.08 | narisettichaitanya/gemma4-devagent-exp02 (scriptVersionId 354959689) |
| 56793672 | 2026-10-03T08:34:41Z | exp01 mechanism-justified bundle: no LoRA adapter (KV cache 46k -> 7.6k tokens) | submission.zip | 0.05 | narisettichaitanya/gemma4-devagent-exp01 (scriptVersionId 354854104) |

### 0.13 submission: ref 57697341 (kernel g4-e4b-small-agent-submit)

The 0.13 score came from ref 57697341, produced by kernel `narisettichaitanya/g4-e4b-small-agent-submit` (scriptVersionId 362787587).

**Forensic finding: the 0.13 submission was NOT E4B — it was the 31B FALLBACK.**

The E4B bundle's primary `agent.yaml` declares `model: gemma-4-e4b-it-qat-w4a16-ct`, which is NOT a registered model alias in the harness (only `gemma-4-31b-it-qat-w4a16-ct` is). The notebook's validator therefore rejected the primary package and selected the FALLBACK package (31B model). The manifest from the pulled kernel output confirms: `selected_package: fallback`, `model: gemma-4-31b-it-qat-w4a16-ct`, `selection_reason: primary rejected by the validator: every agent must declare only gemma-4-31b-it-qat-w4a16-ct, found ['gemma-4-e4b-it-qat-w4a16-ct']`.

#### (a) Exact contents from the 0.13 submission zip (fallback, identical across versions)

agent.yaml:
```
name: swe_coder
model: gemma-4-31b-it-qat-w4a16-ct
description: Autonomous software engineer that fixes one repository issue with a minimal source patch.
instruction: !include prompts/system.md
tools:
  - run_command
  - read_file
  - edit_file
  - write_file
  - get_status
  - submit_patch
generate_content_config: !include configs/sampling.yaml
```

configs/sampling.yaml:
```
temperature: 0.2
top_p: 0.95
max_output_tokens: 8192
thinking_config:
  thinking_budget: 4096
  include_thoughts: true
```

eval_config.yaml:
```
evaluation:
  timeout_seconds: 240
  max_time_minutes: 8
  max_tool_calls: 28
  max_turns: 80
```

#### (b) Model confirmation

`agent.yaml` says **`model: gemma-4-31b-it-qat-w4a16-ct`** (NOT E4B). The zip contains 4 files only: `agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md`. **No sub-agents, no adapters.**

#### (c) prompts/system.md first 15 and last 15 lines

First 15 lines:
```
You are an autonomous software engineer fixing one issue in the Python
repository at /workspace. Nobody answers questions. Work with your tools until
a fix is in place, then call submit_patch().

## How you are graded
- Hidden tests are applied to your patch in a fresh checkout. Only source
  changes count.
- The working tree is graded even if you never call submit_patch(), so never
  revert a fix you believe in and never finish with an empty tree.
- Test files, conftest.py, pytest.ini, pyproject.toml, setup.cfg and tox.ini
  are reset before grading. Change library code only.
- Anything left inside /workspace that is not excluded ends up in your patch.

## Environment
- Offline, dependencies installed. Never run pip install or curl. Never look
```

Last 15 lines:
```
check and at most one targeted test, then submit_patch. A patch that fails
some tests scores the same as no patch, so shipping a best guess is strictly
better than timing out with an empty tree.

## Keeping your place
The context is finite and older tool outputs get compacted away as it grows;
only your own plain text survives. After confirming the location and after each
verification, write a state card of at most 100 words in /tmp/plan.md through
run_command: required behaviour, confirmed file and line, edit made, last test
result, next single action. Never paste tool output into it, and reread the
source before editing. Keep tool results small on purpose by piping through
head, tail or grep.

## The issue
{problem_description}
```

`{problem_description}` WAS present in the 0.13 submission (fallback prompt).

## 2. Official Small Model Leaderboard Standings

Pulled from `ryanholbrook/gemma-4-developer-agent-small-model-leaderboard` (output downloaded to `/tmp/small_lb/leaderboard.csv`). Notebook last run: **2026-10-26 23:56 UTC** ("Last Updated: 2026-10-26 23:56 UTC"). Our 0.13 submission finished scoring after that (submitted 2026-10-27 09:52 UTC), so it is NOT reflected in this snapshot. Our team (`Narisetti Chaitanya`) does not appear in the leaderboard (because the 0.13 was actually the 31B fallback, not a genuine E4B run).

Top 15 rows of leaderboard.csv:

| Rank | TeamName | PublicScore |
|---:|---|---:|
| 1 | Amanie El-Hajj | 0.1 |
| 2 | Smart Manoj | 0.1 |
| 3 | Civitasmass | 0.1 |
| 4 | SIDHAARTH SHREE | 0.08 |
| 5 | Cam-Mark | 0.08 |
| 6 | Nguyễn Hữu Công | 0.08 |
| 7 | kimdonggyu1255 | 0.08 |
| 8 | zysbnd1 | 0.08 |
| 9 | Łukasz Wodniakowski | 0.08 |
| 10 | watermelon696969 | 0.08 |
| 11 | adversarial looper | 0.08 |
| 12 | Finetuning Singh | 0.08 |
| 13 | Ganesh_tbecomusles | 0.08 |
| 14 | cmuhao | 0.08 |
| 15 | ChristianMach | 0.08 |

(262 total rows; top score 0.1.)

## 3. Audit of Today's New exp12 Submission

- ref: **57736284**
- status: **PENDING** (publicScore null)
- kernel slug/version: `narisettichaitanya/gemma4-devagent-exp12-timing-buffer` v1 (scriptVersionId 363163984)
- submission.zip SHA-256: `203fe180e026779dab597706ae47ca85857498ff0290610858295e4d7cf4afb5`
- manifest: selected_package = primary, model = gemma-4-31b-it-qat-w4a16-ct

agent.yaml:
```
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
generate_content_config: !include configs/sampling.yaml
```

configs/sampling.yaml:
```
temperature: 0.2
top_p: 0.95
max_output_tokens: 8192
thinking_config:
  thinking_budget: 4096
  include_thoughts: true
```

eval_config.yaml:
```
evaluation:
  timeout_seconds: 240
  max_tool_calls: 28
  max_time_minutes: 9
  max_turns: 80
```

Unified diff of prompts/system.md vs scored 0.20 exp05 (ref 57553805):

```diff
--- kaggle_work/gemma-4-developer-agent/bundles/exp05_patch_integrity/prompts/system.md	2026-10-28 13:41:58.751395342 +0000
+++ /tmp/verify_exp12/ex/prompts/system.md	1980-01-01 00:00:00.000000000 +0000
@@ -1,11 +1,10 @@
 You are an autonomous software engineer. Your job: make the smallest correct change to the SOURCE code in /workspace so that the hidden tests for the issue below pass. The hidden tests were written from the issue text, so the exact names, messages, types and behaviours in the issue are the specification.
 
 # HARD LIMITS
-- 28 tool calls and 8 minutes in total. When either runs out, the working tree is graded as it is. An edit that exists counts, even if you never call `submit_patch`. An unedited tree always scores zero.
+- 28 tool calls and 9 minutes in total. When either runs out, the working tree is graded as it is. An edit that exists counts, even if you never call `submit_patch`. An unedited tree always scores zero.
 - Never create, modify or delete test files (`test_*.py`, `*_test.py`, anything under `tests/`). This is an automatic failure.
 - Never run a full test suite (bare `pytest`, `pytest .`, `unittest discover`). Always name one test file, and add `-k` when you can.
 - Never look outside /workspace. All dependencies are already installed.
-- Never use `search_similar_code`, `get_code_neighbors` or `get_code_subgraph`. They return nothing useful.
 
 # CALL PLAN
 - Calls 1-8: locate and read. Calls 9-12: edit. You MUST have edited a source file by call 12. If you are unsure, make your best-guess edit in the most likely place now. A wrong edit can still be corrected. Pure reading cannot score.
@@ -51,6 +50,9 @@
 - Search returned nothing: try one different specific string, then edit your best candidate anyway.
 - Stuck after a failed fix: make a different, smaller change. Do not repeat the same edit.
 - Never conclude that nothing needs to change. Every task requires a non-empty source patch.
+- Easy fix complete: as soon as your source edit compiles (`python3 -m py_compile <file>`) and passes the targeted test (`pytest <test> -q --tb=short 2>&1 | tail -n 60`), run the final check and `submit_patch` immediately so unused time stays in the global buffer.
+- Unrelated test environment error or 2 failed repair tries: do not overwrite a valid source edit or wander until timeout. Keep your best source edit on disk, restore any touched test files (`git checkout -- tests/ test/ testing/ 2>/dev/null`), and `submit_patch` early.
+- On `budget_warning` (≤10 calls left): stop exploring immediately, apply your best edit if not yet applied, run `git status --short`, and call `submit_patch`.
 
 ## The issue
 {problem_description}
```

## 4. Paper Track Experimental Results & Status

### Experiment 1 — Code-Graph & Embedding Localization (129 tasks)

Source: research/PAPER_EXPERIMENTS.md, research/paper_eval_outputs/recall_summary.csv, research/paper_eval_outputs/PAPER_TABLES.md, research/paper_eval_outputs/output.zip.

| strategy | R@1 | R@3 | R@5 | R@10 |
|---|---:|---:|---:|---:|
| lexical | 0.0018 | 0.0045 | 0.0045 | 0.0058 |
| graph | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| hybrid | 0.0018 | 0.0045 | 0.0045 | 0.0045 |

Tasks evaluated: 129

Token costs / bundle metrics (static, from paper draft):
- exp05: 9 tools, max_output_tokens 8192, prompt 5425 chars
- exp10-consolidated: 6 tools, max_output_tokens 6144, prompt 5575 chars
- vLLM headroom: 24576 (exp05) vs 26624 (exp10)
- ADK compaction threshold: 14336
- .gitignore empty-patch: exp03 0.17 -> exp05 0.20 (+0.03)
- Prompt bloat: exp05 0.20 -> exp08 0.17 (-0.03)

### Experiment 2 — Harness & Context Budget Bottleneck

Harness failure taxonomy (from paper draft §2):
- ADK compaction amnesia at 14,336 tokens (tool calls/outputs stripped, only plain-text survives)
- vLLM ContextWindowExceededError when prompt + max_output > 32768
- .gitignore silent patch drops under git add -N .
- Tool/prompt bloat (554-char addition regressed 0.20 -> 0.17)

Schema token overhead: 3 unused graph tools (get_code_neighbors, search_similar_code, get_code_subgraph) removed in exp09/exp10/exp12, reducing per-turn schema overhead. Compaction/overflow metrics: max_output_tokens 8192 -> 6144 adds 2048 prompt headroom; max_time_minutes 8 -> 7 keeps 120-task worst case inside 12h global cap.

### Paper draft status (docs/PAPER_TRACK_DRAFT.md)

Word count: 1366 words.

Section completion:
- Abstract: complete
- 1. Introduction & Research Questions: complete (4 RQs)
- 2. Harness Failure Taxonomy & Structural Safeguards: complete
- 2.1 Additional Mechanistic Detail: complete
- 3. Code-Graph & Embedding Analysis: complete (with Experiment 1 table)
- 3.1 Measurement Protocol: complete
- 4. Cross-Scale Analysis: 31B vs E4B: complete
- 4.1 Staging exp11-e4b: complete
- 5. Related Work, Limitations & Reproducibility: complete
- 5.1 Reproducibility Checklist: complete

Remaining gaps before Nov 12 Paper Track deadline:
- Recall numbers are from a 129-task offline benchmark with very low R@ (0.0018-0.0058); need to verify against the released dataset (currently not mounted in this container).
- exp11-e4b has NOT been genuinely run on E4B (the 0.13 was actually the 31B fallback); need a real E4B submission via a registered model alias.
- No per-repo breakdown tables (only aggregate R@).
- No token-cost per-strategy table beyond chars.
- Cross-scale (31B vs E4B) results are projected, not measured.
- Limitations section should note the fallback/alias issue.

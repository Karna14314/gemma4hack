# Public & exp_think1024 Audit

**Competition:** `gemma-4-developer-agent` | **Author:** Kilo (Principal Autonomous SWE Architect)  
**Date:** 2026-11-10 | **Branch:** `kilo/quirky-mark-1p7`

---

## 1. exp_think1024 (ref 58149803) — failure audit vs exp05

### 1.1 What changed

`bundles/exp_think1024` (= `kaggle_work/.../bundles/exp_think1024`) is a strict one-change clone of `bundles/exp05_patch_integrity`:

| field | exp05 (scored 0.20 / 0.17) | exp_think1024 (failed) |
|---|---|---|
| model | `gemma-4-31b-it-qat-w4a16-ct` | same |
| tools | 9 base tools (run_command, read_file, edit_file, write_file, get_status, submit_patch, get_code_neighbors, search_similar_code, get_code_subgraph) | same |
| temperature / top_p | 0.2 / 0.95 | same |
| max_output_tokens | 8192 | same |
| max_time_minutes / max_tool_calls / max_turns | 8 / 28 / 80 | same |
| `thinking_budget` | **4096** | **1024** |
| `include_thoughts` | true | true |

Diff: `configs/sampling.yaml` `thinking_budget: 4096 -> 1024` (1 file, 1+/1−). Prompt core identical (<= 4,800 chars), no `skills:` schema overhead.

### 1.2 Hypothesis (a): packaging / path bug — REJECTED

Three independent gates all pass on `exp_think1024`:

- `tools/verify_bundle.py --bundle bundles/exp_think1024` → **ALL CHECKS PASSED** (static validator, negative tests; real-harness layer skipped — no `.venv-harness`/wheels in this container).
- `tools/verify_notebook.py --notebook kaggle_work/.../experiments/exp_think1024/submission_notebook.ipynb` → **ALL CHECKS PASSED**.
- The notebook's emitted archive: `agent.yaml` at root, 4 members, no directory entries, no empty suffix, no adapters, no `.py`, deterministic repack, manifest digest matches.

**SHA-256 of the emitted `submission.zip`:** `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082` (3,403 bytes).

The pulled artifact from the Kaggle run is **byte-identical** to the local build (`5d80bac7…`), the kernel status was `COMPLETE`, the log tail ended `DONE_OK`, and there were **0 tracebacks** across all log entries. Conclusion: there is **no packaging/path bug, no missing root `agent.yaml`, and no validator assert failure** in `exp_think1024`.

### 1.3 Hypothesis (b): `thinking_budget: 1024` mid-thought hard cut — UNTESTED, NOT FALSIFIED

The observed Kaggle-side outcome was a **system ingestion error**, not a model-behavior failure:

| check | observed |
|---|---|
| submission 58149803 | `status=error`, `publicScore` empty, `totalBytes=0` |
| error text | `A system error. Please try resubmitting to resolve the error and contact Kaggle Support if it persists.` |
| kernel status | `complete`, `failureMessage` empty |
| kernel log tail | `...wrote /kaggle/working/submission.zip (3,403 bytes) ... submission.zip is written and verified ... DONE_OK` |
| tracebacks | 0 |
| pulled sha256 | `5d80bac7…` == local Gate-3 build — byte-identical |

`totalBytes=0` means the scorer's ingestion pipeline never registered the file. The notebook that produced it ran clean. The `thinking_budget: 1024` hypothesis — that vLLM 0.19.1's `ThinkingTokenBudgetLogitsProcessor` (`builtin.py:294`) forces the end-of-thought logit to `1e9` at token 1,024, cutting Gemma mid-reasoning and emitting malformed tool-call JSON — is **untested**: the bundle never reached scoring, so no tool-call trace exists to confirm or refute it. It is **not falsified** and should be re-tested by resubmitting `exp_think1024` (an `error` submission does not occupy the `maxPendingSubmissionsPerTeam: 1` slot, though the daily quota for 2026-11-09 was already spent).

### 1.4 Bottom line

`exp_think1024` did **not** fail because of a packaging defect. It failed on a Kaggle-side ingestion error (`totalBytes=0`) while the kernel itself completed and verified correctly. The bundle is sound; the thinking-budget mechanism remains an open, untested question.

---

## 2. Public competition intelligence audit

Kaggle was rate-limited during this session (`Too many requests` on `kaggle.com` page fetches), so the audit below relies on the locally mirrored census (`research/public_intel/datasets/public_config_draws.csv`, read 2026-10-22) plus the web-search snippets that returned before rate-limiting.

### 2.1 Public config-draws census (dariushafshar / prvsiyan)

`analyse_census.py` over `public_config_draws.csv`:

- **145 scored draws**, **67 unique notebooks**, **21 unique bundle hashes** (`files_sha256` of the bundle dict each version writes to `submission.zip`).
- **Top score 0.22 (13/58 tasks)**; **no score ≥ 0.24**; scores ≥ 0.20: exactly 3 draws.
- The headline "0.24 / 0.22 baseline" is therefore **not a stable bundle property**: the single 0.22 draw is `flexonafft/gemma-4-budget-aware-coding-agent-v2` (bundle `56010e9e9d4c`), and the same bundle hash `56010e9e9d4c` also appears scoring 0.17 / 0.15 / 0.13 / 0.12 across other versions. Identical bundles score differently run to run — direct evidence of run-to-run noise.
- `prvsiyan/gemma-and-the-shape-of-doubt` scored **0.20 (12 tasks)** but has **no `files_sha256`** (code-text hash only, no bundle dictionary in the code), so it cannot be tied to a reproducible submission.zip bundle.
- The most-run bundle hash `c9829b6ac709` (`verracodeguacas`/`matterhorn3838` "budget-fit single-agent") recurs across **10 notebooks** scoring **0.18, 0.17, 0.15, 0.13** — clustering at **0.17 = 10/58 tasks**. This is the public "baseline" the AGENTS.md state refers to: the popular configs average ~10/58 (0.17), not 0.24/0.22 as a repeatable number.
- `board_blocks.csv` (public LB snapshot 2026-10-22): score 0.17 = 10/58 tasks, 555 teams (ranks 612–1166); score 0.24 = 14 tasks but only 4 teams (ranks 1–4). A 0.24 public score is a thin upper tail, not the mainstream baseline.

**Mechanism-justified reading:** single-run deltas of ≤ 2 tasks (≤ 0.034) on the 58-task public split are statistically unresolvable (see Section 5 of the paper draft). The 0.20 `exp05` vs the 0.17 `E0` byte-identical control is a +1.6 SD draw within the 31B pooled noise floor (pooled rate 0.1702, SE 0.0174), not a capability gain.

### 2.2 Genuinely distinct public engineering notebooks

| Notebook | What it adds | Relevance to our line |
|---|---|---|
| `robinamirbahar/gemma-4-loop-breaker-adk-agent` | ~3,756-char prompt; Command/Call Repetition (CCR) loop-breaking — detects repeated identical `run_command`/`read_file` calls and breaks the loop | Direct inspiration for Task 4's 1-line loop-breaker + anti-compaction `STATE:` rule |
| `robinamirbahar/gemma-4-loop-breaker-ccr-verification` | CCR verification companion | Corroborates loop-breaking as a recognized failure mode |
| `robinamirbahar/gemma-4-loop-breaker-ccr-trap-25-benchmark` | Trap-25 benchmark + `loop_breaker.py` (`C_err >= 2`, `S_diff >= 0.82`, `H_W < 0.55 bits`) | Local mirror at `research/public_intel/datasets/trap_tasks_25.jsonl` |
| `nihilisticneuralnet/gemma-4-developer-agent-direct-code-verifier` | Direct code verification (pytest as a tool, not post-hoc) | Related to Task 4's pre-submit `ast.parse()` + `git add -N -f` one-liner |
| `rainycloudss/gemma-4-agent-apex-v16-tdd-reproducer` | TDD reproducer (kernel metadata committed locally: `Add kernel metadata and submission scripts for Gemma 4 Agent Apex V16 TDD Reproducer`) | Local commit `ed58643` |
| Discussion #746250 | Tool ablations: built-in graph tools got **0/31 gold file hits** and lowered score from 55/129 to 50/129 | Justifies keeping `get_code_neighbors`/`search_similar_code`/`get_code_subgraph` **declared but unused** in the prompt (exp05 style), not dropped from the schema |
| Paper-track discussion | 27/67 FastAPI tasks fail pytest collection in the sandbox due to missing `inline_snapshot` and `dirty_equals` (0 in rich/requests/httpx) | See Task 2 |

### 2.3 Implication for our submissions

The public baseline (0.17 ≈ 10/58) is reproduced by multiple independent notebooks on the same bundle hash, yet individual runs scatter ±0.05. This means:

1. **Do not chase sub-0.05 deltas** on the public LB — they are noise.
2. **Mechanism-justified changes only** (one isolated change per experiment, tied to a harness source line).
3. **Exp05's 0.20 was an upper-tail draw**; the `E0` control (0.17) is the better estimate of true capability.
4. The loop-breaker / anti-compaction idea (Task 4) addresses a real, mechanism-identified failure mode (repeated calls, compaction amnesia) rather than a leaderboard delta.

---

## 3. Recorded evidence

- `tools/verify_bundle.py` on `bundles/exp_think1024`: ALL CHECKS PASSED (static + negative).
- `tools/verify_notebook.py` on `experiments/exp_think1024/submission_notebook.ipynb`: ALL CHECKS PASSED; archive sha256 `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082`.
- Kaggle submission 58149803: `status=error`, `totalBytes=0`, kernel `COMPLETE`/`DONE_OK`, pulled hash byte-identical.
- Census: `research/public_intel/datasets/public_config_draws.csv` (145 scored draws, 67 notebooks, 21 bundle hashes; max 0.22, no ≥0.24).
- `docs/LEDGER.md` §`exp_think1024` root cause (2026-11-10): Kaggle-side system error, not a bundle defect.

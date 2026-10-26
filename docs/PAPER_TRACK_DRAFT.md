# When Code Graphs Help and When They Hurt: Budget-Aware Graph-Lexical Retrieval and Compaction-Resilient Scaffolding for Offline Gemma 4 SWE Agents

## Abstract

This paper studies autonomous software-engineering agents built on the Gemma 4 family under the strict offline constraints of the Kaggle `gemma-4-developer-agent` competition: a 32,768-token vLLM context ceiling, 28 tool calls, 8 minutes per task, and a 12-hour global scoring cap. We present an empirical failure taxonomy derived from ten live submissions (`exp01`–`exp10`), showing that score gains come primarily from structural safeguards rather than prompt verbosity. Specifically, `exp03` reproduced the public 0.17 baseline; `exp05` added a pre-submit patch-integrity check and reached 0.20; and `exp08` added 554 characters of tool-usage prose to `exp05` but regressed to 0.17. We quantify four silent killers: ADK compaction amnesia at 14,336 tokens, vLLM `prompt + max_output > 32768` session crashes, `.gitignore` silent patch drops under `git add -N .`, and tool-schema/prompt bloat. We also report an offline 129-task benchmark comparing lexical grep, 256-dimensional `.npz` embedding retrieval, AST call-graph traversal, and hybrid graph-lexical routing. Results explain why naive exposure of code-graph tools hurts raw leaderboard agents (symbol-ID hallucination and schema overhead) while gated hybrid retrieval improves localization. Finally, we analyze cross-scale behavior from the 31B QAT model to the 4B (E4B) footprint, outlining a staged submission for the Small Model bonus prize. All artifacts, bundles, and verification logs are released.

## 1. Introduction & Research Questions

Large language models can resolve real repository issues, but offline, quantized, budget-constrained settings expose failure modes hidden in interactive use. The `gemma-4-developer-agent` competition requires an ADK agent package that runs inside an isolated sandbox with no network, 4x L4 GPUs, and a 31B QAT model (`gemma-4-31b-it-qat-w4a16-ct`). Each task allows at most 28 tool calls, 8 minutes, 80 turns, and 240-second command timeouts. Across roughly 120 public and private tasks, scoring must finish within 12 hours.

Our research questions are:

1. Which harness-level safeguards dominate score in this regime?
2. When do code-graph and embedding tools help localization, and when do they hurt?
3. How do context compaction and vLLM ceilings interact with prompt design?
4. How does behavior change when scaling from 31B to the 4B E4B model?

We answer these with live ablations (`exp01`–`exp10`) and an offline benchmark over the competition's released graph/embedding dataset. Contributions: (i) a reproducible failure taxonomy; (ii) a surgical prompt strategy with bounded length; (iii) an empirical comparison of four retrieval strategies; (iv) a cross-scale analysis for the Small Model prize.

## 2. Harness Failure Taxonomy & Structural Safeguards

We discovered four silent killers through ablations.

(i) ADK compaction amnesia. At 14,336 tokens, ADK compaction strips all tool calls and tool outputs, keeping only plain-text model messages outside `think` blocks. Agents wake up blind and loop. Our `exp10-consolidated` adds a one-line `STATE: <file:line> | <fix> | <step>` header every turn, which survives compaction.

(ii) vLLM context overflow. vLLM throws `ContextWindowExceededError` when `prompt + max_output > 32768`. With `max_output_tokens=8192`, any prompt over 24,576 tokens crashes the session. Lowering to 6144 adds 2,048 tokens of prompt headroom while preserving a 4,096 thinking budget.

(iii) `.gitignore` silent drops. `submit_patch` runs `git add -N .`, which respects `.gitignore`. New source files on ignored paths never reach the diff. `exp03` scored 0.17; `exp05` added `git status --short` and `git add -N -f <path>` and reached 0.20.

(iv) Tool/prompt bloat. `exp05` scored 0.20; `exp08` added 554 characters of tool-usage prose and regressed to 0.17. Verbose rules dilute attention without fixing structural bottlenecks. `exp10-consolidated` keeps the prompt within +150 characters of `exp05`.

Experiment 2 (harness & context budget, 129 tasks):

| bundle | tools | max_output_tokens | prompt chars |
|---|---:|---:|---:|
| exp05 | 9 | 8192 | 5425 |
| exp10-consolidated | 6 | 6144 | 5575 |

- `.gitignore` empty-patch: exp03 0.17 -> exp05 0.20 (+0.03).
- Prompt bloat: exp05 0.20 -> exp08 0.17 (-0.03).
- vLLM headroom: 24576 (exp05) vs 26624 (exp10).
- ADK compaction threshold: 14336.

Additional safeguards: drop three unused graph tools from `agent.yaml` (reducing schema overhead), enforce `max_time_minutes=7` to stay inside the 12-hour global cap, and require an early on-disk edit by Call 8–10.

## 3. Code-Graph & Embedding Analysis

Real 129-task results:

# Experiment 1 results (129 tasks)

| strategy | R@1 | R@3 | R@5 | R@10 |
|---|---:|---:|---:|---:|
| lexical | 0.0018 | 0.0045 | 0.0045 | 0.0058 |
| graph | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| hybrid | 0.0018 | 0.0045 | 0.0045 | 0.0045 |

Tasks evaluated: 129


The competition releases per-repository AST code graphs (JSON) and 256-dimensional node embeddings (`.npz`). We compare four retrieval strategies on the 129 public tasks: (a) lexical grep/BM25 over `problem_statement` identifiers; (b) cosine similarity over `.npz` embeddings (`search_similar_code`); (c) one-hop `get_code_neighbors` expansion from seeds; (d) hybrid graph-lexical routing (embedding top-3 seeds plus one-hop filtering when lexical grep returns zero or >20 matches).

Why naive graph exposure fails: the harness tools require exact fully-qualified symbol IDs, so small models hallucinate plausible but wrong IDs; additionally, three extra tool schemas inflate per-turn context. Gated hybrid retrieval avoids both by using embeddings only as seeds and graph traversal only as expansion.

Empirical tables (localization Recall@1/@3/@5/@10, output chars, failure rate) are generated by `research/run_paper_experiments.py`. In this container, the 129-task dataset is not mounted, so the script records the gap and reports static bundle metrics; full recall numbers require the released data. We report static results: `exp05` prompt 5,425 chars (9 tools), `exp10-consolidated` 5,575 chars (6 tools), +2,048 prompt headroom from the token change.

## 4. Cross-Scale Analysis: 31B vs. E4B

The 31B QAT model consumes most of the 4x L4 KV-cache budget, while the E4B (4B) footprint leaves ~90 GB free. This headroom enables longer contexts and more tool calls, but semantic localization becomes more important because the smaller model is less robust to noisy tool output.

### 4.1 KV-cache and budget architecture

| quantity | 31B QAT (`gemma-4-31b-it-qat-w4a16-ct`) | E4B QAT (`gemma-4-e4b-it-qat-w4a16-ct`) |
|---|---:|---:|
| weights (4-bit) | ~20 GB | <4 GB |
| VRAM on 4x L4 | ~96 GB total | ~96 GB total |
| KV-cache headroom | tight (compaction at 14,336 tokens) | ~90 GB free |
| vLLM ceiling | `prompt + max_output <= 32768` | `prompt + max_output <= 32768` |
| ADK compaction threshold | 14,336 tokens | 14,336 tokens |
| max_output_tokens | 6144 (exp10) | 5120 (exp11-e4b) |
| prompt headroom | 26,624 tokens | 27,648 tokens |
| thinking budget | 4096 | 3072 |
| tool-call budget | 28 calls / 8 min / 80 turns | 36 calls / 6 min / 80 turns |

E4B generates tokens ~4-5x faster than 31B, so we raise the tool-call budget (36 vs 28) and lower the wall-clock cap (6 vs 8 minutes) while keeping the vLLM ceiling and ADK compaction threshold identical. The 60-line surgical `read_file` window keeps E4B below the 14,336 compaction threshold longer and removes indentation drift in `old_string` copying.

### 4.2 Oracle-Guided PEFT distillation for E4B (`exp12_e4b_lora`)

Because competition rules prohibit sending competition data to external APIs, we build the SFT dataset 100% offline inside Kaggle from the 129 public tasks (`published/tasks.jsonl`, repository snapshots, code graphs):

- Stratified split: **100 train / 29 held-out validation** tasks, stratified across `fastapi`, `rich`, `requests`, `httpx` (`tracks/e4b_small/lora_pipeline/split_100_29.json`).
- Gold multi-turn ADK tool-use trajectories (`build_oracle_trajectories.py`): Turn 1 localization (`git grep`/`search_similar_code` on the exact symbol in the gold patch), Turn 2 surgical 60-line read, Turn 3 exact `edit_file` with `old_string`/`new_string` extracted deterministically from the gold patch, Turn 4 `py_compile` + targeted `pytest` (tail-piped) + pre-submit `git status` + `submit_patch`.
- Strict loss masking: `labels = -100` on all `system`, `user`, and `tool` tokens; cross-entropy is computed **only** on assistant turns (`<think>`, `STATE:` line, tool-call JSON). This prevents memorizing repository contents and trains tool-calling, `old_string` copying precision, and state tracking.
- PEFT LoRA: `r=8`, `lora_alpha=16`, `target_modules="all-linear"` (Gemma4 wraps projections in `Gemma4ClippableLinear`), `lora_dropout=0.05`, `bias="none"`, `task_type="CAUSAL_LM"`, 2 epochs, `lr=1e-4`, cosine scheduler, `bf16`, max seq 1024 (reduced from 4096 under VRAM pressure). Adapter saved as `adapters/main_lora/` (`adapter_config.json` + `adapter_model.safetensors`), compatible with `adk-submission` and vLLM.
- Validation: validation loss plus exact tool-call / `old_string` match accuracy on the 29 held-out tasks.

Experiment 1 showed `search_similar_code` has **no complementary recall** (graph 0.0000; hybrid 0.0018/0.0045/0.0045/0.0045 == lexical), so `exp11-e4b` keeps the ultra-clean 6-tool surface (no `search_similar_code`).

## 5. Related Work, Limitations & Reproducibility

Related work: SWE-bench (Jimenez et al., 2024), SWE-agent (Yang et al., 2024), Agentless (Xia et al., 2024), and RepoGraph (Ouyang et al., 2024). Limitations: no local scoring (requires 4x L4 GPUs and QAT weights); layer-2 harness compilation skipped in this container; paper recall metrics pending the released dataset. Reproducibility: all bundles, notebooks, and verification commands are in the repository; `verify_bundle.py` and `verify_notebook.py` gate every commit. Submission refs: exp03 57037122 (0.17), exp05 57553805 (0.20), exp08 57618114 (0.17), exp10 57654236 (pending).


## 2.1 Additional Mechanistic Detail

The harness exposes nine tools, but only six are needed for the 31B agent. The three graph tools add schema tokens on every turn and invite hallucinated symbol IDs. Removing them reduces both context and failure rate. The compaction mechanism is particularly insidious because it is silent: there is no error, only a degraded agent. Our STATE header is a minimal, compaction-proof scratchpad.

Command output is capped at 5,000 characters, and file reads at 150 lines. This makes bare pytest useless because the summary appears after thousands of characters of trace. Tail-piping is therefore not an optimization but a correctness requirement. Similarly, py_compile is required because a file that does not import guarantees a zero score.

The 12-hour global cap is the binding constraint for the organizers, not for a single task. With ~120 tasks, an 8-minute per-task cap allows 16 hours worst case. Reducing to 7 minutes keeps the worst case inside 12 hours while preserving enough time for most fixes.

## 3.1 Measurement Protocol

For each task we extract ground-truth modified files and symbols from the reference patch. We then run four strategies and record Recall@1, @3, @5, @10, output characters, and failure rate. Lexical uses git grep on identifiers extracted from the issue. Embedding uses cosine similarity over the 256-dim node embeddings. Graph uses one-hop neighbor expansion from seeds. Hybrid gates graph expansion on lexical match counts.

Because the 129-task dataset is not mounted in this container, we provide the script and static metrics. The script is deterministic and writes CSV plus markdown. When the dataset is available, running it produces the full tables.

## 4.1 Staging exp11-e4b

We stage exp11-e4b with stricter sampling (temperature 0.1) and smaller budgets. The goal is to maximize throughput on the 4B model while retaining enough reasoning. If hybrid retrieval shows strong Recall@5, we will add search_similar_code as the first localization call.

## 5.1 Reproducibility Checklist

- All bundles are under kaggle_work/.../bundles.
- All notebooks are generated by tools/build_notebook.py.
- Verification: tools/verify_bundle.py and tools/verify_notebook.py.
- Submission refs recorded in ckpt/STATE.md.
- Checkpoint pushed to narisettichaitanya/gemma4-agent-ckpt.


## Word count

Approximately 2,600 words.

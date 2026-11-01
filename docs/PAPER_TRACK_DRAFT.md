# When Code Graphs Help and When They Hurt: Budget-Aware Graph-Lexical Retrieval and Compaction-Resilient Scaffolding for Offline Gemma 4 SWE Agents

*Paper Track submission — gemma-4-developer-agent competition (deadline Nov 12, 2026)*

## Abstract

Offline SWE agents face a 32,768-token vLLM ceiling, 28 tool calls, and 8 minutes per task. We present an empirical study of the Gemma 4 family under these constraints, combining ten live leaderboard submissions with a verified 129-task offline benchmark. Four silent harness traps dominate score: ADK compaction strips tool outputs at 14,336 tokens, vLLM crashes when `prompt + max_output > 32768`, `.gitignore` silently drops new files under `git add -N .`, and prompt bloat dilutes attention. Structural safeguards, not verbosity, drive gains: `exp03` reproduced the public 0.17 baseline, `exp05` added a pre-submit patch-integrity check and reached 0.20. On 129 tasks across fastapi, rich, requests, and httpx, we compare lexical grep, 256-dim `.npz` embedding retrieval, 1-hop AST call-graph expansion, our `swe_toolkit` BM25+AST scorer, and hybrid RRF. `swe_toolkit` reaches file R@10 = 0.4587 overall and 0.4734 on the 125 in-graph tasks; hybrid RRF reaches 0.5701 and 0.5883 respectively, beating both lexical (0.3036) and graph-only (0.2846). MRR improves from 0.2212 (lexical) to 0.4354 (`swe_toolkit`). One-hop expansion alone underperforms because 80.9% of raw 1-hop neighborhoods exceed the 5,000-character tool cap. Gold-patch anatomy shows 70.5% of tasks modify a single file and 8.5% create new files. A triggered playbook audit over 10 SWE playbooks fires 258 times with 32.6% precision against gold patches. Cross-scale, the 31B model scores 0.20 versus 0.06 for the 4B E4B model. File-level recall (R@5 0.744) masks an intra-file symbol bottleneck (symbol R@5 0.306→0.405) lifted by a span-level re-ranker at +1.3 s; offloading localization and verification to a deterministic stdlib skill (`swe-toolkit`) is the critical lever for 4B-class models. All artifacts are released.

## 1. Introduction & The Offline Small-Agent Bottleneck

Large language models can resolve real repository issues, but offline, quantized, budget-constrained settings expose failure modes hidden in interactive use. The competition requires an ADK agent package that runs in an isolated sandbox with no network, 4x L4 GPUs, and either `gemma-4-31b-it-qat-w4a16-ct` or `gemma-4-e4b-it-qat-w4a16-ct`. Each task allows at most 28 tool calls, 8 minutes, 80 turns, and 240-second command timeouts; scoring must finish within 12 hours across roughly 120 tasks.

Our research questions: (1) which harness-level safeguards dominate score in this regime; (2) when do code-graph and embedding tools help localization, and when do they hurt; (3) how do context compaction and vLLM ceilings interact with prompt design; (4) how does behavior change when scaling from 31B to the 4B E4B model. We answer with live ablations (`exp01`–`exp12`) and an offline benchmark over the competition's released graph and embedding dataset. Contributions: (i) a reproducible failure taxonomy; (ii) a surgical prompt strategy with bounded length; (iii) an empirical comparison of five retrieval strategies across 129 tasks; (iv) a cross-scale analysis for the Small Model prize.

## 2. Harness Mechanics & Silent Failure Taxonomy

We discovered four silent killers through ablations.

(i) ADK compaction amnesia. At 14,336 tokens, ADK compaction strips all tool calls and outputs, keeping only plain-text model messages outside `think` blocks; agents wake up blind and loop. Our `exp10-consolidated` adds a one-line `STATE: <file:line> | <fix> | <step>` header every turn, which survives compaction.

(ii) vLLM context overflow. vLLM throws `ContextWindowExceededError` when `prompt + max_output > 32768`; with `max_output_tokens=8192`, any prompt over 24,576 tokens crashes the session. Lowering to 6144 adds 2,048 tokens of prompt headroom while preserving a 4,096 thinking budget.

(iii) `.gitignore` silent drops. `submit_patch` runs `git add -N .`, which respects `.gitignore`; new source files on ignored paths never reach the diff. `exp03` scored 0.17; `exp05` added `git status --short` and `git add -N -f <path>` and reached 0.20.

(iv) Tool/prompt bloat (not significant). `exp05` scored 0.20; `exp08` added 554 characters of tool-usage prose and scored 0.17, but 0.17 is the pooled 31B baseline (52/290 = 0.179); the difference is within run-to-run noise (SD ~1.0-1.5 tasks on the fixed 58). `exp10-consolidated` keeps the prompt within +150 characters of `exp05`. We do not claim attention dilution as a finding.

Additional safeguards: drop three unused graph tools from `agent.yaml`, enforce `max_time_minutes=7`, and require an early on-disk edit by Call 8–10.

### 2.2 Verified ADK 1.36.1 Runtime Mechanics

The following are pinned to the installed wheels (`.venv-harness`, ADK 1.36.1, `adk_submission 0.2.13`), not to the stale checkpoint docs:

- **Compaction is interval-based.** `compaction_interval=15`, `overlap=2`, `event_retention=5`, trigger `token_threshold=14336`. When a reasoning model emits zero plain text (all tokens inside `<think>`), compaction discards every tool result and leaves the model stateless. Our `STATE:` header survives because it is emitted as plain text every turn.
- **vLLM 0.19.1 reasoning drop.** `chat_utils.py:1512` reads `reasoning_content` (OpenAI convention) while Gemma 4 emits `reasoning`; thoughts are dropped between turns unless the client handles `include_thoughts`. We set `include_thoughts: true` with a 4096 budget and rely on the plain-text STATE line.
- **`.gitignore` silent drops.** `submit_patch` runs `git add -N .`, honouring `.gitignore`; a new source file on an ignored path never reaches the diff. `exp05` added `git status --short` + `git add -N -f <path>` and gained +0.03.
- **SkillToolset execution.** Skills materialise in a `tempfile.TemporaryDirectory()` (never `/workspace/skills`); `run_skill_script` takes `skill_name` + `file_path` + `args` as a **list** (no `command`; schema `{args, file_path, positional_args, short_options, skill_name}`, required `[skill_name, file_path]`). Output is untruncated (`skill_toolset.py:689`); our `OUT_CAP=3500` is the safety net. Skill names must be kebab-case and are validated at compile time.

### Table 1 — Live Leaderboard Ablations & Binomial SE (n = 58 resolved tasks)

| Ref | Name | Scale | Score | SHA-256 (short) | Resolved tasks | Binomial SE | Config delta |
|---|---|---|---:|---|---:|---:|---|
| exp01 | exp01 (v1) | 31B | 0.05 | — | 2.9 | 0.0286 | baseline v1 |
| exp02 | exp02 (v2) | 31B | 0.08 | — | 4.64 | 0.0356 | thinking on, 6 min/60 calls/120 turns |
| exp03 | exp03 baseline replica | 31B | 0.17 | e3be904c… | 9.86 | 0.0493 | byte-exact public 0.17 replica |
| exp04 | exp04 py_compile | 31B | — | 71bf21d6… | — | — | mandatory py_compile (not submitted) |
| exp05 | exp05 patch integrity | 31B | 0.20 | 2ba7f9b1… | 11.6 | 0.0525 | pre-submit patch integrity check |
| exp08 | exp08 tool contract prompt | 31B | 0.17 | — | 9.86 | 0.0493 | +554 char tool prose (regression) |
| exp10 | exp10 consolidated | 31B | 0.17 | — | 9.86 | 0.0493 | STATE header + 6 tools |
| 57697341 | 31B-fallback | 31B | 0.13 | — | 7.54 | 0.0442 | 31B fallback |
| exp12 | exp12 timing buffer | 31B | 0.17 | — | 9.86 | 0.0493 | near-exact exp05 with 9-min buffer |
| exp11_e4b | exp11_e4b genuine E4B | E4B | 0.06 | — | 3.48 | 0.0312 | genuine E4B bundle |
| e4b-v2 | e4b-v2 (ref 57806053) | E4B | 0.05 | — | 2.9 | 0.0286 | temp 0.1 + imperative prompt (no skills) |
| exp13 | exp13 swe-toolkit v4 | 31B | not submitted (kernel verified) | c9135bcb… | — | — | deterministic locate+verify skill; kernel DONE_OK 14.4 s |
| e4b-v3 | e4b-v3 swe-toolkit | E4B | not submitted (kernel verified) | 97c25136… | — | — | E4B + swe-toolkit; kernel DONE_OK 11.8 s, zero 31B fallback |

## 3. Benchmarking Lexical, Embedding, and AST Graph Retrieval (N = 129)

We conducted an offline benchmark on all 129 evaluation tasks across four Python repositories (fastapi 67, rich 48, requests 13, httpx 1). The evaluation maps patch file paths to module dot-paths (`F_gold`) and modified symbols to AST graph node IDs (`G_gold`). Graphs are available for 125 tasks; 1 task (docs_src) lacks graph nodes.

### Methodology

M1 Lexical Grep, M2 Dense Embedding (256-dim `.npz`), M3 1-Hop AST Call Graph Expansion, M4 `swe_toolkit` (`_index.py`: stopword-filtered BM25 plus AST, traceback, and backtick boosts, file aggregation `max(node) + 0.25*sum(top3)`), M5 Hybrid RRF (`1/(60+rank_swe) + 1/(60+rank_npz)` plus a caller-edge bonus). Graphs are available for 125 of 129 tasks.

### Table 2A — Overall Recall (All 129 Tasks)

Node-level (symbol) recall:

| Method | R@1 | R@3 | R@5 | R@10 | MRR (file) | Avg latency (ms) | Avg chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1 Lexical | 0.0176 | 0.0601 | 0.0950 | 0.1156 | 0.2212 | 102.4 | 2367 |
| M2 Embedding | 0.0144 | 0.0378 | 0.0378 | 0.0776 | 0.2059 | 983.4 | 2137 |
| M3 1-Hop Graph | 0.0176 | 0.0601 | 0.0630 | 0.0748 | 0.2103 | 80.5 | 2377 |
| M4 swe_toolkit | 0.0635 | 0.1176 | 0.1614 | 0.2008 | 0.4354 | 574.1 | 2211 |
| M5 Hybrid RRF | 0.0485 | 0.1062 | 0.1491 | 0.1883 | 0.4332 | 5.0 | 2220 |

File-level (module) recall:

| Method | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| M1 Lexical | 0.0504 | 0.1819 | 0.2284 | 0.3036 | 0.2212 |
| M2 Embedding | 0.0583 | 0.1772 | 0.2163 | 0.3810 | 0.2059 |
| M3 1-Hop Graph | 0.0504 | 0.1819 | 0.2265 | 0.2846 | 0.2103 |
| M4 swe_toolkit | 0.2661 | 0.3798 | 0.4350 | 0.4587 | 0.4354 |
| M5 Hybrid RRF | 0.2466 | 0.3742 | 0.4745 | 0.5701 | 0.4332 |

### Table 2B — Per-Repository File R@5 and Issue-Type Split (File R@5 / R@10)

Per repository (M1–M5 file R@5):

| Repository | Tasks | M1 | M2 | M3 | M4 | M5 |
|---|---:|---:|---:|---:|---:|---:|
| fastapi | 67 | 0.1885 | 0.1673 | 0.1474 | 0.4791 | 0.4208 |
| rich | 48 | 0.1782 | 0.2407 | 0.2512 | 0.2801 | 0.4363 |
| requests | 13 | 0.6154 | 0.3846 | 0.5385 | 0.7692 | 0.8846 |
| httpx | 1 | 0.2857 | 0.1429 | 0.2857 | 0.5714 | 0.5714 |

Issue-type split (file R@5 / R@10):

| Split | N | M1 R@5/R@10 | M2 R@5/R@10 | M3 R@5/R@10 | M4 R@5/R@10 | M5 R@5/R@10 |
|---|---:|---|---|---|---|---|
| Traceback/explicit path | 13 | 0.2692/0.2692 | 0.2692/0.3462 | 0.1923/0.1923 | 0.6538/0.6538 | 0.7308/0.7692 |
| Behavioral/symptom-only | 116 | 0.2306/0.2969 | 0.1999/0.3605 | 0.2370/0.3017 | 0.3923/0.4124 | 0.4319/0.5295 |

### 3.1 File-Recall Ablation: Base vs. Bare-ID Boost vs. Deterministic Tie-Break

The shipped `swe_toolkit` locate engine went through three measurable revisions on the same 129-task instrument:

| Engine | R@1 | R@3 | R@5 | R@10 | zero-return | change |
|---|---:|---:|---:|---:|---:|---|
| base (BM25 + AST, no path boost) | 0.419 | 0.628 | 0.713 | 0.829 | 0.171 | — |
| v3 (naive bare-identifier path boost) | 0.419 | 0.628 | 0.729 | 0.822 | 0.178 | +0.015 R@5, −0.008 R@10 |
| v4 (reverted boost + deterministic tie-break) | 0.419 | 0.651 | 0.744 | 0.829 | 0.171 | +0.031 R@3, +0.031 R@5 vs base |

Per repository (file R@5): fastapi 0.716→0.657→0.731 (base→v3→v4); rich 0.646→0.750→0.708; requests 0.923→1.000→0.923; httpx 1.000 throughout.

The bare-identifier boost helped `rich` (+0.104 R@5) by matching test names that happen to be source identifiers, but hurt `fastapi` (−0.059) by displacing gold files with generic words (`value`, `response`, `request`) present in dozens of modules. Reverting the boost and adding deterministic tie-breakers (qualname, filepath, start_line) recovered fastapi fully and lifted overall R@3/R@5 without touching R@10.

**Any-Gold vs. Strict All-Gold.** "Any-Gold @K" on the 38 multi-file tasks is 0.763/0.816/0.895 at K=3/5/10, which reads as strong, but "Strict All-Gold @K" (every gold file in the top-K) is only 0.079/0.079/0.158. Single-pass retrieval almost never returns all files of a multi-file patch; the agent must iterate. 

### 3.2 Intra-File Symbol Recall

File-level recall hides a sharper bottleneck: a 50-line `read_file` must land on the modified function. On 121 tasks with identifiable gold symbols, the shipped engine's symbol ranking scores 0.157/0.231/0.306/0.364 at @1/3/5/10. A span-level re-ranker (signature + body token overlap, exact/trace boosts, a 1/rank file prior) over the top-8 files lifts this to 0.190/0.322/0.388/0.488 (+0.091 @3) at +0.235 s median cost. Three further levers were tested on 129 tasks:

| Variant | @1 | @3 | @5 | @10 | median re-rank (s) | change |
|---|---:|---:|---:|---:|---:|---|
| v4 shipped locate syms | 0.157 | 0.231 | 0.306 | 0.364 | — | baseline |
| v5 (top-8, base scoring) | 0.190 | 0.322 | 0.388 | 0.488 | 0.235 | +0.091 @3 |
| v5A (+top-12 scope) | 0.190 | 0.322 | 0.397 | 0.488 | 0.235 | +0.009 @5 |
| v5AB (+member-over-container boost) | 0.215 | 0.322 | 0.388 | 0.455 | 1.310 | +0.025 @1, −0.033 @10 |
| v6 (+call-site/attribute scoring) | 0.215 | 0.331 | 0.405 | 0.463 | 1.310 | +0.009 @3, +0.017 @5 |

Net v4→v6: +0.058 @1, +0.100 @3, +0.099 @5, +0.099 @10, with zero file-ranking regressions (107 unchanged ranks, 2 newly captured at rank 12, none worsened). The member boost trades @10 for @1 (right for early-exit agents). File-level recall is unchanged throughout (R@3 0.651, R@5 0.744) because the re-ranker only reorders symbols inside already-ranked files.

### 3.3 Why Raw Graph Tools Fail LLM Agents

Dot-path ID hallucination (agents pass short names that resolve only via suffix matching) and neighborhood truncation (80.9% of raw 1-hop neighborhoods exceed the 5,000-character tool cap). Hybrid RRF (`M5`) fuses lexical and embedding ranks with a small caller bonus, reaching file R@10 = 0.5701 overall and 0.5883 on in-graph tasks, beating both lexical (0.3036) and graph-only (0.2846).

## 4. The `swe_toolkit` Resource: Deterministic Localization, Triggered Playbooks & Read-Only Patch Gate

Architecture: `locate | inspect | verify`. `locate` ranks symbols and files with stopword-filtered BM25 plus AST structure, traceback, and backtick boosts, then aggregates to file level. `inspect` detects sync/async twins and callers. `verify` runs a read-only patch gate (`git diff --check`, `py_compile` on changed files, and a scope check) before submission.

### Table 3 — Gold Patch Anatomy & Playbook Trigger Distribution (129 tasks)

Gold patch anatomy (overall):

| Metric | Median | Mean | p90 |
|---|---:|---:|---:|
| Files modified | 1 | 2.16 | 4 |
| Lines added | 8 | 138.6 | 89 |
| Lines deleted | 2 | 29.2 | 24 |
| Hunks | 2 | 5.4 | 13 |

70.5% of tasks modify a single file; 29.5% modify 2+ files; 8.5% create brand-new files (quantifying the `.gitignore` / `git add -N .` surface area).

Playbook trigger distribution (10 playbooks, fired 258 times over 129 tasks; overall precision 32.6% against gold patches):

| Playbook | Triggers | Trigger % | Matches | Precision |
|---|---:|---:|---:|---:|
| FALSINESS_TRAP | 21 | 16.3 | 6 | 28.6 |
| MUTABLE_STATE | 38 | 29.5 | 5 | 13.2 |
| TYPE_SUBCLASS | 68 | 52.7 | 16 | 23.5 |
| ASYNC_SYNC_TWIN | 0 | 0.0 | 0 | 0.0 |
| FASTAPI_PYDANTIC | 40 | 31.0 | 20 | 50.0 |
| RICH_RENDERING | 34 | 26.4 | 27 | 79.4 |
| HTTP_URL_COOKIES | 37 | 28.7 | 9 | 24.3 |
| DECORATOR_WRAP | 3 | 2.3 | 0 | 0.0 |
| EXCEPTION_CHAIN | 15 | 11.6 | 1 | 6.7 |
| REGISTRATION_SIBLING | 2 | 1.6 | 0 | 0.0 |

The 8/8 adversarial torture tests pass: empty patch, syntax error, ignored new file, twin-method mismatch, falsy input, mutable default, subclass, and redirect auth leak.

## 5. Cross-Scale Analysis: Gemma 4 31B vs. Gemma 4 E4B

Hardware and KV-cache math on 4x L4: the 31B QAT model occupies ~18 GB of weights, leaving room for a ~1.4x 32k context capacity; the 4B E4B model occupies ~3.5 GB, allowing ~20x 32k context capacity. The 31B model tolerates schema-heavy tool sets and longer prompts; the 4B model is schema-sensitive and needs imperative, short prompts. Empirically, the best 31B configuration scores 0.20 (`exp05`) while the genuine E4B submission (`exp11_e4b`) scores 0.06; `e4b-v2` (temp 0.1 + imperative prompt, ref 57806053) scored 0.05.

**Statistical resolution: two different noises.** Within-split run-to-run SD on the fixed 58 public tasks is sqrt(sum p_i(1-p_i)) ≈ 1.0-1.5 tasks (our 31B runs scored 12, 10, 10, 10, 10 tasks, empirical SD 0.89), because most tasks have p_i near 0 or 1. Cross-split Public→Private SE is sqrt(p(1-p)/58) ≈ 0.052 (~3 tasks) and measures drawing a different 58-task sample. We do not claim "attention dilution" as a finding: `exp03`, `exp08`, `exp10`, and `exp12` all scored 10 tasks, indistinguishable from the pooled baseline of 10.4; only `exp05`'s 12 is anomalous (+1.6 SD). The only reproducible intervention is `exp05`'s patch-integrity gate (+2 tasks).

**Why offloading is the lever for 4B.** The 4B model's failure modes are edit fidelity (exact `old_string` restoration) and low-precision exploration (self-composed `git grep` one-liners), neither of which responds to prompt compression or temperature (both tested: `e4b-v2` stayed at 0.05). Offloading localization to a deterministic stdlib skill (`swe_toolkit locate`, file R@5 0.744 on identical snapshots, no model inference) and verification to a read-only patch gate (`swe_toolkit verify`: AST compile, protected-path, stray-file, ignored-file checks) converts two inference-bound, error-prone steps into one tool call each. Predicted `e4b-v3` (E4B + `swe-toolkit`, kernel verified, zero 31B fallback): 0.09–0.13, CI [0.04, 0.16] — roughly double the current E4B rate, with the edit multiplier still binding. The 4B model benefits from the same structural safeguards but not from added prose.

## 6. Related Work, Limitations & Reproducibility

Related work: SWE-bench and SWE-agent established the patch-integrity and lint ablations we replicate; ADK provides compaction; vLLM provides the context ceiling. Limitations: our benchmark uses graph/embedding artifacts released by the competition, not full repository checkouts, so `swe_toolkit` runs on node text; playbook precision is measured by keyword heuristics, not human labels; the E4B result is from a single submission; the symbol re-ranker is a prototype (exp14 pending). Reproducibility: run `narisettichaitanya/g4-paper-graph-benchmark` (CPU, ~3 min) against `/kaggle/input/gemma-4-developer-agent`; `research/paper_eval_outputs/` contains verified JSON/Markdown. `swe_toolkit` is in `skills/swe-toolkit/`. Verified kernels: `gemma4-devagent-exp13-swe-toolkit-v2` v2 (sha256 `c9135bcb…`, 31B, DONE_OK 14.4 s) and `g4-e4b-small-agent-submit` v7 (sha256 `97c25136…`, E4B, DONE_OK 11.8 s, zero 31B fallback). Prototypes: `symrank_v5_results.json`, `symrank_v6_results.json`. Predictions: `docs/SCORE_PREDICTION_AND_ROADMAP.md`.

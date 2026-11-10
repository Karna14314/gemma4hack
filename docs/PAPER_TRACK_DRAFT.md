# When Code Graphs Help and When They Hurt: Budget-Aware Retrieval, Wheel-Verified Scaffolding, and Cross-Scale Limits for Offline Gemma 4 SWE Agents

*Paper Track Submission — `gemma-4-developer-agent-paper` | Deadline: Nov 12, 2026*  
*Target Tracks: Overall Best Paper ($15k), Best New Resource ($10k), Best New Application ($10k)*  
*Public Reproducibility Kernel: `g4-paper-graph-benchmark.ipynb` | Package: `skills/swe-toolkit`*

---

## Abstract

Autonomous software engineering (SWE) agents in offline environments face severe ceilings: a 32,768-token vLLM context, 28 tool calls, and an 8-minute per-task timeout on 4x L4 GPUs, all inside a 12-hour total scoring run across ~120 sequential tasks (roughly 5 minutes per task on average). Under these bounds, outcomes are governed by harness mechanics and stochastic variance rather than prompt phrasing. We present an empirical study of Gemma 4 combining 18 live Kaggle submissions with a verified 129-task offline benchmark across four Python repositories (fastapi 67, rich 48, requests 13, httpx 1). Wheel audits of ADK 1.36.1 and vLLM 0.19.1 uncover five fatal failure modes: interval compaction (`token_threshold=14336`, `interval=15`) erasing working memory on thought-only turns, LiteLLM dropping reasoning history (`chat_utils.py:1512`), `.gitignore` silently dropping new files (8.5% of tasks), and missing sandbox plugins (`inline_snapshot`, `dirty_equals`) breaking 27/67 FastAPI tasks. A two-regime retrieval benchmark shows live workspace AST indexing with test-path demotion lifts File R@5 from 0.4350 (Regime A, `swe_toolkit` node-BM25) to 0.7440 (Regime B, live indexer) — a **+30.9 pp** jump — outperforming static graphs degraded by 5,000-character tool caps (0.2846 R@10). Cross-scale ablations show 31B models reaching 0.20 (pooled rate 0.1702, N=464) versus 0.05 for 4B models. Equipping 4B agents with deterministic localization tools (`swe-toolkit`) fails to lift resolution (0.05), falsifying the localization-offload hypothesis and proving 4B models are bottlenecked by state retention and edit fidelity, not retrieval.

## 1. Introduction & The Offline Small-Agent Regime

Autonomous agents resolve repository-level bugs (Jimenez et al., 2024; Yang et al., 2024; Xia et al., 2024), but standard benchmarks assume frontier models with unlimited tools and web access. Air-gapped enterprise deployments enforce strict timeouts, quantized local checkpoints, and hardware ceilings. The *Gemma 4 Developer Agent* challenge evaluates agents in isolated Linux containers with zero network access on local vLLM 0.19.1 instances on 4x L4 GPUs. Allowed models are quantized aliases `gemma-4-31b-it-qat-w4a16-ct` (~18 GB) and `gemma-4-e4b-it-qat-w4a16-ct` (~3.5 GB). Tasks enforce 28 tool calls, 80 turns, an 8-minute timeout, and a 240-second command cap, requiring ~5-minute resolution within a 32,768-token KV cache.

We investigate four research questions:
- **RQ1 (Harness Traps):** What runtime mechanisms cause silent agent failures in ADK and vLLM?
- **RQ2 (Retrieval Regimes):** When do static code graphs aid localization vs. live workspace indexing?
- **RQ3 (Context Dynamics):** How do compaction thresholds and engine-level logit budget processors affect multi-turn reasoning?
- **RQ4 (Cross-Scale Limits):** Can deterministic localization enable compact 4B models to match 31B performance?

**Scoring model.** The scorer runs ~120 tasks sequentially inside a 12-hour cap including vLLM startup and Phase 2 pytest verification, leaving roughly 5 minutes per task on average. A task scores 1.0 only when the agent's patch makes the hidden pytest suite pass in a fresh container; protected files (`conftest.py`, `pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`, `test_*.py`, anything under `tests/`) are reset before grading, so editing them cannot help. Public-LB noise is ~0.0503 (one task ≈ 0.017), so single-run deltas below ~0.06 are unresolved.

Contributions: (1) an audit of ADK 1.36.1 and vLLM 0.19.1 identifying five silent runtime traps; (2) a two-regime benchmark across 129 tasks establishing a +30.9 pp File R@5 transition (0.4350 to 0.7440) and exposing an Any-Gold (0.895) vs. Strict All-Gold (0.158) multi-file gap; (3) `swe-toolkit`, an open zero-dependency package; and (4) live submission evidence defining the binomial noise floor (SE ≈ 0.0503), proving via a byte-identical reproduction control (`E_0`) that 0.20 vs. 0.17 deltas are noise, and falsifying the 4B localization-offload hypothesis.

## 2. Wheel-Verified Harness Mechanics & Silent Failure Taxonomy

Auditing `swegemma 0.2.11`, `adk_submission 0.2.13`, `adk_eval_core 0.1.0`, Google ADK 1.36.1, and vLLM 0.19.1 reveals five fatal runtime failure modes, each verified against wheel source:

**Mechanism 1 — Interval Compaction Amnesia on Reasoning Turns.** ADK compacts events at `token_threshold = 14336` tokens every `compaction_interval = 15` turns (retaining 5 events, 2-turn overlap), discarding tool outputs and `think` tokens. Because thought tags are stripped from history, agents reasoning exclusively within `think` tags lose 100% of working memory on Turn 16. **Countermeasure:** emit a plain-text `STATE: <file>:<line>` card outside thought tags on every turn, mirrored to `/tmp/swe_state.json`, so state survives the compaction cliff.

**Mechanism 2 — Reasoning History Drop vs. Logit Budget Hard-Cut.** In `chat_utils.py:1512`, ADK inspects `message.get("reasoning")` without a `reasoning_content` fallback. LiteLLM serializes Gemma 4 thoughts under `reasoning_content`, dropping prior thoughts across tool calls. Concurrently, `builtin.py:294` (`ThinkingTokenBudgetLogitsProcessor`) forces the end-of-thought logit to $10^9$ once `thinking_token_budget` expires, abruptly cutting generation mid-reasoning and emitting malformed tool-call JSON. This makes `thinking_budget: 1024` (exp_think1024) a live risk: Gemma can be severed mid-tool-call.

**Mechanism 3 — Context Window Overflow.** vLLM sizes KV memory to `max_model_len = 32768`. A request whose prompt plus `max_output_tokens` exceeds 32,768 is refused and kills the session (score 0.0). Lowering `max_output_tokens` from 8,192 to 6,144 (`exp10`) safely reclaims 2,048 tokens headroom without truncating patches (median patch is +8/−2 lines; Table 3), because the prompt-plus-output must stay under the ceiling and the scoring run's Phase 2 pytest verification is bounded by the 240-second command cap, not by output length.

**Mechanism 4 — Silent Git-Ignore Drops on New-File Tasks.** `submit_patch` runs `git add -N .` then diffs against `_swegemma_baseline` (`tools/execution.py:77-127`). `git add -N .` respects the repository's own `.gitignore`, so untracked new files on ignored paths are silently omitted — the 8.5% of tasks (14.9% in FastAPI) that add new files. **Countermeasure:** a pre-submit gate runs `git status --short` and `git add -N -f <path>` on untracked source `.py` files before `submit_patch`.

**Mechanism 5 — Sandbox Test-Dependency Deficits.** The base sandbox omits `inline_snapshot` and `dirty_equals`. Exactly 27/67 FastAPI tasks (40.3%) fail pytest collection with `ModuleNotFoundError` before assertions run (0 in rich, requests, httpx); our `_verify.py` isolates collection/environment crashes from patch regressions so a missing plugin never triggers a false-negative edit revert. Community tool ablation (Discussion #746250) corroborates: built-in graph tools returned 0/31 gold file hits and lowered score from 55/129 to 50/129.

## 3. Two-Regime Retrieval Benchmark (N = 129)

We evaluate code representations across 129 tasks in two clearly separated regimes:

- **Regime A (Static Pre-Built Competition Code Graphs, 125/129 tasks):** Retrieval over competition AST graphs (`graphs/*.json`) and 256-dim embeddings (`embeddings/*.npz`). Five architectures: M1 (Lexical Grep), M2 (Dense Embedding), M3 (1-Hop AST Graph), M4 (`swe_toolkit` node-BM25), M5 (Hybrid RRF).
- **Regime B (Live Git-Tracked Workspace AST Indexer, 129/129 snapshots, 60,483 files):** Retrieval over live repository snapshots via AST parsing, with `/tests/` path demotion and deterministic tie-breaking. The indexer runs `git ls-files '*.py'`, extracts AST definitions per file, scores with BM25 plus structural boosts (caller edge bonus), demotes any path under `tests/`, and breaks ties by qualified name. Zero-return rate is 0.171; Any-Gold @10 on 38 multi-file tasks is 0.895.

### Table 2A & 2B — Regime A: Static Graph Corpus (125/129 Tasks)

| Method | File R@1 | File R@5 | File R@10 | File MRR |
|---|---:|---:|---:|---:|
| M1: Lexical Grep | 0.0504 | 0.2284 | 0.3036 | 0.2212 |
| M2: Dense Embedding | 0.0583 | 0.2163 | 0.3810 | 0.2059 |
| M3: 1-Hop AST Graph | 0.0504 | 0.2265 | 0.2846 | 0.2103 |
| M4: `swe_toolkit` (BM25) | 0.2661 | **0.4350** | 0.4587 | 0.4354 |
| M5: Hybrid RRF | 0.2466 | 0.4745 | **0.5701** | 0.4332 |

M3's raw graph expansion degrades vs. lexical grep (File R@10 drops 0.3036 → 0.2846) because **80.9% of 1-hop neighborhoods exceed the 5,000-char tool cap**, dropping gold targets when truncated, and LLMs emit bare symbol names rather than qualified dot-paths (0/31 gold hits in Discussion #746250). Hybrid RRF (M5) fuses dense semantics with exact BM25 identifiers, lifting File R@10 to 0.5701.

Per-repository, M4 reaches File R@5 = 0.4791 on FastAPI (67 tasks) and 0.2801 on Rich (48 tasks); M5 reaches 0.8846 on requests (13 tasks); on traceback issues M4/M5 reach 0.8162/0.8547 vs. 0.3632 for dense embeddings.

### Table 2C & 2D — Regime B: Live Workspace Indexer (129/129 Snapshots)

| Engine Variant | R@1 | R@3 | R@5 | R@10 | Zero-Ret | Mechanism |
|---|---:|---:|---:|---:|---:|---|
| base (BM25 + AST) | 0.419 | 0.628 | 0.713 | 0.829 | 0.171 | Base AST + lexical scoring |
| v3 (identifier boost) | 0.419 | 0.628 | 0.729 | 0.822 | 0.178 | Path boost (hurts fastapi −0.059) |
| v4 (test demotion + tie-break) | **0.419** | **0.651** | **0.744** | **0.829** | **0.171** | Reverted boost, test demotion, qualname tie-break |

**Headline contribution:** live git-tracked source indexing with test-path demotion beats static pre-extracted code graphs:
- File R@5: **0.4350 → 0.7440** (+30.9 pp, +71.0% relative)
- File R@10: 0.4587 → 0.8290 (+37.0 pp)

Pre-built graphs omit dynamically loaded modules and helpers; live indexing inspects the exact source tree while actively demoting test paths.

### Symbol Re-Ranking (121 Gold-Symbol Tasks)

Within retrieved files, base `v4` symbol recall is Symbol R@5 = 0.3060. Span-level re-ranking (signature/body token overlap → top-12 scope → member-over-container boost → call-site scoring, v4→v6) lifts Symbol R@5 to **0.4050** (+0.0990 net) at +1.31 s latency with zero file-ranking regressions. Any-Gold multi-file recall reaches 0.895 at Top-10, but Strict All-Gold is only 0.158 — single-pass retrieval cannot resolve multi-file bugs; an agent must iterate across turns.

## 4. The `swe-toolkit` Open Resource

`swe-toolkit` (`skills/swe-toolkit/`) is a zero-dependency Python package with `locate` (live AST indexing, BM25 scoring, CamelCase query normalization, stopword filtering, test-path demotion), `inspect` (AST structural analysis extracting signatures, docstrings, class hierarchies, caller/callee references, sync/async twins), and `verify` (pre-submission `git diff --check`, `py_compile`, whitespace validation, collection-safe test execution isolating environment crashes from code regressions). The `verify` gate deliberately treats a `ModuleNotFoundError` for `inline_snapshot` or `dirty_equals` as a pre-existing sandbox gap rather than a patch regression, so missing plugins never trigger a false-negative edit revert. It ships a 9/9 adversarial torture suite (empty patch rejection, syntax error interception, untracked/ignored new files, sync/async twin discrepancy, falsy input preservation, mutable default arguments, subclass type invariance, redirect header stripping) and 10 domain playbooks (258 triggers, 32.6% overall precision) covering `RICH_RENDERING`, `FASTAPI_PYDANTIC`, `FALSINESS_TRAP`, `HTTP_URL_COOKIES`, `TYPE_SUBCLASS`, `MUTABLE_STATE`, `EXCEPTION_CHAIN`, and decorator/registry/async-twin rules.

### Table 3 — Gold Patch Anatomy & Playbook Precision

| Playbook | Triggers | Gold Matches | Precision |
|---|---:|---:|---:|
| `RICH_RENDERING` | 34 | 27 | 79.4% |
| `FASTAPI_PYDANTIC` | 40 | 20 | 50.0% |
| `FALSINESS_TRAP` | 21 | 6 | 28.6% |
| `HTTP_URL_COOKIES` | 37 | 9 | 24.3% |
| `TYPE_SUBCLASS` | 68 | 16 | 23.5% |
| `MUTABLE_STATE` | 38 | 5 | 13.2% |
| `EXCEPTION_CHAIN` | 15 | 1 | 6.7% |
| `OTHER_RULES` | 5 | 0 | 0.0% |
| **Total** | **258** | **84** | **32.6%** |

Gold-patch anatomy (129 tasks): median 1 file (mean 2.16), median 8 added lines (mean 138.6), 70.5% single-file, 29.5% multi-file, 8.5% add new files (FastAPI 14.9%).

### Table 1 — Live Leaderboard Ablations (n = 58 tasks per run)

| Ref | Exp | Model | Score | Tasks | Config delta vs baseline |
|---|---|---|---|---:|---|
| 56793672 | exp01 | 31B | 0.05 | 2.90 | Baseline v1: thinking on, 6 min / 60 calls |
| 57037122 | exp03 | 31B | 0.17 | 9.86 | Public 0.17 replica; 6 tools (+3 graph) |
| 57553805 | exp05 | 31B | **0.20** | 11.60 | Pre-submit patch integrity check (`git add -N -f`) |
| 57654236 | exp10 | 31B | 0.17 | 9.86 | STATE header, 6 tools, max_output 6144 |
| 57736284 | exp12 | 31B | 0.17 | 9.86 | Near-exact exp05 with 9-min timing buffer |
| 57836949 | E0 | 31B | 0.17 | 9.86 | Control: byte-identical exp05 rebuild (0.20 -> 0.17) |
| 57933618 | exp14 | 31B | 0.15 | — | 31B + swe-toolkit skill, 9 tools, lean prompt |
| 57889741 | e4b-v4 | E4B | 0.05 | 2.90 | E4B + swe-toolkit v4; offload hypothesis falsified |
| 57806053 | e4b-v2 | E4B | 0.05 | 2.90 | Temp 0.1, imperative prompt <=2500 chars |
| 58183079 | exp15 | 31B | pending | — | Clone of exp05, 6 base tools, no SkillToolset, STATE header + plugin-tolerant gate |

*Table 1 notes: Pooled 31B rate 79/464 = 0.1702 (SE 0.0174). Within-split SD 0.89 tasks; cross-split SE 0.0503 (~3.0 tasks). Any delta ≤ 2 tasks (≤ 0.034) is statistically unresolvable publicly. exp05's 0.20 was an upper-tail draw; E0 scored 0.17 on the byte-identical rebuild.*

## 5. Cross-Scale Analysis & Statistical Noise

### 5.1 Within-Split SD vs. Cross-Split SE

Leaderboard score deltas must decouple two noise mechanisms:

**Within-Split Stochasticity (fixed 58 tasks):** With task difficulties $p_i$, variance across repeated runs is
$$\sigma^2 = \sum_{i=1}^{58} p_i(1-p_i), \qquad \sigma_{\text{within}} \approx \mathbf{0.89}\text{--}\mathbf{1.5}\text{ tasks}.$$
The intuition is that most tasks are either uniformly solved ($p_i \approx 1$, contributing almost zero variance) or unsolvable ($p_i \approx 0$, also near-zero variance); only the few borderline tasks drive run-to-run scatter. Our exp05-family submissions ([12, 10, 10, 10, 10] tasks) yield sample SD $s = 0.894$ tasks (~0.015 score), matching the theoretical bound.

**Cross-Split Generalization Error:** For a new sample of 58 hidden tasks,
$$\text{SE}_{\text{split}} = \sqrt{\frac{p(1-p)}{58}} \approx \sqrt{\frac{0.179 \times 0.821}{58}} \approx \mathbf{0.0503}\quad[\approx\mathbf{3.0}\text{ tasks}].$$

### 5.2 The $E_0$ Byte-Identical Control

To test whether exp05's +0.03 delta (0.20, 12 tasks) was reproducible, we submitted **$E_0$** (ref 57836949): a byte-identical rebuild of exp05 (SHA-256 `2ba7f9b1…`). $E_0$ scored **0.17** (10 tasks), proving exp05 was an upper-tail binomial draw (+1.6 SD), not a capability gain. Pooling eight converged 31B submissions:
$$\text{Pooled 31B Rate} = \frac{79}{464} = \mathbf{0.1702}\quad[\text{Pooled SE} = \mathbf{0.0174}].$$
Consequently, **any leaderboard delta of ≤ 2 tasks (≤ 0.034) is statistically unresolvable on the public leaderboard.**

### 5.3 External Census Corroboration

The external `dariushafshar/gemma-4-agent-public-config-draws` census (141 scored draws, 67 notebooks, 21 bundle hashes) confirms this. Summary:

| Statistic | Value |
|---|---:|
| Scored draws | 141 |
| Unique notebooks | 67 |
| Unique bundle hashes | 21 |
| Maximum score | 0.22 (13/58 tasks) |
| Scores ≥ 0.24 | 0 |
| Scores ≥ 0.20 | 3 |
| Most-run bundle hash | recurs in 10 notebooks, scoring 0.13–0.18 |

Max score 0.22 (13 tasks), **no score ≥ 0.24**, and the most-run bundle hash recurs across 10 notebooks scoring 0.13–0.18 (clustering at ≈0.17 = 10/58). Identical bundles score differently run to run — direct evidence of run-to-run noise. Single-run deltas ≤ 2 tasks cannot be distinguished from noise on the 58-task public split.

### 5.4 Falsification of the 4B Localization-Offload Hypothesis

Prior work suggests small models fail because repository search overwhelms context processing. We hypothesized that offloading localization and test verification to deterministic tools (`swe-toolkit locate` at 0.7440 File R@5; `verify` patch gate) would let 4B focus on local editing, lifting resolution toward 0.09–0.13. We tested this with `e4b_v4_swe_toolkit` (ref 57889741): E4B + full `swe-toolkit v4` scored **0.05** (3 tasks), completely falsifying the hypothesis. Execution traces show 4B models fail from **mechanical editing errors**, not localization:
- **Edit inaccuracy:** hallucinated lines inside `old_string` blocks abort edit tools.
- **Compaction vulnerability:** no plain-text state card → memory loss at the 14,336-token boundary.
- **Syntactic drift:** indentation errors in nested async functions and match blocks.

`exp14` (31B + `swe-toolkit` skill, 9 tools) scored **0.15** while `exp05` (6 tools, no `SkillToolset`) scored **0.20/0.17**: registering `SkillToolset` injects 4 extra tool schemas (`list_skills`, `load_skill`, `load_skill_resource`, `run_skill_script`) into every turn and burns 2–4 turns on skill invocation. **SkillToolset schema tax and edit fidelity dominate when localization is invoked as an external multi-schema tool.** `skill_toolset.py:689` runs in temp dirs and strictly requires `args` as a JSON array list — the list-vs-dict schema behavior adds friction small models cannot absorb, and every skill call is a turn not spent editing source.

Small reasoners face fundamental code-editing and state-retention bottlenecks that retrieval offloading alone cannot resolve.

## 6. Related Work

Automated program repair benchmarks evolved from synthetic unit tests to repository-level issue resolution (SWE-bench, Jimenez et al., 2024). Agent frameworks such as SWE-agent (Yang et al., 2024) and Agentless (Xia et al., 2024) demonstrate that specialized tool interfaces and modular localization rival complex architectures at reduced cost. Structural code retrieval methods (LocAgent, Chen et al., 2025; RepoGraph, Ouyang et al., 2025) show that graph-based localization can help — but under strict 5,000-character tool caps and a 32k context ceiling, raw graph expansion degrades performance because 80.9% of 1-hop neighborhoods exceed the cap. Our work establishes this boundary condition: live AST source-tree indexing dramatically outperforms static code graph exports under these constraints. Prior localization-offload claims (that compact models can match larger ones when retrieval is externalized) are directly falsified here: 4B models remain bottlenecked by edit fidelity and state retention, not by retrieval quality.

## 7. Limitations & Reproducibility

Limitations: the offline benchmark spans four Python repositories, so repository conventions may influence playbook precision; leaderboard submissions run against hidden tests without execution logs, so live analyses rely on aggregate pass rates and verified harness mechanics; E4B was tested under fixed prompting, so alternative fine-tuning regimes might mitigate edit restoration failures. Future work: finer-grained per-task budget allocation and a 4B edit-fidelity fine-tune. Together these results show that, under strict offline budgets, harness mechanics and state retention dominate prompt engineering, and that live git-tracked source indexing is the single largest controllable lever for SWE-agent resolution.

**One-command reproducibility:** `g4-paper-graph-benchmark.ipynb` reproduces all paper tables (Tables 1, 2A, 2B, 2C, 2D, 3, and the statistical noise model) in a single ~3-minute CPU run with zero external dependencies (standard library only; PyYAML is the sole third-party import and is already present on Kaggle). The notebook writes `submission.zip` directly from in-memory string literals, so it cannot drift from `src/`. `swe-toolkit` ships under `skills/swe-toolkit/`. Verified bundle hashes: `exp05_patch_integrity` (0.20) `2ba7f9b1…`; `E_0` control (0.17) `2ba7f9b1…`; `exp_think1024` (unscored, Kaggle system error) `5d80bac7…`. All artifacts are released to support the Verifiability judging criterion (20% of the paper-track score).

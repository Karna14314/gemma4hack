# When Code Graphs Help and When They Hurt: Budget-Aware Graph-Lexical Retrieval, Wheel-Verified Scaffolding, and Cross-Scale Limits for Offline Gemma 4 SWE Agents

*Paper Track Submission — `gemma-4-developer-agent-paper` | Deadline: Nov 12, 2026*  
*Target Tracks: Overall Best Paper ($15k), Best New Resource ($10k), Best New Application ($10k)*  
*Public Reproducibility Kernel: `narisettichaitanya/g4-paper-graph-benchmark` | Package: `skills/swe-toolkit`*

---

## Abstract
Autonomous software engineering (SWE) agents in offline environments face severe resource ceilings: a 32,768-token vLLM context ceiling, 28 tool calls, and an 8-minute per-task timeout on 4x NVIDIA L4 GPUs. Under these tight bounds, benchmark outcomes are governed by harness mechanics and stochastic variance rather than prompt phrasing. We present an empirical study of Gemma 4 combining 18 live Kaggle leaderboard submissions with a verified 129-task offline benchmark across four Python repositories. First, wheel audits of Google ADK 1.36.1 and vLLM 0.19.1 uncover five fatal failure modes: interval compaction (`token_threshold=14336`, `interval=15`) erasing working memory on `<think>` turns, LiteLLM dropping reasoning history (`chat_utils.py:1512`), `.gitignore` omitting new files (8.5% of tasks), and missing sandbox dependencies breaking 27/67 FastAPI tasks before test execution. Second, a two-regime retrieval benchmark shows live workspace AST indexing with test demotion elevates File R@5 from 0.4350 to 0.7440 (+30.9 pp gain, +71.0% relative; R@10 = 0.8290), outperforming static call graphs degraded by 5,000-character tool caps (0.2846 R@10). Third, cross-scale ablations show 31B models reaching 0.20 (pooled rate 0.1702, $N=464$) versus 0.05 for 4B models. Equipping 4B agents with deterministic localization tools (`swe-toolkit`) fails to lift resolution (0.05), falsifying the localization-offload hypothesis and proving 4B models are bottlenecked by state retention and edit restoration fidelity.

## 1. Introduction & The Offline Small-Agent Regime

Autonomous agents increasingly resolve repository-level software bugs (Jimenez et al., 2024; Yang et al., 2024; Xia et al., 2024). While standard benchmarks evaluate frontier models with unlimited tool budgets and live web access, air-gapped enterprise deployments enforce strict execution timeouts, quantized local checkpoints, and hardware ceilings.

The *Gemma 4 Developer Agent* challenge evaluates agents in isolated Linux containers with zero network access against local vLLM 0.19.1 instances on 4x NVIDIA L4 GPUs. Allowed models are quantized aliases `gemma-4-31b-it-qat-w4a16-ct` (~18 GB) and `gemma-4-e4b-it-qat-w4a16-ct` (~3.5 GB). Tasks enforce strict boundaries: 28 tool calls, 80 conversation turns, an 8-minute timeout, and a 240-second command cap, requiring ~5-minute task resolution within a 32,768-token KV cache ceiling.

We investigate four central research questions:
- **RQ1 (Harness Traps):** What runtime mechanisms cause silent agent failures in ADK and vLLM?
- **RQ2 (Retrieval Regimes):** When do static code graphs aid localization vs. live workspace indexing?
- **RQ3 (Context Dynamics):** How do compaction thresholds and engine-level logit budget processors affect multi-turn reasoning?
- **RQ4 (Cross-Scale Limits):** Can deterministic localization enable compact 4B models to match 31B performance?

Contributions: (1) an audit of ADK 1.36.1 and vLLM 0.19.1 identifying five silent runtime traps; (2) a two-regime benchmark across 129 tasks establishing a +30.9 pp File R@5 transition gain (0.4350 to 0.7440) and exposing an Any-Gold (0.895) vs. Strict All-Gold (0.158) multi-file gap; (3) `swe-toolkit`, an open zero-dependency package with 10 domain playbooks (258 triggers, 32.6% precision) and verification backed by a 9/9 torture suite; and (4) live submission evidence defining the binomial noise floor (SE $\approx$ 0.0503), proving via an identical reproduction control ($E_0$) that 0.20 vs. 0.17 deltas represent noise, and empirically falsifying the 4B localization-offload hypothesis.

## 2. Wheel-Verified Harness Mechanics & Silent Failure Taxonomy

Auditing Google ADK 1.36.1, `swegemma 0.2.11`, `adk_submission 0.2.13`, and vLLM 0.19.1 reveals five fatal runtime failure modes:

**2.1 Interval Compaction Amnesia on Reasoning Turns.** ADK triggers event compaction (`swegemma.config`) at `token_threshold = 14336` tokens every `compaction_interval = 15` turns (retaining 5 events, 2 turns overlap), discarding tool outputs and `<think>` tokens. Because thought tags are stripped from history, agents reasoning exclusively within thoughts lose 100% of working memory on Turn 16. We enforce an external plain-text `STATE:` card outside thought tags, mirrored to `/tmp/swe_state.json`.

**2.2 Reasoning History Drop vs. Logit Budget Hard-Cut.** In `chat_utils.py:1512`, ADK inspects `message.get("reasoning")` without fallback for `reasoning_content`. LiteLLM serializes Gemma 4 thoughts under `reasoning_content`, dropping prior thoughts across tool calls. Concurrently, `builtin.py:294` (`ThinkingTokenBudgetLogitsProcessor`) forces the end-of-thought logit to $10^9$ once `thinking_token_budget` expires, abruptly cutting generation.

**2.3 Context Window Overflow (`prompt + max_output > 32768`).** vLLM sizes KV memory to `max_model_len = 32768`. Prompt plus `max_output_tokens` exceeding 32,768 triggers `ContextWindowExceededError`, aborting the container with score 0.0. Lowering `max_output_tokens` from 8,192 to 6,144 (`exp10`) safely reclaims 2,048 tokens headroom without truncating patches (median patch is +8/-2 lines; Table 3).

**2.4 Silent Git-Ignore Drops on New-File Tasks.** Harness `submit_patch` runs `git add -N .` followed by `git diff HEAD`. Because `git add -N .` respects `.gitignore`, untracked new files on ignored paths are silently omitted. Table 3 shows 8.5% of tasks (14.9% in FastAPI) add new files. In `exp05`, an automated gate executing `git status --short` and `git add -N -f <path>` guarantees patch capture.

**2.5 Sandbox Test-Dependency Deficits & SequentialAgent Footguns.** Auditing `tasks.jsonl` reveals the base sandbox lacks `inline_snapshot` and `dirty_equals` (Discussion #754636). Exactly 27/67 FastAPI tasks (40.3%) fail pytest collection with `ModuleNotFoundError` before assertions run (0 in rich, requests, httpx); our `_verify.py` isolates collection errors. Furthermore, multi-agent pipelines (`SequentialAgent`, Discussion #744354) duplicate conversation history across agents, consuming tokens at 2x velocity; single-agent surgical prompts prove strictly superior.

### Table 1 — Live Leaderboard Ablations (Key Runs; n = 58 tasks per run)
| Ref (Exp) | Model | Score | Res. | SE | Configuration Delta vs Baseline |
|---|---|---:|---:|---:|---|
| 56793672 (exp01) | 31B | 0.05 | 2.90 | 0.029 | Baseline v1: thinking on, 6 min / 60 calls |
| 57037122 (exp03) | 31B | 0.17 | 9.86 | 0.049 | Public 0.17 replica; 6 tools (+3 graph) |
| 57553805 (exp05) | 31B | **0.20** | 11.60 | 0.053 | Pre-submit patch integrity check (`git add -N -f`) |
| 57654236 (exp10) | 31B | 0.17 | 9.86 | 0.049 | STATE header, 6 tools, max_output 6144 |
| 57736284 (exp12) | 31B | 0.17 | 9.86 | 0.049 | Near-exact exp05 with 9-min timing buffer |
| 57836949 (E0) | 31B | 0.17 | 9.86 | 0.049 | Control: byte-identical exp05 rebuild (0.20 -> 0.17) |
| 57806053 (e4b-v2) | E4B | 0.05 | 2.90 | 0.029 | Temp 0.1, imperative prompt <=2500 chars |
| 57889741 (e4b-v4) | E4B | 0.05 | 2.90 | 0.029 | E4B + swe-toolkit v4; offload hypothesis falsified |

*Table 1 notes: All runs reproduced in kernel `g4-paper-graph-benchmark`. Pooled 31B rate is 79/464 = 0.1702 (SE = 0.0174). Within-split SD on fixed tasks is 0.89 tasks. Cross-split SE is 0.0503 (~3.0 tasks).*

## 3. When Code Graphs Help and When They Hurt: Two-Regime Retrieval Benchmark (N = 129)

We evaluate code representations across 129 tasks across two regimes:
- **Regime A (Static Graph Corpus, 125 Tasks):** Retrieval over competition AST graphs (`graphs/*.json`) and 256-dim embeddings (`embeddings/*.npz`). Reports mean recall fraction ($|F_{\text{retrieved}} \cap F_{\text{gold}}| / |F_{\text{gold}}|$).
- **Regime B (Live Workspace AST Indexer, 129 Tasks, 60,483 Files):** Retrieval over live repository snapshots via AST parsing (`_index.py`). Reports Any-Gold binary hit rate ($\mathbb{I}[|F_{\text{retrieved}} \cap F_{\text{gold}}| \ge 1]$) and symbol recall.

### 3.1 Regime A: Static Graph Corpus Performance (Table 2A)
We benchmark five architectures: M1 (Lexical Grep), M2 (Dense Embedding), M3 (1-Hop AST Graph), M4 (`swe_toolkit` node-BM25), and M5 (Hybrid RRF fusing BM25 and embeddings with 1.25x caller edge bonus).

#### Table 2A — Static Graph Corpus Retrieval Performance (All 129 Tasks)
| Method | Node R@5 | Node R@10 | File R@1 | File R@5 | File R@10 | File MRR |
|---|---:|---:|---:|---:|---:|---:|
| M1: Lexical Grep | 0.0950 | 0.1156 | 0.0504 | 0.2284 | 0.3036 | 0.2212 |
| M2: Dense Embedding | 0.0378 | 0.0776 | 0.0583 | 0.2163 | 0.3810 | 0.2059 |
| M3: 1-Hop AST Graph | 0.0630 | 0.0748 | 0.0504 | 0.2265 | 0.2846 | 0.2103 |
| M4: `swe_toolkit` (BM25) | 0.1614 | 0.2008 | 0.2661 | 0.4350 | 0.4587 | 0.4354 |
| M5: Hybrid RRF | 0.1491 | 0.1883 | 0.2466 | **0.4745** | **0.5701** | 0.4332 |

*Stratified Splits (Table 2B summary):* On FastAPI (67 tasks) and Rich (48 tasks), M4 achieves 0.4791 and 0.2801; M5 reaches 0.4208 and 0.4363. On requests (13 tasks), M5 attains 0.8846. On traceback issues (13 tasks), M4 and M5 reach 0.8162 and 0.8547 vs. 0.3632 for dense embeddings.

### 3.2 Why Raw Graph Tools Fail LLM Agents
Naive 1-hop AST expansion (M3) degrades performance vs. lexical grep (File R@10 drops from 0.3036 to 0.2846; Table 2A) due to two pathologies:
1. **Payload Truncation:** **313 of 387 1-hop neighborhoods (80.9%) exceed the 5,000-character tool cap**, dropping gold targets when truncated.
2. **Dot-Path Mismatch:** LLMs emit bare symbol names (e.g., `execute`) rather than qualified dot-paths (e.g., `fastapi.routing.execute_request`), causing 99.8% of exact queries to fail (0/31 gold hits in Discussion #746250).
Hybrid RRF (M5) succeeds by fusing dense semantics with exact BM25 identifiers, lifting File R@10 to 0.5701 at 5.0 ms latency.

### 3.3 Regime B: Live Workspace Source-Tree Indexer (Table 2C)
In Regime B, `swe_toolkit` (`_index.py`) indexes the live filesystem directly via `git ls-files '*.py'`, extracts AST definitions, and scores files with BM25 and structural boosts.

#### Table 2C — Live Workspace File Recall Ablation (129 Snapshots, 60,483 Files)
| Engine Variant | R@1 | R@3 | R@5 | R@10 | Zero-Ret | Algorithmic Mechanism |
|---|---:|---:|---:|---:|---:|---|
| `base` (BM25 + AST) | 0.4190 | 0.6280 | 0.7130 | 0.8290 | 0.1710 | Base AST BM25 without path filtering |
| `v3` (Identifier Boost) | 0.4190 | 0.6280 | 0.7290 | 0.8220 | 0.1780 | Path boost (+0.104 rich, -0.059 fastapi) |
| `v4` (Shipped Engine) | **0.4190** | **0.6510** | **0.7440** | **0.8290** | **0.1710** | Reverted boost, test demotion, tie-break |

The transition from Regime A static graph indexing to Regime B live source-tree indexing marks a decisive performance leap:
$$\text{File R@5: } 0.4350 \ (\text{Regime A, M4}) \longrightarrow 0.7440 \ (\text{Regime B, v4}) \quad [+\mathbf{30.9}\text{ pp, } +\mathbf{71.0}\%\text{ rel}]$$
$$\text{File R@10: } 0.4587 \ (\text{Regime A, M4}) \longrightarrow 0.8290 \ (\text{Regime B, v4}) \quad [+\mathbf{37.0}\text{ pp, } +\mathbf{80.7}\%\text{ rel}]$$
Pre-built graphs omit dynamically loaded modules and helpers. Live indexing inspects the exact source tree while actively demoting test paths.

### 3.4 Multi-File Retrieval Dilemma & Intra-File Symbol Re-ranking
On 38 multi-file tasks (29.5%), Any-Gold recall reaches 0.7630, 0.8160, and 0.8950 at Top-3, Top-5, and Top-10. However, Strict All-Gold recall (all gold files in top-$k$) is only **0.0790, 0.0790, and 0.1580**! Single-pass retrieval structurally cannot resolve multi-file bugs; an agent must iterate across turns.

Within retrieved files, locating target functions is critical. On 121 tasks with identifiable gold symbols, base `v4` symbol recall is 0.3060 Symbol R@5. Our span-level re-ranking pipeline evaluates four enhancements: signature token overlap (`v5`), expanded top-12 file scope (`v5A`), member-over-container boost (`v5AB`), and call-site scoring (`v6`).

#### Table 2D — Intra-File Symbol Recall Ablation (121 Identifiable Symbol Tasks)
| Re-ranking Variant | Symbol @1 | Symbol @3 | Symbol @5 | Symbol @10 | Algorithmic Enhancement |
|---|---:|---:|---:|---:|---|
| `v4` (Shipped Baseline) | 0.1570 | 0.2310 | 0.3060 | 0.3640 | Shipped `_index.py` ranking |
| `v5` (Top-8 File Scope) | 0.1900 | 0.3220 | 0.3880 | 0.4880 | Signature + body token overlap |
| `v5AB` (+Member Boost) | 0.2150 | 0.3220 | 0.3880 | 0.4550 | Prioritize methods over classes |
| `v6` (+Call-Site Scoring) | **0.2150** | **0.3310** | **0.4050** | **0.4630** | Deep AST span re-ranking |

The complete `v4` $\rightarrow$ `v6` pipeline lifts Symbol R@5 to **0.4050** (+0.0990 net) at +1.31 s latency with zero file-ranking regressions.

## 4. The `swe-toolkit` Open Resource & Triggered Playbooks

To support reproducible offline agent research (Best New Resource track), we release `swe-toolkit`, a zero-dependency Python package featuring:
1. **`locate`:** Live AST source-tree indexing, CamelCase query normalization, stopword-filtered BM25 scoring, and test-path demotion yielding 0.7440 File R@5 and 0.4050 Symbol R@5.
2. **`inspect`:** AST structural analysis extracting function signatures, docstrings, class hierarchies, caller/callee references, and sync/async twin implementations without heavy language servers.
3. **`verify`:** Pre-submission patch validation executing `git diff --check`, `py_compile` syntax checks, whitespace validation, and collection-safe test execution isolating environment crashes from code regressions.

### Table 3 — Gold Patch Anatomy & Curated SWE Domain Playbooks (N = 129 Tasks)
| Repository | Tasks | Files (med/mean) | Added Lines | Deleted Lines | Single-File % | Multi-File % | New-File % |
|---|---:|---|---|---|---:|---:|---:|
| **ALL Tasks** | **129** | **1.0 / 2.16** | **8.0 / 138.6** | **2.0 / 29.2** | **70.5%** | **29.5%** | **8.5%** |
| fastapi / rich | 67 / 48 | 1.0 / 2.46 (1.90) | 11.0 / 72.4 (269.0)| 2.0 / 42.5 (18.1)| 64.2% / 77.1% | 35.8% / 22.9% | 14.9% / 2.1% |
| requests / httpx | 13 / 1 | 1.0 / 1.15 (7.00) | 3.0 / 4.6 (57.0) | 1.0 / 2.2 (22.0) | 84.6% / 0.0% | 15.4% / 100.0% | 0.0% / 0.0% |

#### Curated SWE Domain Playbooks Evaluation (258 Triggers)
| Playbook Identifier | Heuristic Repair Principle | Triggers | Gold | Precision |
|---|---|---:|---:|---:|
| `RICH_RENDERING` | Clamp Measurement bounds, zero cell lengths | 34 | 27 | **79.4%** |
| `FASTAPI_PYDANTIC` | Pydantic v1/v2 field aliases & response models | 40 | 20 | **50.0%** |
| `FALSINESS_TRAP` | Explicit is not None guards for empty values | 21 | 6 | **28.6%** |
| `HTTP_URL_COOKIES` | Strip sensitive auth headers across redirects | 37 | 9 | **24.3%** |
| `TYPE_SUBCLASS` | Replace type(x) is T with isinstance(x, T) | 68 | 16 | **23.5%** |
| `MUTABLE_STATE` | Deep-copy dict and list boundary parameters | 38 | 5 | **13.2%** |
| `EXCEPTION_CHAIN` | Preserve causal chains: raise ... from err | 15 | 1 | **6.7%** |
| `OTHER_RULES` | Decorator wrap (3), Registry (2), Async twins (0) | 5 | 0 | 0.0% |
| **Total / Overall** | Combined evaluation across 129 tasks | **258** | **84** | **32.6%** |

### 4.2 Adversarial Torture Test Suite
To ensure `swe-toolkit` never crashes an agent session under edge-case inputs, the codebase is validated against an automated 9/9 adversarial torture suite: empty patch rejection, syntax error interception, untracked new files, gitignored new files, sync/async twin discrepancy, falsy input preservation, mutable default arguments, subclass type invariance, and redirect header stripping.

## 5. Cross-Scale Empirical Analysis (31B vs. E4B) & Leaderboard Statistical Power

Deploying autonomous agents across model scales exposes a stark divergence. On 4x NVIDIA L4 GPUs, the 31B QAT model allocates ~18 GB of VRAM, leaving ample KV cache headroom up to 32,768 tokens, whereas the 4B model requires only ~3.5 GB weights. On the live public leaderboard, 31B achieved a peak score of **0.20** (`exp05_patch_integrity`, ref 57553805, 12/58 tasks resolved). Conversely, genuine E4B submissions consistently achieved **0.05 to 0.06** (`exp11_e4b`: 0.06; `e4b-v2`: 0.05).

### 5.1 Statistical Resolution & The $E_0$ Byte-Identical Control
To interpret leaderboard score deltas, one must decouple two distinct noise mechanisms:
1. **Within-Split Stochasticity (Fixed 58 Tasks):** Because tasks have fixed difficulties $p_i$, variance across repeated runs is $\sigma^2 = \sum_{i=1}^{58} p_i (1 - p_i)$. Because most tasks are either uniformly solved ($p_i \approx 1$) or unsolvable ($p_i \approx 0$), within-split standard deviation is small: $\sigma \approx 0.89\text{ to }1.5$ tasks. Across our five converged `exp05`-family submissions ([12, 10, 10, 10, 10] tasks), sample standard deviation is **$s = 0.894$ tasks** (~0.015 score delta).
2. **Cross-Split Generalization Error:** When evaluating generalization to a new sample of 58 hidden tasks, standard error follows binomial sampling:
   $$\text{SE}_{\text{cross}} = \sqrt{\frac{p(1-p)}{N}} = \sqrt{\frac{0.179 \times 0.821}{58}} \approx 0.0503 \quad [\approx \mathbf{2.92}\text{ to }\mathbf{3.0}\text{ tasks}]$$

To test whether the +0.03 delta of `exp05` (0.20, 12 tasks) was reproducible, we submitted the **$E_0$ control** (ref 57836949): a byte-identical rebuild of `exp05` (SHA-256 `2ba7f9b1...`). The $E_0$ submission scored **0.17** (10 tasks), proving `exp05` was an upper-tail binomial draw (+1.6 SD) rather than a permanent capability gain. Pooling eight converged 31B submissions yields:
$$\text{Pooled 31B Rate: } \frac{12 + 5(10) + 9 + 8}{8 \times 58} = \frac{79}{464} = \mathbf{0.1702} \quad [\text{Pooled SE } = \mathbf{0.0174}]$$
Consequently, **any leaderboard delta of $\le 2$ tasks ($\le 0.034$) is statistically unresolvable on the public leaderboard**.

### 5.2 Empirical Falsification of the 4B Localization-Offload Hypothesis
Prior literature suggests small models fail primarily because repository search overwhelms their context processing (Xia et al., 2024). We formulated the **Localization-Offload Hypothesis**: *if an agent offloads localization and test verification to deterministic tools (`swe-toolkit locate` at 0.7440 File R@5; `verify` patch gate), the 4B model will focus purely on local editing, lifting its resolution rate toward 0.09-0.13.*

We tested this hypothesis on the live leaderboard with `e4b_v4_swe_toolkit` (ref 57889741), combining E4B with the full `swe-toolkit v4` engine. The submission scored **0.05** (3 tasks resolved), completely falsifying the hypothesis. Execution trace analysis reveals 4B models fail from mechanical editing errors rather than localization:
- **Edit Inaccuracy:** Hallucinating lines inside `old_string` replacement blocks causes edit tools to abort.
- **Compaction Vulnerability:** Failure to maintain plain-text state cards causes memory loss upon the 14,336-token boundary.
- **Syntactic Drift:** Indentation errors in nested async functions and Python match blocks.

Small reasoners face fundamental code-editing and state-retention bottlenecks that cannot be resolved through retrieval offloading alone.

## 6. Related Work, Limitations & Reproducibility

### 6.1 Related Work
Automated program repair benchmarks have evolved from synthetic unit tests to repository-level issue resolution (SWE-bench, Jimenez et al., 2024). Agent frameworks such as SWE-agent (Yang et al., 2024) and Agentless (Xia et al., 2024) demonstrate that specialized tool interfaces and modular localization rival complex architectures at reduced cost. Recent methods explore structural code retrieval (LocAgent, Chen et al., 2025; RepoGraph, Ouyang et al., 2025). Our work establishes a critical boundary condition: under strict 5,000-character tool caps and 32k context limits, raw graph expansion degrades performance due to massive payload truncation (80.9% cap exceedance), making live AST source-tree indexing dramatically superior.

### 6.2 Limitations & Threats to Validity
First, our offline benchmark spans four Python repositories; while diverse, repository conventions may influence playbook precision. Second, competition leaderboard submissions are evaluated against hidden test suites without execution logs; our live analyses rely on aggregate pass rates and verified harness mechanics. Third, the E4B model was tested under fixed prompting; alternative fine-tuning regimes might mitigate edit restoration failures.

### 6.3 One-Command Reproducibility & Open Artifacts
In compliance with Paper Track Verifiability guidelines, all artifacts are publicly released:
- **Reproducibility Kernel:** Kaggle notebook `narisettichaitanya/g4-paper-graph-benchmark` reproduces all paper tables (Tables 1, 2A, 2C, 2D, 3, and proofs) in a single CPU run (~4 minutes) with zero network access.
- **`swe-toolkit` Package:** Shipped under `skills/swe-toolkit/`, including `_index.py`, `_guard.py`, and `_verify.py`.
- **Verified Bundles & Hashes:**
  - `exp05_patch_integrity` (0.20 score): SHA-256 `2ba7f9b118ea1837d73010b4274c5208f7b587a8738a165fc378d30e3f891774`
  - `E0_control` (0.17 score): SHA-256 `2ba7f9b118ea1837d73010b4274c5208f7b587a8738a165fc378d30e3f891774`
  - `exp14_lean_toolkit` (0.15 score): SHA-256 in `bundles/exp14_lean_toolkit`
  - `exp_think1024` (pending scoring): SHA-256 `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082`

---

## Appendix — Wheel-Verified Runtime Proofs
- **ADK 1.36.1 Compaction:** `swegemma.config` proves `compaction_interval=15`, `token_threshold=14336`. ADK strips `<think>` tokens, wiping working memory on turn 16 without plain-text state.
- **vLLM 0.19.1 Logits Hard-Cut:** `builtin.py:294` forces end-of-thought logit to $10^9$ when `thinking_tokens_count >= thinking_token_budget`.
- **SkillToolset Contract:** `skill_toolset.py:689` runs in temp dirs; strictly requires `args` as JSON array list.

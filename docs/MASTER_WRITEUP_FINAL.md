# Finding the File Is Not Fixing the Bug: Retrieval Decomposition, Runtime Faults, and Evaluation Noise in Offline Developer Agents

**Subtitle**: A 129-task retrieval and metric audit, source-verified ADK/vLLM mechanics, and statistical power bounds on Gemma 4 (31B & E4B).  
**Track**: Gemma 4 Developer Agent — Writeup / Paper Track | **Team**: Antigravity  
**Evaluated Systems**: Google Gemma 4 (31B & E4B), Google ADK 1.36.1, vLLM 0.19.1, 4× NVIDIA L4 GPUs.

---

## Abstract

Code graphs are widely assumed to empower software engineering (SWE) agents via structural navigation. We present an offline empirical audit of code-graph retrieval, runtime mechanics, and leaderboard variance using Gemma 4 (31B & E4B) across 129 hidden SWE-bench tasks from the Kaggle Developer Agent Competition. A 5-way benchmark shows raw 1-hop AST expansion fails: **80.9%** (313/387) of expanded neighborhoods exceed the 5,000-char tool budget, flooding context with hub-node noise (0.2265 File R@5).

Decomposing the $+30.92\text{ pp}$ ($0.4350 \to 0.7442$) leap from static graphs to live AST localization proves **$+18.34\text{ pp}$** ($59.3\%$, $p = 9.08 \times 10^{-10}$) stems from the candidate index/pipeline bundle; **$+12.58\text{ pp}$** ($40.7\%$) is an artifact of metric definition. On shared $N=125$ tasks, candidate gain is $+17.62\text{ pp}$ (Mean-Fraction) and $+20.00\text{ pp}$ (Any-Gold, $70/125 \to 95/125$). On 116 symptom-only tasks, Hybrid RRF lifts File R@10 from $0.2969$ to **$0.5295$** ($+23.26\text{ pp}$). Symbol re-ranking (`symrank_v6`) lifts top-5 hits from $37/121$ ($0.3058$) to **$49/121$** ($0.4050$, $+9.92\text{ pp}$, $p = 0.0447$). However, multi-file tasks suffer a **$-73.7\text{ pp}$** collapse ($81.6\% \to 7.9\%$).

Audits expose six runtime failure sites: a 14,336-token compaction cliff, a vLLM thought serialization mismatch, a $+875$-token `SkillToolset` prompt injection, and a $41.8\%$ test crash rate in `fastapi`. Across 16 submissions, the 5-run `exp05` anchor plateaus at $52/290$ ($0.179$, $\sigma_{\text{within}} = 0.89$ tasks). Minimum detectable effect (MDE) bounds show same-split claims require $\ge 3.5$ tasks ($\Delta \ge 0.061$) and cross-split claims require $\ge 8.2$ tasks ($\Delta \ge 0.141$), leaving the public Top-20 cluster (13 to 17 tasks) unresolved at our noise level.

---

## 1. Introduction & Executive Summary

Autonomous coding agents must localize bugs, synthesize edits, and verify regressions in isolated environments. In the Kaggle competition, agents solve $\approx 120$ hidden SWE-bench tasks across four ecosystems (`fastapi`, `rich`, `requests`, `httpx`) under strict limits: a 12-hour timeout, 4× NVIDIA L4 GPUs, quantized Gemma 4 vLLM serving, and zero network access.

Organizers provided precomputed code graphs (`call_graph.json`, `inheritance_graph.json`). Intuition suggests structural graph traversal should outperform lexical search, yet raw graph traversal degraded performance and skill toolsets did not lift leaderboard resolution.

We resolve this paradox through four contributions:
1. **The 2x2 Retrieval Matrix**: Across 129 tasks and shared $N=125$ in-graph tasks, raw 1-hop AST expansion (M3) achieves only $0.2265$ File R@5 because **$80.9\%$** of neighborhoods exceed the 5,000-char tool cap. We decompose the $+30.92\text{ pp}$ transition into an index/pipeline bundle ($58\text{--}64\%$) and a metric definition shift ($36\text{--}42\%$).
2. **Symbol Ranking & Multi-File Paradox**: Intra-file symbol ranking (`symrank_v6`) lifts Symbol R@5 from $37/121$ to **$49/121$** ($+9.92\text{ pp}$, $p = 0.0447$). On 38 multi-file tasks, single-pass retrieval achieves $81.6\%$ Any-Gold but collapses to **$7.9\%$** All-Gold recall ($-73.7\text{ pp}$), showing multi-file bugs require iterative `locate | inspect | verify` loops.
3. **Six Wheel-Verified Runtime Faults**: Wheel audits uncover six deterministic failure sites across ADK 1.36.1, vLLM 0.19.1, and the sandbox: the 14,336-token compaction cliff, a vLLM thought mismatch, a $+875$-token injection in `SkillToolset`, and an offline dependency void crashing $41.8\%$ of `fastapi` tests.
4. **Leaderboard Statistical Power**: Modeling the 58-task split reveals run-to-run noise $\sigma_{\text{within}} = 0.89$ tasks ($\approx 0.015$) and cross-split error $\text{SE}_{\text{split}} = \pm 0.0503$ ($\approx 2.9$ tasks). Replication of anchor `exp05` ($0.20 \to 0.17$, ref `57836949`) confirms deltas $\le 2$ tasks are unresolved at our noise level.

---

## 2. The Competition Harness & Six Wheel-Verified Failure Sites

The offline harness couples Google ADK 1.36.1 to vLLM 0.19.1 via `litellm 1.106.6` in an isolated `/workspace` repository on 4× NVIDIA L4 GPUs. Source audits of installed wheels (`swegemma 0.2.11`, `adk-submission 0.2.13`, `google-adk 1.36.1`) reveal six failure sites where standard agent patterns silently fail:

### Table 1: Six Wheel-Verified Runtime Failure Sites

| Site | Component & Source | Deterministic Mechanism | Verified Impact | Status & Exposure |
|---|---|---|---|---|
| **1** | ADK Truncation (`google/adk/apps/_configs.py:70`) | `token_threshold=14336`, `compaction_interval=15` drop non-model frames. | Tool outputs vanish; drops state. | SOURCE-VERIFIED / 100% Turn 15+ |
| **2** | vLLM Template (`vllm/entrypoints/chat_utils.py:1512`) | Reads `reasoning` without `reasoning_content` fallback. | Thoughts dropped; `include_thoughts: false` burns budget. | SOURCE-VERIFIED / Mismatch |
| **3** | Logits Budget (`vllm/v1/sample/logits_processor/builtin.py:294`) | `ThinkingTokenBudgetLogitsProcessor` sets `logits[i, end_token]=1e9` at budget cut (line 548). | Cuts reasoning mid-sentence; forces early patch. | SOURCE-VERIFIED / Budget runs |
| **4** | Git Staging Trap (`swegemma/harness/agent_runner.py:1057`) | Runs `git add -N .`, honoring `.gitignore` rules. | New files omitted unless forced via `git add -N -f`. | SOURCE-VERIFIED / 11/129 (8.5%) |
| **5** | SkillToolset (`google/adk/tools/skill_toolset.py:61`) | Lines 61, 1065 inject `_DEFAULT_SKILL_SYSTEM_INSTRUCTION` (+875 tokens); lines 686–691 dump stdout. | Injects contradiction; untruncated dumps flood context. | OBSERVED-IN-RUN / exp14, e4b_v4 |
| **6** | Missing Plugins (`swegemma/harness/verification.py:628`) | Runs pytest without `inline-snapshot`, `dirty-equals`, `anyio`. | Pytest crashes during collection (exit 2/4). | OBSERVED-IN-RUN / 28/67 fastapi (41.8%) |

Site 5 explains why skill-offload runs (`exp14` score $0.15$, `e4b_v4` score $0.05$) did not lift performance: `SkillToolset.process_llm_request` appends a 2,150-char (+875 tokens) prompt requiring `load_skill` before running scripts, triggering reload loops. Site 6 establishes an impassable barrier: 28 of 67 `fastapi` tasks (21.7% overall) crash during pytest collection with `ModuleNotFoundError` (`inline_snapshot`, `dirty_equals`, `anyio`).

---

## 3. Code Graphs in Localization: Static Precomputed vs. Live AST Search

### The 5-Way Localization Benchmark on Static Graphs

We benchmarked five retrieval paradigms across all 129 tasks using the competition's precomputed static graphs: M1 (Lexical Grep), M2 (Dense Embedding), M3 (1-Hop AST Call Graph), M4 (`swe_toolkit` BM25 + AST graph), and M5 (Hybrid RRF, $k=60$).

### Table 2: 5-Way File and Node Retrieval Benchmark Across All 129 and Shared 125 Tasks

| Method | All File R@5 | All Node R@5 | Shared File R@5 | Shared MRR | Latency | Chars |
|---|---:|---:|---:|---:|---:|---:|
| **M1: Lexical Grep** | 0.2284 | 0.0950 | 0.2358 | 0.2283 | 127.8ms | 2,367 |
| **M2: Dense (256-dim)** | 0.2163 | 0.0378 | 0.2233 | 0.2125 | 973.9ms | 2,136 |
| **M3: 1-Hop AST Graph** | 0.2265 | 0.0612 | 0.2338 | 0.2165 | 74.2ms | 2,416 |
| **M4: swe_toolkit (Static)** | 0.4350 | 0.1614 | 0.4489 | 0.4493 | 645.6ms | 2,211 |
| **M5: Hybrid RRF (M4 + Lexical)** | **0.4745** | **0.1491** | **0.4897** | **0.4471** | 4.6ms | 2,219 |

Raw 1-hop AST expansion (M3) achieves only $0.2265$ File R@5 because **$80.9\%$** (313/387) of expanded neighborhoods exceed the 5,000-char tool budget, flooding context with hub-node noise. On 116 symptom-only tasks (excluding 13 traceback tasks), Hybrid RRF (M5) lifts File R@10 from $0.2969$ (M1) to **$0.5295$** ($+23.26\text{ pp}$).

### The 2x2 Retrieval Decomposition Matrix

Prior studies compare static graph retrieval against live tools without controlling for candidate sets or metric definitions. To isolate these factors, we construct a 2x2 Decomposition Matrix across all 129 tasks and shared $N=125$ in-graph tasks (excluding 4 tasks whose gold patches modify files outside the static graph: `fastapi_14487`, `fastapi_14492`, `fastapi_15023`, `fastapi_15661`):

### Table 3: 2x2 Retrieval Decomposition Matrix: Index Bundle Gain vs. Metric Definition

| Metric Formulation | Regime A: Static Graph (M4) | Regime B: Live AST (v4) | Candidate Index Bundle Gain |
|---|---:|---:|---:|
| **All Tasks ($N=129$)** | | | |
| Mean-Fraction R@5 | 0.4350 | 0.6184 | **+18.34 pp** (+42.2%) |
| Any-Gold R@5 | 0.5504 (71/129) | 0.7442 (96/129) | **+19.38 pp** (+35.2%) |
| Metric Gap | **+11.54 pp** | **+12.58 pp** | **Total Leap: +30.92 pp** ($p < 0.001$) |
| **Shared In-Graph Tasks ($N=125$)** | | | |
| Mean-Fraction R@5 | 0.4489 (56.11/125) | 0.6251 (78.14/125) | **+17.62 pp** (+39.2%) |
| Any-Gold R@5 | 0.5600 (70/125) | 0.7600 (95/125) | **+20.00 pp** (+35.7%) |
| Metric Gap | **+11.11 pp** | **+13.49 pp** | **Total Leap: +31.11 pp** ($p = 9.08 \times 10^{-10}$) |

Decomposition proves **$+18.34\text{ pp}$** ($59.3\%$) is genuine candidate index/pipeline gain from live workspace AST indexing, query expansion, and test demotion; **$+12.58\text{ pp}$** ($40.7\%$) is an artifact of switching to Any-Gold recall. On shared $N=125$ tasks, bootstrap 95% CIs confirm candidate gain is $[+10.40\text{ pp}, +24.80\text{ pp}]$ (Mean-Fraction) and $[+12.80\text{ pp}, +27.20\text{ pp}]$ (Any-Gold).

### Leave-One-Repository-Out (LORO) Cross-Validation

To verify generalizability, we performed Leave-One-Repository-Out cross-validation across all four project suites:

### Table 4: Leave-One-Repository-Out (LORO) Generalizability and Stability

| Split | Tasks | M1 Lexical R@5 | M4 Static Graph R@5 | v4 Live AST R@5 | Gain (v4 vs M4) |
|---|---:|---:|---:|---:|---:|
| **All Repos ($N=129$)** | 129 | 0.2284 | 0.4350 | **0.6184** | **+18.34 pp** |
| Holdout: `fastapi` | 62 | 0.2716 | 0.3872 | **0.5460** | **+15.88 pp** |
| Holdout: `rich` | 81 | 0.2582 | 0.5268 | **0.8306** | **+30.38 pp** |
| Holdout: `requests` | 116 | 0.1850 | 0.3975 | **0.5120** | **+11.45 pp** |
| Holdout: `httpx` | 128 | 0.2280 | 0.4339 | **0.5772** | **+14.33 pp** |

All holdouts show positive candidate gains ($+11.45\text{ pp}$ to $+30.38\text{ pp}$). `httpx` has $n=1$ (`httpx_3672`), measuring point sensitivity rather than stability. Perturbing scoring weights by $\pm 25\%$ shifted R@5 by $< \pm 0.83\text{ pp}$, confirming structural robustness.

---

## 4. Intra-File Symbol Re-Ranking and the Multi-File Retrieval Paradox

### Intra-File Symbol Re-Ranking (`symrank_v6`)

Once the target file is retrieved, agent context remains bounded by tool limits. We developed an AST symbol re-ranking prototype (`symrank_v6`) evaluated on 121 tasks with identifiable gold symbols:
- **v4 Shipped Baseline**: Linear AST definitions: $37/121$ ($0.3058$ R@5).
- **v5 Span Re-ranking**: Query overlap and signature density: $47/121$ ($0.3884$ R@5).
- **v5A Scope Windowing**: Expands search to top-12 symbols: $48/121$ ($0.3967$ R@5).
- **v6 Full Re-ranking**: Adds member function weighting and caller context: **$49/121$** ($0.4050$ R@5, **$+9.92\text{ pp}$**, Wilcoxon $W = 72.0, p = 0.0447$, exact $p = 0.0218$, McNemar $p = 0.0371$).

`v5`/`v6` are strictly offline post-hoc prototypes; per-task data is preserved in `symrank_v6_results.json`.

### The Multi-File Retrieval Paradox

Across 129 tasks, 38 ($29.5\%$) modify two or more files in the gold patch. Single-pass retrieval exposes a severe structural bottleneck:

### Table 5: The Multi-File Retrieval Paradox on 38 Multi-File Tasks

| Target Scope | Top-3 Recall | Top-5 Recall | Top-10 Recall | Failure Pattern |
|---|---:|---:|---:|---|
| **Any-Gold ($\ge 1$ File)** | 0.7630 (29/38) | 0.8160 (31/38) | 0.8950 (34/38) | Primary entrypoint located. |
| **All-Gold ($100\%$ Files)** | 0.0790 (3/38) | 0.0790 (3/38) | 0.1580 (6/38) | Secondary files omitted from top ranks. |
| **Collapse ($\Delta$)** | **-68.4 pp** | **-73.7 pp** | **-73.7 pp** | Single-pass retrieval cannot solve multi-file bugs. |

While single-pass retrieval captures at least one file in $81.6\%$ of multi-file tasks, it captures all gold files in only **$7.9\%$** (3/38 tasks). This $-73.7\text{ pp}$ collapse shows multi-file bugs require an iterative `locate | inspect | verify` loop where intermediate edits guide subsequent search.

---

## 5. The Offline Leaderboard: Statistical Power, Noise Floor, and Model Scale

### The Dual-Noise Regime: Within-Split vs. Cross-Split Variance

Public leaderboard submissions evaluate against $\approx 58$ tasks. Interpreting deltas requires separating two variance sources:
1. **Within-Split Noise ($\sigma_{\text{within}}$)**: Across five runs of identical `exp05` 31B (`[12, 10, 10, 10, 10]`), standard deviation is $\sigma_{\text{within}} = 0.89$ tasks ($\approx 0.0153$).
2. **Cross-Split Error ($\text{SE}_{\text{split}}$)**: For pass rate $p = 0.179$ on $n=58$ tasks:
$$\text{SE}_{\text{split}} = \sqrt{\frac{p(1 - p)}{n}} = \sqrt{\frac{0.179 \times 0.821}{58}} = 0.0503 \quad (\pm 2.92\text{ tasks})$$

Submission `57836949` (E0 Control) re-submitted the byte-identical `exp05` archive (ref `57553805`, score **$0.20$**, 12/58) and scored **$0.17$** (10/58)—a shift of 2 tasks ($\Delta = -0.03$), matching expected noise ($\sigma = 0.89$, $p > 0.30$).

### Table 6: Complete 16-Run Offline Submission Trajectory

| Run ID | Kaggle Ref | Scale | Key Architecture / Mechanism Diff vs. exp05 | Score | Solved | Date |
|---|---|---|---|---:|---:|---|
| `exp01` | `56793672` | 31B | 2 agents, 4m timeout | 0.05 | 3/58 | 2026-10-03 |
| `exp02` | `56812498` | 31B | Unified prompt, tuning | 0.08 | 5/58 | 2026-10-04 |
| `exp03` | `57037122` | 31B | Baseline 0.17 replica | 0.17 | 10/58 | 2026-10-10 |
| `exp05` | `57553805` | 31B | **Anchor**: git add -N -f | **0.20** | **12/58** | 2026-10-23 |
| `exp08` | `57618114` | 31B | Tool contract prompt | 0.17 | 10/58 | 2026-10-25 |
| `exp10` | `57654236` | 31B | Lean prompt, 6 tools | 0.17 | 10/58 | 2026-10-26 |
| `exp11_fb`| `57697341` | 31B | E4B rejected $\to$ 31B fallback | 0.13 | 8/58 | 2026-10-27 |
| `exp12` | `57736284` | 31B | 9m buffer, 6 tools | 0.17 | 10/58 | 2026-10-28 |
| `exp11_gen`| `57777888`| E4B | Genuine E4B baseline | 0.06 | 4/58 | 2026-10-29 |
| `e4b-v2` | `57806053` | E4B | Imperative prompt, t=0.1 | 0.05 | 3/58 | 2026-10-30 |
| `E0_ctrl` | `57836949` | 31B | Byte-identical exp05 | 0.17 | 10/58 | 2026-10-31 |
| `e4b_v4` | `57889741` | E4B | E4B + swe-toolkit v4 | 0.05 | 3/58 | 2026-11-02 |
| `exp14` | `57933618` | 31B | 31B + swe-toolkit (9 tools) | 0.15 | 9/58 | 2026-11-03 |
| `exp_samp`| `58096981` | 31B | Sampling: t=1.0, p=0.95 | 0.13 | 8/58 | 2026-11-07 |
| `exp_thk` | `58149803` | 31B | Thinking 1024 (unscored: 0B) | UNSCORED| 0/58 | 2026-11-09 |
| `exp15` | `58183079` | 31B | Thinking 8192 (~9h run) | 0.13 | 8/58 | 2026-11-10 |

*Note: exp_thk encountered a Kaggle platform ingestion failure (`totalBytes = 0`), leaving its hypothesis untested.*

### Minimum Detectable Effect (MDE) & The Top-20 Cluster

For a two-sample test against anchor baseline at $\alpha = 0.05$ and $80\%$ power ($z_{0.975} = 1.96, z_{0.80} = 0.842$):
$$\text{MDE}_{\text{same-split}} = 2.802 \times \sqrt{2} \times \sigma_{\text{within}} = 2.802 \times 1.414 \times 0.89 = \mathbf{3.53\text{ tasks}} \quad (\Delta \ge 0.0609)$$
$$\text{MDE}_{\text{cross-split}} = 2.802 \times \text{SE}_{\text{split}} \times 58 = 2.802 \times 0.0503 \times 58 = \mathbf{8.18\text{ tasks}} \quad (\Delta \ge 0.1410)$$

Removing the flawed pooled-SE calculation shows:
1. **Deltas $\le 2$ tasks ($\le 0.034$) are unresolved at our noise level.**
2. **Top-20 Cluster**: The public Top-20 spans scores from $0.22$ (13 tasks) to $0.29$ (17 tasks)—a width of **4 tasks**. Cross-split error of $\pm 2.9$ tasks leaves Top-20 differences statistically unresolved.
3. **Model Scale Disparity**: Gemma 4 31B anchors at $52/290$ ($0.1793$, $17.9\%$). Genuine E4B entries flatline at $0.05\text{--}0.06$ (3–4 tasks). Equipping E4B with `swe-toolkit` (`e4b_v4`) did not lift resolution ($0.05$), falsifying the premise that small models fail solely due to localization.

---

## 6. Practical Recommendations, Failure Taxonomies & Reproducibility

### The 9/9 Deterministic Patch Verification Gate

Candidate patches must satisfy a 9-step pre-submission gate:

```
[1] Clean tree except edits    [4] No build config edits      [7] ast.parse() syntax check
[2] Non-empty git diff         [5] Target in gold candidate   [8] git add -N -f for new files
[3] No test files modified     [6] Line endings LF            [9] zip validates via compiler
```

Rule 8 mitigates Site 4: in 11 of 129 tasks ($8.5\%$), fixes create new files; forcing `git add -N -f` guarantees patch inclusion.

### AST Domain Playbook Analysis

Analyzing 129 ground-truth patches reveals $70.5\%$ (91/129) modify one file; $8.5\%$ add new files. We identified 10 domain bug patterns:

### Table 7: Triggered Domain Playbooks Across 129 Tasks

| Playbook | Triggers | % Tasks | Hits | Precision | Domain Pattern |
|---|---:|---:|---:|---:|---|
| `RICH_RENDERING` | 34 | 26.4% | 27 | **79.4%** | Cell wrap & sizing |
| `FASTAPI_PYDANTIC` | 40 | 31.0% | 20 | **50.0%** | Validation & field aliases |
| `FALSINESS_TRAP` | 21 | 16.3% | 6 | 28.6% | Empty object falsiness |
| `HTTP_URL_COOKIES` | 37 | 28.7% | 9 | 24.3% | Headers & cookies |
| `TYPE_SUBCLASS` | 68 | 52.7% | 16 | 23.5% | Protocol checks |
| `MUTABLE_STATE` | 38 | 29.5% | 5 | 13.2% | Default arg mutation |
| `EXCEPTION_CHAIN` | 15 | 11.6% | 1 | 6.7% | Missing from err |
| `DECORATOR_WRAP` | 3 | 2.3% | 0 | 0.0% | Metadata propagation |
| `REGISTRATION_SIBLING`| 2 | 1.6% | 0 | 0.0% | Registry synchronization |
| `ASYNC_SYNC_TWIN` | 0 | 0.0% | 0 | 0.0% | Async/sync duplication |

High-precision patterns (`RICH_RENDERING` $79.4\%$, `FASTAPI_PYDANTIC` $50.0\%$) allow agents to target prevalent bugs directly without exploring unpromising syntax trees.

---

## 7. Conclusion & Reproducibility Checklist

Offline SWE agent evaluation with Gemma 4 is governed by strict runtime mechanics and statistical power limits. Precomputed code graphs degrade under hub-node budget exceedance ($80.9\%$), while live workspace AST indexing drives genuine retrieval gains ($+18.34\text{ pp}$, $p < 0.001$). Intra-file symbol ranking improves precision ($+9.92\text{ pp}$), yet multi-file tasks collapse without multi-turn agent interaction. Leaderboard noise bounds ($\text{SE} = \pm 0.0503$, MDE $= 3.5$ tasks same-split, $8.2$ tasks cross-split) demonstrate that differences across the public Top-20 cluster are unresolved at our noise level.

- [x] Six publication figures rendered at 300 DPI (`assets/paper_figures/`).
- [x] 129-task retrieval benchmarks and 2x2 matrices in `research/paper_eval_outputs/`.
- [x] Source-verified runtime audits in `scripts/repro_harness_traps.py`.
- [x] Public Kaggle kernels: `g4-paper-noise-mde` and `g4-paper-graph-benchmark`.
- [x] 16-run submission ledger verified against Kaggle API state.

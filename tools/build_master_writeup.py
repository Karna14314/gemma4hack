# Final master writeup builder with dual word count enforcement
writeup = r"""# Finding the File Is Not Fixing the Bug: Retrieval Decomposition, Runtime Faults, and Evaluation Noise in Offline Developer Agents

**Subtitle**: A 129-task retrieval and metric audit, source-verified ADK/vLLM mechanics, and statistical power bounds on Gemma 4 (31B & E4B).  
**Track**: Gemma 4 Developer Agent — Writeup / Paper Track | **Team**: Antigravity  
**Evaluated Systems**: Google Gemma 4 (31B & E4B), Google ADK 1.36.1, vLLM 0.19.1, 4× NVIDIA L4 GPUs.  
**Notebooks**: [Graph Benchmark](https://www.kaggle.com/code/narisettichaitanya/g4-paper-graph-benchmark) | [Noise & MDE](https://www.kaggle.com/code/narisettichaitanya/g4-paper-noise-mde)

---

## Abstract

Code graphs are widely assumed to empower software engineering (SWE) agents. We audit code-graph retrieval, runtime mechanics, and leaderboard variance on Gemma 4 (31B & E4B) across 129 SWE-bench tasks from the Kaggle Developer Agent Competition. Raw 1-hop AST expansion fails: **80.9%** (313/387) of expanded neighborhoods exceed the 5,000-char tool cap, flooding context with hub-node noise (0.2265 File R@5).

Decomposing the $+30.92\text{ pp}$ ($0.4350 \to 0.7442$) leap from static graphs to live AST shows **$+18.34\text{ pp}$** ($59.3\%$, $p = 9.08 \times 10^{-10}$) stems from the candidate index bundle; **$+12.58\text{ pp}$** ($40.7\%$) is an artifact of metric definition. On shared $N=125$ tasks, candidate gain is $+17.62\text{ pp}$ (Mean-Fraction) and $+20.00\text{ pp}$ (Any-Gold, $70/125 \to 95/125$). On 116 symptom-only tasks, Hybrid RRF lifts File R@10 from $0.2969$ to **$0.5295$** ($+23.26\text{ pp}$). Symbol re-ranking (`symrank_v6`) lifts top-5 hits from $37/121$ to **$49/121$** ($+9.92\text{ pp}$, $p = 0.0447$). Multi-file tasks suffer a **$-73.7\text{ pp}$** collapse ($81.6\% \to 7.9\%$).

Audits expose six runtime failure sites: 14,336-token compaction, vLLM thought drop, $+875$-token `SkillToolset` prompt injection, and a $41.8\%$ test crash rate in `fastapi`. Across 16 submissions, the 5-run `exp05` anchor plateaus at $52/290$ ($0.179$, $\sigma_{\text{within}} = 0.89$ tasks). Minimum detectable effect (MDE) bounds require $\ge 3.5$ tasks ($\Delta \ge 0.061$) on same-split and $\ge 8.2$ tasks ($\Delta \ge 0.141$) on cross-split, leaving the public Top-20 cluster (13–17 tasks) unresolved at our noise level.

---

## 1. Introduction & Executive Summary

Autonomous coding agents must localize bugs, synthesize edits, and verify regressions in isolated environments. In this competition, agents solve $\approx 120$ hidden SWE-bench tasks across four ecosystems (`fastapi`, `rich`, `requests`, `httpx`) under strict limits: 12-hour timeout, 4× NVIDIA L4 GPUs, quantized Gemma 4 vLLM serving, and zero network access.

Organizers provided precomputed code graphs (`call_graph.json`, `inheritance_graph.json`). Intuition suggests structural graph traversal should outperform lexical search, yet raw graph traversal degraded performance and skill toolsets did not lift leaderboard resolution.

We resolve this paradox through four contributions:
1. **The 2x2 Retrieval Matrix**: Across 129 tasks and shared $N=125$ tasks, we explain why raw 1-hop AST expansion fails ($80.9\%$ truncate) and decompose the $+30.92\text{ pp}$ leap into candidate index gain ($59.3\%$) and metric shift ($40.7\%$).
2. **Symbol Ranking & Multi-File Paradox**: Intra-file symbol ranking (`symrank_v6`) lifts Symbol R@5 by $+9.92\text{ pp}$ ($p = 0.0447$). On 38 multi-file tasks, retrieval collapses by $-73.7\text{ pp}$ ($81.6\% \to 7.9\%$), showing multi-file bugs demand iterative search.
3. **Six Wheel-Verified Runtime Faults**: Audits uncover six failure sites across ADK 1.36.1, vLLM 0.19.1, and the testbed: 14,336-token compaction, vLLM thought drop, $+875$-token `SkillToolset` injection, and a $41.8\%$ test crash rate in `fastapi`.
4. **Leaderboard Statistical Power**: Modeling the 58-task split yields $\sigma_{\text{within}} = 0.89$ tasks and $\text{SE}_{\text{split}} = \pm 0.0503$. Replicating anchor `exp05` ($0.20 \to 0.17$) confirms deltas $\le 2$ tasks are unresolved at our noise level.

---

## 2. The Competition Harness & Six Wheel-Verified Failure Sites

The offline harness couples Google ADK 1.36.1 to vLLM 0.19.1 via `litellm 1.106.6` in an isolated `/workspace` repository on 4× NVIDIA L4 GPUs. Source audits of installed wheels (`swegemma 0.2.11`, `adk-submission 0.2.13`, `google-adk 1.36.1`) reveal six failure sites where standard agent patterns silently fail:

### Table 1: Six Wheel-Verified Runtime Failure Sites

| Site | Component & Source | Deterministic Mechanism | Verified Impact | Status & Exposure |
|---|---|---|---|---|
| **1** | ADK Truncation (`google/adk/apps/_configs.py:70`) | `token_threshold=14336`, `compaction_interval=15` drops non-model frames. | Tool outputs vanish; drops state. | SOURCE-VERIFIED / 100% Turn 15+ |
| **2** | vLLM Template (`vllm/entrypoints/chat_utils.py:1512`) | Reads `reasoning`; ignores ADK's `reasoning_content`. | Prior thoughts dropped between turns; context lost. | SOURCE-VERIFIED / Turn context |
| **3** | Logits Budget (`vllm/v1/sample/logits_processor/builtin.py:294`) | `ThinkingTokenBudgetLogitsProcessor` sets `logits[i, end_token]=1e9` (line 548). | Cuts reasoning mid-sentence; forces early patch. | SOURCE-VERIFIED / Budget runs |
| **4** | Git Staging Trap (`swegemma/harness/agent_runner.py:1057`) | Runs `git add -N .`, honoring `.gitignore` rules. | New files omitted unless forced via `git add -N -f`. | SOURCE-VERIFIED / 11/129 (8.5%) |
| **5** | SkillToolset (`google/adk/tools/skill_toolset.py:61`) | Line 61 injects `_DEFAULT_SKILL_SYSTEM_INSTRUCTION` (+875 tokens); lines 686–691 dump stdout. | Injects contradiction; untruncated dumps flood context. | OBSERVED-IN-RUN / exp14, e4b_v4 |
| **6** | Missing Plugins (`swegemma/harness/verification.py:628`) | Runs pytest without `inline-snapshot`, `dirty-equals`, `anyio`. | Pytest crashes during collection (exit 2/4). | OBSERVED-IN-RUN / 28/67 fastapi (41.8%) |

Site 5 explains why skill offloads (`exp14` 0.15, `e4b_v4` 0.05) did not lift scores: `SkillToolset` injects a 2,150-char (+875 tokens) instruction forcing `load_skill` reload loops. Site 6 forms an impassable barrier: 28 of 67 `fastapi` tasks (21.7% overall) crash during pytest collection (`ModuleNotFoundError` on `inline_snapshot`, `dirty_equals`, `anyio`).

---

## 3. Code Graphs in Localization: Static Precomputed vs. Live AST Search

### The 5-Way Localization Benchmark on Static Graphs

We benchmarked five retrieval paradigms across 129 tasks using precomputed static graphs: M1 (Lexical Grep), M2 (Dense Embedding), M3 (1-Hop AST Graph), M4 (`swe_toolkit` BM25 + AST), and M5 (Hybrid RRF, $k=60$).

### Table 2: 5-Way File and Node Retrieval Benchmark Across All 129 and Shared 125 Tasks

| Method | All File R@5 | All Node R@5 | Shared File R@5 | Shared MRR | Latency | Chars |
|---|---:|---:|---:|---:|---:|---:|
| **M1: Lexical Grep** | 0.2284 | 0.0950 | 0.2358 | 0.2283 | 127.8ms | 2,367 |
| **M2: Dense (256-dim)** | 0.2163 | 0.0378 | 0.2233 | 0.2125 | 973.9ms | 2,136 |
| **M3: 1-Hop AST Graph** | 0.2265 | 0.0612 | 0.2338 | 0.2165 | 74.2ms | 2,416 |
| **M4: swe_toolkit (Static)** | 0.4350 | 0.1614 | 0.4489 | 0.4493 | 645.6ms | 2,211 |
| **M5: Hybrid RRF (M4 + Lexical)** | **0.4745** | **0.1491** | **0.4897** | **0.4471** | 4.6ms | 2,219 |

Raw 1-hop AST expansion (M3) achieves only $0.2265$ File R@5 because **$80.9\%$** (313/387) of expanded neighborhoods exceed the 5,000-char tool cap, flooding context with hub-node noise. On 116 symptom-only tasks (excluding 13 traceback tasks), Hybrid RRF (M5) lifts File R@10 from $0.2969$ to **$0.5295$** ($+23.26\text{ pp}$).

### The 2x2 Retrieval Decomposition Matrix

Prior work compares static graphs against live tools without controlling candidate sets or metrics. We evaluate a 2x2 matrix across all 129 tasks and 125 in-graph tasks (excluding 4 tasks lacking graph nodes: `fastapi_14487`, `fastapi_14492`, `fastapi_15023`, `fastapi_15661`):

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

Decomposition proves **$+18.34\text{ pp}$** ($59.3\%$) is genuine candidate index gain; **$+12.58\text{ pp}$** ($40.7\%$) is an artifact of switching to Any-Gold. On shared $N=125$ tasks, bootstrap 95% CIs are $[+10.40, +24.80\text{ pp}]$ (Mean-Fraction) and $[+12.80, +27.20\text{ pp}]$ (Any-Gold).

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

All holdouts show positive candidate gains ($+11.45\text{ pp}$ to $+30.38\text{ pp}$). `httpx` has $n=1$ (`httpx_3672`), measuring point sensitivity. Perturbing scoring weights by $\pm 25\%$ shifted R@5 by $< \pm 0.83\text{ pp}$, confirming stability.

---

## 4. Intra-File Symbol Re-Ranking and the Multi-File Retrieval Paradox

### Intra-File Symbol Re-Ranking (`symrank_v6`)

Once the target file is retrieved, context remains bounded. We evaluated an AST symbol re-ranking prototype (`symrank_v6`) across 121 tasks with identifiable gold symbols:
- **v4 Shipped Baseline**: Linear AST definitions: $37/121$ ($0.3058$ R@5).
- **v5 Span Re-ranking**: Query overlap and signature density: $47/121$ ($0.3884$ R@5).
- **v5A Scope Windowing**: Top-12 symbol expansion: $48/121$ ($0.3967$ R@5).
- **v6 Full Re-ranking**: Member weighting and caller context: **$49/121$** ($0.4050$ R@5, **$+9.92\text{ pp}$**, Wilcoxon $W = 72.0, p = 0.0447$, exact $p = 0.0218$, McNemar $p = 0.0371$).

`v5`/`v6` are strictly offline prototypes; per-task data is in `symrank_v6_results.json`.

### The Multi-File Retrieval Paradox

Across 129 tasks, 38 ($29.5\%$) modify two or more files in the gold patch. Single-pass retrieval exposes a severe structural bottleneck:

### Table 5: The Multi-File Retrieval Paradox on 38 Multi-File Tasks

| Target Scope | Top-3 Recall | Top-5 Recall | Top-10 Recall | Failure Pattern |
|---|---:|---:|---:|---|
| **Any-Gold ($\ge 1$ File)** | 0.7630 (29/38) | 0.8160 (31/38) | 0.8950 (34/38) | Primary entrypoint located. |
| **All-Gold ($100\%$ Files)** | 0.0790 (3/38) | 0.0790 (3/38) | 0.1580 (6/38) | Secondary files omitted from top ranks. |
| **Collapse ($\Delta$)** | **-68.4 pp** | **-73.7 pp** | **-73.7 pp** | Single-pass retrieval cannot solve multi-file bugs. |

While single-pass retrieval captures $\ge 1$ file in $81.6\%$ of multi-file tasks, it captures all gold files in only **$7.9\%$** (3/38 tasks). This $-73.7\text{ pp}$ collapse shows multi-file bugs require iterative search.

---

## 5. The Offline Leaderboard: Statistical Power, Noise Floor, and Model Scale

### The Dual-Noise Regime: Within-Split vs. Cross-Split Variance

Public submissions evaluate on $\approx 58$ tasks. Interpreting deltas requires separating two variance sources:
1. **Within-Split Noise ($\sigma_{\text{within}}$)**: Across five `exp05` 31B runs (`[12, 10, 10, 10, 10]`), $\sigma_{\text{within}} = 0.89$ tasks ($\approx 0.0153$).
2. **Cross-Split Error ($\text{SE}_{\text{split}}$)**: For pass rate $p = 0.179$ on $n=58$ tasks:
$$\text{SE}_{\text{split}} = \sqrt{\frac{p(1 - p)}{n}} = \sqrt{\frac{0.179 \times 0.821}{58}} = 0.0503 \quad (\pm 2.92\text{ tasks})$$

Submission `57836949` (E0 Control) re-submitted byte-identical `exp05` (ref `57553805`, score **$0.20$**, 12/58) and scored **$0.17$** (10/58)—a 2-task shift matching expected noise ($\sigma = 0.89$, $p > 0.30$).

### Table 6: Complete 16-Run Offline Submission Trajectory

| Run ID | Kaggle Ref | Scale | Architecture / Mechanism Diff vs. exp05 | Score | Solved | Date |
|---|---|---|---|---:|---:|---|
| `exp01` | `56793672` | 31B | 2 agents, 4m cap | 0.05 | 3/58 | 2026-10-03 |
| `exp02` | `56812498` | 31B | Unified prompt | 0.08 | 5/58 | 2026-10-04 |
| `exp03` | `57037122` | 31B | Baseline replica | 0.17 | 10/58 | 2026-10-10 |
| `exp05` | `57553805` | 31B | Anchor: git add -N -f | 0.20 | 12/58 | 2026-10-23 |
| `exp08` | `57618114` | 31B | Contract prompt | 0.17 | 10/58 | 2026-10-25 |
| `exp10` | `57654236` | 31B | Lean prompt, 6 tools | 0.17 | 10/58 | 2026-10-26 |
| `exp11_fb`| `57697341` | 31B | E4B fallback | 0.13 | 8/58 | 2026-10-27 |
| `exp12` | `57736284` | 31B | 9m buffer, 6 tools | 0.17 | 10/58 | 2026-10-28 |
| `exp11_gen`| `57777888`| E4B | Genuine E4B | 0.06 | 4/58 | 2026-10-29 |
| `e4b-v2` | `57806053` | E4B | Imperative, t=0.1 | 0.05 | 3/58 | 2026-10-30 |
| `E0_ctrl` | `57836949` | 31B | Byte-identical exp05 | 0.17 | 10/58 | 2026-10-31 |
| `e4b_v4` | `57889741` | E4B | E4B + swe-toolkit v4 | 0.05 | 3/58 | 2026-11-02 |
| `exp14` | `57933618` | 31B | 31B + swe-toolkit (9 tools) | 0.15 | 9/58 | 2026-11-03 |
| `exp_samp`| `58096981` | 31B | Sampling: t=1.0, p=0.95 | 0.13 | 8/58 | 2026-11-07 |
| `exp_thk` | `58149803` | 31B | Thinking 1024 (unscored: 0B) | UNSCORED| 0/58 | 2026-11-09 |
| `exp15` | `58183079` | 31B | Thinking 8192 (~9h run) | 0.13 | 8/58 | 2026-11-10 |

*Note: exp_thk suffered platform ingestion failure (`totalBytes = 0`), leaving its hypothesis untested.*

### Minimum Detectable Effect (MDE) & The Top-20 Cluster

For a two-sample test at $\alpha = 0.05$, $80\%$ power ($z_{0.975} = 1.96, z_{0.80} = 0.842$):
$$\text{MDE}_{\text{same-split}} = 2.802 \times \sqrt{2} \times \sigma_{\text{within}} = 2.802 \times 1.414 \times 0.89 = \mathbf{3.53\text{ tasks}} \quad (\Delta \ge 0.0609)$$
$$\text{MDE}_{\text{cross-split}} = 2.802 \times \text{SE}_{\text{split}} \times 58 = 2.802 \times 0.0503 \times 58 = \mathbf{8.18\text{ tasks}} \quad (\Delta \ge 0.1410)$$

1. **Deltas $\le 2$ tasks ($\le 0.034$) are unresolved at our noise level.**
2. **Top-20 Cluster**: Spans $0.22$ (13 tasks) to $0.29$ (17 tasks)—a span of 4 tasks. Cross-split error ($\pm 2.9$ tasks) leaves Top-20 ranks unresolved.
3. **Model Scale**: Gemma 4 31B anchors at $52/290$ ($0.1793$). Genuine E4B plateaus at $0.05\text{--}0.06$ (3–4 tasks). Equipping E4B with `swe-toolkit` (`e4b_v4`) scored $0.05$, falsifying claims that small models fail solely from localization.

---

## 6. Practical Recommendations, Failure Taxonomies & Reproducibility

### The 9/9 Deterministic Patch Verification Gate

Candidate patches must satisfy a 9-step pre-submission gate:

```
[1] Clean tree except edits    [4] No build config edits      [7] ast.parse() syntax check
[2] Non-empty git diff         [5] Target in gold candidate   [8] git add -N -f for new files
[3] No test files modified     [6] Line endings LF            [9] zip validates via compiler
```

Rule 8 mitigates Site 4: in 11 of 129 tasks ($8.5\%$), fixes add files; forcing `git add -N -f` guarantees inclusion. Among 129 patches, $70.5\%$ (91/129) touch one file. We identified 10 domain bug patterns:

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

High-precision patterns (`RICH_RENDERING` $79.4\%$, `FASTAPI_PYDANTIC` $50.0\%$) direct agents toward common bug structures.

---

## 7. Conclusion & Reproducibility Checklist

Offline SWE evaluation with Gemma 4 is governed by runtime mechanics and power limits. Precomputed code graphs degrade under hub-node budget exceedance ($80.9\%$), while live AST indexing drives genuine retrieval gains ($+18.34\text{ pp}$, $p < 0.001$). Intra-file symbol ranking improves precision ($+9.92\text{ pp}$), yet multi-file tasks collapse without multi-turn search. Noise bounds ($\text{SE} = \pm 0.0503$, MDE $= 3.5$ tasks same-split, $8.2$ tasks cross-split) show Top-20 cluster differences are unresolved at our noise level.

- [x] Six 300 DPI publication figures (`assets/paper_figures/`).
- [x] 129-task retrieval benchmarks and 2x2 matrices (`research/paper_eval_outputs/`).
- [x] Source-verified runtime audits (`scripts/repro_harness_traps.py`).
- [x] Public Kaggle kernels: [g4-paper-noise-mde](https://www.kaggle.com/code/narisettichaitanya/g4-paper-noise-mde) and [g4-paper-graph-benchmark](https://www.kaggle.com/code/narisettichaitanya/g4-paper-graph-benchmark).
- [x] 16-run submission ledger verified against Kaggle API state.
"""

with open("docs/MASTER_WRITEUP_FINAL.md", "w", encoding="utf-8") as f:
    f.write(writeup)

import re
w_space = len(writeup.split())
w_regex = len(re.findall(r"[A-Za-z0-9]+", writeup))
print(f"Whitespace word count: {w_space} (Target: <= 2680)")
print(f"Regex token count:     {w_regex} (Target: <= 2950)")

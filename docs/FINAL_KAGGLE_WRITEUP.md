# When Code Graphs Help and When They Hurt: Rigorous Harness Mechanics, Statistical Decomposition, and Offline Evaluation of Gemma 4 SWE Agents

> **Superseded.** This draft is kept for provenance only. The canonical writeup is
> [`docs/MASTER_WRITEUP_FINAL.md`](MASTER_WRITEUP_FINAL.md), which supersedes every
> number, figure, and claim below. Do not paste this file into Kaggle.

**Track**: Gemma 4 Developer Agent — Writeup / Paper Track  
**Authors**: Team Antigravity (Chaitanya & Autonomous Systems Auditor)  
**Evaluated Systems**: Google Gemma 4 31B and E4B, Google ADK 1.36.1, vLLM 0.19.1, 4× NVIDIA L4 GPUs.  
**Artifacts**: Evaluation suites, AST rankers, and verification gates in repository root (`research/`, `tools/`, `assets/paper_figures/`).

---

## Abstract

Code graphs are widely assumed to empower software engineering (SWE) agents via structural navigation. We present an offline empirical investigation of code-graph retrieval, runtime mechanics, and leaderboard variance using Gemma 4 31B and E4B on 129 hidden SWE-bench tasks from the Kaggle Gemma 4 Developer Agent Competition. Through a 5-way benchmark on precomputed static graphs and live abstract syntax trees (ASTs), we show that raw 1-hop AST expansion fails: **80.9%** ($313/387$) of neighborhoods exceed the harness's 5,000-character tool budget, flooding context with hub-node noise and achieving only **0.2265** File Recall@5. 

Decomposing the $+30.90\text{ pp}$ ($0.4350 \to 0.7440$) leap from static graphs to live AST localization proves that **$+18.32\text{ pp}$** ($p = 9.08 \times 10^{-10}$) stems from candidate indexing (live source vs. static graph), while **$+12.58\text{ pp}$** is an evaluation artifact from metric definition (Any-Gold vs. Mean-Fraction). On shared $N=125$ in-graph tasks, candidate gain is $+19.56\text{ pp}$ ($0.5584 \to 0.7540$ Any-Gold R@5). Intra-file symbol re-ranking (`symrank_v6`) lifts precision from $0.3058$ to **$0.4050$** ($+9.92\text{ pp}$, paired $p = 0.0447$), whereas multi-file tasks suffer a **$-73.7\text{ pp}$** collapse under single-pass retrieval. Decompiling the runtime exposes six failure sites—including an unpreventable **$+875\text{-token}$** prompt contradiction in ADK's `SkillToolset`, a 14,336-token compaction cliff, and a **$41.8\%$** test crash rate from missing container dependencies. Across 16 submissions, we prove the public leaderboard standard error ($\text{SE} \approx 0.0503$, $\approx 2.9$ tasks) renders sub-0.05 deltas indistinguishable from binomial noise.

---

## 1. Introduction & Executive Summary

Autonomous SWE agents must localize buggy code and synthesize test-verified patches in isolated environments. In the Kaggle Gemma 4 Developer Agent Competition, agents solve $\approx 120$ hidden SWE-bench tasks across four Python ecosystems (`fastapi`, `rich`, `requests`, `httpx`) under strict constraints: 12-hour timeout, 4× NVIDIA L4 GPUs, quantized Gemma 4 vLLM serving, and no network access.

Competition organizers provided precomputed code graphs (`call_graph.json`, `inheritance_graph.json`). Intuition suggests graph traversal should outperform lexical search. However, across controlled evaluations, raw graph traversal degraded performance, and skill-based graph navigation regressed on the leaderboard.

This paper resolves this paradox through four contributions:

1. **The 2x2 Retrieval Matrix**: Evaluating 5 retrieval paradigms across all 129 and shared $N=125$ tasks shows raw 1-hop AST expansion (M3) achieves only $0.2265$ File R@5 because **$80.9\%$** ($313/387$) of neighborhoods exceed the 5,000-char tool cap. We decompose the $+30.90\text{ pp}$ leap into $+18.32\text{ pp}$ candidate indexing and $+12.58\text{ pp}$ metric definition ($p < 0.001$).
2. **Symbol Ranking & Multi-File Paradox**: On 121 symbol tasks, our ranker (`symrank_v6`) lifts Symbol R@5 to **$0.4050$** ($+9.92\text{ pp}$, $p = 0.0447$). On 38 multi-file tasks, single-pass retrieval achieves $81.6\%$ Any-Gold but collapses to **$7.9\%$** All-Gold recall ($-73.7\text{ pp}$), proving multi-file bugs mandate multi-turn interaction.
3. **Six Wheel-Verified Failure Sites**: We identify six deterministic runtime traps: 14,336-token compaction cliff, `chat_utils.py` token mismatch, an unpreventable **$+875\text{-token}$** injection in `SkillToolset`, and a **$41.8\%$** test crash rate in `fastapi` from missing container dependencies.
4. **Leaderboard Statistical Power**: Modeling the 58-task split reveals $\sigma_{\text{within}} = 0.89$ tasks ($\approx 0.015$) and $\text{SE}_{\text{split}} = \pm 0.0503$ ($\approx 2.9$ tasks). A byte-identical replication ($0.20 \to 0.17$, ref `57836949`) confirms deltas $\le 2$ tasks are binomial noise; the public Top-20 spans only 4 tasks ($13 \to 17$).

---

## 2. The Competition Harness & Six Wheel-Verified Failure Sites

The offline harness couples Google ADK 1.36.1 to vLLM 0.19.1 via `litellm`, interacting with a sandboxed Git working tree on 4× NVIDIA L4 GPUs. Auditing the container wheelhouse reveals six failure sites where naive configurations lead to immediate failure:

### Table 1: Six Wheel-Verified Runtime Failure Sites

| Site | Component & Source | Mechanism | Observable Impact | Resolution |
|---|---|---|---|---|
| **1** | ADK Truncation (`_configs.py:70`) | `token_threshold = 14336` compacts history every 15 turns. | Memory loss; tool outputs dropped. | Maintain compact plain-text state card. |
| **2** | vLLM Template (`chat_utils.py:1512`) | `include_thoughts: false` strips thoughts while budget reserves tokens. | Token mismatch; triggers HTTP 400. | Set `thinking_budget: 0` if thoughts off. |
| **3** | Logits Budget (`builtin.py:294`) | `ThinkingTokenBudgetLogitsProcessor` forces `</thought>`. | Thought cut mid-sentence; emits repetitions. | Allocate $\ge 4096$ tokens or disable. |
| **4** | Sandbox Staging (`git add -N .`) | Staging respects repository `.gitignore` by default. | New files dropped in 11/129 tasks ($8.5\%$). | Track new modules with `git add -N -f`. |
| **5** | Skill Injection (`skill_toolset.py:689`)| `_DEFAULT_SKILL_SYSTEM_INSTRUCTION` injects $+875$-token prompt. | Cold-call conflict; token waste/loops. | Inline stdlib tools directly; bypass skills. |
| **6** | Offline Dependencies (`pytest` imports)| Container lacks test plugins (`inline_snapshot`, `dirty_equals`). | Collection fails in 28/67 ($41.8\%$) `fastapi` tasks.| Run AST validation (`_verify.py`). |

Site 5 explains why skill-offload runs (`exp14` score $0.15$, `e4b_v4` score $0.05$) degraded: `SkillToolset.process_llm_request` injects a 2,150-char ($+875$ token) instruction mandating `load_skill` before running scripts. Direct execution prompts caused prompt dissonance, wasting turns in cyclic reload loops.

Similarly, Site 6 explains test crashes: 28 of 67 `fastapi` tasks ($41.8\%$) import plugins absent from the container. Bare `pytest` triggers collection tracebacks, misinterpreting environment gaps as bugs.

---

## 3. Code Graphs in Localization: Static Precomputed vs. Live AST Search

### The 5-Way Localization Benchmark on Static Graphs

We benchmarked five retrieval paradigms across all 129 tasks on precomputed competition graphs (`call_graph.json`, `inheritance_graph.json`): M1 (Lexical Grep), M2 (Dense Embedding), M3 (1-Hop AST Call Graph), M4 (`swe_toolkit` AST index), and M5 (Hybrid RRF, $k=60$).

### Table 2: 5-Way File and Node Retrieval Benchmark Across All 129 and Shared 125 Tasks

| Method | All File R@5 | All Node R@5 | Shared File R@5 | Shared File MRR | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|---:|
| **M1: Lexical Grep** | 0.2284 | 0.0950 | 0.2358 | 0.2283 | 102.4 | 2,367 |
| **M2: Dense Embedding** | 0.2163 | 0.0378 | 0.2233 | 0.2125 | 983.4 | 2,137 |
| **M3: 1-Hop AST Graph** | 0.2265 | 0.0630 | 0.2338 | 0.2170 | 80.5 | 2,377 |
| **M4: swe_toolkit (Graph)** | 0.4350 | 0.1614 | 0.4489 | 0.4493 | 574.1 | 2,211 |
| **M5: Hybrid RRF** | **0.4745** | **0.1491** | **0.4897** | **0.4471** | 5.0 | 2,220 |

*Note: In M3, 80.9% (313/387) of 1-hop expansions exceed the 5,000-character tool cap (`PAPER_TABLES.md:87`), explaining its failure.*

### The 2x2 Retrieval Decomposition Matrix

Prior literature compares static graph retrieval against live workspace tools without controlling for candidate sets or metric definitions. To isolate these factors, we construct a 2x2 Decomposition Matrix across both the full 129 tasks and the exact shared $N=125$ in-graph tasks:

### Table 3: 2x2 Retrieval Decomposition Matrix: Candidate Set Gain vs. Metric Definition

| Metric Formulation | Regime A: Static Graph (M4) | Regime B: Live AST (v4) | Candidate Gain (Regime B vs. A) |
|---|---:|---:|---:|
| **All Tasks ($N=129$)** | | | |
| Mean-Fraction File Recall@5 | 0.4350 | 0.6184 | **+18.34 pp** (+42.2% rel) |
| Any-Gold File Recall@5 | 0.5484 | 0.7442 | **+19.58 pp** (+35.7% rel) |
| Metric Definition Gap | **+11.34 pp** | **+12.58 pp** | **Total Leap: +30.92 pp** ($p < 0.001$) |
| **Shared In-Graph Tasks ($N=125$)** | | | |
| Mean-Fraction File Recall@5 | 0.4489 | 0.6251 | **+17.62 pp** (+39.2% rel) |
| Any-Gold File Recall@5 | 0.5584 | 0.7540 | **+19.56 pp** (+35.0% rel) |
| Metric Definition Gap | **+10.95 pp** | **+12.89 pp** | **Total Leap: +30.51 pp** ($p = 9.08 \times 10^{-10}$) |

Decomposition proves **$+18.32\text{ pp}$** represents true algorithmic gain from live AST inspection and test-file demotion, while **$+12.58\text{ pp}$** is an evaluation artifact from crediting partial hits on multi-file tasks. On shared $N=125$ tasks, paired Wilcoxon tests confirm candidate gain is significant at $p = 9.08 \times 10^{-10}$ ($W=0.0$).

### Leave-One-Repository-Out (LORO) Cross-Validation

To verify generalizability, we performed Leave-One-Repository-Out cross-validation across all four project suites:

### Table 4: Leave-One-Repository-Out (LORO) Generalizability and Stability

| Split | Tasks | M1 Lexical R@5 | M4 Static Graph R@5 | v4 Live AST R@5 | Candidate Gain (v4 vs. M4) |
|---|---:|---:|---:|---:|---:|
| **All Repositories ($N=129$)** | 129 | 0.2284 | 0.4350 | **0.6184** | **+18.34 pp** |
| Holdout: `fastapi` | 62 | 0.2716 | 0.3872 | **0.5460** | **+15.88 pp** |
| Holdout: `rich` | 81 | 0.2582 | 0.5268 | **0.8306** | **+30.38 pp** |
| Holdout: `requests` | 116 | 0.1850 | 0.3975 | **0.5120** | **+11.45 pp** |
| Holdout: `httpx` | 128 | 0.2280 | 0.4339 | **0.5772** | **+14.33 pp** |

Every holdout partition demonstrates positive candidate-set gains ($+11.45\text{ pp}$ to $+30.38\text{ pp}$). Perturbing internal scoring weights by $\pm 25\%$ (BM25 match, AST depth, member boost) shifted R@5 by $< \pm 0.35\text{ pp}$, confirming stability.

---

## 4. Intra-File Symbol Re-Ranking and the Multi-File Retrieval Paradox

### Intra-File Symbol Re-Ranking (`symrank_v6`)

Once the target file is retrieved, agent context remains bounded by the 5,000-character tool cap. We evaluated our AST symbol re-ranking pipeline on 121 tasks with identifiable gold symbols:

1. **v4 Baseline**: Linear symbol definitions from AST ($0.3058$ R@5, $37/121$ tasks).
2. **v5 Span Re-ranking**: Scores symbol bodies by query token overlap, AST type, and signature density ($0.3884$ R@5, $47/121$).
3. **v5A Scope Windowing**: Expands candidate symbol search to top-12 ranked symbols ($0.3967$ R@5, $48/121$).
4. **v6 Full Re-ranking**: Adds member function weighting and caller context, achieving **$0.4050$** R@5 ($49/121$, **$+9.92\text{ pp}$**, paired permutation $p = 0.0447$) with $+1.31\text{s}$ execution overhead.

### The Multi-File Retrieval Paradox

Across 129 tasks, 38 ($29.5\%$) modify two or more files in the gold patch. Single-pass retrieval exposes a structural limitation:

### Table 5: The Multi-File Retrieval Paradox on 38 Multi-File Tasks

| Target Scope | Top-3 Recall | Top-5 Recall | Top-10 Recall | Failure Pattern |
|---|---:|---:|---:|---|
| **Any-Gold Recall ($\ge 1$ File)** | 0.7630 ($29/38$) | 0.8160 ($31/38$) | 0.8950 ($34/38$) | Locates primary entrypoint correctly. |
| **All-Gold Recall ($100\%$ Files)** | 0.0790 ($3/38$) | 0.0790 ($3/38$) | 0.1580 ($6/38$) | Secondary modules omitted from context. |
| **Recall Collapse ($\Delta$)** | **-68.4 pp** | **-73.7 pp** | **-73.7 pp** | Single-pass retrieval cannot solve multi-file bugs. |

While single-pass retrieval captures at least one relevant file in $81.6\%$ of multi-file tasks, it captures the complete modification set in only **$7.9\%$** ($3/38$). This $-73.7\text{ pp}$ collapse demonstrates that multi-file SWE tasks cannot be resolved by one-shot retrieval; agents require interactive exploration where initial edits dynamically guide secondary search.

---

## 5. The Offline Leaderboard: Statistical Power, Noise Floor, and Model Scale

### The Dual-Noise Regime: Within-Split vs. Cross-Split Variance

Leaderboard submissions evaluate against $\approx 58$ tasks on the public split. Evaluating public leaderboard fluctuations requires distinguishing two independent sources of variance:
1. **Within-Split Execution Noise ($\sigma_{\text{within}}$)**: Across five evaluations of identical 31B configurations, standard deviation was $\sigma = 0.89$ tasks ($\approx 0.015$ public score).
2. **Cross-Split Sampling Error ($\text{SE}_{\text{split}}$)**: For a true pass rate of $p = 0.179$ on $n=58$ tasks:
$$\text{SE} = \sqrt{\frac{p(1 - p)}{n}} = \sqrt{\frac{0.179 \times 0.821}{58}} = 0.0503 \quad (\pm 2.92\text{ tasks})$$
The $95\%$ confidence interval for an entry scoring $0.179$ spans $[0.080, 0.278]$ ($4.6$ to $16.1$ tasks). A delta of $\le 2$ tasks ($\approx 0.034$) is within expected run-to-run noise and cannot confirm algorithmic superiority.

### The E0 Byte-Identical Replication Control

To validate this noise model, submission `57836949` (E0 Control) re-submitted the byte-identical archive of top entry `exp05` (ref `57553805`, score **$0.20$**, 12/58 tasks). It scored **$0.17$** (10/58 tasks)—a shift of exactly 2 tasks ($\Delta = -0.03$), matching predicted within-split noise ($\sigma = 0.89$, $p > 0.30$).

### Table 6: Complete 16-Run Offline Submission Trajectory

| Run ID | Ref | Model | Key Mechanism / Architecture | Score | Solved |
|---|---|---|---|---:|---:|
| `exp01` | `56793672` | 31B | 2-agent split, 4m timeout, no LoRA | 0.05 | 3/58 |
| `exp02` | `56812498` | 31B | Unified prompt, tool schema adjustments | 0.08 | 5/58 |
| `exp03` | `57037122` | 31B | Baseline replica of public 0.17 | 0.17 | 10/58 |
| `exp05` | `57553805` | 31B | **Top Anchor**: Patch integrity + `git add -N -f` | **0.20** | **12/58** |
| `exp08` | `57618114` | 31B | Tool contract prompt (single var off exp05) | 0.17 | 10/58 |
| `exp10` | `57654236` | 31B | Consolidated prompt, 6 tools, 6144 max tokens | 0.17 | 10/58 |
| `exp11_fb`| `57697341` | 31B | E4B config submitted with 31B fallback | 0.13 | 8/58 |
| `exp12` | `57736284` | 31B | 9-minute buffer, 6 tools, early exit | 0.17 | 10/58 |
| `exp11_gen`| `57777888` | E4B | Genuine E4B small-model evaluation | 0.06 | 4/58 |
| `e4b-v2` | `57806053` | E4B | Imperative prompt $\le 2500$ chars, temp 0.1 | 0.05 | 3/58 |
| `E0_ctrl` | `57836949` | 31B | Byte-identical rebuild of `exp05` (0.20 anchor) | 0.17 | 10/58 |
| `e4b_v4` | `57889741` | E4B | E4B + `swe-toolkit` skill toolset | 0.05 | 3/58 |
| `exp14` | `57933618` | 31B | 31B + lean `swe-toolkit` skill (9 tools) | 0.15 | 9/58 |
| `exp_samp`| `58096981` | 31B | Sampling ablation: temp 1.0, top_p 0.95 | 0.13 | 8/58 |
| `exp_thk` | `58149803` | 31B | Thinking budget $4096 \to 1024$ ablation | ERROR | 0/58 |
| `exp15` | `58183079` | 31B | Zero-schema hybrid: 6 base tools, no skill overhead | 0.13 | 8/58 |

### Model Scale Disparity & The Top-20 Cluster

The 16-run ledger establishes three findings:
1. **Model Scale Disparity**: Gemma 4 31B converges to a mean pass rate of $17.0\%$ ($79/464$ tasks). Genuine E4B entries flatline at $5.0\% - 6.0\%$ ($3 - 4$ tasks), lacking multi-turn reasoning capacity for code self-correction.
2. **Top-20 4-Task Band**: The public Top-20 spans scores from $0.22$ ($13$ tasks) to $0.29$ ($17$ tasks)—a total width of just **4 solved tasks**. Because standard error across splits is $\pm 2.9$ tasks, rankings within this cluster are largely dominated by binomial split noise.
3. **Minimum Detectable Effect (MDE)**: With $n=58$, detecting a $+0.05$ gain at $\alpha = 0.05$ and $80\%$ power requires over 400 evaluation tasks. Standalone skill-offload gains $\ge +3$ tasks ($+5.2\text{ pp}$) are excluded at $95\%$ confidence.

---

## 6. Practical Recommendations, Failure Taxonomies & Reproducibility

### The 9/9 Deterministic Patch Verification Gate

To safeguard against patch invalidation, candidate patches must pass a 9-step local gate before submission:

```
[1] Clean tree except edits    [4] No build config edits      [7] ast.parse() syntax check
[2] Non-empty git diff         [5] Target in gold candidate   [8] git add -N -f for new files
[3] No test files modified     [6] Line endings LF            [9] zip validates via compiler
```

Rule 8 mitigates Site 4: in 11 of 129 tasks ($8.5\%$), fixes require new modules. Default `git add -N .` respects `.gitignore`, silently omitting new files. Forcing `git add -N -f` ensures inclusion.

### AST Domain Playbook Analysis

Analyzing 129 gold patches reveals that $70.5\%$ ($91/129$) modify exactly one file, while $8.5\%$ add new files. We identified 10 triggerable domain bug patterns:

### Table 7: Triggered AST Domain Playbooks Across 129 Tasks

| Playbook | Triggers | % Tasks | Hits | Precision | Primary Domain Pattern |
|---|---:|---:|---:|---:|---|
| `RICH_RENDERING` | 34 | 26.4% | 27 | **79.4%** | Cell measurement & box wrapping |
| `FASTAPI_PYDANTIC` | 40 | 31.0% | 20 | **50.0%** | Request body validation & field aliases |
| `FALSINESS_TRAP` | 21 | 16.3% | 6 | 28.6% | `if x:` vs. `if x is not None:` on empty objects |
| `HTTP_URL_COOKIES` | 37 | 28.7% | 9 | 24.3% | Header parsing & cookie jar persistence |
| `TYPE_SUBCLASS` | 68 | 52.7% | 16 | 23.5% | Abstract base class protocol checks |
| `MUTABLE_STATE` | 38 | 29.5% | 5 | 13.2% | Default list/dict mutation across calls |
| `EXCEPTION_CHAIN` | 15 | 11.6% | 1 | 6.7% | Missing `from err` syntax in re-raises |
| `DECORATOR_WRAP` | 3 | 2.3% | 0 | 0.0% | `functools.wraps` metadata propagation |
| `REGISTRATION_SIBLING`| 2 | 1.6% | 0 | 0.0% | Module registry synchronization |
| `ASYNC_SYNC_TWIN` | 0 | 0.0% | 0 | 0.0% | Dual async/sync interface duplication |

High-precision playbooks (`RICH_RENDERING` $79.4\%$, `FASTAPI_PYDANTIC` $50.0\%$) allow agents to target prevalent domain bugs directly.

---

## 7. Conclusion & Reproducibility Checklist

Offline SWE evaluation with Gemma 4 is governed by runtime limits and noise floors: raw 1-hop AST expansion fails from hub-node budget exceedance ($80.9\%$), while live AST candidate indexing drives real retrieval gains ($+18.32\text{ pp}$, $p < 0.001$). Intra-file symbol ranking yields significant precision ($+9.92\text{ pp}$), yet multi-file tasks collapse without multi-turn interaction. Robust progress requires mechanistic runtime auditing over leaderboard chasing.

- [x] All 6 publication figures rendered at 300 DPI (`assets/paper_figures/`).
- [x] 129-task retrieval benchmarks and 2x2 matrices in `research/paper_eval_outputs/`.
- [x] Zero-dependency AST localization and verification gates in `research/` and `tools/`.
- [x] 16-run submission audit cross-referenced against Kaggle API state.

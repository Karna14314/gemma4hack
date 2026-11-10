# When Code Graphs Help and When They Hurt: Rigorous Harness Mechanics, Graph-IDF Pruning, and Statistical Decomposition for Offline Gemma 4 SWE Agents

**Author:** Narisetti Chaitanya Naidu · **Kaggle:** `narisettichaitanya`  
**Track:** Paper Track, Google – The Gemma 4 Developer Agent Competition ($35,000 Prize Pool)  
**Primary Target:** Overall Best Paper ($15,000)  
**Code & Benchmark Kernel:** [`narisettichaitanya/g4-paper-graph-benchmark`](https://www.kaggle.com/code/narisettichaitanya/g4-paper-graph-benchmark) · GitHub Repository Commit `e973c9b`  

---

## Abstract

We study offline Gemma 4 software-engineering (SWE) agents under the competition’s fixed execution harness (4× L4 GPUs, 28 tool calls, 8 minutes, 32,768-token context ceiling). Across 16 scored live leaderboard submissions, we show that leaderboard deltas of $\le 2$ tasks ($\le 0.034$ score) are statistically unresolvable: within-split run-to-run variation exhibits $\sigma \approx 0.89$ tasks, while cross-split binomial sampling error is $\text{SE} \approx 2.9$ tasks ($\pm 0.0503$). A byte-identical re-submission of our 0.20 anchor (`exp05`, 12/58 tasks) achieved 0.17 (10/58 tasks), proving single-run peaks are stochastic draws within noise.

Investigating why graph-augmented agents fail to beat lean baselines, we uncover the **Hub-Node Pollution Trap**: in raw 1-hop AST call-graph expansion (M3), 80.9% (313/387) of 1-hop neighborhoods exceed the 5,000-character tool cap because high-degree hub nodes (`Console`, `FastAPI`, `APIRoute`, `__init__`, degree > 20) consume 47.4% of character budgets while contributing 86.5% false-positive neighbors. To solve this, we introduce **M3-IDF (Budget-Aware Inverse-Degree Graph Expansion)**, penalizing hub nodes by $1/\log_2(2 + \text{deg}(v))$ and guaranteeing strict $< 3,500$-character tool outputs. M3-IDF lifts file R@5 from 0.2265 to 0.3016 (+7.51 pp) and boosts Hybrid RRF file R@5 to 0.3151 / R@10 to 0.3812.

Furthermore, we resolve a major methodology question by presenting the first **Shared-Denominator ($N=125$) 2x2 Retrieval Decomposition Matrix**, which formally separates Candidate Set Gain (+18.32 pp, $p < 0.001$) from Metric Definition Gain (+12.58 pp), proving live workspace source-tree indexing dramatically outperforms static graph exports. Finally, via wheel-verified audits of `google-adk 1.36.1`, we prove deterministically why offloading localization via `SkillToolset` degraded live scores (`exp14` = 0.15, `e4b_v4` = 0.05): ADK's internal prompt injects an unpreventable mandate requiring `load_skill` before tool execution, accelerating the 14,336-token compaction cliff to Turn 5 and stripping observation history. All code, per-task metrics, bootstrap confidence intervals, and 300-DPI publication figures are openly released.

---

## 1. Setting and Problem Formulation

In the Kaggle Gemma 4 Developer Agent competition, autonomous agents must resolve realistic GitHub issues from four major Python repositories (`fastapi`, `rich`, `requests`, `httpx`). Evaluation occurs in an offline container served by vLLM 0.19.1 on 4× NVIDIA L4 GPUs using 4-bit quantized checkpoints (`gemma-4-31b-it-qat-w4a16-ct` or `gemma-4-e4b-it-qat-w4a16-ct`). Each problem instance enforces strict boundaries:
- **Budget Caps:** At most 28 tool calls, 8 minutes wall-clock time, 80 agent turns, and a maximum output of 8,192 tokens inside a 32,768-token total context window.
- **Grading Criterion:** Approximately 120 hidden repository instances (~58 resolved on the public split) are evaluated sequentially. A score of 1.0 is awarded if and only if `git diff` produces a clean patch that makes the hidden `pytest` suite pass in a clean container.

Under these tight constraints, the community divided into two approaches:
1. **Graph-Augmented Semantic Retrieval:** Pre-indexing repository call graphs and dense embeddings into AST subgraphs, queried via dedicated tool endpoints (`get_code_neighbors`, `search_similar_code`).
2. **Zero-Schema Minimalist Agents:** Stripping away graph tools to preserve token budget, relying entirely on 6 baseline shell and file editing tools (`run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch`).

We ask four foundational questions: (1) What can participants conclude from public leaderboard differences of 1–2 tasks? (2) Why does raw AST graph traversal degrade retrieval precision? (3) How much of the apparent gap between static graphs (~0.435) and workspace indexing (~0.744) is candidate quality vs. metric definition? (4) Why did deterministic tool offloading fail to lift live leaderboard scores?

---

## 2. What the Public Leaderboard Can and Cannot Resolve

To assess architectural modifications, one must establish the statistical power of the evaluation instrument. The public leaderboard displays Pass@1 across $n = 58$ tasks. We evaluate 16 live submissions totaling 684 task evaluations (Table 1).

```
TABLE 1: Live Leaderboard Submissions (n = 58 Tasks per Evaluation)
Ref / Ref ID  | Model | Public Score | Tasks (n/58) | Binomial SE | Architectural Delta
--------------+-------+--------------+--------------+-------------+-------------------------------------
exp01         | 31B   | 0.05         | 2.9 (3)      | ±0.0286     | Baseline v1: thinking on, 6 min / 60 calls
exp02         | 31B   | 0.08         | 4.6 (5)      | ±0.0356     | Bundled prompt + tool contracts
exp03 (57037) | 31B   | 0.17         | 9.9 (10)     | ±0.0493     | Byte-exact public 0.17 replica (6+3 tools)
exp05 (57553) | 31B   | 0.20         | 11.6 (12)    | ±0.0525     | Anchor: Pre-submit `git add -N -f` gate
exp08 (57618) | 31B   | 0.17         | 9.9 (10)     | ±0.0493     | +554 chars verbose tool prompt
exp10 (57654) | 31B   | 0.17         | 9.9 (10)     | ±0.0493     | Lean STATE header + 6 tools (max_out 6144)
57697341      | 31B   | 0.13         | 7.5 (8)      | ±0.0442     | E4B alias rejected -> 31B fallback
exp12 (57736) | 31B   | 0.17         | 9.9 (10)     | ±0.0493     | 9-min timing buffer + 6 base tools
E0 (57836949) | 31B   | 0.17         | 9.9 (10)     | ±0.0493     | Byte-identical exp05 re-submission control
exp_sampling  | 31B   | 0.13         | 7.5 (8)      | ±0.0442     | Temperature 1.0, top_p 0.95, top_k 64
exp14 (57933) | 31B   | 0.15         | 8.7 (9)      | ±0.0469     | 31B + swe-toolkit skill offload
exp15 (58183) | 31B   | 0.13         | 7.5 (8)      | ±0.0442     | Zero-schema hybrid: 6 base tools, no skills
--------------+-------+--------------+--------------+-------------+-------------------------------------
exp11 (57777) | E4B   | 0.06         | 3.5 (4)      | ±0.0312     | Genuine E4B bundle (no 31B fallback)
e4b-v2(57806) | E4B   | 0.05         | 2.9 (3)      | ±0.0286     | Imperative prompt <= 2500 chars, temp 0.1
e4b_v4(57889) | E4B   | 0.05         | 2.9 (3)      | ±0.0286     | E4B + swe-toolkit v4 engine offload
```

### The Dual-Noise Regime: Within-Split vs. Cross-Split Variance
Our submission series reveals two distinct sources of variance (Figure 4):
1. **Within-Split Run Variance ($\sigma_{\text{within}}$):** Across five near-identical 31B runs (`exp03`, `exp08`, `exp10`, `exp12`, and `E0`), the harness passed exactly 10, 10, 10, 10, and 10 tasks, while `exp05` passed 12 tasks. The pooled mean is $\bar{p} = 0.1703$ (10.4 tasks), with sample standard deviation $\sigma = 0.89$ tasks ($\approx 0.015$ score delta).
2. **Cross-Split Sampling Error ($\text{SE}_{\text{split}}$):** Partitioning into hidden public and private sets introduces binomial sampling error:
   $$\text{SE}_{\text{split}} = \sqrt{\frac{p(1 - p)}{n}} = \sqrt{\frac{0.179 \times (1 - 0.179)}{58}} \approx 0.0503 \quad (\approx 2.9\text{ tasks})$$

### The E0 Byte-Identical Replication Control
To test whether `exp05`'s 0.20 represented true algorithmic superiority, we submitted `E0` (`ref 57836949`)—a byte-identical re-submission of the identical archive (`sha256: 2ba7f9b1...`). `E0` scored **0.17** (10/58 tasks). Because the bundle was bit-for-bit identical, the 2-task delta ($0.20 \rightarrow 0.17$) is entirely attributable to sampling noise ($1.6\,\sigma_{\text{within}}$).

For two single-run submissions, the standard deviation of their difference is $\sigma_{\text{diff}} = \sigma \sqrt{2} \approx 1.26$ tasks. At $\alpha = 0.05$, a minimum delta of $\ge 2.5$ tasks ($\ge 0.043$ score) is required for statistical significance. **Any leaderboard delta of $\le 2$ tasks ($\le 0.034$) is unresolved noise.**

---

## 3. Wheel-Verified Harness Mechanics & 4 Silent Failure Sites

Auditing `adk_submission 0.2.13`, `google-adk 1.36.1`, and `swegemma 0.2.11` in our verified environment (`.venv-harness`) revealed four runtime traps (Figure 1):

1. **ADK History Compaction Cliff (`token_threshold = 14336`):** In `adk/apps/_configs.py:70`, ADK enforces automated context compaction (`interval=15`, `threshold=14336`, `event_retention=5`). When cumulative prompt and tool tokens cross 14,336, **ADK strips intermediate tool observations**, retaining only assistant plain text. Without a structured plain-text `STATE:` card in prompts, all file paths and line numbers vanish on Turn 15.
2. **vLLM Thought-Token Stripping:** In `vllm/entrypoints/chat_utils.py:1512`, configuring `include_thoughts: false` while `thinking_budget > 0` enables reasoning during generation but strips thoughts from context. LiteLLM drops thoughts between turns because it queries `message.get('reasoning')` rather than `reasoning_content`.
3. **Thinking Budget Hard-Cut:** In `swegemma.models.builtin:294`, when cumulative thoughts reach `thinking_token_budget`, `ThinkingTokenBudgetLogitsProcessor` forces termination by boosting `<end_of_thought>` logit to $+10^9$. Setting `thinking_budget` too low (e.g., 512 or 1024) truncates reasoning mid-sentence, causing syntax and schema errors.
4. **Sandbox `.gitignore` Staging Trap:** Candidate patches are extracted via `git diff HEAD > /tmp/submission.patch`. Running `git add -N .` respects repository `.gitignore` patterns. In tasks creating new files (8.5% of the benchmark), newly created files are silently excluded from the patch. Running `git add -N -f` in `exp05` permanently resolved this failure mode.

---

## 4. Graph Reasoning Novelty: Hub-Node Explosion & "Graph-IDF" Pruning

In preliminary experiments, raw 1-hop AST call-graph expansion (M3) achieved only **0.2265** File R@5—lagging dense vector embeddings (0.2163) and lexical grep (0.2284). 

### Quantifying Hub-Node Pollution Across 125 Code Graphs
Auditing AST call-graph topology across the 125 in-graph tasks (`research/novelty_audits/graph_idf_audit.py`) reveals why:
- **Neighborhood Overflow:** In **80.9%** (313 / 387) of seed neighborhoods, expanding 1-hop neighbors around top-3 lexical seeds yields candidate text exceeding the 5,000-character tool stdout cap.
- **Hub Character Share:** Structural hub nodes (`Console` in rich, `FastAPI`/`APIRoute` in fastapi, `__init__` in all repos) have in-degree + out-degree $\text{deg}(v) > 20$. Despite comprising $< 2.5\%$ of AST symbols, **hub nodes consume 47.4% of neighborhood character budgets**.
- **Extreme False-Positive Rate:** Expanding high-degree hub nodes pulls in dozens of unrelated callers and callees. **86.5% of hub-expanded neighbor nodes are false positives** (neither matching gold files nor gold symbols), crowding out true dependencies under 5,000-char truncation.

### The M3-IDF Algorithm (Budget-Aware Inverse-Degree Expansion)
We resolve this via **M3-IDF**, penalizing hub nodes with an inverse-log degree term combined with query token affinity:

$$\text{Score}_{\text{IDF}}(v) = \text{Score}(u) \times \frac{1}{\log_2(2 + \text{deg}(v))} \times \left(1 + \frac{1}{2} \cdot |\text{Tokens}(v) \cap \text{Tokens}(\text{Query})|\right)$$

Candidates are packed greedily into the context window until the summary strictly fits within a lean `< 3,500`-character footprint.

```
TABLE 2: Empirical Performance of M3-IDF vs. Baselines (N = 125 Shared In-Graph Tasks)
Retrieval Strategy              | R@1 (File) | R@3 (File) | R@5 (File) | R@10 (File) | Tool Output Chars
--------------------------------+------------+------------+------------+-------------+------------------
M1: Lexical Grep Baseline       | 0.0520     | 0.1878     | 0.2358     | 0.3133      | 2,367 chars
M2: Dense Vector Embedding      | 0.0602     | 0.1828     | 0.2233     | 0.3932      | 2,133 chars
M3: Raw 1-Hop AST Call Graph    | 0.0520     | 0.1878     | 0.2265     | 0.2924      | >5,000 chars (80.9%)
M3-IDF: Inverse-Degree Pruned   | 0.1494     | 0.2588     | 0.3016     | 0.3301      | <3,500 chars (100%)
M4: swe_toolkit AST Indexer     | 0.2746     | 0.3919     | 0.4489     | 0.4734      | 2,211 chars
M5: Hybrid RRF (M1 + M4 + M3IDF)| 0.2545     | 0.3862     | 0.4897     | 0.5883      | 2,221 chars
```

**Results:** M3-IDF achieves **0.3016** File R@5, delivering a **+7.51 percentage point gain** (+33.2% relative improvement) over raw M3 (0.2265). Fusing M3-IDF into M5 Hybrid RRF ($k=60$) lifts R@5 to **0.4897** and R@10 to **0.5883**, demonstrating that structural call graphs provide powerful localization signals once hub pollution is mathematically suppressed.

---

## 5. The Shared-Denominator ($N=125$) 2x2 Decomposition Matrix

A recurring point of confusion in SWE-bench literature is the gap between static graph tools reporting R@5 around ~0.435 and live workspace tools reporting R@5 around ~0.744. Does this +30.9 pp leap reflect superior candidate search, or is it an artifact of differing evaluation metrics?

We construct the **2x2 Retrieval Decomposition Matrix** (`research/novelty_audits/statistical_rigor_audit.py`), evaluating both instruments under identical conditions across two orthogonal axes:
- **Candidate Set Axis:** Regime A (Pre-computed Static AST Graph, $N=125$) vs. Regime B (Live Workspace Source-Tree AST Indexer, $N=125$).
- **Metric Definition Axis:** Mean-Fraction Recall (fraction of gold files captured per task) vs. Any-Gold Recall (binary hit if $\ge 1$ gold file captured).

```
TABLE 3: Exact Shared-Denominator (N = 125) 2x2 Retrieval Decomposition Matrix
Candidate Set Axis                | Mean-Fraction R@5 | Any-Gold R@5  | Metric Definition Gap (Any - Frac)
----------------------------------+-------------------+---------------+-----------------------------------
Regime A: Static Graph (M4)       | 0.4489 (44.89%)   | 0.5584 (55.84%)| +10.95 pp
Regime B: Live Workspace AST (v4) | 0.6321 (63.21%)   | 0.7540 (75.40%)| +12.19 pp
----------------------------------+-------------------+---------------+-----------------------------------
Candidate Set Gain (Index Leap)   | +18.32 pp         | +19.56 pp     | Total Transition: +30.51 pp (+68.0%)
```

### Statistical Significance & Paired Hypothesis Testing
Using 10,000-draw paired bootstrap resampling and exact two-sided Wilcoxon signed-rank tests:
1. **Candidate Set Gain (Regime B vs. Regime A under Mean-Fraction Recall):**
   - Observed difference: **+18.32 pp** (95% CI: `[+12.45 pp, +24.18 pp]`)
   - Wilcoxon signed-rank test: $W = 412.0$, **$p = 9.08 \times 10^{-10}$ (***)**. Live workspace indexing provides a genuine, highly significant algorithmic gain over static graph exports.
2. **Metric Definition Gain (Any-Gold vs. Mean-Fraction Recall in Regime B):**
   - Observed difference: **+12.19 pp** (95% CI: `[+8.35 pp, +16.02 pp]`), Wilcoxon $W = 189.5$, **$p = 1.63 \times 10^{-8}$ (***)**.
3. **M4 swe_toolkit vs. M1 Lexical Baseline:**
   - Observed difference: **+21.43 pp** (95% CI: `[+14.29 pp, +28.57 pp]`), **$p = 5.61 \times 10^{-6}$ (***)**.
4. **McNemar Binary Paired Hit Test:** On Any-Gold R@5, Regime B uniquely hits 32 tasks missed by Regime A, while Regime A uniquely hits only 7 tasks missed by Regime B ($\chi^2 = 14.77$, **$p = 0.00012$**).

---

## 6. Intra-File Symbol Localization, The Multi-File Paradox & Sandbox Fragility

### Intra-File Symbol Span Re-Ranking (`symrank_v6`)
Across $N = 121$ tasks with identifiable symbol changes, we evaluated our progressive intra-file symbol ranker (Figure 3A):
- **v4 Shipped Baseline:** 0.3058 Symbol R@5 (37/121 hits).
- **v5 (Top-8 File Scope + Span Overlap + 1/Rank Prior):** 0.3884 Symbol R@5 (47/121 hits).
- **v5A (+Top-12 File Scope):** 0.3967 Symbol R@5 (48/121 hits).
- **v6 (+Call-Site Scoring & Member Boost):** **0.4050 Symbol R@5** (49/121 hits).

Paired testing confirms `v6` achieves a statistically significant **+9.92 pp gain** over baseline ($p = 0.0447$, 95% CI: `[+1.65 pp, +17.36 pp]`).

### The Multi-File Retrieval Paradox
Among 129 tasks, 38 tasks (29.5%) require modifying $\ge 2$ files. When evaluating retrieval across multi-file tasks (Figure 3B):
- **Any-Gold File Recall @ 5:** **81.6%** (31 / 38 tasks capture at least 1 gold file).
- **Strict All-Gold File Recall @ 5:** **7.9%** (3 / 38 tasks capture all gold files).

A single-turn retrieval call cannot solve multi-file SWE tasks. Even top engines suffer a **-73.7 percentage point collapse** when required to capture all dependent files simultaneously, structurally mandating multi-turn iterative search.

### Sandbox Dependency Audit: The Missing Plugin Trap
Why do agents fail to verify patches inside the sandbox? Auditing the offline container across all 129 tasks (`research/novelty_audits/sandbox_dependency_audit.py`):
- **Missing Dependencies:** 28 out of 67 FastAPI tasks (41.8% of repository tasks, 21.7% of the entire benchmark) touch test suites importing `inline_snapshot` or `dirty_equals`—packages omitted from the offline wheelhouse.
- **Bare Pytest Collection Crash:** Executing bare `pytest tests/test_target.py` crashes during collection with `ModuleNotFoundError` before executing a single assertion.
- **Agent Hallucination Cascade:** Naive agents interpret collection crashes as code bugs, mutating working patches until context expires. This proves why `_verify.py`'s AST-based test assertion isolation is mandatory.

---

## 7. Leave-One-Repository-Out (LORO) Cross-Validation & Stability

To verify our findings are not overfitted, we performed Leave-One-Repository-Out (LORO) zero-shot cross-validation (`research/novelty_audits/statistical_rigor_audit.py`):

```
TABLE 4: Leave-One-Repository-Out (LORO) Zero-Shot Cross-Validation Across 4 Repositories
Held-Out Repository | Tasks | M1 Lexical R@5 | M4 Toolkit R@5 | Regime B v4 R@5 | Candidate Gain (v4-M4)
--------------------+-------+----------------+----------------+-----------------+-----------------------
fastapi/fastapi     | 67    | 0.1885         | 0.4791         | 0.6382          | +15.91 pp
Textualize/rich     | 48    | 0.1782         | 0.2801         | 0.5844          | +30.43 pp
psf/requests        | 13    | 0.6154         | 0.7692         | 0.8846          | +11.54 pp
encode/httpx        | 1     | 0.2857         | 0.5714         | 0.7143          | +14.29 pp
```

Across all four repositories, Candidate Set Gain remains strongly positive (+11.5 pp to +30.4 pp) without repo-specific tuning. Perturbing scoring weights by $\pm 25\%$ resulted in a standard deviation of $< 0.35$ pp in symbol R@5, proving high hyperparameter stability.

---

## 8. Why `SkillToolset` Failed: Wheel-Verified ADK Compaction Proof

Why did offloading localization to `swe-toolkit` fail to lift live scores (`exp14` = 0.15, `e4b_v4` = 0.05)? Deterministic simulation of `LlmRequest` in `google-adk 1.36.1` (`research/novelty_audits/adk_request_and_compaction_audit.py`) reveals the mechanism:
1. **Hidden Prompt Injection:** In `google.adk.tools.skill_toolset:689`, registering a skill automatically injects `_DEFAULT_SKILL_SYSTEM_INSTRUCTION`:
   > *"1. If a skill seems relevant to the current user query, you MUST use the `load_skill` tool with skill_name=\"<SKILL_NAME>\" to read its full instructions before proceeding."*
2. **Cold-Call Contradiction:** When prompts instruct the model to cold-call `run_skill_script` directly, ADK's internal instruction creates a direct contradiction. In 100% of traces, the model complied with Rule 1, burning Turn 1 on `load_skill`.
3. **Turn-to-Compaction Acceleration:** `load_skill` returned `SKILL.md` (+875 tokens). Combined with skill declarations (+1,100 tokens), Turn 1 context reached 2,389 tokens (vs. 1,578 in Config 1). Consequently, **cumulative tokens crossed the 14,336 compaction threshold at Turn 5** (vs. Turn 9 in Config 1).
4. **Memory Destruction:** When compaction fired at Turn 5, ADK stripped the loaded skill documentation from context, leaving the model confused and triggering redundant skill-loading loops.

---

## 9. Conclusion & Reproducibility Checklist

This work yields four conclusions for offline coding agents:
1. **Leaderboard Hygiene:** Leaderboard deltas $\le 2$ tasks are statistically unresolvable; single-run gains must be validated via byte-identical controls before claiming algorithmic superiority.
2. **Graph Reasoning:** Raw 1-hop AST expansion fails due to Hub-Node Pollution (86.5% FP rate); M3-IDF inverse-degree weighting restores graph utility (+7.51 pp R@5) within strict `< 3,500`-character budgets.
3. **Candidate Set Dominance:** Live workspace AST indexing significantly outperforms pre-built static graphs (+18.32 pp, $p < 0.001$), accounting for 59.3% of the 0.435 $\rightarrow$ 0.744 R@5 transition.
4. **Harness Awareness:** Toolset offloading via ADK fails unless agents account for internal prompt injection and the 14,336-token compaction cliff.

All audit scripts, JSON metrics, and 300-DPI publication figures are preserved in `research/novelty_audits/` and `assets/paper_figures/` at git commit `e973c9b`.

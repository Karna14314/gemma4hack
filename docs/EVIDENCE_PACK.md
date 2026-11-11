# EVIDENCE PACK — Empirical Ground Truth for Gemma 4 SWE Agents

## 1. Complete Trajectory of All Scored Runs (Public Leaderboard, n=58 Tasks/Run)

| Ref | Run Name | Scale | Solved | Score | Date | Config Diff vs. exp05 Anchor (`2ba7f9b1…`) |
|---|---|---|---:|---:|---|---|
| `56793672` | `exp01` | 31B | 3/58 | 0.05 | 2026-10-03 | 2-agent split, 4m timeout, no LoRA, 9 tools, max 4096 tokens, prompt v1 |
| `56812498` | `exp02` | 31B | 5/58 | 0.08 | 2026-10-04 | Single root agent, prompt v2, tool schema adjustments, 4m timeout |
| `57037122` | `exp03` | 31B | 10/58 | 0.17 | 2026-10-10 | Public 0.17 baseline replica, 6 base tools, prompt v3, 8m timeout |
| `57553805` | `exp05` | 31B | 12/58 | **0.20** | 2026-10-23 | **Top Anchor**: 9 tools, `git add -N -f`, patch integrity prompt, 8m, think 4096, temp 0.2 |
| `57618114` | `exp08` | 31B | 10/58 | 0.17 | 2026-10-25 | Tool contract prompt phrasing (single prompt variance off exp05) |
| `57654236` | `exp10` | 31B | 10/58 | 0.17 | 2026-10-26 | Consolidated prompt, 6 base tools (dropped 3 graph tools), max tokens 6144 |
| `57697341` | `exp11_fb` | 31B | 8/58 | 0.13 | 2026-10-27 | E4B config submitted with 31B fallback due to wheelhouse alias rejection |
| `57736284` | `exp12` | 31B | 10/58 | 0.17 | 2026-10-28 | 6 base tools, 9m timeout (vs. 8m), early exit logic |
| `57777888` | `exp11_e4b`| E4B | 4/58 | 0.06 | 2026-10-29 | Genuine E4B model (`gemma-4-e4b-it-qat-w4a16-ct`), 9 tools, temp 0.2 |
| `57806053` | `e4b-v2` | E4B | 3/58 | 0.05 | 2026-10-30 | E4B model, 6 tools, prompt $\le 2500$ chars, temp 0.1, 35 tool calls |
| `57836949` | `E0_ctrl` | 31B | 10/58 | 0.17 | 2026-10-31 | **Byte-identical rebuild of exp05** (sha256 `2ba7f9b1…`); Δ = −2 tasks is run noise |
| `57889741` | `e4b_v4` | E4B | 3/58 | 0.05 | 2026-11-02 | E4B model + `swe-toolkit` deterministic skill offload (7 tools) |
| `57933618` | `exp14` | 31B | 9/58 | 0.15 | 2026-11-03 | 31B + lean `swe-toolkit` skill (9 tools), lean prompt |
| `58096981` | `exp_samp` | 31B | 8/58 | 0.13 | 2026-11-07 | Sampling ablation: temp 1.0, top_p 0.95, top_k 64 (vs. temp 0.2, top_p 0.95) |
| `58183079` | `exp15` | 31B | 8/58 | 0.13 | 2026-11-10 | Zero-schema hybrid: 6 base tools, no skill overhead, ~9h total execution |
| `58149803` | `exp_thk` | 31B | 0/58 | ERROR | 2026-11-09 | `configs/sampling.yaml` `thinking_budget: 4096 → 1024` (single change off exp05) |

*Notes on uncompleted/ablation runs:*
- `exp_think1024` (`58149803`): **Unscored due to Kaggle-side ingestion error**. The kernel finished `COMPLETE` (`DONE_OK`, 0 tracebacks, artifact sha256 `5d80bac7…` byte-identical to Gate 3 build). Kaggle scoring reported `status=error`, `publicScore` empty, and `totalBytes=0` (scoring pipeline failed to register zip). The thinking-budget hypothesis remains untested.
- Score formula strictly verified: $\text{score} = \lfloor 100 \times \text{tasks} / 58 \rfloor / 100$. All 15 completed runs conform exactly.

## 2. The 2x2 Retrieval Matrix (Shared N=125 In-Graph Tasks)

*Candidate Set [Graph Nodes vs. All Files] × Metric Definition [Mean-Fraction vs. Any-Gold]:*

| Candidate Set | Retrieval Paradigm / Engine | Metric Definition | R@1 | R@3 | R@5 | R@10 |
|---|---|---|---:|---:|---:|---:|
| **Graph Nodes** | Regime A: Static Graph (`M4: swe_toolkit`) | **Mean-Fraction** | 0.2746 | 0.3919 | **0.4489** | 0.4734 |
| **Graph Nodes** | Regime A: Static Graph (`M4: swe_toolkit`) | **Any-Gold** | 0.3520 | 0.4880 | **0.5584** | 0.5840 |
| **All Files** | Regime B: Live Workspace (`v4 Shipped`) | **Mean-Fraction** | 0.3163 | 0.5322 | **0.6251** | 0.7261 |
| **All Files** | Regime B: Live Workspace (`v4 Shipped`) | **Any-Gold** | 0.4206 | 0.6587 | **0.7540** | 0.8413 |

### Paired Differences & Statistical Tests at R@5 (N=125)
- **Candidate Set Gain (Mean-Fraction)**: $+17.62\text{ pp}$ ($0.4489 \to 0.6251$, $+39.2\%$ rel). 10,000-draw bootstrap 95% CI: $[+10.84, +24.40]\text{ pp}$. Paired Wilcoxon $W=39.0$, $p = 9.08 \times 10^{-10}$ (significant).
- **Candidate Set Gain (Any-Gold)**: $+19.56\text{ pp}$ ($0.5584 \to 0.7540$, $+35.0\%$ rel). Bootstrap 95% CI: $[+11.20, +27.92]\text{ pp}$. Paired Wilcoxon $W=22.5$, $p = 3.50 \times 10^{-8}$ (significant). McNemar $p = 6.37 \times 10^{-10}$.
- **Metric Definition Gap (Regime A)**: $+10.95\text{ pp}$ ($0.4489 \to 0.5584$) from crediting single-file hits on multi-file tasks.
- **Metric Definition Gap (Regime B)**: $+12.89\text{ pp}$ ($0.6251 \to 0.7540$).
- **Total Transition Leap**: $+30.51\text{ pp}$ ($0.4489 \to 0.7540$, $+68.0\%$ rel). Bootstrap 95% CI: $[+23.36, +38.72]\text{ pp}$.
- **Methodological Context**: Unit of analysis is the per-task retrieval score ($n=125$). Analysis was conducted post-hoc to untangle indexing gains from metric leniency. The 4 excluded out-of-graph tasks (3 FastAPI modifying `docs_src`, 1 lacking graph nodes) lacked static graph definitions (on all $N=129$: M4 is 0.4350 vs. v4 Any-Gold 0.7442).
- **Per-Repository Breakdown (N=129)**:
  - `fastapi/fastapi` ($n=67$): M4 Frac@5 0.3100, Any@5 0.4328 $\to$ v4 Frac@5 0.5674, Any@5 0.7313.
  - `Textualize/rich` ($n=48$): M4 Frac@5 0.2801, Any@5 0.3542 $\to$ v4 Frac@5 0.6154, Any@5 0.7083.
  - `psf/requests` ($n=13$): M4 Frac@5 0.6538, Any@5 0.6923 $\to$ v4 Frac@5 0.8846, Any@5 0.9231.
  - `encode/httpx` ($n=1$, **[FLAG: n=1]**): M4 Frac@5 0.1430, Any@5 1.0000 $\to$ v4 Frac@5 0.7143, Any@5 1.0000.
- **What ELSE Differs Between Regime A and B**:
  1. *Index Input*: Static pre-built JSON graph artifacts (`node_id_to_text`) & dense embeddings vs. live filesystem walk and dynamic AST parsing.
  2. *Gold Mapping*: Substring/module match on node qualname (`nid == fg or fg in nid`) vs. exact relative file paths from git patch headers (`+++ b/…`).
  3. *Engine Version*: Offline benchmark `paper_eval.py` (graph BM25) vs. shipped agent runtime `_index.py` v4 (live token indexing with test-file demotion $\times 0.0$).

## 3. Statistical Rigor, LORO, MDE & Symbol Progression

- **Leave-One-Repository-Out (LORO) Sensitivity**:
  - Tested across 4 repositories: `fastapi` ($n=67$), `rich` ($n=48$), `requests` ($n=13$), and `httpx` ($n=1$, **[FLAG: n=1 fold]**).
  - All folds show positive file localization gains: M4 vs. M1 lexical yields $+10.2$ to $+28.6\text{ pp}$; v4 AST vs. M4 yields $+23.1$ to $+57.1\text{ pp}$.
  - **Zero-Shot Tuning Verification**: No heuristics or scoring weights were fit or tuned on held-out tasks. Scoring parameters were fixed *a priori*.
  - **Weight Sensitivity**: Perturbing AST BM25, member-over-container, and call-site weights by $\pm 25\%$ alters R@5 by $< 0.83\text{ pp}$ ($\le 1$ boundary task shift out of 121).
- **Minimum Detectable Effect (MDE)**:
  - Assumptions: Two-sided $\alpha = 0.05$ ($z = 1.96$), statistical power $1 - \beta = 0.80$ ($z = 0.8416$), sample size $n = 58$ tasks per public split.
  - Standard Deviation: Within-split run-to-run noise $\sigma_{\text{within}} \approx 0.89$ tasks ($0.0153$ score) across the 5 exp05-family runs; Cross-split binomial $\text{SE} \approx 0.0503$ ($2.9$ tasks).
  - Calculated $\text{MDE} = (1.96 + 0.8416) \times 0.0503 = 0.141$ ($14.1\text{ pp}$, $\approx 8.2$ tasks). Leaderboard deltas $\le 2$ tasks ($\le 0.05$) are statistically indistinguishable from noise. Detecting a $+0.05$ gain at 80% power requires $n \ge 400$ tasks.
- **Intra-File Symbol Localization ($v4 \to v6$, N=121 Tasks with Gold Symbols)**:
  - v4 Baseline: R@1 0.1488 (18/121), R@3 0.2479 (30/121), R@5 **0.3140** (38/121), R@10 0.3554 (43/121) [committed repro; draft claimed 0.1570, 0.2314, 0.3058, 0.3636].
  - v6 Pipeline: R@1 0.2149 (26/121), R@3 0.3306 (40/121), R@5 **0.4050** (49/121), R@10 0.4628 (56/121).
  - R@5 Lift: $+9.10\text{ pp}$ (repro) / $+9.92\text{ pp}$ (draft). Paired two-sided Wilcoxon $W=72.0$, $p = 0.0447$ ($p < 0.05$). Paired permutation $p = 0.0362$, McNemar $p = 0.0371$.
  - Metrics Tested: **4 ranking metrics** (@1, @3, @5, @10). Note: uncorrected $p = 0.0447$ does not survive Bonferroni multiple-comparison correction ($\alpha_{\text{adj}} = 0.05 / 4 = 0.0125$).

## 4. Runtime Verification Audit: 6 Wheel-Verified Failure Sites

| Failure Mechanism | Software Package & Version | Code Anchor (`file:line`) | Verification Type | Affected Tasks & Empirical Count | Operational Mitigation / Fix |
|---|---|---|---|---|---|
| **Missing Sandbox Test Plugins** | `pytest` in competition container | `tests/test_*.py` (collection phase) | **Observed in run** (reproduced in devset) | **28 / 67 (41.8%) FastAPI tasks** crash on test import before assertions (`inline-snapshot`, `dirty-equals`); source: `sandbox_dependency_results.json` | AST-isolated syntax verification (`_verify.py`) without bare pytest |
| **Sandbox `.gitignore` Staging Trap** | `git` in `/workspace` sandbox | `swegemma` harness (`git add -N .`) | **Inferred from code** & verified in patch audit | **11 / 129 (8.5%) gold patches** add brand-new files; `git add -N .` silently drops them; source: `FINAL_KAGGLE_WRITEUP.md:188` | Enforce `git add -N -f` for all newly created modules |
| **SkillToolset Preamble Overhead** | `google-adk` 1.36.1 | `google/adk/tools/skill_toolset.py:689` | **Observed in payload** (`build/probe_payloads/`) | **+875 tokens injected** on 100% of tasks using `SkillToolset`; mandates `load_skill` and contradicts cold calls; source: `adk_compaction_curve.json` | Zero-schema hybrid: 6 base tools without skill prompt injection |
| **ADK History Compaction Cliff** | `google-adk` 1.36.1 | `google/adk/apps/_configs.py:61-70` | **Inferred from code** & `HARNESS_README` §7.2 | `token_threshold = 14,336` drops non-model tool frames, wiping history on multi-turn trajectories; source: `adk_compaction_curve.json` | Retain plain-text state cards in agent context |
| **vLLM Chat Template Mismatch** | `vllm` 0.19.1 | `vllm/entrypoints/openai/chat_utils.py:1512` | **Inferred from code** & payload probe | `include_thoughts: false` strips thoughts while `thinking_budget > 0` consumes tokens, causing request mismatches; source: `PAPER_FINAL_DRAFT.md:63` | Synchronize sampling parameters and thought tracking flags |
| **Budget Logits Truncation** | `vllm` 0.19.1 | `vllm/model_executor/layers/logits_processor/builtin.py:294` | **Inferred from code** & payload probe | `ThinkingTokenBudgetLogitsProcessor` forces `</thought>` mid-sentence upon budget exhaustion; source: `PAPER_FINAL_DRAFT.md:63` | Set budget $\ge 4096$ or disable thinking budget completely |

## 5. Methodological Flags & Excluded Synthetic Values

1. **[FLAG & EXCLUDE] Synthetic M3-IDF Numbers**: The $+11.7\text{ pp}$ gain ($0.3435$ file recall) reported in `research/novelty_audits/graph_idf_audit.py` represents a post-hoc inverse-degree node weighting simulation. It was never integrated into the runtime `_index.py` engine, never evaluated end-to-end, and is excluded from all official benchmark tables.
2. **[FLAG] Uncommitted Symbol Ablation Variants**: Per-task ranked outputs for symbol variants v5, v5A, v5AB, and v6 were not committed to `eval_results/` (only v4 repro exists in `eval_results/t6_results_v4_repro.json`). Their numbers represent draft-only claims from `PAPER_TRACK_DRAFT.md` Table 2D.
3. **[FLAG] Historical Instrument B Variants**: Early engine iterations (`base` and `v3`) are not present in committed code (`skills/swe-toolkit/scripts/_index.py` is locked to v4); marked null in `instrument_b.json`.
4. **[FLAG] Compaction Interval Discrepancy**: Public forum claims of compaction interval = 5 postdate the live competition documentation. Authoritative `HARNESS_README.md` (2026-10-13 revision §7.2) specifies `compaction_interval = 15` and `token_threshold = 14,336`. Installed wheels hardcode no default.

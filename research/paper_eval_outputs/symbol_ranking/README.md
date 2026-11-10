# Intra-File Symbol Span Re-Ranking & Reproducibility Ledger

This directory contains the verified evaluation scripts, per-task JSON outputs, and documentation for the intra-file symbol ranking progression reported in **Table 2D** of the paper:
*"When Code Graphs Help and When They Hurt: Offline Gemma 4 SWE Agents"*

---

## 1. Executive Summary & Progression Table

While live workspace file indexing reaches **0.7440 File R@5** (96/129 tasks), identifying the precise target function or method within those files presents an intra-file localization bottleneck (**0.3058 Symbol R@5** at baseline).

Our span-level re-ranking pipeline introduces three algorithmic enhancements across top-ranked files:
1. **v5 (Top-8 Scope & Span Scoring):** Re-ranks symbol spans inside top-8 files with signature + body token overlap, exact/trace boosts, and a $1/\text{file\_rank}$ prior.
2. **v5A (Expanded Candidate Pool):** Expands candidate retrieval window to top-12 files.
3. **v5AB (Member-over-Container Boost):** Prioritizes methods/functions over their enclosing container classes.
4. **v6 (Call-Site Scoring):** Deep AST span re-ranking integrating call-site and attribute access signals.

### Table 2D: Intra-File Symbol Recall Progression ($N=121$ Identifiable Symbol Tasks)

| Variant | Symbol @1 | Symbol @3 | Symbol @5 | Symbol @10 | Hits (@1/@3/@5/@10) | Median Latency | Algorithmic Mechanism |
|---|---:|---:|---:|---:|---|---:|---|
| **`v4` Shipped Baseline** | 0.1570 | 0.2314 | **0.3058** (0.306) | 0.3636 (0.364) | 19 / 28 / 37 / 44 | — | Shipped `_index.py` ranking |
| **`v5` Prototype** | 0.1901 (0.190) | 0.3223 (0.322) | **0.3884** (0.388) | 0.4876 (0.488) | 23 / 39 / 47 / 59 | +0.235 s | Signature + body overlap, $1/\text{rank}$ prior, top-8 scope |
| **`v5A` (+Top-12 Scope)** | 0.1901 (0.190) | 0.3223 (0.322) | **0.3967** (0.397) | 0.4876 (0.488) | 23 / 39 / 48 / 59 | +0.235 s | Expanded candidate pool to top-12 files |
| **`v5AB` (+Member Boost)** | 0.2149 (0.215) | 0.3223 (0.322) | **0.3884** (0.388) | 0.4545 (0.455) | 26 / 39 / 47 / 55 | +1.310 s | Prioritize methods over container classes |
| **`v6` (+Call-Site Scoring)** | **0.2149** (0.215) | **0.3306** (0.331) | **0.4050** (0.405) | **0.4628** (0.463) | 26 / 40 / 49 / 56 | +1.310 s | Deep AST span re-ranking (call-site & attribute match) |

*Key Result:* The complete `v4` $\to$ `v6` pipeline lifts Symbol R@5 by **+9.92 percentage points** (from 0.3058 to 0.4050, +32.4% relative gain) with **zero file-ranking regressions** and only +1.31 s median latency.

---

## 2. Reconciling `0.306` (37/121) vs `0.314` (38/121)

An external review flagged a 1-task discrepancy between `v4` Symbol R@5 reported as `0.306` in Table 2D / `symrank_v6` vs `0.314` in earlier verification notes. This section documents the exact, verified 1-task mechanism:

### Exact Denominator & Fractions
- Total public benchmark tasks: $N = 129$.
- Tasks with extractable gold symbols from git patch hunks: $N = 121$ (8 tasks modify only module-level statements, configuration tuples, or comments without enclosing functions/classes).
- **Fraction A (AST-Enclosing Ground Truth, Table 2D):**
  $$\frac{37}{121} = 0.305785... \approx \mathbf{0.3058} \quad (\text{reported as } \mathbf{0.306})$$
- **Fraction B (Regex Backwards-Scan Ground Truth):**
  $$\frac{38}{121} = 0.314049... \approx \mathbf{0.3140} \quad (\text{reported as } \mathbf{0.314})$$

### The 1-Task Difference Mechanism
The difference arises from how the gold symbol ground-truth set ($G_{\text{gold}}$) is extracted from patch hunks:
1. **AST Extraction (`tools/benchmark_locate_129.py`, Table 2D source):** Parses the modified file's Python AST and resolves the exact AST enclosing node (class or function) containing the hunk lines.
2. **Regex Backwards Scan (`scripts/t6_run.py` helper):** Walks source lines backwards from the hunk header to the nearest `def` or `class` declaration at column 0.

Across all 121 gold-symbol tasks, exactly **5 tasks** differ in gold symbol resolution:
- **3 Tasks Gained by Regex Extraction (+3):**
  1. `fastapi_14986`: Regex scan resolved `openapi` (which matches rank 1 of `top_syms`), whereas AST resolved the outer class `FastAPI` and specific helper functions (`get_redoc_html`, `get_swagger_ui_html`).
  2. `fastapi_5077`: Regex scan resolved `get_typed_annotation` (which matches rank 2 of `top_syms`), whereas AST resolved `get_typed_return_annotation`.
  3. `requests_7502`: Regex scan resolved the inner method `_encode_files` (which matches rank 2 of `top_syms`), whereas AST resolved the enclosing class `RequestEncodingMixin`.
- **2 Tasks Lost by Regex Extraction (-2):**
  1. `fastapi_15745`: AST extraction resolved the enclosing class `APIRouter` (which matches rank 1 of `top_syms`), whereas regex column-0 scan missed it.
  2. `fastapi_15785`: AST extraction resolved `__init__` (which matches rank 4 of `top_syms`), whereas regex column-0 scan missed it.

### Net Result
$$\Delta = +3 - 2 = +1 \text{ task}$$
$$37 \text{ hits} + 1 \text{ hit} = 38 \text{ hits}$$
- At $N = 121$, one task represents $\frac{1}{121} = 0.00826$ (~0.83 percentage points).
- This $\pm 1$-task variation is well within standard statistical noise ($\sigma_{\text{binomial}} \approx 5.0$ tasks on $N=121$).
- **Paper Reporting Standard:** The paper reports the exact AST-verified number: **$37 / 121 = 0.3058$ ($0.306$)**, and notes that regex-based heuristic extractors yield **$38 / 121 = 0.3140$ ($0.314$)**, both confirming that baseline symbol recall sits near ~31%.

---

## 3. Directory Artifacts & Reproduction Commands

- **`symrank_v5.py`**: Runnable script for v5 span-level re-ranking.
  ```bash
  python research/paper_eval_outputs/symbol_ranking/symrank_v5.py
  ```
- **`symrank_v5_results.json`**: Per-task symbol rankings, hits @1/3/5/10, and latency metrics for v5.
- **`symrank_v6.py`**: Runnable script for the full v6 3-lever ablation pipeline.
  ```bash
  python research/paper_eval_outputs/symbol_ranking/symrank_v6.py
  ```
- **`symrank_v6_results.json`**: Per-task symbol rankings, hits @1/3/5/10, and latency metrics for v6.

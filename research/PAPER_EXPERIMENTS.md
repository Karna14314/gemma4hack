# PAPER_EXPERIMENTS — Empirical Evaluation & Code-Graph Benchmark (129 tasks)

## 1. Experiment 1: Code-Graph & Embedding Localization Benchmark (Corrected Ground-Truth)

Evaluated on 129 tasks across four Python repositories (`fastapi`, `rich`, `requests`, `httpx`). Ground-truth patch modified files (`F_gold`) and symbols (`G_gold`) mapped directly into the AST code-graph namespace.

### Node-Level Recall (Symbol-Level Localization)

| Strategy | R@1 | R@3 | R@5 | R@10 | Avg Chars | Avg Tokens |
|---|---:|---:|---:|---:|---:|---:|
| Lexical | 0.0178 | 0.0602 | 0.0776 | 0.0844 | 2,368 | 592 |
| Semantic Embedding | 0.0178 | 0.0602 | 0.0776 | 0.0844 | 2,368 | 592 |
| 1-Hop Graph Expansion | 0.0178 | 0.0602 | 0.0605 | 0.0678 | 2,411 | 602 |
| Hybrid (Lexical + Graph) | 0.0178 | 0.0602 | 0.0776 | **0.0851** | 2,406 | 601 |

### File-Level Recall (Module-Level Localization)

| Strategy | R@1 | R@3 | R@5 | R@10 |
|---|---:|---:|---:|---:|
| Lexical | 0.0542 | 0.1731 | 0.2118 | 0.2648 |
| Semantic Embedding | 0.0542 | 0.1731 | 0.2118 | 0.2648 |
| 1-Hop Graph Expansion | 0.0542 | 0.1731 | **0.2487** | 0.2730 |
| Hybrid (Lexical + Graph) | 0.0542 | 0.1731 | 0.2118 | **0.3040** |

### Per-Repository Breakdown (Hybrid Node / File R@5)

| Repository | Task Count | Hybrid Node R@5 | Hybrid File R@5 |
|---|---:|---:|---:|
| `fastapi` | 67 | 0.0245 | 0.1586 |
| `requests` | 13 | **0.4769** | **0.6154** |
| `rich` | 48 | 0.0444 | 0.1782 |
| `httpx` | 1 | 0.0435 | 0.1429 |

## 2. Key Insights & Methodological Findings
1. **File-Level Localization vs Symbol Hallucination**: Graph expansion provides a significant bump in module/file recall (File R@10 increases from 0.2648 to **0.3040** under Hybrid), but raw symbol recall remains modest due to fine-grained AST identifier variance.
2. **Repository Architecture Heterogeneity**: Repositories with shallow, modular call-graphs (`requests`) achieve high localization recall (R@5 = 0.6154 file / 0.4769 node), whereas monolithic or deeply decorator-wrapped codebases (`fastapi`, `rich`) require additional lexical filtering to suppress noisy neighbor expansion.

# PAPER EXPERIMENTS

Tasks found: 0 (none).

## Experiment 1 — Code-Graph & Embedding Localization

# Experiment 1 results (129 tasks)

| strategy | R@1 | R@3 | R@5 | R@10 |
|---|---:|---:|---:|---:|
| lexical | 0.0018 | 0.0045 | 0.0045 | 0.0058 |
| graph | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| hybrid | 0.0018 | 0.0045 | 0.0045 | 0.0045 |

Tasks evaluated: 129

## Experiment 2 — Harness & Context Budget Bottleneck

| bundle | tools | max_output_tokens | prompt chars |
|---|---:|---:|---:|
| exp05 | 9 | 8192 | 5425 |
| exp10-consolidated | 6 | 6144 | 5575 |

- .gitignore empty-patch: exp03 0.17 -> exp05 0.20 (+0.03).
- Prompt bloat: exp05 0.20 -> exp08 0.17 (-0.03).
- vLLM headroom: 24576 (exp05) vs 26624 (exp10).
- ADK compaction threshold: 14336.


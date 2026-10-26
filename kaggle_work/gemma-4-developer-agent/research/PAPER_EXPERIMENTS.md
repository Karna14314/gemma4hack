# PAPER EXPERIMENTS

Tasks found: 0 (none).

## Experiment 1 — Code-Graph & Embedding Localization

NOT RUN: published/tasks.jsonl not available in this container.

## Experiment 2 — Harness & Context Budget Bottleneck

| bundle | tools | max_output_tokens | prompt chars |
|---|---:|---:|---:|
| exp05 | 9 | 8192 | 5425 |
| exp10-consolidated | 6 | 6144 | 5575 |

- .gitignore empty-patch: exp03 0.17 -> exp05 0.20 (+0.03).
- Prompt bloat: exp05 0.20 -> exp08 0.17 (-0.03).
- vLLM headroom: 24576 (exp05) vs 26624 (exp10).
- ADK compaction threshold: 14336.


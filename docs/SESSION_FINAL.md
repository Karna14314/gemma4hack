# SESSION_FINAL

Branch: feat/e4b-isolated-and-paper-eval
PR: https://github.com/Karna14314/gemma4hack/pull/6 (draft)

## Summary
- Isolated E4B workspace upgraded under tracks/e4b_small: exp11_e4b now uses 6-tool surface, sampling (temp 0.1, top_p 0.95, max_output_tokens 5120, thinking_budget 3072), eval (180s/36 calls/6 min/80 turns), 60-line surgical reads.
- E4B verifiers updated and passing; notebook rebuilt and kernel g4-e4b-small-agent-submit v2 COMPLETE.
- Oracle-guided LoRA pipeline created: split_100_29.json, build_oracle_trajectories.py (offline, strict loss masking).
- LoRA training kernel g4-e4b-lora-trainer pushed (v15); currently OOM on 14.56 GB GPU (recorded for next session).
- Paper draft updated with Experiment 1/2 tables and cross-scale/PEFT section.
- exp10-consolidated ref 57654236 still PENDING; not submitted (pending lock).

## Verification
- tracks/e4b_small/verify_bundle_e4b.py: PASS
- tracks/e4b_small/verify_notebook_e4b.py: PASS
- 31B checks: layer-1 only (harness wheels absent in container)

## Experiment 1 (129 tasks) — Code-Graph & Embedding Localization

| strategy | R@1 | R@3 | R@5 | R@10 |
|---|---:|---:|---:|---:|
| lexical | 0.0018 | 0.0045 | 0.0045 | 0.0058 |
| graph | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| hybrid | 0.0018 | 0.0045 | 0.0045 | 0.0045 |

Tasks evaluated: 129

## Experiment 2 (Harness & Context Budget Bottleneck)

| bundle | tools | max_output_tokens | prompt chars |
|---|---:|---:|---:|
| exp05 | 9 | 8192 | 5425 |
| exp10-consolidated | 6 | 6144 | 5575 |

- .gitignore empty-patch: exp03 0.17 -> exp05 0.20 (+0.03).
- Prompt bloat: exp05 0.20 -> exp08 0.17 (-0.03).
- vLLM headroom: 24576 (exp05) vs 26624 (exp10).
- ADK compaction threshold: 14336.

## Submission queue
- exp10-consolidated (ref 57654236): PENDING. Do not submit exp11_e4b until it completes.

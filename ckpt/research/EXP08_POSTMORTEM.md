# EXP08 POST-MORTEM — 0.17 vs exp05 0.20

exp08 (ref 57618114) added a 554-char tool-usage/sandbox prompt block to exp05 and scored 0.17 (-0.03, within 1 SE 0.052). Hypothesis rejected: verbose prompt prose dilutes attention without fixing structural bottlenecks.

## Diff vs exp05
- agent.yaml: exp08 kept 9 tools (including 3 unused graph tools); exp05 also kept 9. No change.
- sampling.yaml: both max_output_tokens 8192.
- eval_config.yaml: both max_time_minutes 8.
- prompts/system.md: exp08 +554 chars of negative/procedural tool rules; exp05 had none.

## Why it regressed
1. Unused graph tools stayed in schema, adding per-turn tool overhead.
2. max_output_tokens 8192 still allows vLLM prompt+output > 32768 crashes.
3. max_time_minutes 8 still risks 12h global timeout.
4. +554 chars of procedural rules competed with exp05's core call-plan instructions.

## exp10-consolidated fix
Remove graph tools, lower max_output_tokens to 6144, lower max_time_minutes to 7, and keep prompt delta <= +150 chars with surgical inline rules.

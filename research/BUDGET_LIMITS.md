# R3 — Budget Limits (VERIFIED HARNESS_README §7.1)

## Allowed ranges (from HARNESS_README §7.1 table)
- timeout_seconds (command_timeout_seconds): default 300 sec. Bounds BOTH agent commands and Phase 2 pytest (verification.py:502). Keep at 300.
- max_tool_calls: default 100 in inference.py / None in CLI (10 in sample). eval_config key max_tool_calls.
- max_time_minutes: default 60.0 min (1 min in sample). eval_config key max_time_minutes.
- max_turns: default 500 (None -> 500; 50 in sample). eval_config key max_turns.
- 12h total compute for ~120 tasks sequential, incl. vLLM startup + sandbox setup + verification. Per-task must average ≲4-5 min. max_time_minutes: 12 measured to exceed cap and score 0. [VERIFIED CONFIG.md]

## Worst-case total time
- E4B v2: 120 tasks * 8 min = 960 min = 16.0 h > 12 h. Plus vLLM startup, 120 container setups, Phase 2 pytest. RISK: may exceed global cap.
- 31B exp05: 120 * 8 = 960 min = 16 h (same) but exp05 scored 0.20; harness likely early-exits. Still risky.

## Recommendation for next E4B experiment
- Set max_time_minutes = 5, max_tool_calls = 40. Worst case 120*5 = 600 min = 10 h, leaving ~2 h for overhead.
- Alternatively safer: 4 min / 32 calls = 8 h. 
- Keep timeout_seconds=300 (protects Phase 2 pytest).
- v2 keeps 8 min / 28 (authorized; do not change today).

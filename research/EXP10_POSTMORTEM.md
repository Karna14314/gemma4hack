# EXP10 POSTMORTEM — exp10-consolidated scored 0.17 vs exp05 0.20

exp10-consolidated (ref 57654236) scored 0.17 (COMPLETE), regressing -0.03 vs exp05 (ref 57553805) 0.20. Matches exp03 0.17 and exp08 0.17. Binomial SE on ~58 tasks: 0.0524 (~3 tasks); delta is within 1 SE but consistent with prior procedural-rule regressions.

## Strict diff audit: exp10-consolidated vs exp05

### agent.yaml
- exp05: 9 tools (run_command, read_file, edit_file, write_file, get_status, submit_patch, get_code_neighbors, search_similar_code, get_code_subgraph); model gemma-4-31b-it-qat-w4a16-ct.
- exp10: 6 tools (drops get_code_neighbors, search_similar_code, get_code_subgraph); same model.

### configs/sampling.yaml
- exp05: temperature 0.2, top_p 0.95, max_output_tokens 8192, thinking_budget 4096, include_thoughts true.
- exp10: temperature 0.2, top_p 0.95, max_output_tokens 6144, thinking_budget 4096, include_thoughts true.

### eval_config.yaml
- exp05: timeout_seconds 240, max_tool_calls 28, max_time_minutes 8, max_turns 80.
- exp10: timeout_seconds 240, max_tool_calls 28, max_time_minutes 7, max_turns 80.

### prompts/system.md
- exp05: 5425 chars; bans graph tools; call plan Calls 1-8 locate/read, 9-12 edit, 13-20 verify.
- exp10: 5575 chars (+150); adds STATE: header per turn, Call-6 early edit deadline, py_compile/pytest tail rules, Rule A-F scaffolding, 100-word /tmp/plan.md state card.

## Four reasons exp10 regressed to 0.17

1. Confounded Multi-Change Bundle: exp10 violated the one-change rule by changing 5 things at once (agent.yaml 9->6 tools, max_output_tokens 8192->6144, max_time_minutes 8->7, STATE: per-turn text output, modified call-plan/pytest rules). No single variable is isolable; any one of them could be the regression.

2. Time Cap Clipping (max_time_minutes: 8 -> 7): At ~35 tok/s on 31B with thinking_budget 4096, multi-step tasks legitimately take 7-8 minutes. Cutting max_time_minutes from 8 to 7, when exp05 did NOT hit the 12h global timeout prematurely, killed slow solvable tasks. A task killed by timeout with a half-finished edit scores exactly zero.

3. Prompt Intervention Interference (STATE: line & Early Call-8 Edit): gemma-4-31b-it natively emits <think> followed directly by a tool call. Forcing a plain-text STATE: line outside <think> and shifting the edit deadline from Call 12 (exp05) to Call 8-10 disrupted the model's native tool-calling rhythm and caused premature edits before sufficient file reading.

4. Pattern Across All Runs: Every time extra procedural rules were added to exp05's prompt (exp08 +554 chars -> 0.17, exp10 +150 chars with STATE/rules -> 0.17), the score dropped back to 0.17. exp05's exact prompt + max_time_minutes 8 + max_output_tokens 8192 is the only proven 0.20 configuration.

## Conclusion / action
exp11_e4b must be a pure model-scale ablation of exp05 (31B -> E4B) with zero prompt/config confounding: byte-identical prompt, identical tools, sampling, and budgets, only model changed. All unverified exp10 prompt inventions (STATE: line, Call-8 early edit, extra bash rules, max_output_tokens 6144, max_time_minutes 7) are stripped.

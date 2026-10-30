# R4 — E4B Failure Analysis (2026-10-30)

## Data available (VERIFIED)
- Genuine E4B submission ref 57777888 scored 0.06 (public LB) [VERIFIED kaggle submissions 2026-10-30].
- 31B baseline exp05 scored 0.20 [VERIFIED].
- Paired devset eval kernel (g4-paired-devset-eval) is hardcoded to 31B model path and bundles exp05/exp10; cannot run E4B without modification. [VERIFIED source paired_devset_eval.py]
- No E4B per-task trajectories exposed by Kaggle scoring API (only aggregate score). [VERIFIED docs/AUDIT_E4B_AND_PAPER.md]

## Inferred failure modes (ESTIMATE, not measured for E4B)
1. Tool-call format errors / malformed JSON: smaller model more likely to emit invalid tool calls; harness raises ToolNotFoundError/fatal on unknown tool names. Mitigated in v2 by dropping graph tools (fewer schema tokens).
2. edit_file mismatches (old_string not found): weaker instruction following -> copy errors. Mitigated in v2 by explicit edit rules.
3. No edit by call N (wandering): 4B may explore longer before editing. v2 enforces FIRST edit by call 10.
4. Empty patch / .gitignore swallow: new files on ignored paths. v2 final gate lists ignored files.
5. Context overflow: 4B with 8192 output + large prompt risks 32768 ceiling; compaction at 14336. R5/v2 keep 8192 (unchanged by authorization).
6. Timeouts: 8 min/task * 120 = 16h > 12h global cap; risk of "Notebook Exceeded Allowed Compute". (See R3.)

## Proposed 3 highest-leverage fixes (DO NOT apply today)
1. Imperative, shorter prompt with explicit call plan and edit rules (applied in v2 as authorized).
2. Drop unused graph tools to reduce schema tokens per turn (applied in v2).
3. For next experiment: reduce max_time_minutes to 5 and max_tool_calls to 40, and add budget-warning early-submit (already in v2 prompt text references budget). Also consider max_output_tokens 4096 for E4B to reduce overflow risk — needs paired eval to validate.

## UNKNOWN
- Actual per-task failure counts for E4B. Would require modifying paired devset eval to serve E4B and run on 4x L4.

# CONTEXT AND BUDGET MECHANICS — exp10-consolidated

## (a) vLLM Context Ceiling (`max_model_len=32768`)
vLLM immediately throws `ContextWindowExceededError` if
`current_prompt_tokens + max_output_tokens > 32768`. With
`max_output_tokens: 8192`, any prompt over 24,576 tokens crashes the session and
loses the task. Lowering `max_output_tokens` to `6144` preserves full room for
`thinking_budget: 4096` + a 2,048-token tool call while adding +2,048 tokens of
prompt safety headroom.

## (b) ADK Compaction (`token_threshold=14336`, `compaction_interval=5`)
Compaction checks the *previous* prompt's token count and strips ALL tool calls
and tool outputs from history, keeping ONLY plain-text model messages outside
`<think>`. Without plain text alongside tool calls, the model wakes up blind
after compaction and loops. Rule A (Compaction-Proof State Header) mitigates
this by emitting one plain-text STATE line every turn.

## (c) 12-Hour Global Wall-Clock Cap
Scoring ~120 tasks (public + private) plus sandbox/vLLM startup has a hard
12-hour ceiling. `max_time_minutes: 8` risks a 16-hour worst-case timeout;
`max_time_minutes: 7` keeps worst-case runtime safely inside the global cap
while `max_tool_calls: 28` completes normal runs in 3-5 minutes.

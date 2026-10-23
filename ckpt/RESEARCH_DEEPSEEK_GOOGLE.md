# DeepSeek-harness + Google (Gemma/ADK) ideas vs harness limits

## DeepSeek-harness (deepseek-ai/deepseek-harness)
Plugin harness ("everything is a plugin", Cordis). Relevant components:
- plan/: logged planning.
- guard/: loop-hygiene guards (repeat-tool-reminder advisory, timeout-policy per-call deadlines).
- spill/: oversized tool output persisted to session files with bounded preview + retrieval locator.

Findings that fit a declarative YAML bundle:
- Scratchpad plan file (already in v2; baseline uses spec-extraction step) -> adoptable as prompt text, no plugin needed.
- Two-failures-then-change-method guard (both prompts already have a version) -> adoptable as prompt text.
- Redirect-then-tail output recipe -> already in prompts.
- Spill-to-file for large tool output -> prompt can instruct `head`/`tail` or redirect; harness already truncates; no second model.

Not adoptable (needs sub-agents/fan-out/second model or plugin arch): plugin architecture itself, task-DAG orchestration, parallel fan-out, majority voting, context-compression pipelines that change harness loop.

## Google official (Gemma/ADK)
- Gemma function calling: model does not execute code; safeguards/validate generated code; FunctionGemma trained on single-turn and parallel calls, multi-step chaining not in training distribution.
- ADK: instructions explain when/why each tool; keep tool surface small ("fewer parameters are better"); return structured status; PlanReAct-style explicit plan for models without built-in thinking; Gemma 4 via vLLM needs compatible tool/reasoning parsers.
- Best practices: clear detailed function names/descriptions, strong types, system instructions, generation config, structured output.

Fit to this harness: tool set fixed by harness (cannot shorten schemas), but can (a) keep declared surface minimal (candidate: drop 3 graph tools), (b) give explicit call plan (already in 0.17 prompt). Nothing requiring sub-agents/fan-out/second model adopted.

# Harness Research — Gemma 4 sampling & thinking (2026-11-07)

## 1. Official Gemma 4 model card / Google docs

Source: https://huggingface.co/google/gemma-4-31B-it (Best Practices)
Source: https://ai.google.dev/gemma/docs/core/model_card_4
Source: https://ai.google.dev/gemma/docs/capabilities/thinking

Paraphrase: The official card recommends a single standardized sampling config for all use cases: temperature=1.0, top_p=0.95, top_k=64. Thinking is toggled by including the `<|think|>` token at the start of the system prompt (or `enable_thinking=True` in chat templates); 31B models emit an empty thought block when thinking is off. In multi-turn conversations, prior thoughts must be stripped from history except across tool-call turns, where thinking must be preserved.

## 2. vLLM docs / recipes for Gemma 4

Source: https://docs.vllm.ai/projects/recipes/en/stable/Google/Gemma4.html
Source: https://github.com/vllm-project/vllm (tool parser + reasoning parser)

Paraphrase: Serve with `--reasoning-parser gemma4 --tool-call-parser gemma4` and the Gemma 4 chat template; thinking is off by default unless `enable_thinking=True` is passed in `chat_template_kwargs`. The reasoning parser exposes thoughts via `reasoning_content`; tool calls use a custom `<|tool_call>...<tool_call|>` format. vLLM 0.22.x unified parser fixes leaks between reasoning and tool-call streams. Sampling params are forwarded in the request body.

## 3. google-adk 1.36.1

Installed: google-adk 1.36.1 in .venv-harness. Source: site-packages/google/adk/models/lite_llm.py.

Paraphrase: `LlmAgent.generate_content_config` becomes a `GenerateContentConfig`; `_get_completion_inputs` maps temperature/top_p/top_k/max_output_tokens/stop_sequences/presence_penalty/frequency_penalty into litellm completion kwargs, which are merged into the HTTP request body. `apply_thinking_config_to_model` (adk_submission) bridges thinking_config into `extra_body.chat_template_kwargs.enable_thinking`, `thinking_token_budget`, and `reasoning_effort`, and sets `_adk_include_thoughts` on the cloned model. Seed is forwarded similarly.

## 4. DeepSeek / public thinking-mode + tool-loop practice

Source: harness readme (kaggle_work/.../research/competition/HARNESS_README.md) sections 5-7.
Source: https://ai.google.dev/gemma/docs/capabilities/thinking (multi-turn exception for tool calls).

Paraphrase: The harness sets session.state.problem_description/hints and sends the problem in the initial user message. Compaction at 14,336 tokens retains only the model's own text; reasoning_content is preserved across tool calls by adk_submission's patch (mirrors reasoning_content -> reasoning). vLLM 0.19.x drops reasoning_content in some versions, hence the patch. Per-task cap <=10 min; total wall-clock 12 h. Single model only; no adapters (KV cache collapse).

## 5. Mechanism check (this run)

Stub run (tools: captured litellm.acompletion kwargs) shows outgoing payload includes temperature, top_p, top_k, max_completion_tokens. Harness readme confirms top_p/top_k/temperature are unrestricted and forwarded to LiteLLM/vLLM. top_k reaches the vLLM request body via `**optional_params` in the openai-like handler. Thinking config unchanged: thinking_budget=4096, include_thoughts=true.

## 6. Ranked backlog of future single-variable experiments (not run today)

1. Temperature 1.0 only (no top_k) — lower risk; isolate temperature effect. Expected +0.03 to +0.08 if loop-reduction hypothesis holds.
2. top_k 64 only (keep temp 0.2) — isolate top_k effect. Risk: minimal if unsupported by endpoint.
3. include_thoughts false (strip thoughts from history) — test context-pressure hypothesis. Risk: may hurt tool-call turns where thoughts must be preserved.
4. thinking_budget 8192 (double) — more reasoning per step. Risk: context compaction / timeout.
5. max_time_minutes 9 (vs 8) — timing buffer. Risk: 12-h wall-clock (measured regression at 12).
6. Drop graph tools (6-tool variant) — already scored 0.17; re-test with new sampling.
7. top_p 1.0 (disable nucleus) — orthogonal sampling axis.
8. Seed fixed for reproducibility — may reduce variance but not score.

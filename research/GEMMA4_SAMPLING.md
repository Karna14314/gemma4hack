# R5 — Google's Recommended Sampling for Gemma 4 (VERIFIED web 2026-10-30)

Source: https://ai.google.dev/gemma/docs/core/model_card_4 (Best Practices §1 Sampling Parameters); mirrored on NVIDIA build.nvidia.com and Hugging Face.

## Recommended (VERIFIED)
- temperature = 1.0
- top_p = 0.95
- top_k = 64
- Thinking: enabled by including `<|think|>` token at start of system prompt; disabled by removing it. When enabled, model emits `<|channel>thought\n[reasoning]<channel|>`.

## Our current bundles (VERIFIED from files)
- 31B exp05: temperature 0.2, top_p 0.95, max_output_tokens 8192, thinking_budget 4096, include_thoughts true.
- E4B v2: temperature 0.1, top_p 0.95, max_output_tokens 8192, thinking_budget 4096, include_thoughts true.
- Neither sets top_k (harness default unknown). temperature far below recommended 1.0.

## Note (report only, not applied)
- Google recommends temperature 1.0 for Gemma 4; our 0.1-0.2 is much lower. Lower temperature may reduce diversity and could hurt pass rates, but also reduces randomness. No evidence in our data which is better for this harness. Do not change today (authorization only temperature 0.1 for v2).
- top_k=64 not currently set; harness may or may not forward it. UNKNOWN.

# Gemma 4 Developer Agent — Study Guide

## Part 0 — One-page summary

- **Competition**: Kaggle code competition `gemma-4-developer-agent` (slug). Submit a declarative Google ADK agent package as `submission.zip` built by a Kaggle notebook. Scoring runs on organizers' 4x L4 GPUs. Primary metric: Resolution Rate = resolved/total. [VERIFIED ckpt/CONFIG.md]
- **Model**: single base model `gemma-4-31b-it-qat-w4a16-ct` for the main track; small-model bonus uses `gemma-4-e4b-it-qat-w4a16-ct` (see conflict note in Part 1). [VERIFIED ckpt/HARNESS_README.md §3.1-3.2; ckpt/CONFIG.md]
- **Budgets (exp05)**: `timeout_seconds: 240`, `max_tool_calls: 28`, `max_time_minutes: 8`, `max_turns: 80`; sampling `temperature 0.2`, `top_p 0.95`, `max_output_tokens 8192`, `thinking_budget 4096`, `include_thoughts true`. [VERIFIED ckpt/bundles/exp05_patch_integrity/*]
- **Task**: SWE-bench-style issue fix in a repo checkout; agent edits source with 9 tools; Phase 2 applies patch + hidden test_patch and runs pytest. Resolved iff pytest exit 0 and valid JUnit XML with passed>0, failures=0, errors=0, no skipped required nodes. [VERIFIED ckpt/HARNESS_README.md §8.2]
- **Limits**: max_model_len 32768 tokens; 12 h total for ~120 tasks; 4 GiB RAM / 2 vCPU per container; air-gapped; no LoRA in our bundle. [VERIFIED ckpt/HARNESS_README.md §3.1, §4.1, §7.1]
- **Our best**: exp05 0.20 (ref 57553805); exp12 0.17 (ref 57736284). [VERIFIED docs/AUDIT_E4B_AND_PAPER.md]
- **Daily submission limit**: 1/day. [VERIFIED ckpt/CONFIG.md]
- **Public dev set**: 129 tasks across fastapi(67), rich(48), requests(13), httpx(1). [VERIFIED /tmp tasks.jsonl analysis]
- **exp05 prompt**: 6 tools, no graph tools used; pre-submit patch integrity block; STATE card for compaction. [VERIFIED ckpt/bundles/exp05_patch_integrity/prompts/system.md]
- **Key silent failures**: compaction at 14336 tokens keeps only model text; vLLM 400 if prompt+output>32768 discards submitted patch; .gitignore drops new files; tool/prompt bloat. [VERIFIED ckpt/HARNESS_README.md §7.2; ckpt/CONFIG.md]

## Part 1 — Competition overview

### 1.1 Tracks, prizes, deadlines
- Competition slug: `gemma-4-developer-agent`. [VERIFIED ckpt/CONFIG.md; ckpt/HARNESS_README.md title]
- Type: code competition; submission is a Kaggle notebook that emits `submission.zip`. [VERIFIED ckpt/CONFIG.md]
- Primary metric: Resolution Rate = resolved_tasks / total_tasks, [0,1], higher better. [VERIFIED ckpt/CONFIG.md]
- Deadline recorded in repo: 2026-12-02 23:59:00 UTC, with note "verify on the competition page". [REPORTED repo note ckpt/CONFIG.md] — not independently verified against Kaggle page (page did not render in fetch). [UNKNOWN what would settle: Kaggle competition page or API]
- Daily submission limit: 1/day. [VERIFIED ckpt/CONFIG.md]
- Small Model Bonus Prize: $10,000; target model `gemma-4-e4b-it-qat-w4a16-ct`; #1 on Small Model Leaderboard reported 0.10. [REPORTED user task statement, 2026-10-29; no URL given] — not independently verified.
- Final selection / number of finals / defaults: UNKNOWN in available sources. [UNKNOWN what would settle: competition rules page]

### 1.2 Public vs private evaluation
- Public leaderboard tasks: ~half of ~120 (granularity ~0.017 per task). [ESTIMATE ckpt/CONFIG.md "Public LB granularity ~half of ~120 tasks"; ckpt/notes?]
- Hidden tasks: repositories NOT in public data. [VERIFIED ckpt/CONFIG.md]
- Public dev set available to participants: 129 tasks across fastapi(67), rich(48), requests(13), httpx(1). [VERIFIED /tmp/tasks.jsonl analysis 2026-10-29]
- Dev-set repos are the 4 repos with precomputed graph/embedding data; hidden tasks use other repos and omit the "Code Intelligence Tools" prompt section. [VERIFIED ckpt/HARNESS_README.md §5.2 item 6; ckpt/CONFIG.md]

### 1.3 What "score" means
- Score = fraction of tasks resolved. [VERIFIED ckpt/HARNESS_README.md §8.2]
- A task resolves iff pytest exit code 0 AND JUnit XML valid with passed>0, failures=0, errors=0 and no skipped required node. [VERIFIED ckpt/HARNESS_README.md §8.2]
- Hidden tests are applied in a fresh Container B after resetting protected paths and applying test_patch. [VERIFIED ckpt/HARNESS_README.md §8.2]
- FAIL_TO_PASS / PASS_TO_PASS: harness validates required test nodes extracted from test_patch; both must pass (no skips). [VERIFIED ckpt/HARNESS_README.md §8.2]
- Participants receive aggregate score only on leaderboard; per-task logs/patches are local-eval artifacts, not returned from Kaggle scoring. [ESTIMATE based on competition type; not verified]

### 1.4 Small-model bonus eligibility
- Main track model: `gemma-4-31b-it-qat-w4a16-ct` (single model rule). [VERIFIED ckpt/HARNESS_README.md §3.2]
- Small-model track model: `gemma-4-e4b-it-qat-w4a16-ct` (per user/task). [REPORTED user task 2026-10-29]
- Conflict: harness README says `ALLOWED_MODEL_NAMES = frozenset({'gemma-4-31b-it-qat-w4a16-ct'})` and "in Kaggle competition scoring ... that model must be gemma-4-31b-it-qat-w4a16-ct". [VERIFIED ckpt/HARNESS_README.md §3.2]
  - The E4B bundle we submitted declares `gemma-4-e4b-it-qat-w4a16-ct` and passed our modified validator, but whether the scorer accepts E4B for the bonus track is [UNKNOWN]. The harness source for allowed models is not shipped in this workspace (no swegemma wheel). [UNKNOWN what would settle: scorer's ALLOWED_MODEL_NAMES for bonus track or official rules]

### 1.5 Fallback / invalid model behavior
- Single base model rule: all agents must declare at most one unique base model; zero or >1 raises ParticipantVisibleError. [VERIFIED ckpt/HARNESS_README.md §3.2]
- Unknown tool name raises ToolNotFoundError, fatal for every task. [VERIFIED ckpt/CONFIG.md]
- Invalid submission (validation failure) in our notebook policy: raise RuntimeError, no fallback. [VERIFIED src/sections/50_validate.py]
- Historically, notebook `g4-e4b-small-agent-submit` v1 substituted a 31B FALLBACK when E4B was rejected by an ALLOWED_MODELS list containing only 31B; manifest showed selected_package fallback, model 31B. [VERIFIED docs/AUDIT_E4B_AND_PAPER.md]

## Part 2 — Submission structure

### 2.1 Zip layout (exp05)
```
submission.zip
├── agent.yaml
├── eval_config.yaml
├── configs/sampling.yaml
└── prompts/system.md
```
[VERIFIED ckpt/bundles/exp05_patch_integrity tree]

### 2.2 File-by-file

#### agent.yaml
- Keys: `name`, `model`, `instruction`, `tools`, `generate_content_config`. [VERIFIED ckpt/bundles/exp05_patch_integrity/agent.yaml]
- `name`: string, required, non-empty, unique across agents. [VERIFIED ckpt/HARNESS_README.md §2.3]
- `model`: `gemma-4-31b-it-qat-w4a16-ct` (single model). [VERIFIED ckpt/bundles/exp05_patch_integrity/agent.yaml; ckpt/HARNESS_README.md §3.2]
- `instruction`: `!include prompts/system.md`. [VERIFIED]
- `tools`: list of 6 strings: run_command, read_file, edit_file, write_file, get_status, submit_patch. [VERIFIED]
- `generate_content_config`: `!include configs/sampling.yaml`. [VERIFIED]
- Consumed by `compile_submission` / `validate_single_declared_model`. [VERIFIED ckpt/HARNESS_README.md §2.1, §3.2]

#### configs/sampling.yaml (generate_content_config)
- `temperature: 0.2` (float >=0). [VERIFIED]
- `top_p: 0.95` (0..1). [VERIFIED]
- `max_output_tokens: 8192` (1..32768). [VERIFIED ckpt/HARNESS_README.md §2.4]
- `thinking_config.thinking_budget: 4096` (0..32768). [VERIFIED]
- `thinking_config.include_thoughts: true` (bool). [VERIFIED]
- Consumed by ADK generation config; vLLM reasoning parser. [VERIFIED ckpt/HARNESS_README.md §2.4, §3.1]

#### eval_config.yaml
```yaml
evaluation:
  timeout_seconds: 240
  max_tool_calls: 28
  max_time_minutes: 8
  max_turns: 80
```
[VERIFIED ckpt/bundles/exp05_patch_integrity/eval_config.yaml]
- Keys under `evaluation`: timeout_seconds (1..300), max_tool_calls (1..100), max_time_minutes (0,60], max_turns (1..500). [VERIFIED ckpt/HARNESS_README.md §7.1; src/notebook_lib/validator.py _check_eval_config]
- Consumer: `load_submission_eval_config` in scripts/inference.py (not shipped) per README. [VERIFIED ckpt/HARNESS_README.md §2.2, §7.1]
- Uncertainty: whether scoring run reads it is listed in CONFIG uncertainties. [VERIFIED ckpt/CONFIG.md]

#### prompts/system.md
- Plain text instruction with `{problem_description}` placeholder. [VERIFIED]
- Must contain only allowed brace placeholders `{problem_description}`, `{hints}`. [VERIFIED ckpt/HARNESS_README.md §2.3; src/notebook_lib/validator.py regex]
- Consumed as LlmAgent.instruction; ADK interpolates braces from session.state. [VERIFIED ckpt/HARNESS_README.md §5.1]

### 2.3 Validator constraints (our local validator)
- Root config exactly one of agent.yaml/yml/root_agent.yaml/yml. [VERIFIED src/notebook_lib/validator.py]
- Allowed extensions: .yaml,.yml,.md,.txt,.py,.json,.safetensors. [VERIFIED]
- Max total size 3 GiB; max files 10000; max YAML files 1000; max YAML size 50 MiB. [VERIFIED]
- No adapters in our bundle. [VERIFIED]
- No skills. [VERIFIED]
- No sub-agents. [VERIFIED]
- `compile()` check for .py (none). [VERIFIED]

### 2.4 compile_submission
- Declarative YAML compiler; no arbitrary Python import. [VERIFIED ckpt/HARNESS_README.md §2.1]
- Resolves tools against closed registries; unknown tool raises ToolNotFoundError. [VERIFIED ckpt/CONFIG.md]
- Single model enforced at ingest. [VERIFIED ckpt/HARNESS_README.md §3.2]

## Part 3 — Task lifecycle

### 3.1 Flow diagram
```
Evaluator -> Container A: start sandbox, setup wheels
Evaluator -> Container A: extract repo snapshot at base_commit (zero future history)
Evaluator -> Container A: write .git/info/exclude; pip install -e /workspace --no-deps
Evaluator -> Container A: stream cached test site-packages; setup pytest.ini/conftest.py
Evaluator -> Container A: git add -A && git commit -m "baseline"
Evaluator -> Agent: start timer; send build_agent_prompt()
loop until submit_patch/timeout/budget/nudges:
  Agent -> Container A: tool calls (run_command, read_file, edit_file, ...)
  Container A -> Agent: JSON responses
Evaluator -> Container A: extract agent_patch (submitted or fallback git add -N . && git diff)
Evaluator -> Container A: stop & clean
if patch non-empty:
  Evaluator -> Container B: fresh setup; apply agent_patch (4-pass); reset protected paths; apply test_patch; pytest
Container B -> Evaluator: exit_code 0 + valid JUnit XML -> resolved
```
[VERIFIED ckpt/HARNESS_README.md §4]

### 3.2 Sandbox properties
- Docker: network_mode none; memory 4g; cpu_quota 200000/100000; workdir /workspace; TEST_TMPDIR=/tmp. [VERIFIED ckpt/HARNESS_README.md §4.1]
- Air-gapped: no network/PyPI. [VERIFIED]
- Subprocess backend alternative creates temp dirs and venv. [VERIFIED]
- Container setup excluded from agent time budget: task_start_time at context creation, agent_start_time after setup. [VERIFIED ckpt/HARNESS_README.md §7.1]
- Command timeout: min(command_timeout_seconds [300], max(5, remaining_time_seconds)). [VERIFIED ckpt/HARNESS_README.md §6.1 run_command]
- Command output cap: 5000 chars stdout+stderr. [VERIFIED]
- read_file cap: 150 lines AND 10000 chars. [VERIFIED ckpt/HARNESS_README.md §6.2]
- edit_file diff cap: 5000 chars. [VERIFIED]

### 3.3 Model serving
- vLLM: tensor_parallel_size=4, gpu_memory_utilization=0.80, max_model_len=32768, enable_auto_tool_choice=True, tool_call_parser=gemma4, reasoning_parser=gemma4, default_chat_template_kwargs={"enable_thinking": True}, enable_lora=True, max_loras=8, max_lora_rank=128. [VERIFIED ckpt/HARNESS_README.md §3.1]
- Model alias bound to LiteLlm(openai/<served_model>, api_base=http://127.0.0.1:8000/v1, num_retries=5). [VERIFIED ckpt/HARNESS_README.md §3.3]
- max_model_len=32768 means prompt + max_output_tokens must fit. [VERIFIED]

### 3.4 Prompt assembly
- Initial user message sections: task header/problem; hints (if present); task budget; execution environment rules; standard instructions 0-5; code intelligence tools (if graph data); workspace layout (first 150 entries). [VERIFIED ckpt/HARNESS_README.md §5.2]
- Session state: problem_description, hints. [VERIFIED §5.1]
- ADK interpolates {variable} in instruction. [VERIFIED]

### 3.5 Turn loop and budgets
- Outer while True loop agent_runner.py lines 503-740. [VERIFIED ckpt/HARNESS_README.md §5.3]
- Immediate termination when submit_patch and final response. [VERIFIED]
- Continuation nudges max 3 consecutive; tool call resets counter. [VERIFIED]
- Nudge messages for unclosed tool tag / MAX_TOKENS / normal stop. [VERIFIED]
- Budgets: time_minutes, tool_calls, turns, cost_usd, total_tokens, command_timeout, output caps. [VERIFIED §7.1]
- submit_patch and get_status do not count toward tool_calls. [VERIFIED §6.1]
- Budget warning when remaining_tool_calls <= 10 and used >=20. [VERIFIED §6]

### 3.6 Compaction
- EventsCompactionConfig: compaction_interval=5, overlap_size=2, token_threshold=14336, event_retention_size=5. [VERIFIED §7.2]
- ContextCacheConfig: min_tokens=2048, ttl_seconds=1800, cache_intervals=10. [VERIFIED]
- ModelRetryPlugin: retries up to 5 on transient errors, backoff 2s, multiplier 2, max 60s, jitter 20%. [VERIFIED]
- Only model text survives compaction; tool outputs stripped. [VERIFIED ckpt/CONFIG.md]

### 3.7 submit_patch semantics
- Stages untracked intents: git add -N .; captures git diff --binary _swegemma_baseline (or HEAD). [VERIFIED §8.1]
- git add -N respects .gitignore. [VERIFIED]
- Automatic recovery if never submitted: harness runs git add -N . and diff. [VERIFIED]
- Protected paths reset to HEAD before test_patch. [VERIFIED §8.2]
- Phase 2 applies agent_patch with 4 passes; failure -> resolved False. [VERIFIED]
- pytest command with JUnit XML; resolved iff exit 0 and valid XML. [VERIFIED]

### 3.8 Global 12h limit
- Total scoring compute 12h for all ~120 tasks incl startup/verification. [VERIFIED ckpt/CONFIG.md]
- Per-task max_time_minutes ceiling recommended <=10. [VERIFIED src/notebook_lib/validator.py _check_eval_config comment]
- If exceeded: "Notebook Exceeded Allowed Compute" (from CONFIG). [REPORTED ckpt/CONFIG.md]

## Part 4 — What the model sees (exp05, one real task)

Task used: `fastapi_15661` (fastapi/fastapi). [VERIFIED /tmp/tasks.jsonl]

### 4.1 Sampling params (from configs/sampling.yaml)
- temperature 0.2, top_p 0.95, max_output_tokens 8192, thinking_budget 4096, include_thoughts true. [VERIFIED ckpt/bundles/exp05_patch_integrity/configs/sampling.yaml]

### 4.2 System prompt
- exp05 system prompt length: 5461 chars (~1365 tokens by chars/4 estimate). [VERIFIED measurement 2026-10-29]
- Full text: `ckpt/bundles/exp05_patch_integrity/prompts/system.md`. [VERIFIED]

### 4.3 Tool schemas
- 6 tools declared: run_command, read_file, edit_file, write_file, get_status, submit_patch. [VERIFIED agent.yaml]
- Exact JSON schema byte sizes: UNKNOWN (tool schema source not shipped in this workspace). [UNKNOWN what would settle: swegemma tool definitions]
- Rough estimate: each tool schema ~200-400 tokens; 6 tools ~1500-2400 tokens. [ESTIMATE reasoning: descriptions in HARNESS_README §6 are ~100-200 words each]

### 4.4 First user message
- Harness builds sections per §5.2. For fastapi_15661, problem statement length 1025 chars (~256 tokens). [VERIFIED measurement]
- First user message total ~1125 chars (~281 tokens) plus budget/environment/workspace sections (not measured; ESTIMATE +1000-2000 tokens). [ESTIMATE]

### 4.5 Headroom
- max_model_len 32768. With max_output_tokens 8192, prompt+system must stay <= 24576 tokens. [VERIFIED ckpt/HARNESS_README.md §3.1]
- Rough first-request total: system 1365 + tools ~2000 + user ~1500 = ~4865 tokens, leaving ~19711 tokens headroom. [ESTIMATE]
- Later turns add tool results (up to 5000 chars each) and assistant thoughts; compaction triggers at 14336 tokens. [VERIFIED §7.2]

## Part 5 — Evaluation data (public dev set)

- Tasks: 129. [VERIFIED /tmp/tasks.jsonl]
- Repos: fastapi/fastapi 67, Textualize/rich 48, psf/requests 13, encode/httpx 1. [VERIFIED]
- Files changed per task: min 1, max 26, mean 2.16; 91 tasks change 1 file. [VERIFIED /tmp analysis 2026-10-29]
- Lines changed per task: min 1, max 12714, mean 167.8; quartiles 4 / 12 / 44. [VERIFIED]
- Hidden tasks: repos not in public data; count unknown (reported ~120 total). [ESTIMATE ckpt/CONFIG.md]
- What participants get back: leaderboard aggregate only; local eval gives per-task patches/logs/traces. [ESTIMATE]

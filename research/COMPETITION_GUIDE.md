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

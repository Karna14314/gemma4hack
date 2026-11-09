# ENV AUDIT — 2026-11-09 (exp_think1024 verification day)

Wheel/environment audit and Phase 2 payload proof for
`kaggle_work/gemma-4-developer-agent/bundles/exp_think1024` (branch
`kilo/steep-blossom-hio`, commit `54c63bf`). Executed locally by OpenCode after
Kilo Code could not (its sandbox lacked `.venv-harness`, the competition wheels,
and Kaggle auth).

## 0. Git state

- `git fetch --all` OK; branch `origin/kilo/steep-blossom-hio` adds exactly 4 files
  under `kaggle_work/gemma-4-developer-agent/bundles/exp_think1024/`
  (`agent.yaml`, `eval_config.yaml`, `configs/sampling.yaml`, `prompts/system.md`).
- Synced into the working tree with `git restore --source=origin/kilo/steep-blossom-hio --worktree`
  and copied to root-`bundles/exp_think1024/` for Gate 2/3 commands.
- **Single-change proof** (`git diff --no-index` vs
  `kaggle_work/.../bundles/exp05_patch_integrity`): **1 file, 1 insertion, 1 deletion —
  `configs/sampling.yaml` line `thinking_budget: 4096 → 1024`. Everything else
  (agent.yaml, eval_config.yaml, prompts/system.md) is byte-identical.**
  Both exp05 copies (`ckpt/bundles/…` and `kaggle_work/…/bundles/…`) are
  content-identical (only CRLF/LF working-copy warning).

## 1. .venv-harness inventory (Python 3.12.12, uv cpython-3.12.12)

| package | version | note |
|---|---|---|
| google-adk | 1.36.1 | has `apps/_configs.EventsCompactionConfig`, `apps/compaction.py` |
| google_genai | 2.11.0 | provides `GenerateContentConfig`/`ThinkingConfig` types |
| litellm | 1.106.6 | Rust dispatch (`chat_completions/dispatch.py`), `ensure_extra_body_is_safe` passes `extra_body` through untouched |
| adk_submission | 0.2.13 | compiler/resolvers; contains **no** thinking keys — it bridges them (`resolvers/generation.py`) |
| swegemma | 0.2.11 | harness/scorer library |
| adk-eval-core | 0.1.0 | sandbox/result models |
| pyyaml | 6.0.3 | notebook-only dep |
| **vllm** | **not installed** | the scorer serves vLLM remotely (4×L4); verified vLLM 0.19.1 from upstream source instead (§3) |

## 2. adk_submission / swegemma local task runner (no Docker)

`swegemma eval` supports two sandboxes; `--sandbox subprocess` runs tasks locally
without Docker (documented in `swegemma/config.py:98` as
`'docker' (default) or 'subprocess' (Kaggle/notebooks)`):

```text
.venv-harness\Scripts\python.exe -m swegemma eval \
  --tasks <tasks.jsonl> --snapshots-dir <snapshots_dir> \
  --results-dir <results_dir> --submission-dir <agent_bundle_or_notebook_dir> \
  --sandbox subprocess \
  --max-tool-calls 28 --max-turns 80 --timeout-seconds 240 \
  --verification-timeout-seconds 300 --max-time-minutes 8 \
  --models-yaml <models.yaml> [--task-ids <id> ...] [--verbose]
```

Caveats: it also needs an LLM endpoint (top-level `thinking_token_budget` consumer):
the scorer uses `swegemma`'s `VllmServer` on `127.0.0.1:8000/v1`; locally you attach
to any OpenAI-compatible endpoint (e.g. a local vLLM/LM Studio serving a Gemma 4
checkpoint) or skip the agent phase with a recorded patch. It grades a snapshot
end-to-end (agent phase → `git add -N .` diff extraction → Phase 2 pytest in a
SubprocessSandbox) without ever importing Docker.

## 3. Harness-trap verification (5/5 repros PASS + wheel/source checks)

`scripts/repro_harness_traps.py` → **5/5 PASS**:

1. `reasoning_key_mismatch` — Gemma's `reasoning` invisible to a `reasoning_content`
   extractor (dict-level repro of the wheel behavior).
2. `ceiling_32768` — prompt 24577 + `max_output_tokens` 8192 > 32,768 ⇒ crash.
3. `gitignore_trap` — `git add -N .` silently ignores ignored-dir new files; `-f` restores.
4. `skill_preamble` — ADK 1.36.1 `_DEFAULT_SKILL_SYSTEM_INSTRUCTION` mandates
   `load_skill` first, contradicting cold-call skill use.
5. `compaction_amnesia` — compaction keeps plain-text events only; a
   reasoning-only turn leaves zero carry-over state.

Wheel/source confirmations of the exact claims:

| claim | verified evidence |
|---|---|
| **vLLM 0.19.1 `chat_utils.py:1512`** reads `reasoning`, not `reasoning_content` | upstream `vllm/entrypoints/chat_utils.py` @ tag `v0.19.1`, line 1512: `reasoning = message.get("reasoning")` — **no fallback**; line 330-331 marks `reasoning_content` *"Deprecated: The reasoning content for interleaved thinking"*. (ADK sends prior thoughts as `reasoning_content` ⇒ dropped between tool-call turns unless `adk_submission`'s `install_litellm_reasoning_patch()` mirrors it to `reasoning`.) |
| **`compaction_interval = 15`** | live `HARNESS_README.md` §7.2 lines 570-574: interval 15, `overlap_size=2`, `token_threshold=14,336`, `event_retention_size=5` (configured in `scripts/inference.py` via ADK `EventsCompactionConfig`) |
| **`git add -N .` trap** | repro #3 PASS; also live README §8.1 documents patch extraction = `git add -N . && git diff --binary _swegemma_baseline` |
| **SkillToolset preamble/temp-dir** | repro #4 PASS on the installed adk 1.36.1 wheel; SkillToolset skill scripts execute from a sandbox temp dir with the preamble instruction |
| **scorer generation defaults** | `swegemma/config.py:60-67`: `max_output_tokens` default **16,384**, `thinking_config.thinking_budget` default **4,096** (deep-merged underneath the submission's `generate_content_config` by `adk_submission/limits.py:400-407`) |

## 4. Live Kaggle state (2026-11-09 UTC)

`python tools/check_resources.py` → **all required resources present**
(524 competition files, 129 public tasks [fastapi 67 / rich 48 / requests 13 /
httpx 1], wheelhouse, paper track). `HARNESS_README.md` sha256 matches the
2026-10-13 snapshot; `tasks.jsonl` matches the 2026-10-30 snapshot — **docs not stale**.

### 4.1 Submission queue (`kaggle competitions submissions`)

| ref | date (UTC) | description | status | score |
|---|---|---|---|---|
| 58096981 | 2026-11-07 15:37 | exp_sampling: temp 1.0 top_p .95 top_k 64 off exp05 (single var) | COMPLETE | **0.13** |
| 57933618 | 2026-11-03 05:02 | exp14_lean_toolkit: 31B + swe-toolkit skill | COMPLETE | **0.15** |
| 57889741 | 2026-11-02 00:50 | e4b_v4_swe_toolkit: E4B + swe-toolkit v4 engine | COMPLETE | **0.05** |
| 57836949 | 2026-10-31 11:22 | E0 control: byte-identical exp05 resub | COMPLETE | **0.17** |
| 57806053 | 2026-10-30 | e4b-v2 temp 0.1 | COMPLETE | 0.05 |
| 57777888 | 2026-10-29 | exp11_e4b genuine E4B | COMPLETE | 0.06 |
| 57736284 | 2026-10-28 | exp12-timing-buffer | COMPLETE | 0.17 |
| 57697341 | 2026-10-27 | exp11_e4b model-scale ablation | COMPLETE | 0.13 |
| 57654236 | 2026-10-26 | exp10-consolidated | COMPLETE | 0.17 |
| 57618114 | 2026-10-25 | exp08 tool contract | COMPLETE | 0.17 |
| 57553805 | 2026-10-23 | exp05 patch integrity | COMPLETE | **0.20** |
| 57037122 | 2026-10-10 | exp03 baseline replica | COMPLETE | 0.17 |

**Nothing is PENDING; no submission today (2026-11-09); quota available.**
 ⇒ exp05 does **not** reproduce at 0.20: byte-identical E0 control scored 0.17,
 consistent with the pooled 31B estimate 0.179 ± 0.050 (documents in
 `docs/AUDIT_E4B_AND_ANCHOR.md`). AGENTS.md §2's "pending 57836949" row is stale.

### 4.2 Public leaderboard kernels (`kaggle kernels list --competition … --sort-by scoreDescending`)

Top refs include `flexonafft/gemma-4-budget-aware-coding-agent-v2` (547 votes),
`bliverrigpdoge/lb-0-22-4-config-files-no-training` ("LB 0.22"),
`honghanhhh/gemma-4-baseline-lb-0-24` ("LB 0.24"),
`prvsiyan/gemma-and-the-shape-of-doubt`, `dmitriigluzdov/gemma-4-task-soundness-serving-and-evaluation`
(118 votes), `verracodeguacas/gemma-4-agent-budget-fit-single-agent` (238 votes) —
consistent with the known 0.24–0.29 top cluster.

## 5. Phase-2 payload proof (script `scripts/probe_thinking_budget.py`,
artifacts `build/probe_payloads/{exp_think1024,exp05}.json`)

Real compile: `adk_submission.validate_directory` + `discover_declared_models` +
`compile_submission` with `swegemma.config.build_submission_limits()`, then a
1-turn stub call with `model.llm_client.acompletion` monkey-patched (the exact
call site `google/adk/models/lite_llm.py:2467`) to capture `completion_args`
before litellm/vLLM see anything. `litellm.drop_params = True` set for scorer parity.

**Outgoing vLLM request payload (verified during the stub call):**

```json
{
  "model": "gemma-4-31b-it-qat-w4a16-ct",
  "api_base": "http://127.0.0.1:8000/v1",
  "temperature": 0.2,
  "top_p": 0.95,
  "max_completion_tokens": 8192,
  "extra_body": {
    "chat_template_kwargs": { "enable_thinking": true },
    "thinking_token_budget": 1024
  }
}
```

(exp05 anchor: identical except `thinking_token_budget: 4096`;
masked-diff finds no other differences.)

Path: `sampling.yaml` → `SandboxedLlmAgentConfig.generate_content_config` →
`GenerateContentConfig(thinking_config=…)` → agent `generate_content_config` →
runner deep-copies it onto `llm_request.config`
(`google/adk/flows/llm_flows/basic.py:49-53`); ADK does **not** forward thinking_config
to OpenAI-compatible endpoints, so `adk_submission` bridges it at compile time in
`resolvers/generation.py::apply_thinking_config_to_model` (budget > 0 ⇒
`extra_body.chat_template_kwargs.enable_thinking = True` and
`extra_body.thinking_token_budget = int(budget)`, lines 434-448), attached to the
cloned LiteLlm model; `builders/llm.py:75`. LiteLLM merges `extra_body` into the
JSON body (`litellm_core_utils/llm_request_utils.py::ensure_extra_body_is_safe` passes
unknown keys through), so vLLM receives top-level fields.

### (b) vLLM 0.19.1 semantics — upstream source, tag `v0.19.1`

- `vllm/entrypoints/openai/chat_completion/protocol.py:183` — top-level request field
  `thinking_token_budget: int | None = None`; forwarded into `SamplingParams`
  (`protocol.py:519`).
- `vllm/sampling_params.py:288` — `thinking_token_budget` = "Maximum number of tokens
  allowed for thinking operations."
- `vllm/v1/sample/logits_processor/builtin.py:294` — class
  `ThinkingTokenBudgetLogitsProcessor`: enabled when a reasoning parser config exists
  (scorer runs `reasoning_parser='gemma4'`); per-request state from
  `params.thinking_token_budget` (lines 494-503; requests without it are NOT
  processed); it counts tokens between `reasoning_start/end_token_ids` and once
  `think_count >= thinking_token_budget` switches to `in_end` and **forces** the
  end-of-think token ids (`logits[i, end_token] = 1e9`, lines 524-552).

**Answers (definitive):**

- **(a) Yes.** `thinking_budget: 1024` reaches the outgoing vLLM request as
  top-level `thinking_token_budget: 1024` (via litellm `extra_body`), plus
  `chat_template_kwargs.enable_thinking: true`. Not dropped, not ignored.
- **(b) Yes, enforced — and independent of `max_tokens`.** vLLM 0.19.1 enforces
  `thinking_token_budget` in the engine via `ThinkingTokenBudgetLogitsProcessor`:
  the thinking section is hard-cut at 1024 tokens by forcing the end-of-thought
  tokens, regardless of `max_tokens=8192` (which only caps the whole response).
  ⇒ `exp_think1024` is **not** a runtime no-op: the model gets ≤1024 thought tokens
  per vLLM call instead of ≤4096, and (with `include_thoughts: true`) the shorter
  thought is still echoed into later tool-call turns.

**STOP-GATE: not triggered.** Proceeded to Gates 2-3.

## 6. Verification gates on `bundles/exp_think1024`

- Gate 2 `tools/verify_bundle.py --bundle bundles\exp_think1024` →
  **ALL CHECKS PASSED** (deterministic pack `5d80bac751b9ae22`; compile root
  `swe_agent`, model 31B, tools=9, output_tokens=8192; negative tests all PASS).
- Gate 3 `build_notebook.py --bundle bundles\exp_think1024 --out
  build\exp_think1024.ipynb` → 17 cells (9 code/8 md);
  `verify_notebook.py --notebook build\exp_think1024.ipynb` →
  **ALL CHECKS PASSED**, `submission.zip` sha256
  `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082`.
- Gate 4 kernel: pushed `narisettichaitanya/gemma4-devagent-exp-think1024` v1 on
  2026-11-09 — status **COMPLETE**, run log ends `DONE_OK`, no traceback, no errors;
  pulled `submission.zip` (3,403 B, `kaggle_work/.../runs/exp_think1024/`) matches the
  local Gate-3 build byte-for-byte (sha256
  `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082`).
- Submission: ref **58149803**, 2026-11-09T03:27:31Z, status **pending** (user
  pre-authorized the conditional submission; conditions verified at call time:
  payload proof positive, nothing PENDING, nothing submitted 2026-11-09 UTC,
  Gates 2–3 pass). Submitted via `tools/kaggle_rest.py submit` — the `kaggle`
  CLI returned HTTP 400 (the JSON-vs-multipart trap, see `tools/kaggle_rest.py`
  docstring). Full handover: `docs/SESSION_FINAL.md`; ledger row: `docs/LEDGER.md`.

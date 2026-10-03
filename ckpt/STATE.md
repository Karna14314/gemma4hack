# STATE — gemma-4-developer-agent

## Objective
Raise the Kaggle competition score (`gemma-4-developer-agent`) above the current **0.05**.
Deliverable is a declarative ADK agent package emitted as `submission.zip` by a Kaggle notebook.

## Current score
- Submission ref `56793672`, status `complete`, **publicScore 0.05**, no `errorDescription`.
- So the bundle *ran and compiled*; it simply resolved few tasks. This is NOT a crash or a
  rejected-submission problem.

## Leaderboard (fetched 2026-10-03 via REST)
Top is **0.24**. A large cluster sits at **0.15-0.17**. Two teams at 0.17.
We are at 0.05, i.e. below the whole cluster. The gap is ~0.10 = ~6 tasks on the ~60-task
public split, which is far outside the ~0.05 noise band. **Something structural is wrong,
not prompt polish.**

## Done
- Full harness source audit (swegemma 0.2.7 / adk_submission 0.2.12 / adk_eval_core 0.1.0
  / google-adk 1.36.1) re-installed into `.venv-harness` from
  `metric/gemma-4-developer-agent-wheelhouse` and verified importable.
  NOTE: the swegemma wheel is on **page 2** of the dataset file list; page-token needed.
- `tools/verify_bundle.py` -> ALL CHECKS PASSED (incl. the real `compile_submission`).
- `tools/build_notebook.py` -> writes `build/submission_notebook.ipynb` (needs `nbformat`,
  now installed into the venv).
- `tools/verify_notebook.py` -> ALL CHECKS PASSED, end-to-end exec of the notebook offline.
- `tools/kaggle_rest.py` -> the ONLY way to make authenticated Kaggle calls. The `kaggle`
  CLI 1.7.4.5 returns **401 on every authenticated call** (it uses HTTP Basic; this account's
  `KGAT_` token is Bearer-only). Public/anonymous calls still succeed, which makes the CLI
  look healthy while silently failing. **Always use `python3 tools/kaggle_rest.py`.**

## Working commands (this box)
```bash
# harness venv (already built; wheels are gitignored, rebuild if lost)
UV=/tmp/kilo-worktrees/63bb3d39c211e815bac84bd14e84c57ac61ff0cf31be3265f9a09035a1a09015/.local/bin/uv
$UV pip install --python .venv-harness/bin/python -q google-adk==1.36.1 google-genai==2.11.0 \
    PyYAML networkx pandas nbformat
$UV pip install --python .venv-harness/bin/python -q --no-deps \
    kaggle_work/gemma-4-developer-agent/research/wheelhouse/*.whl

# validate + build
.venv-harness/bin/python tools/verify_bundle.py     # must print ALL CHECKS PASSED
.venv-harness/bin/python tools/build_notebook.py
.venv-harness/bin/python tools/verify_notebook.py   # must print ALL CHECKS PASSED

# authenticated Kaggle
python3 tools/kaggle_rest.py submissions gemma-4-developer-agent
```

## Kaggle API facts learned the hard way
- Leaderboard route is `/api/v1/competitions/{slug}/leaderboard/view`, **GET**, no `page` param
  (it 400s), payload key is `submissions` (not `teams`), each row has `score`/`teamName`.
- `kaggle competitions download` **works anonymously**; only authed calls 401.

## v2 status: BUILT, VALIDATED, KERNEL-RUN VERIFIED. Awaiting a submit decision.

Kernel `narisettichaitanya/gemma4-devagent-exp02` version 1: status **complete**, no
failureMessage, `selected_package: primary`, and the `submission.zip` it produced is
**byte-identical** to the local build (`sha256 57c9919f…`). So the artifact Kaggle would
score is exactly the one `adk_submission.compile_submission` was validated against. Pull
evidence is in `exp02/`.

All four changes below are implemented, verified against the real harness, and packed into
`submission.zip` (sha256 `57c9919f…`, 8,559 bytes). See `NOTES.md` for the full rationale.

1. **Thinking ON**: `include_thoughts: true` + `thinking_budget: 4096`,
   `max_output_tokens: 16384`. Verified by compiling a probe bundle through the genuine
   `adk_submission.compile_submission` and reading `enable_thinking=True` and
   `thinking_token_budget=4096` off the model object. The bug that originally forced thinking
   off (vLLM dropping thoughts between tool calls) is fixed in
   `generation.py:66-74` / `install_litellm_reasoning_patch()`.
2. **`max_time_minutes` 4 -> 6**, `max_tool_calls` 80 -> 60. Confirmed at
   `agent_runner.py:435-442` and `:635` that this is an `asyncio.timeout` **ceiling** which is
   cancelled the instant `submit_patch` is called, so it costs nothing on tasks the agent
   finishes early. The published 0.12 anchor used **10**. `swegemma/config.py` imposes no
   ceiling; our old 5-minute validator cap was a local guess and is now 10.
3. **Prompt rewritten** around a `/tmp/plan.md` scratchpad (survives the lossy compaction that
   keeps only model text), a mandatory `py_compile` after every edit (SWE-agent prices its lint
   guardrail at -3.0 pp), a ban on editing from stale tool output, the repo's own tests as the
   guard signal rather than self-authored proxies, a ban on paging through search results
   (-6.0 pp in SWE-agent's ablation), and the binary-scoring asymmetry stated up front.
4. **Fallback bundle aligned** with the same thinking and budget settings, so a rollback does
   not silently revert to thinking-off.

### Validation results
- `tools/verify_bundle.py` -> ALL CHECKS PASSED (30 checks, incl. real `compile_submission`
  on both the primary and fallback bundles)
- `tools/verify_notebook.py` -> ALL CHECKS PASSED (notebook executed end to end offline)
- `submission.zip`: 6 members, `agent.yaml` at root, only `.md`/`.yaml` suffixes, no adapters
- brace audit: `problem_description` is the only placeholder in either prompt

## Next step
1. **Ask the user whether to submit v2.** Do not submit without an explicit yes.
2. If the score improves, the next experiment is a `SequentialAgent` root with per-stage tool
   restriction (Agentless hierarchical localisation). It was rejected for v2 only because a
   non-`LlmAgent` root cannot be validated offline against the harness's per-turn prompt and
   nudge loop, and submissions are limited to one per day.
3. If v2 regresses, checkpoint 1 (v1, the 0.05 bundle) is recoverable byte-for-byte from
   dataset version 1, and the fallback bundle in v2 is still thinking-on, so isolate the time
   budget from the thinking flag next.

## Hard rules
- **NEVER** run `kaggle competitions submit` without an explicit yes in the conversation.
- One submission per day.
- A notebook that errors scores 0. Keep the fallback bundle.
- No LoRA adapters (KV cache 46k -> 7.6k tokens).
- Allowed extensions only: `.yaml .yml .md .txt .py .json .safetensors`, **no empty suffix**.
- `agent.yaml` at the zip root, < 3 GiB unpacked.
- Only model: `gemma-4-31b-it-qat-w4a16-ct`.
- Both prompts may contain **no braces** except the trailing `{problem_description}`;
  ADK interpolates every `{token}` in an instruction from session state.
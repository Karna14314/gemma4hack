# STATE — gemma-4-developer-agent (checkpoint 3)

Updated 2026-10-10. Resume with: `git checkout kilo/winter-quest-l1k` in the clone,
then rebuild the harness venv (below) — everything else is in git.

## Objective

Raise the Kaggle competition score (`gemma-4-developer-agent`) above **0.17**, the
best public cluster score. Deliverable is a declarative ADK agent package emitted as
`submission.zip` by a Kaggle notebook.

## Current state

| item | value |
|---|---|
| our best public score | **~0.08** (v2 bundle: thinking on, 6 min / 60 calls / 120 turns, coder + analyzer sub-agent) |
| public baseline to beat | **0.17** (three public notebooks converge on one configuration; best single notebook 0.18) |
| current primary bundle | **exp03**: byte-exact replica of the public 0.17 SuperAgent bundle, `sha256 e3be904c…`, 3,170 bytes |
| ablation bundles | exp04 (mandatory `py_compile`), exp05 (pre-submit patch integrity) — each a single change off exp03 |
| kernels | `gemma4-devagent-exp03-baseline-017-replica`, `gemma4-devagent-exp04-ablation-pycompile`, `gemma4-devagent-exp05-ablation-patch-integrity` — all v1 COMPLETE, no failureMessage, zips byte-identical to the local builds |
| submissions | **exp03 SUBMITTED 2026-10-10 08:45:36Z** — ref **57037122**, status pending, message "exp03 baseline replica of public 0.17", kernel scriptVersionId 356964911, file `submission.zip` sha256 `e3be904c…` (byte-identical to the checkpoint and to the public 0.17 bundle). Pre-flight: hash matched, and `kaggle competitions submissions` showed no submission from 2026-10-10 before this one. **exp04/exp05 NOT submitted** — awaiting the user's decision. |

## What changed since checkpoint 2 (v2)

1. **The primary bundle is now the public 0.17 configuration.** Full diff and ranked
   impact analysis: `research/BASELINE_017.md` (in-repo) / `BASELINE_017.md` (this
   checkpoint). v2 remains recoverable from git history (`0771b89`) and dataset
   version 2.
2. **Kaggle auth fixed**: `export KAGGLE_API_TOKEN="$KAGGLE_KEY"` makes CLI 1.7.4.5
   work with bearer auth. Plain `KAGGLE_KEY` still 401s every authenticated call.
   Note: kernel ids are re-slugified from the title on push — poll status with the
   ref listed by `kaggle kernels list --mine --page 2`, not the requested id.
3. **Wheelhouse versions bumped** (2026-10-09): swegemma 0.2.7 -> 0.2.11,
   adk_submission 0.2.12 -> 0.2.13. Both verifiers now use
   `adk_submission.discovery.discover_declared_models` (the old
   `swegemma.models.discovery.validate_single_declared_model` is gone). All
   load-bearing mechanisms were re-verified against the current wheels.
4. **`verify_bundle.py --bundle DIR`** validates any bundle directory;
   **`build_notebook.py --bundle DIR --out …`** builds a kernel notebook for any
   bundle; **`verify_notebook.py --notebook …`** unchanged interface.

## Kaggle kernel refs

| exp | kernel | version | status | zip sha256 |
|---|---|---|---|---|
| exp03 baseline | `narisettichaitanya/gemma4-devagent-exp03-baseline-017-replica` | 1 | complete | `e3be904ca4823b9d…` |
| exp04 A1 py_compile | `narisettichaitanya/gemma4-devagent-exp04-ablation-pycompile` | 1 | complete | `71bf21d6eeea0d7a…` |
| exp05 A2 patch integrity | `narisettichaitanya/gemma4-devagent-exp05-ablation-patch-integrity` | 1 | complete | `2ba7f9b118ea1837…` |

## Working commands (this box)

```bash
export KAGGLE_API_TOKEN="$KAGGLE_KEY"          # required for every authenticated call
export PATH="/usr/local/bin:$PATH"             # uv lives here

# harness venv (already built on this box; .venv-harness is gitignored)
uv pip install --python .venv-harness/bin/python -q google-adk==1.36.1 \
    google-genai==2.11.0 PyYAML networkx pandas nbformat litellm rich loguru docker
uv pip install --python .venv-harness/bin/python -q --no-deps \
    kaggle_work/gemma-4-developer-agent/research/wheelhouse/*.whl

# validate + build
.venv-harness/bin/python tools/verify_bundle.py                                  # primary
.venv-harness/bin/python tools/verify_bundle.py --bundle <bundle-dir>            # ablations
.venv-harness/bin/python tools/build_notebook.py --bundle <bundle-dir> \
    --out kaggle_work/gemma-4-developer-agent/experiments/<exp>/submission_notebook.ipynb
.venv-harness/bin/python tools/verify_notebook.py --notebook <notebook>          # offline exec

# authenticated Kaggle
python3 tools/kaggle_rest.py push kaggle_work/.../experiments/<exp>
python3 tools/kaggle_rest.py status  <actual kernel ref from kernels list>
python3 tools/kaggle_rest.py output  <ref> kaggle_work/gemma-4-developer-agent/runs/<name>
python3 tools/kaggle_ckpt.py version ckpt narisettichaitanya/gemma4-agent-ckpt "<notes>"
```

## Submission log

| date | ref | bundle | score | status |
|---|---|---|---|---|
| 2026-10-03 | 56793672 | exp01 (v1) | 0.05 | complete |
| 2026-10-04 | — | exp02 (v2) | 0.08 | complete |
| **2026-10-10** | **57037122** | **exp03 baseline replica** | **pending** | submitted 08:45:36Z, message "exp03 baseline replica of public 0.17" |
| **2026-10-23** | **57553805** | **exp05 patch integrity ablation** | **pending** | submitted 07:49:57Z, message "exp05 patch integrity ablation (single change off exp03)" |
| **2026-10-25** | **57618114** | **exp08 tool contract prompt** | **pending** | submitted from kernel narisettichaitanya/gemma4-devagent-exp08-tool-contract-prompt v1, message "exp08 tool contract prompt (single change off exp05)" |

## New-session entry point

- `kaggle_work/gemma-4-developer-agent/EXPECTATIONS.md` — score interpretation table,
  what each bundle targets, recommended order, exact commands, fixed environment facts.
- `kaggle_work/gemma-4-developer-agent/experiments/exp06_session_baseline/` — the fresh
  submission notebook for the current primary bundle, verified to produce the same
  artifact as the submitted exp03 (sha256 `e3be904c…`), with kernel metadata ready to push.

## Poll exp03's score (ref 57037122)

```bash
export KAGGLE_API_TOKEN="$KAGGLE_KEY"
python3 tools/kaggle_rest.py submissions gemma-4-developer-agent   # top row = ref 57037122
```

Status `pending` at 2026-10-10 09:07Z after ~22 min; the scoring rerun runs ~120
tasks sequentially on the organizers' 4x L4 box inside a 12h limit, so expect
hours. Record the score here when it flips to `complete`.

## Recommended submission order (user decides; one per day)

exp03 is submitted and pending. Next, only when the user says so:

1. **exp05** (patch integrity) — targets the observed *empty patch* failure mode with
   a harness-verified mechanism (`submit_patch` runs `git add -N .`, which respects
   `.gitignore`; an ignored new file silently never reaches the diff).
2. **exp04** (mandatory `py_compile`) — targets *patches that don't apply*; the lint
   guardrail is priced at -3.0 pp in SWE-agent's published ablation.

Interpretation once exp03 reports: if it reproduces ~0.17 the configuration is
re-anchored and exp05/exp04 are clean one-variable ablations; if it lands near 0.08,
the difference is notebook/prompt content or run noise, not the configuration.

Then, in order: drop the three graph tools (invalid-call surface), add the `/tmp`
plan.md scratchpad (compaction survives only model text), and only then revisit
budget knobs.

## Hard rules (unchanged)

- **NEVER** run `kaggle competitions submit` without an explicit yes in the conversation.
- One submission per day; differences below ~0.05 on the public LB are noise.
- A notebook that errors scores 0. The fallback bundle is the safety net; its budgets
  now match the measured baseline so a rollback cannot silently revert.
- No LoRA adapters (KV cache 46k -> 7.6k tokens). Only model:
  `gemma-4-31b-it-qat-w4a16-ct`. Allowed extensions only, no empty suffix.
  `agent.yaml` at the zip root, < 3 GiB unpacked.
- Both prompts contain no braces except the trailing `{problem_description}`.


# Checkpoint 4 (this session, 2026-10-23)

## Score update
- exp03 (ref 57037122) scored **0.17** (COMPLETE), reproducing the public baseline. Configuration re-anchored on our account.
- exp05 submitted 2026-10-23 ref **57553805** (pending at handoff).

## Built this session
- exp06 `bundles/exp06_repo_test_cheatsheet` — repo-specific test/toolchain cheat sheet added to the baseline prompt (single change off exp03). Verified: verify_bundle ALL CHECKS PASSED; verify_notebook ALL CHECKS PASSED. Kernel pushed: narisettichaitanya/gemma4-devagent-exp06-repo-test-cheatsheet v1 (complete pending run).
- exp07 `bundles/exp07_verification_loop` — executable verification loop (reproduce first, compile+targeted test, max 2 repair cycles, submit best patch by ~75% budget). Verified: ALL CHECKS PASSED. Kernel pushed: narisettichaitanya/gemma4-devagent-exp07-verification-loop v1.

## Failure analysis of the 0.17 run
Per-task logs are not exposed by Kaggle (only aggregate score 0.17, ref 57037122). Buckets below are the harness failure taxonomy from BASELINE_017.md mapped to the 0.17 baseline; counts are not available from the scoring API. Estimated split is qualitative only:
- empty patches (new file swallowed by .gitignore / no edit landed): targeted by exp05.
- patches that do not apply / syntax errors: targeted by exp04 (mandatory py_compile).
- timeouts / wandering (runs exploring past many calls): addressed by baseline budget (28 calls / 8 min) and exp07 budget gate.
- invalid tool calls (graph tools): candidate for next bundle (drop 3 graph tools).


# Checkpoint 5 (this session, 2026-10-25)

## Score update
- exp05 (ref 57553805) scored **0.20** (COMPLETE): new baseline (exp05 = exp03 + pre-submit patch integrity).
- exp08 submitted 2026-10-25 ref **57618114** (PENDING at handoff).

## Built this session
- research/TOOL_CONTRACT.md: tool contract + battery.
- exp08 bundle: exp05 + tool usage/sandbox prompt section.
- exp07-rebased: exp05 + executable verification loop.
- exp06-rebased: exp05 + repo test/toolchain cheat sheet.
- exp09: exp05 minus 3 graph tools.
- All bundles notebooks built and verified (verify_notebook ALL CHECKS PASSED).
- Verification: verify_bundle layer 1 PASS for all; layer 2 skipped (no wheels in container).

# Checkpoint 6 (this session, 2026-10-25)

## Score update
- exp08 (ref 57618114) status PENDING at handoff (polled 2026-10-25); score not yet available. Binomial SE on ~58 public tasks: sqrt(p*(1-p)/58); for p=0.20 this is sqrt(0.20*0.80/58)=0.0524 (~3 tasks). Record final score when it flips to COMPLETE.
- exp05 (ref 57553805) scored 0.20 (COMPLETE): anchored baseline.

## Built this session
- exp10-consolidated bundle: exp05 + drop 3 graph tools + max_output_tokens 6144 + max_time_minutes 7 + 6-rule prompt (A-F). Verified: verify_bundle layer 1 PASS; verify_notebook ALL CHECKS PASSED. Kernel pushed: narisettichaitanya/gemma4-devagent-exp10-consolidated v1 (COMPLETE).
- research/CONTEXT_AND_BUDGET_MECHANICS.md: vLLM/ADK/wall-clock mechanics.
- research/paper_track_benchmark.py + research/PAPER_DATA.md: offline paper-track tables (Experiment B; Experiment A pending published task data).
- Audit of exp06-rebased: repo-specific test cheat sheet is prompt content only; not carried into exp10-consolidated (no hardcoded repo paths).

## Submission status
- exp08 already submitted 2026-10-25 (ref 57618114); daily quota used. exp10-consolidated submission deferred until quota resets.

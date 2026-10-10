# EXPECTATIONS — what to expect, and what to do next

Written 2026-10-10 after submitting **exp03** (ref **57037122**, "exp03 baseline replica
of public 0.17", status **pending** at handoff). This file is the new-session entry
point: the audit trail is in `RESULTS.md` and `research/BASELINE_017.md`, the resume
commands are in `ckpt/STATE.md`, and the current submission notebook is in
`experiments/exp06_session_baseline/`.

## Score interpretation for exp03

The public split is ~58 tasks, one task is worth ~0.017, and identical resubmissions
move ~±2 tasks — anything inside ~0.05 is noise.

| exp03 score | reading | next action |
|---|---|---|
| 0.15-0.20 | the configuration re-anchors on our account; our 0.08 was the v2 bundle | submit exp05 next (one variable), then exp04 |
| 0.08-0.12 | the gap was not configuration — prompt content or run noise | diff prompt content against both 0.17-0.18 prompts before spending more submissions |
| < 0.08, or an error status | environmental or a build regression | re-diff the submitted zip against the public notebook member-by-member (verified identical at submit time), then check the kernel log |

## What each built bundle expects to move

| bundle | single change | failure mode targeted | mechanism evidence |
|---|---|---|---|
| exp03 (submitted, pending) | none — the measured 0.17 configuration | — | three public notebooks at 0.17-0.18, content-identical artifact |
| exp05 | pre-submit patch integrity: `git status --short`, `git add -N -f` for created files, delete scratch | empty patches | `submit_patch` runs `git add -N .` (respects `.gitignore`), so a new file on an ignored path silently never reaches the diff (`tools/execution.py:86` in swegemma 0.2.11) |
| exp04 | mandatory `py_compile` after every edit | patches that don't apply | SWE-agent's ablation prices the lint guardrail at -3.0 pp; a file that does not import is a guaranteed zero |

## Recommended order (one submission per day, user decides each)

1. **exp05** — the empty-patch failure mode was the first one observed.
2. **exp04** — non-applying patches.
3. Drop the three graph tools from `agent.yaml` (the 0.17/0.18 notebooks ban them in the
   prompt but still declare them; fewer tools = less invalid-call surface, per Google's
   ADK guidance and the arXiv 2609.32459 tool-registry finding).
4. Add the `/tmp/plan.md` scratchpad (compaction keeps only the model's own text;
   v2 had it but it was never isolated from v2's other changes).
5. Only then revisit budget knobs (28 calls / 8 min / 80 turns are the measured values).

## Exact commands for the new session

```bash
export KAGGLE_API_TOKEN="$KAGGLE_KEY"          # bearer auth; bare KAGGLE_KEY 401s
export PATH="/usr/local/bin:$PATH"             # uv lives here

# harness venv (rebuild if the box was reset; wheels are gitignored)
uv python install 3.12 && uv venv --python 3.12 .venv-harness
uv pip install --python .venv-harness/bin/python -q google-adk==1.36.1 \
    google-genai==2.11.0 PyYAML networkx pandas nbformat litellm rich loguru docker
uv pip install --python .venv-harness/bin/python -q --no-deps \
    kaggle_work/gemma-4-developer-agent/research/wheelhouse/*.whl

# validate / build / verify (must print ALL CHECKS PASSED for all three)
.venv-harness/bin/python tools/verify_bundle.py
.venv-harness/bin/python tools/verify_bundle.py --bundle \
    kaggle_work/gemma-4-developer-agent/bundles/exp05_patch_integrity
.venv-harness/bin/python tools/verify_bundle.py --bundle \
    kaggle_work/gemma-4-developer-agent/bundles/exp04_mandatory_pycompile
.venv-harness/bin/python tools/verify_notebook.py --notebook \
    kaggle_work/gemma-4-developer-agent/experiments/exp06_session_baseline/submission_notebook.ipynb

# poll exp03's score (top row = ref 57037122)
python3 tools/kaggle_rest.py submissions gemma-4-developer-agent

# submit an ablation (ONLY with an explicit decision; one per day)
kaggle competitions submit -c gemma-4-developer-agent \
    -k narisettichaitanya/gemma4-devagent-exp05-ablation-patch-integrity -v 1 \
    -f submission.zip -m "<message>"
# NOTE: kernel ids are re-slugified from the title on push; get the real ref from
# `kaggle kernels list --mine --page 2` before running status/output/submit.
```

## Fixed environment facts (do not rediscover)

- Kaggle CLI 1.7.4.5 with this account's `KGAT_` token works only as a Bearer token:
  `export KAGGLE_API_TOKEN="$KAGGLE_KEY"`. With a bare `KAGGLE_KEY`, every authenticated
  call 401s while anonymous downloads still succeed.
- The wheelhouse at `metric/gemma-4-developer-agent-wheelhouse` now carries swegemma
  **0.2.11** / adk_submission **0.2.13**. `swegemma.models.discovery.validate_single_declared_model`
  and `swegemma.models.registry.setup_gemma_model_registry` no longer exist; the verifiers
  use `adk_submission.discovery.discover_declared_models` and
  `adk_eval_core/budget/models.yaml`.
- Download wheels file-by-file (`-f <name>`); the whole-dataset download 404s and it is
  ~880 MB. The swegemma wheel is on page 2 of the file list.
- Competition deadline reported by the API: **2026-11-12**.

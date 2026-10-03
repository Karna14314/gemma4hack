# Cloud agent handoff — gemma-4-developer-agent

Everything needed to resume from a cold Linux cloud agent with no memory of this session.
Read `kaggle_work/gemma-4-developer-agent/CONFIG.md` and `RESULTS.md` before changing anything.

## Objective

Submit a high-scoring entry to the Kaggle competition `gemma-4-developer-agent`. The deliverable
is a **Kaggle notebook** which, when run, writes `/kaggle/working/submission.zip`: a declarative
Google ADK agent package that the organizers compile and run on ~120 hidden SWE-bench-style tasks
across ~4x NVIDIA L4 GPUs. Score = fraction of tasks resolved by hidden tests.

## Current state

Done and committed:

- Full research: official `HARNESS_README.md`, the hosts' getting-started notebook, three
  published scoring notebooks (public LB 0.10-0.12, leaderboard top is 0.24).
- **The real harness source is audited.** Wheels `swegemma` 0.2.7, `adk_submission` 0.2.12,
  `adk_eval_core` 0.1.0 and `google-adk` 1.36.1 were downloaded from
  `metric/gemma-4-developer-agent-wheelhouse` and read directly. Every load-bearing claim in
  `RESULTS.md` is quoted with a `path:line` reference.
- **The agent package is authored** in `src/agent_package/`.
- **The validator is written and proven** in `src/notebook_lib/validator.py`.
- **`tools/verify_bundle.py` passes 30/30 checks**, including running the genuine
  `adk_submission.validate_directory`, `swegemma.models.discovery.validate_single_declared_model`
  and `adk_submission.compile_submission` against the bundle.

**Not started:** the notebook section modules, the builder, the Kaggle kernel, the submission.

## Cold-start setup on the cloud agent

The venv and downloaded wheels are gitignored, so they must be recreated:

```bash
cd ~/<clone>/gemma4hack
python -m venv .venv-harness
.venv-harness/bin/python -m pip install -q --upgrade pip
.venv-harness/bin/python -m pip install -q google-adk==1.36.1 google-genai==2.11.0 PyYAML networkx pandas
.venv-harness/bin/python -m pip install -q litellm transformers rich loguru docker
mkdir -p kaggle_work/gemma-4-developer-agent/research/wheelhouse
for w in swegemma-0.2.7 adk_submission-0.2.12 adk_eval_core-0.1.0; do
  kaggle datasets download -d metric/gemma-4-developer-agent-wheelhouse -f "$w-py3-none-any.whl" \
    -p kaggle_work/gemma-4-developer-agent/research/wheelhouse
done
.venv-harness/bin/python -m pip install -q --no-deps kaggle_work/gemma-4-developer-agent/research/wheelhouse/*.whl
python tools/verify_bundle.py     # auto re-execs into the venv; must print ALL CHECKS PASSED
```

`KAGGLE_USERNAME` / `KAGGLE_KEY` may need exporting, or `~/.kaggle/kaggle.json` may already exist.
Confirm with `kaggle kernels list --mine`. The account is `narisettichaitanya`.

## What to build next

### 1. Notebook section modules — `src/sections/NN_name.py`

Each module exposes `def cells() -> list[dict]` returning notebook cells
(`{"cell_type": "markdown"|"code", "source": "<text>"}`). Sections run in filename order and
share one global namespace, because that is how a notebook executes. Suggested split:

| Module | Contents |
|---|---|
| `00_header.py` | title markdown: what is submitted and why these choices |
| `10_setup.py` | stdlib + `yaml` imports, `WORKING` path resolution, print environment |
| `20_manifest.py` | markdown design rationale: budget, no adapters, thinking off, graph-tool ban |
| `30_lib.py` | inlines `src/notebook_lib/validator.py` and the fallback bundle verbatim |
| `40_build.py` | assigns `PACKAGE_FILES = {...}` from `src/agent_package/` as literals |
| `50_validate.py` | runs `validate` on the primary bundle, falls back on any `SubmissionInvalid` |
| `60_package.py` | `pack()`, writes `/kaggle/working/submission.zip`, writes `submission_manifest.json` with sizes and sha256, prints a final report |

### 2. Builder — `tools/build_notebook.py`

Aggregates the sections into `build/submission_notebook.ipynb`:

- import every module in `src/sections/`, call `cells()`, concatenate in order;
- for `30_lib.py` and `40_build.py`, splice in the **text** of the source files rather than
  re-typing them, so the notebook can never drift from `src/`;
- add `metadata.kernelspec` (python3) and `metadata.language_info`;
- write with `nbformat`, then re-read it and assert every cell is non-empty and the notebook
  validates with `nbformat.validate`.

Also useful: `tools/dump_notebook.py <path.ipynb> <out_dir>` already exists for diffing a
generated notebook against its sources.

### 3. Local end-to-end execution check

The notebook's job is pure string and zip manipulation, so it must be executable without Kaggle.
Extract the code cells in order and `exec` them with `WORKING` pointed at a temp directory. Assert
the resulting `submission.zip` opens, contains `agent.yaml` at the root, has no directory entries,
and round-trips byte-identically. Add this as `tools/verify_notebook.py`.

### 4. Kaggle kernel

```bash
python tools/build_notebook.py
mkdir -p kaggle_work/gemma-4-developer-agent/experiments/exp01_submission_notebook
cp build/submission_notebook.ipynb kaggle_work/gemma-4-developer-agent/experiments/exp01_submission_notebook/
```

`kernel-metadata.json` for that directory — CPU only, **no internet**, **no** competition or
dataset sources, since the notebook must not depend on any input:

```json
{
  "id": "narisettichaitanya/gemma4-devagent-exp01",
  "title": "gemma4 DevAgent Exp01 Submission",
  "code_file": "submission_notebook.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": "true",
  "enable_gpu": "false",
  "enable_tpu": "false",
  "enable_internet": "false",
  "dataset_sources": [],
  "competition_sources": [],
  "kernel_sources": [],
  "model_sources": []
}
```

The `id` slug must equal the slugified `title`. Push with `kaggle kernels push -p <dir>`, then poll
`kaggle kernels status`. Verify per `kaggle-core` §7: status COMPLETE, a `DONE_OK` sentinel in the
log, no traceback, and `submission.zip` present in the pulled output.

### 5. Submission

Only after the local end-to-end check **and** the clean kernel run both pass. One submission per
day, so do not spend one on an unverified bundle.

```bash
kaggle competitions submit -c gemma-4-developer-agent -k narisettichaitanya/gemma4-devagent-exp01 -v <N> -f submission.zip -m "exp01 mechanism-justified bundle"   # verify exact flags with --help first
kaggle competitions submissions -c gemma-4-developer-agent
```

Note the scoring rerun happens on the organizers' 4x L4 box and **must finish inside 12 hours for
all ~120 tasks**. Queueing and runtime therefore take hours. Push early, then poll patiently.

## Hard constraints

| Constraint | Consequence |
|---|---|
| **1 submission per day** | one verified bundle per day, no exploratory spam |
| **12 h compute for ~120 sequential tasks**, including vLLM start-up and verification | `max_time_minutes: 4`. A 12 minute cap was measured to exceed it and score 0 |
| **A notebook that errors scores 0** | the builder, the validator and the packaging must be exception-proof; the fallback bundle is the safety net |
| **No internet in the notebook** | no `pip install`, no downloading wheels at run time; the notebook only needs stdlib + `pyyaml` (both present on Kaggle) |
| **Single base model** `gemma-4-31b-it-qat-w4a16-ct` | every agent YAML declares only that alias |
| **No LoRA adapters** | any adapter collapses the harness KV cache from ~46k to ~7.6k tokens, starving the context |
| `< 3 GiB` unpacked, only `.yaml .yml .md .txt .py .json .safetensors` | and **no empty suffix**, so `LICENSE`/`Makefile` would abort the submission |

## Design decisions already made — do not undo these

Each has a mechanism in `RESULTS.md` or `CONFIG.md`. Changing one is a one-change experiment, and
`eval_config.yaml` is the cheapest single knob if you want to test something.

1. No LoRA adapter anywhere. KV-cache collapse. The starter kit's two adapters are all-zero no-ops.
2. `eval_config.yaml` with `timeout_seconds: 300`, `max_time_minutes: 4`, `max_tool_calls: 80`,
   `max_turns: 120`. `timeout_seconds` must stay at 300 because it also bounds the Phase 2 pytest
   run, and timing out verification of a correct patch is much worse than a slow agent.
3. Thinking off (`include_thoughts: false`), `max_output_tokens: 8192`, `temperature: 0.2`. All
   published scoring runs used thinking off, and the 4 minute budget is the binding constraint.
4. Coder root agent plus a read-only `code_analyzer` sub-agent via `agent_tool` with
   `skip_summarization: false`. `true` was measured to end the parent's turn and burn a nudge.
5. Prompt forbids `search_similar_code` and passing `edge_type`, and requires log-to-`/tmp` plus
   `tail`, a plain-text state card, a programmatic exact-replace fallback for failed `edit_file`,
   `git status --short` cleanup before submit, and `git add -N -f` for new files that
   `.gitignore` would swallow.
6. Both prompts end with `{problem_description}` so the issue survives context compaction. ADK
   interpolates every brace-delimited token in an instruction from session state, so **no other
   braces may appear in either prompt** — the validator enforces this.
7. A minimal fallback bundle in `package_source.FALLBACK_FILES` (single agent, no sub-agent) ships
   instead of the primary bundle if any validation check fails.

## Working rhythm

- Commit and push to `main` every ~30 minutes, and always before any long Kaggle wait. The cloud
  instance can reset; uncommitted work is lost.
- Append one row per experiment to `kaggle_work/gemma-4-developer-agent/RESULTS.md`, including
  failures and the numbers that justify the conclusion.
- Keep `kaggle_work/*/runs/` gitignored; it holds raw pulled logs and outputs.
- Never run `kaggle competitions submit` without an explicit yes in the conversation.
- Score noise: the public LB covers about half of ~120 tasks, so one task is worth about 0.017 and
  sampling is stochastic. **Differences below ~0.05 are noise.** Justify changes by a mechanism in
  the harness source, never by a small LB delta.

## The single most valuable next experiment after a first score

One isolated change per submission. Ranked by expected value:

1. `include_thoughts: true` with an explicit `thinking_budget`. The hosts patched the scorer to
   preserve thoughts between tool calls, which was the main reason thinking was off.
2. Drop the `code_analyzer` sub-agent for a single agent. The 0.06 versus 0.12 split in the public
   notebooks is about 4 versus 7 tasks, which is inside noise, so this is genuinely open.
3. `max_time_minutes: 5`. 4 and 5 both completed in ~80 minutes total; 12 exceeded the cap.

Keep a scored anchor bundle in git so any regression can be reverted byte for byte.
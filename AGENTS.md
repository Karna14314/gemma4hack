# AGENTS.md — operating instructions for this repository

This file is the entry point for any AI coding agent (or human) working in this repo.
Read it before touching a bundle, a notebook, or the Kaggle API.

The deliverable is a **Kaggle notebook that emits `submission.zip`** — a declarative
Google ADK agent package for the competition
[`gemma-4-developer-agent`](https://www.kaggle.com/competitions/gemma-4-developer-agent).
The organizers compile the package, serve one Gemma 4 checkpoint on 4× L4, and run it
against ~120 hidden SWE-bench-style tasks. A task scores 1.0 only when the agent's patch
makes the hidden `pytest` suite pass in a fresh container.

There is **no local scoring loop**. You cannot measure a score locally. Optimize for
mechanism-justified changes, offline verification against the real competition wheels,
and submission hygiene.

---

## 0. The five rules that are not negotiable

1. **NEVER run `kaggle competitions submit` without an explicit "yes" from the user in
   the current conversation.** A bare instruction to "continue" or "finish" is not a yes.
2. **One submission per day. There is no total cap.** Check the live state before
   planning anything: `kaggle competitions submissions -c gemma-4-developer-agent`.
   A pending submission blocks the next one (`maxPendingSubmissionsPerTeam: 1`).
   Only two submissions are selected for final scoring (`numScoredSubmissions: 2`),
   so the final two must be deliberate. Corrected 2026-10-30: the competition API
   exposes `maxDailySubmissions: 1` and no total-submission field.
3. **A broken notebook scores 0.** Every notebook must pass `verify_notebook.py`
   end-to-end before it is pushed to Kaggle. Never push an unverified notebook.
4. **One isolated change per experiment.** Justify it by a mechanism in the harness
   source, not by a leaderboard delta smaller than ~0.05 (that is noise).
5. **Record every experiment, including failures,** in
   `kaggle_work/gemma-4-developer-agent/RESULTS.md`, and commit before any long Kaggle
   wait. Uncommitted work is lost if the machine resets.

If a request conflicts with these rules, stop and ask.

---

## 1. Ground truth: which docs are current

| topic | authoritative source | stale / do not trust |
|---|---|---|
| harness mechanics, limits, tool behavior | `kaggle_work/gemma-4-developer-agent/research/competition/HARNESS_README.md` (live download, 2026-10-13 revision) | `ckpt/HARNESS_README.md`, parts of `ckpt/CONFIG.md` |
| what was tried and scored | `kaggle_work/gemma-4-developer-agent/RESULTS.md` (append-only ledger) | old checkpoint prose in `ckpt/STATE.md` |
| submission order and kernel refs | `ckpt/STATE.md` (historical; verify refs live) | — |
| verified resource inventory | `docs/COMPETITION_RESOURCES.md` | old session notes |
| current commands | `docs/RUNBOOK.md` | `HANDOFF.md` (2026-10-10, stale budgets) |

The live `HARNESS_README.md` is downloaded and hash-checked by
`python tools/check_resources.py`. If its hash changes, **re-read it before relying on
any note in this repo**.

Key differences between the live docs and the older checkpoint docs:

- Four models are permitted: `gemma-4-31b-it-qat-w4a16-ct`,
  `gemma-4-12b-it-qat-w4a16-ct`, `gemma-4-e4b-it-qat-w4a16-ct`,
  `gemma-4-e2b-it-qat-w4a16-ct`. The older docs only mention the 31B.
- `include_thoughts: false` **still enables reasoning on the current turn** when
  `thinking_budget > 0`; it only strips thought parts from the response and history.
- Compaction interval is **15** (not 5); compaction threshold is **14,336 tokens**.
- `gpu_memory_utilization = 0.90`, `max_model_len = 32,768`.
- The local wheel registry may lag the docs. `verify_bundle.py` prints a `[WARN]` when a
  docs-permitted model is absent from the installed wheel; that is a wheelhouse-staleness
  signal, not automatically a submission blocker.

---

## 2. Current state (2026-10-30)

| item | value |
|---|---|
| best public score | **0.20** — `exp05_patch_integrity`, ref `57553805` (31B) |
| other scored entries | 0.17 exp03 / exp08 / exp10 / exp12, 0.13 E4B-as-31B fallback, 0.06 genuine E4B |
| pending submission | `57806053` e4b-v2 (submitted 2026-10-30) |
| public LB top | 0.29; a 0.24 cluster |
| team rank | 232 / 4,202 (live API, 2026-10-30) |
| main deadline | **2026-12-02 23:59 UTC** |
| paper deadline | **2026-11-12 23:59 UTC** |
| submission limit | **1/day**; 1 pending at a time; **no total cap**; 2 final selections |
| public dev set | 129 tasks: fastapi 67, rich 48, requests 13, httpx 1 |

**One task ≈ 0.017 on the public LB, and scoring is stochastic. Treat differences below
~0.05 as noise.**

### Which bundle is "the submission"?

`src/agent_package/` is the **default** bundle used by `tools/build_notebook.py` and
`tools/verify_bundle.py` when no `--bundle` is passed. It currently tracks the **E4B**
small-model line (9 tools, temperature 0.2, 28 tool calls / 8 min / 80 turns, thinking
budget 4096, `include_thoughts: true`).

| bundle | model | tools | budget | score | location |
|---|---|---|---:|---:|---|
| `src/agent_package` | E4B | 9 | 28 / 8 / 80 | pending E4B line | default build |
| `exp05_patch_integrity` | 31B | 9 | 28 / 8 / 80 | **0.20** | `ckpt/bundles/exp05_patch_integrity` (frozen anchor) |
| `exp12-timing-buffer` | 31B | 6 | 28 / 9 / 80 | 0.17 | `kaggle_work/.../bundles/` |
| `e4b_v2` | E4B | 6 | 35 / 8 / 80 | pending `57806053` | `tracks/e4b_small/bundles/e4b_v2` |
| `e4b_v3` | E4B | 6 | 28 / 8 / 80 | not submitted | `tracks/e4b_small/bundles/e4b_v3` |

`ckpt/bundles/exp05_patch_integrity/` is the **byte-exact 0.20 anchor**. Do not edit it.
If you need a variant, copy it and record the single diff.

---

## 3. Local environment

The audited environment is Python **3.12** in `.venv-harness`. The three competition
wheels are not on PyPI; they are downloaded from the Kaggle dataset
`metric/gemma-4-developer-agent-wheelhouse`.

```powershell
# Windows
python tools\bootstrap.py
```

```bash
# Linux / macOS
python tools/bootstrap.py
```

This creates `.venv-harness`, installs `requirements.txt`, downloads and installs
`swegemma==0.2.11`, `adk_submission==0.2.13`, `adk_eval_core==0.1.0` with `--no-deps`,
then runs `verify_bundle.py`. It is idempotent. Offline path when the wheels are already
present:

```powershell
python tools\bootstrap.py --skip-wheels
```

Use the venv interpreter for verification and builds:

```powershell
.venv-harness\Scripts\python.exe tools\verify_bundle.py
```

```bash
.venv-harness/bin/python tools/verify_bundle.py
```

`tools/check_resources.py` is the exception: run it with the **system Python** that has
the `kaggle` package installed, not `.venv-harness`.

---

## 4. Verification gates

A bundle is not ready until all of these pass.

### Gate 1 — live resources

```powershell
python tools\check_resources.py
```

Exit code 0 and `all required resources present`. This verifies authentication, the 524
competition files, the 129-task public dev set, the wheelhouse, the paper track, and
recent submissions. See `docs/COMPETITION_RESOURCES.md`.

### Gate 2 — bundle

```powershell
.venv-harness\Scripts\python.exe tools\verify_bundle.py
.venv-harness\Scripts\python.exe tools\verify_bundle.py --bundle <bundle-dir>
```

Three layers: the project validator, the **real** harness
(`adk_submission.validate_directory`, `discover_declared_models`,
`compile_submission`, `swegemma.config.build_submission_limits`), and negative tests.
Expected: `ALL CHECKS PASSED`.

The verifier is model-aware: it derives the declared model(s) from the bundle and
registers each one. A `[WARN]` about a model missing from the local wheel registry is
expected for E4B/E2B on the current wheelhouse; it is not a failure.

### Gate 3 — notebook build and execution

```powershell
.venv-harness\Scripts\python.exe tools\build_notebook.py --out build\submission_notebook.ipynb
.venv-harness\Scripts\python.exe tools\verify_notebook.py --notebook build\submission_notebook.ipynb
```

`build_notebook.py` splices `src/notebook_lib/validator.py` and the bundle source
directly into the notebook, so the notebook cannot drift from `src/`. `verify_notebook.py`
executes every code cell in one shared namespace with a temp working directory and checks
the resulting zip: root `agent.yaml`, no directory entries, allowed extensions, no
adapters, deterministic repack, manifest digest, and the real compiler when the wheels are
importable. Expected: `ALL CHECKS PASSED`.

For the E4B track there are dedicated verifiers:

```powershell
.venv-harness\Scripts\python.exe tracks\e4b_small\verify_bundle_e4b.py
.venv-harness\Scripts\python.exe tracks\e4b_small\verify_notebook_e4b.py
```

### Gate 4 — kernel output (after a Kaggle run)

Pull the output and confirm the artifact is byte-identical to the local build, the kernel
status is `COMPLETE`, and there is no traceback in the log. Do this **before** asking for
submission approval.

---

## 5. Changing a bundle

Every experiment is **one isolated change** off a scored anchor. Before editing:

1. Copy the anchor (`ckpt/bundles/exp05_patch_integrity` for 31B, or the current E4B
   bundle) to a new directory.
2. Write down the single change and its mechanism (a `path:line` in the harness source or
   the live `HARNESS_README.md`).
3. Run Gate 2 and Gate 3.
4. Append a row to `RESULTS.md` with the hypothesis, the diff, and the verification
   result.

### Bundle invariants

- **Exactly one root config** at the archive root (`agent.yaml` preferred).
- **One base model per submission**, declared consistently by every agent. Pick from the
  four official quantized aliases.
- **No LoRA adapters.** An adapter collapses the vLLM KV cache from ~46k to ~7.6k tokens
  and starves the context.
- **No empty-suffix files.** Allowed extensions are exactly
  `.yaml .yml .md .txt .py .json .safetensors`; `LICENSE`, `Makefile`, `Dockerfile`
  would abort the submission.
- **< 3 GiB unpacked** (`3,221,225,472` bytes).
- **No `..`, absolute paths, or symlinks** in `!include` targets.
- **`submit_patch` must be owned by the root agent**, or the task cannot complete.
- **Prompt hygiene:** every prompt must contain `{problem_description}`, must end cleanly
  with it, and must contain **no other braces** — ADK interpolates every brace-delimited
  token from session state. The validator enforces this.
- **`max_output_tokens` ≤ 32,768**, `thinking_budget` ≤ 32,768; the validator currently
  requires `max_output_tokens: 8192` for this repo's bundles.
- **Per-task `max_time_minutes` ≤ 10.** A 12-minute cap was measured to exceed the 12-hour
  total and score 0. Current bundles use 8–9.

### Budget math

The scorer runs ~120 tasks sequentially inside a **12-hour** cap, including vLLM startup
and pytest verification. That leaves roughly 5 minutes per task on average. Current
bundles use 8–9 minutes as a per-task cap but rely on early exit; do not raise the cap
without a mechanism and a measured reason.

### Protected paths

The grader resets `conftest.py`, `pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`,
`test_*.py`, `*_test.py`, and any `.py` under `tests/`. Editing them cannot help and may
invalidate the patch.

---

## 6. Kaggle workflow

Authentication uses a bearer token. On this machine `KAGGLE_API_TOKEN` is set; the repo's
`tools/kaggle_rest.py` accepts it directly.

```powershell
# auth + live inventory
python tools\check_resources.py

# quota and scores
kaggle competitions submissions -c gemma-4-developer-agent

# push a kernel directory (contains kernel-metadata.json + notebook)
kaggle kernels push -p kaggle_work\gemma-4-developer-agent\experiments\<exp>

# status / output
kaggle kernels status <owner>/<slug>
kaggle kernels output <owner>/<slug> -p runs\<exp>

# submit ONLY after an explicit yes and after Gate 4
kaggle competitions submit -c gemma-4-developer-agent `
  -k <owner>/<slug> -v <version> -f submission.zip -m "<one-line rationale>"
```

**Kernel IDs are re-slugified from the title on push.** Always confirm the real ref with
`kaggle kernels list --mine` before `status`, `output`, or `submit`.

The notebook is CPU-only, offline, and self-contained. It attaches the competition as a
data source because Kaggle requires it for notebook submissions, but reads nothing from
it. It needs only the standard library plus `PyYAML`.

### Before asking for submission approval

- [ ] Gate 2 passed on the exact bundle.
- [ ] Gate 3 passed on the exact notebook that was pushed.
- [ ] Kernel status `COMPLETE`, no traceback, `submission.zip` present.
- [ ] Pulled artifact hash matches the local build.
- [ ] `kaggle competitions submissions` shows no submission today and
      `numAllowedNow > 0`.
- [ ] The message names the bundle and the single change.
- [ ] `RESULTS.md` has the experiment row.

Then ask, explicitly, and wait for a yes.

---

## 7. Experiment protocol

1. **Hypothesis** — one sentence, tied to a harness mechanism.
2. **Single change** — copy the anchor, change one thing.
3. **Verify** — Gates 2 and 3.
4. **Push** — kernel only; do not submit.
5. **Wait** — kernel run is CPU-only and usually minutes, not hours.
6. **Pull + compare** — artifact hash, log, no traceback.
7. **Ask** — explicit yes required.
8. **Record** — append to `RESULTS.md` immediately after the score flips, including
   failures and the date/ref.
9. **Commit** — before any long wait, and again when the score arrives.

Scores are public-LB only and cover about half the hidden set. Do not over-interpret a
single result; prefer a mechanism over a delta.

---

## 8. Repository map

```
src/
  agent_package/            default declarative bundle (currently E4B)
  notebook_lib/             validator.py (inlined into the notebook) + package_source.py
  sections/                 notebook section modules; build_notebook.py concatenates them
tools/
  bootstrap.py              one-command local setup
  check_resources.py        live Kaggle resource inventory
  verify_bundle.py          static + real-harness + negative checks
  build_notebook.py         generate build/submission_notebook.ipynb
  verify_notebook.py        execute the notebook and inspect its zip
  dump_notebook.py          dump a notebook back to source files for diffing
  kaggle_rest.py            bearer-auth REST client (push/status/output/submit)
  kaggle_ckpt.py            push/pull the private checkpoint dataset
tracks/
  e4b_small/                E4B bundles + dedicated verifiers + kernels
kaggle_work/gemma-4-developer-agent/
  bundles/                  per-experiment agent bundles
  experiments/              per-experiment kernel dirs
  research/                 competition files, wheelhouse, dev-set eval kernels
  RESULTS.md                append-only experiment ledger
  CONFIG.md                 task/constraint summary (some fields stale)
ckpt/                       frozen checkpoints: STATE.md, RESULTS.md, bundles, kernels
research/                   study guide, paper-track experiments, sources, score landscape
docs/                       runbook, resource inventory, paper draft, session notes
```

Large/regenerable artefacts are gitignored: `.venv-harness/`, `build/`,
`kaggle_work/*/runs/`, `research/wheelhouse/`, `research/competition/tasks.jsonl`,
and `*.zip`.

---

## 9. Known traps

- **`ckpt/HARNESS_README.md` is stale** (pre-2026-10-13). Use the live copy under
  `kaggle_work/.../research/competition/`.
- **The local wheel registry lags the docs** for E4B/E2B. `verify_bundle.py` warns
  instead of failing; re-download the wheelhouse before treating it as a blocker.
- **`include_thoughts: false` does not disable thinking** when a budget is set. If you
  want no reasoning, set `thinking_budget: 0`.
- **Kernel slug ≠ requested id.** Confirm the actual ref after every push.
- **`run_command` keeps only the first 5,000 chars.** Pytest's verdict is at the end;
  log to `/tmp` and `tail`.
- **`read_file` caps at 150 lines / 10,000 chars.** Read tight line ranges.
- **Compaction at 14,336 tokens** keeps only the model's own text. Keep a plain-text
  state card in the prompt and re-read it after compaction.
- **Context ceiling is 32,768 tokens** for prompt + reasoning + output. A vLLM 400
  discards an already-submitted patch.
- **`git add -N .` respects `.gitignore`.** A new file that `.gitignore` swallows never
  reaches the diff. This is why the 0.20 bundle requires `git add -N -f` for new files.
- **A pending submission blocks the next one**, even if the daily quota would otherwise
  allow it. Poll `kaggle competitions submissions`.
- **Public-LB noise is ~0.05.** A 0.17 vs 0.20 difference is about 2 tasks.

---

## 10. Definition of done

For a documentation/setup change:

- `python tools/check_resources.py` exits 0 with no warning.
- `verify_bundle.py` and (if the notebook changed) `verify_notebook.py` print
  `ALL CHECKS PASSED`.
- `git status` shows only intended files; large artefacts remain ignored.
- The change is committed and pushed.

For an experiment:

- Gates 2–4 passed, `RESULTS.md` updated, score recorded when available, and the
  bundle/kernel refs are committed so the result is reproducible.

For a submission:

- The user said yes, the quota was available, the artifact was verified byte-for-byte,
  and the ref + message were recorded in `RESULTS.md` and `ckpt/STATE.md`.

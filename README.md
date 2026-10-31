# gemma4hack — Gemma 4 Developer Agent

Private engineering workspace for the Kaggle competition
[`gemma-4-developer-agent`](https://www.kaggle.com/competitions/gemma-4-developer-agent).

The deliverable is a **Kaggle notebook that emits `submission.zip`**: a declarative
[Google ADK](https://google.github.io/adk-docs/) agent package. The organizers compile that
package with `adk-submission`, serve one Gemma 4 checkpoint on 4× NVIDIA L4, and run the agent
against ~120 hidden SWE-bench-style tasks. A task scores 1.0 only when the agent's patch makes
the hidden `pytest` suite pass in a fresh container.

There is **no local scoring loop**. The real evaluator needs the 31B QAT weights, the container
image and 4× L4, so this repo optimizes for three things instead:

1. **Mechanism-justified design** — every prompt or config change cites a line in the harness
   source, not a small leaderboard delta.
2. **Offline verification** — the bundle is checked by the *real* competition wheels, then the
   notebook is executed end-to-end and its artifact is checked byte-for-byte.
3. **Submission hygiene** — one verified bundle per day, with a recorded hash and kernel version.

---

## Status at a glance

| item | value |
|---|---|
| best public score | **0.20** — `exp05_patch_integrity`, ref `57553805` (31B) |
| other scored entries | 0.17 exp03 / exp08 / exp10 / exp12, 0.13 E4B-as-31B fallback, 0.06 genuine E4B |
| pending | `57806053` e4b-v2 (submitted 2026-10-30) |
| public LB top | 0.29 (2026-10-29); 0.24 cluster |
| team rank | 231 / 4,201 teams (2026-10-30) |
| main competition deadline | **2026-12-02 23:59 UTC** |
| paper-track deadline | **2026-11-12 23:59 UTC** |
| submission limit | **1 per day**; 1 pending at a time; no total cap (verified via the Kaggle API, 2026-10-30) |
| public dev set | 129 tasks: fastapi 67, rich 48, requests 13, httpx 1 |

Public-LB granularity is ~half of ~120 tasks, so **one task ≈ 0.017** and run-to-run sampling is
stochastic. **Differences below ~0.05 are noise**; do not tune to them.

---

## Quick start

### 1. Bootstrap the local harness

```powershell
# Windows (PowerShell)
python tools\bootstrap.py
```

```bash
# Linux / macOS
python tools/bootstrap.py
```

The bootstrap script creates `.venv-harness` on Python 3.12, installs `requirements.txt`,
downloads the three competition wheels from
[`metric/gemma-4-developer-agent-wheelhouse`](https://www.kaggle.com/datasets/metric/gemma-4-developer-agent-wheelhouse),
installs them with `--no-deps`, and runs the verifier. It is idempotent.

If the wheels are already present, the whole setup works offline:

```powershell
python tools\bootstrap.py --skip-wheels
```

### 2. Verify the current bundle

```powershell
.venv-harness\Scripts\python.exe tools\verify_bundle.py
```

```bash
.venv-harness/bin/python tools/verify_bundle.py
```

Expected: `ALL CHECKS PASSED`. The verifier runs three layers:

1. the project's strict static validator (`src/notebook_lib/validator.py`);
2. the **real** harness (`adk_submission.validate_directory`,
   `adk_submission.discovery.discover_declared_models`,
   `adk_submission.compile_submission`, `swegemma.config.build_submission_limits`);
3. 16 negative tests that prove the validator rejects broken bundles.

Validate any other bundle with `--bundle`:

```powershell
.venv-harness\Scripts\python.exe tools\verify_bundle.py --bundle kaggle_work\gemma-4-developer-agent\bundles\exp05_patch_integrity
```

### 3. Build and execute the notebook

```powershell
.venv-harness\Scripts\python.exe tools\build_notebook.py --out build\submission_notebook.ipynb
.venv-harness\Scripts\python.exe tools\verify_notebook.py --notebook build\submission_notebook.ipynb
```

`build_notebook.py` splices `src/notebook_lib/validator.py` and the bundle source directly into
the notebook, so the notebook cannot drift from `src/`. `verify_notebook.py` executes every code
cell in one shared namespace with a temp working directory, then checks the resulting zip:
root `agent.yaml`, no directory entries, allowed extensions, no adapters, deterministic repack,
manifest digest, and (when the wheels are importable) the real compiler.

### 4. Check the live competition resources

```powershell
python tools\check_resources.py
```

This uses the Kaggle API to verify authentication, the 524 competition files, the public dev set,
the wheelhouse, the paper track and recent submissions. Details and the verified inventory are in
[`docs/COMPETITION_RESOURCES.md`](docs/COMPETITION_RESOURCES.md).

---

## Which bundle is "the submission"?

`src/agent_package/` is the **default** bundle: `tools/build_notebook.py` and
`tools/verify_bundle.py` use it when no `--bundle` is given. It currently tracks the **E4B**
small-model track (9 tools, `temperature 0.2`, `max_tool_calls 28`, `max_time_minutes 8`,
`max_turns 80`, thinking on at 4096). The best-scoring 31B bundle is kept separately.

| bundle | model | tools | budget | score | where |
|---|---|---|---:|---:|---|
| `src/agent_package` | E4B | 9 | 28 calls / 8 min / 80 turns | pending E4B line | default build |
| `exp05_patch_integrity` | 31B | 9 | 28 / 8 / 80 | **0.20** | `kaggle_work/.../bundles/` |
| `exp12-timing-buffer` | 31B | 6 | 28 / 9 / 80 | 0.17 | `kaggle_work/.../bundles/` |
| `e4b_v2` | E4B | 6 | 35 / 8 / 80 | pending `57806053` | `tracks/e4b_small/bundles/` |
| `e4b_v3` | E4B | 6 | 28 / 8 / 80 | not submitted | `tracks/e4b_small/bundles/` |
| `ckpt/bundles/*` | mixed | — | frozen copies | — | `ckpt/bundles/` |

Before submitting, **diff the bundle you intend to submit against the last scored bundle** and
record the single change. `ckpt/bundles/exp05_patch_integrity/` is the 0.20 anchor; keep it
byte-exact.

The E4B track has its own verifiers:

```powershell
.venv-harness\Scripts\python.exe tracks\e4b_small\verify_bundle_e4b.py
.venv-harness\Scripts\python.exe tracks\e4b_small\verify_notebook_e4b.py
```

---

## Repository map

```
src/
  agent_package/            default declarative bundle (currently E4B)
  notebook_lib/             validator.py (inlined into the notebook) + package_source.py
  sections/                 notebook section modules; tools/build_notebook.py concatenates them
tools/
  bootstrap.py              one-command local setup
  check_resources.py        live Kaggle resource inventory
  verify_bundle.py          static + real-harness + negative checks
  build_notebook.py         generate build/submission_notebook.ipynb
  verify_notebook.py        execute the notebook and inspect its zip
  dump_notebook.py          dump a notebook back to source files for diffing
  kaggle_rest.py            bearer-auth REST client (kernel push/status/output/submit)
  kaggle_ckpt.py            push/pull the private checkpoint dataset
tracks/
  e4b_small/                E4B small-model track: bundles + dedicated verifiers + kernels
kaggle_work/gemma-4-developer-agent/
  bundles/                  per-experiment agent bundles
  experiments/              per-experiment kernel dirs (kernel-metadata.json + notebook)
  research/                 competition files, wheelhouse, dev-set eval kernels
  RESULTS.md                append-only experiment ledger
  CONFIG.md                 task/constraint summary (some fields stale; see live docs)
ckpt/                       frozen checkpoints: STATE.md, RESULTS.md, bundles, kernels, dataset
research/                   study guide, paper-track experiments, sources, score landscape
docs/                       runbook, resource inventory, paper draft, session notes
skills/swe-toolkit/         optional ADK skill (not used by the current primary bundle)
```

Key reading order for a new session:

1. `AGENTS.md` — hard rules and operating procedure.
2. this README;
3. `docs/COMPETITION_RESOURCES.md` — what is actually available;
4. `ckpt/STATE.md` — resume commands, submission order, kernel refs;
5. `kaggle_work/gemma-4-developer-agent/RESULTS.md` — what was tried and what happened;
6. `kaggle_work/gemma-4-developer-agent/research/competition/HARNESS_README.md` — the **live**
   harness documentation (newer than `ckpt/HARNESS_README.md`).

---

## Kaggle workflow

Authentication uses a bearer token. On this machine `KAGGLE_API_TOKEN` is set; the repo's
`tools/kaggle_rest.py` also accepts `KAGGLE_API_TOKEN` now.

```powershell
# inventory + auth check
python tools\check_resources.py

# recent submissions (status/score)
kaggle competitions submissions -c gemma-4-developer-agent

# kernel run status / output
kaggle kernels status narisettichaitanya/gemma4-devagent-exp05-ablation-patch-integrity
kaggle kernels output narisettichaitanya/gemma4-devagent-exp05-ablation-patch-integrity -p runs\exp05

# submit a completed kernel (ONLY with an explicit yes; one per day)
kaggle competitions submit -c gemma-4-developer-agent `
  -k narisettichaitanya/gemma4-devagent-exp05-ablation-patch-integrity `
  -v 1 -f submission.zip -m "exp05 patch integrity"
```

Kernel pushes can be done with the CLI or with `python tools/kaggle_rest.py push <dir>`.
Kernel IDs are re-slugified from the title, so always confirm the real ref with
`kaggle kernels list --mine` before `status`/`output`/`submit`.

The notebook itself is **CPU-only, offline, and self-contained**. It attaches the competition
as a data source (Kaggle requires this for notebook submissions) but reads nothing from it. It
only needs the standard library plus `PyYAML`.

---

## Hard constraints

| constraint | consequence |
|---|---|
| **1 submission/day** | one verified bundle per day; no total cap, but no exploratory spam |
| **12 h compute for ~120 sequential tasks** | per-task agent budget must average ≲4–5 min; 12 min was measured to exceed the cap and score 0 |
| **A notebook that errors scores 0** | build, validate and package must be exception-proof; test the notebook offline first |
| **No internet in the notebook** | no `pip install`, no downloads at run time |
| **Single base model per submission** | choose one of the four official quantized models; every agent in the bundle must declare the same one |
| **No LoRA adapters** | an adapter collapses the vLLM KV cache from ~46k to ~7.6k tokens and starves the context |
| **< 3 GiB unpacked** | only `.yaml .yml .md .txt .py .json .safetensors`; **no empty suffix** (so `LICENSE`, `Makefile`, `Dockerfile` would abort) |
| **Protected paths** | `conftest.py`, `pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`, `test_*.py`, `*_test.py`, and any `.py` under `tests/` are reset before grading |
| **`run_command` keeps the first 5,000 chars** | pytest's verdict is at the end; log to `/tmp` and `tail` |
| **`read_file` caps at 150 lines / 10,000 chars** | read tight line ranges |
| **Compaction at 14,336 tokens** | only the model's own text survives; keep a plain-text state card |
| **Context ceiling 32,768 tokens** | prompt + `max_output_tokens` must fit; a vLLM 400 discards an already-submitted patch |

The live `HARNESS_README.md` (2026-10-13) is authoritative. It permits four quantized models
(`gemma-4-31b-it-qat-w4a16-ct`, `gemma-4-12b-it-qat-w4a16-ct`,
`gemma-4-e4b-it-qat-w4a16-ct`, `gemma-4-e2b-it-qat-w4a16-ct`) and documents changed thinking
semantics; `ckpt/HARNESS_README.md` and parts of `ckpt/CONFIG.md` predate that revision.

---

## Experiment history (public LB)

| ref | date | bundle | score | model |
|---|---|---|---|---:|
| 57806053 | 2026-10-30 | e4b-v2 (temp 0.1 + imperative prompt) | pending | E4B |
| 57777888 | 2026-10-29 | exp11_e4b genuine E4B | 0.06 | E4B |
| 57736284 | 2026-10-28 | exp12-timing-buffer | 0.17 | 31B |
| 57697341 | 2026-10-27 | exp11_e4b (31B fallback) | 0.13 | 31B |
| 57654236 | 2026-10-26 | exp10-consolidated | 0.17 | 31B |
| 57618114 | 2026-10-25 | exp08 tool contract prompt | 0.17 | 31B |
| **57553805** | **2026-10-23** | **exp05 patch integrity** | **0.20** | **31B** |
| 57037122 | 2026-10-10 | exp03 baseline replica | 0.17 | 31B |
| 56812498 | 2026-10-04 | exp02 | 0.08 | 31B |
| 56793672 | 2026-10-03 | exp01 | 0.05 | 31B |

The full audit trail, failure analysis and per-experiment rationale are in
`kaggle_work/gemma-4-developer-agent/RESULTS.md`, `ckpt/RESULTS.md` and `docs/AUDIT_E4B_AND_PAPER.md`.

---

## Documentation

| file | purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | hard rules and workflow for AI coding agents |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | copy-paste commands for setup, verify, push, submit, recover |
| [`docs/TASKLIST.md`](docs/TASKLIST.md) | live task queue: instrument repair, E1 build, gates, submission ladder, deadlines |
| [`docs/AUDIT_E4B_AND_ANCHOR.md`](docs/AUDIT_E4B_AND_ANCHOR.md) | why 0.17/0.20 is noise, why the E4B line is closed, and what the 0.20 anchor really is |
| [`docs/COMPETITION_RESOURCES.md`](docs/COMPETITION_RESOURCES.md) | verified live resource inventory (files, hashes, deadlines) |
| [`docs/TASK_CLASSIFICATION.md`](docs/TASK_CLASSIFICATION.md) | what the 129 dev tasks look like: categories, patch shapes, hot files, difficulty |
| [`docs/SKILLS_ARCHITECTURE.md`](docs/SKILLS_ARCHITECTURE.md) | final skills/scripts/knowledge design, verified harness facts, 31B experiment ladder |
| [`docs/AUDIT_SNAPSHOTS.md`](docs/AUDIT_SNAPSHOTS.md) | downloaded audit snapshots: manifest, usage audit, retention policy |
| [`docs/AUDIT_E4B_AND_PAPER.md`](docs/AUDIT_E4B_AND_PAPER.md) | forensic audit of E4B/paper submissions |
| [`docs/PAPER_TRACK_DRAFT.md`](docs/PAPER_TRACK_DRAFT.md) | paper-track draft |
| [`research/COMPETITION_GUIDE.md`](research/COMPETITION_GUIDE.md) | 12-part study guide |
| [`ckpt/STATE.md`](ckpt/STATE.md) | checkpoint: resume commands and submission order |
| [`kaggle_work/gemma-4-developer-agent/RESULTS.md`](kaggle_work/gemma-4-developer-agent/RESULTS.md) | append-only experiment ledger |

---

## Contributing

This is a small, high-stakes repo: a broken notebook scores 0 and submissions are limited to one
per day. Before changing anything, read `AGENTS.md`. The short version:

- one isolated change per experiment, with a mechanism in the harness source;
- run `verify_bundle.py` **and** `verify_notebook.py` before pushing a kernel;
- never submit without an explicit yes in the conversation;
- record every experiment (including failures) in `RESULTS.md`;
- commit and push before long Kaggle waits.

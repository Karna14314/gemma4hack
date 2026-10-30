# RUNBOOK — copy-paste commands

Operational commands for this repo. For the rules and current state, read
[`../AGENTS.md`](../AGENTS.md) first. Paths are relative to the repo root.

Two shells are shown where they differ:

- **Windows / PowerShell** — `.venv-harness\Scripts\python.exe`, backslashes.
- **Linux / macOS** — `.venv-harness/bin/python`, forward slashes.

`python tools/check_resources.py` is the one command that must run with the **system
Python** (the one that has the `kaggle` package), not the venv.

---

## 1. First-time setup

### Prerequisites

| tool | why | check |
|---|---|---|
| Python 3.11+ (3.12 recommended) | `adk_eval_core` requires ≥3.11 | `python --version` |
| `uv` (optional but recommended) | fast venv + installs | `uv --version` |
| Kaggle CLI + credentials | download wheels, push/pull kernels | `kaggle --version` |
| GitHub CLI (optional) | push/PRs | `gh auth status` |

Authentication (either form works):

```powershell
$env:KAGGLE_API_TOKEN = "<KGAT_ bearer token>"
```

```bash
export KAGGLE_API_TOKEN="<KGAT_ bearer token>"
```

The legacy `~/.kaggle/kaggle.json` (`KAGGLE_USERNAME` + `KAGGLE_KEY`) also works. A bare
`KAGGLE_KEY` holding a `KGAT_` token does **not** work with older CLIs; the repo's
`tools/kaggle_rest.py` accepts `KAGGLE_API_TOKEN` directly.

### One-command bootstrap

```powershell
python tools\bootstrap.py
```

```bash
python tools/bootstrap.py
```

This creates `.venv-harness` on Python 3.12, installs `requirements.txt`, downloads
`swegemma`, `adk_submission`, `adk_eval_core` from the wheelhouse dataset, installs them
with `--no-deps`, and runs `verify_bundle.py`.

Useful flags:

| flag | effect |
|---|---|
| `--skip-wheels` | offline; fail if the three wheels are missing |
| `--skip-verify` | install only |
| `--notebook` | also build and execute the submission notebook |
| `--force` | delete and recreate `.venv-harness` |

If the wheels are already on disk, this is fully offline:

```powershell
python tools\bootstrap.py --skip-wheels
```

### Manual setup (if bootstrap cannot run)

```powershell
uv venv --python 3.12 .venv-harness
uv pip install --python .venv-harness\Scripts\python.exe -r requirements.txt
kaggle datasets download -d metric/gemma-4-developer-agent-wheelhouse `
  -f swegemma-0.2.11-py3-none-any.whl -p kaggle_work\gemma-4-developer-agent\research\wheelhouse --unzip
# repeat -f for adk_submission-0.2.13-py3-none-any.whl and adk_eval_core-0.1.0-py3-none-any.whl
uv pip install --python .venv-harness\Scripts\python.exe --no-deps `
  kaggle_work\gemma-4-developer-agent\research\wheelhouse\*.whl
```

---

## 2. Check the live competition resources

```powershell
python tools\check_resources.py
```

Expected tail:

```
all required resources present
```

Options:

```powershell
python tools\check_resources.py --refresh      # re-download tasks.jsonl + HARNESS_README.md
python tools\check_resources.py --no-download  # inventory only
```

This verifies authentication, the 524 competition files, the 129-task public dev set,
the wheelhouse, the paper track, and recent submissions. Exit code 0 = all required
resources present; 1 = a required resource is missing. A `[WARN]` means a hash or size
changed since the 2026-10-30 snapshot — re-read the live file before trusting old notes.

Full inventory: [`COMPETITION_RESOURCES.md`](COMPETITION_RESOURCES.md).

---

## 3. Verify a bundle

Current default bundle (`src/agent_package`):

```powershell
.venv-harness\Scripts\python.exe tools\verify_bundle.py
```

```bash
.venv-harness/bin/python tools/verify_bundle.py
```

Any other bundle:

```powershell
.venv-harness\Scripts\python.exe tools\verify_bundle.py `
  --bundle kaggle_work\gemma-4-developer-agent\bundles\exp05_patch_integrity
```

Expected: `ALL CHECKS PASSED`.

What it does:

1. project static validator (`src/notebook_lib/validator.py`);
2. real harness: `adk_submission.validate_directory`,
   `adk_submission.discovery.discover_declared_models`,
   `adk_submission.compile_submission`, `swegemma.config.build_submission_limits`;
3. negative tests proving the validator rejects broken bundles.

A `[WARN] model ... is not in the local harness registry` is expected for E4B/E2B when
the installed wheel lags the live docs. Re-download the wheelhouse before treating it as
a blocker.

---

## 4. Build and execute the notebook

```powershell
.venv-harness\Scripts\python.exe tools\build_notebook.py --out build\submission_notebook.ipynb
.venv-harness\Scripts\python.exe tools\verify_notebook.py --notebook build\submission_notebook.ipynb
```

```bash
.venv-harness/bin/python tools/build_notebook.py --out build/submission_notebook.ipynb
.venv-harness/bin/python tools/verify_notebook.py --notebook build/submission_notebook.ipynb
```

Build for a non-default bundle:

```powershell
.venv-harness\Scripts\python.exe tools\build_notebook.py `
  --bundle kaggle_work\gemma-4-developer-agent\bundles\exp12-timing-buffer `
  --out kaggle_work\gemma-4-developer-agent\experiments\exp12-timing-buffer\submission_notebook.ipynb
```

`verify_notebook.py` executes every code cell in one shared namespace with a temp working
directory and checks the resulting zip: root `agent.yaml`, no directory entries, allowed
extensions, no adapters, deterministic repack, manifest digest, and the real compiler.
Expected: `ALL CHECKS PASSED`.

### E4B track verifiers

```powershell
.venv-harness\Scripts\python.exe tracks\e4b_small\verify_bundle_e4b.py
.venv-harness\Scripts\python.exe tracks\e4b_small\verify_notebook_e4b.py
```

These assert E4B-specific invariants (6 tools, no graph tools, temperature 0.2, 8192
output tokens, 4096 thinking budget, 28/8/80 budgets, clean prompt ending, no 31B leak).
For `e4b_v2` use `verify_bundle_e4b_v2.py` / `verify_notebook_e4b_v2.py`.

---

## 5. Push a kernel

A kernel directory needs `kernel-metadata.json` and the notebook named by `code_file`.

```powershell
kaggle kernels push -p kaggle_work\gemma-4-developer-agent\experiments\<exp>
```

Or with the repo's bearer-auth client:

```powershell
python tools\kaggle_rest.py push kaggle_work\gemma-4-developer-agent\experiments\<exp>
```

**The pushed slug can differ from the requested `id`** because Kaggle re-slugifies the
title. Confirm the real ref immediately:

```powershell
kaggle kernels list --mine
```

Then poll:

```powershell
kaggle kernels status <owner>/<slug>
```

A notebook kernel is CPU-only and normally finishes in minutes. `COMPLETE` is necessary
but not sufficient: pull the output and inspect it.

```powershell
kaggle kernels output <owner>/<slug> -p runs\<exp>
```

Check:

- `runs\<exp>\submission.zip` exists;
- `runs\<exp>\submission_manifest.json` (if emitted) has the expected hash;
- the kernel log has no traceback and ends with the expected sentinel;
- the pulled zip is byte-identical to the local build.

---

## 6. Submissions (only with an explicit yes)

> **Hard rule:** never run this without an explicit "yes" from the user in the current
> conversation. One submission per day; one pending at a time; there is **no total cap**.
> A pending submission blocks the next one.

Check quota and history first:

```powershell
kaggle competitions submissions -c gemma-4-developer-agent
```

Submit a completed kernel version:

```powershell
kaggle competitions submit -c gemma-4-developer-agent `
  -k <owner>/<slug> -v <version> -f submission.zip `
  -m "<bundle>: <single change>"
```

Or with the REST client:

```powershell
python tools\kaggle_rest.py submit `
  --competition gemma-4-developer-agent `
  --kernel <owner>/<slug> --version <N> `
  --filename submission.zip `
  --message "<bundle>: <single change>"
```

After submitting, record the ref, timestamp, kernel version, and message in
`kaggle_work/gemma-4-developer-agent/RESULTS.md` and `ckpt/STATE.md`.

Poll:

```powershell
python tools\kaggle_rest.py submissions gemma-4-developer-agent
```

Scoring runs on the organizers' 4× L4 box and can take hours. Do not resubmit while one
is pending.

---

## 7. Checkpoint dataset

`tools/kaggle_ckpt.py` pushes a directory to the private checkpoint dataset over REST
(bearer auth). It skips `.git`, `.venv-harness`, `__pycache__`, `.verify_build`, `ckpt`,
and metadata files.

```powershell
python tools\kaggle_ckpt.py version ckpt narisettichaitanya/gemma4-agent-ckpt "notes"
python tools\kaggle_ckpt.py pull   narisettichaitanya/gemma4-agent-ckpt ckpt_pull
```

First creation uses `create <dir> <owner>/<slug> <title> <notes>`.

---

## 8. Recovery

### `verify_bundle.py` cannot import `adk_submission` / `swegemma`

The script re-execs into `.venv-harness` automatically if it exists. If it still fails:

```powershell
python tools\bootstrap.py --skip-verify
```

or reinstall the wheels:

```powershell
uv pip install --python .venv-harness\Scripts\python.exe --no-deps `
  kaggle_work\gemma-4-developer-agent\research\wheelhouse\*.whl
```

### The venv is broken or has the wrong Python

```powershell
python tools\bootstrap.py --force
```

### The wheelhouse is missing or stale

```powershell
kaggle datasets download -d metric/gemma-4-developer-agent-wheelhouse `
  -p kaggle_work\gemma-4-developer-agent\research\wheelhouse --unzip
```

The dataset is ~840 MiB / 41 files. `check_resources.py` verifies the three wheels the
verifiers need.

### Kaggle 401s but anonymous downloads work

The token is bearer-only. Use `KAGGLE_API_TOKEN` (not a bare `KAGGLE_KEY`) or the repo's
REST client. Confirm with `kaggle kernels list --mine`; an anonymous call succeeding is
not proof of authentication.

### `kernels status` says "not found"

The slug was re-slugified from the title. List your kernels and use the actual ref:

```powershell
kaggle kernels list --mine
```

### Submission rejected: pending submission / quota

```
Submission not allowed: Your team already has 1 pending submissions
```

Wait for the pending run to finish scoring. Check `kaggle competitions submissions`.
Do not try to work around the limit.

### Submission rejected: bundle invalid

Run Gate 2 and Gate 3 on the **exact** bundle and notebook. Common causes:

- an empty-suffix file (`LICENSE`, `Makefile`) or a disallowed extension;
- two root configs;
- a prompt with a stray `{brace}` or a missing `{problem_description}`;
- a model not in the four official aliases;
- `adapters/` present;
- > 3 GiB unpacked.

### Notebook runs but the zip is wrong

Compare the pulled artifact to the local build:

```powershell
Get-FileHash runs\<exp>\submission.zip -Algorithm SHA256
Get-FileHash build\submission.zip -Algorithm SHA256
```

Rebuild with `build_notebook.py` and re-run `verify_notebook.py`. Do not hand-edit the
notebook; it is generated from `src/`.

### A score came back 0 or unexpectedly low

Check, in order:

1. Did the kernel actually finish and emit a zip? (A notebook error scores 0.)
2. Did every task exceed the per-task time cap? (12 min was measured to blow the 12 h
   total.)
3. Did the bundle declare a model the scorer rejects?
4. Was the patch empty because `git add -N .` respected `.gitignore`?
5. Is the delta within noise (~0.05)? One task is ~0.017.

Record the failure mode in `RESULTS.md` before trying a fix.

---

## 9. Git hygiene

```powershell
git status --short
git diff
git add <intended files>
git commit -m "<type>: <what changed and why>"
git push origin main
```

Ignored on purpose: `.venv-harness/`, `build/`, `kaggle_work/*/runs/`,
`kaggle_work/*/research/wheelhouse/`,
`kaggle_work/*/research/competition/tasks.jsonl`, `*.zip`.

Commit before any long Kaggle wait, and again when a score arrives.

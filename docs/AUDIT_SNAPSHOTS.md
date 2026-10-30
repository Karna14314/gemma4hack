# Audit snapshots — manifest, usage, retention

Seven repository snapshots from the competition dataset were downloaded and extracted on
**2026-10-30** for the localization audit that informs `docs/SKILLS_ARCHITECTURE.md`.
They are **research artefacts, not submission inputs**, and they are gitignored.

- Location: `audit_snapshots/` (repo root)
- Volume: **786.3 MB compressed** (`.tgz`), **829.5 MB extracted**, 1.6 GB on disk
- Coverage: 7 of the 129 public dev tasks, chosen for archetype coverage, not at random
- Rebuild: `python tools/audit_locate.py` (read-only; never writes inside a snapshot)
- Result file: `audit_snapshots/locate_benchmark.json` (gitignored, regenerable)

The competition dataset holds 129 snapshots totalling **21.5 GB**, so the full set is not
practical to keep. Seven is enough to calibrate the ranker and expose its failure modes.

## 1. Manifest

| task | repo | tgz MB | extracted MB | `.py` files | gold files | locate rank | why this task |
|---|---|---:|---:|---:|---:|---:|---|
| `httpx_3672` | encode/httpx | 1.6 | 1.9 | 45 | 7 | **1** | multi-file, `httpx`/`ahttpx` mirror, title-only issue |
| `requests_7502` | psf/requests | 37.5 | 39.1 | 37 | 1 | **2** | 67-char title-only issue, single-file fix |
| `requests_7315` | psf/requests | 37.6 | 39.3 | 36 | 1 | **1** | prose issue with expected behaviour, single file |
| `rich_3061` | Textualize/rich | 90.6 | 95.4 | 190 | 1 | **1** | rich bugfix, single file |
| `rich_3470` | Textualize/rich | 92.9 | 97.8 | 190 | 1 | **10** | ranker failure: tests occupy the whole top 3 |
| `fastapi_15280` | fastapi/fastapi | 294.2 | 310.7 | 1,118 | 2 | **2** | feature request for a symbol absent from the base (`@app.vibe()`) |
| `fastapi_14371` | fastapi/fastapi | 231.9 | 245.4 | 1,279 | 4 | **1** | multi-file FastAPI/Pydantic compatibility task |
| **total** | | **786.3** | **829.5** | | | | |

Extraction cost is roughly 1.05–1.06× the tarball for these repositories. The FastAPI
snapshots dominate the footprint (526 MB of 786 MB) because they include `.git` history,
`docs_src/`, and test fixtures.

## 2. Usage audit

What was done with the snapshots:

| action | scope | writes |
|---|---|---|
| `tar -xzf` extraction | all 7 | `audit_snapshots/<task>/` |
| `tools/audit_locate.py` run | all 7 | `audit_snapshots/locate_benchmark.json` |
| test-demotion counterfactual | all 7 | none (in-memory re-rank) |
| source inspection | `rich_3470`, `fastapi_15280`, `httpx_3672` | none |

What was **not** done: no edits to snapshot files, no `pip install` inside a snapshot, no
test execution inside a snapshot, no Kaggle write operation, no submission. The snapshots
are checked out at each task's `base_commit` and were only read.

### 2.1 Locate benchmark (real `skills/swe-toolkit` ranker)

`_index.locate(root, problem_statement, top_n=10)`, file-level aggregation, no
modifications. Gold files come from the task's `patch` field.

| task | best gold rank | hit@1 | hit@3 | hit@5 | hit@10 | runtime |
|---|---:|---|---|---|---|---:|
| `httpx_3672` | 1 | yes | yes | yes | yes | 0.30 s |
| `requests_7502` | 2 | no | yes | yes | yes | 0.40 s |
| `requests_7315` | 1 | yes | yes | yes | yes | 0.38 s |
| `rich_3061` | 1 | yes | yes | yes | yes | 1.11 s |
| `rich_3470` | 10 | no | no | no | yes | 1.14 s |
| `fastapi_15280` | 2 | no | yes | yes | yes | 3.04 s |
| `fastapi_14371` | 1 | yes | yes | yes | yes | 3.14 s |
| **overall** | | **4/7** | **6/7** | **6/7** | **7/7** | median 1.11 s |

Runtime is well inside the 25 s locate deadline, including the 1,279-file FastAPI repo.
The earlier ad-hoc lexical ranker needed 20–25 s on FastAPI and missed `fastapi_15280`;
the prototype's AST/IDF ranker is both faster and better, so the prototype is the right
base to extend.

### 2.2 Test-demotion counterfactual

Test files are never gold: the harness resets `tests/` and applies its own `test_patch`.
Yet tests occupied at least one of the top 3 files in 5 of 7 tasks, and all of the top 3
in `rich_3470`. Re-ranking with test paths removed (same scores, no other change):

| metric | raw | tests demoted |
|---|---:|---:|
| hit@1 | 4/7 | **5/7** |
| hit@3 | 6/7 | **7/7** |
| hit@5 | 6/7 | **7/7** |

This is a one-line ranker change with a mechanism (protected paths cannot be gold) and a
measured effect. It is the first change to make in `_index.py`.

### 2.3 Known failure mode

`fastapi_15280` asks for `@app.vibe()`, which does not exist in the base commit. Pure
lexical/AST search cannot find a symbol that is not there. The gold patch is
`fastapi/applications.py` (add the method) plus `docs_src/vibe/tutorial001_py310.py`
(the executable example). The ranker still puts `applications.py` at rank 2 by matching
`app`, `vibe`, and sibling methods, but the `docs_src` file is found only by path prior,
not by content. Feature tasks need a sibling/registration-point heuristic
(`__all__`, routers, `docs_src/<feature>/`), not a better lexical score.

## 3. Retention policy

**Keep them.** They are cheap relative to the value of re-running the benchmark and they
make the paper-track numbers reproducible. They are gitignored, so they never enter a
commit or a submission archive.

Delete only when one of these is true:

1. the 31B toolkit line is closed and no further locate work is planned;
2. disk pressure on this machine;
3. the competition ends (2026-12-02) and the paper track is submitted (2026-11-12).

Before deleting, preserve the audit trail:

1. the summary tables in this file and in `docs/TASK_CLASSIFICATION.md` are already the
   durable record — they do not depend on the snapshots;
2. copy `audit_snapshots/locate_benchmark.json` to `docs/audit/` if a future session
   needs the raw per-task rows;
3. append a dated line to §4 below with what was deleted and why.

Deletion (PowerShell):

```powershell
Remove-Item -Recurse -Force audit_snapshots
```

Re-download one task (about 1–5 minutes each on this connection):

```powershell
kaggle competitions download -c gemma-4-developer-agent `
  -f snapshots/<task_id>.tgz -p audit_snapshots --quiet
New-Item -ItemType Directory -Force audit_snapshots\<task_id> | Out-Null
tar -xzf audit_snapshots\<task_id>.tgz -C audit_snapshots\<task_id>
python tools\audit_locate.py --tasks <task_id>
```

`tools/audit_locate.py` auto-discovers every extracted directory that contains `.git`, so
a partial re-download does not invalidate the rest of the benchmark.

## 4. Change log

| date | change | reason |
|---|---|---|
| 2026-10-30 | downloaded and extracted 7 snapshots (786 MB) | localization audit for the 31B toolkit design |
| 2026-10-30 | added `audit_snapshots/` to `.gitignore` | keep large artefacts out of git |

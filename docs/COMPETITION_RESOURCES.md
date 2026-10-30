# Competition resources — verified inventory

Live snapshot taken **2026-10-30** with the Kaggle API. Everything below was verified by
`python tools/check_resources.py`, not copied from older notes.

Re-verify at any time:

```powershell
python tools\check_resources.py            # inventory + cached small files
python tools\check_resources.py --refresh  # re-download HARNESS_README.md + tasks.jsonl
python tools\check_resources.py --no-download
```

Exit code 0 means every required resource is present. A `[WARN]` means a size or hash
changed since this snapshot — re-read the live file before relying on any note here.

---

## Competition metadata

| field | value |
|---|---|
| competition | `gemma-4-developer-agent` |
| URL | https://www.kaggle.com/competitions/gemma-4-developer-agent |
| task | patch ~120 hidden SWE-bench-style issues; score = fraction resolved by hidden tests |
| deliverable | Kaggle notebook that writes `submission.zip` (declarative ADK agent package) |
| main deadline | **2026-12-02 23:59 UTC** |
| paper track | `gemma-4-developer-agent-paper`, deadline **2026-11-12 23:59 UTC** |
| submission limit | **1 per day**; 1 pending at a time; no total cap (verified via the API 2026-10-30) |
| public LB top | 0.29 (2026-10-29); a 0.24 cluster |
| our team rank | 232 / 4,202 (2026-10-30) |
| our best public score | **0.20** (`exp05_patch_integrity`, ref `57553805`, 31B) |
| pending at snapshot | `57806053` e4b-v2 (2026-10-30), status PENDING |

Submission mechanics, verified from `competitions.CompetitionService/GetCompetition` on
2026-10-30: `maxDailySubmissions: 1`, `maxPendingSubmissionsPerTeam: 1`,
`numScoredSubmissions: 2`, `leaderboardPercentage: 50`,
`requiredSubmissionFilename: submission.zip`. **There is no total-submission cap**; the
earlier "10 total" note was wrong. Only two submissions are selected for final scoring, so
the last two must be deliberate.

The scoring rerun runs ~120 tasks sequentially on the organizers' 4× L4 box inside a
**12-hour** cap, including vLLM startup and pytest verification. Queueing and runtime can
take hours. One public-LB task is worth ~0.017; differences below ~0.05 are noise.

---

## Competition files: 524 total

| group | count | what it is |
|---|---:|---|
| `snapshots/` | 129 | per-task repository snapshots (one per public dev task) |
| `graphs/` | 127 | code-graph artifacts used by the graph tools |
| `embeddings/` | 127 | code embeddings used by `search_similar_code` |
| `wheels/` | 124 | vendored Python wheels for the task environments |
| `sample_submission/` | 10 | sample `submission.zip` layouts / starter bundles |
| `docker/` | 4 | task container definitions |
| `sandbox/` | 1 | sandbox image/definition |
| `HARNESS_README.md` | 1 | **the live harness documentation** (authoritative) |
| `tasks.jsonl` | 1 | public dev set, 129 tasks |
| **total** | **524** | |

The exact counts sum to 524. `tools/check_resources.py` enforces minimum counts, not exact
counts, so a small addition upstream is not a failure; a missing group is.

### Small files (cached locally)

| file | size | sha256 |
|---|---:|---|
| `HARNESS_README.md` | 55,940 B | `445000219b803942c469391ec8b69791a31e9cec2f934738c767e34b5ca0aa1f` |
| `tasks.jsonl` | 1,984,455 B | `e4b3fd60f69dbc2b9213e54eeb9636db78aefe92c1d06269d73d9f5f8f3c8ad6` |

Both are downloaded to
`kaggle_work/gemma-4-developer-agent/research/competition/`. `tasks.jsonl` is gitignored
(1.9 MiB, regenerable); `HARNESS_README.md` is small enough to commit and is the reference
the repo's rules are based on.

The live `HARNESS_README.md` is the **2026-10-13 revision**. It supersedes
`ckpt/HARNESS_README.md` and parts of `ckpt/CONFIG.md`. It documents:

- four permitted models: `gemma-4-31b-it-qat-w4a16-ct`,
  `gemma-4-12b-it-qat-w4a16-ct`, `gemma-4-e4b-it-qat-w4a16-ct`,
  `gemma-4-e2b-it-qat-w4a16-ct`;
- `include_thoughts: false` still enables reasoning on the current turn when
  `thinking_budget > 0`;
- compaction interval 15, threshold 14,336 tokens;
- `max_model_len = 32,768`, `gpu_memory_utilization = 0.90`;
- `< 3 GiB` unpacked, extensions `.yaml .yml .md .txt .py .json .safetensors`;
- `run_command` / graph output truncation at 5,000 chars, `read_file` at 150 lines.

If the hash changes, re-read the file before acting on any of the above.

---

## Public dev set: 129 tasks

| repo | tasks |
|---|---:|
| `fastapi/fastapi` | 67 |
| `Textualize/rich` | 48 |
| `psf/requests` | 13 |
| `encode/httpx` | 1 |
| **total** | **129** |

Each row has at least: `instance_id`, `repo`, `problem_statement`, `patch`, `test_patch`.
Task ids are unique. The public dev set is for offline analysis and the paired GPU eval
kernel; it is **not** the hidden scoring set.

---

## Wheelhouse dataset

| field | value |
|---|---|
| dataset | `metric/gemma-4-developer-agent-wheelhouse` |
| URL | https://www.kaggle.com/datasets/metric/gemma-4-developer-agent-wheelhouse |
| files | 41 |
| total size | 840.0 MiB |
| local path | `kaggle_work/gemma-4-developer-agent/research/wheelhouse/` (gitignored) |

The three wheels the local verifier needs:

| wheel | version | used for |
|---|---|---|
| `swegemma-0.2.11-py3-none-any.whl` | 0.2.11 | harness config, limits, tools, scoring |
| `adk_submission-0.2.13-py3-none-any.whl` | 0.2.13 | declarative compiler + validation |
| `adk_eval_core-0.1.0-py3-none-any.whl` | 0.1.0 | sandbox/eval infrastructure |

Download:

```powershell
kaggle datasets download -d metric/gemma-4-developer-agent-wheelhouse `
  -p kaggle_work\gemma-4-developer-agent\research\wheelhouse --unzip
```

Install with `--no-deps` into `.venv-harness`; `tools/bootstrap.py` does this
automatically. The installed `swegemma` wheel's model registry can lag the live docs (it
currently registers only 31B and E4B), which is why `verify_bundle.py` warns rather than
fails for a docs-permitted model it does not know.

---

## Paper track

| field | value |
|---|---|
| competition | `gemma-4-developer-agent-paper` |
| files | 1 |
| file | `NOTE.md` (55 B) |
| contents | "Welcome! This is a Hackathon with no provided dataset." |
| deadline | **2026-11-12 23:59 UTC** |

The paper track exposes no dataset and no separate scoring files through the API. The
repo's paper material lives in `docs/PAPER_TRACK_DRAFT.md`,
`docs/AUDIT_E4B_AND_PAPER.md`, and `research/` (benchmarks, sources, score landscape).

---

## What is available vs. not available

### Available

- The public dev set (`tasks.jsonl`) and per-task snapshots/graphs/embeddings.
- The exact harness libraries (`swegemma`, `adk_submission`, `adk_eval_core`) as wheels,
  so `validate_directory` / `compile_submission` / budget limits can be run locally.
- The live harness documentation, including tool behavior, limits, and failure modes.
- Sample submissions and Docker/sandbox definitions.
- Kernel execution (CPU-only) and competition submission APIs.

### Not available

- The hidden scoring tasks and their tests.
- Per-task scoring logs or a breakdown of which tasks passed (only the aggregate public
  score is exposed).
- The organizers' 4× L4 runtime, so the real per-task latency and vLLM behavior cannot be
  measured locally.
- A local end-to-end score. `verify_notebook.py` proves the artifact is well-formed; it
  cannot prove the agent solves tasks.

This is why the repo optimizes for mechanism-justified changes and offline verification,
and treats public-LB deltas below ~0.05 as noise.

---

## Recent submissions at snapshot

| ref | date | status | public | bundle |
|---|---|---|---:|---|
| `57806053` | 2026-10-30 | PENDING | — | e4b-v2 (temp 0.1 + imperative prompt) |
| `57777888` | 2026-10-29 | COMPLETE | 0.06 | exp11_e4b genuine E4B |
| `57736284` | 2026-10-28 | COMPLETE | 0.17 | exp12-timing-buffer |
| `57697341` | 2026-10-27 | COMPLETE | 0.13 | exp11_e4b (31B fallback) |
| `57654236` | 2026-10-26 | COMPLETE | 0.17 | exp10-consolidated |
| `57618114` | 2026-10-25 | COMPLETE | 0.17 | exp08 tool contract prompt |
| `57553805` | 2026-10-23 | COMPLETE | **0.20** | exp05 patch integrity |
| `57037122` | 2026-10-10 | COMPLETE | 0.17 | exp03 baseline replica |

The API's `numAllowedNow` was `0` at snapshot time because `57806053` is pending. Always
check the live list before planning a submission; a pending run blocks the next one even
if the daily quota would otherwise allow it.

---

## Staleness checklist

Run this before trusting the inventory:

1. `python tools/check_resources.py` exits 0.
2. The `HARNESS_README.md` and `tasks.jsonl` hashes match the table above. If not, re-read
   the live file and update this document.
3. The wheelhouse still contains the three wheel filenames above. If versions bump,
   update `requirements.txt`, `tools/bootstrap.py`, `tools/check_resources.py`,
   `tools/verify_bundle.py`, and this document together.
4. The live submission list still matches the table (scores flip from PENDING to
   COMPLETE asynchronously).

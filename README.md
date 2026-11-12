# gemma4hack — Budget-Aware Graph-Lexical Retrieval for Offline Gemma 4 SWE Agents

Repo for the Kaggle competition [`gemma-4-developer-agent`](https://www.kaggle.com/competitions/gemma-4-developer-agent)
and its **paper track** (`gemma-4-developer-agent-paper`, deadline 2026-11-12).

**Summary** (from `docs/PAPER_TRACK_DRAFT.md`, §Abstract — the authoritative thesis statement;
`docs/MASTER_WRITEUP_FINAL.md` is the machine-gated writeup of the same work, see `scripts/reproduce_all.py`):
Autonomous SWE agents in offline environments face hard resource ceilings — a 32,768-token vLLM context,
28 tool calls, and an 8-minute per-task timeout on 4× NVIDIA L4. Under these bounds, outcomes are governed
by harness mechanics and stochastic variance rather than prompt phrasing. Combining 18 live Kaggle
submissions with a verified 129-task offline benchmark across four Python repositories, this work shows:
(1) wheel audits of Google ADK 1.36.1 and vLLM 0.19.1 surface five silent failure modes (interval compaction
amnesia on thought turns, reasoning-history drops, context-window overflow, `git add -N` ignoring new files,
and missing sandbox test dependencies); (2) a two-regime retrieval benchmark shows live workspace AST
indexing lifts File R@5 from 0.4350 (static code graphs, degraded by 5,000-char tool caps) to 0.7440;
(3) cross-scale ablations show 31B models at 0.20 (pooled 0.17) while equipping 4B agents with
deterministic localization tools (`skills/swe-toolkit`) fails to lift resolution (0.05), falsifying the
localization-offload hypothesis.

---

## Paper artifact map

| Paper item | Script | Input data | Output file | Status |
|---|---|---|---|---|
| Fig 0–5 (writeup figures) | `scripts/generate_paper_figures.py` | `research/verified_json/*.json` (committed) | `assets/paper_figures/fig0..fig5.png` | reproducible from repo (verified: renders byte-identical to committed PNGs) |
| Res-fig 0–3 (resource paper) | `scripts/generate_resource_figures.py` | in-script data + verified JSONs | `assets/resource_figures/res_fig0..3.png` | reproducible from repo (verified this session) |
| Fig 1–3 + thumbnail (evidence pack) | `research/paper_figs/make_figures.py` | `research/paper_figs/ledger.csv`, `eval_results/instrument_b.json`, `symbol_ablation.json` | `research/paper_figs/fig{1,2,3}.png` + `*_data.csv` | reproducible from repo (verified this session) |
| Every number in `docs/MASTER_WRITEUP_FINAL.md` | `scripts/reproduce_all.py` (gate; `--fill` machine-writes) | `research/verified_json/*.json` JSON pointers | `docs/number_audit.csv` | reproducible from repo; gate exits non-zero on drift |
| Table 1 — leaderboard ablations (n=58/run) | manual ledger from Kaggle API | `docs/ENV_AUDIT.md` §4.1, `kaggle_work/.../RESULTS.md` | `research/paper_figs/ledger.csv` | committed data |
| Table 2A — static graph corpus (M1–M5; M4 File R@5 0.4350) | `research/kernel_paper_eval/paper_eval.py` (runs **on Kaggle**) | `tasks.jsonl` + `graphs/*.json` + `embeddings/*.npz` (Kaggle inputs) | `research/PAPER_TABLES.md`; per-task: `research/quarantined_legacy_audits/regime_a_per_task.json` | Kaggle-only rerun; per-task rows committed (quarantined path) |
| Table 2C — live workspace v4 (0.419/0.651/0.744/0.829) | `scripts/t6_run.py` | `eval_snapshots/` (via `scripts/fetch_eval_data.py`) + `skills/swe-toolkit/scripts/_index.py` | `eval_results/t6_results_v4_repro.json`; per-task v4: `eval_results/instrument_b.json` | v4 per-task committed; full re-run needs `eval_snapshots/` (re-fetchable) |
| Table 2D — symbol re-ranking (v4…v6) | `scripts/t6_run.py` (v4 only) | `eval_results/t6_results_v4_repro.json` | `research/paper_figs/symbol_ablation.json` | v4 recomputed from committed data; **v5/v5A/v5AB/v6 per-task data not committed** |
| Table 3 — patch anatomy + 27/67 dep failures | Kaggle kernel `research/kernel_swe_toolkit_demo/g4-swe-toolkit-resource-demo.ipynb` | `tasks.jsonl` gold patches + snapshots | per-repo `PATCH_STATS` in kernel; `docs/PAPER_TRACK_DRAFT.md` Table 3 | runs on Kaggle; counts embedded in committed kernel source |
| Headline: pooled 31B 79/464 = 0.170, SE 0.0503 | recomputation from ledger | `research/paper_figs/ledger.csv`, `docs/ENV_AUDIT.md` | `docs/PAPER_VERIFY.md` §B | verified doc-level math |
| Headline: 0.4350 → 0.7440 transition | `paper_eval.py` + `t6_run.py` (different metrics — see gaps) | graph corpus vs `eval_snapshots/` | `docs/PAPER_VERIFY.md` §A | both sides sourced; labels must stay distinct |
| 80.9% payload truncation (313/387) | — (cap-sweep graphs not committed) | — | `docs/PAPER_TRACK_DRAFT.md` §3.3 | **not re-verifiable from repo** (see gaps) |

All paths above verified to exist in the repo. Note: `docs/PAPER_ASSETS.md:18` says
`python scripts/make_paper_figs.py`, but that path does not exist — the tracked figure script is
`research/paper_figs/make_figures.py`.

## Reproduce

Audited environment: **Python 3.12** in `.venv-harness` (venv is gitignored). The three competition
wheels are not on PyPI; they come from the Kaggle dataset `metric/gemma-4-developer-agent-wheelhouse`.

```bash
# 1) venv + wheels + verification (idempotent; Python 3.12)
python tools/bootstrap.py

# 2) figures + integrity gate (stdlib + matplotlib + numpy + Pillow; tested on Python 3.13 system python)
python scripts/generate_paper_figures.py      # -> assets/paper_figures/
python scripts/generate_resource_figures.py   # -> assets/resource_figures/
python research/paper_figs/make_figures.py    # -> research/paper_figs/
python scripts/reproduce_all.py               # number gate -> docs/number_audit.csv

# 3) fetch the 129-task eval snapshots (~21.5 GB compressed, multi-hour; needs Kaggle auth)
python scripts/fetch_eval_data.py             # downloads + extracts + verifies -> eval_snapshots/
python scripts/fetch_eval_data.py --verify-only

# 4) main eval scripts (need eval_snapshots/ from step 3)
.venv-harness/Scripts/python.exe scripts/t6_run.py --out eval_results/t6_results_v4_repro.json   # ~30 min
.venv-harness/Scripts/python.exe scripts/capped_query_eval.py
.venv-harness/Scripts/python.exe scripts/run_verified_experiments.py  # -> research/verified_json/*.json

# 5) Kaggle-side instruments (run inside Kaggle, not locally)
#    research/kernel_paper_eval/paper_eval.py          (Table 2A, graph corpus)
#    research/kernel_swe_toolkit_demo/g4-swe-toolkit-resource-demo.ipynb  (Table 3, playbooks)
```

Figure scripts were executed against the committed inputs during the 2026-11-12 doc pass and
regenerated all tracked PNGs with **zero git diff** (deterministic).

## Known gaps and errata

Stated plainly, so nobody has to rediscover them:

- **v5 / v5A / v5AB / v6 symbol re-ranking**: per-task data and a runnable re-ranker are **not committed**
  (draft Table 2D values only; `bundles/exp14_lean_toolkit/.../_index.py` has the v6 file-level levers
  but no per-task symbol entry point). `research/paper_figs/fig3` was omitted from `PAPER_ASSETS.md`
  for this reason; a regenerated `fig3.png` is now committed.
- **Instrument B**: per-task any-gold ranks committed **for v4 only** (129 tasks, `eval_results/instrument_b.json`);
  `base`/`v3` aggregates are draft-only (historical engine variants not in committed code).
- **M1 / M2**: per-task any-gold ranks **not committed** (aggregate summary only).
- **No runtime skill-invocation traces** exist for any submission (see `docs/PAPER_VERIFY.md` §C):
  whether `run_skill_script` actually fired during scoring is unverifiable locally.
- **Compaction interval unresolved**: 5 (public Kaggle posts #747186 et al.) vs 15 (live 2026-10-13
  `HARNESS_README` / `AGENTS.md` §1). Wheels hardcode nothing; the scorer's operative value is
  unknowable from installed wheels (see `docs/PAPER_ASSETS.md` §Step 4). This repo's docs use 15.
- **File-recall definitions differ and must not be compared**: Table 2A (0.4350) is mean per-task
  *fraction* over graph-node candidates (`research/kernel_paper_eval/paper_eval.py`); §3.1 (0.7440) is
  binary *any-gold* over all `.py` files on disk (`scripts/t6_run.py` + `_index.py`).
  See `docs/PAPER_VERIFY.md` §A.2 for the three independent causes.
- **v4 symbol recall recomputation**: committed-data recompute gives 0.1488 / 0.2479 / 0.3140 / 0.3554
  (18/30/38/43 of 121 tasks), vs draft Table 2D's 0.157 / 0.231 / 0.306 / 0.364 — off by 1–2 tasks at
  every rank. Both sets exist; the draft was not re-edited.
- **Pooled 31B count is 79/464 = 0.170, not 77/464 = 0.166** (draft §5 misstatement; verified in
  `docs/PAPER_VERIFY.md` §B.2). The 0.89 task-SD covers only the 5-run exp05-family subset.
- **exp11_e4b task count is inconsistent in the ledger** (fixed 3→4 in `research/paper_figs/ledger.csv`
  because 0.06 = floor(100·4/58)/100; older ledgers/docs still say 3).
- **cap-sweep graph files are not committed**, so the "80.9% (313/387) of 1-hop neighborhoods exceed the
  5,000-character tool cap" claim is not re-verifiable from this repo.

## Repo layout

| path | what it is |
|---|---|
| `src/agent_package/` | default declarative ADK bundle used by the notebook builders |
| `src/notebook_lib/`, `src/sections/` | validator + notebook section modules (`tools/build_notebook.py` splices them) |
| `tools/` | bootstrap, resource checks, bundle/notebook verify+build, Kaggle REST client |
| `tracks/e4b_small/` | E4B small-model line: bundles, dedicated verifiers, kernels |
| `kaggle_work/gemma-4-developer-agent/` | competition workspace: bundles, kernel dirs, live competition docs, `RESULTS.md` ledger |
| `ckpt/` | frozen checkpoints: `STATE.md`, `RESULTS.md`, bundles, submission archives |
| `research/` | paper-track experiments: `verified_json/`, `paper_figs/`, `kernel_paper_eval/`, audits, quarantined legacy builders |
| `docs/` | runbook, resource inventory, paper drafts + verification, audits, ledger |
| `scripts/` | figure generation, integrity gate, eval runners, snapshot fetcher |
| `skills/swe-toolkit/` | the released zero-dependency localization/inspection/verification package |
| `bundles/`, `judgeguard_submission/` | experiment agent bundles (exp13/13swe/14/think1024/breakthrough, judgeguard) |
| `assets/` | rendered paper + resource figures (committed PNGs) |
| `eval_results/` | committed per-task eval JSONs (v4 repro, instrument B) |
| `results/` | `claim_toolkit_*.json` — toolkit claim evidence |
| `notes/pulled_txt/` | text dumps of public competitor notebooks |
| `runs/` (gitignored) | pulled kernel outputs / third-party eval CSVs — not redistributed |
| `audit_snapshots/` (gitignored) | older snapshot cache; re-downloadable from Kaggle |
| `eval_snapshots/` (gitignored) | 129 extracted per-task repo trees (42 GB); rebuilt by `scripts/fetch_eval_data.py` |
| `build/` (gitignored) | generated `submission_notebook.ipynb` |

## Data

Competition data is **not redistributed** in this repo. To obtain it (Kaggle account required):

- **Task list + harness docs**: `python tools/check_resources.py` (verifies the 524 competition files
  and 129-task dev set) or `kaggle competitions download -c gemma-4-developer-agent`.
- **Per-task snapshots**: `python scripts/fetch_eval_data.py` (129 snapshots → `eval_snapshots/`).
- **Graphs / embeddings / wheelhouse**: attached inputs of the starter kernel
  [`ryanholbrook/getting-started-gemma-4-developer-agent`](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent)
  and the dataset `metric/gemma-4-developer-agent-wheelhouse`.
- **Third-party notebooks / eval CSVs** (`research/public_notebooks/`, `runs/`): kept locally only.

No LICENSE file exists in this repository yet.

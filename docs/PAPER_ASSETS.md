# PAPER_ASSETS.md — paper assets for the 3,000-word paper (Gemma 4 Developer Agent Paper Track)

Read-only repo work except creating scripts/make_paper_figs.py, research/paper_figs/*, eval_results/instrument_b.json, and this file. No Kaggle submissions, no GPU, no downloads >1 GB, no eval_snapshots/ contents read.

## Produced

| asset | path | description |
|---|---|---|
| ledger CSV (+ score col) | research/paper_figs/ledger.csv | every submission; added `score` column; exp11_e4b tasks_passed fixed 3→4 because score 0.06 = floor(100*4/58)/100 = 0.06 (3 tasks would give 0.05). 3 scored E4B runs; exp_think1024 pending. |
| symbol ablation | research/paper_figs/symbol_ablation.json | v4 recomputed from committed eval_results; v5/v5A/v5AB/v6 draft-only (no per-task symbol re-rancher committed); differences vs draft Table 2D listed. |
| instrument B | eval_results/instrument_b.json | per-task any-gold file ranks for v4 committed (129 tasks); base/v3 null (not reproducible — see below). |
| figures | research/paper_figs/fig{1,2}.png + fig{1,2}_data.csv | 300 dpi, colorblind-safe, value-annotated, readable at half width. Fig3 OMITTED (see step 3). |

## Commands

Generate figures:
```
python scripts/make_paper_figs.py
```
The script asserts `floor(100*tasks/58)/100 == score` for every scored ledger row (passed). Reads ledger.csv / instrument_b.json; writes PNGs + data CSVs.

Regenerate v4 instrument B (requires eval_snapshots/ extracted by scripts/fetch_eval_data.py; ~30 min at ~14 s/task, >5 min, not rerun here — v4 aggregates already confirmed: 0.4186/0.6512/0.7442/0.8295 ≈ 0.419/0.651/0.744/0.829):
```
.venv-harness\Scripts\python.exe scripts/t6_run.py --out eval_results/t6_results_v4_repro.json
```

## Step 1 — LEDGER (done)

All scored rows pass the assertion floor(100*tasks/58)/100 == score:
exp01 3→0.05, exp02 5→0.08, exp03 10→0.17, exp05 12→0.20, exp08 10→0.17, exp10 10→0.17, 57697341 8→0.13, exp12 10→0.17, 57836949 10→0.17, exp_sampling 8→0.13, exp11_e4b 4→0.06 (fixed from 3), e4b-v2 3→0.05, e4b-v4 3→0.05, exp14 9→0.15.
exp_think1024 pending (score null). Unsubmitted/kernel-verified rows have no score.

## Step 2 — INSTRUMENT B (base/v3 NOT reproducible)

v4 per-task any-gold ranks committed to eval_results/instrument_b.json (129 tasks; aggregates match draft Table 2C v4). base (0.419/0.628/0.713/0.829) and v3 (0.419/0.628/0.729/0.822) are historical engine variants NOT implemented in committed code — skills/swe-toolkit/scripts/_index.py (commit 41c2854) is v4 only, and _index.py is not in the allowed-change set. So base/v3 per-task regeneration is infeasible; they are marked null in instrument_b.json. Only v4 is confirmed from committed data.

## Step 3 — SYMBOLS (v5/v6 NOT recomputable; Fig3 omitted)

v4 recomputed from committed eval_results/t6_results_v4_repro.json (121 gold-symbol tasks, bare-name match): Symbol @1 0.1488 (18/121), @3 0.2479 (30/121), @5 0.3140 (38/121), @10 0.3554 (43/121). Draft Table 2D claims 0.1570/0.2310/0.3060/0.3640 — off by 1-2 tasks at every rank (within AGENTS.md §9 ±1-2 task noise, but a real mismatch between committed eval_results and draft text).
v5/v5A/v5AB/v6 per-task symbol re-rankings are NOT committed as runnable code (only draft Table 2D values); bundles/exp14_lean_toolkit/skills/swe-toolkit/scripts/_index.py has v6 file-level score levers (call-site +60, member-over-container +3) but no per-task symbol re-ranker entry point, and _index.py is not modifiable. So v5/v6 cannot be re-run; Fig3 is OMITTED. Numbers in any figure lacking committed per-task data: all v5/v6 symbol values (draft-only), and base/v3 file-recall values (draft-only).

## Step 4 — COMPACTION (reconciled)

Installed packages hardcode nothing: google-adk 1.36.1 apps/_configs.py:61 `compaction_interval: int` (required, no default), :65 overlap, :70 token_threshold=None, :80 retention=None; adk_submission 0.2.13 schema.py:131 only a docstring example; swegemma 0.2.11 config.py:118 default None. Operative value = scorer's external config.
- Live HARNESS_README (2026-10-13 revision, kaggle_work/.../competition/HARNESS_README.md §7.2) + AGENTS.md §2: compaction_interval = 15, overlap_size = 2, token_threshold = 14,336, event_retention_size = 5.
- Public Kaggle discussions conflict: #744692 (Avery Wright, posted ~2026-10-09, PREDATES 2026-10-13 README) debates token_threshold 32,768 vs 14,336; a #744692 comment (~2026-10-22) and #747186 (Whisper Last, ~2026-10-31, POSTDATES 2026-10-13 README) claim interval = 5 / threshold 14,336; #748584 (htn, ~2026-10-25) quotes HARNESS_README as interval = 15 / threshold = 32,768. So the interval=5 public claims postdate the 2026-10-13 README, and no two public artifacts agree with each other or with the live README on all three knobs. The scorer's operative compaction values cannot be independently verified from the installed wheels alone; interval=15 per the live authoritative README is the best-supported value, interval=5 is unverified and possibly refers to the Getting Started notebook rather than the scorer.

## Open problems
1. base/v3 per-task ranks not committed (instrument_b.json null); engine variants not in committed code.
2. M1/M2 per-task any-gold ranks not committed (only aggregate summary).
3. v5/v5A/v5AB/v6 per-task symbol re-rankings not committed; Fig3 omitted.
4. Compaction interval conflict unresolved (live README=15 vs public claims=5; wheels hardcode nothing).
5. exp_think1024 (ref 58149803) pending scoring; outcome unknown.
6. Draft "77/464 = 0.166" is wrong → 79/464 = 0.170 (see PAPER_VERIFY.md §B); SD 0.89 covers only the 5-run exp05-family subset.

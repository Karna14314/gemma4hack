# SESSION_FINAL — paper/notebooks (g4 paper reproducibility)

Branch: `paper/notebooks` (created from `kilo/gallant-hatch-va4`, never `main`)
Date: 2026-11-11
Commit: 19c5583 "paper/notebooks: Task 1 fresh paper kernel + Task 2 noise/MDE notebook"
Push: `origin paper/notebooks` (new branch)
PR draft URL: https://github.com/Karna14314/gemma4hack/pull/new/paper/notebooks
(PR not auto-created: `GH_TOKEN` invalid; `gh` auth fails. Create manually from the URL above and paste this file into the PR body.)

Kaggle auth: bearer token via `tools/kaggle_rest.py` (KAGGLE_KEY=KGAT_…). The `kaggle` CLI (1.7.4.5) 401s (legacy Basic auth); bearer works.

No submissions. No GPU. All notebooks CPU-only, zero internet.

================================================================================
TASK 1 — narisettichaitanya/g4-paper-graph-benchmark (DONE)
================================================================================
- Already public (`isPrivate: false`), CPU-only, no internet, competition source `gemma-4-developer-agent`.
- Pushed a fresh version 23 (`research/kernel_paper_eval/paper_eval.ipynb`, converted from `paper_eval.py`).
- Public URL: https://www.kaggle.com/narisettichaitanya/g4-paper-graph-benchmark
- Kaggle status: COMPLETE, no error, no traceback.
- Runtime: ~246 s (~4.1 min) — matches the paper's "~4 minutes".
- Outputs match the paper:
  - Pooled converged 31B rate: 79/464 = 0.1703 (17.0%), pooled SE = 0.0174.
  - Table 2A M4 file R@5 = 0.435 (R@10 = 0.4587).
  - Table 2C v4 file R@5 = 0.744, R@10 = 0.829.
  - Table 3 playbook overall precision = 32.6% (84/258).
  - 129 tasks evaluated; in-graph 125.
- Authoritative local log: `research/paper_eval_outputs/g4-paper-graph-benchmark.log` (same code as v23).

================================================================================
TASK 2 — noise figure + MDE notebook (DONE)
================================================================================
- Small CPU notebook reading embedded `ledger.csv` data + anonymized leaderboard
  counts (score -> number of teams; no names). Regenerates the noise figure and
  MDE numbers from paper §5.1 / Table 1 notes / fig4.
- New kernel: `narisettichaitanya/g4-paper-noise-mde` v1.
- Public URL: https://www.kaggle.com/code/narisettichaitanya/g4-paper-noise-mde
- Kaggle status: COMPLETE, no error.
- Output: `noise_figure.png` saved to `/kaggle/working`; binomial SE bands and MDE
  printed to the log.
- Regenerated numbers (match paper):
  - Per-run binomial SE = sqrt(p(1-p)/58) for all 14 scored ledger rows.
  - Pooled converged 31B rate = 79/464 = 0.1703, pooled SE = 0.0174.
  - Cross-split SE (n=58, p=0.179) = 0.0503 (~2.9 tasks).
  - Within-split SD (exp05 family [12,10,10,10,10]) = 0.89 tasks.
  - MDE at 80% power (2.802 x SE): cross-split = 0.141 (~8.2 tasks); pooled =
    0.049 (~2.8 tasks).
  - Anonymized top-20: 0.22 (8 teams), 0.24 (11 teams), 0.29 (1 team) ->
    ~13 to ~17 tasks (4-task band); deltas <= 2 tasks (<=0.034) within noise.
  - E0 control: byte-identical exp05 scored 0.20 vs rebuild 0.17 -> 0.20 was a
    high-draw, not a permanent gain.

================================================================================
TASK 3 — public URLs + failures
================================================================================
- URL 1 (Task 1): https://www.kaggle.com/narisettichaitanya/g4-paper-graph-benchmark
- URL 2 (Task 2): https://www.kaggle.com/code/narisettichaitanya/g4-paper-noise-mde
- Failed steps: NONE. Both kernels ran COMPLETE with no error/traceback.
  Notes: kaggle CLI 401s (legacy Basic auth) — worked around with bearer auth via
  tools/kaggle_rest.py. Kaggle output JSON has encoding quirks (raw control chars)
  that break naive json.loads; used control-char stripping to parse.

================================================================================
Process compliance
================================================================================
- Branch `paper/notebooks` from default (`kilo/gallant-hatch-va4`), never `main`.
- Committed at phase end (19c5583). Pushed to origin.
- Verification gate before commit: all touched JSON files (kernel-metadata.json +
  notebooks) validated with json.load; notebook math cross-checked locally against
  paper figures (identical).
- Progress file: docs/PAPER_NOTEBOOKS_PROGRESS.md (maintained, with resume commands).
- No submissions, no GPU.

================================================================================
Resume commands
================================================================================
cd /workspace/app
git checkout paper/notebooks
python3 tools/kaggle_rest.py status narisettichaitanya/g4-paper-graph-benchmark
python3 tools/kaggle_rest.py status narisettichaitanya/g4-paper-noise-mde

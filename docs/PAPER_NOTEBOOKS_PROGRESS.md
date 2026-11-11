# Progress — paper/notebooks session

Branch: paper/notebooks (created from kilo/gallant-hatch-va4, never main)
Date: 2026-11-11
Kaggle auth: bearer token via tools/kaggle_rest.py (KAGGLE_KEY=KGAT_...). CLI `kaggle` 401s; bearer works.

## Phase A — Environment check (DONE)
- kaggle CLI installed but 401s (legacy Basic auth). bearer auth via tools/kaggle_rest.py works.
- Kernel narisettichaitanya/g4-paper-graph-benchmark: public, CPU, no internet.
- Disk: 14G free. Network: OK.

## Phase B — Task 1: g4-paper-graph-benchmark fresh Kaggle run (DONE)
- Kernel already public (isPrivate: false).
- Pushed fresh version 23 (research/kernel_paper_eval/paper_eval.ipynb), status COMPLETE, no error.
- Public URL: https://www.kaggle.com/narisettichaitanya/g4-paper-graph-benchmark
- Runtime: ~246s (~4.1 min), matches paper "~4 minutes".
- Outputs match paper: pooled 79/464=0.1703; Table 2A M4 file R@5=0.435; Table 2C v4 file R@5=0.744/R@10=0.829; Table 3 playbook precision 32.6%; 129 tasks, in-graph 125.
- Authoritative local log: research/paper_eval_outputs/g4-paper-graph-benchmark.log (same code as v23).

## Phase C — Task 2: noise figure + MDE notebook (IN PROGRESS)
- Small CPU notebook reading ledger.csv + anonymized leaderboard counts (score, #teams; no names).
- Regenerates noise figure (binomial SE bands) and MDE numbers.
- Push + run on Kaggle.
- Source data: research/paper_figs/ledger.csv (has score column, all scored rows).

## Phase D — Task 3: report both public URLs + failures (PENDING)

## Commit/push cadence
- Commit + push every 30 min and at each phase end.
- Verification gate before each commit (deps install, scripts run clean, lint, tests for new scripts).
- Draft PR after first audit commit.

## Resume commands
cd /workspace/app
git checkout paper/notebooks
python3 tools/kaggle_rest.py status narisettichaitanya/g4-paper-graph-benchmark

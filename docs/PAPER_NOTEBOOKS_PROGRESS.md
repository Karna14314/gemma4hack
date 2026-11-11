# Progress — paper/notebooks session

Branch: paper/notebooks (created from kilo/gallant-hatch-va4, never main)
Date: 2026-11-11
Kaggle auth: bearer token via tools/kaggle_rest.py (KAGGLE_KEY=KGAT_...). CLI `kaggle` 401s; bearer works.

## Phase A — Environment check (DONE)
- kaggle CLI installed but 401s (legacy Basic auth). bearer auth via tools/kaggle_rest.py works.
- Kernel narisettichaitanya/g4-paper-graph-benchmark: public, v22, CPU, no internet, last run 2026-11-08.
- Disk: 14G free. Network: OK.

## Phase B — Task 1: g4-paper-graph-benchmark fresh Kaggle run (IN PROGRESS)
- Goal: push a fresh version, run on Kaggle, capture runtime/outputs, compare to paper numbers.
- Local source: research/kernel_paper_eval/paper_eval.py + kernel-metadata.json
- Prior log (research/paper_eval_outputs/g4-paper-graph-benchmark.log): ran ~246s, 129 tasks, in-graph 125.
- Paper numbers to match: Table 1 pooled 79/464=0.1703; Table 2A M4 file R@5=0.435; Table 2C v4 file R@5=0.744/R@10=0.829; Table 3 playbook precision 32.6%.

## Phase C — Task 2: noise figure + MDE notebook (PENDING)
- Small CPU notebook reading ledger.csv + anonymized leaderboard counts (score, #teams; no names).
- Regenerates noise figure (binomial SE bands) and MDE numbers.
- Push + run on Kaggle.

## Phase D — Task 3: report both public URLs + failures (PENDING)

## Commit/push cadence
- Commit + push every 30 min and at each phase end.
- Verification gate before each commit (deps install, scripts run clean, lint, tests for new scripts).
- Draft PR after first audit commit.

## Resume commands
cd /workspace/app
git checkout paper/notebooks
python3 tools/kaggle_rest.py status narisettichaitanya/g4-paper-graph-benchmark

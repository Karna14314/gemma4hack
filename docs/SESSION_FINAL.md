# Session Final — Paper Track Complete Benchmarks

Branch: `feat/paper-track-complete-benchmarks`

## Verified benchmark artifacts
- Kernel: `narisettichaitanya/g4-paper-graph-benchmark` v20, status COMPLETE.
- Outputs: `research/paper_eval_outputs/` (`paper_experiments.json`, `PAPER_TABLES.md`, `PAPER_EXPERIMENTS.md`).
- Committed verified tables: `research/PAPER_EXPERIMENTS.md`.

## Key results
- Tasks evaluated: 129; in-graph: 125; docs_src tasks lacking graph nodes: 1.
- 1-hop neighborhood >5000-char cap exceedance: 80.88%.
- M4 `swe_toolkit` file R@10: 0.4587 (all), 0.4734 (in-graph); MRR 0.4354.
- M5 Hybrid RRF file R@10: 0.5701 (all), 0.5883 (in-graph); MRR 0.4332.
- Lexical baseline file R@10: 0.3036.
- Gold patch anatomy: median 1 file, 8 lines added, 2 deleted, 2 hunks; 70.5% single-file, 8.5% new files.
- Playbook audit: 258 triggers, 32.6% precision.
- e4b-v2 (ref 57806053): PENDING, no score yet.

## e4b-v2 poll
`kaggle competitions submissions -c gemma-4-developer-agent`: ref 57806053 status `pending` (submitted 2026-10-30T12:56:30Z). Not submitted today beyond existing.

## Files changed
- `research/kernel_paper_eval/paper_eval.py` (4 experiments)
- `docs/PAPER_TRACK_DRAFT.md` (~2,240 words, submission-ready)
- `research/PAPER_EXPERIMENTS.md` (verified tables)

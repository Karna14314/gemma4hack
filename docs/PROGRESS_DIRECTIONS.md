# PROGRESS_DIRECTIONS.md — Paper Track thesis direction research (branch paper/directions-kilo)

Resume: on branch `paper/directions-kilo` (from `main`, last commit `ed58643` on main).
Files to create (read-only on existing docs/*): docs/PAPER_DIRECTIONS_KILO.md, research/direction_checks/*, docs/PROGRESS_DIRECTIONS.md, docs/SESSION_FINAL.md.
Do NOT modify docs/PAPER_TRACK_DRAFT.md or other existing files.

## Phase status
- Phase 1 RULES: DONE. Source: docs/PAPER_VERIFY.md:106-112 (Kaggle fetched Oct/Nov 2026). Prize cats: Overall Best Paper $15k, Best New Resource $10k, Best New Application $10k. Judges choose category (not submission-time), max 2 writeups, one prize per writeup. Word count: tables+captions count; references+figures do NOT count. Exact 5 criterion names UNVERIFIED (JS-rendered Kaggle pages return only title).
- Phase 2 PUBLIC CONTEXT: PARTIAL. Public notebooks/writeups cited in docs/PAPER_VERIFY.md:114-117 (ryanholbrook starter, jefferyjeromeharris paper writeup, community EDA notebooks; dariushafshar census; prvsiyan; robinamirbahar loop-breaker; discussion #746250 tool ablation). Kaggle discussion pages JS-rendered → UNVERIFIED via direct fetch.
- Phase 3 LEADERBOARD: DONE. Live `/leaderboard/view` via bearer auth -> research/direction_checks/leaderboard_live.csv (top-20 only: 0.29, 0.24x11, 0.22x8). All scores are multiples of 1/58 (0.29~17/58, 0.24~14/58, 0.22~13/58). Full distribution from local snapshot research/public_intel/datasets/board_blocks.csv (2026-10-22, 3430 teams): 0.17 = 555 teams (ranks 612-1166), largest cluster; 0.24=4, 0.22=35, 0.20=148, 0.18=424, 0.15=480, 0.13=351, 0.12=310, 0.10=275, 0.08=219, 0.06=158, 0.05=143, 0.03=109, 0.01=66, 0.00=153. Adjacent rank gaps: within-tier gap 0, between-tier gap 1 task (0.017). Fraction of adjacent gaps <=1 task = 100% (3429/3429 pairs), <=2 = 100%, <=3 = 100%. LB is extremely dense/single-task-noise.
- Phase 4 PRIOR ART: DONE. docs/PAPER_VERIFY.md:92-103 (7 verified refs: SWE-bench ICLR24, SWE-agent NeurIPS24, Agentless arXiv2407/FSE25, LocAgent ACL25 arXiv:2503.09089, RepoGraph ICLR25 arXiv:2410.14684, Wang ICLR26 repository memory, OrcaLoca cited-by-reference). Variance/reliability-specific papers: none verified yet.
- Phase 5 CANDIDATE THESES: IN PROGRESS.
- Phase 6 QUICK CHECKS: NOT STARTED (scripts below).
- Phase 7 RECOMMENDATION: NOT STARTED.

## Key measured numbers (cited)
- Pooled 31B rate = 79/464 = 0.1702 (SE 0.0174) [docs/PAPER_TRACK_DRAFT.md:150-151 on main; PAPER_VERIFY.md:57 corrects draft's "77/464=0.166" -> 79/464=0.170]
- E0 byte-identical control: exp05 0.20 -> E0 0.17 (ref 57836949) [docs/LEDGER.md; docs/AUDIT_E4B_AND_ANCHOR.md]
- Within-split SD 0.89 tasks; cross-split SE 0.0503 (~3.0 tasks)
- E4B line closed: 0.05-0.06 (~3/58), localization-offload falsified [docs/AUDIT_E4B_AND_ANCHOR.md]
- exp14 (31B+SkillToolset 9 tools)=0.15 vs exp05 (6 tools)=0.20/0.17 [docs/LEDGER.md]
- Regime B live indexing File R@5 0.744 vs Regime A 0.4350 (+30.9 pp) [docs/PAPER_TRACK_DRAFT.md:88]
- exp15 pending ref 58183079 sha 7219eb5c [docs/LEDGER.md]

## Next commands
- python3 research/direction_checks/bootstrap_ci.py   (bootstrap CI over Instrument A / leaderboard tasks)
- python3 research/direction_checks/cap_sweep.py      (tool-output-cap sweep on committed graph artifacts)
- python3 - <<'PY' recompute pooled rate/SD from docs/LEDGER.md or eval_results/instrument_b.json

## Last commit
ed58643 (main) — branch point; no commits yet on paper/directions-kilo.

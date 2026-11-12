# PROGRESS_CHECKS2.md — Paper Track checks2 progress (branch paper/checks2)

Resume: branch `paper/checks2` (from `main`, branch point `ed58643`). Last commit pushed.
Existing files read-only. New files only under docs/ and research/direction_checks2/.
No Kaggle submissions, no GPU.

## Phase status (all complete)
- Phase 1 GAP DECOMPOSITION: DONE. Total gap 30.9 pp = (i) recall definition 12.58 pp + (ii) candidate set 18.32 pp. Pure (ii) not isolatable (Instrument A per-task graph ranks not committed). Script: phase1_gap_decomposition.py/json.
- Phase 2 VERIFY/CUT: DONE. VERIFIED: 80.9% (PAPER_TABLES.md:87), 0.895/0.158 (recomputed 34/38 & 6/38), 9/9 torture (recomputed pass), 60,483 files (committed claim). UNVERIFIED: 0/31 and 99.8% (external Discussion #746250, not in committed data).
- Phase 3 TOP TEAMS: DONE. Live LB via bearer auth (HTTP 200): 0.29×1 (Yurnero), 0.24×11, 0.22×8. All ≈ multiples of 1/58. Two downloaded notebooks, neither confirmed top-20. No Kaggle CLI (401s on KGAT).
- Phase 4 DATA TERMS: DONE. Rules page JS-rendered (unreadable). No explicit permission to release derived per-task dataset/gold labels. NOT CONFIRMED.

## Verification gate (passed before commit)
- python3 -m py_compile phase1_gap_decomposition.py phase3_top_teams.py → clean
- phase1_gap_decomposition.py runs, outputs phase1_gap_decomposition.json (gap 30.9 pp)
- phase3_top_teams.py runs, fetches live LB (HTTP 200), outputs phase3_top_teams.json + leaderboard_live.csv

## Files to commit
- docs/PAPER_CHECKS2.md (88 lines, <=150)
- docs/PROGRESS_CHECKS2.md (this file)
- docs/SESSION_FINAL.md (to be written)
- research/direction_checks2/{phase1_gap_decomposition.py,phase1_gap_decomposition.json,phase3_top_teams.py,phase3_top_teams.json,leaderboard_live.csv}

## Resume commands
- python3 research/direction_checks2/phase1_gap_decomposition.py
- python3 research/direction_checks2/phase3_top_teams.py
- python3 -m py_compile research/direction_checks2/*.py

## Branch/PR
- Branch: paper/checks2 (do not commit to main)
- PR: to be opened after first commit; mark ready after gate passes

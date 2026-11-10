# SESSION_FINAL.md — Paper Track thesis direction research (complete)

**Branch:** `paper/directions-kilo` (from `main`, branch point `ed58643`).  
**Last commit:** `52b0aa1` ("Paper Track thesis direction research").  
**PR:** https://github.com/Karna14314/gemma4hack/pull/20 (draft; mark ready after gate passes).  
**Deadline:** Nov 12, 2026 23:59 UTC. No Kaggle submissions made in this session.

---

## Short summary

Completed independent research to recommend the best thesis for the Kaggle "Gemma 4 Developer Agent" Paper Track writeup (3,000 words, deadline Nov 12 23:59 UTC). Ran all 7 phases (rules, public context, leaderboard data, prior art, candidate theses, quick checks, recommendation). **Recommended thesis: T2** — live git-tracked workspace AST indexing + test-path demotion is the largest controllable lever for SWE-agent resolution (+30.9 pp File R@5: 0.4350 Regime A → 0.7440 Regime B), bootstrap CI [0.6667, 0.8140] excludes 0.4350 so the gap is robust. Fallback: T1 (harness mechanics dominate prompt engineering). All existing files kept read-only; only new files created.

---

## Per-phase status & commit hashes

| Phase | Status | Commit | Key result |
|---|---|---|---|
| 1 RULES | complete | 52b0aa1 | Prize cats: Overall Best Paper $15k / Best New Resource $10k / Best New Application $10k (judges choose category; max 2 writeups; one prize each). Word count: tables+captions count; references+figures do not. Exact 5 criterion names UNVERIFIED (JS-rendered). Source: docs/PAPER_VERIFY.md:106-112 |
| 2 PUBLIC CONTEXT | complete | 52b0aa1 | Public notebooks/writeups catalogued (ryanholbrook starter, jefferyjeromeharris paper writeup, dariushafshar census, robinamirbahar loop-breaker, discussion #746250 tool ablation, etc.). Kaggle pages JS-rendered → UNVERIFIED via direct fetch. |
| 3 LEADERBOARD DATA | complete | 52b0aa1 | Live LB top-20 via bearer auth (CLI 401s on KGAT): 0.29, 0.24×11, 0.22×8; all scores ≈ multiples of 1/58. Full snapshot (board_blocks.csv): 0.17 = 555 teams (largest cluster). Adjacent rank gaps 100% ≤1 task (3,415/3,429 gap 0, 14 gap 1) → extreme density. |
| 4 PRIOR ART | complete | 52b0aa1 | 7 verified references (SWE-bench ICLR24, SWE-agent NeurIPS24, Agentless FSE25, LocAgent ACL25, RepoGraph ICLR25, Wang ICLR26, OrcaLoca cited-by-reference). No variance/reliability paper verified; our noise model is our own derivation. |
| 5 CANDIDATE THESES | complete | 52b0aa1 | 4 candidates (T1–T4) scored 1–5 on the five judging criteria. T2 recommended primary, T1 fallback. |
| 6 QUICK CHECKS | complete | 52b0aa1 | bootstrap_ci.py: Regime B v4 File R@5 = 0.7442, 95% CI [0.6667, 0.8140], 0.4350 outside CI → gap robust. cap_sweep.py: 0 committed graph files → 80.9% cap claim NOT re-verifiable here (gap). Pooled rate recomputed 79/464 = 0.1702 (draft already correct on main). |
| 7 RECOMMENDATION | complete | 52b0aa1 | Primary T2 (+swe-toolkit resource → Best New Resource $10k / Best New Application $10k / Best Paper $15k stretch), fallback T1. Section outline + word budget (~2,580 judged text) + 2.5-day schedule. |

---

## Files changed (this branch only)

Created (9 files, 646 insertions):
- docs/PAPER_DIRECTIONS_KILO.md (decision table + 7 phases + recommendation)
- docs/PROGRESS_DIRECTIONS.md (resume file)
- research/direction_checks/bootstrap_ci.py / bootstrap_ci.json
- research/direction_checks/cap_sweep.py / cap_sweep.json
- research/direction_checks/fetch_leaderboard.py / leaderboard_live.csv / leaderboard_live.json

Not created (deferred, per task scope): docs/SESSION_FINAL.md was written below and committed separately.

Existing files: NOT modified (read-only per task rules). docs/PAPER_TRACK_DRAFT.md untouched.

---

## Verification gate results (before this commit)

- Dependencies: all three direction_checks scripts use Python standard library only (json, csv, random, urllib, pathlib, os). No install needed.
- Scripts run clean: `python3 research/direction_checks/bootstrap_ci.py` → CI [0.6667, 0.8140], 0.4350 outside CI. `python3 research/direction_checks/cap_sweep.py` → 0 graph files found (data-absence result, logged). `python3 research/direction_checks/fetch_leaderboard.py` → HTTP 200, top-20 leaderboard saved.
- Lint: `python3 -m py_compile` on all three scripts → ALL COMPILE CLEAN.
- Tests: no test suite exists for these analysis scripts; behavior verified by direct run outputs recorded above. No tests were skipped or weakened.
- Gate passed → commit `52b0aa1` made and pushed to `paper/directions-kilo`.

---

## NOT-verified items

- Exact five Kaggle judging criterion names (JS-rendered pages; docs/PAPER_VERIFY.md:112).
- Writeup-editable-before-deadline (not confirmed on fetched pages).
- "80.9% of 1-hop neighborhoods exceed the 5,000-char tool cap" claim — not re-verifiable from committed files (cap_sweep.json = 0 files); sourced to earlier-session AGENTS.md §2 Regime A. Re-measure or soften in the writeup.
- Public notebook/discussion page bodies (JS-rendered; only titles fetchable).
- Any runtime skill-invocation traces for e4b_v4/exp14 (docs/PAPER_VERIFY.md:C.2 = "NONE").
- Writeup word count < 3,000 judged text (to be confirmed when pasted into the portal; tables count).

---

## Known gaps

- base/v3 per-task ranks not committed (only v4); engine variants not in committed code (docs/PAPER_ASSETS.md:35).
- Committed graph artifacts absent; 80.9% cap claim rests on earlier-session measurement.
- exp15_zero_schema_hybrid (ref 58183079) still PENDING on the main track — not part of this paper task, do not submit new main-track bundles.
- PR description not yet populated with SESSION_FINAL.md content (see resume instructions).

---

## Resume instructions

- Branch: `paper/directions-kilo` (do not commit to `main`).
- Last commit: `52b0aa1` (pushed).
- PR: https://github.com/Karna14314/gemma4hack/pull/20 (draft; paste this SESSION_FINAL.md into the PR description, then mark ready for review after the verification gate passes — gate already passed).
- Re-run checks: `python3 research/direction_checks/bootstrap_ci.py`, `python3 research/direction_checks/cap_sweep.py`, `python3 research/direction_checks/fetch_leaderboard.py`, then `python3 -m py_compile research/direction_checks/*.py`.
- Next work: integrate T2/T1 into the Paper Track writeup, confirm word count < 3,000 (tables count), submit via Kaggle Paper Track portal before Nov 12 23:59 UTC.

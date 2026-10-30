# SESSION FINAL — feat/e4b-v2 (2026-10-30)

## Summary
Built e4b-v2 bundle (temp 0.1 + imperative prompt <=2500 chars), submitted once (ref 57806053, pending). Completed research R1-R5. Branch feat/e4b-v2, PR #13 (draft).

## Step 0 outcome
No unfinished cleanup found on this branch (main clean, no exp13 conflict artifacts). Created branch feat/e4b-v2 from main.

## Per-phase status
- Phase 1 (build e4b-v2): DONE. commit d33c321.
- Phase 2 (gates): DONE. verify_bundle_e4b_v2 PASS; verify_notebook_e4b_v2 PASS; gate one-liner tested.
- Phase 3 (submission): DONE. ref 57806053 submitted 2026-10-30, pending.
- Phase 4 (research R1-R5): DONE. files in research/.

## Commit hashes
- d33c321 feat(e4b): build e4b-v2 bundle (temp 0.1 + imperative prompt) and research R1-R5

## Files changed (key)
- tracks/e4b_small/bundles/e4b_v2/* (agent.yaml identical to baseline, sampling temp 0.1, system.md 2440 chars)
- tracks/e4b_small/bundles/e4b_v3/* (prepared, thinking_budget 1024, not submitted)
- tracks/e4b_small/verify_bundle_e4b_v2.py, verify_notebook_e4b_v2.py
- tracks/e4b_small/kernel_e4b_v2_submit/* (notebook + metadata)
- research/SMALL_MODEL_PRIZE.md, SKILL_CONTRACT.md, BUDGET_LIMITS.md, E4B_FAILURE_ANALYSIS.md, GEMMA4_SAMPLING.md
- docs/LEDGER.md

## Verification commands and results
- python3 tracks/e4b_small/verify_bundle_e4b_v2.py -> E4B V2 VERIFY_BUNDLE: ALL CHECKS PASSED (prompt 2440 chars)
- python3 tracks/e4b_small/verify_notebook_e4b_v2.py -> LOCAL E4B NOTEBOOK VERIFICATION ALL CHECKS PASSED
- Gate one-liner tested in scratch repos: no changes, changed .py, new untracked, new ignored, syntax error, filename with spaces, zero .py, only test/config -> all passed.
- Bundle sha256 (submission.zip): 5881be16cb3ba6761b4b2d724510ffbb44c37a47c9b5a5f66d1701fc0a5b312d

## Paired A/B eval
NOT RUN. g4-paired-devset-eval is hardcoded to 31B model path and bundles exp05/exp10; requires 4x L4 GPU. This CPU instance cannot run it. Not blocking submission.

## Submission refs and quota
- e4b-v2 ref 57806053 (pending), quota used 1/1 today. e4b-v3 not submitted (daily cap reached).
- Baseline 57777888 scored 0.06.

## Decision rule
Pending scoring. Once 57806053 completes: >=0.10 promising (rerun to confirm); 0.07-0.09 inconclusive; <=0.06 direction not helping, ablate each change.

## NOT-verified items
- e4b-v2 score (pending).
- Paired A/B E4B (could not run).
- eval_config.yaml read during scoring (UNKNOWN).
- top_k forwarding by harness (UNKNOWN).

## Known gaps
- v2 keeps 8 min/28 calls (16h worst case > 12h global cap) — risk; recommend 5 min/40 calls for next experiment.
- temperature 0.1 vs Google recommended 1.0 (R5) — not applied (authorization).
- e4b-v3 prepared but not submitted.

## Next steps
- Poll 57806053 ~every 20 min.
- If promising: submit e4b-v3 (thinking_budget 1024) next day.
- If <=0.06: ablate temperature vs prompt separately.
- Finish paper-track draft by Nov 12.

## Resume instructions
git checkout feat/e4b-v2 && git pull

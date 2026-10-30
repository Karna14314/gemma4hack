# LEDGER — e4b-v2

## Baseline bundle (57777888)
- Bundle: tracks/e4b_small/bundles/exp11_e4b
- Model: gemma-4-e4b-it-qat-w4a16-ct
- Score: 0.06 (ref 57777888, complete)
- File hashes:
  - agent.yaml: 2d25f715647c996542528d843cc6c9fdb7938aee86bcf559143d47ada20128fd
  - configs/sampling.yaml: 571a934e89911734927533f1d36cbcc7b8d493592febe63b217e911cf7ed4926
  - eval_config.yaml: 916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531
  - prompts/system.md: ab4fda662643c26f920b106986ac9858f9e041e8c6d0a25f74255aff635c663d

## e4b-v2 bundle
- Bundle: tracks/e4b_small/bundles/e4b_v2
- Diff vs baseline (57777888): only configs/sampling.yaml (temperature 0.2 -> 0.1) and prompts/system.md (rewritten, 2440 chars). agent.yaml and eval_config.yaml byte-identical.
- Unified diff recorded in commit/PR.

## Submission
- Ref: 57806053
- Kernel: narisettichaitanya/g4-e4b-v2-small-agent-submit v1
- Bundle sha256 (submission.zip): 5881be16cb3ba6761b4b2d724510ffbb44c37a47c9b5a5f66d1701fc0a5b312d
- Time: 2026-10-30 (pending scoring)
- Status: pending

## Gate results
- verify_bundle_e4b_v2.py: ALL CHECKS PASSED (prompt 2440 chars)
- verify_notebook_e4b_v2.py: LOCAL E4B NOTEBOOK VERIFICATION ALL CHECKS PASSED
- Final gate one-liner: tested in scratch repo covering no changes, changed .py, new untracked file, new ignored file, syntax error, filename with spaces, zero .py changes, only test/config files changed. All passed.

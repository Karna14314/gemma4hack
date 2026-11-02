# SUBMISSION RUN — e4b_v4_swe_toolkit

Branch: feat/e4b-v4-submit
Base commit: a6405db exp14_lean_toolkit + e4b_v4_swe_toolkit
Bundle: tracks/e4b_small/bundles/e4b_v4_swe_toolkit
Competition slug: gemma-4-developer-agent

## Phase 0 — Audit
- Kaggle auth: KAGGLE_API_TOKEN set from KAGGLE_KEY (KGAT_ bearer). check_resources.py: all required resources present.
- Submissions: latest 57836949 (2026-10-31) COMPLETE; no pending; nothing submitted 2026-11-02 UTC.
- Disk: ~14G free.
- Venv: .venv-harness created (Python 3.13), wheels installed.

## Resume commands
- git checkout feat/e4b-v4-submit
- .venv-harness/bin/python tracks/e4b_small/verify_bundle_e4b_v4.py

## Bundle file sha256 (pre-build)
- agent.yaml: 91c269ba846c6eb1c27106aa4a06598f3b687cd3a6f4affcf83018554d4b4fc8
- configs/sampling.yaml: 46f440a86c78adac8226ce4f91ba7e4edd3db623fa023b5b5f00c255338a88d0
- eval_config.yaml: 8228dce2ac49910cb4076fc8d55b7747be5269660461eaf9601d97a7450540fb
- prompts/system.md: 5f5eaf19dd2b7244bf4980f12b8d8be0a29c19969a6d486db3a1be94de96d685
- skills/swe-toolkit/SKILL.md: 65d175bc403ee72fc1daacc3867f19b3033ab0a7698fb0c43a8491b6f5540134
- scripts/_guard.py: 9bceeee0fb93d79f3b8b97ef214d08177cdf0bc03bb3e1b5ccb0137257589bc2
- scripts/_index.py: a484e514ff59037768299cff4e285dbd4cf5fdaa9212c7808bf00fadcc7b19dd
- scripts/_knowledge.py: 095feca9cba8a59e5fe897c5993e0aac706e8d9e1a9d7ba3b59fc7fb2a79738d
- scripts/_verify.py: 61d8616c3125f1127aa675b45dc39cf0f1c29610712e676be9aba8a33aae483f
- scripts/swe.py: 65648a8a869e296c5c230151ec578dc3b73cbcab21ce5aa0527a04eb7a01dec9

## Phase 1 — Gates
- verify_bundle_e4b_v4.py: ALL CHECKS PASSED (prompt 2116 chars, 10 files, skill hashes pinned to upgraded engine)
- build_notebook.py: wrote build/e4b_v4_submission_notebook.ipynb (17 cells)
- verify_notebook.py: ALL CHECKS PASSED; real harness compile_submission builds agent (7 tools); zip sha256 8a179b8af032ca97dbc64f54f0dbd3721434a10765e5c01167f36250822329a0
- E4B-only model: gemma-4-e4b-it-qat-w4a16-ct; zero 31B; 7 tools; skill dir skills/swe-toolkit (lowercase); SKILL.md 2374 bytes

## Phase 2 — Recall check (129 tasks)
Metric: task-level hit@k (fraction of tasks with >=1 gold file in top k).
Baseline full-issue (given): 0.419/0.651/0.744/0.829 @1/3/5/10.
Capped variants:
- first250: 0.341/0.543/0.659/0.806
- last250:  0.318/0.504/0.589/0.760
- keyword:   0.403/0.682/0.760/0.837
Best capped @5 = keyword 0.760 >= 0.694 threshold. PASS (no stop).
Note: full-issue recomputed hit@ = 0.395/0.612/0.674/0.822 (slightly below given baseline; likely engine/version drift).

## Phase 3 — Submit
- Kernel: narisettichaitanya/g4-e4b-v4-small-agent-submit v1 (status COMPLETE, no traceback)
- Pulled zip sha256 matches local build: 8a179b8af032ca97dbc64f54f0dbd3721434a10765e5c01167f36250822329a0
- Submission ref: 57889741
- Timestamp: 2026-11-02T00:50:17Z
- Status: PENDING (polled once)

## Phase 4 — Finalize
- docs/SESSION_FINAL.md to be written.

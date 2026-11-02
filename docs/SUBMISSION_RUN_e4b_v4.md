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

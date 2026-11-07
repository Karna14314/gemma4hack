# SUBMISSION RUN — exp14_lean_toolkit

Branch: feat/exp14-lean-toolkit-submit
Base commit: 8a0f927 (merge PR #17)
Bundle: bundles/exp14_lean_toolkit
Competition slug: gemma-4-developer-agent

## Phase 0 — Audit
- Kaggle auth: KAGGLE_API_TOKEN (KGAT_ bearer). check_resources.py: all required resources present.
- Submissions: latest 57889741 (2026-11-02) COMPLETE; no pending; nothing submitted 2026-11-03 UTC before this run.
- Disk: ~14G free. Venv .venv-harness (Python 3.13), wheels installed.

## Bundle file sha256 (pre-build)
- agent.yaml: 400ac082c121c1910e7393693bbc573ecf8ad5fd8aad4a300bd9a02e45a269ee
- configs/sampling.yaml: 571a934e89911734927533f1d36cbcc7b8d493592febe63b217e911cf7ed4926
- eval_config.yaml: 916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531
- prompts/system.md: 938fea16d7e340b4241afe696b839c8f22aef25e0bbf0eb9d5699aa8e2bcd052
- skills/swe-toolkit/SKILL.md: 65d175bc403ee72fc1daacc3867f19b3033ab0a7698fb0c43a8491b6f5540134
- scripts/_guard.py: 9bceeee0fb93d79f3b8b97ef214d08177cdf0bc03bb3e1b5ccb0137257589bc2
- scripts/_index.py: a484e514ff59037768299cff4e285dbd4cf5fdaa9212c7808bf00fadcc7b19dd
- scripts/_knowledge.py: 095feca9cba8a59e5fe897c5993e0aac706e8d9e1a9d7ba3b59fc7fb2a79738d
- scripts/_verify.py: 61d8616c3125f1127aa675b45dc39cf0f1c29610712e676be9aba8a33aae483f
- scripts/swe.py: 65648a8a869e296c5c230151ec578dc3b73cbcab21ce5aa0527a04eb7a01dec9

## Phase 1 — Harness audit
- docs/SKILL_EXEC_AUDIT.md written with file:line evidence.
- Integration test: /tmp/scratchpad/integration_test.py — all 5 assertions passed (cold locate OK + gold file; SESSION STATE header; verify catches SyntaxError in 0.4s; dict/malformed args; tool declarations saved).

## Phase 2 — Gates
- verify_bundle.py --bundle bundles/exp14_lean_toolkit: ALL CHECKS PASSED.
- build_notebook.py: wrote build/exp14_submission_notebook.ipynb (17 cells).
- verify_notebook.py: ALL CHECKS PASSED; single model gemma-4-31b-it-qat-w4a16-ct; zip sha256 02fd7e818320c186ac57d9f3ca7b92f5413b96a00799899bb1cb9c8d91846ab8.
- Prompt = exp05 verbatim + toolkit block (306 chars <= 350).

## Phase 3 — Submit
- Kernel: narisettichaitanya/gemma4-devagent-exp14-lean-toolkit v1; status COMPLETE; no traceback.
- Pulled zip sha256 matches local build: 02fd7e818320c186ac57d9f3ca7b92f5413b96a00799899bb1cb9c8d91846ab8.
- Submission ref: 57933618
- Timestamp: 2026-11-03T05:02:14.867Z
- Status: PENDING (polled once)

## Pre-registered rule vs 31B pool (mean 10.3 tasks)
- >=13 tasks (>=0.22): real effect; keep as final 31B slot.
- 9-12 tasks: null; toolkit has no effect → stop toolkit work.
- <=8 tasks: regression.

## Resume commands
- git checkout feat/exp14-lean-toolkit-submit
- .venv-harness/bin/python tools/verify_bundle.py --bundle bundles/exp14_lean_toolkit
EOF
echo written
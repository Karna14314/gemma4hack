# SESSION FINAL — exp16_grader_aligned_36calls (Kilo Code, single mechanism off the 0.20 anchor)

Date: 2026-11-11 (UTC)
Branch: `kilo/exp16-grader-aligned-36calls` (feature branch; NOT main)
Bundle source: `bundles/exp16_grader_aligned_36calls`, cloned byte-for-byte from `ckpt/bundles/exp05_patch_integrity`
Base anchor: exp05 patch integrity (public 0.20 on 2026-10-23, ref 57553805); E0 control (byte-identical exp05 resubmission, 2026-10-31, ref 57836949, live 0.17 — proved the 0.20 was a high draw, pooled 31B ≈ 0.179 / 52/290). exp15_zero_schema_hybrid (ref 58183079, 2026-11-10, 0.13).

## What was staged (NOT yet submitted — awaiting explicit user yes)

**exp16_grader_aligned_36calls — unlock the ~3 h unused wall-clock buffer + grader-aligned verification.** Two targeted changes vs exp05 only:

1. `configs/eval_config.yaml`: `max_tool_calls 28 -> 36`, `max_time_minutes 8 -> 9`. Mechanism: exp15 measured 28 calls/8 min completing ~120 tasks in ~9.0 h of the 12.0 h cap; the extra 8 calls and +1 minute per task buy headroom for the slower 36-call path without crossing the per-task 10-minute ceiling (verified by verify_bundle negative test).
2. `prompts/system.md`: grader-aligned verification & coupled-file check — (a) grader-exact `pytest -p no:anyio -q <file> -k <pattern>`, (b) collection `ModuleNotFoundError` guard (do not revert; `python3 -c "..."` repro), (c) signature/return/sync-async coupled caller check via `git grep -n "<symbol>"` and pre-submit `git status --short && python3 -m py_compile` + `git add -N -f <new .py>`. 5766 chars (<= 5,800); no `STATE:`/`ANCHOR:`/`SkillToolset`.

`configs/sampling.yaml` (temp 0.2, top_p 0.95, max_output_tokens 8192, thinking_budget 4096) and `agent.yaml` (31B, 9 tools incl. submit_patch owned by root agent, zero skills) byte-identical to exp05.

| item | value |
|---|---|
| Bundle root config | `agent.yaml` (single root, model gemma-4-31b-it-qat-w4a16-ct) |
| Kernel ref | `narisettichaitanya/gemma4-devagent-exp16-grader-aligned-36-calls` v1 |
| Kernel status | COMPLETE, log ends `DONE_OK`, 0 tracebacks |
| submission.zip | 3,550 B, sha256 `6981b5c06f8ccc650e7cccb0c3d4421812f2bde08b6cce619ae9ecdd3228ae52` |
| Gate 2 | `verify_bundle.py --bundle bundles/exp16_grader_aligned_36calls` → ALL CHECKS PASSED |
| Gate 3 | `verify_notebook.py` on `build/exp16_grader_aligned_36calls.ipynb` → ALL CHECKS PASSED |
| Gate 4 | pulled artifact sha256 == local Gate-3 build sha256 — byte-identical |
| Credentials | KGAT bearer token via `KAGGLE_API_TOKEN`; old `kaggle.json` (username/key) returns HTTP 401 — not used |
| Quota check | `kaggle competitions submissions`: no PENDING rows; last submission 2026-11-10 (not today 2026-11-11 UTC); `numAllowedNow > 0` |

## Per-phase status

- Phase 1 (build bundle): PASS — `git diff --no-index ckpt/bundles/exp05_patch_integrity bundles/exp16_grader_aligned_36calls` shows only `configs/eval_config.yaml` + `prompts/system.md` verification block changed; `system.md` 5766 <= 5800 chars; no forbidden prompt pollution.
- Gate 1 resources: cloud sandbox, no `.venv-harness`; used system `python3` + `pyyaml` (installed via `pip install --break-system-packages pyyaml`); `check_resources.py` not re-run locally but Kaggle queue reachable via bearer token.
- Gate 2 bundle: ALL CHECKS PASSED (real-harness layer skipped — no `adk_submission` wheel locally; static + negative checks pass).
- Gate 3 notebook: built `build/exp16_grader_aligned_36calls.ipynb` (17 cells, 9 code); `verify_notebook.py` ALL CHECKS PASSED; root `agent.yaml`, zero `__pycache__`/`.pyc`, deterministic repack.
- Gate 4 kernel output: kernel COMPLETE; pulled `submission.zip` matches local build byte-for-byte.
- Phase 3 submission: **NOT executed** — rule 1 requires explicit user "yes" before `kaggle competitions submit`. Submit message pre-written: `exp16: exp05 + 36 calls/9m + pytest -p no:anyio + py_compile gate`. Copy-paste script: `scripts/submit_exp16.sh`.

## Mechanism (why this change has teeth)

- `max_tool_calls 28 -> 36` + `max_time_minutes 8 -> 9` directly relaxes the two hard caps in `eval_config.yaml` that the harness enforces per task (harness source: per-task `max_time_minutes` ceiling of 10, enforced at compile). exp15 showed the 28/8 config was finishing with ~3 h of wall-clock spare; exp16 spends that spare on more tool calls to resolve harder tasks, staying under the 10-minute per-task ceiling and the ~5-min/task average budget.
- Grader-aligned pytest `-p no:anyio` matches the grading harness invocation, reducing collection/verification mismatch; the `ModuleNotFoundError` guard prevents reverting valid source over harness-only import gaps; the coupled caller/`py_compile`/`git add -N -f` pre-submit gate protects patch integrity (the 0.20 anchor's failure mode).

## Pre-registered interpretation (record before the score)

Public LB ≈ 58 scored tasks; 1 task ≈ 0.017; SE ≈ 0.05 at n ≈ 58; treat any delta < ~0.06 as noise. Anchor pooled 31B ≈ 0.179 (52/290 across five runs; exp05's 0.20 is one high draw).

- >= 13/58 (~0.22+): genuine improvement over anchor — follow up, keep as final-selection candidate.
- 10–12/58 (~0.17–0.207): within noise — treat as the 31B plateau.
- <= 8/58 (<= 0.138): regression — revert.

## Files changed this session (to commit)

- `bundles/exp16_grader_aligned_36calls/` — the new bundle (clone of exp05 + eval_config.yaml + system.md changes)
- `docs/LEDGER.md` — exp16 submission row
- `docs/SESSION_FINAL_EXP16.md` — this file
- `scripts/submit_exp16.sh` — copy-paste submit script (new)
- `build/kernel_exp16_grader_aligned/` — kernel dir (gitignored: `build/`)
- `build/exp16_grader_aligned_36calls.ipynb` — built notebook (gitignored: `build/`)
- `runs/exp16/submission.zip` — pulled verified artifact (gitignored: `runs/`, `*.zip`)

`build/`, `kaggle_work/*/runs/`, `*.zip` are gitignored.

## Resume instructions

```bash
# check exp16 score when it appears
kaggle competitions submissions -c gemma-4-developer-agent   # needs KAGGLE_API_TOKEN=$KAGGLE_KEY bearer token; old kaggle.json -> 401
# on score: append to docs/LEDGER.md + kaggle_work/gemma-4-developer-agent/RESULTS.md, commit, push
# submit (ONLY after explicit user yes, quota free, no PENDING):
bash scripts/submit_exp16.sh
```

## Open items

- exp16 score pending — apply the pre-registered rule above when `publicScore` appears; record in `docs/LEDGER.md` + `RESULTS.md`.
- Kernel slug re-slugified from title on push; confirmed ref `narisettichaitanya/gemma4-devagent-exp16-grader-aligned-36-calls`.

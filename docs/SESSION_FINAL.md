# SESSION FINAL — exp_think1024 submission (Kilo Code single-change bundle)

Date: 2026-11-09 (UTC)
Branch: `main` (working repo) — bundle source: branch `kilo/steep-blossom-hio`, commit `54c63bf`
Base: the 0.20-anchor artifact `ckpt/exp05/submission.zip` lineage; anchor bundle
`kaggle_work/gemma-4-developer-agent/bundles/exp05_patch_integrity` (E0 control proved the
0.20 was a draw, pooled 31B ≈ 0.166).

## What was submitted

**exp_think1024 — closing the thinking-budget question.**
Bundle `kaggle_work/gemma-4-developer-agent/bundles/exp_think1024` (root mirror
`bundles/exp_think1024`), single change vs exp05: `configs/sampling.yaml`
`thinking_budget: 4096 → 1024`. Authored by Kilo Code; local verification + submission
by OpenCode.

| item | value |
|---|---|
| Submission ref | **58149803** |
| Submitted at | 2026-11-09T03:27:31Z |
| Status | pending (scoring turnaround historically 1–2 days) |
| Kernel | `narisettichaitanya/gemma4-devagent-exp-think1024` v1 (scriptVersionId 367147645) |
| Artifact | `submission.zip`, 3,403 B, sha256 `5d80bac751b9ae2218e5bffa32bc7078f8c9a3dd9abc4b21edf44d2b50ad7082` |
| Compiled | root `swe_agent`, model 31B, tools 9, `max_output_tokens` 8192, thinking budget 1024 |
| Quota state after | 1/day used; pending row blocks the next submission until scored |

The user pre-authorized a **conditional** submission: payload proof positive + Gates 2–3
pass. All conditions were verified at call time (no pending rows, nothing submitted
2026-11-09 UTC, gates passed, Gate-4 pulled artifact byte-identical).

## Mechanism (why this change has teeth)

The thinking budget is **engine-enforced, not prompt text**: the bundle's
`generate_content_config` crosses into the served engine as top-level vLLM
`thinking_token_budget` (litellm `extra_body`; `protocol.py:183`, forwarded into
`SamplingParams` at `protocol.py:519`), and vLLM 0.19.1 enforces it independently of
`max_tokens` via `ThinkingTokenBudgetLogitsProcessor`
(`v1/sample/logits_processor/builtin.py:294`, forced end-of-think at `builtin.py:524-552`),
under the scorer's `reasoning_parser='gemma4'`. Payload proof captured at the exact
`model.llm_client.acompletion` call site (`google/adk/models/lite_llm.py:2467`) via
`scripts/probe_thinking_budget.py`; payloads for exp05 vs exp_think1024 differ only in
`thinking_token_budget` (4096 vs 1024). STOP GATE (budget-dropped/no-op path) did **not** trigger.

## Per-phase status

- Phase 0/1 wheel+env audit: PASS — `docs/ENV_AUDIT.md` (google-adk 1.36.1,
  google_genai 2.11.0, litellm 1.106.6, adk_submission 0.2.13, swegemma 0.2.11,
  adk-eval-core 0.1.0; vLLM not local — verified from upstream tag `v0.19.1`;
  offline runner: `swegemma eval --sandbox subprocess`; `scripts/repro_harness_traps.py` 5/5 PASS).
  Gate 1 `check_resources.py` exit 0, docs hashes unchanged.
- Phase 2 payload proof: PASS (above; artifacts `build/probe_payloads/*.json`,
  sha256 `7BEAE700…` / `060503DF…`).
- Gate 2: `verify_bundle.py --bundle bundles\exp_think1024` → ALL CHECKS PASSED
  (deterministic pack digest `5d80bac751b9ae22`).
- Gate 3: `build/exp_think1024.ipynb` (17 cells) → `verify_notebook.py` ALL CHECKS PASSED.
- Gate 4: kernel COMPLETE, log ends `DONE_OK`, no traceback; pulled output
  (`kaggle_work/gemma-4-developer-agent/runs/exp_think1024/`) matches local build byte-for-byte.
- Phase 3 submission: DONE (ref 58149803). CLI trap note: `kaggle competitions submit`
  returned HTTP 400 (the JSON-vs-multipart trap, `tools/kaggle_rest.py` docstring);
  submitted via `tools/kaggle_rest.py submit`.
- Phase 4 finalize: this file; ledger rows in `kaggle_work/gemma-4-developer-agent/RESULTS.md`
  (incl. the 2026-10-31→11-07 score catch-up) and `docs/LEDGER.md`; paper updated
  `docs/PAPER_TRACK_DRAFT.md` (engine-enforcement finding, E0-control statistics,
  falsified E4B offload prediction — 2,997 words, under the 3,000 limit).

## Pre-registered interpretation (record before the score)

Public LB ≈ 58 tasks; 1 task ≈ 0.017; SE ≈ 0.05; pooled converged-config 31B ≈ 0.166
(8 scored runs: 0.20, 0.17×5, 0.15, 0.13; E0 control proved exp05's 0.20 non-reproducible).

- ≥13/58 (≈0.22+): real win over the anchor — follow up with a budget sweep (2048?) and
  keep as a final-selection candidate.
- 9–12/58 (0.155–0.207): null — budget reduction is score-neutral; treat 0.17-cluster as
  the 31B plateau, close the question.
- ≤8/58 (≤0.138): regression — thinking depth matters at 31B; revert and never reduce
  budget below 4096 again without a planned-parallel sweep.

## Files changed this session (to commit)

- `bundles/exp_think1024/`, `kaggle_work/gemma-4-developer-agent/bundles/exp_think1024/` — the bundle (synced from `kilo/steep-blossom-hio`)
- `kaggle_work/gemma-4-developer-agent/experiments/exp_think1024/` — kernel dir (`kernel-metadata.json` + `submission_notebook.ipynb`)
- `scripts/probe_thinking_budget.py` — payload-proof script (works standalone with `.venv-harness`)
- `docs/ENV_AUDIT.md` — wheel/env audit + payload proof (new)
- `docs/LEDGER.md` — exp_think1024 submission row
- `kaggle_work/gemma-4-developer-agent/RESULTS.md` — score catch-up + experiment section
- `docs/PAPER_TRACK_DRAFT.md` — finding + statistics updates (deadline 2026-11-12)
- `docs/SESSION_FINAL.md` — this file

`build/`, `kaggle_work/*/runs/`, `*.zip` are gitignored (payload JSON evidence under
`build/probe_payloads/` referenced by hash in `docs/ENV_AUDIT.md`).

## NOT-verified / open items

- Score pending — apply the pre-registered rule above when `publicScore` appears; record
  in `RESULTS.md` + `docs/LEDGER.md`.
- Paper track (2026-11-12): draft content is current, but the final PDF/form has not been
  cut in this session; if exp_think1024's score arrives before then, fold it into §2.2/Table 1.
- Next single-change candidates off the 0.166 pooled anchor (mechanism-first, one variable):
  thinking budget sweep (2048) only if exp_think1024 scores ≥13; `max_time_minutes` 8→9
  with the timing-buffer pattern; `include_thoughts` toggle (compaction pressure).
- Daily slot free again only after 58149803 completes.

## Resume instructions

```powershell
# check score
.venv-harness\Scripts\python.exe tools\kaggle_rest.py submissions gemma-4-developer-agent
# or: kaggle competitions submissions -c gemma-4-developer-agent
# on score: append to kaggle_work/gemma-4-developer-agent/RESULTS.md + docs/LEDGER.md, commit, push
```

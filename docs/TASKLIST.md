# Tasklist — 31B line

Live queue. **The first unchecked task is the only one in progress.** Each task names its
gate and its done-when so it can be closed without re-deriving context.

Updated 2026-10-30. Design rationale: `docs/SKILLS_ARCHITECTURE.md`. Evidence:
`docs/TASK_CLASSIFICATION.md`, `docs/AUDIT_SNAPSHOTS.md`.

## State

| item | value |
|---|---|
| best public score | **0.20** (`exp05_patch_integrity`, ref `57553805`, 31B) |
| pooled 31B estimate | **0.179** (52/290 across five runs) — see `docs/AUDIT_E4B_AND_ANCHOR.md` |
| pending submission | **`57836949`** E0 control, byte-identical exp05 (2026-10-31) |
| E4B line | **closed** — 0.05–0.06, about 3/58 tasks; not a competition entry |
| submission days left | 32 (2026-11-01 → 2026-12-02) |
| final selections | 2 (`numScoredSubmissions: 2`) |
| measurement instrument | `research/kernel_devset_eval/` = `KernelWorkerStatus.ERROR` |
| paper deadline | 2026-11-12 23:59 UTC |
| main deadline | 2026-12-02 23:59 UTC |

---

## T0 — E0 control  *(submitted 2026-10-31, ref `57836949`, awaiting score)*

Byte-identical resubmission of the 0.20 artifact, to separate 0.20 from 0.17.

**Why it is not simply "re-run the frozen bundle".** `ckpt/bundles/exp05_patch_integrity`
carries 36 extra chars (`## The issue` + `{problem_description}`) that were added *after*
the 0.20 submission. The true artifact is `ckpt/exp05/submission.zip`, sha256
`2ba7f9b118ea1837…`. The control was rebuilt from that archive; the kernel output is
byte-identical. Full evidence: `docs/AUDIT_E4B_AND_ANCHOR.md` §Audit E.

**Kernel.** `narisettichaitanya/g4-e0-exp05-control-resubmit` v1 (slug re-derived from the
title, not the requested id).

**Done when.** Score recorded in `RESULTS.md`, and the branch below is chosen.

| E0 result | reading | next |
|---|---|---|
| ≈ 0.20 | anchor real; 0.17 is the low tail | E1 must beat 0.20 |
| ≈ 0.17 | anchor is 0.179 pooled; 0.20 was noise | prompt line exhausted; E1 vs 0.18, paired instrument required |
| ≤ 0.13 | environment drift, not the bundle | stop the ladder, re-audit resources and artifact |
| ≥ 0.24 | upside variance larger than modelled | repeat before concluding |

---

## T1 — Repair the paired dev-set eval kernel  ← start here

**Why.** The LB is ~58 tasks; one task ≈ 0.017 and noise ≈ 0.05. A +0.03–0.07 effect is 2–4
tasks, which a single LB run cannot resolve. Paired per-task outcomes on 24 tasks can, and
they cost no submission slot. Every task below is judged through this instrument, so it is
repaired before any bundle work is called done.

**Steps.**

1. `kaggle kernels status narisettichaitanya/g4-paired-devset-eval` — confirm it is still
   `ERROR`.
2. Get the log. The REST call `GetKernelSessionOutput` returned HTTP 404, so use
   `kaggle kernels output narisettichaitanya/g4-paired-devset-eval -p runs\paired` and read
   the log file it writes.
3. Classify the failure into **exactly one** bucket, then fix only that:
   - import/API drift against `swegemma 0.2.11` / `adk-submission 0.2.13`
   - dataset mount (competition or wheelhouse not attached to the kernel)
   - vLLM startup / GPU memory on the 4×L4 box
   - bundle path inside the kernel (`bundles/exp05_patch_integrity` not found)
   - task list path (`tasks.jsonl` / `eval_24_tasks.json`)
4. Push, re-check status. **One fix per push.**
5. Smoke one task, then run all 24.
6. Record the paired table in `RESULTS.md` as row `INST-1`.

**Done when.** Status `COMPLETE`, no traceback, and an artifact with per-task pass/fail for
both arms.

**Fallback.** If it is not fixed after two attempts, record the blocker and switch to E0 +
E1 double-runs on the LB (T6, T7), treating any delta below 0.05 as unresolved.

---

## T2 — Toolkit v1 code delta

The itemized gap is `docs/SKILLS_ARCHITECTURE.md` §6.4. One PR-sized change:

| # | change |
|---|---|
| 1 | `_index.locate`: demote test paths to ×0; add traceback ×6, error-string ×4, `docs_src` ×0.5, vendored ×0.3 |
| 2 | `_index.locate` output: top 5 files, 40-line excerpt for #1, signature + 8 lines for #2–5, test command, fallback command |
| 3 | stop injecting `_knowledge` hints from `locate` (keep the module for the paper track) |
| 4 | `_verify`: include untracked files in the changed set; FAIL on empty diff; scan for `.adk_exec_*`, `*.orig`, `*.rej`; extract assertion line + last non-test repo frame from JUnit |
| 5 | `_verify` output: `STATUS` line, `PASS`/`FAIL` per check, `NEXT` line |
| 6 | `swe.py`: `--issue` (alias `--query`), `--top`, `--run-repro`; `PARTIAL` status |
| 7 | extract the watchdogs into `_guard.py`; print the partial report before `os._exit(0)` |
| 8 | delete `scripts/bootstrap.py` (unreferenced, `rglob`s `/`) |

**Gate.** `python tools/audit_locate.py` still runs; unit-level sanity on a fixture repo.
**Done when.** Test demotion shows hit@3 7/7 on the seven snapshots and no regression on the
other six tasks.

**Status 2026-11-01 — done.** All 8 items landed. hit@1 5/7, hit@3 7/7, hit@5 7/7, median
3.19 s, max 6.87 s; `rich_3470` rank 10 → 2. `verify` was exercised on 8 fixtures covering
empty / untracked / stray / protected / gitignored / syntax / pytest-green / pytest-red.
Details in `RESULTS.md` under 2026-11-01. The bundle copy in
`ckpt/bundles/exp13_swe_toolkit/skills/swe-toolkit/` is hash-identical to `skills/swe-toolkit/`.

---

## T3 — Adversarial fixtures

One throwaway repo per case, run `locate`, `inspect`, `verify` against each: empty repo,
missing `_swegemma_baseline`, non-UTF8 file, Python 2 file, deep nesting, symlink loop,
5 MB `.py`, hanging pytest, repo with no tests.

**Done when.** Every case returns a `STATUS` line in under the watchdog, exit code 0, no
traceback.

---

## T4 — 129-task retrieval benchmark, demoted ranker

Re-run the benchmark in `research/PAPER_EXPERIMENTS.md` with the T2 ranker.
**Done when.** File R@10 ≥ 0.55 (current `swe_toolkit` 0.4587, hybrid RRF 0.5701) and the
per-task rows are committed.

---

## T5 — Bundle and notebook gates for E1

```
.venv-harness\Scripts\python.exe tools\verify_bundle.py --bundle <e1-bundle>
.venv-harness\Scripts\python.exe tools\build_notebook.py --bundle <e1-bundle> --out build\e1.ipynb
.venv-harness\Scripts\python.exe tools\verify_notebook.py --notebook build\e1.ipynb
```

**Done when.** `ALL CHECKS PASSED` on both, and the prompt contains exactly one
`{problem_description}` and no other braces.

---

## T6 — E0 control submission

Re-run `ckpt/bundles/exp05_patch_integrity` **byte-identical**. It is the only way to learn
whether 0.20 reproduces; without it every later delta is measured against a single
unreplicated observation.

**Gate.** Rebuild, `verify_bundle`, `verify_notebook`, push kernel, Gate 4 (pulled artifact
hash == local build), `numAllowedNow > 0`, explicit yes.
**Done when.** Score recorded in `RESULTS.md`; the run-to-run noise band is written down.

---

## T7 — E1 submission

Single change vs E0: `skills/swe-toolkit/` + the `skills:` line + `## TOOLKIT` paragraph.
**Do not append `{problem_description}`** — the harness already sends the problem statement
as the user turn (`agent_runner.py:677`), and the 0.20 artifact has no placeholder.

**Gate (added 2026-10-31).** `locate` hit@3 ≥ 60% on the 30 single-file never-solved tasks,
`locate` returns in < 5 s on fastapi with no `DEGRADED`/empty body, and the prompt names the
skill `swe-toolkit` and calls it without `find /`.
**Done when.** Score recorded; keep only if the paired instrument shows a real per-task gain
and the LB is ≥ E0 + 0.06 (0.05 is 1 standard error, see Audit A).

**Status 2026-11-01 — two of three gate clauses pass, the third is unmeasured.**
`locate` hit@3 is 7/7 on the 7 extracted snapshots, but those are archetype picks, not the
30 never-solved tasks, so 7/7 is not the gate. `locate` is 3.0–3.9 s warm on fastapi and
`--budget 1` returns `STATUS: PARTIAL` with a body, so the latency clause passes. The prompt
names `swe-toolkit`, has one `run_skill_script` call shape, and contains no `find /`.
Remaining work: download the 30 single-file never-solved snapshots (≈2–4 GB), re-run
`tools/audit_locate.py`, and record hit@3 before building E1.

---

## T8 — Ladder after E1

One change per submission, in this order, each gated on the previous:

| exp | change | keep if |
|---|---|---|
| E2 | test demotion already in T2 — confirm on LB | paired gain holds |
| E3 | `verify` runs pytest (if E1 shipped gate-only) | call counts drop, no score loss |
| E4 | 28→34 calls, 8→9 min | logs show `BudgetExceeded` or first edit after call 8; revert on any 12 h overrun |
| E5 | six-row knowledge table in `system.md` | E1–E4 plateau **and** error analysis shows wrong fixes, not wrong locations |

---

## T9 — Paper track (2026-11-12)

`docs/PAPER_TRACK_DRAFT.md` is the base. It needs the audit numbers from
`docs/TASK_CLASSIFICATION.md`, the locate benchmark from `docs/AUDIT_SNAPSHOTS.md`, and the
E0/E1 results. Separate track; it does not consume competition submissions.
**Done when.** Submitted before 2026-11-12 23:59 UTC.

---

## T10 — Freeze the final two (by 2026-11-25)

Leave a week of slack before 2026-12-02. Pick the two best mechanism-backed bundles, not
the two highest noisy scores. Re-verify both artifacts byte-for-byte before selecting.
**Done when.** The two refs are written into `RESULTS.md` and `ckpt/STATE.md`.

---

## Blocked / not ours

| item | blocked by |
|---|---|
| any submission before 2026-10-31 00:00 UTC | pending `57806053` + daily quota |
| E0/E1 on the LB | explicit yes (AGENTS.md rule 1) |
| hidden-set repo composition | unverified; `ckpt/CONFIG.md` claims repos outside the public four |

## Deliberately not doing

- **The E4B line.** 0.05–0.06 = ~3/58 tasks (95% CI 1.8%–14.1%); reaching 0.179 needs 3.4×.
  Keep `tracks/e4b_small/` only as the paper-track scale ablation.
- LoRA on the 129 public tasks — dev-only, and adapters collapse the KV cache to ~7.6k.
- Planner/coder multi-agent split — `exp01` scored 0.05.
- `max_time_minutes` above 9 — the 12 h total is binding; 12-minute tasks scored 0.
- Raising `max_tool_calls` — tested (28 → 35 on E4B), no gain; see Audit D.
- A large knowledge book in v1 — 32.6% playbook precision.
- Per-language skills — all 129 tasks are Python.
- Early `submit_patch` as insurance — the working tree is graded regardless.

## Decision log

| date | decision |
|---|---|
| 2026-10-30 | one skill, one entrypoint, three modes; `python_swe` dropped |
| 2026-10-30 | knowledge ships as a six-row table in `system.md`; `_knowledge.py` not wired until error analysis justifies it |
| 2026-10-30 | `verify` runs targeted pytest itself, because `run_command` truncates at 5,000 chars |
| 2026-10-30 | instrument repair (T1) precedes all bundle work |
| 2026-10-31 | E4B line closed; genuine E4B is 0.05–0.06 |
| 2026-10-31 | the 0.20 anchor is `ckpt/exp05/submission.zip`; the frozen bundle is a later variant (+36 chars) |
| 2026-10-31 | LB resolution is ±0.05 (1 SE at n=58); only ≥ 0.06 deltas are admissible |
| 2026-10-31 | anchor mean is 10.4/58 (12,10,10,10,10); 0.24 = 4.0 SD, so 0.17 is the modal expectation |
| 2026-10-31 | 0.24 is **not** arithmetically impossible: it needs ~7 of the 30 single-file never-solved tasks; the blocker is localization |
| 2026-10-31 | `exp13_swe_toolkit` is **not submittable**: `locate` is 13.5–25.7 s on fastapi, the 25 s watchdog returns `DEGRADED` with no output, the prompt uses `find /`, the skill name is wrong, `SKILL.md` omits `locate`, and the `{problem_description}` append makes it 2 changes |
| 2026-10-31 | T2 gate is now a 30-task locate benchmark at hit@3 ≥ 60%; no E1 submission until it passes |

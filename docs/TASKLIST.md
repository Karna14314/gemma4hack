# Tasklist — 31B line

Live queue. **The first unchecked task is the only one in progress.** Each task names its
gate and its done-when so it can be closed without re-deriving context.

Updated 2026-10-30. Design rationale: `docs/SKILLS_ARCHITECTURE.md`. Evidence:
`docs/TASK_CLASSIFICATION.md`, `docs/AUDIT_SNAPSHOTS.md`.

## State

| item | value |
|---|---|
| best public score | **0.20** (`exp05_patch_integrity`, ref `57553805`, 31B) |
| pending submission | `57806053` e4b-v2 — **blocks the next submission** |
| next submission slot | **2026-10-31 00:00 UTC** (`maxDailySubmissions: 1`) |
| submission days left | 33 (2026-10-31 → 2026-12-02) |
| final selections | 2 (`numScoredSubmissions: 2`) |
| measurement instrument | `research/kernel_devset_eval/` = `KernelWorkerStatus.ERROR` |
| paper deadline | 2026-11-12 23:59 UTC |
| main deadline | 2026-12-02 23:59 UTC |

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

Single change vs E0: `skills/swe-toolkit/` + the `skills:` line + `# CALL PLAN` → `## TOOLKIT`.
**Gate.** T2–T5 complete; T1 shows no regression on the paired set.
**Done when.** Score recorded; keep only if ≥ E0 + 0.05 or the paired instrument shows a
real per-task gain.

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

- LoRA on the 129 public tasks — dev-only, and adapters collapse the KV cache to ~7.6k.
- Planner/coder multi-agent split — `exp01` scored 0.05.
- `max_time_minutes` above 9 — the 12 h total is binding; 12-minute tasks scored 0.
- A large knowledge book in v1 — 32.6% playbook precision.
- Per-language skills — all 129 tasks are Python.

## Decision log

| date | decision |
|---|---|
| 2026-10-30 | one skill, one entrypoint, three modes; `python_swe` dropped |
| 2026-10-30 | knowledge ships as a six-row table in `system.md`; `_knowledge.py` not wired until error analysis justifies it |
| 2026-10-30 | `verify` runs targeted pytest itself, because `run_command` truncates at 5,000 chars |
| 2026-10-30 | instrument repair (T1) precedes all bundle work |

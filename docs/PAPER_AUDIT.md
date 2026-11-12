# PAPER_AUDIT.md — read-only repo audit for the Gemma 4 Developer Agent Paper Track

**Prepared:** 2026-11-09 (message time 2026-11-09T06:08:56Z) | **Scope:** read-only; no files modified except this one; no Kaggle submits, no evals, no training, no `eval_snapshots/` reads (44 GB; only dir names/sizes listed); no network.

Every number is cited as `path:line` or `path` + key. "NOT FOUND" = not present in the repo; nothing is guessed.

---

## 1. INVENTORY (depth 3)

Top-level tracked tree (from `git ls-files`, repo root): `AGENTS.md`, `HANDOFF.md`, `README.md`, `bundles/`, `ckpt/`, `docs/`, `eval_results/`, `kaggle_work/`, `notes/`, `requirements.txt`, `research/`, `scripts/`, `skills/`, `src/`, `tracks/`, `tools/`.

`docs/` (21 files, last commits 2026-10-29 → 2026-11-09; total ~299 KB):
| file | purpose | size | last commit |
|---|---|---|---|
| `docs/AGENTS.md` | operating instructions (hard rules) — repo root | ~29 KB | 2026-10-31 |
| `docs/ADK_SKILL_CONTRACT.md` | ADK skill contract notes | 818 B | 2026-10-30 |
| `docs/AUDIT_E4B_AND_ANCHOR.md` | E4B vs anchor audit; noise math (0.05 SE) | 12.45 KB | 2026-10-31 |
| `docs/AUDIT_E4B_AND_PAPER.md` | forensic audit of E4B/paper submissions | 12.93 KB | 2026-10-29 |
| `docs/AUDIT_PUBLIC_RESEARCH.md` | 0.24 tail + union-ceiling analysis | 9.31 KB | 2026-10-31 |
| `docs/AUDIT_SNAPSHOTS.md` | 7-snapshot localization audit manifest | 7.26 KB | 2026-11-01 |
| `docs/COMPETITION_RESOURCES.md` | live Kaggle resource inventory | 8.73 KB | 2026-10-30 |
| `docs/ENV_AUDIT.md` | wheel/env audit + payload proof | 12.34 KB | 2026-11-09 |
| `docs/EXP13_VS_EXP05_STRICT_AUDIT.md` | exp13 pre-mortem strict audit | 9.78 KB | 2026-11-01 |
| `docs/FINAL_HARNESS_COMPARISON.md` | exp13 readiness dual-track audit | 13.92 KB | 2026-11-01 |
| `docs/LEADERBOARD_STATS.md` | leaderboard stats + noise model | 3.36 KB | 2026-11-07 |
| `docs/LEDGER.md` | submission ledger | 3.31 KB | 2026-11-09 |
| `docs/OPENCODE_REPORT.md` | OpenCode session report | 72.02 KB | 2026-11-01 |
| `docs/OPENCODE_REPORT_2.md` | OpenCode session report | 33.61 KB | 2026-11-01 |
| `docs/PAPER_TRACK_DRAFT.md` | paper-track draft (2,997 words, 161 lines) | 19.52 KB | 2026-11-09 |
| `docs/RUNBOOK.md` | copy-paste ops commands | 11.32 KB | 2026-10-30 |
| `docs/SCORE_PREDICTION_AND_ROADMAP.md` | exp13/E4B score predictions | 11.22 KB | 2026-11-03 |
| `docs/SESSION_FINAL.md` | exp_think1024 submission handover | 6.33 KB | 2026-11-09 |
| `docs/SKILLS_ARCHITECTURE.md` | swe-toolkit skill design | 23.20 KB | 2026-11-01 |
| `docs/SUBMISSION_RUN_e4b_v4.md` | e4b_v4 submission run record | 2.94 KB | 2026-11-02 |
| `docs/TASKLIST.md` | live experiment queue + state | 15.80 KB | 2026-11-01 |
| `docs/TASK_CLASSIFICATION.md` | 129-task dev-set categorization | 8.67 KB | 2026-10-30 |

Stale / duplicate / contradictory docs flagged:
- `ckpt/HARNESS_README.md` is **stale** (pre-2026-10-13); the live copy is `kaggle_work/gemma-4-developer-agent/research/competition/HARNESS_README.md` (`AGENTS.md` §9, `COMPETITION_RESOURCES.md:80`).
- `ckpt/CONFIG.md` partially stale (`AGENTS.md` table 1).
- `ckpt/STATE.md` (updated 2026-10-10) is stale vs `docs/LEADERBOARD_STATS.md` and `docs/ENV_AUDIT.md:4.1` (e.g. claims exp03 pending; ENV_AUDIT shows it scored 0.17; claims "pending 57836949" but ENV_AUDIT shows it COMPLETE 0.17).
- `docs/LEDGER.md:15` misdocuments e4b-v2 (see §3).
- `docs/AUDIT_E4B_AND_PAPER.md:241` says paper draft is 1,366 words — stale; the draft is now 2,997 words (§9/§finale).
- `research/SCORES.md` is a 3-line stub pointing to `COMPETITION_GUIDE.md Part 7` (`research/SCORES.md:1-3`).
- `docs/AUDIT_E4B_AND_PAPER.md:215` table (low recall 0.0018–0.0058) contradicts `research/PAPER_TABLES.md` (high recall 0.0176–0.5701) — see §3.

`bundles/` (root, 4 bundle dirs): `exp13`, `exp13_swe_toolkit`, `exp14_lean_toolkit`, `exp_think1024`. Each has `agent.yaml`, `eval_config.yaml`, `configs/sampling.yaml`, `prompts/system.md`; `exp13_swe_toolkit` and `exp14_lean_toolkit` add `skills/swe-toolkit/`.
`ckpt/bundles/` (frozen copies): `exp04_mandatory_pycompile`, `exp05_patch_integrity` (the 0.20 anchor source), `exp06_rebased_cheatsheet`, `exp06_repo_test_cheatsheet`, `exp07_rebased_verification`, `exp07_verification_loop`, `exp08_tool_contract`, `exp09_drop_graph_tools`, `exp10_consolidated`, `exp11_e4b`, `exp13_swe_toolkit` — each with the 4 config members; `exp13_swe_toolkit` adds skills. `ckpt/bundles/exp05_patch_integrity/prompts/system.md` carries the **+36-char post-submission trailer** (`## The issue` + `{problem_description}`) and is therefore NOT the scored artifact (`docs/AUDIT_E4B_AND_ANCHOR.md:155-171`).
`tracks/e4b_small/bundles/` (5 bundles): `e4b_v2`, `e4b_v3`, `e4b_v3_swe_toolkit`, `e4b_v4_swe_toolkit`, `exp11_e4b`. Each has the 4 config members; the `*_swe_toolkit` ones add `skills/swe-toolkit/` (SKILL.md + 5 scripts).
`kaggle_work/gemma-4-developer-agent/bundles/` (11 bundles): mirrors of `exp04`–`exp12`, `exp13_swe_toolkit`, `exp_think1024`; used by Gate 2/3 commands.
`tracks/e4b_small/kernel_*/` (3 kernel dirs): `kernel_e4b_submit`, `kernel_e4b_v2_submit`, `kernel_e4b_v4_submit` — each `kernel-metadata.json` + `submission_notebook.ipynb`.
`kaggle_work/gemma-4-developer-agent/experiments/` (~19 kernel dirs): `exp01`–`exp13`, `e0_exp05_control`, `exp_think1024`, `exp06_session_baseline` — each `kernel-metadata.json` + `submission_notebook.ipynb`.
`scripts/` (5): `capped_query_eval.py`, `fetch_eval_data.py`, `probe_thinking_budget.py`, `repro_harness_traps.py`, `t6_run.py`.
`tools/` (12): `audit_locate.py`, `benchmark_locate_129.py`, `bootstrap.py`, `build_notebook.py`, `check_resources.py`, `dump_notebook.py`, `kaggle_ckpt.py`, `kaggle_rest.py`, `sync_exp13.py`, `test_verify_8_scenarios.py`, `verify_bundle.py`, `verify_notebook.py`.
`eval_results/` (2): `capped_query_results.json` (106 B), `t6_results_v4_repro.json` (1.84 MB, **129 per-task rows**; §5).
`research/` (top-level): `BUDGET_LIMITS.md`, `COMPETITION_GUIDE.md`, `DEVSET_EVAL_MECHANICS.md`, `E4B_FAILURE_ANALYSIS.md`, `GEMMA4_SAMPLING.md`, `PAPER_EXPERIMENTS.md`, `PAPER_TABLES.md` (duplicate of `research/paper_eval_outputs/PAPER_TABLES.md`), `PROGRESS.md`, `SCORES.md` (3-line stub), `SKILL_CONTRACT.md`, `SMALL_MODEL_PRIZE.md`, `SOURCES.md`, plus `kernel_devset_eval/`, `kernel_paper_eval/`, `paper_eval_outputs/`.
`research/paper_eval_outputs/` (5): `PAPER_EXPERIMENTS.md`, `PAPER_TABLES.md` (7,878 B each, duplicates of `research/PAPER_*.md`), `g4-paper-graph-benchmark.log` (941 B), `output.zip` (500 B), `paper_experiments.json` (23,984 B, full 129-task instrument), `recall_summary.csv` (123 B — **OLD low-recall measurement**, contradicts PAPER_TABLES.md; §3).
`ckpt/exp03`–`ckpt/exp06`: per-exp `kernel-metadata.json`, `output.zip`, `submission.zip`, `submission_manifest.json`, `submission_notebook.ipynb` (gitignored zips).
`src/`: `agent_package/` (default E4B bundle), `notebook_lib/` (`__init__.py`, `package_source.py`, `validator.py`), `sections/` (`00_header.py`–`60_package.py`).
`skills/swe-toolkit/` (repo root, not in default bundle): `SKILL.md`, `scripts/_guard.py`, `_index.py`, `_knowledge.py`, `_verify.py`, `swe.py`.
No `LICENSE`/`LICENSE.txt`/`LICENSE.md` found (`ls` returned none). Repo README describes it as a **private engineering workspace** (`README.md:1`); no public/repo-license info in repo.

---

## 2. SUBMISSION LEDGER

Scores from `docs/ENV_AUDIT.md:4.1` (full queue, 2026-11-09) and `docs/LEADERBOARD_STATS.md`, `docs/LEDGER.md`, `docs/AUDIT_E4B_AND_ANCHOR.md`. Config verified against bundle files (§1). 1 task = 1/58 ≈ 0.017 (`docs/AUDIT_E4B_AND_ANCHOR.md:25`).

| ref | date | bundle / artifact | model | temp | max_tool_calls | max_output / thinking | prompt chars | tools | public LB score | tasks/58 | status | change vs previous |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 56793672 | 2026-10-03 | exp01 | 31B | — | — | — | — | — | 0.05 | 3 | scored | baseline v1 |
| 56812498 | 2026-10-04 | exp02 v2 | 31B | — | 60 | — | — | — | ~0.08 | 5 | scored | thinking on, 6 min/60 calls/120 turns, prompt rewrite (4 changes bundled) |
| 57037122 | 2026-10-10 | exp03 baseline replica | 31B | 0.2 | 28 | 8192 / 4096 | ~5,500 | 6 (+3 graph) | 0.17 | 10 | scored | byte-exact public 0.17 replica; SHA `e3be904c…` |
| 57553805 | 2026-10-23 | exp05 patch integrity | 31B | 0.2 | 28 | 8192 / 4096 | 5,461 (frozen) / 5,425 (submitted zip) | 9 (+3 graph) | **0.20** | 12 | scored | pre-submit patch integrity (`git status --short` + `git add -N -f`); SHA `2ba7f9b1…` |
| 57618114 | 2026-10-25 | exp08 tool contract prompt | 31B | 0.2 | 28 | 8192 / 4096 | 6,040 (+554) | 6 | 0.17 | 10 | scored | +554 char tool prose (regression) |
| 57654236 | 2026-10-26 | exp10 consolidated | 31B | 0.2 | 28 | 6144 / 4096 | 9,867 (+4,350) | 6 | 0.17 | 10 | scored | STATE header + Call-8 rush; max_output 6144 → headroom 26,624 |
| 57697341 | 2026-10-27 | exp11_e4b (31B fallback) | 31B (fallback) | 0.2 | 28 | 8192 / 4096 | 5,353 | 6 | 0.13 | 8 | scored | E4B alias rejected by validator → 31B fallback package (`docs/AUDIT_E4B_AND_PAPER.md:24`) |
| 57736284 | 2026-10-28 | exp12 timing buffer | 31B | 0.2 | 28 | 8192 / 4096 | 6,109 (+592) | 6 | 0.17 | 10 | scored | near-exact exp05, 9-min buffer |
| 57777888 | 2026-10-29 | exp11_e4b genuine E4B | E4B | 0.2 | 28 | 8192 / 4096 | 5,353 | 6 | 0.06 | 4 | scored | genuine E4B bundle (model swap only); tasks corrected 3→4 on 2026-11-12 (0.06 = 4/58 per `research/paper_figs/ledger.csv`) |
| 57806053 | 2026-10-30 | e4b-v2 | E4B | 0.1 | **35** | 8192 / 4096 | **1,746** | 6 | 0.05 | ~3 | scored | temp 0.1 + imperative prompt + 35 calls (3 changes; LEDGER misdocuments as 2/2440; §3) |
| 57836949 | 2026-10-31 | E0 control (byte-identical exp05) | 31B | 0.2 | 28 | 8192 / 4096 | 5,425 | 9 | 0.17 | 10 | scored | reproduction check; **exp05's 0.20 did not reproduce** (identical artifact scored 0.17); SHA `2ba7f9b1…` |
| 57889741 | 2026-11-02 | e4b_v4_swe_toolkit | E4B | 0.1 | **35** | 8192 / 4096 | 2,116 | 7 + SkillToolset | 0.05 | ~3 | scored | E4B + swe-toolkit v4 engine; skill offload prediction falsified |
| 57933618 | 2026-11-03 | exp14_lean_toolkit | 31B | 0.2 | 28 | 8192 / 4096 | 5,767 (lean) | 9 + SkillToolset | 0.15 | ~9 | scored | 31B + swe-toolkit skill, lean prompt |
| 58096981 | 2026-11-07 | exp_sampling | 31B | 1.0 | 28 | 8192 / 4096 | 5,461 | 9 | 0.13 | — | scored | temp 1.0 / top_p .95 / top_k 64 off exp05; within noise |
| 58149803 | 2026-11-09 | exp_think1024 | 31B | 0.2 | 28 | 8192 / **1024** | 5,461 | 9 | **pending** | — | **pending scoring** | thinking budget 4096→1024 (single change off exp05); **newest submission** |

Marking: all rows above are **scored** except `58149803` (**pending scoring**, Gate 4 complete + pulled hash byte-identical, `docs/ENV_AUDIT.md:201-204`). No submission newer than `58149803` exists in the repo (git log top commit is `exp_think1024 submitted (ref 58149803)`; `docs/ENV_AUDIT.md:106` "Nothing is PENDING; no submission today (2026-11-09)"). `docs/LEDGER.md:23-24` still marks e4b-v2 `57806053` "pending" — **stale**; it completed at 0.05 (`docs/ENV_AUDIT.md:97`).

Pooled converged-config 31B = 8 scored runs (0.20, 0.17×5, 0.15, 0.13) = 79/464 = **0.170**, SE ≈ 0.018 (`docs/LEDGER.md:49-50` results section; `docs/LEADERBOARD_STATS.md:17`). E0 control proves exp05's 0.20 was a high draw, not a reproducible +2 (`docs/AUDIT_E4B_AND_ANCHOR.md:58`).
**Errata (2026-11-12):** this paragraph previously read "≈ 77/464 = 0.166"; the correct count of the 8 scored runs (12 + 5×10 + 9 + 8 tasks) is **79/464 = 0.170** (`docs/PAPER_VERIFY.md` §B.2).

---

## 3. DISCREPANCIES (docs vs actual bundle contents)

### 3.1 e4b-v2 (ref 57806053) — the known one, plus two more

`docs/LEDGER.md:15` claims: "Diff vs baseline (57777888): **only** `configs/sampling.yaml` (temperature 0.2 -> 0.1) and `prompts/system.md` (rewritten, **2440 chars**). agent.yaml and eval_config.yaml **byte-identical**."

Actual bundle `tracks/e4b_small/bundles/e4b_v2/`:
- `configs/sampling.yaml:1` `temperature: 0.1` ✓ (changed)
- `eval_config.yaml:3` `max_tool_calls: 35` — baseline `exp11_e4b/eval_config.yaml:3` is `max_tool_calls: 28` → **eval_config.yaml is NOT byte-identical** (LEDGER false on this)
- `prompts/system.md` = **1,746 chars, 33 lines** (measured), not 2,440 (`docs/AUDIT_E4B_AND_ANCHOR.md:85` table lists prompt chars 1,746)
- 3 changes total (temperature, max_tool_calls 28→35, prompt rewrite), not 2 → violates AGENTS.md rule 4 ("one isolated change per experiment") per `docs/AUDIT_E4B_AND_ANCHOR.md:90-91`.

So e4b-v2 is documented as **2 changes / 2,440 chars**; actual is **3 changes / 1,746 chars**.

### 3.2 Prompt placeholder hygiene vs the scored artifact

`docs/LEDGER.md:26-27` and `docs/TRACK` verifiers require the prompt to end with `{problem_description}` ("prompt has problem_description", "prompt ends cleanly"). But `docs/AUDIT_E4B_AND_ANCHOR.md:160-181` (Audit E) shows the **scored 0.20 artifact** (`ckpt/exp05/submission.zip`, SHA `2ba7f9b1…`) has prompt 5,425 B **without** the placeholder, while the frozen bundle `ckpt/bundles/exp05_patch_integrity/prompts/system.md` is 5,461 B **with** `## The issue` + `{problem_description}` appended (+36 chars, lines 55-56). `verify_bundle.py` rejects the true 0.20 artifact on prompt-hygiene; the official harness (`adk_submission.validate_directory`, `compile_submission`) accepts it (`docs/AUDIT_E4B_AND_ANCHOR.md:177-181`). So the repo's prompt-hygiene rule is **stricter than the harness** and the frozen bundle is a **variant, not the anchor**.

### 3.3 Low-recall table contradicts the instrument

`docs/AUDIT_E4B_AND_PAPER.md:213-217` (Experiment 1) and `research/paper_eval_outputs/recall_summary.csv:1-4` report lexical R@5 = 0.0045 / graph 0.0 / hybrid 0.0045 on 129 tasks. `research/PAPER_TABLES.md:8-14` and `docs/PAPER_TRACK_DRAFT.md:76-80` report M1 lexical file R@5 = 0.2284 / node R@5 = 0.0950, M5 hybrid RRF file R@10 = 0.5701. These are **contradictory** (node-level 0.0045 vs 0.0950; graph 0.0 vs 0.0630). The draft uses the PAPER_TABLES.md numbers; `recall_summary.csv` is an older/superseded measurement.

### 3.4 exp05 prompt char count

`docs/AUDIT_E4B_AND_PAPER.md:222` lists exp05 prompt 5,425 chars (the submitted zip's value); `docs/FINAL_HARNESS_COMPARISON.md:141` lists exp05 base as 5,517 and exp13 as 7,001. The working-tree `ckpt/bundles/exp05_patch_integrity/prompts/system.md` is **5,461 chars** (§1 measurement) — i.e. frozen bundle = submitted 5,425 + 36-char trailer. No single canonical number; three values (5,425 / 5,461 / 5,517) circulate.

### 3.5 Deadline contradiction

`ckpt/STATE.md:44` ("deadline 2026-12-02") vs the competition API `2026-11-12T23:59:00.807Z` flagged in `kaggle_work/gemma-4-developer-agent/RESULTS.md:43-44`. `COMPETITION_RESOURCES.md:27` and `README.md:33` give paper deadline **2026-11-12 23:59 UTC** and main deadline **2026-12-02 23:59 UTC** (consistent with each other; STATE.md row is the stale one).

---

## 4. EVIDENCE MAP (claims in docs/PAPER_TRACK_DRAFT.md)

Word count: **2,997 words, 161 lines** (measured via token-split). The draft has **no separate references/bibliography section**; all citations are inline file references, so there is nothing to exclude from the count — the 2,997 includes abstract, tables, and body.

| # | Claim (approx. quote) | Supporting file/data | Status |
|---|---|---|---|
| 1 | "32,768-token vLLM ceiling, 28 tool calls, 8 minutes per task" | `docs/COMPETITION_RESOURCES.md:87` (max_model_len 32,768); `ckpt/bundles/exp05_patch_integrity/eval_config.yaml:3-4` (28 calls, 8 min) | VERIFIED |
| 2 | "ADK compaction strips tool outputs at 14,336 tokens" | live `HARNESS_README.md` §7.2 lines 570-574 (`compaction_interval=15`, `token_threshold=14336`); `docs/ENV_AUDIT.md:76-77` | VERIFIED (live harness) |
| 3 | "vLLM crashes when prompt + max_output > 32768" | `docs/ENV_AUDIT.md:65` (repro #2 `ceiling_32768` PASS); `docs/PAPER_TRACK_DRAFT.md:21` | VERIFIED |
| 4 | ".gitignore silently drops new files under git add -N ." | `docs/ENV_AUDIT.md:66` (repro #3 PASS); `submit_patch` mechanism | VERIFIED |
| 5 | "public-LB deltas of ≤2 tasks are statistically unresolvable" | `docs/AUDIT_E4B_AND_ANCHOR.md:27-37` (SE 0.0504; P(12\|0.172)=0.102) | VERIFIED |
| 6 | "exp03 reproduced the public 0.17 baseline" | `docs/LEDGER.md` (ref 57037122 scored 0.17); `docs/ckpt/STATE.md:139` | VERIFIED |
| 7 | "exp05 added a pre-submit patch-integrity check and reached 0.20" | ref 57553805 scored 0.20 (`docs/ENV_AUDIT.md:103`) | VERIFIED (score) |
| 8 | "not reproduced by an identical control: 0.17" | E0 ref 57836949 scored 0.17 (`docs/ENV_AUDIT.md:96`) | VERIFIED |
| 9 | "129 tasks across fastapi, rich, requests, httpx" | `COMPETITION_RESOURCES.md:97-103` (67/48/13/1 = 129); `TASK_CLASSIFICATION.md:14-19` | VERIFIED |
| 10 | "swe_toolkit reaches file R@10 = 0.4587 overall and 0.4734 on the 125 in-graph tasks; hybrid RRF 0.5701 / 0.5883" | `research/PAPER_TABLES.md:22-23, 40-41` (M4 file R@10 0.4587; in-graph 0.4734; M5 0.5701 / 0.5883); `paper_eval_outputs/PAPER_TABLES.md` duplicate | VERIFIED |
| 11 | "beating both lexical (0.3036) and graph-only (0.2846)" | `research/PAPER_TABLES.md:19-21` (M1 file R@10 0.3036; M3 0.2846) | VERIFIED |
| 12 | "80.9% of raw 1-hop neighborhoods exceed the 5,000-character tool cap" | `research/PAPER_TABLES.md:87` (313/387 = 80.9%) | VERIFIED |
| 13 | "70.5% of tasks modify a single file and 8.5% create new files" | `research/PAPER_TABLES.md:93` (%1-file 70.5, %new files 8.5); `TASK_CLASSIFICATION.md:86-90` (71% one file) | VERIFIED |
| 14 | "10 triggered SWE playbooks fire 258× with 32.6% gold-patch precision" | `research/PAPER_TABLES.md:102-115` (258 triggers, precision 32.6% = 84/258) | VERIFIED |
| 15 | "31B model scores 0.20 versus 0.06 for the 4B E4B model" | refs 57553805 (0.20) and 57777888 (0.06) (`docs/ENV_AUDIT.md:103,99`) | VERIFIED (single draws) |
| 16 | "File-level recall (R@5 0.744) masks an intra-file symbol bottleneck (symbol R@5 0.306→0.405)" | `research/SCORE_PREDICTION_AND_ROADMAP.md:127-131` (v4 sym@5 0.306 → v6 0.405); `PAPER_TRACK_DRAFT.md:127-131` | VERIFIED (offline instrument) |
| 17 | "span-level re-ranker at +1.3 s" | `docs/SCORE_PREDICTION_AND_ROADMAP.md:130` (v5AB/v6 re-rank cost 1.310 s median) | VERIFIED |
| 18 | "offloading ... to a deterministic stdlib skill (swe-toolkit), predicted to double the 4B rate, was measured at 0.05 and falsified" | `docs/SCORE_PREDICTION_AND_ROADMAP.md:112-116` (predicted 0.09–0.13); ref 57889741 scored 0.05 (`docs/ENV_AUDIT.md:95`) | VERIFIED (falsified) |
| 19 | "E4B line closed (0.05–0.06 across four submissions)" | refs 57777888 (0.06), 57806053 (0.05), 57889741 (0.05), + exp11_e4b (`docs/AUDIT_E4B_AND_ANCHOR.md:273`) | VERIFIED |
| 20 | "the 4B bottleneck is edit fidelity and state retention, not localization" | `docs/SCORE_PREDICTION_AND_ROADMAP.md:85-100` (mechanism diagnosis) | UNVERIFIED (inference; no per-task traces — `docs/AUDIT_E4B_AND_ANCHOR.md:114-117`) |
| 21 | "pooled converged-config 31B ≈ 0.166 (0.20, 0.17×5, 0.15, 0.13 ⇒ ≈77/464)" | `docs/LEDGER.md` results section (2026-11-09) | VERIFIED — **errata 2026-11-12: recomputed 79/464 = 0.170 (`docs/PAPER_VERIFY.md` §B.2); quoted text kept as the historical audit record** |
| 22 | "exp05's 0.20 was a high draw" / "pooled 0.179" | `docs/AUDIT_E4B_AND_ANCHOR.md:58` (52/290 = 0.179) | VERIFIED |
| 23 | "symbol re-ranker is a prototype (exp14 shipped a lean-toolkit variant, scored 0.15)" | ref 57933618 exp14 scored 0.15 (`docs/ENV_AUDIT.md:94`); re-ranker unshipped (`%TEMP%/opencode/`, outside repo) | VERIFIED (score) / prototype outside repo |
| 24 | "run narisettichaitanya/g4-paper-graph-benchmark (CPU, ~3 min)" | `research/paper_eval_outputs/g4-paper-graph-benchmark.log` (941 B) | UNVERIFIED locally (kernel not rerun) |
| 25 | "Verified kernels: gemma4-devagent-exp13-swe-toolkit-v2 v2 (c9135bcb…), g4-e4b-small-agent-submit v7 (97c25136…), gemma4-devagent-exp-think1024 v1 (5d80bac7…)" | `kaggle_work/.../RESULTS.md` (Gate 4 rows); artifact hashes match local builds | VERIFIED (Gate 4) |

**UNVERIFIED / caveat-heavy claims:** #20 (no per-task traces exist — `docs/AUDIT_E4B_AND_ANCHOR.md:114-117`), #16/#17 (offline instrument only, not on the hidden set), #24 (benchmark log only, not re-executed), #1 (4x L4 / isolated sandbox — cannot be reproduced locally, `COMPETITION_RESOURCES.md:175-176`).

---

## 5. ANALYSES AVAILABLE

**Committed analysis results:**
- `research/paper_eval_outputs/paper_experiments.json` (23,984 B) — full 129-task instrument: per-task `file_hit`/`sym_hit` @1/3/5/10, `best_rank`, `seconds`, `top`/`top_syms`, `gold_files`/`gold_syms`.
- `research/paper_eval_outputs/PAPER_TABLES.md` + `research/PAPER_TABLES.md` (identical, 7,878 B each) — Experiment 1 (5-way localization, all/in-graph/traceback/symptom/per-repo), Experiment 2 (gold patch anatomy), Experiment 3 (10 playbooks), Experiment 4 (leaderboard ablations).
- `eval_results/t6_results_v4_repro.json` (1.84 MB) — **129 per-task rows** with `file_hit`, `sym_hit`, `best_rank`, `issue_chars`, `seconds`, `stats.files_indexed/found/truncated/seconds`, `top`, `top_syms`.
- `eval_results/capped_query_results.json` (106 B) — capped-query recall: n=129, R@5 full=96 / first300=92 / last300=83 / keywords<=300=94 (counts, not rates).
- `docs/AUDIT_SNAPSHOTS.md:56-65` — locate benchmark on 7 snapshots: re-measured hit@1 5/7, hit@3 7/7, hit@5 7/7, hit@10 7/7, median 3.19 s.
- `docs/FINAL_HARNESS_COMPARISON.md:38-42` — corrected engine table: base @1/3/5/10 = 0.419/0.628/0.713/0.829; v3 = 0.419/0.628/0.729/0.822; v4 shipped = 0.419/0.651/**0.744**/0.829; zero-return 0.171 (22/129).
- Symbol Hit@3 v4 vs v5 vs v6: v4 0.231 → v5 0.322 (+0.091) → v5A 0.322 → v5AB 0.322 → v6 **0.331** (`docs/SCORE_PREDICTION_AND_ROADMAP.md:137-142`, `PAPER_TRACK_DRAFT.md:125-131`). v4→v6: +0.058 @1, +0.100 @3, +0.099 @5, +0.099 @10.
- Anchor 31B runs: five scored runs 12, 10, 10, 10, 10 tasks (pooled 0.179; `docs/AUDIT_E4B_AND_ANCHOR.md:50-58`).
- Per-repo file R@5: fastapi 0.4791 (swe_toolkit), rich 0.2801, requests 0.7692, httpx 0.5714 (`PAPER_TABLES.md:80-85`).

**Ranker recall @1/3/5/10** (file-level, all 129, `PAPER_TABLES.md:17-23`): M1 lexical 0.0504/0.1819/0.2284/0.3036; M2 embedding 0.0583/0.1772/0.2163/0.3810; M3 graph 0.0504/0.1819/0.2265/0.2846; M4 swe_toolkit 0.2661/0.3798/0.4350/0.4587; M5 hybrid RRF 0.2466/0.3742/0.4745/**0.5701**.

**Dataset size / gold labels:** 129 public dev tasks (fastapi 67, rich 48, requests 13, httpx 1) — `COMPETITION_RESOURCES.md:97-103`. Gold labels built from each task's `patch` field (gold file paths → module dot-paths `F_gold`; modified symbols → AST graph node IDs `G_gold`; graphs available for 125/129) — `PAPER_TRACK_DRAFT.md:64`, `PAPER_TABLES.md:3`. Hidden scoring set is ~120 tasks, not available (`COMPETITION_RESOURCES.md:172`).

**Known caveats:** gold-symbol extractor rebuilt / approximate (`PAPER_TRACK_DRAFT.md:155` "gold-sym extraction approx" in git log `21119b7`; `docs/AUDIT_E4B_AND_ANCHOR.md` notes); per-task differences ±1–2 are noise (`docs/AUDIT_E4B_AND_ANCHOR.md:27`); `recall_summary.csv` low-recall table is stale/contradicted (§3.3); `swe.py locate` latency 13.5–25.7 s on fastapi with 25 s watchdog `DEGRADED` risk (`docs/AUDIT_PUBLIC_RESEARCH.md:135-139`); only 7 snapshots extracted locally (786 MB), full 129 snapshots = 21.5 GB not kept (`docs/AUDIT_SNAPSHOTS.md:8-14`).

---

## 6. FIGURES (proposed, from committed data only — not generated yet)

1. **Leaderboard ablation time series** — public LB score vs submission date for the 15 refs (§2 table). Input: `docs/ENV_AUDIT.md:4.1` table (ref, date, score). Script: none exists; write a small plotting script. Effort: low.
2. **5-way localization recall (file-level R@1/3/5/10)** — grouped bar chart of M1–M5. Input: `research/PAPER_TABLES.md:17-23` (or `paper_eval_outputs/PAPER_TABLES.md`). Script: none. Effort: low.
3. **Symbol Hit@1/3/5/10 progression v4→v6** — line chart of the five variants. Input: `docs/SCORE_PREDICTION_AND_ROADMAP.md:137-142` table. Script: none. Effort: low.
4. **Gold patch anatomy** — bar/histogram of files changed (median 1, p90 4), %1-file 70.5 / %2+ 29.5 / %new 8.5. Input: `research/PAPER_TABLES.md:91-97`. Script: none. Effort: low.
5. **Playbook trigger rate vs precision** — scatter of 10 playbooks (trigger % vs precision, bubble = matches). Input: `research/PAPER_TABLES.md:102-113`. Script: none. Effort: low.

None of these scripts exist committed; all inputs are committed tables that would need to be transcribed into a plotting script (no data regeneration required).

---

## 7. NOTEBOOKS / LINKS & REPRODUCIBILITY

**URLs referenced in the repo:**
- https://www.kaggle.com/competitions/gemma-4-developer-agent (`COMPETITION_RESOURCES.md:24`, `README.md:4`) — **public** competition page.
- https://www.kaggle.com/datasets/metric/gemma-4-developer-agent-wheelhouse (`COMPETITION_RESOURCES.md:116`, `README.md:58`) — **public** dataset (41 files, 840 MiB; gitignored local copy at `kaggle_work/.../research/wheelhouse/`).
- https://google.github.io/adk-docs/ (`README.md:8`) — **public** Google ADK docs.
- Kernel slugs (owner `narisettichaitanya`): `gemma4-devagent-exp01`, `exp03-baseline-017-replica`, `exp08-tool-contract-prompt`, `exp10-consolidated`, `exp12-timing-buffer`, `exp13-swe-toolkit-v2`, `gemma4-devagent-exp-think1024`, `g4-e4b-small-agent-submit` (v1/v4/v7), `g4-e0-exp05-control-resubmit`, `g4-e4b-v2-small-agent-submit`, `g4-e4b-v4-small-agent-submit`, `g4-paired-devset-eval`. These are **private to the team's Kaggle account** (not verifiable as public without network); slugs are re-slugified from titles (`RUNBOOK.md:199-201`).
- `ryanholbrook/gemma-4-developer-agent-small-model-leaderboard` (`docs/AUDIT_E4B_AND_PAPER.md:111`) — public small-model LB snapshot (pulled 2026-10-26); our team not on it because the 0.13 was the 31B fallback.
- Public research notebooks cited in `docs/AUDIT_PUBLIC_RESEARCH.md:2.2`: `flexonafft/gemma-4-budget-aware-coding-agent-v2`, `bliverrigpdoge/lb-0-22-4-...`, `honghanhhh/gemma-4-baseline-lb-0-24`, `prvsiyan/gemma-and-the-shape-of-doubt`, `dmitriigluzdov/gemma-4-task-soundness-...`, `verracodeguacas/gemma-4-agent-budget-fit-single-agent` — public, but only names, no data.

**Repo license:** NO `LICENSE` file found (§1). README does not state a license. Repo is described as a **private engineering workspace** (`README.md:1`); public/private status of the GitHub repo not determinable from the repo alone.

**Reviewer reproducibility from the repo alone:** **Partially.** The bundle source (`src/`, `bundles/`, `tracks/`, `skills/`), the real-harness verifiers (`verify_bundle.py`, `verify_notebook.py`), and the 129-task instrument (`paper_eval_outputs/paper_experiments.json`, `t6_results_v4_repro.json`) are committed, so a reviewer can: (a) re-verify any bundle with the three competition wheels (downloadable from the public wheelhouse dataset), (b) rebuild + execute the notebook, (c) recompute all localization tables. What is missing: the three competition wheels are **not** in the repo (gitignored `wheelhouse/`, must be downloaded — 840 MiB, public dataset), `.venv-harness` is gitignored, `tasks.jsonl` is gitignored (regenerable via `check_resources.py --refresh`, needs Kaggle auth), the hidden scoring set and per-task scores are unavailable (`COMPETITION_RESOURCES.md:172-175`), vLLM/4×L4 runtime is not local. So the artifact is verifiable end-to-end but the actual task-resolution score cannot be reproduced locally.

---

## 8. CANDIDATE FRAMINGS (ranked by strength of committed evidence)

### Framing A — Evaluation-methodology / negative-results paper (strongest)
**3 strongest facts:** (i) 0.17 vs 0.20 statistically indistinguishable (SE 0.0504, `docs/AUDIT_E4B_AND_ANCHOR.md:27-37`); (ii) identical 0.20 artifact re-submitted as E0 control scored 0.17 (`docs/ENV_AUDIT.md:96`, ref 57836949); (iii) prompt micro-changes (exp08/10/12) all landed at 0.17 — pooled 31B = 0.179 (`docs/AUDIT_E4B_AND_ANCHOR.md:58`, `docs/LEADERBOARD_STATS.md:17`). **Strong committed evidence: measurement noise dominates.**
**3 weakest points:** no per-task traces exist to attribute failures (`docs/AUDIT_E4B_AND_ANCHOR.md:114-117`); public LB covers only ~50% of ~120 hidden tasks (`COMPETITION_RESOURCES.md:37`); cannot run the real scorer locally (`COMPETITION_RESOURCES.md:176`).
**Missing:** a formally modeled noise budget and a pre-registered analysis plan (the pre-registration exists informally in `docs/TASKLIST.md`/`SESSION_FINAL.md` but not as a paper artifact).

### Framing B — Locate-ranker resource / `swe_toolkit` (moderate)
**3 strongest facts:** file R@5 0.744 / R@10 0.829 on 129 tasks, hybrid RRF R@10 0.5701 (`research/PAPER_TABLES.md:22-23, 40-41`); 7-snapshot audit hit@3 7/7 after test demotion (`docs/AUDIT_SNAPSHOTS.md:65`); engine deltas measured via controlled A/B (bare-identifier rule removed, deterministic tie-breakers) (`docs/FINAL_HARNESS_COMPARISON.md:48-78`). **Strong committed offline evidence.**
**3 weakest points:** never submitted on the LB as a 31B entry (exp13 kernel-verified only, not submitted — `docs/EXP13_VS_EXP05_STRICT_AUDIT.md:92-94`); locate latency 13.5–25.7 s on fastapi with `DEGRADED` watchdog risk (`docs/AUDIT_PUBLIC_RESEARCH.md:135-139`); gold-symbol extractor approximate / rebuilt (`docs/AUDIT_E4B_AND_ANCHOR.md`; git log `21119b7`).
**Missing:** end-to-end LB score for the toolkit (exp14 scored 0.15 but as a lean variant, not a clean isolate); `swe_toolkit` not wired into any scored 31B bundle.

### Framing C — Skills / toolkit as an ADK artifact (weakest)
**3 strongest facts:** skill contract verified against ADK 1.36.1 wheel (`docs/SKILLS_ARCHITECTURE.md:28-37`, `docs/ENV_AUDIT.md:79`); `run_skill_script` schema matches (`docs/kaggle_work/.../RESULTS.md` Gate 2 rows); single skill, three modes (locate/inspect/verify) with call budget 9–17 of 28 (`docs/SKILLS_ARCHITECTURE.md:287-296`). **Reasonable design evidence.**
**3 weakest points:** E4B + swe-toolkit scored 0.05 (falsified the offload prediction — `docs/ENV_AUDIT.md:95`, ref 57889741); `ADK_SKILL_CONTRACT.md:15-17` warns skill files can pollute the patch (contradicted by `docs/SKILLS_ARCHITECTURE.md:29` which says skills materialize to a temp dir — internal contradiction); skill never landed in a scored 31B submission.
**Missing:** any scored submission where the skill is the decisive variable.

---

## 9. RISKS

**Claims that overstate the evidence:**
- PAPER_TRACK_DRAFT.md abstract §2: "exp05 added a pre-submit patch-integrity check and reached 0.20" — 0.20 is one high draw; pooled 0.179; E0 control scored 0.17 (`docs/AUDIT_E4B_AND_ANCHOR.md:58`, `docs/ENV_AUDIT.md:96`). Overstates causality.
- PAPER_TRACK_DRAFT.md §5: "the 4B bottleneck is edit fidelity and state retention, not localization" — inference only, no traces (`docs/AUDIT_E4B_AND_ANCHOR.md:114-117`). Overstates.
- PAPER_TRACK_DRAFT.md: "cross-scale, the 31B model scores 0.20 versus 0.06 for the 4B E4B model" — compares two single draws, one of which (0.20) failed to reproduce. Misleading without noise framing.
- PAPER_TRACK_DRAFT.md §3 presents the PAPER_TABLES.md recall numbers; `recall_summary.csv` contradicts them (§3.3) — the draft must justify which instrument is canonical.
- PAPER_TRACK_DRAFT.md §6: "All artifacts are released" — no LICENSE file, repo is a private workspace (§1). Overstates release status.

**Contradictions with official rules / harness:**
- `docs/LEDGER.md:15` claims e4b-v2 changed only 2 files and eval_config byte-identical; actual `max_tool_calls: 35` vs baseline 28 (§3.1). If the submission record is cited as a "single-change experiment," it's wrong.
- `ckpt/HARNESS_README.md` is stale vs the live 2026-10-13 revision (§1; `COMPETITION_RESOURCES.md:78-79`). Citing it would cite wrong compaction interval (5 vs 15) and model list.
- Prompt-hygiene rule (`{problem_description}` required, clean end) is stricter than the harness — the true 0.20 artifact lacks the placeholder and compiles fine (`docs/AUDIT_E4B_AND_ANCHOR.md:177-181`). The verifier would reject the anchor artifact itself.
- `docs/AUDIT_E4B_AND_PAPER.md:44` says small-model LB top score is 0.1 (262 teams) — but our genuine E4B scored 0.05–0.06 below that; consistent, but the leaderboard snapshot is from 2026-10-26 and stale.
- No LoRA adapters (allowed models only; adapter collapses KV cache 46k→7.6k) — `README.md:228`, `ckpt/STATE.md:130`; consistent across bundles (no `adapters/` anywhere in git ls-files).
- Single base model per submission — `exp11_e4b` 0.13 was the 31B fallback because the E4B alias was rejected (`docs/AUDIT_E4B_AND_PAPER.md:24`); the four `tracks/e4b_small/*_swe_toolkit` bundles declare E4B only (verified in `docs/kaggle_work/.../RESULTS.md` e4b_v3 row).

---

## 10. OPEN QUESTIONS (max 8)

1. Which recall instrument is canonical for the paper — `research/PAPER_TABLES.md` (high) or `research/paper_eval_outputs/recall_summary.csv` (low, 0.0018–0.0058)? (§3.3)
2. Is exp_think1024 (ref 58149803, pending) scored yet, and which pre-registered bucket does it fall in (≥13 real win / 9–12 null / ≤8 regression)?
3. The repo has no LICENSE and is a private workspace — what license/release statement should the paper track claim for "All artifacts are released"?
4. Should `ckpt/bundles/exp05_patch_integrity` be annotated as a variant (not the anchor), given the +36-char trailer and that `verify_bundle.py` rejects the true scored artifact? (§3.2)
5. Can per-task traces be obtained (organizers' logs) to substantiate the E4B "edit fidelity / state retention" claim (#20 in §4), which is currently inference-only?
6. Is there any submission newer than 58149803 on the live Kaggle account not reflected in this repo's git log / ENV_AUDIT snapshot?
7. Which two bundles should be frozen as the final selections (`numScoredSubmissions: 2`) given all are within noise of 0.166–0.179?
8. Does the paper track require a PDF/form beyond `docs/PAPER_TRACK_DRAFT.md`, and what is its submission mechanism (the paper-track dataset exposes only a 55 B `NOTE.md`, `COMPETITION_RESOURCES.md:145-151`)?

---

## Finale

- **Total words in `docs/PAPER_TRACK_DRAFT.md`:** 2,997 words, 161 lines (measured by whitespace-token split; no separate references section exists, so nothing is excluded).
- **`git log --oneline -15`:**

```
2145464 exp_think1024 submitted (ref 58149803): thinking_budget 4096->1024 single change, payload-proven + gates; docs handover + leaderboard catch-up + paper updates
1140644 capped-query eval: first300 0.713, last300 0.643, keywords 0.729 (full 0.744)
21119b7 eval runner rebuilt; v4 file recall reproduced exactly (R@3 0.651, R@5 0.744); sym Hit@3 +2 tasks vs paper (gold-sym extraction approx)
1f6ca99 eval: fetch script + harness-trap repros (5/5) + leaderboard stats (E0=0.17, exp14=0.15, e4b_v4=0.05)
0a98f3c raise --issue cap to 1500 (31B) / 500 (E4B); trim SKILL.md sync
7d2b0ca trim SKILL.md to 1377 chars (ADK preamble cost) + score-doc caveat
8a0f927 Merge pull request #17 from Karna14314/feat/e4b-v4-submit
e8e6e61 docs: fix last commit hash in SESSION_FINAL
1ddb160 docs: add SESSION_FINAL for e4b_v4 submission
caecd3c docs: record e4b_v4 submission ref 57889741 and kernel v1
0b46d04 docs: add submission run progress file for e4b_v4
a6405db exp14_lean_toolkit + e4b_v4_swe_toolkit: upgraded swe-toolkit engine + lean prompt
01e23f6 audit: exp13 vs exp05 strict pre-mortem + paper draft final + v6 report
7497dd3 gate4: refresh kernel notebook from Gate-3 build (build/exp13_swe_toolkit.ipynb)
342473b e4b_v3_swe_toolkit staged+verified; v5 symbol prototype measured; score-prediction doc
```

# PAPER_CHECKS2.md — Four CPU-only checks to settle the Paper Track thesis

**Branch:** `paper/checks2` (from `main`, branch point `ed58643`). **Deadline:** Nov 12, 2026 23:59 UTC.  
Existing files read-only; new files only under `research/direction_checks2/`. No Kaggle submissions, no GPU.

---

## Phase 1 — Decompose the 0.435 vs 0.744 gap

Instrument A (Regime A, Table 2A): M4 swe_toolkit File R@5 = **0.4350** — mean per-task file-recall fraction over graph-node candidates (125 in-graph + 4 embedding fallback). Per-task ranks NOT committed.

Instrument B (Regime B, Table 2C): v4 File R@5 = **0.7440** — binary any-gold over all 60,483 .py files. Per-task ranks committed (`eval_results/instrument_b.json`, v4 available 129/129).

Recomputed from Instrument B (top-k over top10 vs gold_files):

| k | any-gold R@k | mean-fraction R@k | recall-definition effect (pp) |
|---|---:|---:|---:|
| 1 | 0.4186 | 0.3167 | 10.19 |
| 3 | 0.6512 | 0.5276 | 12.36 |
| 5 | 0.7442 | 0.6184 | 12.58 |
| 10 | 0.8295 | 0.7170 | 11.25 |

Decomposition at R@5 (total gap 30.9 pp):
- (i) Recall definition: **12.58 pp** (any-gold 0.7442 − mean-fraction 0.6184)
- (ii) Candidate set / index input: **18.32 pp** (mean-fraction 0.6184 − Instrument A 0.4350)
- Pure (ii) **not isolatable**: Instrument A per-task graph-node ranks not committed (no graph JSON artifacts on this branch). The public kernel (`g4-paper-graph-benchmark`) is stdlib-only and prints tables from in-memory strings; a copy cannot dump Instrument A ranks without the graph data.

Script: `research/direction_checks2/phase1_gap_decomposition.py` → `phase1_gap_decomposition.json`.

---

## Phase 2 — Verify or cut numbers (file:line)

| Number | Claim in draft | Verification | Verdict | Source |
|---|---|---|---|---|
| 80.9% | 1-hop neighborhoods exceed 5,000-char cap | 313/387 = 80.9% recomputed | **VERIFIED** | `research/PAPER_TABLES.md:87`; `docs/PAPER_TRACK_DRAFT.md:76`; `docs/PAPER_AUDIT.md:143` |
| 0/31 live gold hits | LLM bare names → 0/31 gold hits | Cites Discussion #746250 (external); not in committed data | **UNVERIFIED** | `docs/PAPER_TRACK_DRAFT.md:77` |
| 99.8% dot-path mismatch | 99.8% of exact queries fail | Cites Discussion #746250 (external); not in committed data | **UNVERIFIED** | `docs/PAPER_TRACK_DRAFT.md:77` |
| 60,483 .py files | Regime B file count | Committed aggregate claim; snapshots not on branch (can't recompute) | **VERIFIED-as-claim** | `research/PAPER_TABLES.md:120`; `research/kernel_paper_eval/paper_eval.py:945` |
| 0.895 vs 0.158 | Any-gold vs all-gold, 38 multi-file tasks | **Recomputed:** top10 any-gold 34/38=0.895, all-gold 6/38=0.158 ✓ | **VERIFIED** | `research/PAPER_TABLES.md:138-139`; `eval_results/instrument_b.json` |
| 9/9 vs 8/8 | 9/9 torture suite | **Recomputed:** tools/test_verify_8_scenarios.py → 9/9 pass ✓ | **VERIFIED** | `tools/test_verify_8_scenarios.py:100`; `docs/PAPER_TRACK_DRAFT.md:138`. 8/8 is a *different* e4b-v2 final-gate test (`docs/OPENCODE_REPORT.md:1187`), not the paper's torture suite. |

Action: keep VERIFIED numbers; cut or flag UNVERIFIED (0/31, 99.8%) unless Discussion #746250 can be opened.

---

## Phase 3 — Top teams (0.22–0.29) vs our harness

Live leaderboard via bearer auth (CLI 401s on KGAT token; HTTP 200). Top-20 teams ≥0.22:

| Score | Teams (n) | Example teams |
|---|---:|---|
| 0.29 | 1 | Yurnero (2026-10-29) |
| 0.24 | 11 | Yike Xu, SAVE, chizhu, pluris, Alberth Moreira, tammam alasha, Pınar Aksoy, Takumu Hata, Serhii Mosiiash, LuisSpecian, MUHAMMED IDRIS BIN YACOOB |
| 0.22 | 8 | Francis Joseph, Deepest Mind, Ayush Barai, omallo, Vibhanshu Singh, ABHIRUP DAS, Thomas TưNhân, 吃白饭的大肥鱼 |

All scores ≈ multiples of 1/58 (0.29≈17/58, 0.24≈14/58, 0.22≈13/58). Top-20 view only; cannot get density near 0.17 from this endpoint.

Downloaded public notebooks (2), **neither confirmed as a top-20 team**:

| Notebook | Author (metadata vs content) | Harness vs ours (exp05 anchor) | Difference |
|---|---|---|---|
| gemma-4-loop-breaker-adk-agent.ipynb | metadata prvsiyan; content robinamirbahar | Same as exp05 (31B, temp 0.2, thinking 4096, 28 calls/8 min, 9 tools) | +loop-breaker STATE rule; prompt ~3,756 vs 5,461 chars |
| lb-0-22-4-config-files-no-training.ipynb | metadata jocelyndumlao; leaderboard bliverrigpdoge | Settings not extractable inline | Full config unavailable |

**Confirmed top-20 match: None.** Cannot fetch per-team notebooks (JS-rendered pages, CLI 401s). Differences above are for downloaded notebooks only, not attributed to top-20 teams.

Our exp05 anchor (`kaggle_work/.../bundles/exp05_patch_integrity/agent.yaml`): model gemma-4-31b-it-qat-w4a16-ct; tools run_command/read_file/edit_file/write_file/get_status/submit_patch/get_code_neighbors/search_similar_code/get_code_subgraph (9); temp 0.2, top_p 0.95, max_output 8192, thinking 4096; 28 calls / 8 min / 80 turns; no skills; patch gate `git add -N -f`; prompt 5,461 chars.

---

## Phase 4 — Data terms (derived dataset / gold labels)

- Kaggle rules page (`.../competitions/gemma-4-developer-agent/rules`) is **JS-rendered**; fetch returns only the page title → **UNREADABLE**.
- No explicit permission found (local docs) for releasing a derived per-task dataset or gold labels of the 129 tasks.
- `docs/PAPER_VERIFY.md:110`: "private sharing outside teams is prohibited (foundational rules)."
- `research/public_intel/datasets/README.md:70`: the *census table* is CC BY 4.0 — different artifact, not the competition task data.
- `docs/PAPER_AUDIT.md:177`: 129 public dev tasks; gold labels built from each task's `patch` field; hidden scoring set (~120 tasks) **not available**.

**Verdict: NOT CONFIRMED.** Do not release derived per-task dataset or gold labels until the competition rules/data license are clarified (relevant to Best New Resource track).

---

## Scripts (all stdlib, CPU-only, ran clean)

- `research/direction_checks2/phase1_gap_decomposition.py` → `phase1_gap_decomposition.json`
- `research/direction_checks2/phase3_top_teams.py` → `phase3_top_teams.json` + `leaderboard_live.csv` (live refetch)
- Lint: `python3 -m py_compile` on both → clean.

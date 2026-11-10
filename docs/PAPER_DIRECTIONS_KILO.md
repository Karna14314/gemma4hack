# PAPER_DIRECTIONS_KILO.md — Recommended thesis for Gemma 4 Developer Agent Paper Track

**Branch:** `paper/directions-kilo` (from `main`, branch point `ed58643`).  
**Deadline:** Nov 12, 2026 23:59 UTC. **Limit:** 3,000 words judged text (tables+captions count; references+figures do not).  
**Read-only on existing files.** This file only recommends; it does not modify `docs/PAPER_TRACK_DRAFT.md` or any other committed file.  
Every claim cites a file path (`path:line`) or a URL with date. Measured vs inferred is separated throughout.

---

## Decision table (top)

| # | Candidate thesis | Prize fit | Key evidence (cited) | Main risk | Falsified if | N / Q / R / V / C* |
|---|---|---|---|---|---|---|
| T1 | Harness mechanics and state retention dominate prompt engineering in offline Gemma 4 SWE agents | Best New Application / Best Paper | five wheel-verified traps (PAPER_TRACK_DRAFT.md:27-39); exp14 9 tools+SkillToolset =0.15 vs exp05 6 tools =0.20/0.17 (LEDGER.md); E0 byte-identical 0.20→0.17 (LEDGER.md; AUDIT_E4B_AND_ANCHOR.md) | exp15 pending (ref 58183079, sha 7219eb5c, LEDGER.md) may land ~0.17, not >0.20 | exp15 scores ≥0.24 | 4 / 4 / 5 / 4 / 3 |
| T2 | Live git-tracked workspace AST indexing + test-path demotion is the largest controllable lever (+30.9 pp File R@5), beating static code graphs | Best New Resource (swe-toolkit locate) / Best Paper | Regime B 0.744 vs Regime A 0.4350 (PAPER_TRACK_DRAFT.md:62-72); bootstrap CI [0.6667,0.8140] excludes 0.4350 (direction_checks/bootstrap_ci.json); symbol v4→v6 +0.099 (PAPER_TRACK_DRAFT.md:76-78) | base/v3 per-task not committed; 80.9% cap claim not re-verifiable here (cap_sweep.json = 0 files) | bootstrap CI includes 0.4350 | 5 / 5 / 4 / 5 / 4 |
| T3 | 4B models are bottlenecked by edit fidelity & state retention, not retrieval — falsifying localization-offload | Best Paper (negative result) | e4b_v4_swe_toolkit =0.05 (LEDGER.md; AUDIT_E4B_AND_ANCHOR.md); E4B line closed 0.05-0.06 (~3/58) | no runtime skill-invocation traces (PAPER_VERIFY.md:C.2 "NONE") | a verified 4B run beats 0.06 | 3 / 4 / 4 / 3 / 3 |
| T4 | Leaderboard noise (SE≈0.0503≈3 tasks) makes single-run 31B deltas ≤2 tasks unresolvable; only harness-mechanics-justified changes warrant submission | Best Paper (meta/methodological) | pooled 31B 0.1702 =79/464 (PAPER_TRACK_DRAFT.md:150-151; verified by recompute); live LB top-20 all ≈ multiples of 1/58 (direction_checks/leaderboard_live.csv); adjacent gaps 100% ≤1 task (board_blocks.csv) | defensive/negative framing less likely to win "Best Paper" | a single run shows a replicable ≥3-task gain | 4 / 4 / 5 / 4 / 4 |

\*N=Novelty, Q=Quality, R=Relevance, V=Verifiability, C=Clarity (1-5). Criteria names themselves UNVERIFIED from Kaggle (JS-rendered pages return only title; docs/PAPER_VERIFY.md:112).

**Recommendation:** **T2 as primary thesis** (fallback T1). T2 pairs a large, robust, offline-measured effect (+30.9 pp, bootstrap-confirmed) with a concrete, releasable resource (swe-toolkit `locate`/`inspect`/`verify`, zero-dependency, 10 playbooks, 9/9 torture suite). That maps cleanly to **Best New Resource ($10k)** and supports **Best New Application ($10k)** via the harness-audit methodology; the full study supports **Overall Best Paper ($15k)**. T1 is the fallback if judges prefer the harness-mechanics narrative. T3/T4 are strong supporting sections, not the lead thesis (T3 = negative result, harder for "Best Paper"; T4 = meta/defensive).

---

## Phase 1 — RULES (Kaggle Paper Track)

Extracted from `docs/PAPER_VERIFY.md:106-112` (Kaggle overview/rules pages fetched Oct-Nov 2026; competition page JS-rendered → only title readable via direct webfetch, so page body treated as UNVERIFIED beyond what PAPER_VERIFY.md captured):

- Competition page: `https://www.kaggle.com/competitions/gemma-4-developer-agent-paper` (Google DeepMind; Featured Hackathon).
- Paper deadline: **November 12, 2026 23:59 UTC** (also on main track page).
- Submission artifact: a Kaggle Writeup documenting methods/experiments; unpublished research only; main-competition participation not required.
- Prize categories (judges choose at review, not submission-time): **Overall Best Paper $15,000; Best New Resource $10,000; Best New Application $10,000**. A team may submit at most two write-ups; judges determine eligibility for each prize; a write-up can be considered for more than one award but wins only one (discussion #743255, host Elan Markowitz).
- Word-count scope: all judged text (including captions and tables) counts; **references and figures do not count**; captions count. No official word counter released yet.
- Exact five judging criterion names: **NOT CONFIRMED** (tracks-and-awards/overview pages are JS-rendered; names not captured). Do not invent them in the writeup; refer to them generically or as "five criteria" unless confirmed.
- Writeup editable before deadline: not confirmed on fetched pages (typical Kaggle writeups are editable until deadline, unverified here).

Agreement with current draft: the draft's target tracks ($15k/$10k/$10k) and prize structure match. The draft's claim of "five criteria ... Novelty, Quality, Relevance, Verifiability, Clarity" is **plausible but UNVERIFIED** from fetched pages (PAPER_VERIFY.md:112) — treat as working assumption, flag in limitations.

---

## Phase 2 — PUBLIC CONTEXT (what is already public)

Kaggle notebook/discussion pages are JS-rendered and could not be opened directly (webfetch returned only page titles). The following are cited from `docs/PAPER_VERIFY.md:114-117` (previously fetched) plus our own audit:

| Item | URL | Date | Author | One-line summary | Already public? |
|---|---|---|---|---|---|
| Official starter | kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent | 2026-10-12 | ryanholbrook | tasks.jsonl + 129 snapshots + graphs starter kit | Yes |
| Paper writeup (community) | kaggle.com/code/jefferyjeromeharris/gemma-4-dev-agent-paper | 2026-09-27 | jefferyjeromeharris | two-agent ADK, ~12% resolution, compaction at 32K tokens | Yes |
| Community EDA notebooks | kaggle.com/code/{romanrozen,lucifer19,zhukovoleksiy,nursrijan}/... | ~2026-10-02 | various | most-voted EDA/adk starter notebooks | Yes (per sweeden-ttu notes) |
| Public config census | kaggle.com/datasets/dariushafshar/gemma-4-agent-public-config-draws | 2026-10 | dariushafshar | 141 scored draws, 67 notebooks, 21 bundle hashes; max 0.22, no ≥0.24 | Yes |
| Public config averages | kaggle.com/datasets/dariushafshar/gemma-4-most-run-public-config-averages-10-58 | 2026-10 | dariushafshar | popular bundles average ~10/58 = 0.17 | Yes |
| Shape-of-doubt | kaggle.com/datasets/prvsiyan/gemma-and-the-shape-of-doubt | 2026-10 | prvsiyan | 0.20 score, no files_sha256 (not bundle-reproducible) | Yes |
| Loop-breaker notebook | kaggle.com/code/robinamirbahar/gemma-4-loop-breaker-adk-agent | 2026-10 | robinamirbahar | ~3,756-char prompt + Command/Call Repetition loop-breaking | Yes |
| Direct-code-verifier | kaggle.com/code/nihilisticneuralnet/gemma-4-developer-agent-direct-code-verifier | 2026-10 | nihilisticneuralnet | pytest-as-a-tool direct verification | Yes |
| TDD reproducer | kaggle.com/code/rainycloudss/gemma-4-agent-apex-v16-tdd-reproducer | 2026-10 | rainycloudss | TDD reproducer; kernel metadata committed locally (ed58643) | Yes |
| Tool ablation discussion | kaggle.com/competitions/gemma-4-developer-agent/discussion/746250 | 2026-10 | community | built-in graph tools 0/31 gold hits, score 55→50/129 | Yes |
| Harness discussions | /discussion/743456, /744692, /744794, /747186 | Oct 2026 | various | compaction, 32,768 overflow, thinking_budget existence | Partially (existence public; engine enforcement ours) |

**Which of our findings are already public:** compaction existence (a), 32,768 overflow (b), thinking_budget parameter existence (d) are public on Kaggle (PAPER_VERIFY.md:D.1 rows a,b,d). Our specific **engine-enforcement verification** (thinking budget reaches vLLM and changes behavior; scripts/probe_thinking_budget.py) and the **.gitignore silent-drop (c)** and **SkillToolset temp-dir semantics (e)** are NOT confirmed publicly — these are our novel contributions.

---

## Phase 3 — LEADERBOARD DATA

Live public leaderboard fetched via bearer auth (Kaggle CLI 401s on KGAT token; bearer works) → `research/direction_checks/leaderboard_live.csv` (top-20 best scores only — the `/leaderboard/view` endpoint does not return the full distribution):

| Score | Approx. tasks/58 | Teams (top-20 view) |
|---|---|---|
| 0.29 | ~17 | 1 (Yurnero) |
| 0.24 | ~14 | 11 |
| 0.22 | ~13 | 8 |

All live scores are multiples of 1/58 rounded to 2 decimals (0.29≈17/58=0.2931; 0.24≈14/58=0.2414; 0.22≈13/58=0.2241). **Limitation:** top-20 view only; cannot get density near 0.17 from this endpoint.

Full distribution from local snapshot `research/public_intel/datasets/board_blocks.csv` (2026-10-22, 3,430 teams):

| Score | Tasks | Teams | Rank range |
|---|---|---|---|
| 0.24 | 14 | 4 | 5-39 |
| 0.22 | 13 | 35 | 40-187 |
| 0.20 | 12 | 148 | 188-611 |
| 0.18 | 10 | 424 | 612-1166 |
| 0.17 | 10 | 555 | 1167-1646 | ← largest cluster |
| 0.15 | 9 | 480 | 1647-1997 |
| 0.13 | 8 | 351 | 1998-2307 |
| 0.12 | 7 | 310 | 2308-2582 |
| 0.10 | 6 | 275 | 2583-2801 |
| 0.08 | 5 | 219 | 2802-2959 |
| 0.06 | 4 | 158 | 2960-3102 |
| 0.05 | 3 | 143 | 3103-3211 |
| 0.03 | 2 | 109 | 3212-3277 |
| 0.01 | 1 | 66 | 3278-3430 |
| 0.00 | 0 | 153 | 3431+ |

**Adjacent rank gaps:** within a score tier the gap is 0 tasks; between adjacent tiers the gap is exactly 1 task (0.017). Of 3,429 adjacent team pairs, 3,415 have gap 0 and 14 have gap 1. Fraction of adjacent gaps **≤1 task = 100%**, **≤2 tasks = 100%**, **≤3 tasks = 100%**. The public leaderboard is extremely dense: a single task (0.017) separates most adjacent ranks.

**Independence assumption:** treating each team's score as an independent draw gives an **upper bound** on the sampling-error band; real scores are correlated (same models/prompts reused), so the true resolvable delta is ≥ the independence bound. Cross-split SE = √(p(1-p)/58) ≈ 0.0503 (~3.0 tasks) at p≈0.179 (PAPER_TRACK_DRAFT.md:127-128).

---

## Phase 4 — PRIOR ART (verified references)

Exact title, authors, year, URL (all opened and verified; `docs/PAPER_VERIFY.md:92-103`):

1. Jimenez et al. "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?" ICLR 2024. arXiv:2310.06770. https://arxiv.org/abs/2310.06770
2. Yang et al. "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering." NeurIPS 2024. arXiv:2405.15793. https://arxiv.org/abs/2405.15793
3. Xia et al. "Agentless: Demystifying LLM-based Software Engineering Agents." arXiv:2407.01489; PACMSE FSE 2025. https://arxiv.org/abs/2407.01489
4. Chen et al. "LocAgent: Graph-Guided LLM Agents for Code Localization." ACL 2025. arXiv:2503.09089. https://arxiv.org/abs/2503.09089
5. Ouyang et al. "RepoGraph: Enhancing AI Software Engineering with Repository-Level Code Graph." ICLR 2025. arXiv:2410.14684. https://arxiv.org/abs/2410.14684
6. Wang et al. "Improving Code Localization with Repository Memory." ICLR 2026. https://proceedings.iclr.cc/paper_files/paper/2026/hash/b4c06f095368497f3ac19422efef8133-Abstract-Conference.html
7. OrcaLoca (Yu et al., 2025) — cited-by-reference only (not independently opened; mark UNVERIFIED if used).

**No variance/reliability-specific paper on agent-benchmark leaderboard noise was verified.** Our binomial noise model (SE 0.0503) is our own derivation; do not attribute it to an external paper. If citing variance literature, find and open a specific paper first, or present it as our own analysis.

---

## Phase 6 — QUICK CHECKS (CPU-only, <1 hour each; scripts in research/direction_checks/)

**bootstrap_ci.py** (`research/direction_checks/bootstrap_ci.json`): resampled Instrument B per-task any-gold hits (129 tasks, `eval_results/instrument_b.json`) 5,000×.
- Observed Regime B v4 File R@5 = **0.7442** (matches draft 0.744).
- 95% CI = **[0.6667, 0.8140]**. Regime A M4 R@5 = 0.4350 is **outside** this CI → the +30.9 pp Regime A→B gap is robust to task sampling, not noise. **Supports T2 strongly.**

**cap_sweep.py** (`research/direction_checks/cap_sweep.json`): static sweep over committed `research/graphs/*.json` for the "80.9% of neighborhoods exceed 5,000-char cap" claim.
- **Found 0 graph files** — committed graph artifacts are absent on this branch (they live in gitignored `kaggle_work/*/research/competition/` and were measured in the earlier session per AGENTS.md §2 Regime A).
- Result: the 80.9% claim is **NOT re-verifiable from committed files here**; it rests on the earlier-session offline benchmark. Flag as a gap / re-measure before the writeup, or soften the claim.

**Pooled-rate recompute** (inline): 8-run converged 31B set = 79 tasks / 464 = **0.1702** (SE 0.0174), matching the draft. SD 0.89 applies only to the 5-run exp05-family subset [12,10,10,10,10]; the 8-run set SD = 1.13. Draft on `main` already states 79/464 = 0.1702 correctly (PAPER_TRACK_DRAFT.md:150-151) — no arithmetic error to correct on this branch.

---

## Phase 7 — RECOMMENDATION

**Primary thesis: T2** ("Live git-tracked workspace AST indexing + test-path demotion is the largest controllable lever for SWE-agent resolution, beating static code graphs"), supported by T1 (harness mechanics dominate prompt engineering).

**Fallback: T1** if judges prefer the harness-mechanics/audit narrative over the retrieval-resource narrative.

**Section outline with word budget (≈2,850 judged text, tables count toward it):**

| Section | Words | Content |
|---|---|---|
| Abstract | 180 | problem, two-regime result (+30.9 pp), noise floor (SE 0.0503), 4B falsification, swe-toolkit |
| 1. Introduction | 320 | offline small-agent regime, scoring model, four RQs, contributions |
| 2. Harness mechanics (T1) | 420 | five wheel-verified traps with file:line citations; countermeasures |
| 3. Two-regime retrieval benchmark (T2) | 560 | Regime A (Table 2A/B) vs Regime B (Table 2C/D), +30.9 pp headline, symbol re-ranking |
| 4. swe-toolkit resource | 260 | zero-dependency package, 10 playbooks, 9/9 torture suite, verify gate |
| 5. Cross-scale & noise | 420 | 31B vs 4B, E0 control, pooled rate 0.1702, SE 0.0503, localization-offload falsified |
| 6. Related work | 220 | 7 verified refs + our positioning |
| 7. Limitations & reproducibility | 200 | gaps (base/v3 per-task, 80.9% cap, no skill traces), one-command notebook |
| **Total** | **~2,580** | leaves buffer under 3,000 (tables count) |

**What to cut from the current draft:** trim the Abstract and §1 scoring-model detail; condense §5.3 external census (already in audit); keep all file:line citations (they're the verifiability strength).

**Numbers in the draft that are unsupported or conflict with files (flag, do not edit draft):**
- "80.9% of 1-hop neighborhoods exceed the 5,000-char tool cap" — not re-verifiable from committed files (cap_sweep.json = 0); sourced to earlier-session AGENTS.md §2 Regime A. Re-measure or soften.
- "Within-split SD 0.89 tasks" — applies to the 5-run exp05-family subset only, not the 8-run set (SD 1.13). Clarify scope.
- Exact five criterion names — UNVERIFIED from Kaggle (PAPER_VERIFY.md:112).

**2.5-day schedule (Nov 10 → Nov 12 deadline):**
- Day 1 (today): finalize this direction doc; re-measure 80.9% cap claim if graph data locatable; confirm criterion names via Kaggle discussion #743255/#743256 if accessible.
- Day 2: integrate T2/T1 into the writeup; run `g4-paper-graph-benchmark.ipynb` end-to-end on Kaggle kernel to confirm ~3-min CPU output; paste into Paper Track portal.
- Day 3 (Nov 11-12): proofread word count (<3,000 judged text incl. tables), verify all numbers cite path:line, submit before 23:59 UTC Nov 12.

**NOT-verified items:** exact five criterion names; writeup-editable-before-deadline; 80.9% cap claim re-verification; public notebook/discussion page bodies (JS-rendered); any runtime skill-invocation traces (PAPER_VERIFY.md:C.2).

**Resume instructions:** branch `paper/directions-kilo`, last commit `ed58643` (main branch point; no commits yet on this branch). Re-run checks: `python3 research/direction_checks/bootstrap_ci.py`, `python3 research/direction_checks/cap_sweep.py`, `python3 research/direction_checks/fetch_leaderboard.py`. PR to open: `https://github.com/Karna14314/gemma4hack/pull/new/paper/directions-kilo` (draft first, mark ready after gate passes). No commits to `main`.

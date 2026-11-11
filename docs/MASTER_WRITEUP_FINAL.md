# Finding a File Is Not Finding the Patch: Retrieval, Hazards & Noise in Gemma 4

**Subtitle**: A 129-task multi-file retrieval study, source- and replay-verified runtime hazards, and N=58 leaderboard uncertainty bounds on Gemma 4.
**Track**: Gemma 4 Developer Agent — Paper Track | **Team**: Antigravity
**Systems**: Gemma 4 (31B, E4B), Google ADK 1.36.1, vLLM 0.19.1, 4× NVIDIA L4.
**Notebooks**: [Graph Benchmark](https://www.kaggle.com/code/narisettichaitanya/g4-paper-graph-benchmark) | [Noise & MDE](https://www.kaggle.com/code/narisettichaitanya/g4-paper-noise-mde)

---

## Abstract

An offline SWE agent fails in three separable places: it retrieves the wrong file, it is defeated by the serving stack, or it is measured too imprecisely to know whether anything changed. We study all three on Gemma 4 across 129 public development tasks.

For retrieval we ladder four rankers that differ by one mechanism each: filename matching (B0), file-level BM25 (B1), AST symbol indexing (B2), and AST indexing with test-path demotion (B3). B3 reaches Any-Gold file R@5 = 0.7442 and Mean-Fraction R@5 = 0.6184. The two numbers differ by construction, not by evidence: a task scores 1 under Any-Gold exactly when its mean fraction is positive, so the 12.58 pp gap at k=5 is definitional and carries no p-value. Across regimes, the static competition graph (M4) records 0.4350 on that metric against B3's 0.6184; we report this as an observed difference across two harnesses and two index bundles, not as a causal effect.

The multi-file picture is sharper than a single recall number suggests. Of 38 multi-file tasks, single-pass retrieval finds at least one gold file in 31/38 and all gold files in 3/38 at k=5. Ten of the 38 touch more than five gold files, for which strict all-gold at k=5 is arithmetically impossible. A budget-matched two-hop expansion trades the entry point for multi-file coverage without adding net recall: at k=5 it gains strict all-gold in 3 tasks while losing any-gold in 2, and neither shift is resolvable (exact paired p = 0.500 and p = 0.250).

Six runtime sites are audited, four against installed wheels and two inherited from upstream. Compaction first fires at turns 8–9; the `SkillToolset` preamble costs 333 tokens and adds 417 tokens at turn 1; all 49 new files created by gold patches are staged, with 0 hidden by `.gitignore`; and bare agent-side `pytest` meets an uninstallable plugin in 22 of 67 `fastapi` tasks by gold-test import, or 17 when restricted to the test files each patch touches.

Finally, 16 logged submissions define the noise floor. Five near-baseline 31B bundles score 12, 10, 10, 10, 10 of 58, mean 10.4, sample SD 0.894 tasks (95% CI [0.54, 2.57]). A byte-identical resubmission moved 2 tasks. The binomial standard error of a single 58-task split is 2.92 tasks. Differences below roughly 2.92 tasks are not evidence of a mechanism change.

---

## 1. What this paper does and does not claim

The competition serves one quantized Gemma 4 checkpoint on 4× L4 and runs a declarative ADK package against roughly 120 hidden SWE-bench-style tasks. A task scores only when the agent's patch passes a hidden `pytest` suite in a fresh container. There is no local scoring loop, so every claim here is either a deterministic re-execution over the 129 public development tasks or a re-derivation from logged submissions.

We make four contributions, each reproducible by one script:

1. **A one-mechanism retrieval ladder** (B0–B3) on identical snapshots, under three metric definitions with task-bootstrap intervals.
2. **A multi-file audit** separating "the patch touches several files" from "the retriever can return them all", plus a budget-matched two-hop test.
3. **Six runtime sites**, each labelled by evidence class: source-quoted, replay-verified, mitigated, inherited, or counted exposure.
4. **Leaderboard estimand rows**: repeat-pair shift, between-bundle dispersion, and split sampling error.

We quarantined legacy non-reproducible artifacts (intra-file symbol re-ranking, synthetic p-values, and non-canonical subsets) under `research/quarantined_legacy_audits/`. Every number here is emitted by `scripts/run_verified_experiments.py`; `scripts/reproduce_all.py` fails the build if any disagrees.

---

## 2. Six runtime sites, and what "verified" means here

Table 1 lists the sites. The evidence label matters more than the mechanism: a quote from an installed wheel is stronger than a plausible reading of upstream source, and a count over the development set is weaker than either.

### Table 1: Runtime sites with evidence class

| # | Site and quote location | Mechanism | Measured value | Evidence |
|---|---|---|---|---|
| 1 | `google/adk/apps/_configs.py:70` | Optional `token_threshold`; compaction drops non-model frames | threshold 14,336 tokens; interval 15; first fires turns 8–9 | Source-Verified + replay |
| 2 | `vllm/entrypoints/chat_utils.py:1512` | Upstream reads `reasoning`; ADK emits `reasoning_content` | 2 install sites | Inherited / Mitigated |
| 3 | `vllm/v1/sample/logits_processor/builtin.py:550` | Forces the end token when the thinking budget expires | inherited | Inherited |
| 4 | `swegemma/harness/agent_runner.py:1057` | Fallback stages with `git add -N .`, which honours `.gitignore` | 49 files across 11 tasks; 0 ignored | Replay-Verified |
| 5 | `google/adk/tools/skill_toolset.py:61` | Hidden preamble injected into the system instruction | 1,333 chars ≈ 333 tokens; +417 tokens at turn 1 | Source-Verified |
| 6 | `swegemma/harness/verification.py:628` | Grader runs `pytest -p no:anyio`; the agent's own shell does not | 22/67 gold `test_patch`; 17/67 touched test files | Exposure Count |

Sites 2 and 3 are labelled *Inherited*. Our host installs `google-adk`, `swegemma`, `adk_submission` and `adk_eval_core`, but not `vllm`; the two vLLM quotes are carried over from upstream audit. Site 2's mitigation is re-derived in the competition wheel: `adk_submission/resolvers/generation.py` defines `install_litellm_reasoning_patch` at line 195, mirrors `reasoning_content` into `reasoning` at line 70, and calls the installer at 2 module sites.

Site 4 corrects an earlier draft claiming 11 of 129 tasks risked losing files to `.gitignore`. Re-running `git check-ignore` on every created path in every base-commit snapshot yields 49 files across 11 tasks and 0 matches: exposure is zero. The trap is latent: `.pytest_cache` is ignored across all 11 snapshots, so scratch artifacts a naive `git add -N .` drops are agent-generated. `git add -N -f` remains correct.

Site 6 has three defensible denominators. Definition A asks whether the gold `test_patch` imports a non-default plugin: 21 of 67 via `inline_snapshot` or `dirty_equals`, or 22 of 67 with the single `anyio`-only task. Definition B restricts to test files each patch touches: 17 of 67. Definition C asks whether the full repository `tests/` tree imports either plugin: 67 of 67, a property of `fastapi`. The retracted figure 27 was definition A plus the five `dirty_equals` tasks, double-counting overlap: 18 + 5 + 1 = 24, minus the two tasks importing both plugins, gives 22. All three are exposure counts, not grader failures: the official grader installs wheels and passes `-p no:anyio`.

---

## 3. The retrieval ladder and the metric that flatters it

Table 2 reproduces the published static-graph aggregates. Table 3 is the new ladder, run over the same 129 snapshots.

### Table 2: Regime A static-graph aggregates (published record)

| Method | File R@5 | File R@10 | MRR | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|
| M1 lexical grep | 0.2284 | 0.3036 | 0.2212 | 127.8 | 2,367 |
| M2 "dense" | 0.2163 | 0.3810 | 0.2059 | 973.9 | 2,136 |
| M3 one-hop AST graph | 0.2265 | 0.2924 | 0.2098 | 74.2 | 2,416 |
| M4 `swe_toolkit` static | 0.4350 | 0.4587 | 0.4354 | 645.6 | 2,211 |
| M5 hybrid RRF | 0.4745 | 0.5701 | 0.4332 | 4.6 | 2,219 |

Three cautions belong with this table. **M2 is not a dense retriever**: it builds queries by lexical suffix matching and falls back to lexical order, scoring below M1. **M3 is not worse than M1**: -0.19 pp is indistinguishable from zero; the claim that code graphs degrade localization is unsupported here. **M5's latency is fusion-only**, measured on M4's cached ranking. Regime A retained no per-task series, so Any-Gold and Strict All-Gold are omitted.

### Table 3: One-mechanism ladder on 129 live snapshots

| Ranker | Any-Gold @5 | Mean-Fraction @5 | Strict All-Gold @5 | Any-Gold @5 95% CI |
|---|---:|---:|---:|---|
| B0 filename match | 0.3023 | 0.2520 | 0.2403 | [0.2248, 0.3798] |
| B1 file BM25 | 0.3488 | 0.2747 | 0.2326 | [0.2713, 0.4341] |
| B2 AST, no demotion | 0.5271 | 0.4252 | 0.3643 | [0.4419, 0.6124] |
| B3 AST + demotion | **0.7442** | **0.6184** | 0.5271 | [0.6667, 0.8140] |

Each step changes one mechanism: B0→B1 adds term weighting and length normalisation; B1→B2 replaces whole-file text with AST symbol extraction; B2→B3 adds `/tests/` demotion. The paired task changes are +4.65 pp, +17.83 pp, and +21.71 pp (cumulative B0→B3 is +44.19 pp). We report these as observed differences between rankers on a fixed task set.

The metric gap is the point most easily misread. Within B3, Any-Gold @5 = 0.7442 while Mean-Fraction @5 = 0.6184, a gap of 12.58 pp. That gap is definitional: Any-Gold is 1 exactly when Mean-Fraction is greater than 0, so the two differ only on tasks where some but not all gold files were found. There are 28 such tasks at k=5. No hypothesis test is applicable, and an earlier draft's p-value for this comparison was an artefact of treating the two definitions as independent measurements.

The cross-regime comparison is the one we are least willing to over-read. M4 records 0.4350; B3 records 0.6184 on the same metric and task count. The +18.34 pp difference is consistent with the index change, but the two runs differ in retrieval library, harness, and snapshot preparation. We report it as an observed difference across regimes and stop there.

---

## 4. Multi-file patches: what retrieval cannot return

Of 129 development patches, 38 touch more than one file. Table 4 stratifies them by how many gold files the patch touches, because the strict all-gold metric is bounded by that count.

### Table 4: Gold-file structure and strict feasibility

| Gold files in patch | Tasks | Any-Gold @5 | Strict All-Gold @5 | P(all \| any) |
|---|---:|---:|---:|---:|
| exactly 1 | 91 | 65/91 | 65/91 | 1.000 |
| exactly 2 | 19 | 14/19 | 3/19 | 0.214 |
| 3 to 5 | 9 | 8/9 | 0/9 | 0.000 |
| more than 5 | 10 | 9/10 | 0/10 | 0.000 |

Two facts follow. First, 10 tasks touch more than five gold files, so Strict All-Gold @5 is arithmetically impossible for them regardless of ranker quality; reporting a single all-gold rate over all multi-file tasks therefore mixes feasibility with performance. Second, the sharpest drop is at the single-to-multi boundary, where strict all-gold falls from 65/91 to 3/19, and the three-to-five bucket reaches 0/9 even though five candidates are still enough to cover it. Retrieval that reliably returns the first gold file does not reliably return the second.

### Table 5: Budget-matched two-hop expansion

| Budget | Arm | Any-Gold | Strict All-Gold | Mean-Fraction |
|---|---:|---:|---:|---:|
| k = 5 | single-pass | 31/38 | 3/38 | 0.3886 |
| k = 5 | two-hop | 29/38 | 6/38 | 0.3965 |
| k = 10 | single-pass | 34/38 | 6/38 | 0.5130 |
| k = 10 | two-hop | 32/38 | 7/38 | 0.4794 |

The treatment is budget-matched by construction: at k=5 it keeps the top three files from `locate` and fills two slots with in-repo files imported by, or importing, the first seed; at k=10 it keeps six and fills four. At k=5 strict all-gold rises from 3/38 to 6/38 (3 gains, 0 losses; exact paired sign test p = 0.250) while any-gold falls from 31/38 to 29/38 as 2 tasks lose their entry point (p = 0.500). At k=10 the same trade reappears: strict all-gold gains 3 tasks against 2 losses (p = 1.000) while any-gold falls from 34/38 to 32/38 with 1 gain against 3 losses (p = 0.625). A two-hop walk therefore converts entry-point hits into multi-file hits; at a fixed budget it adds no measurable coverage, and mean-fraction is flat at k=5 (0.3886 to 0.3965) and lower at k=10 (0.5130 to 0.4794).

The cost is not the expansion. Building the import graph once per snapshot has a median of 4.48 s against 4.20 s for a single `locate` call, so the graph costs more than the search it is meant to improve, before the agent reads anything.

---

## 5. Leaderboard: three estimands, not one

Kaggle displays two decimals, which hides the integer that determines the score. Recovering `k/58` from the logged fractions is what makes these rows exact.

### Table 6: Leaderboard estimand rows

| Row | Quantity | Value | Interpretation |
|---|---|---|---|
| 1 | identical-code repeat on a fixed split | 12/58 vs 10/58 | a 2-task shift on identical artifacts |
| 2 | five near-baseline 31B bundles | 10.4/58, SD 0.894 | between-bundle dispersion at 4 df |
| 3 | split sampling error, one 58-task draw | SE 2.92 tasks (5.04 pp) | error of evaluating on only 58 tasks |

Row 1 is the cleanest evidence we have that the harness is stochastic on identical artifacts: `exp05` scored 12/58 and its byte-identical control scored 10/58, a shift of 2 tasks. Row 2 pools five bundles that differ in prompt or tool surface but not in model scale; its dispersion is the between-bundle noise, with only 4 degrees of freedom, so the interval on the SD is wide ([0.54, 2.57] tasks). Row 3 is a different quantity: the error incurred by evaluating on 58 tasks rather than the hidden set. Conflating rows 2 and 3 produces the familiar but wrong claim that a two-task leaderboard move is meaningful.

The 16 logged submissions comprise 12 scored 31B entries, 3 E4B entries, and 1 unscored entry. The E4B line is closed: genuine E4B submissions cluster at 3 tasks, and equipping E4B with the same toolkit (`e4b_v4`) did not move it. We do not attribute the 31B spread to any single mechanism, because the bundles differ in more than one way and the noise per row is comparable to the gaps.

---

## 6. What we would do differently, and how to check us

Four practices follow directly from the measurements:
- **Report both recall definitions, and never test between them.** Mean-Fraction measures retrieval coverage; Any-Gold diagnoses entry-point discovery. Testing between them inflates significance for free.
- **State denominator, budget, and split.** A 38-task multi-file subset and a 129-task set are distinct. Strict all-gold at k=5 is infeasible for patches touching six files. The corrected record uses 129 for development and 58 for leaderboard splits.
- **Treat 2-hop as a budget decision, not a feature.** At a fixed candidate budget it trades entry-point hits for multi-file hits, not net coverage.
- **Prefer a deterministic producer to a remembered constant.** `scripts/run_verified_experiments.py` writes four JSONs; `scripts/reproduce_all.py` binds every number to a JSON Pointer, rejects unbound numbers and legacy strings, enforces word budgets, and emits `docs/number_audit.csv`.

The runtime sites are worth fixing even where exposure is zero, because failure is silent: dropped new files, stripped tool frames, or broken imports look like model reasoning errors from the outside. Naming the site, wheel, and line separates diagnosis from guesswork.

---

### Figures

All five figures and the listing card are rendered from `research/verified_json/*.json` by `scripts/generate_paper_figures.py`; none contains a hand-typed value.

- **Figure 1** — the harness and the six audited sites: `assets/paper_figures/fig1_harness_architecture.png`
- **Figure 2** — retrieval ladder and the metric definition: `assets/paper_figures/fig2_retrieval_ladder.png`
- **Figure 3** — baselines by repository and the budget-matched two-hop arm: `assets/paper_figures/fig3_baselines_and_twohop.png`
- **Figure 4** — the submission ledger and the three estimand rows: `assets/paper_figures/fig4_leaderboard_power.png`
- **Figure 5** — patch anatomy and measured exposure: `assets/paper_figures/fig5_patch_anatomy_exposure.png`
- **Listing card** — thumbnail for the writeup gallery: `assets/paper_figures/fig0_card_thumbnail.png`

---

### Reproducibility checklist

- [x] One producer for all numbers: `scripts/run_verified_experiments.py` → `research/verified_json/*.json`.
- [x] One gate: `scripts/reproduce_all.py` → `docs/number_audit.csv`, non-zero exit on any mismatch.
- [x] Six figures rendered from the same JSON: `scripts/generate_paper_figures.py`.
- [x] Public kernels: [g4-paper-graph-benchmark](https://www.kaggle.com/code/narisettichaitanya/g4-paper-graph-benchmark), [g4-paper-noise-mde](https://www.kaggle.com/code/narisettichaitanya/g4-paper-noise-mde).
- [x] Legacy calibrated artifacts quarantined: `research/quarantined_legacy_audits/`.

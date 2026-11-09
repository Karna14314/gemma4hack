# PAPER_FINAL_DRAFT.md — reference copy of the final draft paper (Gemma 4 Developer Agent Paper Track)

Stored from user-provided final draft (message time 2026-11-09T08:28:15Z). Use this as the authoritative section-by-section source when writing the Kaggle writeup; do not drift from these numbers without re-checking the cited files.

Title: A 0.17 Plateau: Replication, Harness Mechanics, and Localization Benchmarks for Offline Gemma 4 SWE Agents
Author: Narisetti Chaitanya Naidu · Kaggle: narisettichaitanya · Paper Track, Google – The Gemma 4 Developer Agent Competition

---

## Abstract

We study offline Gemma 4 software-engineering agents under the competition's fixed harness (28 tool calls, 8 minutes, 32,768-token context). Across 14 scored leaderboard submissions, none produced a change distinguishable from run-to-run noise: five near-identical runs passed 12, 10, 10, 10 and 10 of 58 tasks. The one apparent gain, a patch-integrity check scoring 0.20 (12/58), did not reproduce under a byte-identical re-submission (10/58). We separate run-to-run noise (SD ≈ 0.9 tasks) from cross-split sampling error (≈ 3 tasks) and give practices for small leaderboards. We contribute a sourced table of harness mechanics, marking what was already public and what we did not measure; a 129-task issue-localization benchmark with two labeled recall instruments, on which BM25+AST file recall@5 is 0.435 versus 0.228 for lexical grep (mean-fraction instrument) and 0.744 (any-gold instrument over all files); and a failed prediction: deterministic localization did not lift the 4B E4B model (0.05, against a predicted 0.09–0.13). We collected no traces, so we claim no mechanism. Code, per-task results and notebooks are public.

## Contributions and released artifacts

1. Measurement protocol (§2). Every submission as integer tasks passed with artifact hashes: research/paper_figs/ledger.csv.
2. Harness mechanics (§3). Six mechanisms with sources, prior public reports and measured score effects; scripts/probe_thinking_budget.py.
3. Localization benchmark (§4). 129 tasks, five methods, two labeled instruments: public kernel narisettichaitanya/g4-paper-graph-benchmark (CPU, about 3 minutes) and eval_results/instrument_b.json.
4. swe-toolkit skill (§5). A deterministic locate/inspect/verify ADK skill (skills/swe-toolkit/), released as is. It did not beat the baseline, and we report that.

## 1. Setting and questions

The competition requires an offline ADK agent package on 4×L4 GPUs using gemma-4-31b-it-qat-w4a16-ct or gemma-4-e4b-it-qat-w4a16-ct. Each task allows 28 tool calls, 8 minutes, 80 turns and 240-second command timeouts; the public leaderboard resolves 58 tasks. We ask: (1) what can a participant conclude from leaderboard differences of a few tasks? (2) Which harness mechanics can silently break a submission, and which were already documented? (3) Which retrieval strategy localizes issues best when tool output is capped at 5,000 characters? (4) Does offloading localization to deterministic code lift the 4B E4B model?

## 2. What the public leaderboard can resolve

Table 1 lists every scored submission as integer tasks passed out of 58. For every row in ledger.csv the displayed score equals floor(100 × tasks / 58) / 100 (asserted in scripts/make_paper_figs.py), so the board appears to truncate to two decimals and a displayed score can hide a one-task difference (0.05 is 3 tasks, 0.06 is 4).

Table 1. Scored submissions, tasks passed of 58.
Family (what changed) | Scale | Tasks passed
exp01, exp02 (early prompts) | 31B | 3, 5
exp03 (byte-exact public baseline replica) | 31B | 10
exp05 family: exp05 patch-integrity gate; E0 byte-identical re-submission; exp08, exp10, exp12 (prompt, STATE header, timing variants) | 31B | 12, 10, 10, 10, 10
31B fallback bundle | 31B | 8
exp_sampling (temperature 1.0, top_p 0.95, top_k 64) | 31B | 8
exp14 (lean swe-toolkit skill) | 31B | 9
exp_think1024 (thinking budget 4096 → 1024) | 31B | pending
exp11_e4b; e4b-v2; e4b_v4 (+ swe-toolkit) | E4B | 4, 3, 3

[Insert fig1.png here]
Figure 1. Tasks passed per submission. Dark band: anchor mean ± 1 SD (10.4 ± 0.89). Light band: ± 2.9 tasks, cross-split sampling error. exp05 and E0 are the same artifact.

Two noises. The five exp05-family runs give a mean of 10.4 tasks (0.179) and SD 0.89. This is run-to-run variation on a fixed 58-task set, estimated from five runs. Drawing a different 58 tasks (the hidden split) adds binomial sampling error, sqrt(58 × 0.179 × 0.821) ≈ 2.9 tasks. The first limits what a same-split A/B comparison can resolve; the second limits what any public score says about the private split.

Minimum detectable effect. For two single runs the SD of the difference is 0.89 × √2 ≈ 1.26 tasks, so at 80% power and α = 0.05 a single run can resolve roughly 3.5 tasks (about +0.06) at best; that bound is approximate because the SD itself comes from five runs. Your interventions plausibly fell below this resolution, so a null result is a flat response within detection limits, not proof of no effect.

Replication control. exp05 added a pre-submit patch-integrity gate (git status, git add -N -f) and scored 12/58 (0.20), 1.8 SD above the five-run mean. A byte-identical re-submission (E0, same SHA-256 prefix 2ba7f9b1…) scored 10/58 (0.17). One artifact therefore produced 12 and 10, and we credit the gate with no gain. For two single runs the SD of the difference is 0.89 × √2 ≈ 1.26 tasks, so a 2-task gap is 1.6 SD and a 3-task gap 2.4 SD. The other family members (+554 characters of tool prose, a plain-text STATE header, a longer timing buffer) are indistinguishable from the reruns.

Below the anchor. Temperature 1.0 (8), the 31B fallback bundle (8) and the lean toolkit (9) fall 1.4–2.4 tasks below the mean. Eight tasks is about 2.7 SD, which is suggestive for temperature 1.0, but each is a single run and we do not claim harm. exp_think1024 was pending when this was written.

Practices. (i) Report integer tasks passed and the artifact hash. (ii) Re-submit a byte-identical artifact before crediting a gain. (iii) Report run-to-run SD and cross-split error separately. (iv) Treat differences of two tasks or fewer as unresolved.

## 3. Harness mechanics

Table 2 lists mechanisms that can silently break a submission, where each comes from, whether others had reported it, and whether we measured a score effect. None has an effect resolvable on the public board.

Table 2. Mechanisms.
Mechanism | Source | Reported before? | Score effect
Compaction removes tool calls and outputs above a token threshold; only plain-text model messages survive | Harness README; not in installed wheels (see below) | Yes, public posts | STATE header (exp10): 10/58, unresolved
vLLM rejects prompt + max_output > 32,768 tokens; with 8,192 output, prompts over 24,576 crash | Public posts; our arithmetic | Yes | Not isolated
git add -N . skips ignored new files; fix git add -N -f | Our reading of submit_patch; 8.5% of gold patches create files | Not found | exp05 gate: 12 vs 10 on rerun, unresolved
vLLM 0.19.1 reads reasoning, the client sends reasoning_content, so thoughts drop between tool turns | chat_utils.py:1512 | Not checked | Not measured
thinking_token_budget is enforced by a logits processor under the gemma4 parser, independent of max_tokens | protocol.py:183,519; builtin.py:294; payload probe | Field public; enforcement not checked | exp_think1024 pending
SkillToolset: temp-dir materialization, list-valued args, untruncated output | skill_toolset.py:689 and related | Not found | n/a

Compaction values are unresolved. The installed ADK defines the compaction fields without defaults (apps/_configs.py:61,65,70,80). The harness README of 2026-10-13 gives interval 15, overlap 2, threshold 14,336 and retention 5. Public posts from late October report interval 5 and postdate the README; another quotes interval 15 with threshold 32,768. We could not verify the operative values from the wheels. Probe. Capturing the outgoing request at the acompletion call site, two bundles differed only in thinking_token_budget (1024 vs 4096).

## 4. Localization benchmark

Data. 129 tasks from the competition's evaluation data (fastapi 67, rich 48, requests 13, httpx 1). Gold files are the patch's paths; gold symbols are the AST nodes it modifies (121 tasks have identifiable symbols; graphs exist for 125). Gold patches are small: 70.5% touch one file, 29.5% touch two or more, 8.5% create new files.

Methods. M1 lexical grep. M2 dense retrieval over the released 256-dimensional embeddings. M3 one-hop expansion over the AST call graph. M4 our swe_toolkit locator: stopword-filtered BM25 plus AST, traceback and backtick boosts, file score = max(node) + 0.25 × sum of the top three. M5 reciprocal-rank fusion of M4 and M2 with a caller-edge bonus.

Two instruments. Instrument A (public kernel) scores the mean per-task fraction of gold files found in the top K, over candidates that are graph nodes. Instrument B scores any-gold recall (a hit if any gold file is in the top K) over every .py file on disk. B is more lenient and its candidate set is larger, so numbers from A and B are not comparable. We ran M1–M5 on A and only the shipped engine on B.

Table 3. File recall on Instrument A, 129 tasks.
Method | R@1 | R@5 | R@10
M1 lexical grep | 0.050 | 0.228 | 0.304
M2 embedding | 0.058 | 0.216 | 0.381
M3 one-hop graph | 0.050 | 0.227 | 0.285
M4 BM25+AST | 0.266 | 0.435 | 0.459
M5 hybrid RRF | 0.247 | 0.475 | 0.570

[Insert fig2.png here]
Figure 2. Left: Instrument A, mean per-task fraction of gold files in top K, M1–M5. Right: Instrument B, any-gold recall over all files, shipped engine.

Findings. (1) Structure helps: M4 and M5 roughly double grep at K = 5. (2) One-hop expansion adds nothing over grep (0.227 vs 0.228). 80.9% of raw one-hop neighborhoods exceed the 5,000-character tool cap, one plausible reason that we did not isolate. (3) Embeddings help only deep: M2 trails M1 at K = 5 but leads at K = 10 (0.381 vs 0.304), and fusion gains most there (0.570). (4) Tracebacks explain part of the gap: on the 13 tasks with a traceback or explicit path, M4 and M5 reach 0.654 and 0.731 at K = 5 against 0.269 for grep; on the 116 symptom-only tasks, 0.392 and 0.432 against 0.231. (5) M4 is stronger on fastapi (0.479) than rich (0.280); M5 is more even (0.421, 0.436).

Instrument B. The shipped engine reaches 0.419 / 0.651 / 0.744 / 0.829 at K = 1 / 3 / 5 / 10 (recomputed from eval_results/instrument_b.json). M5 was not run on B, so we make no claim about M5 versus the shipped engine there.

Symbols are harder than files. On the 121 tasks with gold symbols, the shipped ranking reaches symbol recall 0.149 / 0.248 / 0.314 / 0.355 at K = 1 / 3 / 5 / 10 (bare-name match, recomputed from committed per-task results), against any-gold file recall@5 of 0.744. Landing a read on the modified function is the harder step.

## 5. Scale and a failed prediction

The E4B model passed 4, 3 and 3 tasks (Table 1), against a 31B anchor of 10.4. Before submitting e4b_v4 we predicted, in docs/SCORE_PREDICTION_AND_ROADMAP.md, that moving localization and verification into a deterministic stdlib skill (file recall@5 0.744 on Instrument B, plus a read-only patch gate) would raise E4B to 0.09–0.13. It scored 0.05 (3/58). The same skill on 31B (exp14) passed 9, against the 10.4 anchor.

The prediction failed. Three explanations fit and we cannot separate them: the 4B model's exact-string edit fidelity, state loss across compaction, or the skill being invoked rarely or its output ignored. We have no runtime traces: both bundles declare and instruct the skill, but no invocation counts exist. We therefore state the failure without a mechanism. A trace study of 15–20 development tasks with per-call tool logs is the obvious next step.

## 6. Related work

SWE-bench (Jimenez et al., 2024) defines the task of resolving real GitHub issues. SWE-agent (Yang et al., 2024) showed that interface design, including guarded edit commands, changes agent success; our patch gate follows that spirit, though we could not resolve its effect. Agentless (Xia et al., 2024) argues for a fixed localize–repair–validate pipeline. LocAgent (Chen et al., 2025), RepoGraph (Ouyang et al., 2024) and OrcaLoca (Yu et al., 2025) use repository graphs or agentic search for localization. We differ in regime and finding: a 32k-context offline model with 5,000-character tool output, where BM25+AST structure helps file recall but one-hop graph expansion adds nothing over grep. We did not compare against these systems, whose settings differ.

## 7. Limitations and reproducibility

Limitations. The public split has 58 tasks; every configuration except the anchor family has one run, and the anchor SD comes from five runs. We have no traces. Instrument A uses released graph and embedding artifacts rather than repository checkouts. Per-task ranks are committed only for the shipped engine on B; M1–M5 on A are aggregates. We omit two development-time variants (an identifier-based path boost and a span-level symbol re-ranker) because their code and per-task data are not in the release. The ten swe-toolkit playbooks are released but not evaluated downstream. exp_think1024 had no score when this was written.

Reproducibility. Instrument A: run narisettichaitanya/g4-paper-graph-benchmark (CPU, about 3 minutes) on the competition dataset. Instrument B needs the evaluation snapshots (44 GB); regenerating the shipped engine's ranks takes about 30 minutes (command in docs/PAPER_ASSETS.md). research/paper_figs/ holds the ledger, figure data and scripts/make_paper_figs.py. The thinking-budget probe is scripts/probe_thinking_budget.py. Bundle SHA-256 prefixes are in ledger.csv.

## References

• Jimenez, C. E., et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues?
• Yang, J., et al. (2024). SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering.
• Xia, C. S., et al. (2024). Agentless: Demystifying LLM-based Software Engineering Agents.
• Chen, Z., et al. (2025). LocAgent: Graph-Guided LLM Agents for Code Localization.
• Ouyang, S., et al. (2024). RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph.
• Yu, Z., et al. (2025). OrcaLoca: An LLM Agent Framework for Software Issue Localization.

---

## Data cross-references (for section-by-section writing)

| section | key numbers | source file |
|---|---|---|
| §2 Table 1 / §2 noise | exp05-family 12,10,10,10,10; mean 10.4; SD 0.89; cross-split ≈ 2.9; E0 = 10 | research/paper_figs/ledger.csv; scripts/make_paper_figs.py assertion |
| §3 Table 2 | compaction interval unresolved (README 15 vs public 5); git add -N -f; vLLM >32,768 crash | docs/PAPER_ASSETS.md §4; PAPER_VERIFY.md §D |
| §4 Table 3 / Fig 2 | M4 BM25+AST R@5 0.435 vs grep 0.228 (Instrument A); B shipped engine 0.744 any-gold @5 | research/paper_eval_outputs/paper_experiments.json:experiment1; eval_results/instrument_b.json |
| §4 symbols | shipped symbol recall 0.149/0.248/0.314/0.355 (121 tasks) | eval_results/t6_results_v4_repro.json recompute; PAPER_ASSETS.md §3 |
| §5 E4B failed prediction | E4B 4,3,3 tasks vs predicted 0.09–0.13; exp14 = 9 tasks | research/paper_figs/ledger.csv; docs/SCORE_PREDICTION_AND_ROADMAP.md |
| §7 reproducibility | Instrument B regen ≈ 30 min; fig scripts/make_paper_figs.py | docs/PAPER_ASSETS.md |

Known caveats to carry into the writeup:
- exp_think1024 (ref 58149803) pending scoring; do not cite a score.
- Draft arithmetic "77/464 = 0.166" is wrong → 79/464 = 0.170 (see PAPER_VERIFY.md §B); SD 0.89 covers only the 5-run exp05-family subset.
- v4 symbol recompute (0.1488/0.2479/0.3140/0.3554) differs by 1-2 tasks vs draft Table 2D (0.1570/0.2310/0.3060/0.3640) — within AGENTS.md §9 noise but a real mismatch.
- base/v3 and M1/M2 per-task ranks not committed; v5/v6 symbol re-rankers not committed runnable code; Fig3 omitted.
- Compaction operative values (interval, threshold) not verifiable from installed wheels; live README says 15/14,336, public posts conflict.

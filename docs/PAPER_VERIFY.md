# PAPER_VERIFY.md — verification + literature pass for the 3,000-word paper

**Prepared:** 2026-11-09 (message time 2026-11-09T06:32:08Z) | Read-only repo work except creating this file; no Kaggle submissions; no evals/training; network used ONLY to read public pages. Every number cited as `path:line` or `path` + key. Public pages cited with URL/title/authors/year; nothing invented; anything not opened = UNVERIFIED.

---

## A. INSTRUMENT RECONCILIATION — Table 2A vs Section 3.1 numbers

### A.1 Code that produced each number set

| Number set | Producing code | Input data | Candidate set | Recall definition | Tasks | Key values |
|---|---|---|---|---|---|---|
| Table 2A (M4 swe_toolkit file R@5 0.4350, R@10 0.4587) | `research/kernel_paper_eval/paper_eval.py` (runs on Kaggle; reads `/kaggle/input/.../tasks.jsonl` + per-task `graphs/*.json` + `embeddings/*.npz`) | Graph nodes from `node_id_to_text` (qualname → node text); embedding-key fallback for tasks without graphs | GRAPH NODES only (125 in-graph tasks use code graphs; others fall back to embedding keys) | mean per-task file-recall fraction: `hit_count / len(F_gold)` averaged over tasks, where a gold file is "hit" if any ranked node `nid == fg or nid.startswith(fg+".") or fg.startswith(nid+".")` | N=129 "all" (plus N=125 "in_graph" subset) | M4: R@1 0.2661, R@3 0.3798, R@5 **0.4350**, R@10 **0.4587** (`research/PAPER_TABLES.md:17-23`) |
| Section 3.1 (file R@5 0.744, R@10 0.829) | `scripts/t6_run.py` (rebuilt v4 file-recall + symbol Hit on 129 tasks); cross-reported in `docs/FINAL_HARNESS_COMPARISON.md:41` | `.py` files on disk inside filesystem snapshots under `eval_snapshots/` | ALL `.py` files on disk (AST-indexed by `_index.py`, not graph-constrained) | any-gold binary per task: `file_hit = bool(any gold file in top-k)`, aggregated as hits/n | N=129 | v4: R@1 0.419, R@3 0.651, R@5 **0.744**, R@10 **0.829** (`docs/PAPER_TRACK_DRAFT.md:111-113`) |

Source-map:
- `paper_eval.py` is the locked instrument behind `paper_experiments.json` (23,984 B, full 129-task instrument) and `research/PAPER_TABLES.md` / `research/paper_eval_outputs/PAPER_TABLES.md` (identical, 7,878 B each).
- `t6_run.py` header: "Rebuilt eval runner: regenerate v4 file recall + symbol Hit on 129 tasks. Uses the locked v4 engine (skills/swe-toolkit/scripts/_index.py, commit 41c2854) on snapshots extracted into eval_snapshots/." Expected file R@1 0.419, R@3 0.651, R@5 0.744, R@10 0.829.

### A.2 Why the same engine scores differently

Three independent differences, none of which is an error:

1. **Recall definition (dominant).** Table 2A averages the *fraction* of a task's gold files recovered in top-k (`hit_count/len(F_gold)`), so a 2-file task where only 1 gold file is found scores 0.5 for that task. Section 3.1 uses binary any-gold (did we find ≥1 gold file?), aggregated hits/n. Multi-file tasks are common (29.5% touch 2+ files; `research/PAPER_TABLES.md:93`), which depresses the mean-fraction metric relative to any-gold. Hence 0.4587 (Table 2A) vs 0.829 (Section 3.1) at R@10 for the same v4 swe_toolkit engine.

2. **Candidate set.** Table 2A M4 ranks only graph nodes (or embedding-key fallback), i.e. symbols present in the code graph. Section 3.1 ranks every `.py` file on disk via `_index.py` AST-indexing (all files, no graph constraint). Broader candidate coverage → higher any-gold recall.

3. **Aggregation scope identical (N=129 "all").** So N is not the cause; definitions (1) and input (2) are.

**Verdict:** The two numbers are reconcilable and both correct for their own metric; the draft must label Table 2A as "mean per-task file-recall fraction (graph-node candidates)" and Section 3.1 as "any-gold file recall (all files on disk)" to avoid an apparent contradiction. No rerun needed (>5 min cap respected; nothing executed).

---

## B. NOISE POOL — all scored 31B submissions

`exp_think1024` (ref 58149803, 2026-11-09) is **pending scoring** and excluded from all pooled recomputations. Tasks passed = round(score × 58). Source: `docs/ENV_AUDIT.md:4.1` (full queue) + `docs/LEADERBOARD_STATS.md`.

| ref | date | bundle | sha256 | config diffs vs exp05 | score | tasks | source |
|---|---|---|---|---|---|---|---|
| 56793672 | 2026-10-03 | exp01 | NOT FOUND | baseline v1 (thinking on, 6 min / 60 calls / 120 turns, prompt rewrite) | 0.05 | 3 | ENV_AUDIT.md:4.1 |
| 56812498 | 2026-10-04 | exp02 v2 | NOT FOUND | 4 bundled changes (prompt + tool contract) | ~0.08 | 5 | ENV_AUDIT.md:4.1 |
| 57037122 | 2026-10-10 | exp03 | e3be904ca4823b9d…0a68 | byte-exact public 0.17 replica; no patch-integrity check; 6 tools (+3 graph) | 0.17 | 10 | ENV_AUDIT.md:4.1; RESULTS.md:164 |
| 57553805 | 2026-10-23 | exp05 | 2ba7f9b118ea1837d…1774 | BASELINE: patch-integrity (`git status --short` + `git add -N -f`), temp 0.2, 28 calls, 8192/4096, 9 tools (+3 graph) | 0.20 | 12 | ENV_AUDIT.md:4.1; RESULTS.md:212 |
| 57618114 | 2026-10-25 | exp08 | NOT FOUND | +554-char tool prose (regression); 6 tools | 0.17 | 10 | ENV_AUDIT.md:4.1 |
| 57654236 | 2026-10-26 | exp10 | NOT FOUND | max_output 6144 (vs 8192); STATE header; 6 tools | 0.17 | 10 | ENV_AUDIT.md:4.1 |
| 57697341 | 2026-10-27 | exp11_e4b fallback | NOT FOUND | E4B alias rejected → 31B fallback package | 0.13 | 8 | ENV_AUDIT.md:4.1; AUDIT_E4B_AND_PAPER.md:24 |
| 57736284 | 2026-10-28 | exp12 | 203fe180e026779d…afb5 | max_time 9 min (vs 8); +592-char prompt; near-exact exp05 | 0.17 | 10 | ENV_AUDIT.md:4.1; AUDIT_E4B_AND_PAPER.md:140 |
| 57836949 | 2026-10-31 | E0 control | 2ba7f9b1… (byte-identical to exp05) | NONE (byte-identical artifact) | 0.17 | 10 | ENV_AUDIT.md:4.1 |
| 57933618 | 2026-11-03 | exp14 | NOT FOUND | 9 tools + SkillToolset (swe-toolkit); lean prompt 5,767 chars | 0.15 | 9 | ENV_AUDIT.md:4.1 |
| 58096981 | 2026-11-07 | exp_sampling | NOT FOUND | temp 1.0 / top_p 0.95 / top_k 64 off exp05 | 0.13 | 8 | ENV_AUDIT.md:4.1 |

### B.1 Recomputed pooled mean / SD

- **(i) Byte-identical artifacts only** (exp05 + E0, both sha 2ba7f9b1…): 12 + 10 = **22 tasks / 116 = 0.190**; mean 11 tasks/run; 2 runs. Proof the same artifact does not reproduce its score (0.20 → 0.17).
- **(ii) exp05-family** (exp05, exp08, exp10, exp12, E0): tasks [12,10,10,10,10] = **52 / 290 = 0.179**; mean 10.4; **sample SD = 0.89** (matches `docs/AUDIT_E4B_AND_ANCHOR.md:58`). This is the set the 0.89 SD actually covers.
- **(iii) All scored 31B** (11 runs above): tasks [3,5,10,12,10,10,8,10,10,9,8] = **95 / 638 = 0.149**; mean 8.64; sample SD ≈ 2.76. (Including the two early outlier runs exp01/exp02 pulls the pool down.)
- **Draft's "eight scored runs"** (exp05, exp03, exp08, exp10, exp12, E0, exp14, exp_sampling = 0.20, 0.17×5, 0.15, 0.13): tasks = 12 + 5×10 + 9 + 8 = **79**, denominator 8×58 = 464 → **79/464 = 0.170**.

### B.2 Draft arithmetic check (§5 of docs/PAPER_TRACK_DRAFT.md)

The draft states "≈77/464 = 0.166". That is **incorrect**: 12 + 5×10 + 9 + 8 = 79, so it should be **79/464 = 0.170** (off by 2 tasks ≈ 0.004, within noise but still a misstatement). Separately, the draft's SD of 0.89 applies only to the 5-run exp05-family subset [12,10,10,10,10] (sample SD 0.894), not to the 8-run set (sample SD 1.13) nor all 11 runs (sample SD 2.76).

---

## C. TRACE EVIDENCE — e4b_v4 and exp14 skill invocation

### C.1 What exists (static, in repo)
- `bundles/exp14_lean_toolkit/agent.yaml:15` and `tracks/e4b_small/bundles/e4b_v4_swe_toolkit/agent.yaml:12` both declare `skills/swe-toolkit` (SkillToolset).
- Prompts instruct `run_skill_script`: exp14 `bundles/exp14_lean_toolkit/prompts/system.md:11-12` (Locate + Verify); e4b_v4 `tracks/e4b_small/bundles/e4b_v4_swe_toolkit/prompts/system.md:8,11` (Locate `<=500 chars>` + Verify).
- Skill bundle present: `SKILL.md` (name `swe-toolkit`, 3 modes locate/inspect/verify), `scripts/swe.py`, `scripts/_verify.py`, `scripts/_guard.py` for both exp14 and e4b_v4.
- `tracks/e4b_small/verify_bundle_e4b_v4.py:65-69` asserts the prompt contains exactly 2 `run_skill_script` calls (static check, passes at bundle build).

### C.2 Runtime traces (was the skill actually invoked at scoring time?)
**NONE.** No `runs/` directories exist locally (`glob **/runs/**/*` → no files; `kaggle_work/*/runs/` is gitignored and not pulled). The submission_notebook.ipynb files contain only the skill *code*, not execution logs. Per `docs/AUDIT_E4B_AND_ANCHOR.md:114-117`: "We have zero traces — no call counts, no elapsed times, no patch sizes — for any of the ten submissions." So we cannot confirm whether `run_skill_script` was invoked during the actual e4b_v4 (ref 57889741, score 0.05) or exp14 (ref 57933618, score 0.15) Kaggle runs. The claim "the skill helped exp14 reach 0.15" is **unverifiable from local traces**.

---

## D. PUBLIC SOURCES

### D.1 Kaggle discussion + public notebooks for gemma-4-developer-agent

Our five "discovered" harness claims vs public record:

| # | Our claim | Public source (URL, date, author) | Status |
|---|---|---|---|
| (a) ADK compaction behavior (compaction_interval, token_threshold) | Kaggle discussion #743456 "Does events compaction ever trigger before the context limit?" (Narendar Kumar Ale, ~1 month ago); #744692 "Compaction can't trigger at token_threshold 32,768" (Avery Wright, ~16 days ago); #744794 "compaction loses tool results" (mahmoud al-ghraibeh, 16 days ago); #747186 "compaction at 14,336 tokens (interval 5, overlap 2, retention 5)" (Whisper Last, 9 days ago) | https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/743456 ; /discussion/744692 ; /discussion/744794 ; /discussion/747186 | **ALREADY PUBLIC** — but note discrepancy: public record and starter notebook say compaction_interval = 5 / token_threshold = 14,336, whereas our repo's live HARNESS_README (2026-10-13) and COMPETITION_RESOURCES.md:86 state interval = 15. Interval conflict unresolved. |
| (b) vLLM prompt+max_output overflow (>32,768 crashes / ContextWindowExceededError discards patch) | #744692 (Avery Wright): "vLLM rejects any request where prompt + max_output_tokens > 32,768... 44 of 44 overflowed sessions had an empty patch"; also #743456 | https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/744692 | **ALREADY PUBLIC** (matches our repro #2 ceiling_32768, docs/ENV_AUDIT.md:65). |
| (c) .gitignore / `git add -N` silent drops new files | Not found in searched Kaggle discussions | — | **UNKNOWN** (not confirmed publicly). |
| (d) thinking_token_budget engine-enforced | #744566 "thinking_budget and seed are missing from HTTP requests" (veronikayaitskikh; admin ryanholbrook: "I will patch"); #744794: "thinking_budget / seed not sent ... all fixed in the latest wheelhouse" (ryanholbrook) | https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/744566 ; /discussion/744794 | Existence of the parameter = **ALREADY PUBLIC**. Our specific engine-enforcement verification (thinking budget actually reaches vLLM and changes behavior) = **NEW** (our own wheelhouse repro, scripts/probe_thinking_budget.py). |
| (e) Skills usage (SkillToolset temp dir, run_skill_script cold-call) | Not found in searched Kaggle discussions; third-party notes (sweeden-ttu/developer-agent) list predefined tools run_command/submit_patch/get_status and `load_skill_resource` but not SkillToolset temp-dir semantics | https://github.com/sweeden-ttu/developer-agent | **UNKNOWN** (skill cold-call and temp-dir materialization not confirmed publicly). |

### D.2 Academic references — exact bibliographic data (verified by opening pages)

1. **SWE-bench.** Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., Narasimhan, K. "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?" ICLR 2024. arXiv:2310.06770 (submitted 2023-10-10, v3 2024-11-11). 2,294 issues across 12 Python repos; Claude 2 solves 1.96%. URL: https://arxiv.org/abs/2310.06770 ; https://github.com/SWE-bench/SWE-bench (MIT).
2. **SWE-agent.** Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., Press, O. "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering." NeurIPS 2024. arXiv:2405.15793 (submitted 2024-05-06). Resolves 12.29% of SWE-bench full test set (SOTA open agent at the time). URL: https://arxiv.org/abs/2405.15793 ; https://github.com/princeton-nlp/SWE-agent.
3. **Agentless.** Xia, C. S., Deng, Y., Dunn, S., Zhang, L. "Agentless: Demystifying LLM-based Software Engineering Agents." arXiv:2407.01489 (submitted 2024-07-01, v2 2024-10-29); PACMSE FSE 2025 (10.1145/3715754). Three-phase localization/repair/validation; 32.00% (96 fixes) on SWE-bench Lite at $0.70/issue. URL: https://arxiv.org/abs/2407.01489 ; https://dl.acm.org/doi/10.1145/3715754.
4. **LocAgent.** Chen, Z., Tang, X., Deng, G., Wu, F., Wu, J., Jiang, Z., Prasanna, V., Cohan, A., Wang, X. "LocAgent: Graph-Guided LLM Agents for Code Localization." ACL 2025 (10.18653/v1/2025.acl-long.426, pp. 8697–8727). arXiv:2503.09089 (submitted 2025-03-12). Graph-based code localization; 92.7% file-level localization with fine-tuned Qwen-2.5-Coder-32B. URL: https://arxiv.org/abs/2503.09089 ; https://aclanthology.org/2025.acl-long.426/ ; https://github.com/gersteinlab/LocAgent (Apache-2.0).
5. **RepoGraph.** Ouyang, S., Yu, W., Ma, K., Xiao, Z., Zhang, Z., Jia, M., Han, J., Zhang, H., Yu, D. "RepoGraph: Enhancing AI Software Engineering with Repository-Level Code Graph." ICLR 2025. arXiv:2410.14684 (submitted 2024-10-03, v2 2025-03-18). Repository-level code-graph plug-in; SOTA among open-source SWE-bench frameworks. URL: https://arxiv.org/abs/2410.14684 ; https://proceedings.iclr.cc/paper_files/paper/2025/hash/4a4a3c197deac042461c677219efd36c-Abstract-Conference.html ; https://github.com/ozyyshr/RepoGraph.

Additional verified (localization / code retrieval):
6. Wang et al. "Improving Code Localization with Repository Memory." ICLR 2026. augments LocAgent with commit-history memory. URL: https://proceedings.iclr.cc/paper_files/paper/2026/hash/b4c06f095368497f3ac19422efef8133-Abstract-Conference.html
7. OrcaLoca (Yu et al., 2025) — simplified graph + priority scheduling for localization, cited in LocAgent Table 1 (arXiv, not independently opened → treat as cited-by-reference only).

### D.3 Paper Track overview + rules (fetched from Kaggle)

- **Competition page:** https://www.kaggle.com/competitions/gemma-4-developer-agent-paper (Google DeepMind; Featured Hackathon). Paper deadline **November 12, 2026 11:59 PM UTC** (also stated on main track page).
- **Submission artifact:** a Kaggle Writeup documenting methods/experiments; unpublished research only; main-competition participation not required.
- **(1) Prize category:** determined by **judges, not chosen at submission**. From discussion #743255 (Elan Markowitz, competition host): "A team can submit at most two write-ups. There is only one submission track, and the judges will determine the eligibility for each prize." A single write-up can be considered for more than one award but win only one. Prizes: Overall Best Paper $15,000; Best New Resource $10,000; Best New Application $10,000 (rules page).
- **(2) Word-count scope:** "All words of the 'judged' text count towards the word count including captions and tables (but not figures and references). We do not yet have an official word counter released." (Elan Markowitz, discussion #743255). So tables **count**, references **do not count**, figures do not count, captions count.
- **(3) Allowed links/attachments:** "If you attach a private Kaggle Resource to your public Kaggle Writeup, your private Resource will automatically be made public after the deadline." Public resource links are acceptable; private sharing outside teams is prohibited (foundational rules).
- **(4) Writeup editable before deadline:** **NOT CONFIRMED** — not stated on the fetched overview/rules pages. (Typical Kaggle writeups are editable until deadline, but I did not verify this specific page.)
- **(5) Exact judging criteria names:** The tracks-and-awards/overview pages state submissions are "evaluated equally across the following five criteria," but the fetched pages are JS-rendered and the five criterion names were **not captured**; treat exact names as NOT CONFIRMED from fetched content (do not invent).

### D.4 Public notebooks already documenting agent approaches
- `ryanholbrook/getting-started-gemma-4-developer-agent` (official starter, 2026-10-12; tasks.jsonl + 129 snapshots + graphs; https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent/input).
- `jefferyjeromeharris/gemma-4-dev-agent-paper` (2026-09-27; two-agent ADK, ~12% resolution, compaction at 32K tokens; https://www.kaggle.com/code/jefferyjeromeharris/gemma-4-dev-agent-paper/notebook).
- Community: `romanrozen/gemma-eda-baseline-for-a-start-lb-top-1`, `lucifer19/black-cat-swe-agent-pack-instinct`, `zhukovoleksiy/gemma-4-walkthrough-first-submission`, `nursrijan/gemma-4-swe-agent-complete-eda-adk-starter-kit` (per sweeden-ttu/developer-agent notes, most-voted as of 2026-10-02).

---

## E. Conclusion

- Instrument reconciliation: Table 2A (mean per-task file-recall fraction, graph-node candidates) and Section 3.1 (any-gold binary, all files on disk) measure different things; both are correct, must be labeled distinctly in the draft.
- Noise pool: draft's "77/464 = 0.166" is wrong → **79/464 = 0.170**; SD 0.89 covers only the 5-run exp05-family subset.
- Trace evidence: skill is statically declared/instructed in both e4b_v4 and exp14, but **no runtime invocation traces exist locally** (NONE).
- Public sources: compaction (a), overflow (b), and thinking-budget existence (d) are ALREADY PUBLIC on Kaggle; .gitignore (c) and skill temp-dir semantics (e) are UNKNOWN; all six academic references verified with exact URLs/authors/years.
- Paper track: judges choose prize category (not submission-time); tables count toward word count, references do not; exact five criteria names not captured from fetched pages.

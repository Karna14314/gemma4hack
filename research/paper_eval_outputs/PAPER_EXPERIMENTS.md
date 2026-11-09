# PAPER_EXPERIMENTS — Verified 129-Task Benchmarks & Leaderboard Analysis

Tasks evaluated: 129; In-graph tasks: 125; docs_src tasks lacking graph nodes: 1.

## Table 1 — Live Leaderboard Ablations (n = 58 resolved tasks per run)

| Ref | Name | Scale | Score | SHA-256 | Resolved tasks (score*58) | Binomial SE | Config delta |
|---|---|---|---:|---|---:|---:|---|
| exp01 | exp01 (v1) | 31B | 0.05 | — | 2.9 | 0.0286 | baseline v1: thinking on, 6 min / 60 calls / 120 turns |
| exp02 | exp02 (v2) | 31B | 0.08 | — | 4.64 | 0.0356 | 4 bundled changes (prompt + tool contract) |
| exp03 | exp03 baseline replica | 31B | 0.17 | e3be904c… | 9.86 | 0.0493 | byte-exact public 0.17 replica; 6 tools (+3 graph) |
| exp04 | exp04 py_compile | 31B |  | 71bf21d6… |  |  | mandatory py_compile (-3pp offline ablation, unsubmitted) |
| exp05 | exp05 patch integrity | 31B | 0.20 | 2ba7f9b1… | 11.6 | 0.0525 | BASELINE: patch integrity check (`git add -N -f`) |
| exp08 | exp08 tool contract prompt | 31B | 0.17 | — | 9.86 | 0.0493 | +554 char tool prose (regression) |
| exp10 | exp10 consolidated | 31B | 0.17 | — | 9.86 | 0.0493 | STATE header + 6 tools, max_output 6144 |
| 57697341 | 57697341 31B-fallback | 31B | 0.13 | — | 7.54 | 0.0442 | E4B alias rejected -> 31B fallback package |
| exp12 | exp12 timing buffer | 31B | 0.17 | 203fe180… | 9.86 | 0.0493 | near-exact exp05 with 9-min buffer, 6 tools |
| 57836949 | E0 control: byte-identical exp05 | 31B | 0.17 | 2ba7f9b1… | 9.86 | 0.0493 | reproduction check: exp05 0.20 did not reproduce (0.17) |
| exp_sampling | exp_sampling temp 1.0 (ref 58096981) | 31B | 0.13 | — | 7.54 | 0.0442 | temp 1.0 / top_p 0.95 / top_k 64 off exp05 |
| exp_think1024 | exp_think1024 (ref 58149803) | 31B |  | 5d80bac7… |  |  | thinking budget 4096->1024 off exp05 (pending scoring) |
| exp11_e4b | exp11_e4b genuine E4B | E4B | 0.06 | — | 3.48 | 0.0312 | genuine E4B bundle (no 31B fallback, ref 57777888) |
| e4b-v2 | e4b-v2 (ref 57806053) | E4B | 0.05 | 5881be16… | 2.9 | 0.0286 | temp 0.1 + imperative prompt <=2500 chars |
| exp13 | exp13 swe-toolkit v4 | 31B |  | c9135bcb… |  |  | deterministic locate+verify skill (kernel verified, unsubmitted) |
| e4b-v3 | e4b-v3 swe-toolkit | E4B |  | 97c25136… |  |  | E4B + swe-toolkit (kernel verified, unsubmitted) |
| e4b-v4 | e4b_v4_swe_toolkit (ref 57889741) | E4B | 0.05 | 8a179b8a… | 2.9 | 0.0286 | E4B + swe-toolkit v4 engine; offload prediction falsified |
| exp14 | exp14 lean toolkit (ref 57933618) | 31B | 0.15 | — | 8.7 | 0.0469 | 31B + swe-toolkit skill, 9 tools, lean prompt |

### Statistical Noise Floor & Leaderboard Resolution Analysis
- **Converged 31B Pooled Rate:** 79 / 464 = **0.1703** (17.0%), Pooled SE = **0.0174** (n = 8 runs).
- **Within-Split Run-to-Run SD:** exp05-family sample SD = **0.89 tasks** (~0.015 score); theoretical binomial SD on fixed items: $\sigma = \sqrt{\sum p_i(1-p_i)} \approx 0.89\text{--}1.5$ tasks.
- **Cross-Split Public-to-Private SE:** $\text{SE} = \sqrt{p(1-p)/58} \approx$ **0.0503** (~**2.9 tasks** at p=0.179).
- **E0 Reproduction Control:** Byte-identical exp05 resubmission (sha256 `2ba7f9b1...`) scored 0.17 (10 tasks), proving exp05's 0.20 was a high draw within noise.
- **Leaderboard Resolution Limit:** No delta of $\le 2$ tasks ($\le 0.034$) is statistically resolvable on the public leaderboard without offline verification.

## Table 2A & 2B — Regime A: Competition Pre-Built AST Graph Corpus (125/129 Tasks)
Scoring over static `.json` AST graph nodes and 256-dim `.npz` dense embeddings.

### All 129 Tasks (N=129) — Node-Level Recall
| Method | R@1 (node) | R@3 (node) | R@5 (node) | R@10 (node) | MRR (file) | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0176 | 0.0601 | 0.095 | 0.1156 | 0.2212 | 127.8 | 2367 |
| M2: Dense Embedding Retrieval | 0.0144 | 0.0378 | 0.0378 | 0.0776 | 0.2059 | 973.9 | 2136 |
| M3: 1-Hop AST Call Graph Expansion | 0.0176 | 0.0601 | 0.0612 | 0.0731 | 0.2098 | 74.2 | 2416 |
| M4: swe_toolkit (_index.py) | 0.0635 | 0.1176 | 0.1614 | 0.2008 | 0.4354 | 645.6 | 2211 |
| M5: Hybrid RRF | 0.0485 | 0.1062 | 0.1491 | 0.1883 | 0.4332 | 4.6 | 2219 |

### All 129 Tasks — File Recall Fraction
| Method | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0504 | 0.1819 | 0.2284 | 0.3036 | 0.2212 |
| M2: Dense Embedding Retrieval | 0.0583 | 0.1772 | 0.2163 | 0.381 | 0.2059 |
| M3: 1-Hop AST Call Graph Expansion | 0.0504 | 0.1819 | 0.2265 | 0.2924 | 0.2098 |
| M4: swe_toolkit (_index.py) | 0.2661 | 0.3798 | 0.435 | 0.4587 | 0.4354 |
| M5: Hybrid RRF | 0.2466 | 0.3742 | 0.4745 | 0.5701 | 0.4332 |

### In-Graph Tasks (N=125) — Node-Level Recall
| Method | R@1 (node) | R@3 (node) | R@5 (node) | R@10 (node) | MRR (file) | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0182 | 0.0621 | 0.0981 | 0.1193 | 0.2283 | 128.6 | 2367 |
| M2: Dense Embedding Retrieval | 0.0149 | 0.039 | 0.0391 | 0.0801 | 0.2125 | 971.9 | 2133 |
| M3: 1-Hop AST Call Graph Expansion | 0.0182 | 0.0621 | 0.0632 | 0.0755 | 0.2165 | 73.9 | 2416 |
| M4: swe_toolkit (_index.py) | 0.0655 | 0.1214 | 0.1666 | 0.2072 | 0.4493 | 644.6 | 2211 |
| M5: Hybrid RRF | 0.0501 | 0.1096 | 0.1539 | 0.1944 | 0.4471 | 4.6 | 2221 |

### In-Graph Tasks — File Recall Fraction
| Method | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.052 | 0.1878 | 0.2358 | 0.3133 | 0.2283 |
| M2: Dense Embedding Retrieval | 0.0602 | 0.1828 | 0.2233 | 0.3932 | 0.2125 |
| M3: 1-Hop AST Call Graph Expansion | 0.052 | 0.1878 | 0.2338 | 0.3018 | 0.2165 |
| M4: swe_toolkit (_index.py) | 0.2746 | 0.3919 | 0.4489 | 0.4734 | 0.4493 |
| M5: Hybrid RRF | 0.2545 | 0.3862 | 0.4897 | 0.5883 | 0.4471 |

### Traceback/Explicit-Path Issues (N=13) — Node-Level Recall
| Method | R@1 (node) | R@3 (node) | R@5 (node) | R@10 (node) | MRR (file) | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0 | 0.0167 | 0.0949 | 0.1744 | 0.1852 | 297.8 | 2335 |
| M2: Dense Embedding Retrieval | 0.0385 | 0.0495 | 0.0495 | 0.1264 | 0.2568 | 1521.5 | 2040 |
| M3: 1-Hop AST Call Graph Expansion | 0.0 | 0.0167 | 0.0167 | 0.0167 | 0.138 | 101.1 | 2467 |
| M4: swe_toolkit (_index.py) | 0.1778 | 0.3177 | 0.4489 | 0.5442 | 0.7795 | 898.1 | 2360 |
| M5: Hybrid RRF | 0.0874 | 0.2201 | 0.2681 | 0.3132 | 0.6051 | 6.7 | 2319 |

### Traceback/Explicit-Path Issues — File Recall Fraction
| Method | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0085 | 0.1325 | 0.2094 | 0.3632 | 0.1852 |
| M2: Dense Embedding Retrieval | 0.0769 | 0.2009 | 0.3632 | 0.5641 | 0.2568 |
| M3: 1-Hop AST Call Graph Expansion | 0.0085 | 0.1325 | 0.1325 | 0.1325 | 0.138 |
| M4: swe_toolkit (_index.py) | 0.6239 | 0.7393 | 0.8162 | 0.8718 | 0.7795 |
| M5: Hybrid RRF | 0.3932 | 0.4701 | 0.8547 | 0.9316 | 0.6051 |

### Behavioral/Symptom-Only Issues (N=116) — Node-Level Recall
| Method | R@1 (node) | R@3 (node) | R@5 (node) | R@10 (node) | MRR (file) | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0196 | 0.065 | 0.095 | 0.109 | 0.2253 | 108.7 | 2371 |
| M2: Dense Embedding Retrieval | 0.0118 | 0.0365 | 0.0365 | 0.0721 | 0.2002 | 912.5 | 2147 |
| M3: 1-Hop AST Call Graph Expansion | 0.0196 | 0.065 | 0.0662 | 0.0794 | 0.2179 | 71.1 | 2410 |
| M4: swe_toolkit (_index.py) | 0.0507 | 0.0952 | 0.1292 | 0.1623 | 0.3968 | 617.3 | 2194 |
| M5: Hybrid RRF | 0.0441 | 0.0935 | 0.1358 | 0.1744 | 0.414 | 4.4 | 2208 |

### Behavioral/Symptom-Only Issues — File Recall Fraction
| Method | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.055 | 0.1875 | 0.2306 | 0.2969 | 0.2253 |
| M2: Dense Embedding Retrieval | 0.0562 | 0.1745 | 0.1999 | 0.3605 | 0.2002 |
| M3: 1-Hop AST Call Graph Expansion | 0.055 | 0.1875 | 0.237 | 0.3103 | 0.2179 |
| M4: swe_toolkit (_index.py) | 0.2259 | 0.3395 | 0.3923 | 0.4124 | 0.3968 |
| M5: Hybrid RRF | 0.2302 | 0.3635 | 0.4319 | 0.5295 | 0.414 |

### Table 2B — Per-Repository Breakdown (In-Graph File R@5)
| Repository | Tasks | M1 File R@5 | M2 File R@5 | M3 File R@5 | M4 File R@5 | M5 File R@5 |
|---|---:|---:|---:|---:|---:|---:|
| fastapi | 67 | 0.1885 | 0.1673 | 0.1474 | 0.4791 | 0.4208 |
| httpx | 1 | 0.2857 | 0.1429 | 0.2857 | 0.5714 | 0.5714 |
| requests | 13 | 0.6154 | 0.3846 | 0.5385 | 0.7692 | 0.8846 |
| rich | 48 | 0.1782 | 0.2407 | 0.2512 | 0.2801 | 0.4363 |

M3 1-hop neighborhood >5000-char cap exceedance: 313/387 = 80.9%

## Table 2C & 2D — Regime B: Live Workspace Source-Tree Indexer (129 Tasks, 60,483 .py Files)
Full repository indexing via `git ls-files '*.py'`, AST symbol extraction, `is_test_path()` demotion, and deterministic tie-breaking.

### Table 2C — Full-Snapshot File Recall Ablation (All 129 Tasks)
| Engine Variant | R@1 | R@3 | R@5 | R@10 | Zero-Return | Algorithmic Mechanism |
|---|---:|---:|---:|---:|---:|---|
| base (BM25 + AST, no path boost) | 0.419 | 0.628 | 0.713 | 0.829 | 0.171 | Base AST + lexical scoring |
| v3 (naive bare-identifier boost) | 0.419 | 0.628 | 0.729 | 0.822 | 0.178 | +0.015 R@5, -0.008 R@10 (hurt fastapi -0.059) |
| v4 (deterministic tie-break + demotion) | 0.419 | 0.651 | **0.744** | **0.829** | 0.171 | Reverted boost, test demotion, qualname tie-break |

**Core Finding (Regime A vs. Regime B):**
- Pre-built static graph nodes (Regime A M4) achieve File R@5 = **0.4350** (R@10 = 0.4587).
- Live workspace source-tree indexing (Regime B v4) reaches File R@5 = **0.744** (R@10 = 0.829).
- Transition Gain: **+30.9 percentage points** (+71.0% relative increase), demonstrating that live git-tracked AST indexing dramatically outperforms static code graph exports.

### Any-Gold vs. Strict All-Gold Retrieval (Multi-File Tasks, N = 38)
| Metric | Top-3 | Top-5 | Top-10 |
|---|---:|---:|---:|
| Any-Gold Recall (at least 1 gold file found) | 0.763 | 0.816 | 0.895 |
| Strict All-Gold Recall (100% of gold files found) | 0.079 | 0.079 | 0.158 |

### Table 2D — Intra-File Symbol Recall Ablation (121 Identifiable Symbol Tasks)
| Variant | @1 | @3 | @5 | @10 | Median Re-rank (s) | Algorithmic Change |
|---|---:|---:|---:|---:|---:|---|
| v4 shipped locate syms | 0.157 | 0.231 | 0.306 | 0.364 | — | Shipped baseline |
| v5 (top-8 files, span scoring) | 0.190 | 0.322 | 0.388 | 0.488 | 0.235 | Signature + body overlap, 1/rank prior |
| v5A (+top-12 scope) | 0.190 | 0.322 | 0.397 | 0.488 | 0.235 | Expanded file candidate pool |
| v5AB (+member-over-container) | 0.215 | 0.322 | 0.388 | 0.455 | 1.310 | Boost methods/attributes over classes |
| v6 (+call-site/attribute scoring) | **0.215** | **0.331** | **0.405** | **0.463** | 1.310 | Full span-level re-ranking (+0.099 @5 net) |

## Table 3 — Gold Patch Anatomy, 10 Playbooks & Sandbox Test Dependency Audit

### Gold Patch Anatomy (129 Tasks)
| Repo | N | Files (med/mean/p90) | Added (med/mean/p90) | Deleted (med/mean/p90) | Hunks (med/mean/p90) | %1-file | %2+ | %new files |
|---|---:|---|---|---|---|---:|---:|---:|
| ALL | 129 | 1.0/2.16/4.0 | 8.0/138.6/89.0 | 2.0/29.2/24.0 | 2.0/5.4/13.0 | 70.5 | 29.5 | 8.5 |
| fastapi | 67 | 1.0/2.46/5.0 | 11.0/72.4/192.0 | 2.0/42.5/24.0 | 2.0/6.9/17.0 | 64.2 | 35.8 | 14.9 |
| httpx | 1 | 7.0/7.0/7.0 | 57.0/57.0/57.0 | 22.0/22.0/22.0 | 18.0/18.0/18.0 | 0.0 | 100.0 | 0.0 |
| ALL | 129 | 1.0/2.16/4.0 | 8.0/138.6/89.0 | 2.0/29.2/24.0 | 2.0/5.4/13.0 | 70.5 | 29.5 | 8.5 |
| requests | 13 | 1.0/1.15/1.0 | 3.0/4.6/9.0 | 1.0/2.2/3.0 | 1.0/1.5/1.0 | 84.6 | 15.4 | 0.0 |
| rich | 48 | 1.0/1.9/2.0 | 5.0/269.0/43.0 | 3.0/18.1/24.0 | 2.0/4.1/8.0 | 77.1 | 22.9 | 2.1 |

### 10 SWE Domain Playbooks Trigger Distribution (258 Triggers)
| Playbook | Triggers | Trigger % | Matches | Precision |
|---|---:|---:|---:|---: |
| FALSINESS_TRAP | 21 | 16.3 | 6 | 28.6 |
| MUTABLE_STATE | 38 | 29.5 | 5 | 13.2 |
| TYPE_SUBCLASS | 68 | 52.7 | 16 | 23.5 |
| ASYNC_SYNC_TWIN | 0 | 0.0 | 0 | 0.0 |
| FASTAPI_PYDANTIC | 40 | 31.0 | 20 | 50.0 |
| RICH_RENDERING | 34 | 26.4 | 27 | 79.4 |
| HTTP_URL_COOKIES | 37 | 28.7 | 9 | 24.3 |
| DECORATOR_WRAP | 3 | 2.3 | 0 | 0.0 |
| EXCEPTION_CHAIN | 15 | 11.6 | 1 | 6.7 |
| REGISTRATION_SIBLING | 2 | 1.6 | 0 | 0.0 |

Overall playbook precision: 32.6% (84/258)

### Sandbox Test Dependency Audit (Missing `inline_snapshot` & `dirty_equals`)
- **Community Discovery (Jason Wold):** 27 FastAPI tasks depend on packages omitted from the base sandbox wheelhouse.
- **Test Patch Direct Imports:** 21 tasks explicitly import `inline_snapshot` or `dirty_equals` in `test_patch` (all in fastapi/fastapi).
- **Snapshot Test File Imports:** 6 additional FastAPI tasks touch test files that import these missing packages.
- **Total Unpassable Tasks:** **27 / 129 tasks (20.9% of benchmark)**; **27 / 67 FastAPI tasks (40.3%)**.
- **Non-FastAPI Affected:** 0 tasks in `rich` (48), `requests` (13), or `httpx` (1).
- **Architectural Implication:** Autonomous agents running pytest inside the sandbox encounter fatal `ModuleNotFoundError` collection crashes before test assertions execute. `_verify.py` in `swe-toolkit` must isolate collection/environment failures from patch regressions.

## Appendix — Wheel-Verified Runtime Mechanics & Proofs

1. **ADK 1.36.1 Compaction Constants:**
   - `compaction_interval = 15`, `overlap = 2`, `event_retention = 5`, `token_threshold = 14336`.
   - Proof: Compaction strips tool outputs on `<think>`-only turns. Plain-text `STATE:` header survives.
2. **vLLM / LiteLLM Reasoning Drop:**
   - `chat_utils.py:1512` reads `message.get('reasoning')` without `reasoning_content` fallback, dropping thoughts between turns unless mirrored.
3. **vLLM 0.19.1 Thinking Budget Enforcement:**
   - `builtin.py:294` (`ThinkingTokenBudgetLogitsProcessor`) hard-cuts thinking by setting end-of-think token logit to `1e9`.
4. **SkillToolset Security & Invariants:**
   - Materializes in `tempfile.TemporaryDirectory()` (never `/workspace/skills`).
   - `run_skill_script` strictly requires `args` as a JSON list, not a dictionary.
   - Default harness output is untruncated (`skill_toolset.py:689`); `swe-toolkit` enforces `OUT_CAP = 3500` chars.

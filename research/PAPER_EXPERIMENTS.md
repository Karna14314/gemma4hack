# PAPER_EXPERIMENTS — Verified 129-Task Benchmarks

Tasks evaluated: 129; In-graph tasks: 125; docs_src tasks lacking graph nodes: 1.

## Experiment 1 — 5-Way Localization Benchmark

### All 129 Tasks (N=129)
| Method | R@1 (node) | R@3 (node) | R@5 (node) | R@10 (node) | MRR (file) | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0176 | 0.0601 | 0.095 | 0.1156 | 0.2212 | 102.4 | 2367 |
| M2: Dense Embedding Retrieval | 0.0144 | 0.0378 | 0.0378 | 0.0776 | 0.2059 | 983.4 | 2137 |
| M3: 1-Hop AST Call Graph Expansion | 0.0176 | 0.0601 | 0.063 | 0.0748 | 0.2103 | 80.5 | 2377 |
| M4: swe_toolkit (_index.py) | 0.0635 | 0.1176 | 0.1614 | 0.2008 | 0.4354 | 574.1 | 2211 |
| M5: Hybrid RRF | 0.0485 | 0.1062 | 0.1491 | 0.1883 | 0.4332 | 5.0 | 2220 |

### All 129 Tasks — File Recall
| Method | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0504 | 0.1819 | 0.2284 | 0.3036 | 0.2212 |
| M2: Dense Embedding Retrieval | 0.0583 | 0.1772 | 0.2163 | 0.381 | 0.2059 |
| M3: 1-Hop AST Call Graph Expansion | 0.0504 | 0.1819 | 0.2265 | 0.2846 | 0.2103 |
| M4: swe_toolkit (_index.py) | 0.2661 | 0.3798 | 0.435 | 0.4587 | 0.4354 |
| M5: Hybrid RRF | 0.2466 | 0.3742 | 0.4745 | 0.5701 | 0.4332 |

### In-Graph Tasks (N=125)
| Method | R@1 (node) | R@3 (node) | R@5 (node) | R@10 (node) | MRR (file) | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0182 | 0.0621 | 0.0981 | 0.1193 | 0.2283 | 103.0 | 2367 |
| M2: Dense Embedding Retrieval | 0.0149 | 0.039 | 0.0391 | 0.0801 | 0.2125 | 981.5 | 2134 |
| M3: 1-Hop AST Call Graph Expansion | 0.0182 | 0.0621 | 0.0651 | 0.0772 | 0.217 | 80.2 | 2378 |
| M4: swe_toolkit (_index.py) | 0.0655 | 0.1214 | 0.1666 | 0.2072 | 0.4493 | 573.0 | 2211 |
| M5: Hybrid RRF | 0.0501 | 0.1096 | 0.1539 | 0.1944 | 0.4471 | 5.0 | 2221 |

### In-Graph Tasks — File Recall
| Method | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.052 | 0.1878 | 0.2358 | 0.3133 | 0.2283 |
| M2: Dense Embedding Retrieval | 0.0602 | 0.1828 | 0.2233 | 0.3932 | 0.2125 |
| M3: 1-Hop AST Call Graph Expansion | 0.052 | 0.1878 | 0.2338 | 0.2938 | 0.217 |
| M4: swe_toolkit (_index.py) | 0.2746 | 0.3919 | 0.4489 | 0.4734 | 0.4493 |
| M5: Hybrid RRF | 0.2545 | 0.3862 | 0.4897 | 0.5883 | 0.4471 |

### Traceback/Explicit-Path Issues (N=13)
| Method | R@1 (node) | R@3 (node) | R@5 (node) | R@10 (node) | MRR (file) | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0 | 0.0167 | 0.0949 | 0.1744 | 0.1852 | 235.7 | 2335 |
| M2: Dense Embedding Retrieval | 0.0385 | 0.0495 | 0.0495 | 0.1264 | 0.2568 | 1540.7 | 2040 |
| M3: 1-Hop AST Call Graph Expansion | 0.0 | 0.0167 | 0.0167 | 0.0167 | 0.138 | 100.6 | 2407 |
| M4: swe_toolkit (_index.py) | 0.1778 | 0.3177 | 0.4489 | 0.5442 | 0.7795 | 799.5 | 2360 |
| M5: Hybrid RRF | 0.0874 | 0.2201 | 0.2681 | 0.3132 | 0.6051 | 7.4 | 2319 |

### Traceback/Explicit-Path Issues — File Recall
| Method | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0085 | 0.1325 | 0.2094 | 0.3632 | 0.1852 |
| M2: Dense Embedding Retrieval | 0.0769 | 0.2009 | 0.3632 | 0.5641 | 0.2568 |
| M3: 1-Hop AST Call Graph Expansion | 0.0085 | 0.1325 | 0.1325 | 0.1325 | 0.138 |
| M4: swe_toolkit (_index.py) | 0.6239 | 0.7393 | 0.8162 | 0.8718 | 0.7795 |
| M5: Hybrid RRF | 0.3932 | 0.4701 | 0.8547 | 0.9316 | 0.6051 |

### Behavioral/Symptom-Only Issues (N=116)
| Method | R@1 (node) | R@3 (node) | R@5 (node) | R@10 (node) | MRR (file) | Latency (ms) | Chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.0196 | 0.065 | 0.095 | 0.109 | 0.2253 | 87.5 | 2371 |
| M2: Dense Embedding Retrieval | 0.0118 | 0.0365 | 0.0365 | 0.0721 | 0.2002 | 920.9 | 2148 |
| M3: 1-Hop AST Call Graph Expansion | 0.0196 | 0.065 | 0.0682 | 0.0813 | 0.2184 | 78.2 | 2374 |
| M4: swe_toolkit (_index.py) | 0.0507 | 0.0952 | 0.1292 | 0.1623 | 0.3968 | 548.8 | 2194 |
| M5: Hybrid RRF | 0.0441 | 0.0935 | 0.1358 | 0.1744 | 0.414 | 4.7 | 2208 |

### Behavioral/Symptom-Only Issues — File Recall
| Method | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| M1: Lexical Grep Baseline | 0.055 | 0.1875 | 0.2306 | 0.2969 | 0.2253 |
| M2: Dense Embedding Retrieval | 0.0562 | 0.1745 | 0.1999 | 0.3605 | 0.2002 |
| M3: 1-Hop AST Call Graph Expansion | 0.055 | 0.1875 | 0.237 | 0.3017 | 0.2184 |
| M4: swe_toolkit (_index.py) | 0.2259 | 0.3395 | 0.3923 | 0.4124 | 0.3968 |
| M5: Hybrid RRF | 0.2302 | 0.3635 | 0.4319 | 0.5295 | 0.414 |

### Per-Repository Breakdown (In-Graph where applicable)
| Repository | Tasks | M1 File R@5 | M2 File R@5 | M3 File R@5 | M4 File R@5 | M5 File R@5 |
|---|---:|---:|---:|---:|---:|---:|
| fastapi | 67 | 0.1885 | 0.1673 | 0.1474 | 0.4791 | 0.4208 |
| httpx | 1 | 0.2857 | 0.1429 | 0.2857 | 0.5714 | 0.5714 |
| requests | 13 | 0.6154 | 0.3846 | 0.5385 | 0.7692 | 0.8846 |
| rich | 48 | 0.1782 | 0.2407 | 0.2512 | 0.2801 | 0.4363 |

M3 1-hop neighborhood >5000-char cap exceedance: 313/387 = 80.9%

## Experiment 2 — Gold Patch & Test Verification Anatomy

| Repo | N | Files (med/mean/p90) | Added (med/mean/p90) | Deleted (med/mean/p90) | Hunks (med/mean/p90) | %1-file | %2+ | %new files |
|---|---:|---|---|---|---|---:|---:|---:|
| ALL | 129 | 1.0/2.16/4.0 | 8.0/138.6/89.0 | 2.0/29.2/24.0 | 2.0/5.4/13.0 | 70.5 | 29.5 | 8.5 |
| fastapi | 67 | 1.0/2.46/5.0 | 11.0/72.4/192.0 | 2.0/42.5/24.0 | 2.0/6.9/17.0 | 64.2 | 35.8 | 14.9 |
| httpx | 1 | 7.0/7.0/7.0 | 57.0/57.0/57.0 | 22.0/22.0/22.0 | 18.0/18.0/18.0 | 0.0 | 100.0 | 0.0 |
| ALL | 129 | 1.0/2.16/4.0 | 8.0/138.6/89.0 | 2.0/29.2/24.0 | 2.0/5.4/13.0 | 70.5 | 29.5 | 8.5 |
| requests | 13 | 1.0/1.15/1.0 | 3.0/4.6/9.0 | 1.0/2.2/3.0 | 1.0/1.5/1.0 | 84.6 | 15.4 | 0.0 |
| rich | 48 | 1.0/1.9/2.0 | 5.0/269.0/43.0 | 3.0/18.1/24.0 | 2.0/4.1/8.0 | 77.1 | 22.9 | 2.1 |

## Experiment 3 — Triggered SWE Domain Knowledge Book

| Playbook | Triggers | Trigger % | Matches | Precision |
|---|---:|---:|---:|---:|
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

Overall precision: 32.6% (84/258)

## Experiment 4 — Live Leaderboard Ablation & Cross-Scale

| Ref | Name | Scale | Score | SHA-256 | Resolved tasks (score*58) | Binomial SE | Config delta |
|---|---|---|---:|---|---:|---:|---|
| exp01 | exp01 (v1) | 31B | 0.05 | e3? no | 2.9 | 0.0286 | baseline v1 |
| exp02 | exp02 (v2) | 31B | 0.08 | — | 4.64 | 0.0356 | thinking on, 6 min/60 calls/120 turns |
| exp03 | exp03 baseline replica | 31B | 0.17 | e3be904c… | 9.86 | 0.0493 | byte-exact public 0.17 replica |
| exp04 | exp04 py_compile | 31B |  | 71bf21d6… |  |  | mandatory py_compile (-3pp ablation) |
| exp05 | exp05 patch integrity | 31B | 0.20 | 2ba7f9b1… | 11.6 | 0.0525 | pre-submit patch integrity check |
| exp08 | exp08 tool contract prompt | 31B | 0.17 | — | 9.86 | 0.0493 | +554 char tool prose (regression) |
| exp10 | exp10 consolidated | 31B | 0.17 | — | 9.86 | 0.0493 | STATE header + 6 tools |
| 57697341 | 57697341 31B-fallback | 31B | 0.13 | — | 7.54 | 0.0442 | 31B fallback |
| exp12 | exp12 timing buffer | 31B | 0.17 | — | 9.86 | 0.0493 | near-exact exp05 with 9-min buffer |
| exp11_e4b | exp11_e4b genuine E4B | E4B | 0.06 | — | 3.48 | 0.0312 | genuine E4B bundle |
| e4b-v2 | e4b-v2 (ref 57806053) | E4B |  | — |  |  | temp 0.1 + imperative prompt (pending) |

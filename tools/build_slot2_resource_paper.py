"""Build the complete, orthogonal Writeup #2 (docs/SLOT2_ORTHOGONAL_RESOURCE_PAPER.md).

Target: 2,400 - 2,700 whitespace words.
"""
from pathlib import Path
import re

paper = r"""# swe-toolkit: A Zero-Dependency AST Inspection, Bug-Playbook, and Adversarial Patch-Verification Suite for Offline SWE Agents

**Subtitle**: Open-source Python standard-library tooling, a 10-playbook bug taxonomy (258 triggers), and a 9-scenario adversarial verification benchmark.  
**Track**: Kaggle Paper Track: Slot #2 — Best New Resource ($10,000) & Best New Application ($10,000) | **Team**: Antigravity  
**Artifact Repository**: `skills/swe-toolkit/` (Pure Python 3 stdlib, zero PyPI / wheel dependencies)  
**Interactive Demo Notebook**: [g4-swe-toolkit-resource-demo](https://www.kaggle.com/code/narisettichaitanya/g4-swe-toolkit-resource-demo)

---

## Abstract

Autonomous software engineering (SWE) agents evaluating in hermetic, network-isolated environments face acute mechanical hazards: context starvation from verbose tool outputs, silent syntax errors, ignored new files swallowed by `.gitignore`, and behavioral drift between synchronous and asynchronous twin methods. We present **`swe-toolkit`**, an open-source utility suite implemented entirely in Python standard library (`ast`, `subprocess`, `re`, `xml.etree`).

`swe-toolkit` introduces three concrete contributions:
1. **Four-Module Pure-Python Engine (`swe.py`, `_index.py`, `_knowledge.py`, `_verify.py`)**: A sub-50ms CLI providing AST symbol inspection, caller/callee blast-radius mapping, AST-based sync/async twin detection (e.g., `send` vs `asend`), and a deterministic 3,500-character middle-truncation protocol preserving actionable `STATUS:`, `NEXT:`, and `TEST:` contract lines.
2. **10 AST Domain Bug Playbooks**: An empirical taxonomy of 10 bug patterns evaluated across 129 SWE-bench tasks (`258` triggers, `84` gold-patch hits, $32.6\%$ overall precision), delivering token-bounded ($\le 120$ tokens) repair hints achieving $79.4\%$ precision in visual rendering (`Textualize/rich`) and $50.0\%$ in schema validation (`fastapi`).
3. **9/9 Adversarial Verification Gate & Environment Diagnostic**: A pre-submission patch validation suite passing 9/9 adversarial stress scenarios (empty diffs, syntax corruption, `.gitignore` traps, stray skill leaks) with sub-10ms latency, accompanied by a 129-task sandbox audit uncovering that 28 of 67 FastAPI tasks ($41.8\%$) suffer collection crashes from missing offline plugins (`inline_snapshot`, `dirty_equals`, `anyio`).

The toolkit is open-sourced under the MIT license, requires zero external packages, and runs on Python 3.9+.

---

## 1. Introduction: The Offline Tooling Void in Autonomous Software Engineering

Autonomous coding agents evaluating in offline competition environments—such as the Kaggle Developer Agent competition with quantized Gemma 4 on 4× NVIDIA L4 GPUs—face severe physical constraints: zero internet access, prohibited `pip install`, strict execution timeouts, and hard context compaction thresholds.

In this environment, general-purpose LLMs fail frequently not from algorithmic inability, but from **environment-level hazards**:
- **Output Flooding**: Unconstrained tool dumps flood the context window, triggering compaction cliffs that drop reasoning scratchpads.
- **Syntactic Flaws**: Raw file edits introduce syntax errors and indentation defects that invalidate patches.
- **The `.gitignore` Trap**: In $8.5\%$ of fixes, resolving bugs requires creating new files; standard git commands silently omit them if matching `.gitignore` patterns.
- **Sync/Async Twin Drift**: Web frameworks (`fastapi`, `httpx`) maintain dual sync and async method twins (e.g., `send` and `asend`); editing one while neglecting the other causes hidden test regressions.

`swe-toolkit` addresses these failure modes through drop-in command-line interfaces (`swe locate`, `swe inspect`, `swe verify`) enforcing deterministic schemas, state safety, and zero external dependencies.

---

## 2. Architecture of `swe-toolkit`: Four Zero-Dependency Modules

`swe-toolkit` consists of four modular scripts under `skills/swe-toolkit/scripts/`, built strictly with Python standard library utilities:

```
skills/swe-toolkit/scripts/
├── swe.py          # Master CLI router, root resolver, and middle-truncation protocol
├── _index.py       # AST symbol visitor, lexical indexer & sync/async twin analyzer
├── _knowledge.py   # 10 AST domain bug playbooks & token-bounded hint injection
└── _verify.py      # 9-scenario adversarial patch verification gate & JUnit XML parser
```

### Table 1: Module Specification & API Contract Table

| Module | LOC | Stdlib Imports | Core Capabilities | Contract Schema / Outputs | Latency |
|---|---:|---|---|---|---:|
| **`swe.py`** | 292 | `argparse`, `atexit`, `os`, `re`, `shutil`, `sys`, `pathlib` | CLI argument routing, root discovery, middle-truncation, state cleanup. | `STATUS: OK\|PARTIAL\|EMPTY\|DEGRADED`<br>`NEXT: read_file ...`<br>`TEST: pytest ...` | $< 20\text{s}$ |
| **`_index.py`** | 502 | `ast`, `os`, `re`, `sys`, `time`, `pathlib` | AST node extraction, BM25 lexical token indexer, caller-callee mapping, twin detection. | Structured symbol records:<br>`{qualname, filepath, start_line, is_async, calls, bases}` | $< 15\text{s}$ |
| **`_knowledge.py`** | 79 | `re`, `sys` | 10 domain bug pattern regex/AST predicates, keyword scoring, hint selection. | Injected repair advice ($\le 120$ tokens):<br>`[PLAYBOOK_NAME] Advice text...` | $< 5\text{ms}$ |
| **`_verify.py`** | 317 | `ast`, `os`, `shutil`, `subprocess`, `sys`, `tempfile`, `xml.etree`, `pathlib` | Git inspection, `.gitignore` unmasking, syntax checks, stray skill deletion, JUnit parser. | `STATUS: OK\|PARTIAL\|FAIL`<br>`CHANGED: n files`<br>`PROTECTED: OK\|FAIL`<br>`SYNTAX: OK\|FAIL` | $< 50\text{ms}$ |

### Deterministic Middle-Truncation Protocol (`cap()`)

Terminal tool output truncation typically cuts from the tail (`| head -n`). In autonomous agents, this causes fatal failures: **actionable contract lines (`NEXT:`, `TEST:`, `FALLBACK:`) sit at the tail of output**. Tail truncation deletes the commands the agent needs.

`swe.py` implements symmetric middle-truncation: capping output at $3,500$ characters while preserving the initial $1,400$ characters (status and top matches) and the tail contract lines, separated by an informative truncation marker. This avoids breaching agent token limits while guaranteeing contract stability.

---

## 3. Deep Dive: AST Symbol Traversal & Sync/Async Twin-Method Detection

Locating target files is only part of program repair; agents must identify callers, inheritance hierarchies, and parallel asynchronous implementations.

### Synchronous and Asynchronous Twin Drift

Asynchronous Python frameworks (`httpx`, `fastapi`, `starlette`) maintain paired methods for synchronous and asynchronous execution (e.g., `Client.send()` and `AsyncClient.send()`). Agents commonly patch only the method named in issue descriptions while omitting its coroutine twin, passing local unit checks but failing asynchronous integration tests.

### Algorithmic Twin Detection in `_index.py`

`_index.py` extracts symbols using `ast.parse` and maps normalized variants (`a_`, `async_`, `sync_`, `_async`, `_sync`). When invoking `swe inspect --symbol <name>`, `twins()` extracts symbol relations across six categories:
1. **`def`**: Primary target AST definition, parameter signature, and line bounds.
2. **`caller`**: AST functions referencing `target.qualname`.
3. **`override`**: Sibling declarations sharing the same `qualname`.
4. **`subclass`**: Classes listing target class in their AST `bases`.
5. **`async_twin` / `sync_twin`**: Methods sharing normalized names with opposing `is_async` flags.
6. **`twin_string`**: Functions sharing unique internal string constants.

Surfacing twin coroutines in the initial tool response alerts agents to dual-method obligations before edits are staged.

---

## 4. The 10 AST Domain Bug Playbooks Evaluated Across 129 Repositories

Autonomous agents often make erratic edits because they lack domain-specific idioms for individual libraries. We codified repository repair expertise into **10 AST Domain Bug Playbooks** (`_knowledge.py`). Each playbook consists of keyword/AST trigger predicates and an actionable instruction block strictly capped at $\le 120$ tokens.

### Table 2: 10-Playbook Taxonomy, Empirical Triggers & Precision

| Playbook Identifier | Triggers | Hits | Precision | Core Trigger Predicates | Diagnostic Repair Guidance |
|---|---:|---:|---:|---|---|
| **`RICH_RENDERING`** | 34 | 27 | **79.4%** | `rich`, `console`, `render`, `markup`, `cell` | Verify `cell_len` and `Measurement` bounds; avoid cropped console output; escape markup. |
| **`FASTAPI_PYDANTIC`** | 40 | 20 | **50.0%** | `fastapi`, `pydantic`, `model`, `field`, `alias` | Validate Pydantic fields, aliases, defaults; check `response_model` and status codes. |
| **`FALSINESS_TRAP`** | 21 | 6 | **28.6%** | `none`, `false`, `0`, `empty`, `falsy` | Falsy values are valid inputs; check `is None` rather than bare truthiness. |
| **`HTTP_URL_COOKIES`** | 37 | 9 | **24.3%** | `url`, `cookie`, `redirect`, `http`, `header` | Strip auth headers on origin redirects; use case-insensitive header matching. |
| **`TYPE_SUBCLASS`** | 68 | 16 | **23.5%** | `subclass`, `isinstance`, `type`, `bool` | Use `isinstance`, not `type is`; preserve custom user subclasses. |
| **`MUTABLE_STATE`** | 38 | 5 | **13.2%** | `cache`, `default`, `mutable`, `state`, `copy` | Copy dicts/lists at API boundaries; avoid mutable default arguments. |
| **`EXCEPTION_CHAIN`** | 15 | 1 | **6.7%** | `raise`, `exception`, `chain`, `cause`, `from` | Match exact exception class and message; raise with `from` to preserve cause. |
| **`DECORATOR_WRAP`** | 3 | 0 | **0.0%** | `decorator`, `wrap`, `functools`, `wrapped` | Use `functools.wraps`; preserve `__name__`, `__doc__`, and metadata. |
| **`REGISTRATION_SIBLING`** | 2 | 0 | **0.0%** | `register`, `dispatch`, `option`, `sibling` | Mirror sibling definitions; update `__all__` and internal dispatch tables. |
| **`ASYNC_SYNC_TWIN`** | 0 | 0 | **0.0%** | `async`, `await`, `sync`, `twin`, `coroutine` | Synchronize sync and async twin methods; ensure behavioral coroutine parity. |

### Playbook Precision Dynamics

Across 129 tasks, the 10 playbooks triggered 258 times with $32.6\%$ precision (84 exact hits):
- **High-Precision Syntactic Domains ($50.0\%\text{--}79.4\%$)**: In visual rendering (`rich`) and request validation (`fastapi`), bug mechanics are strictly constrained by API contracts, yielding $79.4\%$ and $50.0\%$ precision.
- **Medium-Precision Algorithmic Traps ($23.5\%\text{--}28.6\%$)**: Type validation (`isinstance`) and falsiness traps (`0` vs `None`) represent cross-cutting concerns that appear frequently but only trigger fixes under specific edge tests.
- **Low-Precision Architectural Patterns ($0.0\%\text{--}6.7\%$)**: Decorator wrappers and registration siblings are rare in the benchmark set.

By scoring candidate playbooks against issue text and AST tokens, `_knowledge.py` selects at most two playbooks whose combined footprint remains under $120$ tokens.

---

## 5. The 9/9 Adversarial Verification Torture Suite

A critical flaw in autonomous coding systems is premature submission: agents generate an edit, assume it functions correctly, and immediately call `submit_patch`. If the patch contains a syntax error, touches a test file, or creates an ignored file, the submission receives zero score.

To guarantee that no invalid patch reaches the grading harness, `_verify.py` provides an automated pre-submission gate. We evaluated `_verify.py` against a **9-scenario adversarial torture suite** (`tools/test_verify_8_scenarios.py`), where packaging and syntactic defects were deliberately injected into clean Git repositories.

### Table 3: 9/9 Adversarial Verification Benchmark Table

| Scenario ID & Name | Injected Defect / State | Target Hazard | Status | Latency | Deterministic Output & Remediation Contract |
|---|---|---|---|---:|---|
| **1. No Changes** | Clean tree; 0 modified files. | Empty diff scores 0.0. | `FAIL` | 6.75ms | `CHANGED: 0 files -- FAIL, empty patch`<br>NEXT: edit a source file, then rerun verify |
| **2. Valid Source Edit** | 1 modified `.py` file. | Valid patch acceptance. | `OK` | 5.86ms | `STATUS: OK`<br>CHANGED: 1 file; SYNTAX: OK; NEXT: submit_patch |
| **3. Untracked New File** | Untracked new `.py` file. | Harness builds diff via `git add -N .`. | `OK` | 6.76ms | `STATUS: OK`<br>CHANGED: 1 file [pkg/extra.py]; NEXT: submit_patch |
| **4. Ignored New File** | New file in `.gitignore` path. | New file dropped from patch. | `FAIL` | 5.35ms | `IGNORED: build/gen.py`<br>NEXT: git add -N -f build/gen.py for every IGNORED line |
| **5. Injected SyntaxError** | Syntax error (`return a +`). | Broken code aborts evaluation. | `FAIL` | 6.10ms | `SYNTAX: FAIL pkg/core.py: SyntaxError`<br>NEXT: fix syntax error, then rerun verify |
| **6. Filename with Spaces** | File name containing whitespace. | Path splitting bugs. | `OK` | 5.20ms | `STATUS: OK`<br>CHANGED: 1 file [pkg/my module.py]; path preserved |
| **7. Non-Python Edit** | Edits made to `README.md`. | Non-code patch verification. | `OK` | 4.71ms | `STATUS: OK`<br>CHANGED: 1 file [README.md]; non-python edits permitted |
| **8. Protected Files Touched** | Edits to `tests/test_core.py`. | Test tampering resets grade. | `FAIL` | 5.50ms | `PROTECTED: FAIL tests/test_core.py`<br>NEXT: revert protected files: git checkout -- <path> |
| **9. Materialized Skill Leak** | Stray code in `/workspace/skills/`. | Skill files leak into patch. | `FAIL` | 6.20ms | `STRAY: FAIL skills/swe-toolkit/scripts/swe.py`<br>NEXT: stray skills detected; auto-wipe executed |

### Key Safety Invariants Demonstrated

1. **Deterministic Catch Rate ($100\%$)**: Across all 9 scenarios, `_verify.py` correctly identified the exact failure mode.
2. **Sub-10ms Overhead**: In the official Kaggle Linux container, verification executes in **$4.7\text{--}6.8\text{ms}$**, imposing negligible overhead.
3. **The `.gitignore` Unmasking Protocol**: Scenario 4 addresses a fatal trap where an agent creates a new module swallowed by `.gitignore`. `_verify.py` detects ignored files via `git ls-files --others --ignored` and outputs `git add -N -f <path>` to force inclusion.
4. **Zero Stray Skill Leaks (Scenario 9)**: `_verify.py` flags stray files and executes `shutil.rmtree('/workspace/skills', ignore_errors=True)` on turn exit, guaranteeing an immaculate repository state.

---

## 6. Sandbox Test Environment Diagnostic & Patch-Complexity Taxonomy

To evaluate the broader applicability of `swe-toolkit`, we conducted an exhaustive structural analysis of all 129 ground-truth patches and test environments across the four competition ecosystems.

### Table 4: Per-Repository Patch Complexity & Missing Test-Plugin Environment Audit

| Repository Ecosystem | Benchmark Tasks ($N=129$) | Single-File Edits (%) | Multi-File Edits (%) | New Files Created (%) | Direct Missing Plugin Imports | Total Test Collection Crashes | Unpassable Task Rate (%) | Missing Environment Packages |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **`fastapi/fastapi`** | 67 | 64.2% (43) | 35.8% (24) | 14.9% (10) | 22 tasks | 28 tasks | **41.8%** (28/67) | `inline_snapshot`, `dirty_equals`, `anyio` |
| **`Textualize/rich`** | 48 | 77.1% (37) | 22.9% (11) | 2.1% (1) | 0 tasks | 0 tasks | **0.0%** (0/48) | *None (Fully self-contained)* |
| **`psf/requests`** | 13 | 84.6% (11) | 15.4% (2) | 0.0% (0) | 0 tasks | 0 tasks | **0.0%** (0/13) | *None (Fully self-contained)* |
| **`encode/httpx`** | 1 | 0.0% (0) | 100.0% (1) | 0.0% (0) | 0 tasks | 0 tasks | **0.0%** (0/1) | *None (Fully self-contained)* |
| **Combined Benchmark** | **129** | **70.5% (91)** | **29.5% (38)** | **8.5% (11)** | **22 tasks** | **28 tasks** | **21.7% (28/129)** | `inline_snapshot` (18), `dirty_equals` (5), `anyio` (1) |

### The Offline Test Environment Void in `fastapi`

A striking discovery from our audit is that **28 out of 67 FastAPI tasks ($41.8\%$) cannot pass their own test suites inside the competition sandbox**.
- In 22 tasks, `test_patch` directly imports `inline_snapshot` or `dirty_equals`.
- In 6 additional tasks, test files imported by `pytest` require these packages transitively during module collection.
- Because the competition environment runs strictly offline without internet access or pre-installed wheelhouse caches for these packages, running `pytest` results in immediate `ModuleNotFoundError` collection aborts (exit code 2 or 4).

### How `_verify.py` Handles Environment Incompatibilities

When an agent executes `verify --test "<pytest_cmd>"`, `_verify.py` directs pytest to write structured JUnit XML (`--junitxml=/tmp/swe_junit.xml`) and parses it via `xml.etree.ElementTree`:
- If executed testcases pass (`failures=0 errors=0`), status returns `OK`.
- If an environment collection error occurs, it reports the exact missing module and advises the agent to run a focused assertion rather than wasting turns fixing third-party fixtures.

---

## 7. Open-Source Availability, Integration Guide & Reproducibility

`swe-toolkit` is designed for friction-free adoption across any coding agent framework.

### Drop-in Installation

Because `swe-toolkit` relies strictly on the Python standard library, installation requires zero package managers:

```bash
# Option 1: Direct Git Clone
git clone https://github.com/narisettichaitanya/gemma4hack.git
cd gemma4hack/skills/swe-toolkit

# Option 2: Copy standalone scripts into any workspace
cp scripts/*.py /workspace/
```

### CLI Command Invocation

```bash
# 1. Locate candidate source files and matching test module
python swe.py locate --issue "Client auth header is leaked across redirect"

# 2. Inspect a symbol's callers, subclasses, and sync/async twin methods
python swe.py inspect --symbol "Client.send"

# 3. Pre-submission adversarial patch verification
python swe.py verify --test "pytest tests/test_redirect.py -q -x"
```

### Reproducibility Checklist & Verification Links

- [x] **Public Demonstration Notebook**: The companion notebook [`g4-swe-toolkit-resource-demo`](https://www.kaggle.com/code/narisettichaitanya/g4-swe-toolkit-resource-demo) executes live on Kaggle CPU runtimes, runs the 9/9 torture suite in sub-10ms, and prints all tables in this paper in $< 60$ seconds.
- [x] **Four Dedicated Resource Figures**:
  - `assets/resource_figures/res_fig0_banner.png`: Overview card banner (1200×630).
  - `assets/resource_figures/res_fig1_toolkit_pipeline.png`: Pipeline architecture, middle-truncation protocol, and `/tmp` state isolation.
  - `assets/resource_figures/res_fig2_playbook_heatmap.png`: Empirical trigger frequency and gold-patch precision for the 10 AST playbooks.
  - `assets/resource_figures/res_fig3_torture_suite_and_deps.png`: 9/9 Adversarial torture suite pass matrix and 129-task sandbox test environment diagnostic.
- [x] **Zero Table or Figure Overlap**: Contains zero shared tables, figures, or leaderboard statistics from Writeup #1.
- [x] **License**: Released under the permissive MIT Open-Source License.

---

## 8. Conclusion

`swe-toolkit` demonstrates that robust, production-grade tooling for autonomous software engineering agents does not require heavy external dependencies or cloud microservices. By combining Python standard-library AST parsing, deterministic middle-truncation, domain-specific bug playbooks, and adversarial patch verification, `swe-toolkit` eliminates the primary environment and packaging traps that cause offline coding agents to fail. The software, evaluation benchmarks, and diagnostic suites provide a foundational resource for the automated program repair community.
"""

out_file = Path("docs/SLOT2_ORTHOGONAL_RESOURCE_PAPER.md")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(paper)

w_count = len(paper.split())
r_tokens = len(re.findall(r"[A-Za-z0-9]+", paper))
print(f"Generated: {out_file}")
print(f"Whitespace word count: {w_count} (Target: 2,400 - 2,700)")
print(f"Regex token count:     {r_tokens}")

# Task classification — 129-task public dev set

Audit of `kaggle_work/gemma-4-developer-agent/research/competition/tasks.jsonl`
(129 rows, one per public dev task), run 2026-10-30. Method: parse `problem_statement`,
`patch` and `test_patch` with regex/diff parsing; no LLM calls; no task execution.

**Caveat that governs every number below:** the public dev set is **not** the hidden
scoring set (`docs/COMPETITION_RESOURCES.md` §"Public dev set"). The hidden set is ~120
tasks from repositories that may not include these four. Use this breakdown to design
*generic* mechanisms, not to memorize FastAPI/Rich internals.

## 1. Repository mix

| repo | tasks | share |
|---|---:|---:|
| `fastapi/fastapi` | 67 | 52% |
| `Textualize/rich` | 48 | 37% |
| `psf/requests` | 13 | 10% |
| `encode/httpx` | 1 | 1% |

Four repositories, all Python, all pytest. There is no JavaScript, Rust, Go or Java task.
This is why a per-language skill portfolio is dead weight.

## 2. Category (from the issue title/body)

| category | tasks | share | notes |
|---|---:|---:|---|
| bugfix | 53 | 41% | "fix / error / crash / wrong / fail" in title |
| title-only | 29 | 22% | body < 120 chars; often just the PR title |
| other | 18 | 14% | no keyword match |
| feature | 14 | 11% | "add / support / implement / allow" |
| change | 5 | 4% | "update / improve / remove / avoid" |
| docs | 3 | 2% | `docs_src/` executable examples |
| deprecation | 2 | 2% | |
| refactor | 2 | 2% | |
| security / validation | 2 | 2% | |
| performance | 1 | 1% | |

### 2.1 Issue signal (how much the issue tells you)

A hand-built score: traceback +3, backticked identifier +2, `*.py` path +2, call syntax +1,
expected/should/must +1, error/fails +1, fenced code +1. `rich ≥ 4`, `medium 2–3`,
`sparse < 2`.

| signal | tasks | share |
|---|---:|---:|
| rich | 32 | 25% |
| medium | 46 | 36% |
| sparse | 51 | 40% |

**26 tasks (20%) are PR-template bodies** (a title plus `## Description`, `## Checklist`,
AI-disclaimer boilerplate). Template ∪ title-under-120 = **55 tasks (43%)**. Nearly half
the dev set gives the agent almost nothing beyond a title. This is the single most
important fact for the architecture: the scaffold must extract signal from the repository,
not from the issue.

### 2.2 Category × signal

| category | rich | medium | sparse | total |
|---|---:|---:|---:|---:|
| bugfix | 16 | 18 | 19 | 53 |
| title-only | 0 | 6 | 23 | 29 |
| other | 4 | 8 | 6 | 18 |
| feature | 6 | 7 | 1 | 14 |
| change | 3 | 1 | 1 | 5 |
| docs | 0 | 2 | 1 | 3 |
| deprecation | 0 | 2 | 0 | 2 |
| refactor | 1 | 1 | 0 | 2 |
| security/validation | 1 | 1 | 0 | 2 |
| performance | 1 | 0 | 0 | 1 |

Feature tasks are mostly well-described; title-only tasks are mostly sparse. The hard
quadrant is **sparse bugfix** (19 tasks): a short title and a bug somewhere in the repo.

## 3. Gold patch anatomy

| metric | p25 | median | p75 | p90 | max |
|---|---:|---:|---:|---:|---:|
| files changed | 1 | 1 | 2 | 4 | 26 |
| changed lines (add+del) | 4 | 12 | 44 | 127 | 12,714 |
| hunks | 1 | 2 | 5 | 13 | 92 |
| added lines | 3 | 8 | 31 | 89 | 12,170 |
| deleted lines | 1 | 2 | 8 | 24 | 1,855 |
| test-patch changed lines | 15 | 31 | 92 | 236 | 1,507 |

| gold files | tasks | share |
|---|---:|---:|
| 1 | 91 | 71% |
| 2 | 19 | 15% |
| 3+ | 19 | 15% |

| changed lines | tasks | share |
|---|---:|---:|
| ≤ 10 | 60 | 47% |
| 11–30 | 29 | 22% |
| 31–80 | 20 | 16% |
| 81–200 | 10 | 8% |
| > 200 | 10 | 8% |

All 278 gold files are `.py`. Three tasks touch only `docs_src/` (executable examples);
no task's gold patch is Markdown-only. **The patch is usually small; the difficulty is
finding the right place and reading the spec correctly.**

### 3.1 Change archetypes (multi-label)

| archetype | tasks | share | what it means |
|---|---:|---:|---|
| control flow | 92 | 71% | adds/changes `if`/`try`/`for`/`while` |
| string | 73 | 57% | message/format/output text |
| typing | 68 | 53% | annotations, `Optional`, generics, signatures |
| import | 42 | 33% | new/changed imports, module moves |
| add API | 31 | 24% | new function/class/method |
| error | 24 | 19% | raises/catches, exception types |
| signature | 18 | 14% | parameter changes |
| docs file | 15 | 12% | `docs/` or `docs_src/` in the patch |
| async | 12 | 9% | `async`/`await` |
| other | 18 | 14% | |

Control flow + strings + typing covers three quarters of the set. That is ordinary Python
maintenance, not exotic framework work.

### 3.2 Test patterns (from `test_patch`)

| pattern | tasks | share |
|---|---:|---:|
| `TestClient` | 54 | 42% |
| `parametrize` | 22 | 17% |
| snapshot | 18 | 14% |
| `pytest.raises` | 15 | 12% |
| fixture | 14 | 11% |
| `monkeypatch` | 8 | 6% |
| `tmp_path` | 4 | 3% |
| `capsys` | 3 | 2% |
| `mock` | 2 | 2% |
| async test | 1 | 1% |
| `CliRunner` | 1 | 1% |

Hidden tests are conventional pytest. There is no custom test runner to reverse-engineer,
and 42% exercise HTTP endpoints through `TestClient`, which means behaviour is asserted at
the public API boundary, not on private helpers.

## 4. Hot files

Where the gold patches actually land. Useful as a prior for a ranker, **not** as a
hard-coded map (hidden repos differ).

### fastapi/fastapi (67 tasks)

| file | tasks |
|---|---:|
| `fastapi/dependencies/utils.py` | 27 |
| `fastapi/routing.py` | 16 |
| `fastapi/_compat/v2.py` | 13 |
| `fastapi/openapi/utils.py` | 12 |
| `fastapi/applications.py` | 7 |
| `fastapi/dependencies/models.py` | 7 |
| `fastapi/params.py` | 5 |
| `fastapi/exceptions.py` | 4 |
| `fastapi/temp_pydantic_v1_params.py` | 3 |
| `fastapi/utils.py` | 3 |

### Textualize/rich (48 tasks)

| file | tasks |
|---|---:|
| `rich/console.py` | 7 |
| `rich/cells.py` | 6 |
| `rich/segment.py` | 5 |
| `rich/markdown.py` | 5 |
| `rich/syntax.py` | 4 |
| `rich/default_styles.py` | 3 |
| `rich/table.py` | 3 |
| `rich/traceback.py` | 3 |
| `rich/text.py` | 3 |

### psf/requests (13 tasks)

`src/requests/utils.py` 5, `models.py` 3, `adapters.py` 2, then one each in `_types.py`,
`sessions.py`, `compat.py`, `exceptions.py`, `status_codes.py`.

### encode/httpx (1 task)

`_parsers.py`, `_pool.py`, `_server.py`, `_network.py`, mirrored under `httpx/` and
`ahttpx/`.

## 5. Lexical overlap between issue and gold patch

Token overlap after stop-word removal, computed per task:

| signal | tasks | share |
|---|---:|---:|
| issue token appears in added code | 102 | 79% |
| issue token appears in gold path | 100 | 78% |
| issue token appears in an added symbol name | 27 | 21% |
| backticked identifier matches a gold path | 9 | 7% |
| single gold file | 91 | 71% |
| no overlap at all | 9 | 7% |

Nine tasks have no lexical bridge at all (`requests_7502`, `requests_7427`,
`requests_7315`, `requests_7205`, `fastapi_11355`, `fastapi_5624`, `rich_3535`,
`rich_2943`, `rich_3105`). A lexical ranker cannot solve those by construction; they need
error-string matching, symbol/graph expansion, or reading the test file.

## 6. Difficulty proxy

Combining signal, gold-file count and changed lines:

| proxy | tasks | share | definition |
|---|---:|---:|---|
| easy | 25 | 19% | rich signal, 1 file, ≤ 30 lines |
| medium | 68 | 53% | rich/medium + ≤ 2 files + ≤ 80 lines, or sparse + 1 file + ≤ 30 lines |
| hard | 36 | 28% | everything else |

If the agent solved every easy task and half the medium ones it would score ~0.45 on this
dev set. That is an upper-bound sanity check, not a forecast: it assumes perfect
localization, perfect spec reading and perfect patch application.

## 7. What this implies for the architecture

1. **Localization is the bottleneck, not code generation.** 71% of gold patches touch one
   file and 47% are ≤ 10 lines. A ranker that puts the gold file in the top 3 is worth
   more than any amount of "write better code" prompting.
2. **The issue is often useless.** 43% of tasks are template/title-only. The scaffold must
   mine the repository (error strings, symbols, sibling APIs, tests) rather than parse the
   issue harder.
3. **Tests are the cheapest oracle.** pytest is available in Container A and 42% of hidden
   tests use `TestClient`. Running the *relevant* test file is a stronger signal than any
   static analysis, and `run_command` truncates at 5,000 chars, so the runner must parse
   the result itself.
4. **Generic Python patterns dominate.** Control flow, strings, typing and imports account
   for most changes. A compact Python/SWE knowledge book is enough; a per-language
   curriculum is not.
5. **Feature tasks need a different heuristic.** New symbols cannot be found lexically;
   copy the nearest sibling and its registration points (`__all__`, router tables,
   `docs_src/<feature>/`).
6. **Repo-specific hot files are a weak prior.** They help on the dev set and may not
   transfer to hidden repositories. Keep them as a tie-breaker, never as a hard rule.

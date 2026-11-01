# Skills, scripts and domain knowledge — final architecture

Decision record for the 31B line, 2026-10-30. Companion to
`docs/TASK_CLASSIFICATION.md` (what the tasks look like) and
`docs/AUDIT_SNAPSHOTS.md` (the localization evidence).

**Decision: one skill, one entrypoint, three modes.**

```
skills/swe-toolkit/
  SKILL.md              # ≤ 25 lines: usage + output legend only
  scripts/swe.py        # locate | inspect | verify
  scripts/_index.py     # walk, AST index, IDF ranking, test demotion
  scripts/_verify.py    # read-only patch gate + targeted pytest
  scripts/_guard.py     # caps, deadlines, subprocess safety
```

Operating rules live in `prompts/system.md`, not in `SKILL.md`. Budgets, sampling and the
model stay exactly as in `ckpt/bundles/exp05_patch_integrity` (the byte-exact 0.20 anchor).

## 1. Verified harness facts that drive the design

These were checked against the installed wheels (`adk_submission 0.2.13`,
`adk-eval-core`, `google-adk 1.36.1`, `swegemma 0.2.11`), not inferred from the README.

| fact | evidence | consequence |
|---|---|---|
| `run_skill_script` does **not** require `load_skill` first | `RunSkillScriptTool.run_async` calls `_get_or_fetch_skill(skill_name)` directly | skip the "mandatory load_skill" call; save 1 of 28 |
| skill scripts run inside Container A | `swegemma/harness/agent_runner.py:609-620` builds `AdkSandboxCodeExecutor` and passes it to `compile_submission` | the script can read `/workspace` and run pytest |
| the executor writes `/workspace/.adk_exec_<id>.py`, runs `python3 <path>`, then deletes it | `adk_eval_core/sandbox/base.py` | dotfile is a (small) patch-pollution risk; `verify` must flag it |
| the skill wrapper materializes scripts to a temp dir and `chdir`s there | `google.adk.tools.skill_toolset._SkillScriptCodeExecutor._build_wrapper_code` | never rely on cwd; default `--root` to `/workspace` |
| skill output is **not** truncated by the harness | executor returns `res.stdout`; only `swegemma/tools/execution.py:54` caps `run_command` | the script must self-cap (~4,000 chars) or it can blow the 32,768 context |
| each `run_skill_script` costs **1 tool call** | the executor calls `budget_check_fn()` → `SwegemmaContext.check_budget()` (default `count_tool_call=True`) | budget it like `run_command` |
| `submit_patch` and `get_status` are free | `@budget_gated(count_tool_call=False)` | always submit |
| `run_command` caps stdout/stderr at 5,000 chars, timeout `min(300, remaining)` | `swegemma/tools/execution.py:21-70` | pytest's verdict at the end is lost; `verify` must parse it itself |
| the initial prompt already contains a workspace map (≤200 entries, `tests/`, `docs/` pruned) and environment rules | HARNESS_README §5.2 | a "repo profiler" script duplicates what the model already has |
| compaction: interval 15, threshold 14,336 tokens, overlap 2, retention 5 | HARNESS_README §7.2 | keep durable rules in `system.md`; treat tool results as ephemeral |

The first and sixth rows are the ones the earlier proposals got wrong in opposite
directions: GPT assumed a mandatory `load_skill` bootstrap (unnecessary), and Kilo assumed
scripts were free (they are not). Both change the call math.

## 2. What survives from each proposal

| element | GPT (2 skills / 4 scripts) | Kilo (1 skill / 3 modes) | verdict |
|---|---|---|---|
| mandatory activation via `system.md` | yes | yes | **keep** — but as a toolkit block, not a `load_skill` step |
| one consolidated first call | `repo_bootstrap.py` | `locate` | **keep Kilo's** — the harness already injects the repo map, so profiling is redundant |
| real code excerpts | yes | yes | **keep** — excerpts are the value; a file list is not |
| read-only validator | `patch_validator.py` | `verify` (gate half) | **keep** — never auto-fix, print the exact command |
| stdlib only | yes | yes | **keep** |
| clean A/B off exp05 | yes | yes | **keep** |
| two skills | `swe_core` + `python_swe` | one | **drop `python_swe`** — every task is Python; generic advice costs a call and tokens the 31B already has |
| four scripts | bootstrap / analyzer / diagnostics / validator | locate / inspect / verify | **drop two** — diagnostics cannot post-process truncated output (it must run pytest, which `verify` does); validator is `verify`'s gate |
| state card in `/tmp/plan.md` | yes | — | **replace** with a free `STATE:` text line at the start of each turn |
| issue transport | not addressed | `--issue` | **keep, and make it a dict arg** (no shell quoting) |
| knowledge book | yes | — | **defer to a 6-row table** in `system.md`; the measured playbook precision is 32.6%, i.e. two thirds noise |
| `test_diagnostics` | post-processes output | — | **drop** — `run_command` truncates to the first 5,000 chars, so post-processing cannot see the verdict |

## 3. Why one skill, and why three modes

**One skill.** A second skill costs a `load_skill` call (if you use it), a second
`SKILL.md` competing for attention, and a second set of instructions that can be
summarized away by compaction. The task audit says 71% control flow / 57% strings /
53% typing / 33% imports — ordinary Python. There is no language-selection decision to
make, so there is no reason to make it a tool call.

**Three modes.** Each mode maps to a decision the agent actually makes:

| mode | question it answers | when |
|---|---|---|
| `locate` | where is the behaviour produced? | call 1, always |
| `inspect` | what else is coupled to this symbol? | only for multi-file, async, inheritance, or "the obvious fix did not work" |
| `verify` | is the patch real, and does the relevant test pass? | before `submit_patch` |

Anything else is a script the agent will not call. `repo_bootstrap` duplicates the
injected workspace map; `test_diagnostics` cannot see past the 5,000-char cut;
`python_analyzer` is `inspect` with a narrower job.

## 4. Archive layout

```
submission.zip
├── agent.yaml                 # 6 tools + `skills: [skills/swe-toolkit]`
├── eval_config.yaml           # 240 s / 28 calls / 8 min / 80 turns  (unchanged)
├── configs/sampling.yaml      # temp 0.2, top_p 0.95, 8192 out, thinking 4096 (unchanged)
├── prompts/system.md          # exp05 prompt, CALL PLAN replaced by TOOLKIT block
└── skills/swe-toolkit/
    ├── SKILL.md
    └── scripts/
        ├── swe.py
        ├── _index.py
        ├── _verify.py
        └── _guard.py
```

`agent.yaml` adds exactly one line:

```yaml
skills:
  - skills/swe-toolkit
```

The six tools stay `run_command`, `read_file`, `edit_file`, `write_file`, `get_status`,
`submit_patch`. No graph tools: the hidden repositories may not ship graph data, and the
public benchmark showed graph-only retrieval is weaker than lexical+AST.

## 5. `prompts/system.md` — the toolkit block

Replace the existing `# CALL PLAN` section (400 chars) with this block (656 chars). Net
prompt growth is **+256 chars**, half the +554-char change that `exp08` showed to be
neutral-to-negative — and this block replaces instructions rather than adding prose.

```markdown
## TOOLKIT
Call 1, before reading anything: run_skill_script with
skill_name="swe-toolkit", file_path="scripts/swe.py",
args={"issue": "<title + exact symbols, error strings, paths, expected behaviour; <=1200 chars>"}.
Use the excerpts it returns. A "123 |" prefix is a line number, not code.
Never run locate twice. If output says STATUS: DEGRADED, run the FALLBACK command it prints.
First source edit by call 8. Start every turn with:
STATE: file:line | edited? | last test | next.
Before submit_patch, run swe.py verify and fix every FAIL line. Then submit_patch.
If a skill tool errors twice, stop retrying and continue with run_command and read_file.
```

The block does four jobs: forces the first call, caps its cost, defines the recovery path,
and keeps a compaction-resilient state line. It deliberately does **not** teach Python or
the harness; the model already has that.

`SKILL.md` stays a legend, not a manual:

```markdown
---
name: swe-toolkit
description: "Locate, inspect and verify a Python fix in /workspace."
---
# swe-toolkit
scripts/swe.py, three modes. Args may be a list or a dict.
- locate  --issue TEXT [--root /workspace] [--top 5] [--run-repro]
          top files with excerpts, test command, fallback command.
- inspect --symbol NAME [--root /workspace]
          definition, callers, overrides, tests, sync/async twins.
- verify  [--test PATH] [--root /workspace]
          read-only patch gate + targeted pytest; prints PASS/FAIL per check.
Output: first line STATUS: OK|PARTIAL|DEGRADED, then <=4000 chars.
"123 | code" = file line 123. Never edit a file based on the prefix.
Exit code is always 0; read STATUS, not the exit code.
```

That is 16 lines. It contains no operating rules that would be lost if compaction drops
the tool result.

## 6. `swe.py` contract

```
python3 swe.py locate  --issue TEXT [--root DIR] [--top N] [--run-repro]
python3 swe.py inspect --symbol NAME [--root DIR]
python3 swe.py verify  [--test PATH] [--root DIR]
```

- `--root` defaults to `/workspace` when it exists, else cwd.
- Args arrive either as a list (`["locate","--issue","..."]`) or a dict
  (`{"issue":"...","root":"/workspace"}`); the ADK wrapper converts a dict to
  `--key value`, one argv element per value, so no shell quoting is involved.
- Always exit 0. First line `STATUS: OK | PARTIAL | DEGRADED(reason)`.
- Hard self-cap 4,000 chars, `[truncated]` marker, per-section budgets.
- Watchdogs: locate 25 s, inspect 40 s, verify 180 s. On expiry print the partial report
  and `os._exit(0)`.
- Never write inside `/workspace`. State goes to `/tmp`. `PYTHONDONTWRITEBYTECODE=1`.

### 6.1 `locate`

1. **Parse the issue** into: backticked identifiers, dotted paths, `*.py` paths, traceback
   frames (`File "...", line N, in fn`), quoted error strings, exception names,
   CamelCase/snake_case tokens, and expected-behaviour phrases.
2. **Walk** with `followlinks=False`; skip `.git`, venvs, `build`, `dist`, `node_modules`,
   caches; skip files > 500 KB and binaries; cap at 8,000 files; `errors="replace"`.
3. **Index** every function and class with `ast`: qualname, line range, signature,
   decorators, bases, calls, string constants, first docstring line. On `SyntaxError`,
   fall back to a regex `def`/`class` scan.
4. **Score** with IDF-weighted matches:
   - traceback frame or exact qualname hit: ×6
   - error string found in source: ×4
   - identifier in name/signature/decorators: ×2
   - identifier in body/strings: ×1
   - path-token match: ×1.5
   - test path: **×0** (never gold — measured: hit@3 6/7 → 7/7)
   - `docs_src/`: ×0.5 (keep: 3 tasks have docs-code gold patches)
   - vendored/`third_party`: ×0.3
5. **Aggregate to files**: best symbol + 0.25 × next three.
6. **Emit** top 5 files. #1 gets up to 40 lines around its best symbol; #2–5 get a
   signature plus 8 lines. Add the test command and a `git grep` fallback.
7. `--run-repro` (off by default): extract fenced code blocks, run each with a 20 s
   timeout, return the traceback. One call instead of a guess-and-run loop.

### 6.2 `inspect`

For one symbol, return: definition and signature; AST-resolved callers; subclass overrides;
tests that reference it; and **parallel paths** — sync/async twins, `to_*`/`from_*`,
`__eq__`/`__hash__`, and other files containing the same error string. The last item is
what multi-change tasks need and what grep cannot do. Skip `inspect` for a one-function
fix; the prompt says so.

### 6.3 `verify`

Two jobs in one call, because they always run together.

**Patch gate (read-only):**

| check | failure it prevents |
|---|---|
| `git status --porcelain` + `git diff --stat _swegemma_baseline` (fallback HEAD) | missing or unexpected edits |
| protected paths (`test_*.py`, `*_test.py`, `tests/`, `conftest.py`, `pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`) | edits the grader resets |
| test-only diff | a patch that becomes empty after stripping |
| ignored new files → print `git add -N -f <path>` | files silently dropped by `git add -N .` |
| in-memory `ast.parse` of changed `.py` | syntax errors (never `py_compile`; it writes `__pycache__`) |
| leftover `.adk_exec_*`, `*.orig`, `*.rej`, `tmp*`, `scratch*` | scratch files in the patch |
| empty diff | submitting nothing |
| whole-file rewrite / CRLF heuristic | `write_file` blowups |

**Targeted tests:** choose `--test`, else `tests/test_<module>.py`, else the first test file
that references the symbol. Run

```
PYTHONDONTWRITEBYTECODE=1 python -m pytest <file> -x -q --tb=short \
  -p no:cacheprovider --junitxml=/tmp/swe_junit.xml
```

with a 150 s timeout, then parse the JUnit XML: failed ids, first assertion line, and the
last traceback frame under `/workspace` that is not a test file. If no test file exists,
fall back to `python -c "import <module>"` plus `ast.parse`.

The gate is read-only by design. It prints the fix command; the root agent decides.

### 6.4 Current implementation vs this contract

The prototype is close, but not there. The delta is the work for E1.

| piece | current | target |
|---|---|---|
| `swe.py` args | `--query`, `--symbol`, `--test`, `--root` | `--issue` (alias `--query`), `--top`, `--run-repro` |
| `_index.locate` | AST + IDF + path tokens | add test demotion (×0), traceback ×6, error string ×4, `docs_src` ×0.5, vendored ×0.3 |
| `_index.locate` output | top files + top symbols + `_knowledge` hints | top 5 files, 40-line excerpt for #1, signature+8 lines for #2–5, test command, fallback |
| `_knowledge` hints | injected by `locate` today | **remove from v1** (32.6% precision); six-row table moves to `system.md` |
| `_verify` gate | diff names, protected, ignored new files, syntax, pytest+JUnit, tail | add untracked files to the changed set, empty-diff FAIL, scratch/`.adk_exec_*` scan, assertion + repo-frame extraction, auto test selection |
| `_verify` output | free text | `STATUS` line + `PASS`/`FAIL` per check + `NEXT` |
| deadlines | watchdog in `swe.py` (25/40/180 s) | extract to `_guard.py`; print partial report before `os._exit(0)` |
| status line | `STATUS: OK` / `DEGRADED` only | add `PARTIAL` for "report produced, one section failed" |

Two concrete bugs to fix while doing this: `git diff --name-only` misses untracked files
(so new files are not syntax-checked), and `_verify` never fails on an empty diff.

Also delete `scripts/bootstrap.py` in E1. It is a leftover from the first prototype that
`rglob`s `/` looking for `swe.py`; it is not referenced by `swe.py`, it is not in the
target layout, and it is exactly the kind of unbounded filesystem walk the reliability
contract forbids.

**Status 2026-11-01 — landed.** Every row above is implemented except `--run-repro`, which
was dropped: the prompt already allows one `python -c` repro and a second code path for the
same thing would only spend calls. `scripts/bootstrap.py` is deleted. The measured effect
and the fixture tests are in `RESULTS.md` (2026-11-01) and `docs/AUDIT_SNAPSHOTS.md` §2.1.

## 7. Domain knowledge: a table, not a book

The paper-track measurement is blunt: 258 playbook triggers, **32.6% precision**. Two
thirds of injected hints are irrelevant, and `exp08` showed that +554 chars of prose did
not help. So v1 ships a six-row "first check" table inside `system.md` (~450 chars), not a
`_knowledge.py` module:

| symptom | first check |
|---|---|
| new API / option | copy the nearest sibling and every registration point (`__all__`, router table, `docs_src/<feature>/`) |
| wrong output / string | exact text and escaping; compare with the nearest passing test |
| exception | exact class and message; search the string in source |
| typing / Pydantic | v1 vs v2 compat; `Optional`, `Annotated`, defaults |
| async | fix the sync twin too; `await` on every path |
| docs task | edit the executable example under `docs_src/` |

The full ten-playbook book stays in the repo (`skills/swe-toolkit/scripts/_knowledge.py`)
for the paper track, but is not wired into the 31B submission until an error analysis shows
failures are wrong *fixes* rather than wrong *locations*. On the current evidence they are
wrong locations.

## 8. Call budget

| step | calls |
|---|---:|
| `locate` | 1 |
| read the top file regions (`read_file` ×3–5) | 3–5 |
| edit (`edit_file` ×2–4) | 2–4 |
| `verify` | 1 |
| fix + re-verify | 2–4 |
| `inspect` (optional) | 0–1 |
| `submit_patch` | 0 |
| **total** | **9–17 of 28** |

GPT's design spends 5 overhead calls before the first edit (`load_skill`, bootstrap,
analyzer, diagnostics, validator) and still cannot see the pytest verdict. This design
spends 2–3 and does see it. The slack (11–19 calls) is what pays for the second and third
fix attempt, which is where the 0.17→0.20 patch-integrity gain came from.

## 9. Reliability contract

- Exit 0 always; `STATUS` is the contract, not the exit code.
- Every module in its own `try/except`; one failure cannot kill the report.
- Subprocesses: explicit `timeout`, new session, `killpg`, `GIT_TERMINAL_PROMPT=0`,
  `GIT_OPTIONAL_LOCKS=0`, `--no-pager`.
- `argparse.parse_known_args` + caught `SystemExit`; bad args fall back to defaults.
- Suppress `SyntaxWarning`; catch `RecursionError`/`MemoryError`; regex fallback on
  `SyntaxError`.
- Never write inside `/workspace`; write state only to `/tmp`.
- Output cap 4,000 chars with a `[truncated]` marker.

## 10. Failure modes and mitigations

| failure | mitigation |
|---|---|
| `locate` ranks the wrong file | fallback `git grep` printed in the report; `verify`'s failing test points at the real file |
| issue extract misses the key identifier | the model may pass the raw title; `locate` also uses the whole token set, not just backticks |
| `NO_CODE_EXECUTOR` | verified present in the real harness (`agent_runner.py:609`); if it ever regresses, the prompt says to fall back to `run_command` after two errors |
| skill not found | `run_skill_script` returns `SKILL_NOT_FOUND`; the `skills:` path must match the directory |
| output too long | 4,000-char self-cap; the harness does **not** cap skill output |
| pytest hangs | 150 s timeout inside `verify`, under the 300 s executor cap |
| pytest missing | import smoke test + `ast.parse` |
| compaction drops the skill text | rules are in `system.md`; `STATE:` line every turn |
| `.adk_exec_*` left in `/workspace` | `verify` flags it; the agent deletes it before submitting |

## 11. What not to build

- **Per-language skills.** Four Python repos, zero non-Python tasks.
- **A separate test runner.** `verify` runs pytest; a second script is another call.
- **A `/tmp/plan.md` state file.** Writing it costs a call; a `STATE:` text line is free and
  survives compaction.
- **A repo profiler.** The harness already injects a 200-entry workspace map and the
  environment rules.
- **A large knowledge book.** 32.6% precision, and prompt growth has already failed once.
- **Auto-fixing validators.** The gate reports; the root agent edits.

## 12. Validation plan

Offline, before any submission:

1. `tools/audit_locate.py` on the seven snapshots: currently hit@1 4/7, hit@3 6/7,
   hit@5 6/7, hit@10 7/7, median 1.1 s. After test demotion: 5/7, 7/7, 7/7, 7/7.
2. Adversarial fixtures: empty repo, missing `_swegemma_baseline`, non-UTF8 file, Python 2
   file, deep nesting, symlink loop, 5 MB `.py`, a hanging pytest.
3. Re-run the 129-task retrieval benchmark (`research/PAPER_EXPERIMENTS.md`) with the
   demoted ranker; target file R@10 ≥ 0.55 (current `swe_toolkit` 0.4587, hybrid RRF
   0.5701).
4. Bundle gates: `verify_bundle.py --bundle <new>` and `verify_notebook.py`.

Harness probes already done (see §1): code executor present, output uncapped, skill calls
count as one tool call, `load_skill` not required.

## 13. 31B experiment plan

Economics, corrected 2026-10-30: **1 submission/day, no total cap, 1 pending at a time,
2 final selections.** That is up to ~33 more submissions before 2026-12-02, which is
enough for a real ladder — but the public LB is only ~58 tasks, so one task ≈ 0.017 and
deltas below ~0.05 are noise. Spend submissions on mechanisms, not on hope.

| exp | single change vs previous | mechanism | expected | decision rule |
|---|---|---|---|---|
| **E0 control** | none — re-run `exp05` byte-identical | measures run-to-run noise | 0.15–0.25 | establishes the noise band; do not skip |
| **E1 toolkit v1** | add `skills/swe-toolkit/` + `skills:` line + replace CALL PLAN with TOOLKIT block | 1 call replaces 4–8 exploratory calls; `verify` sees the pytest verdict the 5 k cap hides; patch gate prevents empty patches | +0.03–0.07 | keep if ≥ E0 + 0.05, or if logs show locate used and verify PASS rate high |
| **E2 test demotion** | one ranker rule in `_index.py` | protected paths cannot be gold; measured 6/7 → 7/7 hit@3 | +0.02 | keep if E1 is kept and offline R@10 improves |
| **E3 verify runs pytest** | only if E1 shipped gate-only | removes a `run_command` round-trip and parses JUnit | +0.02 | keep if call counts drop without score loss |
| **E4 budget rebalance** | 28→34 calls, 8→9 min | only if E1 logs show `BudgetExceeded` or first edit after call 8 | 0 to +0.03 | revert if any run exceeds the 12 h total |
| **E5 knowledge table** | add the six-row table | wrong-fix failures only | ~0 | keep only if E1–E4 plateau and error analysis shows wrong fixes |

**Instrument.** The LB is the final arbiter, but it is noisy. Repair
`research/kernel_devset_eval/` (currently `KernelWorkerStatus.ERROR`) and use the 24-task
paired run for go/no-go: paired per-task outcomes need far fewer samples than two
independent LB scores. If it cannot be repaired, run E0 and E1 twice each and treat any
difference below 0.05 as unresolved.

**What I would not do:** fine-tune a LoRA on the 129 public tasks (small, dev-only, and
adapter serving collapses the KV cache), add a planner/coder multi-agent split (`exp01`
scored 0.05), or raise `max_time_minutes` above 9 (the 12 h total is the binding
constraint, and 12-minute tasks were measured to score 0).

## 14. Is 0.29 the ceiling?

No, but it is close to the ceiling for a *prompt-only* 31B scaffold.

- The patch is usually tiny (47% ≤ 10 lines, 71% single-file), and a ranker already puts
  the gold file in the top 3 on 6/7 representative tasks (7/7 with test demotion). The
  model is not failing because the code is hard to write; it is failing because it does not
  reliably find, verify and submit the change within 28 calls.
- That is an engineering gap, and it is the gap this toolkit attacks. A realistic band for
  the next three or four experiments is **0.24–0.34**. A 0.40+ result would need a
  genuinely better scaffold plus favorable task sampling; I would not promise it.
- The 0.29 leader is probably running the same 31B with a better harness. There is no
  evidence of a different model or of an unreachable technique. The 0.24 cluster is
  consistent with "same model, slightly worse scaffolding", which is exactly where a
  deterministic locate/verify loop should show up.
- The honest risk: the hidden repositories differ from the dev set, so repo-specific
  priors do not transfer. Every mechanism above is repository-agnostic by construction;
  that is deliberate.

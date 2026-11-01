---
name: swe-toolkit
description: "Locate the file for an issue, inspect a symbol, verify an edit in /workspace."
---
# swe-toolkit

`scripts/swe.py`, three modes. All output is plain text on stdout and the exit code is
always 0 — read the `STATUS:` line, not the exit code.

| mode | what it returns | arguments |
|---|---|---|
| `locate` | the 5 most likely source files, an excerpt of the best one, a test command and a `git grep` fallback | `--issue TEXT` (or `--query TEXT`), `--top 5` |
| `inspect` | definition, callers, overrides, subclasses and sync/async twins of a symbol | `--symbol NAME` |
| `verify` | read-only patch gate plus one targeted pytest run | `--test "tests/test_x.py -x -q -k keyword"` |

`--root` defaults to `/workspace`. Do not pass it unless the repository is elsewhere.

## Calling it

Use `run_skill_script` (cold-call is fine; ADK may also suggest `load_skill` first, either works):

```
run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py",
                 args=["locate", "--issue", "<the issue text>"])
```

`args` is a list; `--root` defaults to `/workspace`, so do not pass it.

## Reading the output

`locate` and `inspect`:

- `STATUS: OK` — full scan.
- `STATUS: PARTIAL` — the scan hit its 20 s budget and ranked only part of the tree.
  The files it did return are still the best guess; use them.
- `STATUS: EMPTY` — no Python files under the root. Use the `FALLBACK:` line.
- `STATUS: DEGRADED` — the tool failed. Use the `FALLBACK:` line.

`verify`:

- `STATUS: OK` — the patch is structurally valid (and the named tests pass, if `--test`).
- `STATUS: PARTIAL` — the patch is valid but a check needs attention (a failing test, or an
  ignored new file). Read the `FAIL`/`IGNORED` line.
- `STATUS: FAIL` — the patch is empty, or it touches a protected path, or a changed file
  does not compile. Do not submit until this is `OK`.

`locate` also prints `NEXT:` (the exact `read_file` call to make) and `TEST:` (the pytest
command to run after editing). Prefer those over inventing your own.

Line prefixes in an excerpt look like `123 | code`; the number is the file line. Never
copy the prefix into an edit.

## Budget

`locate` costs one tool call and up to ~20 s. Call it once per task, before the first
`read_file`, and only when the issue does not already name a file. Do not call it twice.

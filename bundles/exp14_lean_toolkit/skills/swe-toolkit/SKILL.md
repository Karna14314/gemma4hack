---
name: swe-toolkit
description: "Locate the file for an issue, inspect a symbol, verify an edit in /workspace."
---
# swe-toolkit

`scripts/swe.py`, three modes (output plain text, exit code always 0; read the `STATUS:` line).

| mode | returns | args |
|---|---|---|
| `locate` | top 5 source files + excerpt + `NEXT:`/`TEST:`/`FALLBACK:` | `--issue TEXT` (or `--query`), `--top 5` |
| `inspect` | def, callers, overrides, subclasses, twins of a symbol | `--symbol NAME` |
| `verify` | read-only patch gate + optional pytest | `--test "tests/test_x.py -x -q -k kw"` |

`--root` defaults to `/workspace`.

## Calling it (cold-call is fine; ADK may suggest `load_skill` first, either works)

```
run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py",
                 args=["locate", "--issue", "<keywords/error <=1500 chars>"])
```
`args` is a list. To verify: `args=["verify"]`.

## Reading output
- `STATUS: OK` full scan; `PARTIAL` hit 20s budget (still use results); `EMPTY`/`DEGRADED` use `FALLBACK:` line.
- `verify`: `OK` = structurally valid; `PARTIAL` = check FAIL/IGNORED line; `FAIL` = empty/protected/stray/syntax.
- `locate` prints `NEXT:` (exact read_file) and `TEST:` (pytest command). Prefer those.

## Budget
`locate` = 1 call, up to ~20s. Call once per task before first read_file, only when issue lacks a path. `verify` caps pytest at 45s.

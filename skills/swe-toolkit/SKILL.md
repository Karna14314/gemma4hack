---
name: swe-toolkit
description: "Locate, inspect and verify a Python fix in /workspace."
---
# swe-toolkit
`scripts/swe.py`, three modes. Args may be a list or a dict.

- `locate --issue TEXT [--root /workspace] [--top 5] [--run-repro]`
  Top files with real excerpts, a test command, and a fallback command.
- `inspect --symbol NAME [--root /workspace]`
  Definition, callers, overrides, tests, sync/async twins.
- `verify [--test PATH] [--root /workspace]`
  Read-only patch gate plus targeted pytest; prints PASS/FAIL per check.

ADK: `run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py", args=["locate","--issue","..."])`

Output: first line `STATUS: OK|PARTIAL|DEGRADED`, then at most 4000 chars.
`123 | code` means file line 123. Never edit a file from the prefix.
Exit code is always 0; read STATUS, not the exit code.
State: `/tmp/swe_state.json`.

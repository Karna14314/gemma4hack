# TOOL CONTRACT — gemma-4-developer-agent harness tools

Source: `HARNESS_README.md` §5–§8 (official harness documentation) plus the tool
implementations in `swegemma.tools` (`execution.py`, `workspace.py`, `graph.py`).
No local wheel execution was available in this container, so exact `error_message`
text is recorded as the harness's documented `error_type` plus the JSON error shape;
the `error_type` strings below are the stable identifiers returned in
`{"status":"error","error_type":...}`.

## 0. Global facts

- Working directory for all tools: `/workspace` (agent sandbox). `run_command` runs
  `bash -c` with cwd `/workspace`. File tools resolve paths relative to
  `/workspace`; leading `/` or `/workspace/` is stripped. Any `..` traversal raises
  `ValidationError`.
- Python: 3.13 (sandbox image). All repo/test deps pre-installed; **offline** —
  no network, no PyPI. Do not run `pip install`.
- Output caps: command stdout/stderr each `5,000` chars; file reads `150` lines
  **and** `10,000` chars (whichever hits first); edit diff `5,000` chars.
- Command timeout: `min(command_timeout_seconds=300, max(5, int(remaining_time)))`.
  A timed-out command returns `error_type: "TimeoutExceeded"` and does **not**
  end the session (unless the session time budget also expired).
- Pager/interactive pitfalls: commands run non-interactively via `bash -c`; there
  is no TTY. Use `git --no-pager`, `--no-color`, `PAGER=cat`, and non-interactive
  flags (`-y`, `--batch`). Long-running or interactive commands will hit the
  300 s timeout and be killed.
- Budget: every tool except `submit_patch` and `get_status` counts toward
  `tool_calls`. When `tool_calls >= 20` and `remaining <= 10`, responses include
  `budget_warning`.
- All tools return a JSON string: success `{"status":"ok",...}` or error
  `{"status":"error","error_type":...,"error_message":...,"details":{...}}`.

## 1. Tool catalog

### run_command(command: str)
- Signature: `run_command(command: str) -> str` (JSON).
- Runs `/bin/bash -c <command>` in `/workspace`.
- Timeout: `min(300, max(5, remaining_time))` s.
- Output: stdout and stderr each truncated to 5,000 chars.
- Success: `{"status":"ok","stdout":...,"stderr":...,"exit_code":0}`.
- Nonzero exit: `{"status":"error","error_type":"CommandError","error_message":...,
  "details":{"stdout":...,"stderr":...,"exit_code":N}}`.
- Timeout: `{"status":"error","error_type":"TimeoutExceeded",...}`.

### submit_patch()
- Signature: `submit_patch() -> str` (JSON).
- Free (does not count toward tool_calls); callable even at tool-call cap while
  wall-clock remains.
- Runs `git add -N .` (respects `.gitignore`), then
  `git diff --binary _swegemma_baseline` (fallback `HEAD`), strips protected
  test/config files, sets `patch_submitted=True`.
- Success: `{"status":"ok","patch_size":N,"files_changed":M}`.
- If never called, harness grades the working tree (fallback).

### get_status()
- Free. Returns budget consumption and patch status:
  `tool_calls_used`, `patch_submitted`, `patch_size`, `tool_calls_remaining`,
  `max_tool_calls`, `time_seconds_remaining`, `max_time_minutes`,
  `agent_elapsed_seconds`, `max_turns`, `command_timeout_seconds`.

### read_file(filepath, start_line=None, end_line=None)
- 1-indexed inclusive line slicing.
- Caps: 150 lines AND 10,000 chars (first hit truncates; `is_truncated:true`,
  `end_line` reflects last complete line).
- Success: `{"status":"ok","filepath":...,"content":...,"start_line":...,
  "end_line":...,"total_lines":...,"is_truncated":bool}`.
- Missing path / wrong type / empty file: error (see battery).

### edit_file(filepath, old_string, new_string, allow_multiple=False)
- 3-tier matching: `exact` (after CRLF->LF), `flexible` (per-line strip +
  re-indent new_string to baseline), `regex` (tokenize on delimiters, `\s*`).
- Uniqueness: >1 match with `allow_multiple=False` -> `FileEditError`, no write.
- Also `FileEditError` if file missing, empty (0 bytes), or `old_string==""`.
- Success: `{"status":"ok","filepath":...,"occurrences":N,"strategy":...,
  "diff":... (<=5000 chars),"is_truncated":bool}`.

### write_file(filepath, content)
- Creates/overwrites; `mkdir -p` parents.
- Success: `{"status":"ok","filepath":...,"size":N}`.

### get_code_neighbors(node, edge_type=None, max_neighbors=50)
- Graph tool; only useful when pre-computed graph/embeddings exist for the repo.
- Resolves short names via 4 tiers (exact -> `.`/`/` suffix -> case-insensitive
  -> substring). `edge_type` optional filter (`CALLS`, `DEFINED_IN`, `IMPORTS`).
- Usually returns nothing useful; banned in prompts.

### search_similar_code(query, k=10)
- Offline cosine similarity over pre-computed `.npz` embeddings; pass a symbol
  name, not prose. Banned in prompts.

### get_code_subgraph(nodes: list[str])
- Induced subgraph for a list of symbols. Banned in prompts.

## 2. Scripted battery (conditions -> error_type)

Run against the harness's real tool implementations where available; results below
record the documented `error_type` for each condition.

| Condition | Tool | error_type | Notes |
|---|---|---|---|
| Missing path | read_file / edit_file / write_file (read) | `FileEditError` (edit) / tool error (read) | read: file not found; edit: file does not exist |
| Wrong working dir | any (path with `..`) | `ValidationError` | `_resolve_workspace_path` rejects traversal |
| Non-unique edit string | edit_file (2+ matches, allow_multiple=False) | `FileEditError` | no modification; make old_string more specific |
| Non-matching edit string | edit_file (0 matches) | `FileEditError` | 3-tier matching attempted first |
| Whitespace/indentation mismatch | edit_file | often succeeds via `flexible`/`regex` tier | strategy field reports which tier matched |
| Stale content after an edit | edit_file with old text from before a prior edit | `FileEditError` (0 matches) | re-read file before editing |
| Very large output | run_command (>5000 chars) | n/a (success) | stdout/stderr truncated to 5000; `is_truncated` not on command, but content cut |
| Binary/huge file read | read_file (>150 lines / >10000 chars) | n/a (success) | `is_truncated:true`, `end_line` last complete line |
| Long-running command | run_command (>300s) | `TimeoutExceeded` | session continues |
| Interactive command | run_command (prompts for input) | `TimeoutExceeded` or hang until 300s | use non-interactive flags |
| Nonzero exit code | run_command (exit != 0) | `CommandError` | details include stdout/stderr/exit_code |

### 2.1 Exact error strings captured

- Command nonzero: `error_type="CommandError"`, `error_message` carries the
  command's failure text; `details.stdout`, `details.stderr`, `details.exit_code`.
- Timeout: `error_type="TimeoutExceeded"`.
- Path traversal: `error_type="ValidationError"` (message: path must be posix
  and free of traversal).
- Edit failures: `error_type="FileEditError"` with messages for: file does not
  exist; file is empty (0 bytes); `old_string` is empty (`""`); multiple
  occurrences found (count reported).
- Budget warning (when <=10 calls remain): field `budget_warning` with text
  `"Only X tool call(s) remaining (Y/Z used). Finalize your edits and call
  submit_patch soon."`

### 2.2 Recommended call patterns (derived)
- Read with `start_line`/`end_line` ranges; never read whole large files.
- Copy edit strings byte-for-byte from the most recent `read_file` output.
- Re-read after every edit to confirm it landed (the diff is truncated at 5000).
- Never edit from stale tool output.
- Check `exit_code` and stdout of every command; cap output with `head`/`tail`.
- Use `timeout` and non-interactive flags; `git --no-pager`.
- No long-running or interactive commands.
- After 2 consecutive tool errors, diagnose once and switch strategy.
- Never run full test suites; name one file and add `-k`.

## 3. Environment rules (from harness initial prompt)
- Single command timeout: 300 s.
- Command output limit: 5000 chars.
- File view limit: 150 lines per read_file.
- File char limit: 10000 chars per read_file.
- Offline: no network/PyPI; all deps pre-installed.
- Working tree graded if submit_patch never called.
- submit_patch free; patch built via `git add -N .` (respects .gitignore).
EOF
echo done
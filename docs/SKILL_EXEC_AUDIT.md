# SKILL_EXEC_AUDIT — exp14_lean_toolkit (swe-toolkit)

Validation that the `swe-toolkit` skill loads and runs inside the real competition
harness. Evidence cited as `file:line` against the installed wheels
(`swegemma 0.2.11`, `adk_submission 0.2.13`, `google-adk 1.36.1`,
`adk_eval_core 0.1.0`) and the live `HARNESS_README.md`.

## a. Where does `run_skill_script` execute?

Inside the **per-task container (Container A)**, on the same filesystem as `/workspace`,
not on the host. Executor: `AdkSandboxCodeExecutor` (adk_eval_core).

Evidence:
- `swegemma/harness/agent_runner.py:604-621` — `script_timeout` derived from
  `config.harness.command_timeout_seconds` (default 300); `code_executor =
  AdkSandboxCodeExecutor(sandbox=context.sandbox, timeout_seconds=script_timeout, ...)`;
  passed to `compile_submission(..., code_executor=code_executor, script_timeout=script_timeout)`.
- `adk_eval_core/sandbox/base.py:195-215` — `execute_code` writes the wrapper to
  `sandbox.work_dir/.adk_exec_<id>.py`, runs `python3 <path>` inside the sandbox,
  then deletes the temp file. `sandbox.work_dir` is `/workspace`.
- `google/adk/tools/skill_toolset.py:625-634` — `_SkillScriptCodeExecutor` materializes
  the skill's files into a `tempfile.TemporaryDirectory()` and `os.chdir(td)` for the
  duration of the run, restoring the original cwd in `finally`. So the script's cwd is a
  temp dir, but `/workspace` is reachable by absolute path (and `--root` defaults to
  `/workspace` in `swe.py:_default_root`).

Conclusion: the script can read `/workspace`, run `git`/`pytest` there, and edit files
via the agent's own tools. It is not host-side.

## b. cwd, env, Python version, git/pytest availability

- Initial cwd of the python process: `/workspace` (sandbox work_dir). The skill wrapper
  then `chdir`s to a temp dir (`skill_toolset.py:626-634`), so `swe.py` must not rely
  on cwd; it defaults `--root` to `/workspace` (`swe.py:_default_root`).
- Env: the container environment; `swe.py` propagates `os.environ` and sets
  `PYTHONDONTWRITEBYTECODE=1` for pytest (`_verify.py:_run_pytest`).
- Python version: the container's `python3` (the wheel targets 3.11+; the harness
  serves 3.12 per the live README). Scripts are stdlib-only, so version is not a risk.
- git: available — `verify` calls `subprocess.run(["git", ...], cwd=root)`
  (`_verify.py:_run_git`, `git_diff_names`).
- pytest: available — `_run_pytest` uses `shutil.which("pytest")` or
  `sys.executable -m pytest` with a 45 s timeout (`_verify.py:_run_pytest`).

## c. Does `/tmp` persist across calls within one task?

Yes. The skill files are materialized into a `TemporaryDirectory` that is deleted after
each call, but container `/tmp` itself persists for the life of the task. `swe.py`
writes `/tmp/swe_session_state.json` on `locate`/`verify` and reads it on the next
`locate` to emit a `[SESSION STATE]` header (idempotent compaction resume).

Evidence: `swe.py:do_locate` (reads `/tmp/swe_session_state.json`); `do_verify` (writes
verify status). Integration test confirmed the header appears on the second call.

## d. Timeouts and stdout truncation

- `run_skill_script` script timeout = `config.harness.command_timeout_seconds` (default
  300) capped by remaining per-task time
  (`AdkSandboxCodeExecutor.execute_code`, `adk_eval_core/sandbox/base.py:195-215`).
- `run_command` (the other tool) caps stdout/stderr at 5,000 chars
  (`swegemma/tools/execution.py`, `max_stdout_chars=5000` in `swegemma/budget.py:29`).
  `run_skill_script` is **not** truncated by the harness, so `swe.py` self-caps output to
  3,500 chars (`swe.py:OUT_CAP`).
- `verify` runs pytest with a 45 s subprocess timeout (`_verify.py:_run_pytest`).
- `locate` uses a 20 s cooperative budget + 25 s hard watchdog (`_guard.run(budget+5)`).
- Tool-call budget: 28 calls / 8 min / 80 turns (bundle `eval_config.yaml`).

## e. How `agent.yaml` wires `SkillToolset`

`agent.yaml` declares:

```yaml
skills:
  - skills/swe-toolkit
```

`adk_submission` compiles this via `resolve_skills`
(`adk_submission/resolvers/tools.py:129-263`):
- validates the skill path stays inside the submission root (no traversal/symlinks);
- loads the skill with `google.adk.skills.load_skill_from_dir`;
- enforces skill count (max_skills) and size (max_skill_size_bytes) limits;
- builds `SkillToolset(skills=[...], code_executor=ctx.code_executor,
  script_timeout=ctx.script_timeout, additional_tools=<resolved tools>)`.

The skill's `name` in `SKILL.md` frontmatter must equal the `skill_name` argument used
at call time (`"swe-toolkit"`). The `RunSkillScriptTool` declaration requires
`skill_name` and `file_path`; `args` may be a dict (converted to `--key value`) or a
list of strings (`skill_toolset.py:724-775`).

## Integration test result

Real `google.adk.tools.skill_toolset.SkillToolset` + `RunSkillScriptTool`, local executor
mirroring `AdkSandboxCodeExecutor`, fixture git repo at `/workspace`:

1. Cold `run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py",
   args=["locate","--issue",...])` → `STATUS: OK`, ranks `src/widget.py` first.
2. Second call emits `[SESSION STATE]` header (state persisted in `/tmp`).
3. `verify` with an injected `SyntaxError` → `STATUS: FAIL`/`SYNTAX: FAIL`, returned in
   0.4 s (<= 45 s).
4. Dict-style args (`args={"issue": ...}`) and malformed args (`args="..."`) handled
   without crashing (dict → OK; malformed → `INVALID_ARGUMENTS`).
5. Tool declarations and `SKILL.md` saved as evidence:
   `/tmp/scratchpad/tool_declarations.json`, `/tmp/scratchpad/system_instruction.txt`.

Evidence files: `/tmp/scratchpad/tool_declarations.json`,
`/tmp/scratchpad/system_instruction.txt`, `/tmp/scratchpad/bundle_system.md`.

## Conclusion

The toolkit's mechanics are sound: scripts run in the task container with access to
`/workspace`, `/tmp` persists across calls, output is self-capped, and verify catches
syntax errors fast. Validation passed — proceeding to gates.
PYEOF
echo written
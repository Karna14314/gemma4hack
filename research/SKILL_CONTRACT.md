# SKILL CONTRACT — VERIFIED against adk_submission 0.2.13 (wheel downloaded 2026-10-30)

## Source provenance (VERIFIED)
- Wheel: `adk_submission-0.2.13-py3-none-any.whl` from Kaggle dataset `metric/gemma-4-developer-agent-wheelhouse`.
- File `adk_submission/resolvers/generation.py` lines 440-448: thinking config binding (quoted below).
- File `adk_submission/resolvers/tools.py` `resolve_skills` (lines ~144-260): skills -> SkillToolset.
- File `adk_submission/discovery.py` `discover_skills` (lines ~562-656): scan for SKILL.md.
- File `adk_submission/schema.py` line 288: `skills: list[str] | None`.
- File `adk_submission/limits.py`: max_skills=1000, max_skill_size_bytes=50 MiB.

## How `skills:` is bound (VERIFIED)
- In agent.yaml, `skills:` is a list of relative paths to skill directories within the submission archive (schema.py:288).
- At compile time, `resolve_skills` (tools.py) validates each path via `validate_sandboxed_path(base_dir=ctx.root_dir, allow_relative=True, must_exist=True, allow_symlinks=False)`.
- If `ctx.skill_registry` is set (pre-discovered), it looks up by name; otherwise loads from disk via `google.adk.skills.load_skill_from_dir(skill_path)`.
- The resolved tools (run_command etc.) are passed as `additional_tools` to the SkillToolset constructor.
- Skill instructions length counts against the instruction-length limit via `ctx.check_instruction_length`.

## Exact tool names/args (VERIFIED)
- Tool registration is by string name resolved through `resolve_tool_item` (registry). SkillToolset exposes the skill's own tools plus `additional_tools`.
- Skill directory must contain `SKILL.md`. Tool names/args are defined by ADK's `load_skill_from_dir` (google.adk.skills), not by this repo. UNKNOWN exact arg schema beyond ADK's standard.

## Where `skills/` is mounted at runtime (VERIFIED)
- Skills are discovered by scanning the entire submission tree for `SKILL.md` (discovery.py: discover_skills). They need not live under `skills/`; any directory with SKILL.md qualifies.
- When referenced by relative path in agent.yaml `skills:`, the path is resolved against `ctx.root_dir` (the unpacked submission root). Convention is `skills/<name>/SKILL.md`, but not enforced by path; only by SKILL.md presence.
- Skill size limit: 50 MiB per skill directory (limits.py max_skill_size_bytes). Total skill count limit: 1000 (max_skills).

## Thinking config binding (VERIFIED, generation.py:440-448)
```
if (enable_thinking and thinking_budget is not None and not isinstance(thinking_budget, bool) and int(thinking_budget) > 0):
    extra_body["thinking_token_budget"] = int(thinking_budget)
else:
    extra_body.pop("thinking_token_budget", None)
```
And `include_thoughts: false` hard-disables thinking (emits enable_thinking=false, removes thinking_token_budget). Confirmed.

## UNKNOWN
- Exact SKILL.md frontmatter schema and tool argument types (defined in google.adk.skills, not in adk_submission). Not verified here.
- Whether skills execute Python scripts at runtime (ADK skill tooling). UNKNOWN.
- Whether the scorer passes a skill_registry or loads from disk (ctx.skill_registry may be None in scoring). UNKNOWN but disk path is the fallback.

## Smallest probe bundle (NOT submitted)
- A minimal bundle = exp05-style agent.yaml + `skills: [skills/hello]` + `skills/hello/SKILL.md` with one trivial instruction. Purpose: confirm skills load and skill tools appear. Do NOT submit today (per task authorization).

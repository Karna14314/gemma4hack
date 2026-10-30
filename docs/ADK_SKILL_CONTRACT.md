# ADK Skill Contract

## Dedicated tools
- `list_skills`
- `load_skill`
- `load_skill_resource`
- `run_skill_script`

## Skill layout
- Skill directories use strict kebab-case (for example `skills/swe-toolkit/`).
- The directory name must match the `name` field in `SKILL.md` front matter.
- `SKILL.md` must contain YAML front matter with `name: <skill-name>`.

## Patch pollution risk
- `run_skill_script` materializes skill files into `/workspace/skills/...`.
- The harness builds the submission patch with `git add -N . && git diff _swegemma_baseline`.
- Materialized skill files can pollute the patch and corrupt evaluation.

## Mandatory mitigation
- Remove materialized skill files before submit: `rm -rf skills/`.
- Verify with `git status --short` that no skill files remain in the patch.

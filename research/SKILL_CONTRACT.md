# SKILL CONTRACT (research/SKILL_CONTRACT.md)

Source inspected: ckpt/HARNESS_README.md §§2.2,2.3,2.4; local search for adk-submission/swegemma source returned no wheels or source in this container.

## Known from HARNESS_README
- Skills are optional directories under `skills/<name>/`, each containing `SKILL.md` with YAML front matter whose `name:` equals directory name. [VERIFIED ckpt/HARNESS_README.md §2.2]
- `agent.yaml` field `skills: list[str]` = relative paths to skill directories. [VERIFIED §2.3]
- Limits: max_skill_size_bytes 50 MiB per skill dir; max_skills 1000. [VERIFIED §2.4]
- Allowed extensions include .py (ADK skill scripts), .md, .txt, .json etc. [VERIFIED §2.4]
- Compile model is declarative; no arbitrary Python entrypoints. [VERIFIED §2.1]

## Unknown
- Exact exposed tool names for skills (`load_skill`, `run_skill_script`, `load_skill_resource`) and parameters: UNKNOWN (no adk-submission source in container). Settle by inspecting adk-submission source or running a minimal skill bundle on Kaggle.
- Whether `run_skill_script` can be called on Call 1 without `load_skill`: UNKNOWN.
- cwd/environment/path of `run_skill_script`: UNKNOWN.
- Output truncation cap on skill script and whether skill calls count toward max_tool_calls: UNKNOWN.

# SESSION FINAL — exp13 clean baseline (2026-10-30)

## 1. ADK skill binding contract
`adk_submission/resolvers/generation.py:440-465` covers thinking-config handling, not skill binding. Skill binding is implemented by `google.adk.tools.skill_toolset.SkillToolset`, compiled via `adk_submission.compiler`. Exposed tools: `list_skills`, `search_skills`, `load_skill`, `load_skill_resource`, `run_skill_script`. `run_skill_script` args: `skill_name` (required), `file_path` (required, e.g. `scripts/swe.py`), optional `args` (object or list of strings), `short_options`, `positional_args`. Scripts are materialized into a temp directory and executed with cwd=that temp dir; access to /workspace requires passing `--root /workspace`. Skill frontmatter `name` must match directory (kebab-case).

## 2. Clean status of bundles/exp13/
`bundles/exp13/agent.yaml` has no `skills:` directive; `prompts/system.md` has no TOOLKIT block. `kernel_wheel_inspect/` removed. `verify_bundle.py --bundle bundles/exp13` exits 0 (ALL CHECKS PASSED).

## 3. Inline patch-gate one-liner
python3 -c "import base64; exec(base64.b64decode('aW1wb3J0IGFzdCxzdWJwcm9jZXNzCmM9W3ggZm9yIHggaW4gc3VicHJvY2Vzcy5jaGVja19vdXRwdXQoWyJnaXQiLCJkaWZmIiwiLS1uYW1lLW9ubHkiLCJfc3dlZ2VtbWFfYmFzZWxpbmUiXSx0ZXh0PVRydWUpLnNwbGl0KCkgaWYgeF0KdT1beCBmb3IgeCBpbiBzdWJwcm9jZXNzLmNoZWNrX291dHB1dChbImdpdCIsInN0YXR1cyIsIi0tcG9yY2VsYWluIl0sdGV4dD1UcnVlKS5zcGxpdGxpbmVzKCkgaWYgeC5zdGFydHN3aXRoKCI/PyIpXQplPVtdCmZvciBmIGluIGM6CiAgICBpZiBmLmVuZHN3aXRoKCIucHkiKToKICAgICAgICB0cnk6IGFzdC5wYXJzZShvcGVuKGYpLnJlYWQoKSkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGV4OiBlLmFwcGVuZCgiU1lOVEFYICIrZisiOiAiK3N0cihleCkpCiAgICBpZiAoZi5zdGFydHN3aXRoKCJ0ZXN0cy8iKSBvciBmLnN0YXJ0c3dpdGgoInRlc3QvIikgb3IgIi90ZXN0cy8iIGluIGYgb3IgZi5lbmRzd2l0aCgiY29uZnRlc3QucHkiKSBvciBmLmVuZHN3aXRoKCJweXByb2plY3QudG9tbCIpIG9yIGYuc3BsaXQoIi8iKVstMV0uc3RhcnRzd2l0aCgidGVzdF8iKSBvciBmLnNwbGl0KCIvIilbLTFdLmVuZHN3aXRoKCJfdGVzdC5weSIpKToKICAgICAgICBlLmFwcGVuZCgiUFJPVEVDVEVEICIrZikKaWYgdTogZS5hcHBlbmQoIlVOVFJBQ0tFRCAiKyIsICIuam9pbih1KSkKcHJpbnQoIlBBVENIX0dBVEU6IFBBU1NFRCIgaWYgbm90IGUgZWxzZSAiUEFUQ0hfR0FURTogRkFJTEVEICIrIjsgIi5qb2luKGUpKQo=').decode())"

## 4. Next actions for pending e4b-v2 evaluation
Poll submission ref 57806053. If score >=0.10, rerun to confirm; 0.07-0.09 inconclusive; <=0.06 ablate temperature vs prompt. Continue paper-track draft by Nov 12.

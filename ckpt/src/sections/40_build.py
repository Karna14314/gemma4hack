"""Section 40 — the primary agent package as inlined literals.

The whole of ``src/agent_package/`` is read at build time and rendered into a
single ``PACKAGE_FILES`` assignment. The builder walks the directory, so adding a
file to ``src/agent_package/`` and rebuilding is the only way to change what ships
— there is no second copy of the package to forget about.
"""

INTRO = '''\
## Primary package

The full agent package, inlined as a string mapping. This directory is the single
source of truth in the repository:

```
agent.yaml                  root coder agent: tools + the analyzer sub-agent
eval_config.yaml            the 12 hour compute budget, allocated per task
configs/sampling.yaml       generation config shared by both agents
prompts/system.md           the coder's instructions
prompts/analyzer.md         the sub-agent's instructions
sub_agents/code_analyzer.yaml   read-only navigator
```
'''

PACKAGE_SPLICE = "#<<<SPLICE_DIR_LITERAL:src/agent_package:PACKAGE_FILES>>>"

SUMMARY = '''\
# What the primary package contains, and its total size.
print("primary files:", len(PACKAGE_FILES))
for _path in sorted(PACKAGE_FILES):
    print(f"  {len(PACKAGE_FILES[_path].encode('utf-8')):>8,d} B  {_path}")
print(f"  {sum(len(v.encode('utf-8')) for v in PACKAGE_FILES.values()):>8,d} B  TOTAL")
print()
print("fallback files:", len(FALLBACK_FILES))
for _path in sorted(FALLBACK_FILES):
    print(f"  {len(FALLBACK_FILES[_path].encode('utf-8')):>8,d} B  {_path}")
'''


def cells() -> list[dict]:
    return [
        {"cell_type": "markdown", "source": INTRO},
        {"cell_type": "code", "source": PACKAGE_SPLICE},
        {"cell_type": "code", "source": SUMMARY},
    ]
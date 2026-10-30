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
agent.yaml                  root agent: the 9 harness tools, no sub-agents
eval_config.yaml            the 12 hour compute budget, allocated per task
configs/sampling.yaml       generation config (thinking on, 8192 output tokens)
prompts/system.md           the agent's instructions
```

This is the byte-exact public 0.17 baseline bundle (SuperAgent), which is also
the 0.18 Budget-Fit configuration. Ablation bundles live under
`kaggle_work/gemma-4-developer-agent/bundles/` and are built into their own
notebooks with `tools/build_notebook.py --bundle ...`.
'''

PACKAGE_SPLICE = "#<<<SPLICE_DIR_LITERAL:src/agent_package:PACKAGE_FILES>>>"

SUMMARY = '''\
# What the primary package contains, and its total size.
print("primary files:", len(PACKAGE_FILES))
for _path in sorted(PACKAGE_FILES):
    print(f"  {len(PACKAGE_FILES[_path].encode('utf-8')):>8,d} B  {_path}")
print(f"  {sum(len(v.encode('utf-8')) for v in PACKAGE_FILES.values()):>8,d} B  TOTAL")
print()
'''


def cells() -> list[dict]:
    return [
        {"cell_type": "markdown", "source": INTRO},
        {"cell_type": "code", "source": PACKAGE_SPLICE},
        {"cell_type": "code", "source": SUMMARY},
    ]
"""Section 00 — title and overview markdown for the submission notebook.

Cells here are prose only. They explain to a human reader exactly what is being
packaged and why, so that the notebook can be reviewed without reading YAML.
"""

TITLE = """\
# gemma-4-developer-agent — submission builder

This notebook builds **`/kaggle/working/submission.zip`**, a declarative Google ADK
agent package. The organizers compile it with `adk-submission` and run the resulting
agent on hidden SWE-bench-style tasks with a single permitted model,
`gemma-4-31b-it-qat-w4a16-ct`, on 4x L4 GPUs.

**What the notebook does, and nothing else:**

1. Holds the agent package as in-memory Python string literals.
2. Validates it against every submission constraint the harness enforces.
3. Writes a deterministic zip with `agent.yaml` at the archive root.

**What it deliberately does not do:** no `pip install`, no downloads, no dataset
inputs, no GPU, no network. The only dependencies are the Python standard library
and `PyYAML`, both of which are already present on Kaggle. Every byte it needs is
written inline in the cells below, so the notebook cannot drift from the package
it is supposed to emit.

## Safety design

A notebook that raises an exception scores **zero**, so the build is written as if
it will fail:

- The primary package is validated. If any single check fails, the notebook falls
  back to a **minimal known-good package** (one agent, no sub-agent, short prompt)
  that is designed to have the fewest possible ways to fail on the scorer's machine.
- If even the packaging step fails, a final cell writes an emergency minimal archive
  directly, bypassing the shared packager.
- The last cell asserts the artifact exists and is a readable zip.

## Contents

| Section | Purpose |
|---|---|
| Setup | import the standard library, resolve the working directory |
| Design rationale | why each load-bearing choice is made |
| Library | the static validator and the fallback package |
| Primary package | the agent YAML, prompts and sampling config |
| Validate | run the checks, choose primary or fallback |
| Package | write the zip and a manifest, print a report |
"""

RUN_NOTE = """\
> **Note.** The agent package itself is what scores; this notebook is only the
> mechanism that delivers it. The interesting content is in `prompts/system.md`
> and `sub_agents/code_analyzer.yaml`, reproduced verbatim in the cells below.
"""


def cells() -> list[dict]:
    return [
        {"cell_type": "markdown", "source": TITLE},
        {"cell_type": "markdown", "source": RUN_NOTE},
    ]
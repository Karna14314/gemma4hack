# CONFIG — gemma-4-developer-agent

```
COMPETITION_SLUG:     gemma-4-developer-agent
USERNAME:             narisettichaitanya
COMPETITION_TYPE:     code-competition (agent package, submitted as a Kaggle notebook)
PRIMARY_METRIC:       Resolution Rate = resolved_tasks / total_tasks, in [0, 1], higher_is_better: true
BASELINE:             none submitted yet by us. Public LB: top = 0.24, cluster = 0.15-0.17,
                      published starter-kit-based agents = 0.10-0.12, unmodified starter kit = ERROR
LB_OR_CV:             public leaderboard only (no local reproduction possible: needs 4x L4)
DEADLINE:             2026-12-02 23:59:00 UTC (verify on the competition page)
SUBMISSIONS_PER_DAY:  1
INTERNET_IN_NOTEBOOKS:off
GPU_QUOTA_NOTE:       notebook itself is CPU-only; scoring rerun happens on the organizers' 4x L4 box
WAIT_MAX_MIN:         25
EXTRA_DATASETS:       none required (metric/gemma-4-developer-agent-wheelhouse used only for
                      OFFLINE local validation on this machine, not attached to the notebook)
```

## Task, in one paragraph

We submit a **declarative Google ADK agent package** (`submission.zip`, files only, `agent.yaml`
at the archive root, < 3 GiB unpacked, allowed extensions only). The organizers compile it with
`adk-submission`, serve the single permitted model `gemma-4-31b-it-qat-w4a16-ct` on 4x L4 with
vLLM (`max_model_len=32768`), and run the agent on ~120 hidden SWE-bench-style tasks drawn from
repositories that are **not** in the public data. Each task gets a `/workspace` git checkout at the
base commit, offline. Phase 1: the agent edits source with 9 sandboxed tools. Phase 2: a fresh
container applies `git diff` + the hidden `test_patch` and runs `pytest`; a task scores 1.0 iff
pytest exits 0 and the JUnit XML is valid with `passed>0, failures=0, errors=0` and no skipped
required node. Score = fraction resolved.

## Hard operational constraints (decisive for the design)

| Constraint | Value | Source | Design consequence |
|---|---|---|---|
| Total scoring compute | **12 h for all ~120 tasks**, sequential, incl. vLLM startup + sandbox setup + verification | walkthrough notebook, hosts confirmed | per-task agent budget must average ≲ 4-5 min. `max_time_minutes: 12` → *Notebook Exceeded Allowed Compute* |
| LoRA adapter present | harness starts vLLM with 8 LoRA slots @ r128 → **KV cache 46k → 7.6k tokens** | forum 744331 | **ship zero adapters.** Biggest single structural decision |
| `search_similar_code` | costs a tool call and returns at most `max_stdout_chars` = 5,000 chars of code **shared across all ten results**, each head-truncated mid-line; ranking is imprecise. **Not** a context-overflow risk — verified in `swegemma/tools/graph.py:260-277` | harness source audit | tool stays declared but prompt **forbids calling it**: a wasted tool call for worse results than `git grep` |
| `run_command` | keeps the **FIRST** 5 000 chars of stdout *and* stderr; pytest prints its verdict at the **end** | `swegemma/tools/execution.py:54-56` | prompt mandates `> /tmp/x.log 2>&1; tail -n 30 /tmp/x.log` |
| `read_file` | 150 lines first, then 10 000 chars — so a 150-line window can be clipped mid-line with no warning | `swegemma/tools/workspace.py:151-163` | prompt mandates tight line ranges |
| `edit_file` returned diff | capped at 5 000 chars (not 10 000) | `swegemma/tools/workspace.py:276-281` | keep edits small |
| File tools | reject any path outside `/workspace`; `write_file('/tmp/x')` fails | `swegemma/harness/agent_runner.py` + `tools/workspace.py` | scratch files must be created by `run_command` heredocs into `/tmp` |
| Context | no client-side preflight exists; exceeding `32768 - max_output_tokens` returns a non-retryable HTTP 400 from vLLM, which escapes as an uncaught exception and **discards an already-submitted patch** | `agent_runner.py:799-801`, `adk_eval_core/plugins/retry_plugin.py:54-117` | `max_output_tokens: 8192` leaves ~24.5k of prompt room; compaction is active in scoring at `token_threshold=14336` (README §7.2) |
| Compaction | the CLI path leaves `events_compaction_config=None`, but the scoring `inference.py` sets `compaction_interval=5, overlap_size=2, token_threshold=14336, event_retention_size=5`. Only the model's own text survives compaction | README §7.2 + getting-started notebook cell 10 | prompt mandates a plain-text **state card** after localisation and after each verification |
| `timeout_seconds` | maps to `config.harness.command_timeout_seconds`, which bounds **both** the agent's commands **and the Phase 2 pytest run** (`verification.py:502`). Default 300 | `swegemma/config.py:179-183`, `harness/verification.py:502` | **keep at 300.** Lowering it risks timing out verification of an already-correct patch — a far worse failure than a slow agent |
| Protected paths | reset to baseline before `test_patch`: `conftest.py`, `pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`, `.pytest.ini`, `sitecustomize.py`, `usercustomize.py`, `_swegemma_stubs.py`, `*.pth`, `test_*.py`, `*_test.py`, and **any `.py` under a `tests`/`test`/`testing` directory** | `harness/verification.py:60-83` | prompt forbids touching them. Note `pyproject.toml` is protected, so config-only tasks are unwinnable by design |
| Repo `.gitignore` | `git add -N .` respects it, so a new file on an ignored path **silently never reaches the patch** | `agent_runner.py:763`, `container_setup.py:498-503` | prompt mandates checking `git status --short` and forcing with `git add -N -f <path>` |
| Untracked files in `/workspace` | included in the patch by `git add -N .`; `/tmp` files are not | `tools/execution.py:86-89`, `agent_runner.py:760-796` | prompt mandates a `git status --short` cleanup before submit |
| `submit_patch` never called | harness still runs `git add -N . && git diff --binary _swegemma_baseline` and grades the working tree | `agent_runner.py:760-776` | never revert a plausible fix; a best-effort patch beats no patch |
| Nudges | `max_nudges = 3` **consecutive**; a turn containing any tool call resets the counter. The 4th nudge-free turn ends the task | `agent_runner.py:499, 677-686` | prompt mandates `get_status()` checks and an explicit submit |
| `skip_summarization: true` | sets `actions.skip_summarization`, making the sub-agent's function-response event *final*, so the parent's flow loop breaks and the harness immediately nudges | `google/adk/tools/agent_tool.py:212-213`, `events/event.py:91-92` | use `skip_summarization: false` |
| Sub-agent turn accounting | sub-agent LLM calls **do** count against the parent's `llm_calls_used`; `budget.turns` defaults to `None`, which means a hard-coded 500 | `swegemma/context.py:276-298`, `agent_runner.py:429-431` | `max_turns: 120` leaves room for analyzer turns |
| Allowed extensions | `.yaml .yml .md .txt .py .json .safetensors` — the competition override **omits the empty suffix**, so `LICENSE`, `Makefile`, `Dockerfile` and `.gitignore` would abort the submission | `swegemma/config.py:20-30`, `adk_submission/discovery.py:122-127` | bundle contains only `.yaml` and `.md` |
| `!include` | supports `.md`, `.txt`, `.yaml`, `.yml` only, max nesting 10, and the tag is consumed by the loader so an included value arrives as a bare path string | `adk_submission/yaml_loader.py:24-28` | validator resolves and parses includes explicitly |
| `.py` in the zip | allowed by extension but **never imported or executed** by the compiler | `adk_submission/compiler.py:1-9` | ship none |
| Callbacks | `callback_registry` is never passed, so `before_model_callbacks:` etc. are accepted by the schema and **silently dropped** | `agent_runner.py:334-346`, `adk_submission/resolvers/callbacks.py:84-85` | do not use callbacks |
| `include_thoughts: false` | genuinely hard-disables thinking: emits `chat_template_kwargs.enable_thinking=false` and actively **removes** `thinking_token_budget` and `reasoning_effort`. The harness default merges `thinking_budget: 4096` underneath, but `include_thoughts is False` is checked first and wins | `adk_submission/resolvers/generation.py:291-345`, `limits.py:401-407` | thinking off, as in every published scoring run |
| Tool registry | all **nine** tools are registered unconditionally on every task, graph data or not (`swegemma/tools/__init__.py:34-46`); an **unknown tool name raises `ToolNotFoundError`**, which is fatal for every task | `adk_submission/registry.py:72-75` | declaring the graph tools is safe; declaring anything else is not |
| Single base model | `validate_single_declared_model` raises `ParticipantVisibleError` for zero or >1 model. It is **not** called per task; it runs at submission-ingest time. There is no `ALLOWED_MODEL_NAMES` constant in the wheel — the scorer enforces the single-model rule, and per-task it is registry membership that matters | `swegemma/models/discovery.py:93-121` | every agent declares exactly `gemma-4-31b-it-qat-w4a16-ct` |
| Graph/embedding data | shipped only for the 4 public repos; hidden tasks are other repos, so the prompt's "Code Intelligence Tools" section is **omitted** for them. The tools still exist and just error | `agent_runner.py:144-181` | prompt calls them weak hints and never names `search_similar_code` as usable |
| `edge_type` filter | data only has lowercase `calls`; the README's `CALLS` matches nothing | graph audit | prompt forbids passing `edge_type` |
| Sandbox tooling | `git`, `grep`, `find`, `sed`, `awk`, `head`, `tail`, `wc`, `sort`, `cut`, `python3` present; **`rg`/`tree`/`jq` absent** | walkthrough | prompt names the available binaries explicitly |
| Public LB granularity | ~half of ~120 tasks → 1 task ≈ 0.017 | walkthrough | differences below ~0.05 are noise; do not over-fit to LB deltas |

### Uncertainties that remain

| Item | Why unresolved |
|---|---|
| Whether `eval_config.yaml` is read during scoring | `load_submission_eval_config` does not exist in any shipped wheel; the consumer is the unshipped `scripts/inference.py`. README §2.2/§7.1 and the getting-started notebook both show it being read, so it is shipped deliberately |
| Whether the repo's own `.gitignore` is stripped before the agent runs | no overriding code found; assumed honoured, hence the `git add -N -f` instruction |
| Whether the organiser passes `--reasoning-parser gemma4` | `VllmConfig.reasoning_parser` defaults to `None` in `adk_submission/server.py:146`; the spawning call is external |
| Exact `EvalConfig` the scoring run builds | the CLI defaults are known but the metric notebook may construct it programmatically |

## Environment facts

- Kaggle CLI 2.2.4, authenticated as `narisettichaitanya` (legacy key via `~/.kaggle/kaggle.json`;
  `KAGGLE_USERNAME`/`KAGGLE_KEY` are **not** exported in this PowerShell session).
- Local Python 3.13.14, `nbformat` available, `pyyaml` available.
- Real harness wheels (`swegemma` 0.2.7, `adk_submission` 0.2.12, `adk_eval_core` 0.1.0,
  `google-adk` 1.36.1) downloaded to `kaggle_work/gemma-4-developer-agent/research/wheelhouse/`
  and extracted to `.harness/` for **offline source inspection and local schema validation**.

## Noisy quantities — do not treat as signal

Resolution rate on ~60 public-LB tasks has a 1-task granularity of ~0.017, and model sampling is
stochastic (`seed` is not forwarded to vLLM). Any single submission difference below ~0.05 is
inside run-to-run noise. The 12 h budget also makes the agent's behaviour time-dependent, so two
runs of the *same* package can differ. Consequence: prefer design choices justified by a mechanism
in the harness source over choices justified by a small LB delta.

# Dev-Set Evaluation Mechanics (Kaggle L4x4)

## Official starter notebook
- Slug: `ryanholbrook/getting-started-gemma-4-developer-agent`
- Pulled to `/tmp/kilo/starter/getting-started-gemma-4-developer-agent.ipynb` (13 cells).
- Machine shape: `NvidiaL4` (4x L4 GPUs), offline (`enable_internet: false`), competition source `gemma-4-developer-agent`, model source `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2`.

## Offline wheel install
- Wheelhouse dataset: `/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse` (symlinked into `/tmp/wheelhouse` with `+cu128` restored in filenames).
- Competition also ships wheels at `/kaggle/input/competitions/gemma-4-developer-agent/wheels` (used as `--find-links` fallback).
- Install: `pip install --no-deps --force-reinstall /tmp/wheelhouse/*.whl` (or `pip install --no-index --find-links <dir> swegemma adk_submission adk-eval-core`).

## Model input
- Path: `/kaggle/input/models/google/gemma-4/other/<declared_model>/2` (e.g. `gemma-4-31b-it-qat-w4a16-ct`).
- Single declared model enforced via `discover_declared_models(AGENT_DIR)`.

## vLLM server
- `VllmConfig`: `max_model_len=32768`, `tensor_parallel_size=4` (when >=4 GPUs), `tool_call_parser='gemma4'`, `reasoning_parser='gemma4'`, `enable_auto_tool_choice=True`, `gpu_memory_utilization=0.90`, `dtype=bfloat16`, `port=8000`.
- TP=4 on 4x L4.

## Phase 1 + Phase 2 in-notebook
- `swegemma.evaluate.Evaluator` with `sandbox='subprocess'` runs Phase 1 (agent patch generation) and Phase 2 (pytest grading) per task via `evaluator.evaluate_task(task=..., task_index=..., total_tasks=...)`.
- Result fields used: `agent_patch`, `resolved`, `test_exit_code`, `tool_calls`, `duration_seconds`.
- Tasks loaded from `/kaggle/input/competitions/gemma-4-developer-agent/tasks.jsonl` (129 public tasks).
- Snapshots: `/kaggle/input/competitions/gemma-4-developer-agent/snapshots`.
- Graphs/embeddings: `/kaggle/input/competitions/gemma-4-developer-agent/{graphs,embeddings}`.

## Compaction / context
- ADK `EventsCompactionConfig`: `token_threshold=14336`, `compaction_interval=15`, `overlap_size=2`, `event_retention_size=5`.
- vLLM overflow when `prompt + max_output > 32768`.

## Dev-set kernel
- Slug: `narisettichaitanya/g4-paired-devset-eval` (version 4, status RUNNING at handoff).
- Evaluates `exp05` (baseline) and `exp10-consolidated` head-to-head on 24 stratified tasks.
- Telemetry flushed to `/kaggle/working/smoke_test_results.json`, `/kaggle/working/paired_eval_results.json`, `/kaggle/working/paired_eval_summary.md`.

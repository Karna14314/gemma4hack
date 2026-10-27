# SESSION_FINAL

Branch: feat/devset-gpu-eval-harness
PR: (draft to be opened)

## Summary
- Paired dev-set GPU eval kernel built and launched: `narisettichaitanya/g4-paired-devset-eval` v4, status RUNNING at handoff.
- 24-task stratified benchmark saved in `research/kernel_devset_eval/eval_24_tasks.json`.
- Official harness evaluation mechanics documented in `research/DEVSET_EVAL_MECHANICS.md`.
- exp10-consolidated (ref 57654236) status PENDING; submission quota blocked, exp11_e4b deferred.

## Verification
- `python3 -m py_compile research/kernel_devset_eval/paired_devset_eval.py`: PASS
- kernel-metadata.json: valid (GPU, offline, competition + model sources)
- 31B checks (`verify_bundle.py`, `verify_notebook.py`) and E4B checks (`tracks/e4b_small/verify_bundle_e4b.py`, `tracks/e4b_small/verify_notebook_e4b.py`): not re-run this session; bundles unchanged (exp05, exp10-consolidated verified previously).

## Kernel status
- slug: narisettichaitanya/g4-paired-devset-eval
- version: 4
- status: RUNNING (at handoff)
- outputs: `/kaggle/working/smoke_test_results.json`, `/kaggle/working/paired_eval_results.json`, `/kaggle/working/paired_eval_summary.md`

## Submission status
- exp10-consolidated ref 57654236: PENDING (not scored)
- exp05 ref 57553805: COMPLETE 0.20
- exp08 ref 57618114: COMPLETE 0.17

## Numerical tables (from research/PAPER_EXPERIMENTS.md, commit ba523ac)

### Experiment 1 — Code-Graph & Embedding Localization (129 tasks)

| strategy | R@1 | R@3 | R@5 | R@10 |
|---|---:|---:|---:|---:|
| lexical | 0.0018 | 0.0045 | 0.0045 | 0.0058 |
| graph | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| hybrid | 0.0018 | 0.0045 | 0.0045 | 0.0045 |

Tasks evaluated: 129

### Experiment 2 — Harness & Context Budget Bottleneck

| bundle | tools | max_output_tokens | prompt chars |
|---|---:|---:|---:|
| exp05 | 9 | 8192 | 5425 |
| exp10-consolidated | 6 | 6144 | 5575 |

- .gitignore empty-patch: exp03 0.17 -> exp05 0.20 (+0.03).
- Prompt bloat: exp05 0.20 -> exp08 0.17 (-0.03).
- vLLM headroom: 24576 (exp05) vs 26624 (exp10).
- ADK compaction threshold: 14336.

### Binomial SE
- sqrt(p*(1-p)/58); for p=0.20: 0.0524 (~3 tasks).
## Dev-set kernel status (latest)
- slug: narisettichaitanya/g4-paired-devset-eval
- latest version: 45
- status: ERROR (environment blocker)
- blocker: byod image Python 3.12 lacks torch/pydantic; Python 3.13 has torch 2.11.0 but vLLM 0.19.1 abi3 wheel is ABI-incompatible (undefined symbol c10::MessageLogger). Wheelhouse has no torch/pydantic wheels. Kernel cannot start vLLM in current image.
- next: use a byod image with torch compatible with vLLM 0.19.1, or run vLLM via a separate compatible runtime.

## Dev-set kernel status (final, v47+)
- slug: narisettichaitanya/g4-paired-devset-eval
- status: ERROR (environment blocker persists)
- helper kernel: narisettichaitanya/g4-torch-wheel-cache (v7, COMPLETE) downloaded 89 wheels but did NOT include torch/vllm (pip download from cu128 index failed).
- blocker: byod image Python 3.12 lacks torch/pydantic; Python 3.13 has torch 2.11.0 but vLLM 0.19.1 requires torch==2.10.0. Wheelhouse has no torch/pydantic wheels. Cannot start vLLM.
- next: provide a byod image with torch 2.10.0 compatible with vLLM 0.19.1, or pre-cache compatible wheels in a dataset.

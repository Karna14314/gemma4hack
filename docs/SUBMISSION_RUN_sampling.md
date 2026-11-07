# Submission run: sampling (temp 1.0, top_p 0.95, top_k 64)

Bundle: kaggle_work/gemma-4-developer-agent/bundles/exp_sampling_temp1
Experiment dir: kaggle_work/gemma-4-developer-agent/experiments/exp_sampling_temp1
Base: ckpt/bundles/exp05_patch_integrity (frozen exp05 bundle; scored artifact ckpt/exp05/submission.zip sha256 2ba7f9b118ea1837d1950038894cc856d1d33fe98c333d216afe6aaac1661774)
Single change: configs/sampling.yaml temperature 0.2 -> 1.0, added top_k 64 (top_p unchanged 0.95); thinking_config unchanged.

Hypothesis: low temperature (0.2) vs Gemma 4 model-card recommendation (1.0) causes loops/poor exploration; raising to 1.0 + top_p 0.95 + top_k 64 improves pass rate.
Pre-registered rule vs 31B pool (mean ~10.3 tasks, SD <1): >=13 tasks (0.22) real; 9-12 null; <=8 regression.

## Verification
- verify_bundle.py --bundle ... : ALL CHECKS PASSED
- build_notebook.py --bundle ... --out ... : OK (17 cells)
- verify_notebook.py --notebook ... : ALL CHECKS PASSED
- Single 31B model: gemma-4-31b-it-qat-w4a16-ct

## Git
Branch: kilo/starry-blossom-vb1

## Resume commands
- Push kernel: kaggle kernels push -p kaggle_work/gemma-4-developer-agent/experiments/exp_sampling_temp1
- Check status: kaggle kernels status <owner>/<slug> (confirm slug via kaggle kernels list --mine)
- Pull output: kaggle kernels output <owner>/<slug> -p kaggle_work/gemma-4-developer-agent/runs/exp_sampling_temp1
- Submit (only after explicit yes): kaggle competitions submit -c gemma-4-developer-agent -k <owner>/<slug> -v <version> -f submission.zip -m "exp_sampling: temp 1.0 top_p .95 top_k 64 off exp05"

## Status
Submitted. Ref 58096981, PENDING (polled once 2026-11-07T15:37Z). Gate 4 passed: kernel COMPLETE, no traceback, sha matches.

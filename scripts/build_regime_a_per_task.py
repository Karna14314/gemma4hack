#!/usr/bin/env python3
"""build_regime_a_per_task.py — Generate 2x2 Decomposition Matrix and genuine metrics.

CRITICAL INTEGRITY DIRECTIVE:
Zero synthetic calibration. Uses ONLY genuine measured data:
- Regime A (M4 Static Graph): aggregate measured Mean-Fraction File R@5 = 0.4350 (56.12/129)
  from research/paper_eval_outputs/paper_experiments.json.
- Regime B (v4 Live AST + Test Demotion): measured per-task in eval_results/t6_results_v4_repro.json:
  - Mean-Fraction File R@5 = 0.6184 (79.77/129, paired bootstrap 95% CI [0.5432, 0.6927])
  - Any-Gold File R@5 = 0.7442 (96/129, paired bootstrap 95% CI [0.6667, 0.8140])
  - Pipeline/Index Gain = +18.34 pp (0.6184 - 0.4350)
  - Metric Definition Gap = +12.58 pp (0.7442 - 0.6184, 95% CI [+8.39, +17.03] pp)
"""
from __future__ import annotations

import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = REPO_ROOT / "kaggle_work" / "gemma-4-developer-agent" / "research" / "competition" / "tasks.jsonl"
EXP_JSON_PATH = REPO_ROOT / "research" / "paper_eval_outputs" / "paper_experiments.json"
V4_REPRO_PATH = REPO_ROOT / "eval_results" / "t6_results_v4_repro.json"
OUT_PATH = REPO_ROOT / "research" / "paper_eval_outputs" / "regime_a_per_task.json"


def load_tasks() -> dict[str, dict]:
    tasks = {}
    if TASKS_PATH.exists():
        for line in TASKS_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                t = json.loads(line)
                tasks[t["instance_id"]] = t
    return tasks


def main():
    print("=" * 80)
    print("TASK 1.1: Build Genuine 2x2 Decomposition Matrix (Zero Calibration)")
    print("=" * 80)

    # 1. Load genuine Regime A aggregate measurements
    exp_data = json.load(open(EXP_JSON_PATH, encoding="utf-8"))
    exp1_summary = exp_data["experiment1"]["summary"]
    m4_all = exp1_summary["all"]["M4"]
    regime_a_m4_mean_frac_r5 = m4_all["R@5_file"]  # 0.4350

    # 2. Load genuine Regime B per-task measurements
    v4_repro = json.load(open(V4_REPRO_PATH, encoding="utf-8"))
    n_tasks = len(v4_repro)  # 129
    assert n_tasks == 129, f"Expected 129 tasks, found {n_tasks}"

    # Compute Regime B metrics across @1, @3, @5, @10
    regime_b_metrics = {}
    per_task_records = []

    for k in (1, 3, 5, 10):
        any_hits = []
        frac_hits = []
        diffs = []
        for r in v4_repro:
            gf = set(r.get("gold_files", []))
            top_k = set(r.get("top", [])[:k])
            has_hit = bool(gf & top_k)
            f_hit = len(gf & top_k) / len(gf) if gf else 0.0
            any_hits.append(1.0 if has_hit else 0.0)
            frac_hits.append(f_hit)
            diffs.append((1.0 if has_hit else 0.0) - f_hit)

        any_mean = sum(any_hits) / n_tasks
        frac_mean = sum(frac_hits) / n_tasks
        paired_diff = any_mean - frac_mean

        regime_b_metrics[f"@{k}"] = {
            "any_gold_recall": round(any_mean, 4),
            "any_gold_hits": int(sum(any_hits)),
            "mean_fraction_recall": round(frac_mean, 4),
            "mean_fraction_sum": round(sum(frac_hits), 2),
            "paired_difference_pp": round(paired_diff * 100, 2),
        }

    # Paired Bootstrap 95% CIs for Regime B @5
    random.seed(42)
    b_fracs_5 = []
    b_anys_5 = []
    b_diffs_5 = []
    for r in v4_repro:
        gf = set(r.get("gold_files", []))
        top5 = set(r.get("top", [])[:5])
        f = len(gf & top5) / len(gf) if gf else 0.0
        a = 1.0 if (gf & top5) else 0.0
        b_fracs_5.append(f)
        b_anys_5.append(a)
        b_diffs_5.append(a - f)

    boot_fracs = []
    boot_anys = []
    boot_diffs = []
    for _ in range(10000):
        sample_idx = [random.randrange(n_tasks) for _ in range(n_tasks)]
        boot_fracs.append(sum(b_fracs_5[i] for i in sample_idx) / n_tasks)
        boot_anys.append(sum(b_anys_5[i] for i in sample_idx) / n_tasks)
        boot_diffs.append(sum(b_diffs_5[i] for i in sample_idx) / n_tasks)

    boot_fracs.sort()
    boot_anys.sort()
    boot_diffs.sort()

    ci_frac_r5 = [round(boot_fracs[250], 4), round(boot_fracs[9750], 4)]
    ci_any_r5 = [round(boot_anys[250], 4), round(boot_anys[9750], 4)]
    ci_diff_r5_pp = [round(boot_diffs[250] * 100, 2), round(boot_diffs[9750] * 100, 2)]

    regime_b_mean_frac_r5 = regime_b_metrics["@5"]["mean_fraction_recall"]  # 0.6184
    regime_b_any_gold_r5 = regime_b_metrics["@5"]["any_gold_recall"]        # 0.7442

    # Decomposition steps:
    # 1. Pipeline / Index gain (same metric: Mean-Fraction R@5): 0.6184 - 0.4350 = +18.34 pp
    pipeline_gain_pp = round((regime_b_mean_frac_r5 - regime_a_m4_mean_frac_r5) * 100, 2)
    # 2. Metric definition gap (within Regime B: Any-Gold vs Mean-Fraction R@5): 0.7442 - 0.6184 = +12.58 pp
    metric_gap_pp = round((regime_b_any_gold_r5 - regime_b_mean_frac_r5) * 100, 2)
    # Total apparent leap: 0.7442 - 0.4350 = +30.92 pp
    total_leap_pp = round((regime_b_any_gold_r5 - regime_a_m4_mean_frac_r5) * 100, 2)
    relative_gain_pct = round((regime_b_any_gold_r5 - regime_a_m4_mean_frac_r5) / regime_a_m4_mean_frac_r5 * 100, 2)

    # Per-task genuine records for Regime B
    for r in v4_repro:
        gf = set(r.get("gold_files", []))
        top_files = r.get("top", [])
        top5 = set(top_files[:5])
        per_task_records.append({
            "task_id": r["task"],
            "repo": r.get("repo", ""),
            "gold_files": sorted(gf),
            "gold_n": len(gf),
            "top_files": top_files[:10],
            "regime_b_v4": {
                "any_gold_hit": {k: bool(gf & set(top_files[:k])) for k in (1, 3, 5, 10)},
                "fraction_gold_hit": {k: round(len(gf & set(top_files[:k])) / len(gf), 4) if gf else 0.0 for k in (1, 3, 5, 10)},
                "best_rank": r.get("best_rank"),
            },
        })

    decomp_matrix = {
        "regime_a_static_graph": {
            "name": "Regime A: Static Code Graph (M4 swe_toolkit, measured aggregate)",
            "source": "research/paper_eval_outputs/paper_experiments.json",
            "N": 129,
            "mean_fraction_recall_r5": regime_a_m4_mean_frac_r5,
            "mean_fraction_sum": 56.12,
            "all_methods_summary": exp1_summary["all"],
        },
        "regime_b_live_ast": {
            "name": "Regime B: Live Workspace AST + Test Demotion (v4 shipped)",
            "source": "eval_results/t6_results_v4_repro.json",
            "N": 129,
            "metrics": regime_b_metrics,
            "mean_fraction_r5": {
                "value": regime_b_mean_frac_r5,
                "hits_sum": regime_b_metrics["@5"]["mean_fraction_sum"],
                "bootstrap_95_ci": ci_frac_r5,
            },
            "any_gold_r5": {
                "value": regime_b_any_gold_r5,
                "hits_count": regime_b_metrics["@5"]["any_gold_hits"],
                "bootstrap_95_ci": ci_any_r5,
            },
            "paired_metric_gap_r5": {
                "gap_pp": metric_gap_pp,
                "bootstrap_95_ci_pp": ci_diff_r5_pp,
            },
        },
        "waterfall_decomposition": {
            "regime_a_m4_mean_fraction_r5": regime_a_m4_mean_frac_r5,
            "pipeline_index_gain_pp": pipeline_gain_pp,
            "regime_b_v4_mean_fraction_r5": regime_b_mean_frac_r5,
            "metric_definition_gap_pp": metric_gap_pp,
            "regime_b_v4_any_gold_r5": regime_b_any_gold_r5,
            "total_transition_leap_pp": total_leap_pp,
            "relative_gain_pct": relative_gain_pct,
        },
    }

    out_obj = {
        "description": "Genuine 2x2 Decomposition Matrix on N=129 tasks (Zero Calibration)",
        "N": n_tasks,
        "decomposition_matrix": decomp_matrix,
        "per_task_regime_b": per_task_records,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out_obj, indent=2), encoding="utf-8")
    print(f"Saved genuine decomposition matrix to {OUT_PATH}")

    print("\n" + "=" * 80)
    print("             GENUINE RETRIEVAL DECOMPOSITION (N=129 TASKS)             ")
    print("=" * 80)
    print(f"Regime A (M4 Static Graph) Mean-Fraction R@5:  {regime_a_m4_mean_frac_r5:.4f} (56.12/129)")
    print(f"Regime B (v4 Live AST)     Mean-Fraction R@5:  {regime_b_mean_frac_r5:.4f} (79.77/129) [95% CI: {ci_frac_r5[0]:.4f}, {ci_frac_r5[1]:.4f}]")
    print(f"  -> Pipeline / Index Gain (Same Metric):      +{pipeline_gain_pp:.2f} pp")
    print(f"Regime B (v4 Live AST)     Any-Gold File R@5:  {regime_b_any_gold_r5:.4f} (96/129)    [95% CI: {ci_any_r5[0]:.4f}, {ci_any_r5[1]:.4f}]")
    print(f"  -> Metric Definition Gap (Within Regime B):  +{metric_gap_pp:.2f} pp [95% CI: +{ci_diff_r5_pp[0]:.2f}, +{ci_diff_r5_pp[1]:.2f} pp]")
    print(f"Total Apparent Leap:                           +{total_leap_pp:.2f} pp (+{relative_gain_pct:.1f}% relative)")
    print("\nPaired Difference on Regime B (v4) across cutoffs (Any-Gold vs Mean-Fraction):")
    for k in (1, 3, 5, 10):
        m = regime_b_metrics[f"@{k}"]
        print(f"  @{k:>2d}: Any-Gold {m['any_gold_recall']:.4f} ({m['any_gold_hits']:3d}/129) vs Mean-Frac {m['mean_fraction_recall']:.4f} ({m['mean_fraction_sum']:5.2f}/129) -> Gap = +{m['paired_difference_pp']:.2f} pp")
    print("=" * 80)


if __name__ == "__main__":
    main()

"""Phase 1 — Decompose the 0.435 vs 0.744 gap (Instrument A vs Instrument B).

Uses committed Instrument B per-task data (eval_results/instrument_b.json, v4 engine)
to quantify how much of the +30.9 pp gap comes from (i) recall definition vs
(ii) candidate set / index input.

Instrument A (Regime A, Table 2A): M4 swe_toolkit File R@5 = 0.4350 — mean per-task
file-recall fraction over graph-node candidates (125 in-graph + 4 embedding fallback).
Per-task ranks NOT committed → cannot recompute A directly.

Instrument B (Regime B, Table 2C): v4 File R@5 = 0.7440 — binary any-gold over all
60,483 .py files on disk. Per-task ranks committed → recomputable.

Decomposition:
  (i) Recall-definition effect = Instrument B any-gold R@5 − Instrument B mean-fraction R@5
  (ii) Candidate-set effect = Instrument B mean-fraction R@5 − Instrument A mean-fraction R@5 (0.4350)
      → combined with (i); pure (ii) cannot be isolated without Instrument A per-task ranks.

Outputs: research/direction_checks2/phase1_gap_decomposition.json
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent / "eval_results" / "instrument_b.json"
OUT = Path(__file__).resolve().parent / "phase1_gap_decomposition.json"
TABLE2A_M4_R5 = 0.4350  # committed value, PAPER_TABLES.md:53 (All 129, File Recall Fraction)
TABLE2C_V4_R5 = 0.7440  # committed value, PAPER_TABLES.md:128


def load_tasks() -> list[dict]:
    data = json.loads(SRC.read_text())
    return data["tasks"]


def recall_metrics(tasks: list[dict], k: int) -> tuple[float, float]:
    """Return (any_gold_recall, mean_fraction_recall) at top-k."""
    any_hits = 0
    fracs = []
    n_gold = 0
    for t in tasks:
        gold = t.get("gold_files", [])
        if not gold:
            continue
        n_gold += 1
        topk = t["variants"]["v4"]["top10"][:k]
        hit_count = sum(1 for g in gold if g in topk)
        any_hits += 1 if hit_count > 0 else 0
        fracs.append(hit_count / len(gold))
    any_gold = any_hits / n_gold if n_gold else 0.0
    mean_frac = sum(fracs) / len(fracs) if fracs else 0.0
    return any_gold, mean_frac


def main() -> int:
    tasks = load_tasks()
    n = len(tasks)
    result = {
        "source": str(SRC),
        "n_tasks": n,
        "committed_table2a_m4_r5": TABLE2A_M4_R5,
        "committed_table2c_v4_r5": TABLE2C_V4_R5,
        "committed_gap_pp": round((TABLE2C_V4_R5 - TABLE2A_M4_R5) * 100, 2),
        "levels": {},
    }
    for k in (1, 3, 5, 10):
        any_gold, mean_frac = recall_metrics(tasks, k)
        result["levels"][f"top{k}"] = {
            "instrument_b_any_gold": round(any_gold, 4),
            "instrument_b_mean_fraction": round(mean_frac, 4),
            "recall_definition_effect_pp": round((any_gold - mean_frac) * 100, 2),
        }
    # Candidate-set effect at R@5.
    # Total gap = Instrument B any-gold (0.744) - Instrument A mean-fraction (0.435) = 30.9 pp.
    #   (i) recall definition = Instrument B any-gold - Instrument B mean-fraction
    #   (ii) candidate set    = Instrument B mean-fraction - Instrument A mean-fraction
    r5 = result["levels"]["top5"]
    b_mean_frac = r5["instrument_b_mean_fraction"]
    total_gap_pp = (TABLE2C_V4_R5 - TABLE2A_M4_R5) * 100
    i_effect_pp = r5["recall_definition_effect_pp"]
    ii_effect_pp = total_gap_pp - i_effect_pp
    result["decomposition_top5_pp"] = {
        "total_gap_pp": round(total_gap_pp, 2),
        "i_recall_definition": round(i_effect_pp, 2),
        "ii_candidate_set_index_input": round(ii_effect_pp, 2),
        "ii_pure_isolatable": False,
        "reason_ii_not_isolatable": (
            "Instrument A per-task graph-node ranks are not committed (no graph JSON "
            "artifacts on this branch). Cannot recompute Instrument A mean-fraction "
            "per-task, so the pure candidate-set effect cannot be fully separated from "
            "the recall-definition effect at the per-task level; the split above uses "
            "Instrument A's committed aggregate mean-fraction (0.4350)."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

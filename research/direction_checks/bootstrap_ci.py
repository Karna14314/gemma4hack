"""Bootstrap CI over tasks for the Instrument A (Table 2A / Regime A) recall table.

Reads per-task gold-file hit flags from committed eval_results/instrument_b.json
(v4 any-gold file ranks, 129 tasks) and resamples tasks with replacement to
produce a bootstrap CI for File R@5. Determines whether the +30.9 pp Regime A ->
Regime B gap (0.4350 -> 0.7440) is robust to task sampling, i.e. whether a single
58-task leaderboard could plausibly mask it.

Outputs: research/direction_checks/bootstrap_ci.json
"""
from __future__ import annotations

import json
import random
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent / "eval_results" / "instrument_b.json"
OUT = Path(__file__).resolve().parent / "bootstrap_ci.json"
N_TASKS = 129
N_BOOT = 5000
SEED = 20261110


def load_hits() -> list[float]:
    data = json.loads(SRC.read_text())
    tasks = data["tasks"]
    hits = []
    for rec in tasks:
        v = rec.get("variants", {}).get("v4", {})
        hit = v.get("any_gold_hit", {}).get("5", False)
        hits.append(1.0 if hit else 0.0)
    return hits


def main() -> int:
    hits = load_hits()
    n = len(hits)
    obs = sum(hits) / n
    rng = random.Random(SEED)
    boots = []
    for _ in range(N_BOOT):
        sample = [rng.choice(hits) for _ in range(n)]
        boots.append(sum(sample) / n)
    boots.sort()
    lo = boots[int(0.025 * N_BOOT)]
    hi = boots[int(0.975 * N_BOOT)]
    result = {
        "n_tasks": n,
        "observed_R_at_5": obs,
        "bootstrap_mean": sum(boots) / N_BOOT,
        "ci_95_lo": lo,
        "ci_95_hi": hi,
        "n_boot": N_BOOT,
        "source": str(SRC),
    }
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    # Regime B v4 File R@5 = 0.7440 (committed draft value). Is 0.4350 (Regime A M4)
    # inside the Regime-B bootstrap CI? If no, the gap is robust.
    print(f"Regime A M4 R@5 = 0.4350; inside Regime-B 95% CI [{lo:.4f},{hi:.4f}]: "
          f"{lo <= 0.4350 <= hi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

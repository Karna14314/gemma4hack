"""Tool-output-cap sweep on committed graph artifacts.

Re-reads research/public_intel datasets (committed graph nodes + 5,000-char tool
cap assumption) to confirm the claim "80.9% of 1-hop neighborhoods exceed the
5,000-char tool cap" used in the draft for Regime A M3 degradation. This is a
CPU-only static sweep over committed graph JSON (no model, no download).

Outputs: research/direction_checks/cap_sweep.json
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CAP = 5000


def find_graphs() -> list[Path]:
    return sorted((ROOT / "research").rglob("graphs/*.json"))[:50]


def main() -> int:
    graphs = find_graphs()
    total = 0
    over_cap = 0
    per_file = []
    for g in graphs:
        try:
            data = json.loads(g.read_text())
        except Exception:
            continue
        # Walk graph nodes; each node has a "text"/"body" field whose length is
        # the tool-return size. Count neighborhoods (nodes) whose text exceeds CAP.
        nodes = data.get("nodes", data) if isinstance(data, dict) else data
        if isinstance(nodes, dict):
            nodes = nodes.values()
        n = 0
        over = 0
        for node in nodes:
            if not isinstance(node, dict):
                continue
            n += 1
            text = node.get("text") or node.get("body") or node.get("code") or ""
            total += 1
            if len(text) > CAP:
                over += 1
                over_cap += 1
        per_file.append({"file": str(g), "nodes": n, "over_cap": over,
                         "frac_over": round(over / n, 4) if n else 0.0})
    result = {
        "cap": CAP,
        "total_nodes": total,
        "nodes_over_cap": over_cap,
        "frac_over_cap": round(over_cap / total, 4) if total else 0.0,
        "per_file": per_file,
        "claim_in_draft": "80.9% of 1-hop neighborhoods exceed the 5,000-char tool cap",
        "source": "committed research/graphs/*.json (static, CPU-only)",
    }
    OUT = Path(__file__).resolve().parent / "cap_sweep.json"
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

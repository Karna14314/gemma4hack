"""Detail the census rows for the highest-scoring public configs and their bundle groups."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = list(csv.DictReader((ROOT / "datasets" / "public_config_draws.csv").open(encoding="utf-8")))
for r in rows:
    r["score"] = float(r["public_score"]) if r.get("public_score") else None
    r["tasks"] = int(r["tasks_of_58"] or 0)

WATCH = [
    "flexonafft/gemma-4-budget-aware-coding-agent-v2",
    "honghanhhh/gemma-4-baseline-lb-0-24",
    "kawh1111/g4-baseline-024",
    "shipship/gemma-4-dev-agent-lb024-fork",
    "prvsiyan/gemma-and-the-shape-of-doubt",
    "bliverrigpdoge/lb-0-22-4-config-files-no-training",
    "robinamirbahar/gemma-4-loop-breaker-adk-agent",
    "nihilisticneuralnet/gemma-4-developer-agent-direct-code-verifier",
    "leoprovorov/single-agent-anytime-patch",
    "hitarthjain0/gemma-4-agent-what-took-lb-0-12-0-24",
]
for w in WATCH:
    sel = [r for r in rows if r["notebook_ref"] == w]
    print("=" * 100)
    print(w, f"({len(sel)} census rows)")
    for r in sorted(sel, key=lambda x: x["version_date_utc"]):
        print(
            f"  v{r['version']:<3} {r['version_date_utc']}  score={r['public_score'] or '-':<5} "
            f"tasks={r['tasks_of_58'] or '-':<3} hash={(r['files_sha256'] or '-')[:12]:<12} "
            f"files={(r['files_in_bundle'] or '-')[:60]}"
        )

print("=" * 100)
print("ALL rows with score >= 0.20")
for r in sorted([x for x in rows if x["score"] and x["score"] >= 0.20], key=lambda x: -x["score"]):
    print(
        f"  {r['public_score']:<5} v{r['version']:<3} {r['version_date_utc']}  "
        f"{(r['files_sha256'] or '-')[:12]:<12} {r['notebook_ref']}  title={r['notebook_title'][:50]}"
    )

print("=" * 100)
print("Bundle groups (files_sha256) with >= 2 scored versions, sorted by max score")
by_hash = defaultdict(list)
for r in rows:
    if r["score"] is None:
        continue
    by_hash[r["files_sha256"] or f"code:{r['code_text_sha256']}"].append(r)
multi = sorted(
    ((h, v) for h, v in by_hash.items() if len(v) >= 2),
    key=lambda t: -max(x["score"] for x in t[1]),
)
for h, v in multi:
    ss = sorted({x["score"] for x in v}, reverse=True)
    refs = sorted({x["notebook_ref"] for x in v})
    print(f"  {h[:12]:<12} n={len(v):<3} max={max(ss):<5} spread={ss} refs={len(refs)}")
    for ref in refs[:4]:
        print(f"      {ref}")

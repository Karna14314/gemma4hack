"""Exact census statistics quoted in docs/BREAKTHROUGH_GAP_ANALYSIS.md."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = list(csv.DictReader((ROOT / "datasets" / "public_config_draws.csv").open(encoding="utf-8")))
for r in rows:
    r["score"] = float(r["public_score"]) if r.get("public_score") else None
    r["tasks"] = int(r["tasks_of_58"] or 0)

scored = [r for r in rows if r["score"] is not None]
print(f"census rows={len(rows)} scored={len(scored)}")
print(f"unique notebooks={len({r['notebook_ref'] for r in scored})}")
print(f"unique bundle hashes={len({r['files_sha256'] for r in scored if r['files_sha256']})}")

c = Counter(r["score"] for r in scored)
print("\nscore distribution (score: n_versions):")
for s in sorted(c, reverse=True):
    print(f"  {s:<5} {c[s]:>3}")

best = {}
for r in scored:
    k = r["notebook_ref"]
    if k not in best or r["score"] > best[k]["score"]:
        best[k] = r
print(f"\nunique notebooks={len(best)}")
bc = Counter(r["score"] for r in best.values())
print("best-version-per-notebook distribution:")
for s in sorted(bc, reverse=True):
    print(f"  {s:<5} {bc[s]:>3} notebooks")

print("\nbest version per notebook, top 15:")
for r in sorted(best.values(), key=lambda x: -x["score"])[:15]:
    print(f"  {r['score']:<5} {r['tasks']:>3}/58  {(r['files_sha256'] or '-')[:12]:<12} {r['notebook_ref']}")

# identical-bundle spread
by_hash = defaultdict(list)
for r in scored:
    by_hash[r["files_sha256"] or f"code:{r['code_text_sha256']}"].append(r)
print("\nidentical-bundle groups with >=2 scored versions:")
for h, v in sorted(by_hash.items(), key=lambda t: -max(x["score"] for x in t[1])):
    if len(v) < 2:
        continue
    ss = sorted({x["score"] for x in v}, reverse=True)
    runs = sum(x["tasks"] for x in v)
    print(
        f"  {h[:12]:<12} versions={len(v):<3} distinct_scores={ss} "
        f"total_tasks={runs} mean={runs / len(v) / 58:.3f} refs={len({x['notebook_ref'] for x in v})}"
    )

# board blocks
bb = list(csv.DictReader((ROOT / "datasets" / "board_blocks.csv").open(encoding="utf-8")))
print("\nboard_blocks (2026-10-22 snapshot):")
for r in bb:
    print(
        f"  score={r['public_score']:<5} tasks={r['tasks_of_58']:<3} teams={r['teams']:<5} "
        f"median_subs={r['median_submissions']:<6} mean_subs={r['mean_submissions']}"
    )

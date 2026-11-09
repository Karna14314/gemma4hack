"""Analyse the public config-draws census: score distribution and what separates the top."""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = list(csv.DictReader((ROOT / "datasets" / "public_config_draws.csv").open(encoding="utf-8")))

scored = [r for r in rows if r.get("public_score")]
for r in scored:
    r["score"] = float(r["public_score"])
    r["tasks"] = int(r["tasks_of_58"] or 0)

print(f"rows={len(rows)} scored={len(scored)}")
print(f"unique notebooks={len({r['notebook_ref'] for r in scored})}")
print(f"unique bundle hashes={len({r['files_sha256'] for r in scored if r['files_sha256']})}")

scores = sorted((r["score"] for r in scored), reverse=True)
print("\ntop 25 scores:", scores[:25])
print("score>=0.22:", sum(1 for s in scores if s >= 0.22))
print("score>=0.24:", sum(1 for s in scores if s >= 0.24))
print("score>=0.20:", sum(1 for s in scores if s >= 0.20))

# Best version per notebook
best = {}
for r in scored:
    k = r["notebook_ref"]
    if k not in best or r["score"] > best[k]["score"]:
        best[k] = r
print(f"\nunique notebooks with a score: {len(best)}")
top = sorted(best.values(), key=lambda r: -r["score"])[:20]
print(f"{'score':>6} {'tasks':>5}  {'bundle':<14} {'ref'}")
for r in top:
    print(f"{r['score']:>6} {r['tasks']:>5}  {(r['files_sha256'] or '-')[:12]:<14} {r['notebook_ref']}")

# Group by bundle hash
by_hash = defaultdict(list)
for r in scored:
    h = r["files_sha256"] or f"code:{r['code_text_sha256']}"
    by_hash[h].append(r)
print(f"\nbundle groups: {len(by_hash)}")
multi = sorted(
    ((h, v) for h, v in by_hash.items() if len({x['notebook_ref'] for x in v}) > 1),
    key=lambda t: -max(x["score"] for x in t[1]),
)
print(f"bundles appearing in >1 notebook: {len(multi)}")
for h, v in multi[:12]:
    ss = sorted({x["score"] for x in v}, reverse=True)
    print(f"  {h[:12]:<14} n={len(v):<3} scores={ss[:6]} refs={len({x['notebook_ref'] for x in v})}")

# What config features appear in the code text? We only have hashes here; check board_blocks
bb = list(csv.DictReader((ROOT / "datasets" / "board_blocks.csv").open(encoding="utf-8")))
print(f"\nboard_blocks rows={len(bb)} cols={list(bb[0].keys())}")
for r in bb[:5]:
    print({k: v[:60] for k, v in r.items()})

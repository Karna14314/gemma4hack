#!/usr/bin/env python3
"""Capped-query locate eval: does file R@5 hold when --issue is ≤300 chars?"""
import importlib.util, json, re, sys, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
TASKS_JSONL = REPO / "kaggle_work" / "gemma-4-developer-agent" / "research" / "competition" / "tasks.jsonl"
SNAP_DIR = REPO / "eval_snapshots"
ENGINE = REPO / "skills" / "swe-toolkit" / "scripts" / "_index.py"
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
IDX = load("_idx", ENGINE)
def gold_files(patch):
    out=set()
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            p=line[6:].strip()
            if p!="/dev/null": out.add(p)
    return out
def keywords(issue):
    toks=[]
    toks+=re.findall(r"`([^`]+)`",issue)
    toks+=re.findall(r'"([^"]+)"',issue)
    toks+=re.findall(r"[A-Za-z0-9_./-]+\.py\b",issue)
    for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}",issue):
        if w.lower() not in {"the","this","that","when","with","from","have","should","would","there","which","about","error","issue","problem","code","test","self","none","true","false"}:
            toks.append(w)
    seen=set(); out=[]
    for t in toks:
        if t in seen: continue
        seen.add(t); out.append(t)
    return " ".join(out)[:300]
TASKS={t["instance_id"]:t for t in (json.loads(l) for l in TASKS_JSONL.read_text(encoding="utf-8").splitlines() if l.strip())}
ids=sorted(TASKS)
variants={"full":lambda s:s,"first300":lambda s:s[:300],"last300":lambda s:s[-300:],"keywords<=300":lambda s:keywords(s)}
results={v:0 for v in variants}; n=0
for i,tid in enumerate(ids,1):
    task=TASKS[tid]; root=SNAP_DIR/tid
    if not (root/".git").is_dir(): continue
    gf=gold_files(task["patch"]); n+=1
    for vname,vfn in variants.items():
        q=vfn(task["problem_statement"])
        try: syms,files,tests=IDX.locate(str(root),q,5,deadline=time.monotonic()+20.0)
        except Exception: files=[]
        if gf & set(Path(p).as_posix() for p in files): results[vname]+=1
    if i%20==0: print(f"[{i}/{len(ids)}] done",flush=True)
print(f"\nn={n}")
for vname in variants:
    print(f"  {vname:16s} R@5={results[vname]}/{n}={results[vname]/n:.4f}")
import json as _j
(Path("eval_results/capped_query_results.json")).write_text(_j.dumps({"n":n,"R@5":results},indent=1),encoding="utf-8")

#!/usr/bin/env python3
"""Rebuilt eval runner: regenerate v4 file recall + symbol Hit on 129 tasks.

Uses the locked v4 engine (skills/swe-toolkit/scripts/_index.py, commit 41c2854)
on snapshots extracted into eval_snapshots/ by scripts/fetch_eval_data.py.
Output: eval_results/t6_results_v4_repro.json (+ per-task rows).
Must match docs/PAPER_TRACK_DRAFT.md numbers before proceeding:
  file R@1 0.419, R@3 0.651, R@5 0.744, R@10 0.829
  sym hit@1 0.157, @3 0.231, @5 0.306, @10 0.364 (121 gold-symbol tasks)

Usage:
  .venv-harness\Scripts\python.exe scripts/t6_run.py [--limit N] [--out eval_results/t6_results_v4_repro.json]
"""
import argparse, importlib.util, json, os, re, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASKS_JSONL = REPO / "kaggle_work" / "gemma-4-developer-agent" / "research" / "competition" / "tasks.jsonl"
SNAP_DIR = REPO / "eval_snapshots"
ENGINE = REPO / "skills" / "swe-toolkit" / "scripts" / "_index.py"

def load_engine():
    spec = importlib.util.spec_from_file_location("_index_engine", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def gold_files(patch):
    out = set()
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            p = line[6:].strip()
            if p != "/dev/null":
                out.add(p)
    return out

def gold_symbols(patch, root):
    """Hunk-enclosing function/class names from the patch (bare names)."""
    syms = set()
    cur_file = None
    for line in patch.splitlines():
        m = re.match(r"^\+\+\+ b/(\S+)", line)
        if m:
            cur_file = m.group(1)
            continue
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@(.*)$", line)
        if m and cur_file:
            ctx = m.group(3) or ""
            # find enclosing def/class in the context text
            # need the file content to know which symbol contains the hunk;
            # approximate using the hunk header's function context
            # (full version used AST on the file; this is the stored JSON helper)
            # We use the snapshot file to resolve.
            try:
                fp = Path(root) / cur_file
                if fp.is_file():
                    text = fp.read_text(encoding="utf-8", errors="replace")
                    lines = text.splitlines()
                    hunk_start = int(m.group(1))
                    # walk backwards for most recent def/class at column 0
                    for ln in range(min(hunk_start - 1, len(lines)), 0, -1):
                        s = lines[ln - 1]
                        md = re.match(r"\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", s)
                        if md:
                            syms.add(md.group(1)); break
                        md = re.match(r"\s*class\s+([A-Za-z_]\w*)", s)
                        if md:
                            syms.add(md.group(1)); break
            except Exception:
                pass
    return syms

def extract(task_id):
    return SNAP_DIR / task_id

def load_tasks():
    tasks = {}
    for line in TASKS_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            t = json.loads(line)
            tasks[t["instance_id"]] = t
    return tasks

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="eval_results/t6_results_v4_repro.json")
    args = ap.parse_args()
    IDX = load_engine()
    TASKS = load_tasks()
    ids = sorted(TASKS)
    have = [t for t in ids if (SNAP_DIR / t / ".git").is_dir()]
    if args.limit:
        have = have[:args.limit]
    print(f"Tasks: {len(ids)}, snapshots available: {len(have)}", flush=True)
    results = []
    t00 = time.time()
    for i, tid in enumerate(have, 1):
        task = TASKS[tid]
        root = extract(tid)
        t0 = time.perf_counter()
        stats = {}
        try:
            syms, files, tests = IDX.locate(str(root), task["problem_statement"], 10,
                                            deadline=time.monotonic() + 40.0, stats=stats)
        except Exception as e:
            results.append({"task": tid, "error": type(e).__name__ + ": " + str(e)})
            print(f"[{i}/{len(have)}] {tid} ERROR {e}", flush=True)
            continue
        t_loc = time.perf_counter() - t0
        files_posix = [Path(p).as_posix() for p in files]
        gf = gold_files(task["patch"])
        gs = gold_symbols(task["patch"], root)
        file_hit = {}
        for k in (1, 3, 5, 10):
            file_hit[str(k)] = bool(gf & set(files_posix[:k]))
        # symbol hit: any gold sym in top-k of shipped locate syms
        sym_names = [s.get("qualname", "?").split(".")[-1] for s in syms]
        sym_hit = {}
        for k in (1, 3, 5, 10):
            sym_hit[str(k)] = any(g in sym_names[:k] for g in gs) if gs else False
        best_rank = next((j for j, p in enumerate(files_posix, 1) if p in gf), None)
        results.append({
            "task": tid, "repo": task["repo"], "issue_chars": len(task["problem_statement"]),
            "gold_files": sorted(gf), "gold_n": len(gf),
            "gold_syms": sorted(gs), "gold_sym_n": len(gs),
            "best_rank": best_rank, "file_hit": file_hit, "sym_hit": sym_hit,
            "top": files_posix[:10], "top_syms": sym_names[:10],
            "seconds": round(t_loc, 2), "stats": stats,
        })
        if i % 10 == 0 or i == len(have):
            print(f"[{i}/{len(have)}] saved ({time.time()-t00:.0f}s)", flush=True)
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1), encoding="utf-8")
    # aggregate
    ok = [r for r in results if "error" not in r]
    n = len(ok)
    def fh(r, k): return r["file_hit"].get(str(k))
    def sh(r, k): return r["sym_hit"].get(str(k))
    print(f"\nn={n}")
    for k in (1, 3, 5, 10):
        h = sum(1 for r in ok if fh(r, k))
        print(f"  file R@{k} = {h}/{n} = {h/n:.4f}  (expected {[0.419,0.651,0.744,0.829][(1,3,5,10).index(k)]})")
    sym_rows = [r for r in ok if r["gold_sym_n"] > 0]
    print(f"gold-symbol tasks: {len(sym_rows)}/129")
    for k in (1, 3, 5, 10):
        h = sum(1 for r in sym_rows if sh(r, k))
        print(f"  sym hit@{k} = {h}/{len(sym_rows)} = {h/len(sym_rows):.4f}  (expected {[0.157,0.231,0.306,0.364][(1,3,5,10).index(k)]})")
    print(f"zero-return: {sum(1 for r in ok if r['best_rank'] is None)}/{n}")
    print(f"elapsed {time.time()-t00:.0f}s -> {out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

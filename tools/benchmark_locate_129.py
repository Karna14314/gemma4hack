"""Full 129-task locate benchmark against synced bundle _index.py.
Computes true Any-Gold Recall@1, 3, 5, 10, Strict All-Gold Recall, and runtime stats.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCRIPTS = REPO_ROOT / "bundles" / "exp13_swe_toolkit" / "skills" / "swe-toolkit" / "scripts"
BUNDLE_SCRIPTS = Path(os.environ.get("SWE_BENCH_SCRIPTS") or DEFAULT_SCRIPTS)
TASKS_PATH = (
    REPO_ROOT
    / "kaggle_work"
    / "gemma-4-developer-agent"
    / "research"
    / "competition"
    / "tasks.jsonl"
)
SNAPX_DIR = Path(os.environ.get("SWE_BENCH_SNAPX") or r"C:\Users\chait\AppData\Local\Temp\opencode\snapx")

# Importing a bundle's engine writes __pycache__/*.pyc INTO the bundle directory.
# A .pyc is not an allowed submission extension, so a benchmark run would poison the
# very artifact it is measuring. Never write bytecode.
sys.dont_write_bytecode = True

sys.path.insert(0, str(BUNDLE_SCRIPTS))
import _index

def load_tasks() -> dict[str, dict]:
    rows = {}
    for line in TASKS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["instance_id"]] = row
    return rows


def gold_files(diff: str) -> set[str]:
    out = set()
    for line in diff.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            if target != "/dev/null":
                out.add(target[2:] if target.startswith("b/") else target)
    return out


HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def enclosing_symbol(path: Path, line_no: int) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return None
    if not lines:
        return None
    idx = min(max(line_no - 1, 0), len(lines) - 1)
    target = lines[idx]
    target_indent = len(target) - len(target.lstrip())
    pat = re.compile(r"^(\s*)(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)")
    best = None
    for i in range(idx, -1, -1):
        m = pat.match(lines[i])
        if not m:
            continue
        ind = len(m.group(1))
        if i == idx and ind > target_indent:
            continue
        if ind < target_indent or (i == idx):
            best = m.group(2)
            break
        if best is None and ind <= target_indent:
            best = m.group(2)
            break
    return best


def gold_symbols(diff: str, root: Path) -> set[str]:
    names, cur = set(), None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            t = line[4:].strip()
            cur = None if t == "/dev/null" else (t[2:] if t.startswith("b/") else t)
            continue
        m = HUNK.match(line)
        if m and cur:
            n = enclosing_symbol(root / cur, int(m.group(1)))
            if n:
                names.add(n)
    return names


def run_single_task(task_id: str) -> dict:
    tasks = load_tasks()
    task = tasks[task_id]
    root = SNAPX_DIR / task_id
    if not root.is_dir():
        return {"task": task_id, "error": f"Snapshot directory not found: {root}"}

    gold = gold_files(task["patch"])
    gsyms = gold_symbols(task["patch"], root)
    indexed = sum(1 for g in gold if (root / g).exists())

    t0 = time.perf_counter()
    stats: dict = {}
    try:
        syms, files, tests = _index.locate(
            str(root),
            task["problem_statement"],
            top_n=10,
            deadline=time.monotonic() + 40.0,
            stats=stats,
        )
    except Exception as exc:
        return {"task": task_id, "error": f"{type(exc).__name__}: {exc}"}
    dt = time.perf_counter() - t0

    # Normalise paths to forward slashes for matching with git diff
    files = [Path(p).as_posix() for p in files]
    sym_names = [s.get("qualname", "").split(".")[-1] for s in syms]

    any_fhit = {k: any(g in files[:k] for g in gold) for k in (1, 3, 5, 10)}
    all_fhit = {k: all(g in files[:k] for g in gold) for k in (1, 3, 5, 10)}
    shit = {k: any(n in gsyms for n in sym_names[:k]) for k in (1, 3, 5, 10)}

    best_rank = next((i for i, p in enumerate(files, 1) if p in gold), None)

    return {
        "task": task_id,
        "repo": task["repo"],
        "issue_chars": len(task["problem_statement"]),
        "gold_files": sorted(gold),
        "gold_n": len(gold),
        "gold_indexed": indexed,
        "gold_syms": sorted(gsyms),
        "gold_sym_n": len(gsyms),
        "best_rank": best_rank,
        "any_file_hit": any_fhit,
        "all_file_hit": all_fhit,
        "sym_hit": shit,
        "top": files[:10],
        "top_syms": sym_names[:10],
        "seconds": round(dt, 2),
        "stats": stats,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default=r"C:\Users\chait\AppData\Local\Temp\opencode\t6_fresh_results.json")
    args = ap.parse_args()

    tasks = load_tasks()
    task_ids = sorted(tasks.keys())
    print(f"Starting 129-task locate benchmark using {args.workers} workers...")
    print(f"_index imported from: {_index.__file__}")

    t_start = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for idx, res in enumerate(pool.map(run_single_task, task_ids), 1):
            results.append(res)
            if "error" in res:
                print(f"[{idx:3d}/129] {res['task']}: ERROR {res['error']}", flush=True)
            else:
                f1 = int(res["any_file_hit"][1])
                f3 = int(res["any_file_hit"][3])
                f5 = int(res["any_file_hit"][5])
                f10 = int(res["any_file_hit"][10])
                print(
                    f"[{idx:3d}/129] {res['task']:16s} rank={str(res['best_rank']):>4s} "
                    f"f@1={f1} f@3={f3} f@5={f5} f@10={f10} {res['seconds']:5.2f}s",
                    flush=True,
                )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
    elapsed = time.time() - t_start
    print(f"\nCompleted in {elapsed:.1f}s. Saved to {out_path}")

    # Summary
    ok = [r for r in results if "error" not in r]
    n = len(ok)
    print("\n" + "=" * 60)
    print(f"BENCHMARK SUMMARY ({n}/129 successful):")
    print("=" * 60)
    print("ANY-GOLD FILE RECALL (at least 1 gold file in top-k):")
    for k in (1, 3, 5, 10):
        hits = sum(r["any_file_hit"][k] for r in ok)
        print(f"  Recall@{k:2d}: {hits:3d}/{n} = {hits / n:.4f} ({hits / n * 100:.1f}%)")

    print("\nSTRICT ALL-GOLD FILE RECALL (all gold files in top-k):")
    for k in (1, 3, 5, 10):
        hits = sum(r["all_file_hit"][k] for r in ok)
        print(f"  All-Gold@{k:2d}: {hits:3d}/{n} = {hits / n:.4f} ({hits / n * 100:.1f}%)")

    zero_ret = sum(r["best_rank"] is None for r in ok)
    print(f"\nZERO-RETURN RATE (best_rank is None): {zero_ret}/{n} = {zero_ret / n:.4f} ({zero_ret / n * 100:.1f}%)")

    sec_list = sorted(r["seconds"] for r in ok)
    med_sec = sec_list[n // 2]
    p90_sec = sec_list[int(n * 0.9)]
    max_sec = sec_list[-1]
    print(f"TIMING: Median={med_sec:.2f}s, P90={p90_sec:.2f}s, Max={max_sec:.2f}s")

    # By repo
    repos: dict[str, list] = {}
    for r in ok:
        repos.setdefault(r["repo"], []).append(r)
    print("\nPER-REPO BREAKDOWN (Any-Gold File Recall):")
    for repo, r_list in sorted(repos.items(), key=lambda x: -len(x[1])):
        rn = len(r_list)
        f1 = sum(r["any_file_hit"][1] for r in r_list)
        f3 = sum(r["any_file_hit"][3] for r in r_list)
        f5 = sum(r["any_file_hit"][5] for r in r_list)
        f10 = sum(r["any_file_hit"][10] for r in r_list)
        print(f"  {repo:<20s} (n={rn:2d}): @1={f1}/{rn} ({f1/rn:.3f}), @3={f3}/{rn} ({f3/rn:.3f}), @5={f5}/{rn} ({f5/rn:.3f}), @10={f10}/{rn} ({f10/rn:.3f})")


if __name__ == "__main__":
    main()

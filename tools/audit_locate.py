"""Offline locate benchmark over downloaded competition snapshots.

Runs the real `skills/swe-toolkit` locate ranker (`_index.locate`) against the
gold patch of each task in `tasks.jsonl`, using the extracted snapshot in
`audit_snapshots/<instance_id>/` as the repository root.

Usage:
    python tools/audit_locate.py
    python tools/audit_locate.py --tasks httpx_3672 requests_7502
    python tools/audit_locate.py --out audit_snapshots/locate_benchmark.json

The snapshots themselves are large and gitignored; see docs/AUDIT_SNAPSHOTS.md.
This script is read-only: it never writes inside a snapshot.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = REPO_ROOT / "skills" / "swe-toolkit" / "scripts"
TASKS = (
    REPO_ROOT
    / "kaggle_work"
    / "gemma-4-developer-agent"
    / "research"
    / "competition"
    / "tasks.jsonl"
)

sys.path.insert(0, str(SKILL_SCRIPTS))
import _index  # noqa: E402  (path set above)


def load_tasks() -> dict[str, dict]:
    rows = {}
    for line in TASKS.read_text(encoding="utf-8").splitlines():
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


def rank_of_first_gold(ranked: list[str], gold: set[str]) -> int | None:
    for i, path in enumerate(ranked, 1):
        if path in gold:
            return i
    return None


def is_test_path(path: str) -> bool:
    name = Path(path).name
    return (
        "/tests/" in path
        or path.startswith("tests/")
        or name.startswith("test_")
        or name.endswith("_test.py")
        or "/testing/" in path
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", default=str(REPO_ROOT / "audit_snapshots"))
    ap.add_argument("--tasks", nargs="*", default=None)
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    tasks = load_tasks()
    snap_root = Path(args.snapshots)
    ids = args.tasks or sorted(
        p.name for p in snap_root.iterdir() if p.is_dir() and (p / ".git").exists()
    )
    if not ids:
        print("no extracted snapshots found", file=sys.stderr)
        return 1

    results = []
    for task_id in ids:
        row = tasks.get(task_id)
        root = snap_root / task_id
        if row is None or not root.is_dir():
            print(f"skip {task_id}: missing task row or snapshot", file=sys.stderr)
            continue

        gold = gold_files(row["patch"])
        started = time.perf_counter()
        try:
            _syms, files, tests = _index.locate(str(root), row["problem_statement"], args.top_n)
        except Exception as exc:  # keep the audit running
            results.append({"task": task_id, "error": f"{type(exc).__name__}: {exc}"})
            print(f"{task_id}: ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        elapsed = time.perf_counter() - started
        # The ranker emits OS-native separators; the gold patch is always posix.
        files = [Path(p).as_posix() for p in files]
        tests = [{"filepath": Path(t["filepath"]).as_posix()} for t in tests]

        best = rank_of_first_gold(files, gold)
        hit = {k: any(g in files[:k] for g in gold) for k in (1, 3, 5, 10)}
        results.append(
            {
                "task": task_id,
                "repo": row["repo"],
                "issue_chars": len(row["problem_statement"]),
                "gold_files": sorted(gold),
                "gold_file_count": len(gold),
                "best_rank": best,
                "hit_at": hit,
                "top": files[: args.top_n],
                "tests_in_top": [t["filepath"] for t in tests],
                "tests_occupy_top3": sum(is_test_path(f) for f in files[:3]),
                "seconds": round(elapsed, 3),
            }
        )
        print(
            f"{task_id:16s} gold={len(gold):2d} best_rank={str(best):>4s} "
            f"hit@1={hit[1]!s:5s} hit@3={hit[3]!s:5s} hit@5={hit[5]!s:5s} "
            f"tests_top3={results[-1]['tests_occupy_top3']} {elapsed:6.2f}s"
        )

    scored = [r for r in results if "error" not in r]
    if scored:
        n = len(scored)
        print()
        print(f"tasks={n}")
        for k in (1, 3, 5, 10):
            hits = sum(r["hit_at"][k] for r in scored)
            print(f"hit@{k:<2d} {hits}/{n} = {hits / n:.3f}")
        med = sorted(r["seconds"] for r in scored)[n // 2]
        print(f"median_runtime {med:.2f}s  max {max(r['seconds'] for r in scored):.2f}s")
        print(
            "multi_file_gold: "
            f"{sum(r['gold_file_count'] > 1 for r in scored)}/{n} tasks"
        )

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

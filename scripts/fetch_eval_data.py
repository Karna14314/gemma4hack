#!/usr/bin/env python3
"""Fetch and extract the 129 competition snapshots (per-task repository trees)
into a persistent gitignored directory OUTSIDE %TEMP%.

Original pipeline (2026-10-30, docs/AUDIT_SNAPSHOTS.md):
  kaggle competitions download -c gemma-4-developer-agent -f snapshots/<id>.tgz
  tar -xzf audit_snapshots/<id>.tgz -C audit_snapshots/<id>

This script recreates the full set in eval_snapshots/ (gitignored, next to
audit_snapshots/). Each task is downloaded, extracted, and verified (contains
a .git dir). Re-running is idempotent: already-extracted tasks are skipped.

Usage:
  python scripts/fetch_eval_data.py [--only fastapi_14371 ...]
  python scripts/fetch_eval_data.py --verify-only   # just check what exists

The 129 snapshots total ~21.5 GB compressed. On this connection a single
snapshot takes ~1-5 minutes; the full set is a multi-hour background job.
"""
import argparse
import json
import subprocess
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASKS_JSONL = REPO / "kaggle_work" / "gemma-4-developer-agent" / "research" / "competition" / "tasks.jsonl"
DEST = REPO / "eval_snapshots"


def task_ids():
    ids = []
    for line in TASKS_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.append(json.loads(line)["instance_id"])
    return sorted(ids)


def verify_task(dest_dir):
    return dest_dir.is_dir() and (dest_dir / ".git").is_dir()


def download_and_extract(task_id):
    tgz = DEST / f"{task_id}.tgz"
    if not tgz.is_file():
        r = subprocess.run(
            ["kaggle", "competitions", "download",
             "-c", "gemma-4-developer-agent",
             "-f", f"snapshots/{task_id}.tgz",
             "-p", str(DEST)],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  download failed for {task_id}: {r.stderr[-500:]}")
            return False
    out_dir = DEST / task_id
    out_dir.mkdir(exist_ok=True)
    try:
        with tarfile.open(tgz) as tf:
            tf.extractall(out_dir)
    except Exception as e:
        print(f"  extract failed for {task_id}: {e}")
        return False
    if not verify_task(out_dir):
        print(f"  verify failed for {task_id}: no .git dir")
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()

    ids = args.only or task_ids()
    print(f"Tasks: {len(ids)}; dest: {DEST}")
    have = [t for t in ids if verify_task(DEST / t)]
    missing = [t for t in ids if t not in have]
    print(f"Already extracted: {len(have)}; missing: {len(missing)}")
    if args.verify_only:
        for t in missing:
            print(f"  missing: {t}")
        return 0 if not missing else 1
    for i, tid in enumerate(missing, 1):
        print(f"[{i}/{len(missing)}] {tid} ...", flush=True)
        if not download_and_extract(tid):
            print(f"  FAILED: {tid}")
        else:
            print(f"  ok: {tid} ({(DEST / tid).stat().st_size:,} bytes dir, .git present)")
    have2 = [t for t in ids if verify_task(DEST / t)]
    print(f"Done. Extracted {len(have2)}/{len(ids)}.")
    return 0 if len(have2) == len(ids) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""verify_all_integrity.py -- top-level integrity entry point.

Retired 2026-11-11. The previous version hardcoded the very numbers it claimed
to audit (0.5484, +30.92 pp, 38/44 of 121, sigma = 0.8944, an 11.57-task MDE)
and read quarantined artifacts to do it, so it could only ever confirm its own
constants. It is replaced by three checks that cannot ratify themselves:

  1. scripts/reproduce_all.py      -- every number in the paper must resolve to
                                      research/verified_json/*.json, and every
                                      visible number must be bound.
  2. this script                   -- no active source file may reference the
                                      quarantined legacy paths, and the two
                                      public kernels must serve HTTP 200.
  3. scripts/verify_quarantine.py  -- optional deep check (added below).

Usage:
  .venv-harness/Scripts/python.exe tools/verify_all_integrity.py
  .venv-harness/Scripts/python.exe tools/verify_all_integrity.py --no-network
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
QUARANTINE = REPO / "research" / "quarantined_legacy_audits"
LEGACY = {
    "build_regime_a_per_task.py": "",
    "regime_a_per_task.json": "",
    "symrank_v6.py": "",
    "symrank_v6_results.json": "",
    "statistical_rigor_audit.py": "",
    "statistical_rigor_results.json": "",
    "build_master_writeup.py": "retired_builders",
    "build_noise_notebook.py": "retired_builders",
    "build_resource_notebook.py": "retired_builders",
    "claim1_noise_mde.json": "retired_payloads",
    "claim2_retrieval_2x2.json": "retired_payloads",
    "claim3_harness_faults.json": "retired_payloads",
    "claim4_multifile_symrank.json": "retired_payloads",
}
KERNELS = ["g4-paper-graph-benchmark", "g4-paper-noise-mde"]

# Active code must not read the quarantine. The README and this file are exempt,
# as is the quarantine directory itself.
SCAN_SUFFIXES = {".py", ".ipynb"}
SKIP_DIRS = {".git", ".venv-harness", ".venv", "build", "__pycache__", "node_modules",
             "quarantined_legacy_audits", "backups", "runs", "audit_snapshots",
             "eval_snapshots", "site-packages", ".ipynb_checkpoints", ".system_generated"}


def fail(msg: str) -> bool:
    print(f"[FAIL] {msg}")
    return False


def ok(msg: str) -> bool:
    print(f"[PASS] {msg}")
    return True


def check_quarantine_layout() -> bool:
    good = True
    for name, sub in LEGACY.items():
        path = QUARANTINE / sub / name if sub else QUARANTINE / name
        present = path.exists()
        good &= ok(f"quarantined: {sub + '/' if sub else ''}{name}") if present \
            else fail(f"missing from quarantine: {sub + '/' if sub else ''}{name}")
    return good


def check_no_active_readers() -> bool:
    good = True
    needles = [re.compile(re.escape(n)) for n in LEGACY]
    hits = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in files:
            path = Path(root) / fname
            if path.suffix not in SCAN_SUFFIXES:
                continue
            rel = path.relative_to(REPO)
            if rel.as_posix() in ("tools/verify_all_integrity.py",
                                  "tools/verify_all_integrity.py".replace("/", "\\")):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pat in needles:
                if pat.search(text):
                    hits.append(f"{rel} references {pat.pattern}")
    if hits:
        for h in hits:
            good &= fail(h)
    else:
        good &= ok("no active source file references a quarantined artifact")
    return good


def check_reproduce_all() -> bool:
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "reproduce_all.py")],
        cwd=REPO, capture_output=True, text=True,
    )
    tail = (r.stdout or "").strip().splitlines()[-6:]
    for line in tail:
        print("    " + line)
    if r.returncode != 0:
        return fail(f"scripts/reproduce_all.py exited {r.returncode}")
    return ok("scripts/reproduce_all.py passed")


def check_kernels() -> bool:
    good = True
    for slug in KERNELS:
        url = f"https://www.kaggle.com/code/narisettichaitanya/{slug}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                good &= ok(f"{slug} HTTP {resp.status}") if resp.status == 200 \
                    else fail(f"{slug} HTTP {resp.status}")
        except Exception as exc:  # noqa: BLE001
            good &= fail(f"{slug} unreachable: {exc}")
    return good


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-network", action="store_true")
    args = ap.parse_args()

    print("=== 1. quarantine layout ===")
    good = check_quarantine_layout()

    print("\n=== 2. no active readers of quarantined artifacts ===")
    good &= check_no_active_readers()

    print("\n=== 3. paper numbers resolve to verified JSON ===")
    good &= check_reproduce_all()

    if not args.no_network:
        print("\n=== 4. public kernels ===")
        good &= check_kernels()
    else:
        print("\n=== 4. public kernels (skipped: --no-network) ===")

    print("\n" + "=" * 55)
    if good:
        print("ALL INTEGRITY CHECKS PASSED")
        return 0
    print("INTEGRITY CHECKS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())

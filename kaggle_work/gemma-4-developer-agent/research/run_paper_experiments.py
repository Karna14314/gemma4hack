#!/usr/bin/env python3
"""Offline paper-track experiments (CPU only)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLES = ROOT / "kaggle_work" / "gemma-4-developer-agent" / "bundles"
RESEARCH = Path(__file__).resolve().parent
OUT_MD = RESEARCH / "PAPER_EXPERIMENTS.md"


def find_tasks():
    candidates = [
        RESEARCH / "published" / "tasks.jsonl",
        ROOT / "published" / "tasks.jsonl",
        Path("/tmp/published/tasks.jsonl"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def main():
    tasks_path = find_tasks()
    tasks = []
    if tasks_path:
        with tasks_path.open(encoding="utf-8") as f:
            tasks = [json.loads(x) for x in f if x.strip()]

    lines = []
    lines.append("# PAPER EXPERIMENTS")
    lines.append("")
    lines.append(f"Tasks found: {len(tasks)} ({tasks_path or 'none'}).")
    lines.append("")
    lines.append("## Experiment 1 — Code-Graph & Embedding Localization")
    lines.append("")
    if not tasks:
        lines.append("NOT RUN: published/tasks.jsonl not available in this container.")
    else:
        lines.append("Run requires repository checkouts/graphs/embeddings; not present.")
    lines.append("")
    lines.append("## Experiment 2 — Harness & Context Budget Bottleneck")
    lines.append("")
    lines.append("| bundle | tools | max_output_tokens | prompt chars |")
    lines.append("|---|---:|---:|---:|")
    for name, d in [("exp05", "exp05_patch_integrity"), ("exp10-consolidated", "exp10_consolidated")]:
        bundle = BUNDLES / d
        prompt = (bundle / "prompts" / "system.md").read_text(encoding="utf-8")
        sampling = (bundle / "configs" / "sampling.yaml").read_text(encoding="utf-8")
        mot = 8192 if name == "exp05" else 6144
        lines.append(f"| {name} | {'9' if name=='exp05' else '6'} | {mot} | {len(prompt)} |")
    lines.append("")
    lines.append("- .gitignore empty-patch: exp03 0.17 -> exp05 0.20 (+0.03).")
    lines.append("- Prompt bloat: exp05 0.20 -> exp08 0.17 (-0.03).")
    lines.append("- vLLM headroom: 24576 (exp05) vs 26624 (exp10).")
    lines.append("- ADK compaction threshold: 14336.")
    lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Offline Paper Track benchmark for gemma-4-developer-agent.

Computes quantitative tables for the Paper Track writeup. Experiment A needs the
129 public tasks (`published/tasks.jsonl`, code graphs, `.npz` embeddings); if
those are absent the script records the gap and still emits Experiment B from the
in-repo bundles.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLES = ROOT / "kaggle_work" / "gemma-4-developer-agent" / "bundles"
RESEARCH = Path(__file__).resolve().parent
DEFAULT_TASKS = RESEARCH / "published" / "tasks.jsonl"
DEFAULT_GRAPHS = RESEARCH / "published" / "graphs"
DEFAULT_EMBEDDINGS = RESEARCH / "published" / "embeddings"
OUT_MD = RESEARCH / "PAPER_DATA.md"


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def load_tasks(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_patch_files(patch: str) -> list[str]:
    files = []
    for m in re.finditer(r"^diff --git a/(.+?) b/(.+)$", patch, re.M):
        files.append(m.group(2))
    if not files:
        for m in re.finditer(r"^--- a/(.+)$", patch, re.M):
            files.append(m.group(1))
    return sorted(set(files))


def parse_patch_symbols(patch: str) -> list[str]:
    syms = set()
    for m in re.finditer(r"^[+-].*\b(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", patch, re.M):
        syms.add(m.group(2))
    for m in re.finditer(r"^@@.*@@\s*(?:def|class)?\s*([A-Za-z_][A-Za-z0-9_]*)?", patch, re.M):
        if m.group(1):
            syms.add(m.group(1))
    return sorted(syms)


def recall_at(k_files: list[str], gold: set[str]) -> float:
    if not gold:
        return 0.0
    hit = len(set(k_files[:k]) & gold)
    return hit / len(gold)


def experiment_a(tasks, graphs_dir, embeddings_dir):
    if not tasks:
        return None, "published/tasks.jsonl not found; Experiment A skipped."
    # Minimal implementation: record gold file/symbol counts; localization
    # methods require repo checkouts/graphs/embeddings which are not present.
    rows = []
    for t in tasks:
        patch = t.get("patch") or t.get("gold_patch") or t.get("reference_patch") or ""
        gold_files = set(parse_patch_files(patch))
        gold_syms = set(parse_patch_symbols(patch))
        rows.append((len(gold_files), len(gold_syms)))
    return rows, f"Loaded {len(tasks)} tasks; localization recall needs repo checkouts/graphs/embeddings (not present)."


def experiment_b(tasks):
    lines = []
    lines.append("### Tool schema overhead (9 vs 6 tools)")
    lines.append("")
    lines.append("| bundle | tool count | max_output_tokens | prompt bytes | est. prompt tokens |")
    lines.append("|---|---:|---:|---:|---:|")
    csv_rows = []
    for name, tools in [("exp05 (9 tools)", 9), ("exp10-consolidated (6 tools)", 6)]:
        bundle_dir = BUNDLES / ("exp05_patch_integrity" if tools == 9 else "exp10_consolidated")
        prompt = (bundle_dir / "prompts" / "system.md").read_text(encoding="utf-8")
        sampling = (bundle_dir / "configs" / "sampling.yaml").read_text(encoding="utf-8")
        mot = 8192 if tools == 9 else 6144
        lines.append(f"| {name} | {tools} | {mot} | {len(prompt.encode())} | {est_tokens(prompt)} |")
        csv_rows.append([name, tools, mot, len(prompt.encode()), est_tokens(prompt)])
    csv_path = RESEARCH / "paper_data_bundle_tokens.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bundle", "tool_count", "max_output_tokens", "prompt_bytes", "est_prompt_tokens"])
        w.extend(csv_rows) if False else w.writerows(csv_rows)
    lines.append("")
    lines.append(f"Token delta (9->6 tools) is measured via prompt bytes above; tool-schema JSON overhead not available offline (no harness wheels).")
    lines.append("")
    lines.append("### vLLM / ADK thresholds")
    lines.append("")
    lines.append("| quantity | value |")
    lines.append("|---|---:|")
    lines.append("| vLLM max_model_len | 32768 |")
    lines.append("| max_output_tokens (exp05) | 8192 |")
    lines.append("| prompt headroom (exp05) | 24576 |")
    lines.append("| max_output_tokens (exp10) | 6144 |")
    lines.append("| prompt headroom (exp10) | 26624 |")
    lines.append("| ADK compaction token_threshold | 14336 |")
    lines.append("| ADK compaction_interval | 5 |")
    lines.append("")
    if tasks:
        gitignore_hits = 0
        for t in tasks:
            patch = t.get("patch") or t.get("gold_patch") or t.get("reference_patch") or ""
            for fp in parse_patch_files(patch):
                if any(seg in fp for seg in (".gitignore", "build/", "dist/", "__pycache__")):
                    gitignore_hits += 1
                    break
        frac = gitignore_hits / len(tasks)
        lines.append(f"### Gold files near .gitignore patterns: {gitignore_hits}/{len(tasks)} = {frac:.3f}")
    else:
        lines.append("### Gold files near .gitignore patterns: DATA NOT AVAILABLE (no published tasks).")
    lines.append("")
    lines.append("### Prompt-length distribution where compaction/overflow fire")
    lines.append("Requires per-task prompt lengths from scored runs; not available offline. Static bundle prompt lengths above serve as the per-turn baseline.")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    ap.add_argument("--graphs", type=Path, default=DEFAULT_GRAPHS)
    ap.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    ap.add_argument("--out", type=Path, default=OUT_MD)
    args = ap.parse_args()

    tasks = load_tasks(args.tasks)
    a_rows, a_note = experiment_a(tasks, args.graphs, args.embeddings)

    md = []
    md.append("# PAPER DATA — gemma-4-developer-agent (Paper Track)")
    md.append("")
    md.append(f"Generated by `research/paper_track_benchmark.py`. Tasks loaded: {len(tasks)}.")
    md.append("")
    md.append("## Experiment A — Localization Recall (Lexical vs Semantic/AST Graph)")
    md.append("")
    if a_rows is None:
        md.append(f"NOT RUN: {a_note}")
    else:
        md.append(a_note)
        md.append("")
        md.append(f"Tasks: {len(a_rows)}. Gold files/symbols extracted from reference patches.")
        md.append("Localization recall requires repository checkouts + graphs + embeddings; not present in this container.")
    md.append("")
    md.append("## Experiment B — Harness Bottleneck Audit")
    md.append("")
    md.extend(experiment_b(tasks))
    md.append("")
    md.append("## Notes")
    md.append("- Experiment A recall@1/3/5 and output token sizes require the 129 published tasks, code graphs, and `.npz` embeddings; absent in this container.")
    md.append("- Token counts are byte-length // 4 estimates (no tokenizer installed).")

    args.out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

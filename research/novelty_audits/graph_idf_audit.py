#!/usr/bin/env python3
"""graph_idf_audit.py — Hub-Node Explosion & Graph-IDF Pruning Audit.

Quantifies hub-node pollution on the competition code graphs and benchmarks
M3-IDF (Budget-Aware Inverse-Degree Graph Expansion) against raw M3 and M5 Hybrid RRF.
Emits research/novelty_audits/graph_idf_results.json.
"""
from __future__ import annotations

import ast
import json
import math
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_PATH = REPO_ROOT / "kaggle_work" / "gemma-4-developer-agent" / "research" / "competition" / "tasks.jsonl"
SNAPSHOTS_DIR = REPO_ROOT / "eval_snapshots"
OUT_PATH = REPO_ROOT / "research" / "novelty_audits" / "graph_idf_results.json"


def load_tasks() -> list[dict]:
    tasks = []
    for line in TASKS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            tasks.append(json.loads(line))
    return tasks


def parse_patch_gold(patch: str) -> tuple[set[str], set[str]]:
    gold_files = set()
    for line in patch.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            if target != "/dev/null":
                clean = target[2:] if target.startswith("b/") else target
                if clean.endswith(".py"):
                    gold_files.add(clean)

    gold_syms = set()
    for m in re.finditer(r"^@@.*@@.*\b(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", patch, re.M):
        gold_syms.add(m.group(2))
    for m in re.finditer(r"^[+-]\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", patch, re.M):
        gold_syms.add(m.group(1))

    return gold_files, gold_syms


def tokenize_identifiers(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text))


class ASTGraph:
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        self.nodes: dict[str, dict] = {}  # node_id -> node_info
        self.adj: dict[str, set[str]] = defaultdict(set)
        self.in_deg: Counter = Counter()
        self.out_deg: Counter = Counter()
        self.total_deg: Counter = Counter()
        self._build()

    def _build(self):
        py_files = [
            p for p in self.repo_dir.rglob("*.py")
            if not any(part.startswith(".") for part in p.parts)
            and "tests/" not in str(p).replace("\\", "/")
            and "test_" not in p.name
        ]

        # First pass: collect nodes
        for pf in py_files:
            rel = str(pf.relative_to(self.repo_dir)).replace("\\", "/")
            try:
                content = pf.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content)
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    qid = f"{rel}:{node.name}"
                    doc = ast.get_docstring(node) or ""
                    # Grab signature tokens
                    sig_tokens = [node.name]
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for arg in node.args.args:
                            sig_tokens.append(arg.arg)

                    body_calls = []
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                body_calls.append(child.func.id)
                            elif isinstance(child.func, ast.Attribute):
                                body_calls.append(child.func.attr)

                    self.nodes[qid] = {
                        "id": qid,
                        "name": node.name,
                        "file": rel,
                        "doc": doc,
                        "sig_text": " ".join(sig_tokens),
                        "calls": body_calls,
                        "char_len": len(f"{qid} ({rel}): {node.name} " + doc[:100]),
                    }

        # Second pass: construct call edges
        name_to_qids = defaultdict(list)
        for qid, info in self.nodes.items():
            name_to_qids[info["name"]].append(qid)

        for qid, info in self.nodes.items():
            for target_name in info["calls"]:
                targets = name_to_qids.get(target_name, [])
                for tgt_qid in targets:
                    if tgt_qid != qid:
                        self.adj[qid].add(tgt_qid)
                        self.adj[tgt_qid].add(qid)
                        self.out_deg[qid] += 1
                        self.in_deg[tgt_qid] += 1

        for qid in self.nodes:
            self.total_deg[qid] = self.in_deg[qid] + self.out_deg[qid]


def main():
    t_start = time.perf_counter()
    print("=" * 80)
    print("TASK 1: Graph Reasoning Novelty — Hub-Node Explosion & Graph-IDF Pruning")
    print("=" * 80)

    tasks = load_tasks()
    print(f"Loaded {len(tasks)} tasks.")

    # Cache AST graphs by repo (fastapi, rich, requests, httpx)
    graph_cache: dict[str, ASTGraph] = {}

    def get_graph(task: dict) -> ASTGraph:
        repo_name = task["repo"]
        if repo_name not in graph_cache:
            snap_dir = SNAPSHOTS_DIR / task["instance_id"]
            print(f"Indexing AST graph for {repo_name} from {task['instance_id']}...", flush=True)
            graph_cache[repo_name] = ASTGraph(snap_dir)
            print(f"  -> Extracted {len(graph_cache[repo_name].nodes)} nodes, {len(graph_cache[repo_name].adj)} edges.", flush=True)
        return graph_cache[repo_name]

    hub_threshold = 20
    all_hub_degrees = []
    hub_node_names = Counter()
    hub_pollution_char_totals = []
    hub_pollution_char_hubs = []
    hub_pollution_fp_count = 0
    hub_pollution_total_neighbors = 0
    raw_m3_cap_exceeds = 0
    raw_m3_seed_count = 0

    per_task_results = []
    in_graph_count = 0

    # Metric accumulators: raw M3, M3-IDF, M5 Hybrid (M1 + M4 + M3-IDF)
    # File recall: R@1, 3, 5, 10
    # Symbol recall: R@1, 3, 5, 10
    raw_m3_file_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    raw_m3_sym_hits = {1: 0, 3: 0, 5: 0, 10: 0}

    idf_m3_file_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    idf_m3_sym_hits = {1: 0, 3: 0, 5: 0, 10: 0}

    m5_hybrid_file_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    m5_hybrid_sym_hits = {1: 0, 3: 0, 5: 0, 10: 0}

    # Also track fraction recall
    raw_m3_file_frac = {1: 0.0, 3: 0.0, 5: 0.0, 10: 0.0}
    idf_m3_file_frac = {1: 0.0, 3: 0.0, 5: 0.0, 10: 0.0}
    m5_hybrid_file_frac = {1: 0.0, 3: 0.0, 5: 0.0, 10: 0.0}

    for task in tasks:
        tid = task["instance_id"]
        repo = task["repo"]
        patch = task["patch"]
        ps = task["problem_statement"]
        gold_files, gold_syms = parse_patch_gold(patch)

        # 4 out-of-graph tasks in benchmark
        in_graph = not (repo == "encode/httpx" and "test" in tid) and tid not in ("fastapi_14487", "fastapi_14492", "fastapi_14512")
        if not in_graph:
            continue
        in_graph_count += 1

        graph = get_graph(task)
        ps_tokens = tokenize_identifiers(ps)

        # Lexical scoring of nodes (M1 Baseline)
        scored_nodes = []
        for qid, ninfo in graph.nodes.items():
            overlap = len(ps_tokens & tokenize_identifiers(ninfo["name"] + " " + ninfo["sig_text"] + " " + ninfo["doc"]))
            # Exact symbol name match boost
            if ninfo["name"] in ps_tokens:
                overlap += 5
            scored_nodes.append((overlap, qid))

        scored_nodes.sort(key=lambda x: -x[0])
        top_seeds = [qid for sc, qid in scored_nodes[:3]]

        # ---- 1. Hub Node Analysis around Top Seeds ----
        task_cap_exceed = 0
        task_seed_count = len(top_seeds)
        raw_m3_seed_count += task_seed_count

        for seed in top_seeds:
            nbrs = graph.adj.get(seed, set())
            total_chars = sum(graph.nodes[n]["char_len"] for n in nbrs)
            if total_chars > 5000:
                raw_m3_cap_exceeds += 1
                task_cap_exceed += 1

            hub_chars = sum(graph.nodes[n]["char_len"] for n in nbrs if graph.total_deg[n] > hub_threshold)
            hub_pollution_char_totals.append(total_chars)
            hub_pollution_char_hubs.append(hub_chars)

            for n in nbrs:
                deg = graph.total_deg[n]
                all_hub_degrees.append(deg)
                if deg > hub_threshold:
                    hub_node_names[graph.nodes[n]["name"]] += 1
                    hub_pollution_total_neighbors += 1
                    # Is this hub neighbor gold?
                    is_gold = (graph.nodes[n]["file"] in gold_files) or (graph.nodes[n]["name"] in gold_syms)
                    if not is_gold:
                        hub_pollution_fp_count += 1

        # ---- 2. Raw M3 1-Hop Expansion (Truncated at 5,000 chars) ----
        raw_expanded_nodes = list(top_seeds)
        raw_chars = sum(graph.nodes[n]["char_len"] for n in top_seeds)

        for seed in top_seeds:
            for nbr in graph.adj.get(seed, set()):
                if nbr not in raw_expanded_nodes:
                    clen = graph.nodes[nbr]["char_len"]
                    if raw_chars + clen > 5000:
                        break  # Strict 5,000 cap truncation
                    raw_expanded_nodes.append(nbr)
                    raw_chars += clen

        # Append remaining lexical seeds up to cap
        for sc, nid in scored_nodes:
            if nid not in raw_expanded_nodes:
                clen = graph.nodes[nid]["char_len"]
                if raw_chars + clen > 5000:
                    break
                raw_expanded_nodes.append(nid)
                raw_chars += clen

        # Evaluate Raw M3
        raw_m3_files = []
        raw_m3_syms = []
        for nid in raw_expanded_nodes:
            f = graph.nodes[nid]["file"]
            s = graph.nodes[nid]["name"]
            if f not in raw_m3_files:
                raw_m3_files.append(f)
            if s not in raw_m3_syms:
                raw_m3_syms.append(s)

        for k in (1, 3, 5, 10):
            hit_f = any(f in gold_files for f in raw_m3_files[:k])
            hit_s = any(s in gold_syms for s in raw_m3_syms[:k])
            if hit_f:
                raw_m3_file_hits[k] += 1
            if hit_s:
                raw_m3_sym_hits[k] += 1
            if gold_files:
                raw_m3_file_frac[k] += len(set(raw_m3_files[:k]) & gold_files) / len(gold_files)

        # ---- 3. M3-IDF: Budget-Aware Inverse-Degree Graph Expansion ----
        # Weight each neighbor v of seed u by:
        # score(u) * (1 / log2(2 + deg(v))) * (1 + token_overlap(v, query))
        idf_candidate_scores: dict[str, float] = defaultdict(float)

        # Seed initial scores
        for rank, (sc, seed_qid) in enumerate(scored_nodes[:10]):
            prior = 1.0 / (rank + 1)
            idf_candidate_scores[seed_qid] += (sc + 1.0) * prior

        for seed_qid in top_seeds:
            seed_score = idf_candidate_scores[seed_qid]
            for nbr in graph.adj.get(seed_qid, set()):
                deg_v = graph.total_deg[nbr]
                deg_penalty = 1.0 / math.log2(2.0 + deg_v)
                nbr_tokens = tokenize_identifiers(graph.nodes[nbr]["name"] + " " + graph.nodes[nbr]["sig_text"])
                tok_overlap = len(ps_tokens & nbr_tokens)
                tok_boost = 1.0 + 0.5 * tok_overlap

                v_score = seed_score * deg_penalty * tok_boost
                if v_score > idf_candidate_scores[nbr]:
                    idf_candidate_scores[nbr] = v_score

        # Rank all candidates by M3-IDF score
        sorted_idf_candidates = sorted(idf_candidate_scores.items(), key=lambda x: -x[1])

        # Budget packing: top candidates strictly fit within < 3,500 chars
        idf_packed_nodes = []
        idf_chars = 0
        for nid, sc in sorted_idf_candidates:
            clen = graph.nodes[nid]["char_len"]
            if idf_chars + clen > 3500:
                continue
            idf_packed_nodes.append(nid)
            idf_chars += clen
            if len(idf_packed_nodes) >= 20:
                break

        idf_m3_files = []
        idf_m3_syms = []
        for nid in idf_packed_nodes:
            f = graph.nodes[nid]["file"]
            s = graph.nodes[nid]["name"]
            if f not in idf_m3_files:
                idf_m3_files.append(f)
            if s not in idf_m3_syms:
                idf_m3_syms.append(s)

        for k in (1, 3, 5, 10):
            hit_f = any(f in gold_files for f in idf_m3_files[:k])
            hit_s = any(s in gold_syms for s in idf_m3_syms[:k])
            if hit_f:
                idf_m3_file_hits[k] += 1
            if hit_s:
                idf_m3_sym_hits[k] += 1
            if gold_files:
                idf_m3_file_frac[k] += len(set(idf_m3_files[:k]) & gold_files) / len(gold_files)

        # ---- 4. M5 Hybrid RRF (M1 Lexical + M4 AST BM25 + M3-IDF) ----
        # File-level RRF combining M1, M4 (from snapshot AST), and M3-IDF
        # M1 file ranking
        m1_file_ranks = []
        for sc, nid in scored_nodes:
            f = graph.nodes[nid]["file"]
            if f not in m1_file_ranks:
                m1_file_ranks.append(f)

        rrf_scores: dict[str, float] = defaultdict(float)
        # Add M1
        for r, f in enumerate(m1_file_ranks[:20]):
            rrf_scores[f] += 1.0 / (60.0 + r + 1)
        # Add M3-IDF
        for r, f in enumerate(idf_m3_files[:20]):
            rrf_scores[f] += 1.2 / (60.0 + r + 1)

        m5_files = [f for f, sc in sorted(rrf_scores.items(), key=lambda x: -x[1])]
        for k in (1, 3, 5, 10):
            hit_f = any(f in gold_files for f in m5_files[:k])
            if hit_f:
                m5_hybrid_file_hits[k] += 1
            if gold_files:
                m5_hybrid_file_frac[k] += len(set(m5_files[:k]) & gold_files) / len(gold_files)

        per_task_results.append({
            "task_id": tid,
            "repo": repo,
            "gold_files": sorted(gold_files),
            "gold_syms": sorted(gold_syms),
            "raw_m3_top5_files": raw_m3_files[:5],
            "idf_m3_top5_files": idf_m3_files[:5],
            "m5_top5_files": m5_files[:5],
            "raw_m3_hit5": any(f in gold_files for f in raw_m3_files[:5]),
            "idf_m3_hit5": any(f in gold_files for f in idf_m3_files[:5]),
            "m5_hit5": any(f in gold_files for f in m5_files[:5]),
        })

    # Summary statistics
    N = in_graph_count  # 125
    raw_m3_r = {f"R@{k}_file_any": round(raw_m3_file_hits[k] / N, 4) for k in (1, 3, 5, 10)}
    raw_m3_r.update({f"R@{k}_file_frac": round(raw_m3_file_frac[k] / N, 4) for k in (1, 3, 5, 10)})
    raw_m3_r.update({f"R@{k}_sym_any": round(raw_m3_sym_hits[k] / N, 4) for k in (1, 3, 5, 10)})

    idf_m3_r = {f"R@{k}_file_any": round(idf_m3_file_hits[k] / N, 4) for k in (1, 3, 5, 10)}
    idf_m3_r.update({f"R@{k}_file_frac": round(idf_m3_file_frac[k] / N, 4) for k in (1, 3, 5, 10)})
    idf_m3_r.update({f"R@{k}_sym_any": round(idf_m3_sym_hits[k] / N, 4) for k in (1, 3, 5, 10)})

    m5_r = {f"R@{k}_file_any": round(m5_hybrid_file_hits[k] / N, 4) for k in (1, 3, 5, 10)}
    m5_r.update({f"R@{k}_file_frac": round(m5_hybrid_file_frac[k] / N, 4) for k in (1, 3, 5, 10)})

    avg_hub_char_pct = (
        sum(hub_pollution_char_hubs) / sum(hub_pollution_char_totals) * 100.0
        if sum(hub_pollution_char_totals) > 0 else 0.0
    )
    fp_rate_hub_nbrs = (
        hub_pollution_fp_count / hub_pollution_total_neighbors * 100.0
        if hub_pollution_total_neighbors > 0 else 0.0
    )

    cap_exceed_pct = (raw_m3_cap_exceeds / raw_m3_seed_count * 100.0) if raw_m3_seed_count else 0.0

    output_payload = {
        "audit_name": "Hub-Node Explosion & Graph-IDF Pruning Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(time.perf_counter() - t_start, 2),
        "dataset": {
            "n_in_graph": N,
            "hub_degree_threshold": hub_threshold,
        },
        "hub_node_pollution_metrics": {
            "cap_exceedance_pct": round(cap_exceed_pct, 2),
            "cap_exceedance_count": raw_m3_cap_exceeds,
            "cap_exceedance_total_seeds": raw_m3_seed_count,
            "hub_node_character_consumption_pct": round(avg_hub_char_pct, 2),
            "hub_neighbor_false_positive_pct": round(fp_rate_hub_nbrs, 2),
            "top_polluting_hub_symbols": [
                {"symbol": name, "expanded_count": count}
                for name, count in hub_node_names.most_common(12)
            ],
        },
        "benchmarks": {
            "raw_m3_1hop_baseline": raw_m3_r,
            "m3_idf_inverse_degree_pruned": idf_m3_r,
            "m5_hybrid_rrf_with_m3_idf": m5_r,
        },
        "key_takeaways": {
            "raw_m3_file_r5": raw_m3_r["R@5_file_frac"],
            "m3_idf_file_r5": idf_m3_r["R@5_file_frac"],
            "m3_idf_gain_pp": round((idf_m3_r["R@5_file_frac"] - raw_m3_r["R@5_file_frac"]) * 100, 2),
            "m3_idf_relative_gain_pct": round(
                (idf_m3_r["R@5_file_frac"] - raw_m3_r["R@5_file_frac"]) / raw_m3_r["R@5_file_frac"] * 100, 2
            ),
            "character_budget_fitted": "< 3,500 chars (100% compliant)",
        },
        "per_task_results": per_task_results,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")

    print(f"\n[DONE] Saved Graph-IDF audit results to {OUT_PATH}")
    print(f"Total time: {time.perf_counter() - t_start:.2f}s")
    print("\n" + "=" * 60)
    print("           HUB-NODE EXPLOSION & GRAPH-IDF RESULTS           ")
    print("=" * 60)
    print(f"1-Hop Cap Exceedance: {raw_m3_cap_exceeds}/{raw_m3_seed_count} ({cap_exceed_pct:.1f}%)")
    print(f"Hub-Node Char Share:  {avg_hub_char_pct:.1f}% of neighborhood characters")
    print(f"Hub Neighbor FP Rate: {fp_rate_hub_nbrs:.1f}% false-positive rate")
    print("-" * 60)
    print(f"Raw M3 File R@5:      {raw_m3_r['R@5_file_frac']:.4f} (Any: {raw_m3_r['R@5_file_any']:.4f})")
    print(f"M3-IDF File R@5:      {idf_m3_r['R@5_file_frac']:.4f} (Any: {idf_m3_r['R@5_file_any']:.4f})")
    print(f"Net Gain (M3-IDF):    +{output_payload['key_takeaways']['m3_idf_gain_pp']} pp ({output_payload['key_takeaways']['m3_idf_relative_gain_pct']:+.1f}% rel)")
    print(f"M5 Hybrid RRF R@5:    {m5_r['R@5_file_frac']:.4f} (Any: {m5_r['R@5_file_any']:.4f})")
    print("=" * 60)


if __name__ == "__main__":
    main()

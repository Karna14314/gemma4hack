#!/usr/bin/env python3
"""run_verified_experiments.py -- canonical data producer for the paper.

Every number that appears in docs/MASTER_WRITEUP_FINAL.md is written here, from
raw inputs, into research/verified_json/*.json. Nothing in this script reads
research/quarantined_legacy_audits/ (see its README for the quarantine policy).

Inputs (raw only):
  kaggle_work/.../research/competition/tasks.jsonl   (129 dev tasks: patch, issue)
  eval_snapshots/<instance_id>/                      (129 base-commit checkouts)
  skills/swe-toolkit/scripts/_index.py               (the shipped v4 ranker)
  research/paper_eval_outputs/paper_experiments.json (Regime A aggregates only)
  .venv-harness wheels                                (runtime-hazard quotes)

Outputs:
  research/verified_json/retrieval_ablation_129.json
  research/verified_json/multifile_2hop_38.json
  research/verified_json/runtime_hazards_verified.json
  research/verified_json/leaderboard_estimands.json

Usage:
  .venv-harness/Scripts/python.exe scripts/run_verified_experiments.py
  .venv-harness/Scripts/python.exe scripts/run_verified_experiments.py --only ablation,multifile
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import math
import random
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASKS_JSONL = REPO / "kaggle_work" / "gemma-4-developer-agent" / "research" / "competition" / "tasks.jsonl"
SNAP_DIR = REPO / "eval_snapshots"
ENGINE = REPO / "skills" / "swe-toolkit" / "scripts" / "_index.py"
REGIME_A_JSON = REPO / "research" / "paper_eval_outputs" / "paper_experiments.json"
V4_REPRO = REPO / "eval_results" / "t6_results_v4_repro.json"
OUT_DIR = REPO / "research" / "verified_json"

REPOS = ("fastapi", "rich", "requests", "httpx")
BOOT_N = 10_000
BOOT_SEED = 20261111


# --------------------------------------------------------------------------- #
# inputs
# --------------------------------------------------------------------------- #
def load_engine():
    spec = importlib.util.spec_from_file_location("_index_engine", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_tasks() -> list[dict]:
    out = []
    with open(TASKS_JSONL, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def gold_files(patch: str) -> set[str]:
    """Files the gold patch touches, posix-normalised."""
    out = set()
    for ln in patch.splitlines():
        if ln.startswith("+++ b/"):
            p = ln[6:].strip()
            if p and p != "/dev/null":
                out.add(p.replace("\\", "/"))
    return out


def created_files(patch: str) -> set[str]:
    """Files the gold patch creates.

    The competition patches carry no `new file mode` header, so creation is
    signalled by a `@@ -0,0 ...` hunk.
    """
    out, cur = set(), None
    for ln in patch.splitlines():
        if ln.startswith("+++ b/"):
            cur = ln[6:].strip().replace("\\", "/")
        elif ln.startswith("@@ -0,0") and cur:
            out.add(cur)
    return out


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #
def _frac(gold: set[str], ranked: list[str], k: int) -> float:
    return len(gold & set(ranked[:k])) / len(gold) if gold else 0.0


def _any(gold: set[str], ranked: list[str], k: int) -> float:
    return 1.0 if (gold & set(ranked[:k])) else 0.0


def _all(gold: set[str], ranked: list[str], k: int) -> float:
    return 1.0 if gold and gold <= set(ranked[:k]) else 0.0


def bootstrap_ci(values: list[float], n: int = BOOT_N, seed: int = BOOT_SEED) -> list[float]:
    """Task-bootstrap 95% CI (percentile)."""
    if not values:
        return [0.0, 0.0]
    rng = random.Random(seed)
    m = len(values)
    draws = sorted(
        sum(values[rng.randrange(m)] for _ in range(m)) / m for _ in range(n)
    )
    return [round(draws[int(0.025 * n)], 4), round(draws[int(0.975 * n) - 1], 4)]


def wilson(k: int, n: int, z: float = 1.959963985) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def summarise(rows: list[dict], key: str, with_per_task: bool = True) -> dict:
    """rows: [{task, repo, gold_files, ranked}] -> exact recall block."""
    n = len(rows)
    block = {
        "N": n,
        "mean_gold_files": round(sum(len(r["gold_files"]) for r in rows) / n, 2),
        "mean_candidates_returned_at_10": round(
            sum(min(len(r["ranked"]), 10) for r in rows) / n, 2),
    }
    for k in (1, 3, 5, 10):
        mf = [_frac(set(r["gold_files"]), r["ranked"], k) for r in rows]
        an = [_any(set(r["gold_files"]), r["ranked"], k) for r in rows]
        al = [_all(set(r["gold_files"]), r["ranked"], k) for r in rows]
        block[f"@{k}"] = {
            "mean_fraction": {"value": round(sum(mf) / n, 4), "sum": round(sum(mf), 2), "ci": bootstrap_ci(mf)},
            "any_gold": {"value": round(sum(an) / n, 4), "hits": int(sum(an)), "ci": bootstrap_ci(an)},
            "all_gold": {"value": round(sum(al) / n, 4), "hits": int(sum(al)), "ci": bootstrap_ci(al)},
        }
    block["per_task"] = [
        {
            "task": r["task"],
            "repo": r["repo"],
            "gold_n": len(r["gold_files"]),
            "ranked": r["ranked"][:10],
            "mean_fraction_5": round(_frac(set(r["gold_files"]), r["ranked"], 5), 4),
            "any_5": int(_any(set(r["gold_files"]), r["ranked"], 5)),
            "all_5": int(_all(set(r["gold_files"]), r["ranked"], 5)),
            "all_10": int(_all(set(r["gold_files"]), r["ranked"], 10)),
        }
        for r in rows
    ] if with_per_task else []
    return block


def paired_sign_test(a: list[int], b: list[int]) -> dict:
    """Exact two-sided sign test on discordant pairs (a vs b)."""
    up = sum(1 for x, y in zip(a, b) if x > y)
    dn = sum(1 for x, y in zip(a, b) if x < y)
    n = up + dn
    if n == 0:
        return {"discordant_a_gt_b": 0, "discordant_b_gt_a": 0, "p_exact": 1.0}
    tail = sum(math.comb(n, i) for i in range(0, min(up, dn) + 1)) / 2 ** n
    return {
        "discordant_a_gt_b": up,
        "discordant_b_gt_a": dn,
        "p_exact": float(min(1.0, 2 * tail)),
    }


# --------------------------------------------------------------------------- #
# group 1: baselines + v4 component ablation
# --------------------------------------------------------------------------- #
def _scan(root: Path, max_bytes: int = 500 * 1024) -> dict[str, str]:
    """Read every .py file once; used by B0 and B1."""
    out = {}
    for p in root.rglob("*.py"):
        try:
            if p.stat().st_size > max_bytes:
                continue
            out[p.relative_to(root).as_posix()] = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
    return out


def _b0_rank(files: dict[str, str], query: str, idx, top_n: int = 10) -> list[str]:
    """B0: filename/identifier string match only. No AST, no demotion."""
    toks = {t for t in idx.tokenize(query) if len(t) >= 4}
    scored = []
    for fp in files:
        low = fp.lower()
        stem = low.rsplit("/", 1)[-1][:-3]
        hits = sum(1 for t in toks if t in stem or t in low)
        exact = sum(1 for t in toks if t == stem)
        scored.append((hits + 3 * exact, fp))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [fp for sc, fp in scored if sc > 0][:top_n] or [fp for _, fp in scored[:top_n]]


def _b1_rank(files: dict[str, str], query: str, idx, top_n: int = 10) -> list[str]:
    """B1: vanilla file-level BM25 over whole-file text, no test demotion."""
    q = [t for t in idx.tokenize(query) if len(t) >= 3]
    if not q:
        return sorted(files)[:top_n]
    docs = {fp: idx.tokenize(text) for fp, text in files.items()}
    n = len(docs)
    avgdl = (sum(len(d) for d in docs.values()) / n) if n else 1.0
    df = {}
    for d in docs.values():
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log((n - c + 0.5) / (c + 0.5) + 1.0) for t, c in df.items()}
    scored = []
    for fp, d in docs.items():
        tf = {}
        for t in d:
            tf[t] = tf.get(t, 0) + 1
        dl = len(d)
        s = 0.0
        for t in q:
            f = tf.get(t, 0)
            if not f or t not in idf:
                continue
            denom = f + 1.5 * (0.25 + 0.75 * dl / avgdl)
            s += idf[t] * (f * 2.5) / (denom if denom else 1.0)
        scored.append((s, fp))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [fp for _, fp in scored[:top_n]]


def run_ablation(tasks: list[dict], idx) -> dict:
    out_path = OUT_DIR / "retrieval_ablation_129.json"
    t0 = time.time()
    rows = {"B0": [], "B1": [], "B2": [], "B3": []}
    latencies = {"B2": [], "B3": []}

    for i, t in enumerate(tasks, 1):
        tid, repo = t["instance_id"], t["repo"].split("/")[-1]
        root = SNAP_DIR / tid
        gf = sorted(gold_files(t["patch"]))
        issue = t["problem_statement"]
        if not root.exists():
            print(f"[skip] {tid} snapshot missing", flush=True)
            continue
        files = _scan(root)
        rows["B0"].append({"task": tid, "repo": repo, "gold_files": gf, "ranked": _b0_rank(files, issue, idx)})
        rows["B1"].append({"task": tid, "repo": repo, "gold_files": gf, "ranked": _b1_rank(files, issue, idx)})

        # B3: shipped v4 (test demotion ON)
        st = {}
        s3 = time.monotonic()
        _, f3, _ = idx.locate(str(root), issue, 10, stats=st)
        latencies["B3"].append(round(time.monotonic() - s3, 3))
        rows["B3"].append({"task": tid, "repo": repo, "gold_files": gf,
                           "ranked": [x.replace("\\", "/") for x in f3]})

        # B2: same ranker with is_test_path demotion disabled
        original = idx.is_test_path
        try:
            idx.is_test_path = lambda _p: False  # type: ignore[assignment]
            s2 = time.monotonic()
            _, f2, _ = idx.locate(str(root), issue, 10)
            latencies["B2"].append(round(time.monotonic() - s2, 3))
        finally:
            idx.is_test_path = original
        rows["B2"].append({"task": tid, "repo": repo, "gold_files": gf,
                           "ranked": [x.replace("\\", "/") for x in f2]})

        if i % 10 == 0:
            print(f"  [{i}/{len(tasks)}] {time.time() - t0:.0f}s", flush=True)

    block = {}
    for name, rs in rows.items():
        block[name] = {"all": summarise(rs, name)}
        for repo in REPOS:
            sub = [r for r in rs if r["repo"] == repo]
            if sub:
                block[name][repo] = summarise(sub, name, with_per_task=False)

    # within-v4 metric-definition shift (genuinely paired, same run)
    def col(rs, fn, k):
        return [fn(set(r["gold_files"]), r["ranked"], k) for r in rs]

    b3 = rows["B3"]
    shift = {}
    for k in (1, 3, 5, 10):
        an = col(b3, _any, k)
        fr = col(b3, _frac, k)
        shift[f"@{k}"] = {
            "any_gold": round(sum(an) / len(an), 4),
            "mean_fraction": round(sum(fr) / len(fr), 4),
            "gap_pp": round(100 * (sum(an) - sum(fr)) / len(an), 2),
            "tasks_partial_credit": sum(1 for x in fr if 0 < x < 1),
            "pointwise_dominance": all(a >= m for a, m in zip(an, fr)),
            "note": (
                "Any-Gold >= Mean-Fraction pointwise by construction (a task scores 1 on "
                "Any-Gold iff its mean fraction is > 0). The gap is therefore definitional "
                "and no hypothesis test is applicable or reported."
            ),
        }

    # component deltas, paired by task
    deltas = {}
    for lo, hi in (("B0", "B1"), ("B1", "B2"), ("B2", "B3"), ("B1", "B3"), ("B0", "B3")):
        a = [int(_any(set(r["gold_files"]), r["ranked"], 5)) for r in rows[lo]]
        b = [int(_any(set(r["gold_files"]), r["ranked"], 5)) for r in rows[hi]]
        am = [round(_frac(set(r["gold_files"]), r["ranked"], 5), 6) for r in rows[lo]]
        bm = [round(_frac(set(r["gold_files"]), r["ranked"], 5), 6) for r in rows[hi]]
        deltas[f"{lo}->{hi}"] = {
            "any_gold_delta_pp": round(100 * (sum(b) - sum(a)) / len(a), 2),
            "mean_fraction_delta_pp": round(100 * (sum(bm) - sum(am)) / len(am), 2),
            "sign_test_any": paired_sign_test(b, a),
        }

    # Regime A: aggregates only. Recorded as measured; no per-task series exists.
    ra_raw = json.load(open(REGIME_A_JSON, encoding="utf-8"))["experiment1"]
    regime_a = {
        "source": "research/paper_eval_outputs/paper_experiments.json (experiment1)",
        "N": ra_raw["evaluated"],
        "aggregates": {
            m: {
                "R@1_file": ra_raw["summary"]["all"][m]["R@1_file"],
                "R@3_file": ra_raw["summary"]["all"][m]["R@3_file"],
                "R@5_file": ra_raw["summary"]["all"][m]["R@5_file"],
                "R@10_file": ra_raw["summary"]["all"][m]["R@10_file"],
                "MRR_file": ra_raw["summary"]["all"][m]["MRR_file"],
                "latency_ms": ra_raw["summary"]["all"][m]["Latency_ms"],
                "chars": ra_raw["summary"]["all"][m]["Chars"],
            }
            for m in ("M1", "M2", "M3", "M4", "M5")
        },
        "any_gold": None,
        "any_gold_note": (
            "Regime A was recorded in aggregate only. No per-task series exists, so Any-Gold "
            "and Strict All-Gold recall cannot be computed for M1-M5 and are NOT reported."
        ),
        "m3_cap": {
            "exceed": ra_raw["m3_cap_exceed"],
            "total": ra_raw["m3_cap_total"],
            "runs": 3,
            "tasks": ra_raw["evaluated"],
            "pct": round(100 * ra_raw["m3_cap_exceed"] / ra_raw["m3_cap_total"], 2),
            "ci_binomial": wilson(ra_raw["m3_cap_exceed"], ra_raw["m3_cap_total"]),
            "ci_task_clustered_conservative": [
                round(100 * (ra_raw["m3_cap_exceed"] / ra_raw["m3_cap_total"])
                      - 1.959963985 * 100 * math.sqrt(
                          (ra_raw["m3_cap_exceed"] / ra_raw["m3_cap_total"])
                          * (1 - ra_raw["m3_cap_exceed"] / ra_raw["m3_cap_total"]) / 129), 2),
                round(100 * (ra_raw["m3_cap_exceed"] / ra_raw["m3_cap_total"])
                      + 1.959963985 * 100 * math.sqrt(
                          (ra_raw["m3_cap_exceed"] / ra_raw["m3_cap_total"])
                          * (1 - ra_raw["m3_cap_exceed"] / ra_raw["m3_cap_total"]) / 129), 2),
            ],
            "note": (
                "387 = 3 repeated runs x 129 tasks. Per-task counts are not retained, so the "
                "task-clustered interval is bounded conservatively at design effect = 3 (effective n = 129)."
            ),
        },
    }

    payload = {
        "generator": "scripts/run_verified_experiments.py",
        "group": "baselines_and_v4_component_ablation",
        "variants": {
            "B0": "filename/identifier string match, live repo .py files, no AST, no demotion",
            "B1": "vanilla file-level BM25, no /tests/ demotion",
            "B2": "v4 AST ranker with /tests/ demotion DISABLED",
            "B3": "v4 shipped (AST ranker + /tests/ demotion)",
        },
        "N": len(rows["B3"]),
        "results": block,
        "component_deltas_paired": deltas,
        "within_v4_metric_shift": shift,
        "regime_a": regime_a,
        "median_seconds": {k: (statistics.median(v) if v else None) for k, v in latencies.items()},
        "wall_seconds": round(time.time() - t0, 1),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] {out_path.name}: B3 any@5={block['B3']['all']['@5']['any_gold']['value']} "
          f"mf@5={block['B3']['all']['@5']['mean_fraction']['value']}", flush=True)
    return payload


# --------------------------------------------------------------------------- #
# group 2: multi-file audit + budget-matched 2-hop
# --------------------------------------------------------------------------- #
NON_SOURCE_PREFIXES = ("docs/", "docs_src/", "examples/", "scripts/", "benchmark", "tests/", "test/")


def _import_resolver(idx):
    """Return (forward_imports, reverse_importers) for one repo root."""

    def mod_candidates(mod: str) -> list[Path]:
        parts = mod.split(".")
        out = []
        for i in range(len(parts), 0, -1):
            base = Path(*parts[:i])
            out += [base.with_suffix(".py"), base / "__init__.py"]
        return out

    def resolve(fp: Path, root: Path) -> set[str]:
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            return set()
        out, pkg = set(), fp.parent.relative_to(root)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    out |= set(mod_candidates(a.name))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    up = pkg
                    for _ in range(node.level - 1):
                        up = up.parent
                    base = up / Path(*(node.module.split(".") if node.module else []))
                    out |= {base.with_suffix(".py"), base / "__init__.py"}
                    for a in node.names:
                        out.add((base / a.name).with_suffix(".py"))
                elif node.module:
                    out |= set(mod_candidates(node.module))
                    for a in node.names:
                        out |= set(mod_candidates(f"{node.module}.{a.name}"))
        return {p.as_posix() for p in out}

    def build(root: Path) -> dict[str, set[str]]:
        graph = {}
        for p in root.rglob("*.py"):
            rel = p.relative_to(root).as_posix()
            graph[rel] = {x for x in resolve(p, root) if (root / x).exists()}
        return graph

    return build


def run_multifile(tasks: list[dict], idx, v4_rows: list[dict] | None = None) -> dict:
    out_path = OUT_DIR / "multifile_2hop_38.json"
    t0 = time.time()
    build_graph = _import_resolver(idx)

    # reuse the freshly produced v4 rankings, so both outputs share one producer
    if v4_rows is None:
        ab_path = OUT_DIR / "retrieval_ablation_129.json"
        if not ab_path.exists():
            raise SystemExit("run --only ablation first: retrieval_ablation_129.json missing")
        ab = json.loads(ab_path.read_text(encoding="utf-8"))
        by_id_t = {t["instance_id"]: t for t in tasks}
        v4_rows = [
            {"task": r["task"], "repo": r["repo"],
             "gold_files": sorted(gold_files(by_id_t[r["task"]]["patch"])),
             "ranked": r["ranked"]}
            for r in ab["results"]["B3"]["all"]["per_task"]
        ]
    by_id = {t["instance_id"]: t for t in tasks}

    multi = [r for r in v4_rows if len(set(r["gold_files"])) > 1]
    print(f"  multi-file tasks: {len(multi)}", flush=True)

    def coupled_seeds(root: Path, graph: dict[str, set[str]], seeds: list[str], files: dict[str, str],
                      issue: str, want: int) -> list[str]:
        """Unvisited in-repo .py files imported by, or importing, the seed files."""
        forward, backward = [], []
        seedset = set(seeds)
        for s in seeds:
            for f in sorted(graph.get(s, ())):
                if f not in seedset:
                    forward.append(f)
        for f, deps in graph.items():
            if f in seedset:
                continue
            if any(s in deps for s in seeds):
                backward.append(f)
        toks = {t for t in idx.tokenize(issue) if len(t) >= 4}

        def lex(f: str) -> int:
            stem = f.rsplit("/", 1)[-1]
            return sum(1 for t in toks if t in stem or t in f)

        forward = sorted(set(forward), key=lambda f: (-lex(f), f))
        backward = sorted(set(backward), key=lambda f: (-lex(f), f))
        return (forward + [f for f in backward if f not in forward])[:want]

    rows = []
    lat = {"control": [], "hop": [], "graph_build": []}
    for i, r in enumerate(multi, 1):
        tid = r["task"]
        root = SNAP_DIR / tid
        if not root.exists():
            continue
        gf = set(r["gold_files"])
        issue = by_id[tid]["problem_statement"]
        files = _scan(root)

        tg = time.monotonic()
        graph = build_graph(root)
        lat["graph_build"].append(round(time.monotonic() - tg, 2))

        tc = time.monotonic()
        _, ctrl, _ = idx.locate(str(root), issue, 10)
        ctrl = [x.replace("\\", "/") for x in ctrl]
        lat["control"].append(round(time.monotonic() - tc, 2))

        th = time.monotonic()
        hop5 = ctrl[:3] + coupled_seeds(root, graph, ctrl[:1], files, issue, 2)
        hop10 = ctrl[:6] + coupled_seeds(root, graph, ctrl[:2], files, issue, 4)
        hop5 = list(dict.fromkeys(hop5))[:5]
        hop10 = list(dict.fromkeys(hop10))[:10]
        lat["hop"].append(round(time.monotonic() - th, 2))

        rec = {"task": tid, "repo": r["repo"], "gold_files": sorted(gf), "gold_n": len(gf)}
        for k, c_list, h_list in ((5, ctrl[:5], hop5), (10, ctrl[:10], hop10)):
            rec[f"k{k}"] = {
                "control": {"any": int(_any(gf, c_list, k)), "all": int(_all(gf, c_list, k)),
                            "mf": round(_frac(gf, c_list, k), 4), "files": c_list},
                "hop": {"any": int(_any(gf, h_list, k)), "all": int(_all(gf, h_list, k)),
                        "mf": round(_frac(gf, h_list, k), 4), "files": h_list},
            }
            rec[f"k{k}"]["transition"] = (
                "fail->success" if rec[f"k{k}"]["control"]["all"] == 0 and rec[f"k{k}"]["hop"]["all"] == 1
                else "success->fail" if rec[f"k{k}"]["control"]["all"] == 1 and rec[f"k{k}"]["hop"]["all"] == 0
                else "none"
            )
        rows.append(rec)
        if i % 5 == 0:
            print(f"  [{i}/{len(multi)}] {time.time() - t0:.0f}s", flush=True)

    def agg(sel: list[dict], k: int, arm: str) -> dict:
        n = len(sel)
        an = sum(r[f"k{k}"][arm]["any"] for r in sel)
        al = sum(r[f"k{k}"][arm]["all"] for r in sel)
        mf = sum(r[f"k{k}"][arm]["mf"] for r in sel) / n
        return {
            "N": n,
            f"any_gold@{k}": {"hits": an, "value": round(an / n, 4), "wilson": wilson(an, n)},
            f"all_gold@{k}": {"hits": al, "value": round(al / n, 4), "wilson": wilson(al, n)},
            f"mean_fraction@{k}": round(mf, 4),
        }

    source_only = [r for r in rows if not any(f.startswith(NON_SOURCE_PREFIXES) for f in r["gold_files"])]
    buckets = {}
    for label, sel in (("all_multi", rows), ("source_only_multi", source_only)):
        buckets[label] = {
            "N": len(sel),
            "pct_of_129": round(100 * len(sel) / 129, 1),
            "gold_n_gt_5_infeasible_at_k5": sum(1 for r in sel if r["gold_n"] > 5),
            "control": {f"k{k}": agg(sel, k, "control") for k in (5, 10)},
            "hop": {f"k{k}": agg(sel, k, "hop") for k in (5, 10)},
        }
    for k in (5, 10):
        for arm in ("any", "all"):
            a = [r[f"k{k}"]["control"][arm] for r in rows]
            b = [r[f"k{k}"]["hop"][arm] for r in rows]
            buckets["all_multi"].setdefault("paired", {}).setdefault(f"k{k}", {})[arm] = paired_sign_test(b, a)
        buckets["all_multi"].setdefault("transitions", {})[f"k{k}"] = {
            t: sum(1 for r in rows if r[f"k{k}"]["transition"] == t)
            for t in ("fail->success", "success->fail", "none")
        }

    # conditional structure of the gold sets (all 129)
    def cond(v4rows, bucket_fn) -> dict:
        out = {}
        for r in v4rows:
            gf, rk = set(r["gold_files"]), r["ranked"]
            key = bucket_fn(len(gf))
            d = out.setdefault(key, {"N": 0, "any5": 0, "all5": 0})
            d["N"] += 1
            d["any5"] += int(_any(gf, rk, 5))
            d["all5"] += int(_all(gf, rk, 5))
        for d in out.values():
            d["p_all_given_any"] = round(d["all5"] / d["any5"], 3) if d["any5"] else None
        return out

    total_hop = [g + h for g, h in zip(lat["graph_build"], lat["hop"])]
    payload = {
        "generator": "scripts/run_verified_experiments.py",
        "group": "multifile_audit_and_budget_matched_2hop",
        "definition": {
            "control": "single-pass locate(), top-k",
            "hop": "k=5: top-3 locate + 2 coupled files from f1; k=10: top-6 locate + 4 coupled files from f1,f2",
            "coupled": "in-repo .py files imported by the seed file, then files importing the seed file, ranked by lexical overlap with the issue",
            "source_only": "multi-file task whose gold set contains no docs/, docs_src/, examples/, scripts/, tests/ path",
        },
        "gold_set_structure_all_129": cond(
            v4_rows, lambda n: "1" if n == 1 else ("2" if n == 2 else ("3-5" if n <= 5 else ">5"))
        ),
        "buckets": buckets,
        "median_seconds": {
            "control_locate": (statistics.median(lat["control"]) if lat["control"] else None),
            "graph_build_once": (statistics.median(lat["graph_build"]) if lat["graph_build"] else None),
            "hop_expansion": (statistics.median(lat["hop"]) if lat["hop"] else None),
            "hop_total": (statistics.median(total_hop) if total_hop else None),
            "control_plus_graph": (
                round(statistics.median(lat["control"]) + statistics.median(lat["graph_build"]), 2)
                if lat["control"] and lat["graph_build"] else None
            ),
        },
        "per_task": rows,
        "wall_seconds": round(time.time() - t0, 1),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] {out_path.name}: multi={buckets['all_multi']['N']} "
          f"source_only={buckets['source_only_multi']['N']}", flush=True)
    return payload


# --------------------------------------------------------------------------- #
# group 3: runtime hazards
# --------------------------------------------------------------------------- #
SITE_QUOTES = {
    "site1": {
        "component": "google-adk",
        "path": "google/adk/apps/_configs.py",
        "line": 70,
        "needle": "token_threshold",
        "label": "Source-Verified (value from docs)",
    },
    "site2": {
        "component": "vllm",
        "path": "vllm/entrypoints/chat_utils.py",
        "line": 1512,
        "needle": "reasoning",
        "label": "Inherited (vLLM wheel not installed locally)",
    },
    "site2_patch": {
        "component": "adk-submission",
        "path": "adk_submission/resolvers/generation.py",
        "line": 70,
        "needle": "reasoning",
        "label": "Mitigated in Scored Stack",
    },
    "site3": {
        "component": "vllm",
        "path": "vllm/v1/sample/logits_processor/builtin.py",
        "line": 550,
        "needle": "1e9",
        "label": "Inherited (vLLM wheel not installed locally)",
    },
    "site4": {
        "component": "swegemma",
        "path": "swegemma/harness/agent_runner.py",
        "line": 1057,
        "needle": "git",
        "label": "Replay-Verified",
    },
    "site5": {
        "component": "google-adk",
        "path": "google/adk/tools/skill_toolset.py",
        "line": 61,
        "needle": "_DEFAULT_SKILL_SYSTEM_INSTRUCTION",
        "label": "Source-Verified",
    },
    "site6": {
        "component": "swegemma",
        "path": "swegemma/harness/verification.py",
        "line": 628,
        "needle": "no:anyio",
        "label": "Exposure Count",
    },
}


def _site_root() -> Path:
    return REPO / ".venv-harness" / "Lib" / "site-packages"


def _read_site(site: Path, rel: str) -> list[str] | None:
    p = site / rel
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8", errors="replace").splitlines()


def _pkg_version(site: Path, dist: str) -> str | None:
    for d in site.glob(f"{dist.replace('-', '_')}-*.dist-info"):
        return d.name.split("-")[1].replace(".dist", "")
    return None


def run_hazards(tasks: list[dict]) -> dict:
    out_path = OUT_DIR / "runtime_hazards_verified.json"
    site = _site_root()
    sites = {}
    for key, spec in SITE_QUOTES.items():
        lines = _read_site(site, spec["path"])
        if lines is None:
            sites[key] = {**spec, "present": False}
            continue
        idx0 = spec["line"] - 1
        window = lines[max(0, idx0 - 3): idx0 + 4]
        sites[key] = {
            **spec,
            "present": True,
            "quote": "\n".join(window),
            "line_matches_needle": spec["needle"].lower() in "\n".join(window).lower(),
            "file_lines": len(lines),
        }

    versions = {
        d: _pkg_version(site, d)
        for d in ("google_adk", "vllm", "swegemma", "adk_submission", "adk-eval-core")
    }

    # --- Site 4: .gitignore exposure on the 11 file-creating tasks
    creating = [(t["instance_id"], sorted(created_files(t["patch"]))) for t in tasks if created_files(t["patch"])]
    ign = {"tasks": len(creating), "files": 0, "ignored": [], "scratch_hits": {}}
    scratch = ["/workspace/skills/swe-toolkit/scripts/swe.py", ".pytest_cache/v/cache/lastfailed"]
    for tid, files in creating:
        root = SNAP_DIR / tid
        for f in files:
            ign["files"] += 1
            if not root.exists():
                continue
            r = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", f], capture_output=True)
            if r.returncode == 0:
                ign["ignored"].append({"task": tid, "file": f})
        for s in scratch:
            probe = s.replace("/workspace/", "")
            r = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", probe], capture_output=True)
            ign["scratch_hits"].setdefault(s, {"tested": 0, "ignored": 0})
            ign["scratch_hits"][s]["tested"] += 1
            ign["scratch_hits"][s]["ignored"] += 1 if r.returncode == 0 else 0
    ign["tasks_detail"] = [{"task": t, "created": f} for t, f in creating]
    ign["ignored_count"] = len(ign["ignored"])

    # --- Site 6: bare-pytest exposure under three exact, non-interchangeable definitions
    #
    # The legacy audit reported "27 of 67 (40.3%)".  That number is 22 + 5: it adds the
    # five `dirty_equals` tasks to a total that already contains them.  The three
    # definitions below are each computed from a different population, so they must never
    # be combined.
    fastapi = [t for t in tasks if t["repo"] == "fastapi/fastapi"]
    plugins = ("inline_snapshot", "dirty_equals")
    direct, touched, tree_all, anyio_only = [], [], [], []
    for t in fastapi:
        tid, tp = t["instance_id"], t["test_patch"]
        d = {p for p in plugins if re.search(rf"\b(?:import|from)\s+{p}\b", tp)}
        has_anyio = bool(re.search(r"\b(?:import|from)\s+anyio\b", tp))
        if d:
            direct.append({"task": tid, "plugins": sorted(d), "anyio": has_anyio})
        elif has_anyio:
            anyio_only.append(tid)

        root = SNAP_DIR / tid

        # definition B: only the test files this task's own test_patch touches
        hits_b = set()
        if root.exists():
            for rel in re.findall(r"^\+\+\+ b/(.+)$", tp, re.M):
                p = root / rel
                if not p.is_file():
                    continue
                try:
                    head = p.read_text(encoding="utf-8", errors="ignore")[:8000]
                except Exception:
                    continue
                for plug in plugins:
                    if re.search(rf"^[ \t]*(?:from[ \t]+{plug}\b|import[ \t]+{plug}\b)", head, re.M):
                        hits_b.add(plug)
        if hits_b:
            touched.append({"task": tid, "plugins": sorted(hits_b)})

        # definition C: the whole repository tests/ tree at the base commit
        hits_c = set()
        if root.exists():
            for p in root.rglob("*.py"):
                rel = p.relative_to(root).as_posix()
                if not ("/tests/" in f"/{rel}" or rel.startswith("tests/") or p.name.startswith("test_")):
                    continue
                try:
                    head = p.read_text(encoding="utf-8", errors="ignore")[:8000]
                except Exception:
                    continue
                for plug in plugins:
                    if re.search(rf"^[ \t]*(?:from[ \t]+{plug}\b|import[ \t]+{plug}\b)", head, re.M):
                        hits_c.add(plug)
                if hits_c:
                    break
        if hits_c:
            tree_all.append({"task": tid, "plugins": sorted(hits_c)})

    n_fa = len(fastapi)
    n_plugin = len(direct)
    n_plus_anyio = n_plugin + len(anyio_only)
    site6 = {
        "fastapi_tasks": n_fa,
        "def_a_test_patch_direct": {
            "count": n_plugin,
            "pct": round(100 * n_plugin / n_fa, 1),
            "definition": "the gold test_patch imports inline_snapshot or dirty_equals",
            "inline_snapshot_any": sum(1 for x in direct if "inline_snapshot" in x["plugins"]),
            "dirty_equals_any": sum(1 for x in direct if "dirty_equals" in x["plugins"]),
            "both": sum(1 for x in direct if len(x["plugins"]) == 2),
            "task_ids": [x["task"] for x in direct],
        },
        "def_a_plus_anyio": {
            "count": n_plus_anyio,
            "pct": round(100 * n_plus_anyio / n_fa, 1),
            "definition": ("definition A plus the tasks whose test_patch imports anyio and "
                           "therefore needs -p no:anyio"),
            "anyio_only_count": len(anyio_only),
            "anyio_only_task_ids": anyio_only,
        },
        "def_b_touched_test_files": {
            "count": len(touched),
            "pct": round(100 * len(touched) / n_fa, 1),
            "definition": ("the base-commit version of the test files this task's own "
                           "test_patch touches imports either plugin"),
            "task_ids": [x["task"] for x in touched],
        },
        "def_c_repo_tests_tree": {
            "count": len(tree_all),
            "pct": round(100 * len(tree_all) / n_fa, 1),
            "definition": ("the repository's whole tests/ tree at the base commit imports "
                           "either plugin (a repository property, not a task property)"),
        },
        "legacy_27_arithmetic": {
            "legacy_value": 27,
            "def_a_plus_anyio": n_plus_anyio,
            "dirty_equals_any": sum(1 for x in direct if "dirty_equals" in x["plugins"]),
            "note": ("27 = definition A+anyio (22) plus the 5 tasks that import dirty_equals, "
                     "which are already inside that total, so the overlap is double-counted. "
                     "18 + 5 + 1 = 24, minus the 2 tasks that import both plugins, gives 22."),
        },
        "note": ("Bare `pytest` inside /workspace only. The official grader installs wheels "
                 "(verification.py:387) and passes -p no:anyio (:628), so none of these "
                 "counts is a task failure. This file is the reproducible source; the three "
                 "definitions are not interchangeable."),
    }

    # --- Site 5: SkillToolset preamble size, measured by AST (implicit concat)
    site5 = {"preamble_chars": None, "preamble_words": None, "preamble_tokens_est": None,
             "label": "Source-Verified", "present": False}
    st_path = site / "google/adk/tools/skill_toolset.py"
    if st_path.exists():
        tree = ast.parse(st_path.read_text(encoding="utf-8", errors="replace"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_DEFAULT_SKILL_SYSTEM_INSTRUCTION"
                for t in node.targets
            ):
                try:
                    preamble = ast.literal_eval(node.value)
                except Exception:
                    preamble = ""
                site5.update({
                    "preamble_chars": len(preamble),
                    "preamble_words": len(preamble.split()),
                    "preamble_tokens_est": round(len(preamble) / 4.0),
                    "first_line": preamble.splitlines()[0] if preamble else "",
                    "present": True,
                })
                break

    # --- Site 1: compaction constants from the audited trajectory
    curve = json.load(open(REPO / "research" / "novelty_audits" / "adk_compaction_curve.json", encoding="utf-8"))
    const = curve.get("compaction_constants", {})
    traj = curve.get("turn_to_compaction_trajectories", {})
    first_turns = {
        name: cfg.get("first_compaction_turn")
        for name, cfg in traj.items() if isinstance(cfg, dict)
    }
    site1 = {
        "token_threshold": const.get("token_threshold"),
        "compaction_interval": const.get("compaction_interval"),
        "event_retention": const.get("event_retention"),
        "overlap": const.get("overlap"),
        "first_compaction_turn_by_config": first_turns,
        "first_compaction_turn_min": min([v for v in first_turns.values() if v]),
        "first_compaction_turn_max": max([v for v in first_turns.values() if v]),
        "config3_turn1_tokens": traj.get("config_3_skilltoolset_10tools", {}).get("initial_tokens"),
        "config2_turn1_tokens": traj.get("config_2_baseline_9tools", {}).get("initial_tokens"),
        "skilltoolset_turn1_marginal_tokens": (
            (traj.get("config_3_skilltoolset_10tools", {}).get("initial_tokens") or 0)
            - (traj.get("config_2_baseline_9tools", {}).get("initial_tokens") or 0)
        ),
        "skill_instruction_consequence": curve.get(
            "skill_toolset_hidden_instruction_audit", {}).get("consequence"),
        "label": "Source-Verified (constants from HARNESS_README §7.2; turns from replay audit)",
    }

    # --- Site 2: confirm the mitigation is installed at import time
    site2_mit = {"patch_defined": False, "install_calls": 0,
                 "path": "adk_submission/resolvers/generation.py",
                 "label": "Mitigated in Scored Stack"}
    gen_path = site / "adk_submission/resolvers/generation.py"
    if gen_path.exists():
        src_lines = gen_path.read_text(encoding="utf-8", errors="replace").splitlines()
        site2_mit["patch_defined"] = any(
            ln.startswith("def install_litellm_reasoning_patch") for ln in src_lines)
        site2_mit["install_calls"] = sum(
            1 for ln in src_lines if ln.strip() == "install_litellm_reasoning_patch()")
        site2_mit["mirror_line"] = next(
            (i + 1 for i, ln in enumerate(src_lines) if 'msg["reasoning"] = rc' in ln), None)
        site2_mit["defined_at_line"] = next(
            (i + 1 for i, ln in enumerate(src_lines)
             if ln.startswith("def install_litellm_reasoning_patch")), None)

    payload = {
        "generator": "scripts/run_verified_experiments.py",
        "group": "runtime_hazards",
        "package_versions": versions,
        "sites": sites,
        "site1_compaction": site1,
        "site2_mitigation": site2_mit,
        "site4_gitignore": ign,
        "site5_skilltoolset": site5,
        "site6_bare_pytest": site6,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] {out_path.name}: ignored={ign['ignored_count']}/{ign['files']} "
          f"site6(A)={site6['def_a_test_patch_direct']['count']} "
          f"site6(A+anyio)={site6['def_a_plus_anyio']['count']} "
          f"site6(B)={site6['def_b_touched_test_files']['count']} "
          f"site6(C)={site6['def_c_repo_tests_tree']['count']}/{site6['fastapi_tasks']}",
          flush=True)
    return payload


# --------------------------------------------------------------------------- #
# group 4: leaderboard estimands
# --------------------------------------------------------------------------- #
RUNS = [
    ("exp01", "56793672", 31, 0.05, "2 agents, 4m cap", "2026-10-03"),
    ("exp02", "56812498", 31, 0.08, "unified prompt", "2026-10-04"),
    ("exp03", "57037122", 31, 0.17, "exp05 replica", "2026-10-10"),
    ("exp05", "57553805", 31, 0.20, "git add -N -f gate", "2026-10-23"),
    ("exp08", "57618114", 31, 0.17, "contract prompt (+554 chars)", "2026-10-25"),
    ("exp10", "57654236", 31, 0.17, "6 tools, lean", "2026-10-26"),
    ("exp11_fb", "57697341", 31, 0.13, "E4B bundle -> 31B fallback", "2026-10-27"),
    ("exp12", "57736284", 31, 0.17, "6 tools, 9m cap", "2026-10-28"),
    ("exp11_gen", "57777888", 4, 0.06, "genuine E4B", "2026-10-29"),
    ("e4b-v2", "57806053", 4, 0.05, "E4B imperative, t=0.1", "2026-10-30"),
    ("E0_ctrl", "57836949", 31, 0.17, "byte-identical exp05", "2026-10-31"),
    ("e4b_v4", "57889741", 4, 0.05, "E4B + swe-toolkit", "2026-11-02"),
    ("exp14", "57933618", 31, 0.15, "31B + SkillToolset", "2026-11-03"),
    ("exp_samp", "58096981", 31, 0.13, "model-card sampling", "2026-11-07"),
    ("exp_thk", "58149803", 31, None, "thinking_budget 1024 (unscored)", "2026-11-09"),
    ("exp15", "58183079", 31, 0.13, "thinking_budget 8192, 6 tools", "2026-11-10"),
]


def run_leaderboard() -> dict:
    out_path = OUT_DIR / "leaderboard_estimands.json"
    rows = []
    for name, ref, scale, score, note, date in RUNS:
        k = None if score is None else int(round(score * 58))
        rows.append({
            "run": name, "ref": ref, "scale_b": scale,
            "displayed_score": score,
            "k_of_58": k,
            "exact_fraction": (round(k / 58, 4) if k is not None else None),
            "mechanism": note, "date": date,
        })
    scored31 = [r for r in rows if r["scale_b"] == 31 and r["k_of_58"] is not None]
    by_name = {r["run"]: r for r in rows}
    five_names = ["exp05", "exp03", "exp08", "exp10", "exp12"]
    five = [by_name[n]["k_of_58"] for n in five_names]
    mean5 = sum(five) / len(five)
    sd5 = statistics.stdev(five)
    six = five + [by_name["E0_ctrl"]["k_of_58"]]
    sd6 = statistics.stdev(six)
    exp05_k = by_name["exp05"]["k_of_58"]
    e0_k = by_name["E0_ctrl"]["k_of_58"]
    repeat_shift = abs(exp05_k - e0_k)
    e4b_k = sorted({r["k_of_58"] for r in rows
                    if r["scale_b"] == 4 and r["k_of_58"] is not None})

    # chi-square 95% CI on sigma with 4 df
    chi_lo, chi_hi = 0.484, 11.143  # chi2.ppf(0.975,4), chi2.ppf(0.025,4)
    n = len(five)
    ci_sigma = [round(sd5 * math.sqrt((n - 1) / chi_hi), 3), round(sd5 * math.sqrt((n - 1) / chi_lo), 3)]

    p = mean5 / 58
    se_split = math.sqrt(p * (1 - p) / 58)
    z = 1.959963985 + 0.841621234  # alpha .05 two-sided, 80% power
    mde_paired = z * math.sqrt(2) * sd5
    mde_cross = z * math.sqrt(2) * se_split * 58
    mde_single = z * se_split * 58

    payload = {
        "generator": "scripts/run_verified_experiments.py",
        "group": "leaderboard_estimands",
        "split_size": 58,
        "runs": rows,
        "estimand_rows": [
            {
                "row": 1,
                "name": "identical-code repeat pair on fixed 58 tasks",
                "exp05_k": exp05_k, "e0_k": e0_k,
                "observed_shift_tasks": repeat_shift,
                "observed_shift_pp": round(100 * repeat_shift / 58, 2),
                "note": "exp05 is not resolvably different from exp03 (also 10/58).",
            },
            {
                "row": 2,
                "name": "5 near-baseline 31B bundles",
                "counts": five,
                "mean_tasks": round(mean5, 2),
                "mean_rate": round(p, 4),
                "sd_tasks": round(sd5, 3),
                "df": 4,
                "sd_ci95": ci_sigma,
                "mde_two_run_point_tasks": round(mde_paired, 2),
                "mde_two_run_upper_tasks": round(z * math.sqrt(2) * ci_sigma[1], 2),
            },
            {
                "row": 3,
                "name": "public-to-hidden split sampling uncertainty",
                "se_split_tasks": round(se_split * 58, 2),
                "se_split_pp": round(100 * se_split, 2),
                "se_two_independent_tasks": round(math.sqrt(2) * se_split * 58, 2),
                "se_two_independent_pp": round(100 * math.sqrt(2) * se_split, 2),
                "mde_single_vs_reference_tasks": round(mde_single, 2),
                "mde_two_independent_tasks": round(mde_cross, 2),
            },
        ],
        "sd_if_e0_included": {
            "counts": six, "sd_tasks": round(sd6, 3),
            "note": f"including the byte-identical control raises n to 6 and lowers SD to {sd6:.3f}",
        },
        "ledger_summary": {
            "n_runs": len(rows),
            "scored_31b": len(scored31),
            "scored_e4b": sum(1 for r in rows
                              if r["scale_b"] == 4 and r["k_of_58"] is not None),
            "unscored": sum(1 for r in rows if r["k_of_58"] is None),
            "e4b_k_values": e4b_k,
            "e4b_k_min": min(e4b_k) if e4b_k else None,
            "e4b_k_max": max(e4b_k) if e4b_k else None,
        },
        "scored_31b_runs": len(scored31),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] {out_path.name}: mean={mean5} sd={sd5:.3f} se_split={se_split*58:.2f}", flush=True)
    return payload


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="ablation,multifile,hazards,leaderboard")
    args = ap.parse_args()
    groups = {g.strip() for g in args.only.split(",") if g.strip()}

    tasks = load_tasks()
    print(f"tasks={len(tasks)} snapshots={sum(1 for t in tasks if (SNAP_DIR / t['instance_id']).exists())}")
    idx = load_engine()

    v4_rows = None
    if "ablation" in groups:
        print("== group 1: baselines + v4 ablation ==", flush=True)
        ab = run_ablation(tasks, idx)
        by_id = {t["instance_id"]: t for t in tasks}
        v4_rows = [
            {"task": r["task"], "repo": r["repo"],
             "gold_files": sorted(gold_files(by_id[r["task"]]["patch"])),
             "ranked": r["ranked"]}
            for r in ab["results"]["B3"]["all"]["per_task"]
        ]
        print(f"  reconstructed {len(v4_rows)} v4 rows for the multi-file group", flush=True)
    if "multifile" in groups:
        print("== group 2: multi-file audit + 2-hop ==", flush=True)
        run_multifile(tasks, idx, v4_rows)
    if "hazards" in groups:
        print("== group 3: runtime hazards ==", flush=True)
        run_hazards(tasks)
    if "leaderboard" in groups:
        print("== group 4: leaderboard estimands ==", flush=True)
        run_leaderboard()
    return 0


if __name__ == "__main__":
    sys.exit(main())

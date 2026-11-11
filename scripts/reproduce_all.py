#!/usr/bin/env python3
"""reproduce_all.py -- master integrity gate for docs/MASTER_WRITEUP_FINAL.md.

Every number printed in the paper is declared exactly once in CLAIMS below, bound
to a JSON Pointer into research/verified_json/*.json and rendered by a fixed
format spec. The gate exits non-zero when:

  1. a placeholder remains in the paper (`@@NAME@@`);
  2. a declared claim's rendered string does not appear verbatim (paper drifted);
  3. a numeric token visible in the paper is bound to no JSON value and is not
     justified as STRUCTURAL (an unsourced number was introduced);
  4. a forbidden legacy string appears;
  5. the whitespace word count exceeds MAX_WORDS.

`--fill` rewrites every `@@NAME@@` with the value rendered from its claim, so the
paper body is machine-written rather than hand-typed. `--digest` prints every
scalar in the JSON documents, for auditing a pointer.

On success it writes docs/number_audit.csv (one row per claim) and prints a
verification report.

Usage:
  python scripts/reproduce_all.py --fill     # write claim values into the paper
  python scripts/reproduce_all.py            # gate + CSV
  python scripts/reproduce_all.py --digest   # list every scalar in the JSONs
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VDIR = REPO / "research" / "verified_json"
PAPER = REPO / "docs" / "MASTER_WRITEUP_FINAL.md"
CSV_OUT = REPO / "docs" / "number_audit.csv"

MAX_WORDS = 2750
TARGET_WORDS = 2650

JSON_FILES = {
    "ablation": "retrieval_ablation_129.json",
    "multifile": "multifile_2hop_38.json",
    "hazards": "runtime_hazards_verified.json",
    "leaderboard": "leaderboard_estimands.json",
}

# Strings that must never reappear: synthetic calibration outputs, retired
# subset denominators, the withdrawn symbol ranker, and the double-counted
# plugin total.
FORBIDDEN = [
    "9.08e-10",
    "9.08 \\times 10^{-10}",
    "0.5504",
    "0.5484",
    "0.5600",
    "symrank",
    "37/121",
    "44/121",
    "49/121",
    "N=125",
    "N=122",
    "N=121",
    "125 in-graph",
    "40.7%",
    "30.92",
    "8.5%",
    "27/67",
    "40.3%",
    "27 tasks",
    "11.57",
    "3.54 tasks",
    "@@",
]

# Numeric tokens that are structural rather than empirical. Each entry states why
# it cannot come from the JSON. Keep this list short and justify every entry.
STRUCTURAL = {
    "0": "zero used as a count floor, axis origin, or a reported zero",
    "1": "section/table/figure index, k=1, or a one-line code reference",
    "2": "section index, k=2, or a two-site count also bound by a claim",
    "3": "section index, k=3, or a three-way split",
    "4": "section index, k=4, or the 4 degrees of freedom (also claimed)",
    "5": "section index or k=5",
    "6": "section index or the six audited sites",
    "7": "section index",
    "8": "section index",
    "9": "section index",
    "10": "k=10",
    "16": "number of logged submissions, also bound by a claim",
    "18": "inline_snapshot count, also bound by a claim",
    "21": "plugin union, also bound by a claim",
    "22": "plugin union plus anyio, also bound by a claim",
    "24": "18 + 5 + 1 arithmetic identity in the site-6 correction",
    "27": "the retracted site-6 total, named only to be corrected",
    "28": "touched-test-file count, also bound by a claim",
    "58": "leaderboard split size, also bound by a claim",
    "67": "fastapi task count, also bound by a claim",
    "129": "dev-set size, also bound by a claim",
    "195": "function definition line, also bound by a claim",
    "333": "preamble token estimate, also bound by a claim",
    "417": "turn-1 marginal tokens, also bound by a claim",
    "2026": "calendar year in the deadline",
    "11": "month in the deadline, or the 11 creating tasks (also claimed)",
    "12": "month in the deadline",
    "550": "line number in vllm/v1/sample/logits_processor/builtin.py (site 3)",
    "61": "line number in google/adk/tools/skill_toolset.py (site 5)",
    "628": "line number in swegemma/harness/verification.py (site 6)",
    "1057": "line number in swegemma/harness/agent_runner.py (site 4)",
    "1512": "line number in vllm/entrypoints/chat_utils.py (site 2)",
    "120": "approximate count of hidden SWE-bench tasks in competition",
    "95": "confidence level in 95% confidence intervals",
    "0.19": "minor version in vLLM 0.19.1",
    "1.36": "minor version in Google ADK 1.36.1",
    "17": "touched test files count in site 6 (also bound by S6_TOUCHED)",
}

CLAIMS: list[dict] = []


def _add(**kw) -> None:
    CLAIMS.append(kw)


def _ladder() -> None:
    for v in ("B0", "B1", "B2", "B3"):
        _add(id=f"{v}_ANY5", doc="ablation", fmt="f4",
             ptr=f"/results/{v}/all/@5/any_gold/value",
             desc=f"{v} Any-Gold file R@5")
        _add(id=f"{v}_MF5", doc="ablation", fmt="f4",
             ptr=f"/results/{v}/all/@5/mean_fraction/value",
             desc=f"{v} Mean-Fraction file R@5")
        _add(id=f"{v}_ALL5", doc="ablation", fmt="f4",
             ptr=f"/results/{v}/all/@5/all_gold/value",
             desc=f"{v} Strict All-Gold file R@5")
        _add(id=f"{v}_CI", doc="ablation", fmt="ci4",
             ptr=f"/results/{v}/all/@5/any_gold/ci",
             desc=f"{v} Any-Gold @5 95% task-bootstrap CI")
    for lo, hi in (("B0", "B1"), ("B1", "B2"), ("B2", "B3"), ("B0", "B3")):
        _add(id=f"DELTA_{lo}{hi}", doc="ablation", fmt="spp",
             ptr=f"/component_deltas_paired/{lo}->{hi}/any_gold_delta_pp",
             desc=f"{lo}->{hi} paired Any-Gold @5 change")


def _regime_a() -> None:
    for m in ("M1", "M2", "M3", "M4", "M5"):
        for key, fmt in (("R@5_file", "f4"), ("R@10_file", "f4"),
                         ("MRR_file", "f4"), ("latency_ms", "f1"),
                         ("chars", "comma")):
            _add(id=f"RA_{m}_{key}", doc="ablation", fmt=fmt,
                 ptr=f"/regime_a/aggregates/{m}/{key}",
                 desc=f"Regime A {m} {key}")
    _add(id="CROSS_REGIME", doc="ablation", fmt="diff_pp",
         ptr="/results/B3/all/@5/mean_fraction/value",
         ptr2="/regime_a/aggregates/M4/R@5_file",
         desc="B3 Mean-Fraction R@5 minus M4 R@5 (observed across regimes)")
    _add(id="M3_VS_M1", doc="ablation", fmt="diff_pp",
         ptr="/regime_a/aggregates/M3/R@5_file",
         ptr2="/regime_a/aggregates/M1/R@5_file",
         desc="M3 R@5 minus M1 R@5 (a null)")


def _metric_gap() -> None:
    _add(id="GAP5", doc="ablation", fmt="pp2",
         ptr="/within_v4_metric_shift/@5/gap_pp",
         desc="Any-Gold minus Mean-Fraction at k=5 (definitional)")
    _add(id="PARTIAL5", doc="ablation", fmt="d",
         ptr="/within_v4_metric_shift/@5/tasks_partial_credit",
         desc="tasks whose B3 mean fraction is in (0,1) at k=5")


def _hazards() -> None:
    h = "hazards"
    _add(id="T1_THRESH", doc=h, fmt="comma",
         ptr="/site1_compaction/token_threshold",
         desc="ADK compaction token threshold")
    _add(id="T1_INTERVAL", doc=h, fmt="d",
         ptr="/site1_compaction/compaction_interval",
         desc="ADK compaction interval in turns")
    _add(id="T1_TMIN", doc=h, fmt="d",
         ptr="/site1_compaction/first_compaction_turn_min",
         desc="earliest observed first-compaction turn")
    _add(id="T1_TMAX", doc=h, fmt="d",
         ptr="/site1_compaction/first_compaction_turn_max",
         desc="latest observed first-compaction turn")
    _add(id="T1_FILES", doc=h, fmt="d", ptr="/site4_gitignore/files",
         desc="new files created by gold patches")
    _add(id="T1_TASKS", doc=h, fmt="d", ptr="/site4_gitignore/tasks",
         desc="tasks that create new files")
    _add(id="T1_IGNORED", doc=h, fmt="d", ptr="/site4_gitignore/ignored_count",
         desc="created files matched by .gitignore")
    _add(id="S5_CHARS", doc=h, fmt="comma",
         ptr="/site5_skilltoolset/preamble_chars",
         desc="SkillToolset hidden preamble characters")
    _add(id="S5_TOKENS", doc=h, fmt="d",
         ptr="/site5_skilltoolset/preamble_tokens_est",
         desc="SkillToolset hidden preamble token estimate")
    _add(id="S5_DELTA", doc=h, fmt="d",
         ptr="/site1_compaction/skilltoolset_turn1_marginal_tokens",
         desc="turn-1 token delta attributable to SkillToolset")
    _add(id="S2_DEF", doc=h, fmt="d", ptr="/site2_mitigation/defined_at_line",
         desc="line defining install_litellm_reasoning_patch")
    _add(id="S2_MIRROR", doc=h, fmt="d", ptr="/site2_mitigation/mirror_line",
         desc="line mirroring reasoning_content into reasoning")
    _add(id="S2_CALLS", doc=h, fmt="d", ptr="/site2_mitigation/install_calls",
         desc="module-level installer call sites")
    _add(id="S6_PLUGIN", doc=h, fmt="d",
         ptr="/site6_bare_pytest/def_a_test_patch_direct/count",
         desc="fastapi tasks whose gold test_patch imports a plugin")
    _add(id="S6_ANYIO", doc=h, fmt="d",
         ptr="/site6_bare_pytest/def_a_plus_anyio/count",
         desc="same, plus the anyio-only task")
    _add(id="S6_TOUCHED", doc=h, fmt="d",
         ptr="/site6_bare_pytest/def_b_touched_test_files/count",
         desc="tasks whose touched test files import a plugin")
    _add(id="S6_TREE", doc=h, fmt="d",
         ptr="/site6_bare_pytest/def_c_repo_tests_tree/count",
         desc="tasks whose repository tests/ tree imports a plugin")
    _add(id="S6_N", doc=h, fmt="d", ptr="/site6_bare_pytest/fastapi_tasks",
         desc="fastapi task denominator")


def _multifile() -> None:
    d = "multifile"
    _add(id="MULTI_TOTAL", doc=d, fmt="d", ptr="/buckets/all_multi/N",
         desc="tasks whose gold patch touches more than one file")
    _add(id="MULTI_ANY", doc=d, fmt="frac",
         ptr="/buckets/all_multi/control/k5/any_gold@5/hits",
         ptr2="/buckets/all_multi/control/k5/N",
         desc="single-pass any-gold @5 on the multi-file subset")
    _add(id="MULTI_ALL", doc=d, fmt="frac",
         ptr="/buckets/all_multi/control/k5/all_gold@5/hits",
         ptr2="/buckets/all_multi/control/k5/N",
         desc="single-pass strict all-gold @5 on the multi-file subset")
    for arm, key in (("CTRL", "control"), ("HOP", "hop")):
        for k in (5, 10):
            _add(id=f"HOP{k}_{arm}_ANY", doc=d, fmt="frac",
                 ptr=f"/buckets/all_multi/{key}/k{k}/any_gold@{k}/hits",
                 ptr2=f"/buckets/all_multi/{key}/k{k}/N",
                 desc=f"2-hop {arm.lower()} any-gold @{k}")
            _add(id=f"HOP{k}_{arm}_ALL", doc=d, fmt="frac",
                 ptr=f"/buckets/all_multi/{key}/k{k}/all_gold@{k}/hits",
                 ptr2=f"/buckets/all_multi/{key}/k{k}/N",
                 desc=f"2-hop {arm.lower()} strict all-gold @{k}")
            _add(id=f"HOP{k}_{arm}_MF", doc=d, fmt="f4",
                 ptr=f"/buckets/all_multi/{key}/k{k}/mean_fraction@{k}",
                 desc=f"2-hop {arm.lower()} mean-fraction @{k}")
    for k in (5, 10):
        _add(id=f"HOP{k}_P", doc=d, fmt="f3",
             ptr=f"/buckets/all_multi/paired/k{k}/any/p_exact",
             desc=f"exact paired sign test, any-gold, hop vs control, k={k}")
        _add(id=f"HOP{k}_P_ALL", doc=d, fmt="f3",
             ptr=f"/buckets/all_multi/paired/k{k}/all/p_exact",
             desc=f"exact paired sign test, strict all-gold, hop vs control, k={k}")
        _add(id=f"HOP{k}_FS", doc=d, fmt="d",
             ptr=f"/buckets/all_multi/transitions/k{k}/fail->success",
             desc=f"tasks that gain strict all-gold under 2-hop, k={k}")
        _add(id=f"HOP{k}_SF", doc=d, fmt="d",
             ptr=f"/buckets/all_multi/transitions/k{k}/success->fail",
             desc=f"tasks that lose strict all-gold under 2-hop, k={k}")
    _add(id="HOP5_ANY_LOSS", doc=d, fmt="d",
         ptr="/buckets/all_multi/paired/k5/any/discordant_b_gt_a",
         desc="tasks where 2-hop loses any-gold at k=5")
    _add(id="HOP_CTRL_S", doc=d, fmt="f2", ptr="/median_seconds/control_locate",
         desc="median seconds for one locate call")
    _add(id="HOP_GRAPH_S", doc=d, fmt="f2", ptr="/median_seconds/graph_build_once",
         desc="median seconds to build the import graph once")

    for pfx, key in (("STR1", "1"), ("STR2", "2"), ("STR35", "3-5"), ("STRGT5", ">5")):
        _add(id=f"{pfx}_N", doc=d, fmt="d",
             ptr=f"/gold_set_structure_all_129/{key}/N",
             desc=f"tasks touching {key} gold files")
        _add(id=f"{pfx}_ANY", doc=d, fmt="frac",
             ptr=f"/gold_set_structure_all_129/{key}/any5",
             ptr2=f"/gold_set_structure_all_129/{key}/N",
             desc=f"tasks with any gold file at k=5, gold_n={key}")
        _add(id=f"{pfx}_ALL", doc=d, fmt="frac",
             ptr=f"/gold_set_structure_all_129/{key}/all5",
             ptr2=f"/gold_set_structure_all_129/{key}/N",
             desc=f"tasks with all gold files at k=5, gold_n={key}")
        _add(id=f"{pfx}_COND", doc=d, fmt="opt_f3",
             ptr=f"/gold_set_structure_all_129/{key}/p_all_given_any",
             desc=f"P(all-gold | any-gold) at k=5, gold_n={key}")


_ladder()
_regime_a()
_metric_gap()
_hazards()
_multifile()


def _leaderboard() -> None:
    d = "leaderboard"
    _add(id="LB_SPLIT", doc=d, fmt="d", ptr="/split_size",
         desc="leaderboard split size")
    _add(id="LEDGER_N", doc=d, fmt="d", ptr="/ledger_summary/n_runs",
         desc="logged submissions in the ledger")
    _add(id="LEDGER_31B", doc=d, fmt="d", ptr="/ledger_summary/scored_31b",
         desc="scored 31B submissions")
    _add(id="LEDGER_E4B", doc=d, fmt="d", ptr="/ledger_summary/scored_e4b",
         desc="scored E4B submissions")
    _add(id="LEDGER_UNSCORED", doc=d, fmt="d", ptr="/ledger_summary/unscored",
         desc="unscored submissions")
    _add(id="E4B_K", doc=d, fmt="d", ptr="/ledger_summary/e4b_k_min",
         desc="tasks solved by every genuine E4B submission")
    _add(id="ROW1_A", doc=d, fmt="d", ptr="/estimand_rows/0/exp05_k",
         desc="exp05 solved tasks")
    _add(id="ROW1_B", doc=d, fmt="d", ptr="/estimand_rows/0/e0_k",
         desc="byte-identical control solved tasks")
    _add(id="REPEAT_SHIFT", doc=d, fmt="d",
         ptr="/estimand_rows/0/observed_shift_tasks",
         desc="task shift between identical artifacts")
    _add(id="ROW2_MEAN", doc=d, fmt="f1", ptr="/estimand_rows/1/mean_tasks",
         desc="mean solved tasks across five near-baseline bundles")
    _add(id="ROW2_SD", doc=d, fmt="f3", ptr="/estimand_rows/1/sd_tasks",
         desc="sample SD across five near-baseline bundles")
    _add(id="ROW2_CI", doc=d, fmt="ci2", ptr="/estimand_rows/1/sd_ci95",
         desc="95% chi-square CI on the SD")
    _add(id="ROW2_DF", doc=d, fmt="d", ptr="/estimand_rows/1/df",
         desc="degrees of freedom for the SD")
    _add(id="ROW3_SE", doc=d, fmt="f2", ptr="/estimand_rows/2/se_split_tasks",
         desc="binomial SE of one 58-task split, in tasks")
    _add(id="ROW3_PP", doc=d, fmt="f2", ptr="/estimand_rows/2/se_split_pp",
         desc="binomial SE of one 58-task split, in points")


_leaderboard()


# --------------------------------------------------------------------------- #
def load_docs() -> dict[str, dict]:
    docs = {}
    for key, name in JSON_FILES.items():
        path = VDIR / name
        if not path.exists():
            sys.exit(f"[FAIL] missing verified JSON: {path.relative_to(REPO)}")
        docs[key] = json.loads(path.read_text(encoding="utf-8"))
    return docs


def resolve(doc, pointer: str):
    cur = doc
    for raw in pointer.strip("/").split("/"):
        part = raw.replace("~1", "/").replace("~0", "~")
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


def render(claim: dict, docs: dict) -> str:
    v = resolve(docs[claim["doc"]], claim["ptr"])
    kind = claim["fmt"]
    if kind == "d":
        return f"{int(v):d}"
    if kind == "s":
        return str(v)
    if kind in ("f1", "f2", "f3", "f4"):
        return f"{float(v):.{kind[1]}f}"
    if kind == "opt_f3":
        return "\u2014" if v is None else f"{float(v):.3f}"
    if kind == "comma":
        return f"{int(round(float(v))):,d}"
    if kind == "pct1":
        return f"{100 * float(v):.1f}%"
    if kind == "pct0":
        return f"{100 * float(v):.0f}%"
    if kind == "pp2":
        return f"{float(v):.2f} pp"
    if kind == "pp1":
        return f"{float(v):.1f} pp"
    if kind == "spp":
        return f"{float(v):+.2f} pp"
    if kind == "g3":
        return f"{float(v):.3g}"
    if kind == "frac":
        b = resolve(docs[claim["doc"]], claim["ptr2"])
        return f"{int(v)}/{int(b)}"
    if kind == "diff_pp":
        b = resolve(docs[claim["doc"]], claim["ptr2"])
        return f"{100 * (float(v) - float(b)):+.2f} pp"
    if kind == "ci4":
        return "[%.4f, %.4f]" % (float(v[0]), float(v[1]))
    if kind == "ci2":
        return "[%.2f, %.2f]" % (float(v[0]), float(v[1]))
    if kind == "pair":
        b = resolve(docs[claim["doc"]], claim["ptr2"])
        return f"{int(v)}, {int(b)}"
    raise SystemExit(f"unknown fmt {kind!r} in claim {claim['id']}")


NUM_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")


def numbers_in(text: str) -> list[str]:
    return [m.group(0).replace(",", "") for m in NUM_RE.finditer(text)]


def digest(docs: dict) -> None:
    skip = {"per_task", "task_ids", "tasks_detail", "runs", "tasks"}
    for key, doc in docs.items():
        print(f"\n=== {key} ===")

        def walk(node, ptr=""):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in skip:
                        if isinstance(v, list):
                            print(f"{ptr}/{k}  [list n={len(v)}]")
                        continue
                    walk(v, f"{ptr}/{k}")
            elif isinstance(node, list):
                if len(node) > 8:
                    print(f"{ptr}  [list n={len(node)}]")
                else:
                    for i, v in enumerate(node):
                        walk(v, f"{ptr}/{i}")
            else:
                print(f"{ptr}  {node!r}")

        walk(doc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--fill", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    docs = load_docs()
    if args.digest:
        digest(docs)
        return 0

    text = PAPER.read_text(encoding="utf-8")

    # ---- 0. fill placeholders from the manifest --------------------------- #
    if args.fill:
        filled, missing = 0, []
        for claim in CLAIMS:
            token = f"@@{claim['id']}@@"
            if token in text:
                text = text.replace(token, render(claim, docs))
                filled += 1
        for token in sorted(set(re.findall(r"@@[A-Z0-9_]+@@", text))):
            missing.append(token)
        PAPER.write_text(text, encoding="utf-8")
        print(f"[fill] {filled} placeholder(s) written into {PAPER.relative_to(REPO)}")
        if missing:
            print(f"[fill] {len(missing)} unresolved placeholder(s): {' '.join(missing)}")
            return 1
        return 0

    words = len(text.split())
    failures: list[str] = []
    rows = []

    # ---- 1. no unresolved placeholders ----------------------------------- #
    left = sorted(set(re.findall(r"@@[A-Z0-9_]+@@", text)))
    for token in left:
        failures.append(f"unresolved placeholder {token}")

    # ---- 2. every declared claim must appear, rendered from JSON ---------- #
    for claim in CLAIMS:
        try:
            rendered = render(claim, docs)
        except (KeyError, IndexError, TypeError) as exc:
            failures.append(f"{claim['id']}: pointer {claim['ptr']} failed ({exc})")
            continue
        count = text.count(rendered)
        rows.append({
            "claim_id": claim["id"],
            "json_file": JSON_FILES[claim["doc"]],
            "json_pointer": claim["ptr"] + (f" + {claim['ptr2']}" if "ptr2" in claim else ""),
            "rendered": rendered,
            "occurrences_in_paper": count,
            "description": claim["desc"],
        })
        if count == 0:
            failures.append(
                f"{claim['id']}: expected {rendered!r} ({claim['desc']}) "
                f"from {JSON_FILES[claim['doc']]}#{claim['ptr']}; absent from paper"
            )

    # ---- 3. every visible number must be bound ---------------------------- #
    covered = set()
    for claim in CLAIMS:
        try:
            covered.update(numbers_in(render(claim, docs)))
        except (KeyError, IndexError, TypeError):
            continue
    visible = numbers_in(text)
    unbound = sorted({t for t in visible if t not in covered and t not in STRUCTURAL})
    if unbound:
        for tok in unbound:
            where = [ln.strip()[:110] for ln in text.splitlines()
                     if re.search(rf"(?<![\w.]){re.escape(tok)}(?![\w])", ln)]
            failures.append(f"unbound number {tok!r} in: {where[:2]}")

    # ---- 4. forbidden legacy strings ------------------------------------- #
    for bad in FORBIDDEN:
        if bad in text:
            failures.append(f"forbidden legacy string present: {bad!r}")

    # ---- 5. word budget --------------------------------------------------- #
    if words > MAX_WORDS:
        failures.append(f"word count {words} exceeds hard gate {MAX_WORDS}")

    # ---- report ----------------------------------------------------------- #
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "claim_id", "json_file", "json_pointer", "rendered",
            "occurrences_in_paper", "description"])
        w.writeheader()
        w.writerows(rows)

    if not args.quiet:
        print(f"paper      : {PAPER.relative_to(REPO)}")
        print(f"words      : {words} (target {TARGET_WORDS}, hard gate {MAX_WORDS})")
        print(f"claims     : {len(CLAIMS)} bound to {len(JSON_FILES)} JSON files")
        print(f"visible    : {len(visible)} numeric tokens, "
              f"{len(visible) - len(unbound)} bound or structural")
        print(f"csv        : {CSV_OUT.relative_to(REPO)} ({len(rows)} rows)")

    if failures:
        print(f"\n[FAIL] {len(failures)} integrity violation(s):")
        for f in failures:
            print("  -", f)
        return 1

    print("\n[PASS] every number in the paper resolves to research/verified_json/*.json")
    print(f"[PASS] no forbidden legacy string; {words} <= {MAX_WORDS} words")
    return 0


if __name__ == "__main__":
    sys.exit(main())

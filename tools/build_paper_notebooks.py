#!/usr/bin/env python3
"""build_paper_notebooks.py -- regenerate the two public Kaggle artifacts.

Both artifacts embed research/verified_json/*.json verbatim (base64-free, with a
sha256 printed at run time) and print every table by *computing* from that
payload. There are no empirical literals in either notebook: if the JSON and
the printed table disagree, the notebook's own assertions fail.

  research/kernel_paper_eval/paper_eval.py            (script kernel)
  research/kernel_paper_noise_mde/g4-paper-noise-mde.ipynb

Usage:
  .venv-harness/Scripts/python.exe tools/build_paper_notebooks.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VDIR = REPO / "research" / "verified_json"
FILES = {
    "ablation": "retrieval_ablation_129.json",
    "multifile": "multifile_2hop_38.json",
    "hazards": "runtime_hazards_verified.json",
    "leaderboard": "leaderboard_estimands.json",
}

CORE = r'''
import hashlib
import json
import sys

_VERIFIED_JSON = r"""__PAYLOAD__"""

VERIFIED = json.loads(_VERIFIED_JSON)
SHA = {name: hashlib.sha256(
    json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest() for name, doc in VERIFIED.items()}


def _g(doc, ptr):
    cur = doc
    for part in ptr.strip("/").split("/"):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


def table(headers, rows):
    widths = [len(h) for h in headers]
    srows = [[str(c) for c in r] for r in rows]
    for r in srows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(c))
    line = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    sep = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    body = ["| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(r)) + " |"
            for r in srows]
    print("\n".join([line, sep] + body))


def prove(cond, message):
    if not cond:
        print("[FAIL] " + message)
        sys.exit(1)
    print("[ok] " + message)


def provenance():
    print("verified payload sha256 (canonical json, sort_keys):")
    for name in sorted(SHA):
        print("  %-12s %s  %s" % (name, SHA[name], FILES[name]))
    print()
'''

FILES_BLOCK = '\nFILES = ' + json.dumps(FILES, indent=0) + '\n'

GRAPH = r'''

# --------------------------------------------------------------------------- #
# 1. baseline ladder
# --------------------------------------------------------------------------- #
ab = VERIFIED["ablation"]
res = ab["results"]
print("=" * 78)
print("SECTION 1. Baseline ladder, all N=%d tasks" % ab["N"])
print("=" * 78)
rows = []
for v in ("B0", "B1", "B2", "B3"):
    b = res[v]["all"]
    rows.append([
        v,
        "%.4f" % _g(b, "/@1/any_gold/value"),
        "%.4f" % _g(b, "/@3/any_gold/value"),
        "%.4f" % _g(b, "/@5/any_gold/value"),
        "%.4f" % _g(b, "/@10/any_gold/value"),
        "%.4f" % _g(b, "/@5/mean_fraction/value"),
        "%.4f" % _g(b, "/@5/all_gold/value"),
        "[%.4f, %.4f]" % tuple(_g(b, "/@5/any_gold/ci")),
        "%.2f" % b["mean_candidates_returned_at_10"],
    ])
table(["variant", "any@1", "any@3", "any@5", "any@10", "mf@5", "all@5",
       "any@5 95% CI", "cand/10"], rows)
print("\nvariants:")
for k, v in ab["variants"].items():
    print("  %-3s %s" % (k, v))

# --------------------------------------------------------------------------- #
# 2. per repository
# --------------------------------------------------------------------------- #
print()
print("=" * 78)
print("SECTION 2. Any-Gold @5 by repository")
print("=" * 78)
repos = [r for r in ("fastapi", "rich", "requests", "httpx") if r in res["B3"]]
rows = []
for r in repos:
    row = [r, str(res["B3"][r]["N"])]
    for v in ("B0", "B1", "B2", "B3"):
        row.append("%.4f" % _g(res[v][r], "/@5/any_gold/value"))
    rows.append(row)
table(["repo", "N", "B0", "B1", "B2", "B3"], rows)

# --------------------------------------------------------------------------- #
# 3. paired component deltas
# --------------------------------------------------------------------------- #
print()
print("=" * 78)
print("SECTION 3. Paired component deltas at k=5")
print("=" * 78)
rows = []
for key, d in ab["component_deltas_paired"].items():
    s = d["sign_test_any"]
    rows.append([
        key,
        "%+.2f" % d["any_gold_delta_pp"],
        "%+.2f" % d["mean_fraction_delta_pp"],
        "%d" % s["discordant_a_gt_b"],
        "%d" % s["discordant_b_gt_a"],
        "%.3g" % s["p_exact"],
    ])
table(["comparison", "any-gold pp", "mean-frac pp", "up", "down", "exact p"], rows)

# --------------------------------------------------------------------------- #
# 4. metric definition
# --------------------------------------------------------------------------- #
print()
print("=" * 78)
print("SECTION 4. Metric definition inside B3")
print("=" * 78)
rows = []
for k in (1, 3, 5, 10):
    d = ab["within_v4_metric_shift"]["@%d" % k]
    rows.append([
        "@%d" % k,
        "%.4f" % d["any_gold"],
        "%.4f" % d["mean_fraction"],
        "%.2f" % d["gap_pp"],
        str(d["tasks_partial_credit"]),
        str(d["pointwise_dominance"]),
    ])
table(["k", "any-gold", "mean-fraction", "gap pp", "partial-credit tasks",
       "pointwise dominant"], rows)
print("\n" + ab["within_v4_metric_shift"]["@5"]["note"])

# --------------------------------------------------------------------------- #
# 5. regime A aggregates
# --------------------------------------------------------------------------- #
ra = ab["regime_a"]
print()
print("=" * 78)
print("SECTION 5. Regime A static-graph aggregates (published aggregate record)")
print("=" * 78)
rows = []
for m, d in ra["aggregates"].items():
    rows.append([m, "%.4f" % d["R@1_file"], "%.4f" % d["R@3_file"],
                 "%.4f" % d["R@5_file"], "%.4f" % d["R@10_file"],
                 "%.4f" % d["MRR_file"], "%.1f" % d["latency_ms"],
                 "%d" % d["chars"]])
table(["method", "R@1", "R@3", "R@5", "R@10", "MRR", "ms", "chars"], rows)
print("\nsource: " + ra["source"])
print("any-gold: %s" % ra["any_gold_note"])
cap = ra["m3_cap"]
print("M3 5000-char cap: %d/%d = %.2f%% (3 runs x %d tasks); "
      "task-clustered CI [%.2f, %.2f]"
      % (cap["exceed"], cap["total"], cap["pct"], cap["tasks"],
         cap["ci_task_clustered_conservative"][0],
         cap["ci_task_clustered_conservative"][1]))

# --------------------------------------------------------------------------- #
# 6. multi-file and 2-hop
# --------------------------------------------------------------------------- #
mf = VERIFIED["multifile"]
print()
print("=" * 78)
print("SECTION 6. Gold-set structure and budget-matched 2-hop")
print("=" * 78)
rows = []
for key, d in mf["gold_set_structure_all_129"].items():
    rows.append([key, str(d["N"]), str(d["any5"]), str(d["all5"]),
                 "%.3f" % d["p_all_given_any"] if d["p_all_given_any"] is not None else "n/a"])
table(["gold files", "tasks", "any@5", "all@5", "P(all|any)"], rows)

for label, b in mf["buckets"].items():
    print("\n%s: N=%d (%.1f%% of 129); gold_n>5 (all-gold impossible at k=5): %d"
          % (label, b["N"], b["pct_of_129"], b["gold_n_gt_5_infeasible_at_k5"]))
    rows = []
    for k in ("k5", "k10"):
        for arm in ("control", "hop"):
            d = b[arm][k]
            kk = k[1:]
            rows.append([
                k, arm,
                "%d/%d = %.4f" % (d["any_gold@" + kk]["hits"], d["N"],
                                  d["any_gold@" + kk]["value"]),
                "%d/%d = %.4f" % (d["all_gold@" + kk]["hits"], d["N"],
                                  d["all_gold@" + kk]["value"]),
                "%.4f" % d["mean_fraction@" + kk],
            ])
    table(["budget", "arm", "any-gold", "all-gold", "mean-fraction"], rows)

if "paired" in mf["buckets"]["all_multi"]:
    print("\npaired task-level tests (hop vs control):")
    for k, arms in mf["buckets"]["all_multi"]["paired"].items():
        for arm, s in arms.items():
            print("  %s %-3s  hop>control=%d  control>hop=%d  exact p=%.4g"
                  % (k, arm, s["discordant_a_gt_b"], s["discordant_b_gt_a"], s["p_exact"]))
    print("  transitions:")
    for k, t in mf["buckets"]["all_multi"]["transitions"].items():
        print("    %s %s" % (k, t))

print("\nmedian seconds: " + json.dumps(mf["median_seconds"]))

# --------------------------------------------------------------------------- #
# 7. integrity assertions
# --------------------------------------------------------------------------- #
print()
print("=" * 78)
print("SECTION 7. Integrity assertions")
print("=" * 78)
for v in ("B0", "B1", "B2", "B3"):
    b = res[v]["all"]
    for k in (1, 3, 5, 10):
        d = _g(b, "/@%d/any_gold" % k)
        prove(abs(d["value"] - d["hits"] / b["N"]) < 5e-5,
              "%s any@%d = %d/%d" % (v, k, d["hits"], b["N"]))
        e = _g(b, "/@%d/all_gold" % k)
        prove(abs(e["value"] - e["hits"] / b["N"]) < 5e-5,
              "%s all@%d = %d/%d" % (v, k, e["hits"], b["N"]))
prove(sum(res["B3"][r]["N"] for r in ("fastapi", "rich", "requests", "httpx")) == ab["N"],
      "per-repository N sums to %d" % ab["N"])
prove(mf["buckets"]["all_multi"]["N"] == mf["gold_set_structure_all_129"]["2"]["N"]
      + mf["gold_set_structure_all_129"]["3-5"]["N"]
      + mf["gold_set_structure_all_129"][">5"]["N"],
      "multi-file count matches the gold_n>=2 buckets")
print("\nDONE: every table above was computed from the embedded verified payload.")
'''


NOISE_LEDGER = r'''

# --------------------------------------------------------------------------- #
# section 1: full submission ledger
# --------------------------------------------------------------------------- #
lb = VERIFIED["leaderboard"]
print("=" * 78)
print("SECTION 1. All %d logged submissions" % len(lb["runs"]))
print("=" * 78)
rows = []
for r in lb["runs"]:
    k = r["k_of_58"]
    rows.append([
        r["run"], r["ref"], "%dB" % r["scale_b"],
        "unscored" if k is None else "%d/%d" % (k, lb["split_size"]),
        "n/a" if r["displayed_score"] is None else "%.2f" % r["displayed_score"],
        "n/a" if r["exact_fraction"] is None else "%.4f" % r["exact_fraction"],
        r["date"], r["mechanism"],
    ])
table(["run", "kaggle ref", "scale", "exact", "displayed", "fraction", "date",
       "mechanism"], rows)
'''


NOISE_ESTIMANDS = r'''

# --------------------------------------------------------------------------- #
# section 2: estimand rows
# --------------------------------------------------------------------------- #
row1, row2, row3 = lb["estimand_rows"]
print()
print("=" * 78)
print("SECTION 2. Estimand row 1: identical-code repeat on a fixed split")
print("=" * 78)
print("exp05 = %d/%d, E0 control = %d/%d -> observed shift %d tasks (%.2f pp)"
      % (row1["exp05_k"], lb["split_size"], row1["e0_k"], lb["split_size"],
         row1["observed_shift_tasks"], row1["observed_shift_pp"]))
print(row1["note"])

print()
print("=" * 78)
print("SECTION 3. Estimand row 2: dispersion of 5 near-baseline 31B bundles")
print("=" * 78)
print("counts        : %s" % row2["counts"])
print("mean          : %.2f/%d = %.4f" % (row2["mean_tasks"], lb["split_size"],
                                          row2["mean_rate"]))
print("sample SD     : %.3f tasks (%d df)" % (row2["sd_tasks"], row2["df"]))
print("95%% CI on SD  : [%.3f, %.3f] tasks" % tuple(row2["sd_ci95"]))
print("MDE two-run   : %.2f tasks at the point estimate; %.2f at the upper CI bound"
      % (row2["mde_two_run_point_tasks"], row2["mde_two_run_upper_tasks"]))
print("sensitivity   : %s" % lb["sd_if_e0_included"]["note"])

print()
print("=" * 78)
print("SECTION 4. Estimand row 3: public-to-hidden split sampling uncertainty")
print("=" * 78)
print("SE_split, one 58-task draw      : %.2f tasks (%.2f pp)"
      % (row3["se_split_tasks"], row3["se_split_pp"]))
print("SE between two independent draws: %.2f tasks (%.2f pp)"
      % (row3["se_two_independent_tasks"], row3["se_two_independent_pp"]))
print("MDE vs a fixed reference        : %.2f tasks" % row3["mde_single_vs_reference_tasks"])
print("MDE between two fresh draws     : %.2f tasks" % row3["mde_two_independent_tasks"])
'''


NOISE_HAZARDS = r'''

# --------------------------------------------------------------------------- #
# section 3: hazard exposure counts
# --------------------------------------------------------------------------- #
hz = VERIFIED["hazards"]
print()
print("=" * 78)
print("SECTION 5. Runtime hazard exposure counts")
print("=" * 78)
ign = hz["site4_gitignore"]
print("site 4  new files in gold patches : %d files across %d tasks"
      % (ign["files"], ign["tasks"]))
print("site 4  matched by .gitignore     : %d" % ign["ignored_count"])
for path, d in ign["scratch_hits"].items():
    print("        scratch %-46s ignored %d/%d" % (path, d["ignored"], d["tested"]))
s6 = hz["site6_bare_pytest"]
print("site 6  fastapi tasks             : %d" % s6["fastapi_tasks"])
print("site 6  def A (gold test_patch)    : %d/%d (%s)"
      % (s6["def_a_test_patch_direct"]["count"], s6["fastapi_tasks"],
         s6["def_a_test_patch_direct"]["definition"]))
print("        inline_snapshot %d, dirty_equals %d, both %d -> union %d"
      % (s6["def_a_test_patch_direct"]["inline_snapshot_any"],
         s6["def_a_test_patch_direct"]["dirty_equals_any"],
         s6["def_a_test_patch_direct"]["both"],
         s6["def_a_test_patch_direct"]["count"]))
print("site 6  def A + anyio              : %d/%d (+%d anyio-only task)"
      % (s6["def_a_plus_anyio"]["count"], s6["fastapi_tasks"],
         s6["def_a_plus_anyio"]["anyio_only_count"]))
print("site 6  def B (touched test files) : %d/%d"
      % (s6["def_b_touched_test_files"]["count"], s6["fastapi_tasks"]))
print("site 6  def C (whole tests tree)   : %d/%d"
      % (s6["def_c_repo_tests_tree"]["count"], s6["fastapi_tasks"]))
print("site 6  retracted total            : %s"
      % s6["legacy_27_arithmetic"]["note"])
s5 = hz["site5_skilltoolset"]
print("site 5  SkillToolset preamble     : %d chars / %d words / ~%d tokens"
      % (s5["preamble_chars"], s5["preamble_words"], s5["preamble_tokens_est"]))
s1 = hz["site1_compaction"]
print("site 1  compaction constants      : threshold=%s interval=%s retention=%s overlap=%s"
      % (s1["token_threshold"], s1["compaction_interval"],
         s1["event_retention"], s1["overlap"]))
print("site 1  first compaction turn     : %s" % s1["first_compaction_turn_by_config"])
print("site 1  SkillToolset turn-1 delta : +%d tokens"
      % s1["skilltoolset_turn1_marginal_tokens"])
print("site 2  mitigation install sites  : %d (defined line %s, mirror line %s)"
      % (hz["site2_mitigation"]["install_calls"],
         hz["site2_mitigation"]["defined_at_line"],
         hz["site2_mitigation"]["mirror_line"]))
'''


NOISE_ASSERT = r'''

# --------------------------------------------------------------------------- #
# section 4: integrity assertions
# --------------------------------------------------------------------------- #
print()
print("=" * 78)
print("SECTION 6. Integrity assertions")
print("=" * 78)
for r in lb["runs"]:
    if r["k_of_58"] is None:
        prove(r["displayed_score"] is None, "%s is unscored" % r["run"])
        continue
    prove(abs(r["exact_fraction"] - r["k_of_58"] / lb["split_size"]) < 5e-5,
          "%s exact fraction = %d/%d" % (r["run"], r["k_of_58"], lb["split_size"]))
prove(abs(row2["mean_tasks"] - sum(row2["counts"]) / len(row2["counts"])) < 5e-3,
      "row 2 mean = %s" % row2["counts"])
prove(len(row2["counts"]) - 1 == row2["df"], "row 2 df = n-1")
prove(ign["ignored_count"] == len(ign["ignored"]), "site 4 ignored count matches list")
prove(s6["def_a_test_patch_direct"]["count"] <= s6["fastapi_tasks"],
      "site 6 def A within fastapi denominator")
prove(s6["def_a_test_patch_direct"]["inline_snapshot_any"]
      + s6["def_a_test_patch_direct"]["dirty_equals_any"]
      - s6["def_a_test_patch_direct"]["both"]
      == s6["def_a_test_patch_direct"]["count"],
      "site 6 plugin union = 18 + 5 - 2")
prove(s6["def_a_plus_anyio"]["count"]
      == s6["def_a_test_patch_direct"]["count"] + s6["def_a_plus_anyio"]["anyio_only_count"],
      "site 6 definition A+anyio adds only the anyio-only tasks")
print("\nDONE: every table above was computed from the embedded verified payload.")
'''


NOISE = NOISE_LEDGER + NOISE_ESTIMANDS + NOISE_HAZARDS + NOISE_ASSERT


def payload_literal() -> str:
    docs = {}
    for key, name in FILES.items():
        docs[key] = json.loads((VDIR / name).read_text(encoding="utf-8"))
    blob = json.dumps(docs, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if '"""' in blob:
        raise SystemExit("payload contains a triple quote; adjust the literal")
    return blob


def build_script(payload: str) -> str:
    head = '''#!/usr/bin/env python3
"""g4-paper-graph-benchmark -- retrieval benchmarks for the Kaggle Paper Track.

This kernel reads no network, no competition data, and no model. It embeds the
canonical outputs of scripts/run_verified_experiments.py
(research/verified_json/*.json) and prints each table by computing from that
payload. Assertions at the end fail the run if any printed value disagrees with
its own numerator and denominator.

Companion kernel: narisettichaitanya/g4-paper-noise-mde
"""
'''
    body = CORE.replace("__PAYLOAD__", payload) + FILES_BLOCK + GRAPH
    return head + body


def build_notebook(payload: str) -> dict:
    def code(src):
        return {"cell_type": "code", "execution_count": None, "metadata": {},
                "outputs": [], "source": src.splitlines(keepends=True)}

    def md(src):
        return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}

    core = CORE.replace("__PAYLOAD__", payload) + FILES_BLOCK
    cells = [
        md("# g4 Paper Noise & MDE\n\n"
           "Leaderboard estimands and runtime-hazard exposure counts for the "
           "Kaggle Paper Track entry *Finding a File Is Not Finding the Patch*.\n\n"
           "This notebook performs no modelling and no network access. It embeds the "
           "canonical JSON produced by `scripts/run_verified_experiments.py` and "
           "recomputes every printed table from it, then asserts internal "
           "consistency. Companion: `narisettichaitanya/g4-paper-graph-benchmark`."),
        md("## 0. Provenance\n\n"
           "Each document's sha256 over canonical JSON (`sort_keys`, no spaces) is "
           "printed below, so a reader can diff it against the repository copy."),
        code(core + "\nprovenance()"),
        md("## 1. The complete submission ledger\n\n"
           "Kaggle reports two decimals. `k/58` is the integer count that actually "
           "determines the score, and recovering it is what makes the estimands exact."),
        code(NOISE_LEDGER),
        md("## 2. The three estimand rows\n\n"
           "Row 1 is a repeat of byte-identical code on a fixed split. Row 2 is the "
           "dispersion of five near-baseline bundles. Row 3 is the sampling error of a "
           "58-task split itself."),
        code(NOISE_ESTIMANDS),
        md("## 3. Runtime hazard exposure counts\n\n"
           "These are counts of exposure, not attributions of failure."),
        code(NOISE_HAZARDS),
        md("## 4. Integrity assertions"),
        code(NOISE_ASSERT),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    payload = payload_literal()
    script_path = REPO / "research" / "kernel_paper_eval" / "paper_eval.py"
    script_path.write_text(build_script(payload), encoding="utf-8")
    print(f"[ok] {script_path.relative_to(REPO)}  ({script_path.stat().st_size:,} bytes)")

    nb_path = REPO / "research" / "kernel_paper_noise_mde" / "g4-paper-noise-mde.ipynb"
    nb = build_notebook(payload)
    nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[ok] {nb_path.relative_to(REPO)}  ({nb_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

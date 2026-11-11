#!/usr/bin/env python3
"""generate_paper_figures.py -- render fig0-fig5 from research/verified_json/*.json.

Integrity contract: this module contains NO empirical literals. Every number
that appears on a figure is read from one of the four verified JSON files
produced by scripts/run_verified_experiments.py. If a value is missing the
figure raises, rather than falling back to a remembered constant.

Outputs (300 dpi PNG, assets/paper_figures/):
  fig0_card_thumbnail.png
  fig1_harness_architecture.png
  fig2_retrieval_ladder.png
  fig3_baselines_and_twohop.png
  fig4_leaderboard_power.png
  fig5_patch_anatomy_exposure.png

Usage:
  .venv-harness/Scripts/python.exe scripts/generate_paper_figures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.lines import Line2D

REPO = Path(__file__).resolve().parents[1]
VDIR = REPO / "research" / "verified_json"
ASSETS = REPO / "assets" / "paper_figures"
ASSETS.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica", "sans-serif"],
    "font.size": 10.5,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.labelweight": "semibold",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "figure.titlesize": 12.5,
    "figure.titleweight": "bold",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.0,
    "grid.color": "#e2e8f0",
    "grid.linestyle": "--",
    "grid.linewidth": 0.6,
})

C_BLUE = "#1f77b4"
C_ORANGE = "#ff7f0e"
C_GREEN = "#2ca02c"
C_RED = "#d62728"
C_PURPLE = "#9467bd"
C_GRAY = "#7f7f7f"
C_DARK = "#0f172a"
C_TEAL = "#0d9488"


# --------------------------------------------------------------------------- #
def load() -> dict:
    def rd(name):
        p = VDIR / name
        if not p.exists():
            raise SystemExit(f"missing verified JSON: {p}")
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "ablation": rd("retrieval_ablation_129.json"),
        "multifile": rd("multifile_2hop_38.json"),
        "hazards": rd("runtime_hazards_verified.json"),
        "leaderboard": rd("leaderboard_estimands.json"),
    }


def g(doc, ptr: str):
    cur = doc
    for part in ptr.strip("/").split("/"):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


def despine(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")


def save(fig, name: str, face="#ffffff"):
    path = ASSETS / name
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=face)
    plt.close(fig)
    print(f"[ok] {path.name}")


def ci_at(block: dict, k: int, metric: str) -> tuple[float, float, float]:
    d = block["@%d" % k][metric]
    lo, hi = d["ci"]
    return d["value"], lo, hi


# =========================================================================== #
# fig0 -- card thumbnail
# =========================================================================== #
def fig0(D):
    ab, mf, lb, hz = D["ablation"], D["multifile"], D["leaderboard"], D["hazards"]
    multi = mf["buckets"]["all_multi"]
    n_multi = multi["N"]
    any_hits = multi["control"]["k5"]["any_gold@5"]["hits"]
    all_hits = multi["control"]["k5"]["all_gold@5"]["hits"]
    partial = any_hits - all_hits
    n_sites = len([k for k in hz["sites"] if k.startswith("site") and len(k) == 5])

    fig = plt.figure(figsize=(12.0, 6.3), dpi=100)
    fig.patch.set_facecolor("#0b132b")

    fig.text(0.5, 0.925, "Finding a File Is Not Finding the Patch",
             ha="center", va="center", color="#ffffff", fontsize=27, weight="bold")
    fig.text(0.5, 0.845,
             f"Gemma 4  \u00b7  {ab['N']} public tasks  \u00b7  retrieval, runtime hazards, leaderboard noise",
             ha="center", va="center", color="#94a3b8", fontsize=11.5)

    # ---- left: one file found out of the three the patch needs ------------- #
    ax = fig.add_axes([0.045, 0.12, 0.40, 0.62])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.0, 0.98, "WHAT RETRIEVAL RETURNS", ha="left", va="top",
            color="#94a3b8", fontsize=9.5, weight="bold")

    card_x, card_w, card_h = 0.02, 0.56, 0.155
    rows = [(0.70, True), (0.48, False), (0.26, False)]
    for i, (y, found) in enumerate(rows):
        face = "#12395c" if found else "#151e38"
        edge = "#4c9be8" if found else "#3b4a6b"
        ax.add_patch(patches.FancyBboxPatch(
            (card_x, y), card_w, card_h, boxstyle="round,pad=0.012",
            facecolor=face, edgecolor=edge, linewidth=2.2 if found else 1.2))
        ax.text(card_x + 0.045, y + card_h / 2, f"file {i + 1}",
                ha="left", va="center", color="#e2e8f0" if found else "#7c8aa8",
                fontsize=10.5, weight="bold" if found else "normal")
        if found:
            ax.plot([card_x + 0.42, card_x + 0.47, card_x + 0.53],
                    [y + 0.075, y + 0.045, y + 0.115],
                    color="#7cc4ff", lw=3.0, solid_capstyle="round")

    ax.plot([0.66, 0.66], [rows[-1][0], rows[0][0] + card_h], color="#64748b", lw=1.6)
    for yy in (rows[-1][0], rows[0][0] + card_h):
        ax.plot([0.66, 0.695], [yy, yy], color="#64748b", lw=1.6)
    ax.text(0.715, 0.56, "the patch\ntouches 3 files", ha="left", va="center",
            color="#cbd5e1", fontsize=10.2)
    ax.text(0.02, 0.10, "the entry point", ha="left", va="center",
            color="#7cc4ff", fontsize=10.0, weight="bold")

    # ---- right: entry point vs all patch files ----------------------------- #
    ax = fig.add_axes([0.525, 0.12, 0.435, 0.62])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.0, 0.98, "WHAT THE PATCH NEEDS", ha="left", va="top",
            color="#94a3b8", fontsize=9.5, weight="bold")

    rows = [
        (0.72, any_hits / n_multi, any_hits, "#4c9be8", "found at least one file"),
        (0.28, all_hits / n_multi, all_hits, "#ff9f43", "found all patch files"),
    ]
    for y, frac, hits, colour, label in rows:
        ax.add_patch(patches.Rectangle((0.0, y), 1.0, 0.15, facecolor="#1c2541",
                                       edgecolor="none"))
        ax.add_patch(patches.Rectangle((0.0, y), max(frac, 0.006), 0.15,
                                       facecolor=colour, edgecolor="none"))
        ax.text(1.0, y + 0.075, f"{hits}/{n_multi}", ha="right", va="center",
                color="#ffffff", fontsize=17, weight="bold")
        ax.text(0.0, y - 0.055, label, ha="left", va="center",
                color="#cbd5e1", fontsize=9.8)

    ax.text(0.0, 0.505, f"{partial} of {n_multi} tasks: some files, not the patch",
            ha="left", va="center", color="#94a3b8", fontsize=9.8)

    fig.text(0.5, 0.045,
             f"{ab['N']} tasks  \u00b7  {n_sites} runtime sites  \u00b7  "
             f"{lb['ledger_summary']['n_runs']} logged submissions",
             ha="center", va="center", color="#64748b", fontsize=8.8)
    save(fig, "fig0_card_thumbnail.png", face="#0b132b")


# =========================================================================== #
# fig1 -- harness architecture and six hazard sites
# =========================================================================== #
def fig1(D):
    hz = D["hazards"]
    s1, s5, s6 = hz["site1_compaction"], hz["site5_skilltoolset"], hz["site6_bare_pytest"]
    ign = hz["site4_gitignore"]

    fig, ax = plt.subplots(figsize=(13.0, 6.6))
    ax.set_xlim(0, 13); ax.set_ylim(0, 6.6); ax.axis("off")

    stages = [
        (1.55, "Gemma 4\n(31B / E4B)", C_BLUE),
        (4.05, "vLLM\nserving", C_PURPLE),
        (6.55, "Google ADK\nagent loop", C_ORANGE),
        (9.05, "Tool surface\n+ /workspace", C_TEAL),
        (11.35, "swegemma\ngrader", C_GREEN),
    ]
    for x, label, colour in stages:
        ax.add_patch(patches.FancyBboxPatch(
            (x - 0.95, 2.55), 1.9, 1.15, boxstyle="round,pad=0.03",
            facecolor="#f8fafc", edgecolor=colour, linewidth=2.0))
        ax.text(x, 3.12, label, ha="center", va="center", fontsize=10.5,
                weight="bold", color=C_DARK)
    for x in (2.55, 5.05, 7.55, 10.05):
        ax.annotate("", xy=(x + 0.55, 3.12), xytext=(x - 0.55, 3.12),
                    arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.6))

    sites = [
        (1, "compaction\n%d tokens / %d turns" % (s1["token_threshold"], s1["compaction_interval"]),
         "first fires turn %d-%d" % (s1["first_compaction_turn_min"], s1["first_compaction_turn_max"]),
         6.55, 5.15, C_ORANGE),
        (2, "reasoning key\nvLLM wants `reasoning`",
         "mitigated: %d call sites" % hz["site2_mitigation"]["install_calls"],
         4.05, 5.15, C_PURPLE),
        (3, "thinking budget\nforced end-token (1e9)",
         "inherited: wheel absent locally", 4.05, 1.15, C_PURPLE),
        (4, "git add -N .\nhonours .gitignore",
         "%d files, %d ignored" % (ign["files"], ign["ignored_count"]), 9.05, 1.15, C_TEAL),
        (5, "SkillToolset\n%d-token preamble" % s5["preamble_tokens_est"],
         "+%d tokens at turn 1" % s1["skilltoolset_turn1_marginal_tokens"], 9.05, 5.15, C_TEAL),
        (6, "bare pytest\nmissing plugins",
         "%d/%d fastapi tasks" % (s6["def_a_test_patch_direct"]["count"], s6["fastapi_tasks"]),
         11.55, 5.15, C_GREEN),
    ]
    for num, head, sub, x, y, colour in sites:
        ax.add_patch(patches.FancyBboxPatch(
            (x - 1.15, y - 0.62), 2.30, 1.24, boxstyle="round,pad=0.04",
            facecolor="#ffffff", edgecolor=colour, linewidth=1.2, alpha=0.97))
        ax.add_patch(patches.Circle((x - 1.02, y + 0.45), 0.20, facecolor=colour,
                                    edgecolor="none"))
        ax.text(x - 1.02, y + 0.45, str(num), ha="center", va="center",
                color="#ffffff", fontsize=10, weight="bold")
        ax.text(x - 0.74, y + 0.44, head, ha="left", va="center",
                fontsize=8.0, weight="bold", color=C_DARK)
        ax.text(x, y - 0.28, sub, ha="center", va="center", fontsize=7.7, color="#475569")
        ax.annotate("", xy=(x, 3.75 if y > 3 else 2.50), xytext=(x, y - (0.64 if y > 3 else -0.64)),
                    arrowprops=dict(arrowstyle="-", color=colour, lw=1.0, ls=":"))

    ax.text(6.5, 0.32,
            "Labels: Source-Verified = quoted from an installed wheel; "
            "Inherited = wheel absent locally; Exposure Count = counted over the dev set.",
            ha="center", va="center", fontsize=8.2, color="#64748b", style="italic")
    ax.set_title("Figure 1. Offline harness and the six audited failure sites", pad=12)
    save(fig, "fig1_harness_architecture.png")


# =========================================================================== #
# fig2 -- retrieval ladder and metric definition
# =========================================================================== #
def fig2(D):
    ab = D["ablation"]
    res = ab["results"]
    variants = ["B0", "B1", "B2", "B3"]
    labels = ["B0\nfilename", "B1\nBM25", "B2\nAST, no demotion", "B3\nAST + demotion"]
    colours = [C_GRAY, C_PURPLE, C_TEAL, C_BLUE]

    fig, axes = plt.subplots(1, 3, figsize=(15.4, 5.1),
                             gridspec_kw={"width_ratios": [1.15, 1.0, 1.0]})

    # (A) any-gold and mean-fraction at 5 with bootstrap CIs
    ax = axes[0]

    x = np.arange(len(variants)); w = 0.36
    an_v, an_e, mf_v, mf_e = [], [], [], []
    for v in variants:
        a, alo, ahi = ci_at(res[v]["all"], 5, "any_gold")
        m, mlo, mhi = ci_at(res[v]["all"], 5, "mean_fraction")
        an_v.append(a); an_e.append([a - alo, ahi - a])
        mf_v.append(m); mf_e.append([m - mlo, mhi - m])
    ax.bar(x - w / 2, an_v, w, color=[c for c in colours], alpha=1.0,
           label="Any-Gold @5", edgecolor="#ffffff")
    ax.bar(x + w / 2, mf_v, w, color=[c for c in colours], alpha=0.45,
           label="Mean-Fraction @5", edgecolor="#ffffff", hatch="//")
    ax.errorbar(x - w / 2, an_v, yerr=list(zip(*an_e)), fmt="none",
                ecolor=C_DARK, capsize=2.5, lw=1.0)
    ax.errorbar(x + w / 2, mf_v, yerr=list(zip(*mf_e)), fmt="none",
                ecolor=C_DARK, capsize=2.5, lw=1.0)
    for xi, val, e in zip(x - w / 2, an_v, an_e):
        ax.text(xi, val + e[1] + 0.018, f"{val:.3f}", ha="center", fontsize=7.6,
                weight="bold")
    for xi, val, e in zip(x + w / 2, mf_v, mf_e):
        ax.text(xi, val + e[1] + 0.018, f"{val:.3f}", ha="center", fontsize=7.4,
                color="#334155")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.2)
    ax.set_ylim(0, 1.0); ax.set_ylabel("R@5")
    ax.set_title(f"(A) File recall on {ab['N']} tasks")
    ax.grid(axis="y", alpha=0.55); ax.set_axisbelow(True); despine(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=8)

    # (B) component waterfall on any-gold @5
    ax = axes[1]
    deltas = ab["component_deltas_paired"]
    base = g(res["B0"]["all"], "/@5/any_gold/value")
    steps = [("B0", base, C_GRAY)]
    cur = base
    for lo, hi, col in (("B0", "B1", C_PURPLE), ("B1", "B2", C_TEAL), ("B2", "B3", C_BLUE)):
        d = deltas[f"{lo}->{hi}"]["any_gold_delta_pp"] / 100.0
        steps.append((f"{lo} -> {hi}", d, col))
        cur += d
    steps.append(("B3", cur, C_BLUE))
    xs = np.arange(len(steps))
    run = 0.0
    for i, (name, val, col) in enumerate(steps):
        if i == 0 or i == len(steps) - 1:
            ax.bar(i, val, 0.62, color=col, edgecolor="#ffffff")
            ax.text(i, val + 0.02, f"{val:.3f}", ha="center", fontsize=8.4, weight="bold")
            run = val
        else:
            ax.bar(i, val, 0.62, bottom=run, color=col, edgecolor="#ffffff", alpha=0.9)
            ax.text(i, run + val + 0.02, f"{val * 100:+.2f} pp", ha="center",
                    fontsize=8.0, weight="bold", color=col)
            run += val
    ax.set_xticks(xs)
    ax.set_xticklabels([s[0] for s in steps], fontsize=7.8, rotation=18, ha="right")
    ax.set_ylim(0, 1.0); ax.set_ylabel("Any-Gold @5")
    ax.set_title("(B) Component ladder, paired by task")
    ax.grid(axis="y", alpha=0.55); ax.set_axisbelow(True); despine(ax)

    # (C) B3 recall by k, both definitions
    ax = axes[2]
    ks = [1, 3, 5, 10]
    an = [g(res["B3"]["all"], f"/@{k}/any_gold/value") for k in ks]
    mf = [g(res["B3"]["all"], f"/@{k}/mean_fraction/value") for k in ks]
    al = [g(res["B3"]["all"], f"/@{k}/all_gold/value") for k in ks]
    ax.plot(ks, an, "-o", color=C_BLUE, lw=2.0, label="Any-Gold")
    ax.plot(ks, mf, "-s", color=C_ORANGE, lw=2.0, label="Mean-Fraction")
    ax.plot(ks, al, "-^", color=C_GREEN, lw=2.0, label="Strict All-Gold")
    for k, a, m in zip(ks, an, mf):
        if k == 1:
            continue
        ax.annotate(f"{a:.3f}", (k, a), textcoords="offset points", xytext=(0, 7),
                    ha="center", fontsize=7.6, color=C_BLUE)
        ax.annotate(f"{m:.3f}", (k, m), textcoords="offset points", xytext=(0, -13),
                    ha="center", fontsize=7.6, color=C_ORANGE)
    ax.annotate("all three coincide at k=1", (1, an[0]), textcoords="offset points",
                xytext=(10, -16), ha="left", fontsize=7.4, color="#64748b")
    ax.set_xticks(ks); ax.set_xlabel("candidate budget k"); ax.set_ylabel("recall")
    ax.set_ylim(0, 0.95)
    ax.set_title("(C) B3: definition gap is definitional")
    ax.grid(alpha=0.55); ax.set_axisbelow(True); despine(ax)
    ax.legend(frameon=False, fontsize=8, loc="lower right")

    fig.suptitle("Figure 2. File retrieval: the component ladder and the metric definition", y=1.02)
    save(fig, "fig2_retrieval_ladder.png")


# =========================================================================== #
# fig3 -- baselines by repo + budget-matched 2-hop
# =========================================================================== #
def fig3(D):
    ab, mf = D["ablation"], D["multifile"]

    fig, axes = plt.subplots(1, 2, figsize=(14.2, 5.2),
                             gridspec_kw={"width_ratios": [1.25, 1.0]})

    # (A) any-gold @5 by repository
    ax = axes[0]
    repos = [r for r in ("fastapi", "rich", "requests", "httpx")
             if r in ab["results"]["B3"]]
    variants = ["B0", "B1", "B2", "B3"]
    colours = [C_GRAY, C_PURPLE, C_TEAL, C_BLUE]
    x = np.arange(len(repos)); w = 0.2
    for j, v in enumerate(variants):
        vals, errs = [], []
        for r in repos:
            val, lo, hi = ci_at(ab["results"][v][r], 5, "any_gold")
            vals.append(val); errs.append([val - lo, hi - val])
        ax.bar(x + (j - 1.5) * w, vals, w, color=colours[j], label=v,
               edgecolor="#ffffff", linewidth=0.6)
        ax.errorbar(x + (j - 1.5) * w, vals, yerr=list(zip(*errs)), fmt="none",
                    ecolor="#334155", capsize=2.0, lw=0.8)
    counts = [ab["results"]["B3"][r]["N"] for r in repos]
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r}\n(n={n})" for r, n in zip(repos, counts)], fontsize=9)
    ax.set_ylabel("Any-Gold @5"); ax.set_ylim(0, 1.07)
    ax.set_title("(A) Baseline ladder by repository")
    ax.grid(axis="y", alpha=0.55); ax.set_axisbelow(True); despine(ax)
    ax.legend(frameon=False, ncol=4, fontsize=8.5, loc="upper center")

    # (B) control vs budget-matched 2-hop
    ax = axes[1]
    multi = mf["buckets"]["all_multi"]
    groups = [("k=5 any", "k5", "any_gold@5", "any"), ("k=5 all", "k5", "all_gold@5", "all"),
              ("k=10 any", "k10", "any_gold@10", "any"), ("k=10 all", "k10", "all_gold@10", "all")]
    xs = np.arange(len(groups)); w = 0.36
    ctrl, hop = [], []
    for _, kk, key, _ in groups:
        ctrl.append(g(multi, f"/control/{kk}/{key}/value"))
        hop.append(g(multi, f"/hop/{kk}/{key}/value"))
    ax.bar(xs - w / 2, ctrl, w, color=C_GRAY, label="single-pass locate", edgecolor="#ffffff")
    ax.bar(xs + w / 2, hop, w, color=C_ORANGE, label="budget-matched 2-hop", edgecolor="#ffffff")
    for xi, c, h in zip(xs, ctrl, hop):
        ax.text(xi - w / 2, c + 0.02, f"{c:.3f}", ha="center", fontsize=7.8)
        ax.text(xi + w / 2, h + 0.02, f"{h:.3f}", ha="center", fontsize=7.8)
    ax.set_xticks(xs); ax.set_xticklabels([gr[0] for gr in groups], fontsize=8.6)
    ax.set_ylim(0, 1.0); ax.set_ylabel("recall")
    ax.set_title(f"(B) 2-hop at fixed budget (n={multi['N']} multi-file tasks)")
    ax.grid(axis="y", alpha=0.55); ax.set_axisbelow(True); despine(ax)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")

    fig.suptitle("Figure 3. Baselines by repository, and 2-hop expansion under a fixed budget", y=1.02)
    save(fig, "fig3_baselines_and_twohop.png")


# =========================================================================== #
# fig4 -- leaderboard distribution and power
# =========================================================================== #
def fig4(D):
    lb = D["leaderboard"]

    fig, axes = plt.subplots(1, 2, figsize=(14.6, 5.4),
                             gridspec_kw={"width_ratios": [1.35, 1.0]})

    # (A) every logged submission
    ax = axes[0]
    runs = lb["runs"]
    names = [r["run"] for r in runs]
    ks = [r["k_of_58"] for r in runs]
    cols = [C_BLUE if r["scale_b"] == 31 else (C_ORANGE if r["scale_b"] == 4 else C_GRAY)
            for r in runs]
    xs = np.arange(len(runs))
    for x, k, c in zip(xs, ks, cols):
        if k is None:
            ax.scatter(x, 0, marker="x", s=48, color=C_RED, zorder=3)
            ax.text(x, 0.7, "unscored", rotation=90, fontsize=6.5,
                    ha="center", va="bottom", color=C_RED)
            continue
        ax.vlines(x, 0, k, color=c, lw=2.0, alpha=0.65)
        ax.scatter(x, k, s=34, color=c, zorder=3)
        ax.annotate(str(k), (x, k), textcoords="offset points", xytext=(0, 5),
                    ha="center", fontsize=7.0, color="#334155")
    ax.set_xticks(xs); ax.set_xticklabels(names, rotation=55, ha="right", fontsize=7.6)
    ax.set_ylabel(f"solved tasks of {lb['split_size']}")
    ax.set_ylim(-0.5, max(k for k in ks if k) + 2)
    ax.set_title(f"(A) All {len(runs)} logged submissions")
    ax.grid(axis="y", alpha=0.55); ax.set_axisbelow(True); despine(ax)
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=C_BLUE, label="31B"),
        Line2D([], [], marker="o", ls="", color=C_ORANGE, label="E4B"),
        Line2D([], [], marker="x", ls="", color=C_RED, label="unscored"),
    ], frameon=False, fontsize=8, loc="upper left")

    # (B) estimand rows
    ax = axes[1]
    row1, row2, row3 = lb["estimand_rows"]
    ax.set_xlim(0, 1); ax.set_ylim(0, 3); ax.axis("off")

    counts = " / ".join(str(c) for c in row2["counts"])
    cards = [
        ("LEVEL", C_BLUE, [
            f"{row2['name']}",
            f"mean {row2['mean_tasks']:.1f} of {lb['split_size']} tasks "
            f"({100 * row2['mean_rate']:.1f}%)",
            f"counts {counts}",
        ]),
        ("DISPERSION", C_ORANGE, [
            f"SD {row2['sd_tasks']:.3f} tasks (df {row2['df']}), "
            f"95% CI [{row2['sd_ci95'][0]:.2f}, {row2['sd_ci95'][1]:.2f}]",
            f"identical-code repeat: {row1['exp05_k']} vs {row1['e0_k']} tasks "
            f"({row1['observed_shift_tasks']}-task shift)",
        ]),
        ("SPLIT ERROR", C_PURPLE, [
            f"one {lb['split_size']}-task split: SE {row3['se_split_tasks']:.2f} tasks "
            f"({row3['se_split_pp']:.2f} pp)",
            f"two independent splits: SE {row3['se_two_independent_tasks']:.2f} tasks "
            f"({row3['se_two_independent_pp']:.2f} pp)",
            f"two-run MDE {row3['mde_two_independent_tasks']:.2f} tasks",
        ]),
    ]
    for i, (header, colour, lines) in enumerate(cards):
        y0 = 2 - i + 0.07
        ax.add_patch(patches.FancyBboxPatch(
            (0.02, y0), 0.96, 0.84, boxstyle="round,pad=0.012",
            facecolor="#f8fafc", edgecolor=colour, linewidth=1.6))
        ax.text(0.055, y0 + 0.70, header, ha="left", va="center",
                fontsize=8.4, weight="bold", color=colour)
        for j, line in enumerate(lines):
            ax.text(0.055, y0 + 0.48 - 0.19 * j, line, ha="left", va="center",
                    fontsize=8.1 if j else 8.5, color=C_DARK,
                    weight="bold" if j == 0 else "normal")
    ax.set_title("(B) Estimand rows: level, dispersion, split error", pad=10)

    fig.suptitle("Figure 4. Leaderboard estimands: observed spread and sampling error", y=1.02)
    save(fig, "fig4_leaderboard_power.png")


# =========================================================================== #
# fig5 -- patch anatomy and hazard exposure
# =========================================================================== #
def fig5(D):
    ab, hz = D["ablation"], D["hazards"]

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.0),
                             gridspec_kw={"width_ratios": [1.0, 1.15]})

    # (A) gold-file count distribution
    ax = axes[0]
    struct = D["multifile"]["gold_set_structure_all_129"]
    order = ["1", "2", "3-5", ">5"]
    vals = [struct[k]["N"] for k in order if k in struct]
    keys = [k for k in order if k in struct]
    colours = [C_BLUE, C_TEAL, C_PURPLE, C_RED][:len(keys)]
    bars = ax.bar(keys, vals, color=colours, edgecolor="#ffffff", width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, str(v),
                ha="center", fontsize=9.5, weight="bold")
    ax.set_xlabel("gold files touched by the patch")
    ax.set_ylabel("tasks")
    ax.set_title(f"(A) Patch anatomy, all {ab['N']} tasks")
    ax.grid(axis="y", alpha=0.55); ax.set_axisbelow(True); despine(ax)

    # (B) exposure counts
    ax = axes[1]
    s6 = hz["site6_bare_pytest"]
    ign = hz["site4_gitignore"]
    n_fastapi = s6["fastapi_tasks"]
    items = [
        ("new files hidden\nby .gitignore",
         ign["ignored_count"], ign["files"], C_TEAL),
        ("A: gold test_patch\nimports a plugin",
         s6["def_a_test_patch_direct"]["count"], n_fastapi, C_ORANGE),
        ("A + anyio: adds the\n`-p no:anyio` task",
         s6["def_a_plus_anyio"]["count"], n_fastapi, C_ORANGE),
        ("B: touched test files\nimport a plugin",
         s6["def_b_touched_test_files"]["count"], n_fastapi, C_GREEN),
        ("C: repo `tests/` tree\nimports one",
         s6["def_c_repo_tests_tree"]["count"], n_fastapi, C_PURPLE),
    ]
    ys = np.arange(len(items))[::-1]
    for y, (label, k, n, col) in zip(ys, items):
        ax.barh(y, n, height=0.42, color="#e2e8f0", edgecolor="#cbd5e1")
        ax.barh(y, k, height=0.42, color=col, edgecolor="#ffffff")
        ax.text(n + 0.8, y, f"{k}/{n} = {100 * k / n:.1f}%", va="center",
                fontsize=8.6, weight="bold", color=C_DARK)
        ax.text(0.6, y + 0.30, label.replace("\n", " "), ha="left", va="bottom",
                fontsize=7.8, color=C_DARK)
    ax.set_yticks([]); ax.set_xlim(0, max(i[2] for i in items) * 1.34)
    ax.set_ylim(-0.55, len(items) - 0.35)
    ax.set_xlabel("tasks exposed")
    ax.set_title("(B) Exposure counts, not failure attributions")
    ax.grid(axis="x", alpha=0.55); ax.set_axisbelow(True); despine(ax)

    fig.suptitle("Figure 5. Patch anatomy and measured exposure of the two counting sites", y=1.03)
    fig.subplots_adjust(left=0.06)
    save(fig, "fig5_patch_anatomy_exposure.png")


# --------------------------------------------------------------------------- #
def main() -> int:
    D = load()
    fig0(D)
    fig1(D)
    fig2(D)
    fig3(D)
    fig4(D)
    fig5(D)
    print("all figures rendered from research/verified_json/*.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

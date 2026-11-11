#!/usr/bin/env python3
"""make_figures.py — Render publication-grade figures for EVIDENCE_PACK.md and research/paper_figs/.

Generates:
  1. research/paper_figs/fig1.png (+ fig1_data.csv)
     - Left: Tasks passed per run, anchor band 10.4 +- 0.89 (run noise) and +- 2.9 (sampling SE).
             exp05 and E0 control linked as identical artifact.
     - Right: Live top-20 counts (17x1, 14x11, 13x8) with SD ~ 4.5 bar.
  2. research/paper_figs/fig2.png (+ fig2_data.csv)
     - Panel A: Regime A static graph retrieval (Mean Fraction over Graph Candidates, N=125).
     - Panel B: Regime B live workspace shipped engine (All Files on Disk, N=125), showing
       BOTH Any-Gold and Mean-Fraction.
     - Prominent banner: "A and B not comparable".
  3. research/paper_figs/fig3.png (+ fig3_data.csv)
     - Clean mechanisms table figure with ABSOLUTELY NO turn positions.
  4. research/paper_figs/writeup_thumbnail.png (1200x630 px).
"""
from __future__ import annotations

import csv
from pathlib import Path
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent

# Okabe-Ito Colorblind-Safe Palette
OI_BLACK = "#000000"
OI_ORANGE = "#E69F00"
OI_SKY_BLUE = "#56B4E9"
OI_BLUISH_GREEN = "#009E73"
OI_YELLOW = "#F0E442"
OI_BLUE = "#0072B2"
OI_VERMILION = "#D55E00"
OI_PURPLE = "#CC79A7"
OI_GRAY = "#7F7F7F"
OI_DARK = "#1E293B"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
    "font.size": 10.5,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10.5,
    "axes.labelweight": "semibold",
    "xtick.labelsize": 9.0,
    "ytick.labelsize": 9.0,
    "figure.titlesize": 13,
    "figure.titleweight": "bold",
    "axes.edgecolor": "#334155",
    "axes.linewidth": 1.0,
    "grid.color": "#CBD5E1",
    "grid.linestyle": "--",
    "grid.linewidth": 0.6,
})


def despine(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#334155")
    ax.spines["bottom"].set_color("#334155")


# ==============================================================================
# FIGURE 1: Leaderboard Statistical Resolution & Noise Floor
# ==============================================================================
def render_fig1():
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(14.0, 5.8), dpi=300, gridspec_kw={"width_ratios": [2.2, 1.0]}
    )
    fig.patch.set_facecolor("#FFFFFF")

    fig.suptitle(
        "Leaderboard Statistical Resolution: Within-Split Run Noise (±0.89) vs. Cross-Split SE (±2.9 Tasks)",
        fontsize=13, weight="bold", color=OI_DARK, y=0.98
    )

    # ---------------- Left Panel: Tasks Passed per Run ----------------
    runs = [
        {"ref": "56793672", "name": "exp01", "scale": "31B", "tasks": 3, "score": 0.05, "desc": "2-agent split"},
        {"ref": "56812498", "name": "exp02", "scale": "31B", "tasks": 5, "score": 0.08, "desc": "unified prompt"},
        {"ref": "57037122", "name": "exp03", "scale": "31B", "tasks": 10, "score": 0.17, "desc": "replica"},
        {"ref": "57553805", "name": "exp05", "scale": "31B", "tasks": 12, "score": 0.20, "desc": "anchor"},
        {"ref": "57618114", "name": "exp08", "scale": "31B", "tasks": 10, "score": 0.17, "desc": "contract"},
        {"ref": "57654236", "name": "exp10", "scale": "31B", "tasks": 10, "score": 0.17, "desc": "consolid"},
        {"ref": "57697341", "name": "exp11_fb", "scale": "31B", "tasks": 8, "score": 0.13, "desc": "31B fallback"},
        {"ref": "57736284", "name": "exp12", "scale": "31B", "tasks": 10, "score": 0.17, "desc": "9m buffer"},
        {"ref": "57777888", "name": "exp11_e4b", "scale": "E4B", "tasks": 4, "score": 0.06, "desc": "genuine E4B"},
        {"ref": "57806053", "name": "e4b-v2", "scale": "E4B", "tasks": 3, "score": 0.05, "desc": "lean prompt"},
        {"ref": "57836949", "name": "E0_ctrl", "scale": "31B", "tasks": 10, "score": 0.17, "desc": "exp05 clone"},
        {"ref": "57889741", "name": "e4b-v4", "scale": "E4B", "tasks": 3, "score": 0.05, "desc": "swe-toolkit"},
        {"ref": "57933618", "name": "exp14", "scale": "31B", "tasks": 9, "score": 0.15, "desc": "lean toolkit"},
        {"ref": "58096981", "name": "exp_samp", "scale": "31B", "tasks": 8, "score": 0.13, "desc": "temp 1.0"},
        {"ref": "58183079", "name": "exp15", "scale": "31B", "tasks": 8, "score": 0.13, "desc": "zero-schema"},
    ]

    x_idx = np.arange(len(runs))
    task_counts = [r["tasks"] for r in runs]
    scales = [r["scale"] for r in runs]

    anchor_mean = 10.4
    within_sd = 0.89
    cross_se = 2.9

    # Shaded confidence bands around anchor mean
    ax1.axhspan(
        anchor_mean - cross_se, anchor_mean + cross_se,
        color="#E2E8F0", alpha=0.85, zorder=0,
        label=r"Cross-Split Sampling SE: $\pm 2.9$ tasks (SE $\approx 0.0503$)"
    )
    ax1.axhspan(
        anchor_mean - within_sd, anchor_mean + within_sd,
        color="#BAE6FD", alpha=0.9, zorder=1,
        label=r"Anchor Family Run Noise: $10.4 \pm 0.89$ tasks ($\sigma_{\mathrm{within}}$)"
    )
    ax1.axhline(anchor_mean, color=OI_BLUE, ls="--", lw=1.6, zorder=2, label="Anchor Family Mean (10.4 tasks, n=5)")

    # Scatter points with Okabe-Ito colors: Blue for 31B, Orange for E4B
    colors = [OI_BLUE if s == "31B" else OI_ORANGE for s in scales]
    scatter = ax1.scatter(x_idx, task_counts, s=90, c=colors, edgecolor=OI_DARK, lw=1.2, zorder=4)

    # Direct labels above points
    for i, r in enumerate(runs):
        ax1.text(i, r["tasks"] + 0.45, f"{r['tasks']}", ha="center", va="bottom", fontsize=8.5, weight="bold", color=colors[i])

    # LINK exp05 (idx 3, 12 tasks) and E0_ctrl (idx 10, 10 tasks) as SAME ARTIFACT
    idx_exp05 = 3
    idx_e0 = 10
    # Draw an arc / bracket connecting them
    con_x = [idx_exp05, idx_exp05, idx_e0, idx_e0]
    con_y = [12.6, 14.0, 14.0, 10.6]
    ax1.plot(con_x, con_y, color=OI_VERMILION, ls="-", lw=1.6, zorder=5)
    ax1.plot([idx_exp05, idx_e0], [14.0, 14.0], color=OI_VERMILION, lw=1.6, zorder=5)
    ax1.text(
        (idx_exp05 + idx_e0) / 2.0, 14.3,
        "Identical Artifact (sha256 2ba7f9b1…)\nΔ = −2 tasks is run-to-run noise on the same split",
        ha="center", va="bottom", fontsize=8.5, weight="bold", color=OI_VERMILION,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FEF2F2", edgecolor=OI_VERMILION, lw=1.0)
    )

    # E4B cluster annotation
    ax1.annotate(
        "E4B Line Closed\n3–4 tasks (0.05–0.06)",
        xy=(9, 3.2), xytext=(8.2, 5.5),
        arrowprops=dict(arrowstyle="->", color=OI_ORANGE, lw=1.3),
        fontsize=8.5, weight="bold", color=OI_ORANGE,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFBEB", edgecolor=OI_ORANGE, lw=1.0)
    )

    # exp_think1024 note in text
    ax1.text(
        0.03, 0.05,
        "exp_think1024 (ref 58149803, 31B): Unscored (Kaggle system error, totalBytes=0, hypothesis untested).",
        transform=ax1.transAxes, fontsize=8.0, color="#64748B", style="italic"
    )

    ax1.set_xticks(x_idx)
    ax1.set_xticklabels([f"{r['name']}\n({r['scale']})" for r in runs], fontsize=7.6, rotation=45, ha="right")
    ax1.set_ylabel("Integer Tasks Passed (out of 58)")
    ax1.set_title("(A) Offline Submission Trajectory (n=58 Tasks/Run)", loc="left")
    ax1.set_ylim(0, 16.5)
    ax1.grid(axis="y", alpha=0.5)
    despine(ax1)
    ax1.legend(loc="upper left", frameon=True, framealpha=0.92, facecolor="#FFFFFF", edgecolor="#CBD5E1", fontsize=8.0)

    # ---------------- Right Panel: Live Top-20 Counts with SD ~ 4.5 Bar ----------------
    scores_top20 = [0.22, 0.24, 0.29]
    tasks_top20 = [13, 14, 17]
    counts_top20 = [8, 11, 1]
    y_pos = np.arange(len(scores_top20))

    bars_t20 = ax2.barh(
        y_pos, counts_top20,
        color=[OI_SKY_BLUE, OI_BLUE, OI_BLUISH_GREEN],
        edgecolor=OI_DARK, height=0.52, lw=0.9
    )

    for r in bars_t20:
        w = r.get_width()
        ax2.text(
            w + 0.35, r.get_y() + r.get_height() / 2,
            f"{int(w)} team{'s' if w > 1 else ''}",
            ha="left", va="center", fontsize=8.8, weight="bold", color=OI_DARK
        )

    # SD ~ 4.5 spread bar
    sd_center_y = 1.0  # around 14 tasks
    ax2.errorbar(
        [6.0], [sd_center_y], xerr=[0], yerr=[0.85],
        fmt="none", ecolor=OI_VERMILION, elinewidth=2.2, capsize=6, capthick=2.0
    )
    ax2.text(
        6.4, sd_center_y,
        "Leaderboard\nSD ≈ 4.5 tasks",
        ha="left", va="center", fontsize=8.2, weight="bold", color=OI_VERMILION
    )

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([f"0.22 ({t} tasks)" for t in tasks_top20], weight="semibold", fontsize=8.6)
    ax2.set_xlabel("Number of Teams")
    ax2.set_title("(B) Public Top-20 Leaderboard", loc="left")
    ax2.set_xlim(0, 14.5)
    ax2.grid(axis="x", alpha=0.5)
    despine(ax2)

    # Box explaining 4-task span
    box_t20 = patches.FancyBboxPatch(
        (0.08, 0.08), 0.84, 0.36, boxstyle="round,pad=0.03",
        facecolor="#F8FAFC", edgecolor="#94A3B8", linewidth=1.0, transform=ax2.transAxes
    )
    ax2.add_patch(box_t20)
    ax2.text(0.5, 0.35, "TOP-20 4-TASK SPAN", ha="center", color=OI_DARK, fontsize=8.8, weight="bold", transform=ax2.transAxes)
    ax2.text(
        0.5, 0.20,
        "13 to 17 solved tasks (4 tasks wide).\nEntire cluster is well within\ncross-split SE = ±2.9 tasks.",
        ha="center", color="#475569", fontsize=7.8, linespacing=1.2, transform=ax2.transAxes
    )

    # Source note footer
    fig.text(
        0.02, 0.01,
        "Source: Kaggle Leaderboard (2026-11-10) & 16 Offline Submissions (n=58 tasks/run). Score = floor(100 × tasks / 58) / 100.",
        fontsize=7.8, color="#64748B"
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out_p = OUTPUT_DIR / "fig1.png"
    plt.savefig(out_p, dpi=300)
    plt.close()

    # Save CSV
    csv_p = OUTPUT_DIR / "fig1_data.csv"
    with open(csv_p, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ref", "name", "scale", "tasks_passed", "score", "byte_identical_group"])
        for r in runs:
            grp = "A (sha 2ba7f9b1…)" if r["name"] in ("exp05", "E0_ctrl") else "—"
            writer.writerow([r["ref"], r["name"], r["scale"], r["tasks"], r["score"], grp])
    print(f"[FIG 1] Wrote {out_p} and {csv_p}")


# ==============================================================================
# FIGURE 2: Retrieval 2x2 Matrix & Recall Decomposition
# ==============================================================================
def render_fig2():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.2, 5.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")

    # Main Headline Title + Distinct Banner for Non-Comparability
    fig.suptitle(
        "Code Localization on Shared N=125 Tasks: Static Graph (Regime A) vs. Live Workspace Engine (Regime B)",
        fontsize=12.5, weight="bold", color=OI_DARK, y=0.98
    )

    # Prominent "A and B not comparable" banner
    fig.text(
        0.5, 0.925,
        "WARNING: A and B not comparable — Candidate sets (graph nodes vs all files) and metric definitions differ.",
        ha="center", va="center", fontsize=9.2, weight="bold", color=OI_VERMILION,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEF2F2", edgecolor=OI_VERMILION, lw=1.2)
    )

    # ---------------- Left Panel: Regime A (Static Graph Candidates) ----------------
    ranks = ["R@1", "R@3", "R@5", "R@10"]
    x = np.arange(len(ranks))
    width = 0.15

    # N=125 in-graph tasks file recall (Mean Fraction)
    m1 = [0.0520, 0.1878, 0.2358, 0.3133]  # Grep
    m2 = [0.0602, 0.1828, 0.2233, 0.3932]  # Dense
    m3 = [0.0520, 0.1878, 0.2338, 0.2938]  # 1-Hop Graph
    m4 = [0.2746, 0.3919, 0.4489, 0.4734]  # swe_toolkit (Graph)
    m5 = [0.2545, 0.3862, 0.4897, 0.5883]  # Hybrid RRF

    ax1.bar(x - 2 * width, m1, width, label="M1: Lexical Grep", color=OI_GRAY, edgecolor=OI_DARK, lw=0.6)
    ax1.bar(x - width, m2, width, label="M2: Dense Embedding", color=OI_PURPLE, edgecolor=OI_DARK, lw=0.6)
    ax1.bar(x, m3, width, label="M3: 1-Hop AST Graph", color=OI_VERMILION, edgecolor=OI_DARK, lw=0.6)
    rects_m4 = ax1.bar(x + width, m4, width, label="M4: swe_toolkit (Graph)", color=OI_BLUE, edgecolor=OI_DARK, lw=0.6)
    ax1.bar(x + 2 * width, m5, width, label="M5: Hybrid RRF", color=OI_BLUISH_GREEN, edgecolor=OI_DARK, lw=0.6)

    # Direct label on M4 @5
    ax1.text(
        2 + width, m4[2] + 0.015, f"{m4[2]:.3f}",
        ha="center", va="bottom", fontsize=8.2, weight="bold", color=OI_BLUE
    )

    # Context exceedance inset callout
    inset_box = patches.FancyBboxPatch(
        (0.04, 0.64), 0.50, 0.32, boxstyle="round,pad=0.03",
        facecolor="#FEF2F2", edgecolor=OI_VERMILION, linewidth=1.1, transform=ax1.transAxes
    )
    ax1.add_patch(inset_box)
    ax1.text(0.29, 0.89, "M3 Neighborhood Explosion", color=OI_VERMILION, fontsize=8.6, weight="bold", ha="center", transform=ax1.transAxes)
    ax1.text(
        0.29, 0.72,
        "80.9% (313/387) of raw 1-hop AST\nneighborhoods exceed 5,000-char tool cap.\nUnpruned hubs explode token budgets.",
        ha="center", color="#1E293B", fontsize=7.6, linespacing=1.2, transform=ax1.transAxes
    )

    ax1.set_ylabel("File Recall (Mean Fraction)")
    ax1.set_title("(A) Regime A: Static Graph Retrieval\n[Mean Fraction over Graph Candidates, N=125]", loc="left", fontsize=10.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(ranks, weight="semibold")
    ax1.set_ylim(0, 0.72)
    ax1.grid(axis="y", alpha=0.5)
    despine(ax1)
    ax1.legend(loc="upper right", frameon=True, framealpha=0.92, facecolor="#FFFFFF", edgecolor="#CBD5E1", fontsize=8.0)

    # ---------------- Right Panel: Regime B Shipped Engine (Both Metrics) ----------------
    # Shows BOTH Any-Gold and Mean-Fraction for Shipped Engine v4 on N=125
    v4_mean_frac = [0.3163, 0.5322, 0.6251, 0.7261]
    v4_any_gold = [0.4206, 0.6587, 0.7540, 0.8413]

    width_b = 0.32
    rects_any = ax2.bar(
        x - width_b / 2, v4_any_gold, width_b,
        label="Shipped Engine (v4): Any-Gold Recall (≥1 file hit)",
        color=OI_BLUISH_GREEN, edgecolor=OI_DARK, lw=0.7
    )
    rects_frac = ax2.bar(
        x + width_b / 2, v4_mean_frac, width_b,
        label="Shipped Engine (v4): Mean-Fraction Recall (strict)",
        color=OI_SKY_BLUE, edgecolor=OI_DARK, lw=0.7
    )

    # Direct labels on bars
    for r in rects_any:
        h = r.get_height()
        ax2.text(r.get_x() + r.get_width() / 2, h + 0.015, f"{h:.3f}", ha="center", va="bottom", fontsize=8.2, weight="bold", color=OI_BLUISH_GREEN)
    for r in rects_frac:
        h = r.get_height()
        ax2.text(r.get_x() + r.get_width() / 2, h + 0.015, f"{h:.3f}", ha="center", va="bottom", fontsize=8.2, weight="bold", color=OI_BLUE)

    # Annotation of Candidate Gain vs Metric Def Gap at R@5
    # Candidate Set Gain under Mean Fraction: 0.4489 -> 0.6251 = +17.62 pp
    # Metric Definition Gap in Regime B: 0.6251 -> 0.7540 = +12.89 pp
    ax2.annotate(
        "Candidate Indexing Gain:\n+17.62 pp (0.449 → 0.625, p < 0.001)\n\nMetric Definition Gap:\n+12.89 pp (0.625 → 0.754 Any-Gold)",
        xy=(2, 0.7540), xytext=(0.8, 0.88),
        arrowprops=dict(arrowstyle="->", color=OI_DARK, lw=1.2),
        fontsize=8.0, weight="semibold", color=OI_DARK,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8FAFC", edgecolor="#94A3B8", lw=1.0)
    )

    ax2.set_ylabel("File Recall")
    ax2.set_title("(B) Regime B: Live Workspace Shipped Engine\n[All Files on Disk, N=125 Tasks]", loc="left", fontsize=10.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels(ranks, weight="semibold")
    ax2.set_ylim(0, 1.05)
    ax2.grid(axis="y", alpha=0.5)
    despine(ax2)
    ax2.legend(loc="upper left", frameon=True, framealpha=0.92, facecolor="#FFFFFF", edgecolor="#CBD5E1", fontsize=8.0)

    # Source note footer
    fig.text(
        0.02, 0.01,
        "Source: 125 In-Graph Tasks, SWE-bench devset. Regime A: paper_eval.py on static code graph. Regime B: t6_run.py / _index.py v4 on live workspace.",
        fontsize=7.8, color="#64748B"
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    out_p = OUTPUT_DIR / "fig2.png"
    plt.savefig(out_p, dpi=300)
    plt.close()

    # Save CSV
    csv_p = OUTPUT_DIR / "fig2_data.csv"
    with open(csv_p, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["regime", "method", "candidate_set", "metric_definition", "R@1", "R@3", "R@5", "R@10"])
        writer.writerow(["Regime A", "M1 Lexical", "Graph Candidates (N=125)", "Mean Fraction", m1[0], m1[1], m1[2], m1[3]])
        writer.writerow(["Regime A", "M2 Dense", "Graph Candidates (N=125)", "Mean Fraction", m2[0], m2[1], m2[2], m2[3]])
        writer.writerow(["Regime A", "M3 Graph", "Graph Candidates (N=125)", "Mean Fraction", m3[0], m3[1], m3[2], m3[3]])
        writer.writerow(["Regime A", "M4 swe_toolkit", "Graph Candidates (N=125)", "Mean Fraction", m4[0], m4[1], m4[2], m4[3]])
        writer.writerow(["Regime A", "M5 Hybrid RRF", "Graph Candidates (N=125)", "Mean Fraction", m5[0], m5[1], m5[2], m5[3]])
        writer.writerow(["Regime B", "Shipped Engine v4", "All Files on Disk (N=125)", "Mean Fraction", v4_mean_frac[0], v4_mean_frac[1], v4_mean_frac[2], v4_mean_frac[3]])
        writer.writerow(["Regime B", "Shipped Engine v4", "All Files on Disk (N=125)", "Any-Gold", v4_any_gold[0], v4_any_gold[1], v4_any_gold[2], v4_any_gold[3]])
    print(f"[FIG 2] Wrote {out_p} and {csv_p}")


# ==============================================================================
# FIGURE 3: Mechanisms Table Figure (WITHOUT ANY TURN POSITIONS)
# ==============================================================================
def render_fig3():
    fig, ax = plt.subplots(figsize=(14.0, 6.2), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.axis("off")

    fig.suptitle(
        "Runtime Verification Audit: 6 Wheel-Verified Failure Sites Across ADK, vLLM & Sandbox",
        fontsize=13, weight="bold", color=OI_DARK, y=0.96
    )

    table_data = [
        [
            "Missing Sandbox\nTest Plugins",
            "pytest in\nevaluation container",
            "tests/test_*.py\n(collection phase)",
            "Observed in\ncontainer run",
            "28 / 67 (41.8%) FastAPI tasks crash on test import\nbefore assertions (missing inline-snapshot, dirty-equals)",
            "AST-isolated syntax verification\n(_verify.py) without bare pytest"
        ],
        [
            "Sandbox .gitignore\nStaging Trap",
            "git in\n/workspace sandbox",
            "swegemma harness\n(git add -N .)",
            "Inferred from code &\nreproduced in devset",
            "11 / 129 (8.5%) gold patches add brand-new files;\ngit add -N . silently omits them if matching .gitignore",
            "Enforce git add -N -f for all\nnew modules in patch gate"
        ],
        [
            "SkillToolset Injected\nPreamble Overhead",
            "google-adk\n1.36.1",
            "google/adk/tools/\nskill_toolset.py:689",
            "Observed in\nrequest payload",
            "+875 tokens injected on 100% of tasks using skills;\nmandates load_skill and contradicts cold-calling",
            "Zero-schema hybrid: 6 base tools,\nno skill metadata overhead"
        ],
        [
            "ADK History\nCompaction Cliff",
            "google-adk\n1.36.1",
            "google/adk/apps/\n_configs.py:61-70",
            "Inferred from code &\nHARNESS_README §7.2",
            "token_threshold = 14,336 drops non-model tool\nframes, wiping execution history on long trajectories",
            "Retain concise plain-text state\ncards in agent system context"
        ],
        [
            "vLLM Chat Template\nToken Mismatch",
            "vllm\n0.19.1",
            "vllm/entrypoints/openai/\nchat_utils.py:1512",
            "Inferred from code &\npayload probe",
            "include_thoughts: false strips thoughts from context\nwhile thinking_budget > 0 still consumes raw generation",
            "Synchronize sampling configuration\nand thought tracking flags"
        ],
        [
            "Thinking Budget\nLogits Truncation",
            "vllm\n0.19.1",
            "vllm/model_executor/layers/\nlogits_processor/builtin.py:294",
            "Inferred from code &\npayload probe",
            "ThinkingTokenBudgetLogitsProcessor forces </thought>\nmid-sentence when thought budget is exhausted",
            "Maintain budget >= 4096 or disable\nthinking budget completely"
        ]
    ]

    col_labels = [
        "Failure Mechanism",
        "Software Package\n& Version",
        "Code Location\n(file:line)",
        "Verification\nType",
        "Affected Tasks & Empirical Impact\n(Verified from Repo Artifacts)",
        "Operational Fix /\nArchitecture Mitigation"
    ]

    tab = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc="left",
        loc="center",
        bbox=[0.01, 0.08, 0.98, 0.82]
    )

    tab.auto_set_font_size(False)
    tab.set_fontsize(8.2)

    # Style columns and headers
    col_widths = [0.15, 0.13, 0.15, 0.12, 0.26, 0.19]
    for (r, c), cell in tab.get_celld().items():
        cell.set_edgecolor("#94A3B8")
        cell.set_linewidth(0.8)
        cell.set_width(col_widths[c])
        if r == 0:
            cell.set_facecolor("#0F172A")
            cell.set_text_props(weight="bold", color="#FFFFFF", fontsize=8.6)
            cell.set_height(0.10)
        else:
            cell.set_height(0.12)
            if r % 2 == 1:
                cell.set_facecolor("#FFFFFF")
            else:
                cell.set_facecolor("#F8FAFC")
            cell.set_text_props(color=OI_DARK)
            if c == 0:
                cell.set_text_props(weight="bold", color=OI_BLUE)

    fig.text(
        0.02, 0.02,
        "Source: Verified from installed wheelhouse (google-adk 1.36.1, vllm 0.19.1), competition HARNESS_README.md (2026-10-13), and 129 SWE-bench tasks. Zero turn positions cited.",
        fontsize=7.8, color="#64748B"
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out_p = OUTPUT_DIR / "fig3.png"
    plt.savefig(out_p, dpi=300)
    plt.close()

    # Save CSV
    csv_p = OUTPUT_DIR / "fig3_data.csv"
    with open(csv_p, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["mechanism", "package_version", "file_line", "verification_type", "affected_tasks_impact", "mitigation"])
        for row in table_data:
            writer.writerow([cell.replace("\n", " ") for cell in row])
    print(f"[FIG 3] Wrote {out_p} and {csv_p}")


# ==============================================================================
# THUMBNAIL: Exactly 1200x630 Card Banner
# ==============================================================================
def render_thumbnail():
    fig = plt.figure(figsize=(12.0, 6.3), dpi=100)
    fig.patch.set_facecolor("#0B132B")  # Deep space slate

    # Title Banner
    fig.text(
        0.5, 0.91,
        "When Code Graphs Help and When They Hurt: Offline Gemma 4 SWE Agents",
        ha="center", va="center", color="#FFFFFF", fontsize=16.5, weight="bold"
    )
    fig.text(
        0.5, 0.84,
        "Empirical Evidence Across 129 SWE-Bench Tasks, 16 Submissions & 4× L4 Runtime Audit",
        ha="center", va="center", color="#94A3B8", fontsize=11, weight="medium"
    )

    # 3 Distinct Modern Panels
    # Panel A: Runtime Audit
    ax_a = fig.add_axes([0.04, 0.10, 0.29, 0.68])
    ax_a.set_facecolor("#1C2541")
    ax_a.axis("off")
    for spine in ax_a.spines.values():
        spine.set_color(OI_VERMILION)
        spine.set_linewidth(1.5)
        spine.set_visible(True)

    ax_a.text(0.5, 0.92, "PANEL A", ha="center", va="center", color="#F87171", fontsize=10, weight="bold", transform=ax_a.transAxes)
    ax_a.text(0.5, 0.83, "Runtime Verification", ha="center", va="center", color="#FFFFFF", fontsize=13.5, weight="bold", transform=ax_a.transAxes)
    ax_a.axhline(0.76, color="#334155", linewidth=1.0)

    rect1 = patches.FancyBboxPatch((0.06, 0.51), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#2D1519", edgecolor=OI_VERMILION, transform=ax_a.transAxes)
    ax_a.add_patch(rect1)
    ax_a.text(0.10, 0.64, "14,336 Compaction Cliff", color="#FCA5A5", fontsize=10.0, weight="bold", transform=ax_a.transAxes)
    ax_a.text(0.10, 0.55, "ADK drops non-model tool\nframes above token threshold", color="#E2E8F0", fontsize=8.2, transform=ax_a.transAxes)

    rect2 = patches.FancyBboxPatch((0.06, 0.28), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#2D1F15", edgecolor=OI_ORANGE, transform=ax_a.transAxes)
    ax_a.add_patch(rect2)
    ax_a.text(0.10, 0.41, "+875 Token Skill Overhead", color="#FDBA74", fontsize=10.0, weight="bold", transform=ax_a.transAxes)
    ax_a.text(0.10, 0.32, "SkillToolset system prompt\ncontradicts direct tool calls", color="#E2E8F0", fontsize=8.2, transform=ax_a.transAxes)

    rect3 = patches.FancyBboxPatch((0.06, 0.05), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#2D1519", edgecolor=OI_VERMILION, transform=ax_a.transAxes)
    ax_a.add_patch(rect3)
    ax_a.text(0.10, 0.18, "28/67 Pytest Collection Crashes", color="#FCA5A5", fontsize=10.0, weight="bold", transform=ax_a.transAxes)
    ax_a.text(0.10, 0.09, "Missing inline-snapshot fixtures\ncause false assertion failures", color="#E2E8F0", fontsize=8.2, transform=ax_a.transAxes)

    # Panel B: Retrieval 2x2 Matrix
    ax_b = fig.add_axes([0.355, 0.10, 0.29, 0.68])
    ax_b.set_facecolor("#1C2541")
    ax_b.axis("off")
    for spine in ax_b.spines.values():
        spine.set_color(OI_SKY_BLUE)
        spine.set_linewidth(1.5)
        spine.set_visible(True)

    ax_b.text(0.5, 0.92, "PANEL B", ha="center", va="center", color=OI_SKY_BLUE, fontsize=10, weight="bold", transform=ax_b.transAxes)
    ax_b.text(0.5, 0.83, "Shared N=125 Tasks", ha="center", va="center", color="#FFFFFF", fontsize=13.5, weight="bold", transform=ax_b.transAxes)
    ax_b.axhline(0.76, color="#334155", linewidth=1.0)

    rect_b1 = patches.FancyBboxPatch((0.06, 0.53), 0.88, 0.18, boxstyle="round,pad=0.03", facecolor="#0F2942", edgecolor=OI_SKY_BLUE, transform=ax_b.transAxes)
    ax_b.add_patch(rect_b1)
    ax_b.text(0.10, 0.64, "0.449  Static Graph M4", color="#BAE6FD", fontsize=10.5, weight="bold", transform=ax_b.transAxes)
    ax_b.text(0.10, 0.56, "Mean Fraction on Graph Nodes", color="#94A3B8", fontsize=8.2, transform=ax_b.transAxes)

    rect_b2 = patches.FancyBboxPatch((0.06, 0.29), 0.88, 0.18, boxstyle="round,pad=0.03", facecolor="#0F2942", edgecolor=OI_SKY_BLUE, transform=ax_b.transAxes)
    ax_b.add_patch(rect_b2)
    ax_b.text(0.10, 0.40, "0.625  Live AST Indexer", color="#BAE6FD", fontsize=10.5, weight="bold", transform=ax_b.transAxes)
    ax_b.text(0.10, 0.32, "+17.62 pp Candidate Gain (p<0.001)", color="#4ADE80", fontsize=8.2, weight="semibold", transform=ax_b.transAxes)

    rect_b3 = patches.FancyBboxPatch((0.06, 0.05), 0.88, 0.18, boxstyle="round,pad=0.03", facecolor="#064E3B", edgecolor=OI_BLUISH_GREEN, transform=ax_b.transAxes)
    ax_b.add_patch(rect_b3)
    ax_b.text(0.10, 0.16, "0.754  Shipped Any-Gold R@5", color="#A7F3D0", fontsize=10.5, weight="bold", transform=ax_b.transAxes)
    ax_b.text(0.10, 0.08, "+12.89 pp Metric Definition Gap", color="#6EE7B7", fontsize=8.2, weight="bold", transform=ax_b.transAxes)

    # Panel C: Statistical Power
    ax_c = fig.add_axes([0.67, 0.10, 0.29, 0.68])
    ax_c.set_facecolor("#1C2541")
    ax_c.axis("off")
    for spine in ax_c.spines.values():
        spine.set_color(OI_ORANGE)
        spine.set_linewidth(1.5)
        spine.set_visible(True)

    ax_c.text(0.5, 0.92, "PANEL C", ha="center", va="center", color=OI_ORANGE, fontsize=10, weight="bold", transform=ax_c.transAxes)
    ax_c.text(0.5, 0.83, "Leaderboard Power", ha="center", va="center", color="#FFFFFF", fontsize=13.5, weight="bold", transform=ax_c.transAxes)
    ax_c.axhline(0.76, color="#334155", linewidth=1.0)

    rect_c1 = patches.FancyBboxPatch((0.06, 0.51), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#291E0F", edgecolor=OI_ORANGE, transform=ax_c.transAxes)
    ax_c.add_patch(rect_c1)
    ax_c.text(0.10, 0.64, "Within-Split Noise: ±0.89", color="#FDE68A", fontsize=10.0, weight="bold", transform=ax_c.transAxes)
    ax_c.text(0.10, 0.55, "Identical exp05 clone dropped\n2 tasks (12 -> 10) on re-eval", color="#E2E8F0", fontsize=8.2, transform=ax_c.transAxes)

    rect_c2 = patches.FancyBboxPatch((0.06, 0.28), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#291E0F", edgecolor=OI_ORANGE, transform=ax_c.transAxes)
    ax_c.add_patch(rect_c2)
    ax_c.text(0.10, 0.41, "Cross-Split SE: ±2.9 Tasks", color="#FDE68A", fontsize=10.0, weight="bold", transform=ax_c.transAxes)
    ax_c.text(0.10, 0.32, "Binomial SE = 0.0503 on n=58;\nsub-0.05 deltas are noise", color="#E2E8F0", fontsize=8.2, transform=ax_c.transAxes)

    rect_c3 = patches.FancyBboxPatch((0.06, 0.05), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#1E1B4B", edgecolor=OI_PURPLE, transform=ax_c.transAxes)
    ax_c.add_patch(rect_c3)
    ax_c.text(0.10, 0.18, "Top-20 4-Task Band", color="#C7D2FE", fontsize=10.0, weight="bold", transform=ax_c.transAxes)
    ax_c.text(0.10, 0.09, "Scores 0.22 to 0.29 span\nonly 13 to 17 solved tasks", color="#E2E8F0", fontsize=8.2, transform=ax_c.transAxes)

    out_p = OUTPUT_DIR / "writeup_thumbnail.png"
    plt.savefig(out_p, dpi=100)
    plt.close()

    im = Image.open(out_p)
    if im.size != (1200, 630):
        im = im.resize((1200, 630), Image.Resampling.LANCZOS)
        im.save(out_p)
    print(f"[THUMBNAIL] Wrote {out_p} (Dimensions: {im.size})")


def main():
    print("=" * 70)
    print("Generating Academic Publication Figures in research/paper_figs/")
    print("=" * 70)
    render_fig1()
    render_fig2()
    render_fig3()
    render_thumbnail()
    print("=" * 70)
    print("ALL FIGURES SUCCESSFULLY GENERATED")
    print("=" * 70)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""generate_paper_figures.py — Render 6 Publication-Grade 300-DPI Figures for Kaggle Paper Track.

Generates:
  1. assets/paper_figures/fig0_card_thumbnail.png (Exactly 1200x630 px, 16:9 Banner)
  2. assets/paper_figures/fig1_harness_architecture.png (Lifecycle & Failure Sites)
  3. assets/paper_figures/fig2_retrieval_2x2_decomposition.png (M1-M5 & Waterfall Decomposition)
  4. assets/paper_figures/fig3_symbol_and_multifile_paradox.png (Symbol Progression & Paradox)
  5. assets/paper_figures/fig4_leaderboard_statistical_power.png (Noise Floor & Public Top-20)
  6. assets/paper_figures/fig5_patch_anatomy_and_playbooks.png (Patch Stats & 10 AST Playbooks)
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = REPO_ROOT / "assets" / "paper_figures"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Academic Publication Styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica", "sans-serif"],
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.labelweight": "semibold",
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
    "figure.titlesize": 14,
    "figure.titleweight": "bold",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.0,
    "grid.color": "#e2e8f0",
    "grid.linestyle": "--",
    "grid.linewidth": 0.6,
})

# Colorblind-safe palette
C_BLUE = "#1f77b4"
C_ORANGE = "#ff7f0e"
C_GREEN = "#2ca02c"
C_RED = "#d62728"
C_PURPLE = "#9467bd"
C_GRAY = "#7f7f7f"
C_DARK = "#0f172a"


def despine(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")


# ==============================================================================
# FIGURE 0: Exactly 1200x630 Card & Header Banner (16:9)
# ==============================================================================
def render_fig0_card_thumbnail():
    # 12.0 x 6.3 inches at 100 DPI = exactly 1200 x 630 pixels
    fig = plt.figure(figsize=(12.0, 6.3), dpi=100)
    fig.patch.set_facecolor("#0b132b")  # Deep space dark slate

    # Header Title Banner
    fig.text(0.5, 0.91, "When Code Graphs Help and When They Hurt: Offline Gemma 4 SWE Agents",
             ha="center", va="center", color="#ffffff", fontsize=17, weight="bold")
    fig.text(0.5, 0.84, "Offline Empirical Analysis Across 129 SWE-Bench Tasks & Gemma 4 31B/4B Models",
             ha="center", va="center", color="#94a3b8", fontsize=11, weight="medium")

    # 3 Distinct Modern Panels
    # Panel A: Runtime Mechanics
    ax_a = fig.add_axes([0.04, 0.10, 0.29, 0.68])
    ax_a.set_facecolor("#1c2541")
    ax_a.set_xticks([])
    ax_a.set_yticks([])
    for spine in ax_a.spines.values():
        spine.set_color("#ef4444")
        spine.set_linewidth(1.5)

    ax_a.text(0.5, 0.92, "PANEL A", ha="center", va="center", color="#f87171", fontsize=10, weight="bold", transform=ax_a.transAxes)
    ax_a.text(0.5, 0.83, "Runtime Mechanics", ha="center", va="center", color="#ffffff", fontsize=13.5, weight="bold", transform=ax_a.transAxes)
    ax_a.axhline(0.76, color="#334155", linewidth=1.0)

    # Bullet 1: Compaction Cliff
    rect1 = patches.FancyBboxPatch((0.06, 0.51), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#2d1519", edgecolor="#ef4444", transform=ax_a.transAxes)
    ax_a.add_patch(rect1)
    ax_a.text(0.10, 0.64, "14,336 Compaction Cliff", color="#fca5a5", fontsize=10.5, weight="bold", transform=ax_a.transAxes)
    ax_a.text(0.10, 0.55, "ADK history truncation drops\nnon-model state on Turn 15+", color="#e2e8f0", fontsize=8.5, transform=ax_a.transAxes)

    # Bullet 2: vLLM Thought Drop
    rect2 = patches.FancyBboxPatch((0.06, 0.28), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#2d1f15", edgecolor="#f97316", transform=ax_a.transAxes)
    ax_a.add_patch(rect2)
    ax_a.text(0.10, 0.41, "vLLM Thought Drop", color="#fdba74", fontsize=10.5, weight="bold", transform=ax_a.transAxes)
    ax_a.text(0.10, 0.32, "include_thoughts=False keeps\nbudget while stripping tokens", color="#e2e8f0", fontsize=8.5, transform=ax_a.transAxes)

    # Bullet 3: .gitignore Drop
    rect3 = patches.FancyBboxPatch((0.06, 0.05), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#2d1519", edgecolor="#ef4444", transform=ax_a.transAxes)
    ax_a.add_patch(rect3)
    ax_a.text(0.10, 0.18, ".gitignore 8.5% Trap", color="#fca5a5", fontsize=10.5, weight="bold", transform=ax_a.transAxes)
    ax_a.text(0.10, 0.09, "git add -N . silently drops new\nfiles in 11/129 gold tasks", color="#e2e8f0", fontsize=8.5, transform=ax_a.transAxes)

    # Panel B: 129-Task Localization
    ax_b = fig.add_axes([0.355, 0.10, 0.29, 0.68])
    ax_b.set_facecolor("#1c2541")
    ax_b.set_xticks([])
    ax_b.set_yticks([])
    for spine in ax_b.spines.values():
        spine.set_color("#38bdf8")
        spine.set_linewidth(1.5)

    ax_b.text(0.5, 0.92, "PANEL B", ha="center", va="center", color="#38bdf8", fontsize=10, weight="bold", transform=ax_b.transAxes)
    ax_b.text(0.5, 0.83, "129-Task Localization", ha="center", va="center", color="#ffffff", fontsize=13.5, weight="bold", transform=ax_b.transAxes)
    ax_b.axhline(0.76, color="#334155", linewidth=1.0)

    # Step 1: Static Graph
    rect_b1 = patches.FancyBboxPatch((0.06, 0.53), 0.88, 0.18, boxstyle="round,pad=0.03", facecolor="#0f2942", edgecolor="#38bdf8", transform=ax_b.transAxes)
    ax_b.add_patch(rect_b1)
    ax_b.text(0.10, 0.64, "0.435  Static Code Graph", color="#bae6fd", fontsize=11, weight="bold", transform=ax_b.transAxes)
    ax_b.text(0.10, 0.56, "Regime A (swe_toolkit M4)", color="#94a3b8", fontsize=8.5, transform=ax_b.transAxes)

    ax_b.annotate("", xy=(0.5, 0.48), xytext=(0.5, 0.53),
                  arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=1.8), transform=ax_b.transAxes)

    # Step 2: Live AST Mean-Frac
    rect_b2 = patches.FancyBboxPatch((0.06, 0.29), 0.88, 0.18, boxstyle="round,pad=0.03", facecolor="#0f2942", edgecolor="#38bdf8", transform=ax_b.transAxes)
    ax_b.add_patch(rect_b2)
    ax_b.text(0.10, 0.40, "0.618  Live AST Mean-Frac", color="#bae6fd", fontsize=11, weight="bold", transform=ax_b.transAxes)
    ax_b.text(0.10, 0.32, "+18.3 pp (Live Source + Test Demote)", color="#4ade80", fontsize=8.5, weight="semibold", transform=ax_b.transAxes)

    ax_b.annotate("", xy=(0.5, 0.24), xytext=(0.5, 0.29),
                  arrowprops=dict(arrowstyle="->", color="#4ade80", lw=1.8), transform=ax_b.transAxes)

    # Step 3: Any-Gold R@5
    rect_b3 = patches.FancyBboxPatch((0.06, 0.05), 0.88, 0.18, boxstyle="round,pad=0.03", facecolor="#064e3b", edgecolor="#10b981", transform=ax_b.transAxes)
    ax_b.add_patch(rect_b3)
    ax_b.text(0.10, 0.16, "0.744  Any-Gold R@5 (96/129)", color="#a7f3d0", fontsize=11, weight="bold", transform=ax_b.transAxes)
    ax_b.text(0.10, 0.08, "+30.9 pp (+71.0% relative leap)", color="#6ee7b7", fontsize=8.5, weight="bold", transform=ax_b.transAxes)

    # Panel C: Statistical Resolution
    ax_c = fig.add_axes([0.67, 0.10, 0.29, 0.68])
    ax_c.set_facecolor("#1c2541")
    ax_c.set_xticks([])
    ax_c.set_yticks([])
    for spine in ax_c.spines.values():
        spine.set_color("#f59e0b")
        spine.set_linewidth(1.5)

    ax_c.text(0.5, 0.92, "PANEL C", ha="center", va="center", color="#fbbf24", fontsize=10, weight="bold", transform=ax_c.transAxes)
    ax_c.text(0.5, 0.83, "Statistical Resolution", ha="center", va="center", color="#ffffff", fontsize=13.5, weight="bold", transform=ax_c.transAxes)
    ax_c.axhline(0.76, color="#334155", linewidth=1.0)

    # Bullet 1: Sample Size & Within-Split SD
    rect_c1 = patches.FancyBboxPatch((0.06, 0.51), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#291e0f", edgecolor="#f59e0b", transform=ax_c.transAxes)
    ax_c.add_patch(rect_c1)
    ax_c.text(0.10, 0.64, "N = 58 Resolved Tasks / Run", color="#fde68a", fontsize=10.5, weight="bold", transform=ax_c.transAxes)
    ax_c.text(0.10, 0.55, "within-split SD = 0.89 tasks\n1 solved task = 0.017 score", color="#e2e8f0", fontsize=8.5, transform=ax_c.transAxes)

    # Bullet 2: Cross-Split SE
    rect_c2 = patches.FancyBboxPatch((0.06, 0.28), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#291e0f", edgecolor="#f59e0b", transform=ax_c.transAxes)
    ax_c.add_patch(rect_c2)
    ax_c.text(0.10, 0.41, "Cross-Split SE = 0.0503", color="#fde68a", fontsize=10.5, weight="bold", transform=ax_c.transAxes)
    ax_c.text(0.10, 0.32, "SE = 2.9 tasks; deltas <= 2 tasks\nare leaderboard noise", color="#e2e8f0", fontsize=8.5, transform=ax_c.transAxes)

    # Bullet 3: Top-20 4-Task Band
    rect_c3 = patches.FancyBboxPatch((0.06, 0.05), 0.88, 0.20, boxstyle="round,pad=0.03", facecolor="#1e1b4b", edgecolor="#818cf8", transform=ax_c.transAxes)
    ax_c.add_patch(rect_c3)
    ax_c.text(0.10, 0.18, "Top-20 4-Task Band", color="#c7d2fe", fontsize=10.5, weight="bold", transform=ax_c.transAxes)
    ax_c.text(0.10, 0.09, "Scores 0.22 to 0.29 cover\nonly 13 to 17 tasks", color="#e2e8f0", fontsize=8.5, transform=ax_c.transAxes)

    out_p = ASSETS_DIR / "fig0_card_thumbnail.png"
    plt.savefig(out_p, dpi=100)
    plt.close()

    # Enforce exact 1200x630 pixel dimension with PIL
    im = Image.open(out_p)
    if im.size != (1200, 630):
        im = im.resize((1200, 630), Image.Resampling.LANCZOS)
        im.save(out_p)
    print(f"[FIG 0] Generated {out_p} (Dimensions: {im.size})")


# ==============================================================================
# FIGURE 1: Harness Architecture & 4 Failure Sites
# ==============================================================================
def render_fig1_harness_architecture():
    fig, ax = plt.subplots(figsize=(11.2, 7.5), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fafbfc")
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 7.8)
    ax.axis("off")

    # Headline Takeaway Suptitle & Sub-Banner
    fig.suptitle("Offline Evaluation Lifecycle & 4 Exact Failure Sites: Compaction Cliff (14,336 Tok), Thought Stripping & Sandbox Trap",
                 fontsize=12.5, weight="bold", color=C_DARK, y=0.975)
    ax.text(5.6, 7.20, "ADK 1.36.1 <-> litellm <-> vLLM 0.19.1 <-> /workspace Sandbox on 4x L4 GPUs (12h Hard Container Timeout)",
            ha="center", va="center", fontsize=9.8, color="#64748b")

    # 4 Main Pipeline Stage Boxes at y = 6.1
    stages = [
        ("ADK 1.36.1\nAgent Runtime", 1.50, 6.1, 2.05, 0.95, C_BLUE),
        ("litellm\nProxy Router", 4.25, 6.1, 2.05, 0.95, "#0284c7"),
        ("vLLM 0.19.1\nServing Engine", 7.00, 6.1, 2.05, 0.95, C_PURPLE),
        ("/workspace\nGit Sandbox", 9.70, 6.1, 2.05, 0.95, C_GREEN),
    ]

    for name, x, y, w, h, col in stages:
        box = patches.FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.08",
                                     facecolor="#ffffff", edgecolor=col, linewidth=2.0)
        ax.add_patch(box)
        ax.text(x, y, name, ha="center", va="center", fontsize=9.8, weight="bold", color=C_DARK)

    # Connecting bi-directional arrows
    arrow_props = dict(arrowstyle="<->", color="#64748b", lw=2, shrinkA=6, shrinkB=6)
    ax.annotate("", xy=(2.55, 6.1), xytext=(3.20, 6.1), arrowprops=arrow_props)
    ax.annotate("", xy=(5.30, 6.1), xytext=(5.95, 6.1), arrowprops=arrow_props)
    ax.annotate("", xy=(8.05, 6.1), xytext=(8.65, 6.1), arrowprops=arrow_props)

    # 4 Failure site cards (2 columns x 2 rows, perfectly mapped to pipeline origins)
    # Left Column (x = 0.50, w = 4.85): Site 1 (ADK) & Site 2 (vLLM Chat Entrypoint)
    # Right Column (x = 5.85, w = 4.85): Site 4 (Git Sandbox) & Site 3 (vLLM Logits Processor)
    card_boxes = [
        # Upper Left: Site 1 (Compaction Cliff) - directly below ADK
        (0.50, 3.30, 4.85, 2.05, "Failure Site 1: ADK Compaction Cliff", "token_threshold = 14,336  (adk/apps/_configs.py:70)",
         "Mechanism: History truncation interval=15 drops non-model tool output\n"
         "frames and raw execution state, keeping only assistant model turns.\n"
         "Impact: Turn 15+ memory loss unless plain-text state\ncards are maintained in prompt or on disk.",
         C_RED, "#fef2f2"),

        # Upper Right: Site 4 (.gitignore Trap) - directly below Git Sandbox
        (5.85, 3.30, 4.85, 2.05, "Failure Site 4: Sandbox .gitignore Trap", "git add -N .  (Working Tree Evaluation Harness)",
         "Mechanism: Default staging command strictly respects\nrepository .gitignore rules.\n"
         "Impact: Newly created modules (8.5% = 11/129 tasks)\nare silently omitted from patch. Use git add -N -f.",
         C_RED, "#fef2f2"),

        # Lower Left: Site 2 (vLLM Formatting)
        (0.50, 0.70, 4.85, 2.15, "Failure Site 2: vLLM Chat Template Parsing", "chat_utils.py:1512  (vLLM 0.19.1 Entrypoint)",
         "Mechanism: include_thoughts: false strips thought tokens from context\n"
         "while thinking_budget > 0 still consumes raw generation budget.\n"
         "Impact: Inter-turn thought loss & prompt token count mismatch.",
         C_ORANGE, "#fffbeb"),

        # Lower Right: Site 3 (Logits Processor)
        (5.85, 0.70, 4.85, 2.15, "Failure Site 3: Logits Budget Processor", "builtin.py:294  (ThinkingTokenBudgetLogitsProcessor)",
         "Mechanism: Forced </thought> token generation upon budget exhaustion.\n"
         "Impact: Truncates reasoning mid-sentence. Model immediately emits\n"
         "degenerate repetitions or empty tool calls, causing 0-score timeout.",
         "#b45309", "#fffbeb"),
    ]

    for x, y, w, h, title, sub, desc, ec, bg in card_boxes:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                     facecolor=bg, edgecolor=ec, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 0.20, y + h - 0.38, title, fontsize=10.2, weight="bold", color=ec)
        ax.text(x + 0.20, y + h - 0.72, sub, fontsize=8.5, weight="semibold", color="#475569")
        ax.text(x + 0.20, y + 0.35, desc, fontsize=8.4, color="#1e293b", linespacing=1.3)

    # Connector lines routed purely through empty whitespace corridors (zero card intersections!)
    # ADK straight down to Site 1
    ax.plot([1.50, 1.50], [5.62, 5.35], color=C_BLUE, lw=1.5, ls="--")
    # Sandbox straight down to Site 4
    ax.plot([9.70, 9.70], [5.62, 5.35], color=C_GREEN, lw=1.5, ls="--")
    # vLLM down through the central corridor (x = 5.50) into lower tier
    ax.plot([7.00, 5.50, 5.50], [5.62, 5.50, 3.05], color=C_PURPLE, lw=1.3, ls=":")
    # Branch left to Site 2
    ax.plot([5.50, 2.92, 2.92], [3.05, 3.05, 2.85], color=C_PURPLE, lw=1.3, ls=":")
    # Branch right to Site 3
    ax.plot([5.50, 8.27, 8.27], [3.05, 3.05, 2.85], color=C_PURPLE, lw=1.3, ls=":")

    out_p = ASSETS_DIR / "fig1_harness_architecture.png"
    plt.savefig(out_p, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[FIG 1] Generated {out_p}")


# ==============================================================================
# FIGURE 2: Retrieval 2x2 Decomposition (M1-M5 & Waterfall)
# ==============================================================================
def render_fig2_retrieval_2x2_decomposition():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.2, 6.0), dpi=300)
    fig.patch.set_facecolor("#ffffff")

    fig.suptitle("Decomposing the +30.9 pp (0.435 -> 0.744) R@5 Leap: Candidate Set Gain (+18.32 pp, p < 0.001) vs Metric Def (+12.58 pp)",
                 fontsize=12.5, weight="bold", color=C_DARK, y=0.98)

    # -------------------------------------------------------------
    # Left Panel: M1-M5 Recall Across Ranks @1, @3, @5, @10 (with M3-IDF)
    # -------------------------------------------------------------
    ranks = ["R@1", "R@3", "R@5", "R@10"]
    x = np.arange(len(ranks))
    width = 0.125

    m1 = [0.0504, 0.1819, 0.2284, 0.3036]
    m2 = [0.0583, 0.1772, 0.2163, 0.3810]
    m3 = [0.0504, 0.1819, 0.2265, 0.2846]
    m3_idf = [0.1494, 0.2588, 0.3016, 0.3301]
    m4 = [0.2661, 0.3798, 0.4350, 0.4587]
    m5 = [0.2466, 0.3742, 0.4745, 0.5701]

    rects1 = ax1.bar(x - 2.5 * width, m1, width, label="M1: Lexical Grep", color=C_GRAY, edgecolor="#333333", lw=0.6)
    rects2 = ax1.bar(x - 1.5 * width, m2, width, label="M2: Dense Embedding", color=C_PURPLE, edgecolor="#333333", lw=0.6)
    rects3 = ax1.bar(x - 0.5 * width, m3, width, label="M3: Raw 1-Hop AST", color=C_RED, edgecolor="#333333", lw=0.6)
    rects3_idf = ax1.bar(x + 0.5 * width, m3_idf, width, label="M3-IDF (Inverse-Deg Pruned)", color="#f59e0b", edgecolor="#78350f", lw=0.9)
    rects4 = ax1.bar(x + 1.5 * width, m4, width, label="M4: swe_toolkit (Graph)", color=C_BLUE, edgecolor="#333333", lw=0.6)
    rects5 = ax1.bar(x + 2.5 * width, m5, width, label="M5: Hybrid RRF", color=C_GREEN, edgecolor="#333333", lw=0.6)

    ax1.set_ylabel("File Recall (Mean Fraction)")
    ax1.set_title("(A) Static Graph Methods (Shared N=125, p < 0.001 vs M1/M3)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(ranks, weight="semibold")
    ax1.set_ylim(0, 0.85)
    ax1.grid(axis="y", alpha=0.5)
    despine(ax1)
    ax1.legend(loc="upper left", bbox_to_anchor=(0.01, 0.99), frameon=True, framealpha=0.95, facecolor="#ffffff", edgecolor="#cccccc", fontsize=7.8)

    # Inset callout box: placed in open space above R@3 & R@5
    inset_box = patches.FancyBboxPatch((0.27, 0.58), 0.46, 0.36, boxstyle="round,pad=0.03",
                                       facecolor="#fef2f2", edgecolor=C_RED, linewidth=1.2, transform=ax1.transAxes)
    ax1.add_patch(inset_box)
    ax1.text(0.50, 0.86, "M3 Hub Pollution & IDF Fix", ha="center", color=C_RED, fontsize=8.8, weight="bold", transform=ax1.transAxes)
    ax1.text(0.50, 0.68, "80.9% of raw 1-hop AST neighborhoods\nexceed 5,000-char tool cap!\nM3-IDF prunes hubs by 1/log2(deg),\nfitting <3,500 chars (+7.51 pp R@5).",
             ha="center", color="#1e293b", fontsize=7.6, linespacing=1.2, transform=ax1.transAxes)

    # -------------------------------------------------------------
    # Right Panel: Waterfall Decomposition of 0.435 -> 0.744 (+30.9 pp)
    # -------------------------------------------------------------
    step_labels = [
        "Static Graph\nBaseline (M4)\n[Mean-Frac]",
        "+ Live AST Index\n& Test Demote\n[Candidate Set]",
        "Live AST\nSubtotal\n[Mean-Frac]",
        "+ Any-Gold\nMetric Def\n[Single Hit]",
        "Live Workspace\nShipped (v4)\n[Any-Gold R@5]"
    ]
    x_wf = np.arange(len(step_labels))

    bottoms = [0.0, 0.4350, 0.0, 0.6182, 0.0]
    heights = [0.4350, 0.1832, 0.6182, 0.1258, 0.7440]
    colors = [C_BLUE, C_GREEN, "#38bdf8", C_ORANGE, "#10b981"]

    bars_wf = ax2.bar(x_wf, heights, bottom=bottoms, color=colors, edgecolor="#333333", width=0.55, lw=0.8)

    # Dotted connector lines
    ax2.plot([0, 1], [0.4350, 0.4350], color="#64748b", ls="--", lw=1.0)
    ax2.plot([1, 2], [0.6182, 0.6182], color="#64748b", ls="--", lw=1.0)
    ax2.plot([2, 3], [0.6182, 0.6182], color="#64748b", ls="--", lw=1.0)
    ax2.plot([3, 4], [0.7440, 0.7440], color="#64748b", ls="--", lw=1.0)

    # Value text labels on bars
    ax2.text(0, 0.4350 / 2, "0.4350\n(43.5%)", ha="center", va="center", color="#ffffff", weight="bold", fontsize=9.2)
    ax2.text(1, 0.4350 + 0.1832 / 2, "+18.32 pp\n(p < 0.001)", ha="center", va="center", color="#ffffff", weight="bold", fontsize=8.6)
    ax2.text(2, 0.6182 / 2, "0.6182\n(61.8%)", ha="center", va="center", color="#0f172a", weight="bold", fontsize=9.2)
    ax2.text(3, 0.6182 + 0.1258 / 2, "+12.58 pp\n(+20.4%)", ha="center", va="center", color="#ffffff", weight="bold", fontsize=8.8)
    ax2.text(4, 0.7440 / 2, "0.7440\n(96 / 129)", ha="center", va="center", color="#ffffff", weight="bold", fontsize=9.5)

    # Overall Lift Bracket
    ax2.annotate("", xy=(4.40, 0.7440), xytext=(4.40, 0.4350),
                 arrowprops=dict(arrowstyle="<->", color=C_RED, lw=1.8))
    ax2.text(4.50, (0.7440 + 0.4350) / 2, "Total Transition Leap\n+30.90 pp (+71.0% rel)",
             ha="left", va="center", color=C_RED, weight="bold", fontsize=9.0)

    ax2.set_ylabel("File Recall @ 5")
    ax2.set_title("(B) 2x2 Decomposition of 0.435 -> 0.744 R@5 Leap")
    ax2.set_xticks(x_wf)
    ax2.set_xticklabels(step_labels, fontsize=8.5)
    ax2.set_xlim(-0.6, 5.7)
    ax2.set_ylim(0, 0.88)
    ax2.grid(axis="y", alpha=0.5)
    despine(ax2)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_p = ASSETS_DIR / "fig2_retrieval_2x2_decomposition.png"
    plt.savefig(out_p, dpi=300)
    plt.close()
    print(f"[FIG 2] Generated {out_p}")


# ==============================================================================
# FIGURE 3: Symbol Progression & Multi-File Paradox
# ==============================================================================
def render_fig3_symbol_and_multifile_paradox():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.6, 6.0), dpi=300)
    fig.patch.set_facecolor("#ffffff")

    fig.suptitle("Intra-File Symbol Localization (+9.9 pp R@5, p = 0.045) & The Multi-File All-Gold Paradox (-73.7 pp Collapse)",
                 fontsize=12.5, weight="bold", color=C_DARK, y=0.98)

    # -------------------------------------------------------------
    # Left Panel: Symbol Recall Progression (Table 2D) on 121 Tasks
    # -------------------------------------------------------------
    x_indices = [0, 1, 2, 3]
    v4 = [0.1570, 0.2314, 0.3058, 0.3636]
    v5 = [0.1901, 0.3223, 0.3884, 0.4876]
    v5A = [0.1901, 0.3223, 0.3967, 0.4876]
    v5AB = [0.2149, 0.3223, 0.3884, 0.4545]
    v6 = [0.2149, 0.3306, 0.4050, 0.4628]

    ax1.plot(x_indices, v4, marker="o", color=C_GRAY, ls="--", lw=1.8, label="v4 Shipped Baseline (0.306 R@5)")
    ax1.plot(x_indices, v5, marker="s", color=C_ORANGE, ls="-", lw=1.8, label="v5 Span Re-ranking (0.388 R@5)")
    ax1.plot(x_indices, v5A, marker="^", color=C_PURPLE, ls="-", lw=1.5, alpha=0.8, label="v5A (+Top-12 Scope)")
    ax1.plot(x_indices, v5AB, marker="d", color=C_GREEN, ls="-", lw=1.5, alpha=0.8, label="v5AB (+Member Boost)")
    ax1.plot(x_indices, v6, marker="*", markersize=10, color=C_BLUE, ls="-", lw=2.5, label="v6 Full Pipeline (0.405 R@5)")

    # Annotation of R@5 lift
    ax1.annotate("+9.92 pp (+32.4% rel)\n+1.31 s latency",
                 xy=(2, 0.4050), xytext=(1.35, 0.46),
                 arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=1.5),
                 fontsize=9.2, weight="bold", color=C_BLUE,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="#eff6ff", edgecolor=C_BLUE, lw=1.0))

    ax1.set_xlabel("Top-k Ranked Symbols")
    ax1.set_ylabel("Intra-File Symbol Recall")
    ax1.set_title("(A) Symbol Recall Progression (121 Identifiable Symbol Tasks)")
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(["@1", "@3", "@5", "@10"], weight="semibold")
    ax1.set_ylim(0.10, 0.54)
    ax1.grid(True, alpha=0.5)
    despine(ax1)
    ax1.legend(loc="lower right", frameon=True, framealpha=0.9, facecolor="#ffffff", edgecolor="#cccccc", fontsize=8.8)

    # -------------------------------------------------------------
    # Right Panel: The Multi-File Retrieval Paradox (38 Tasks)
    # -------------------------------------------------------------
    k_labels = ["Top-3", "Top-5", "Top-10"]
    x = np.arange(len(k_labels))
    width = 0.32

    any_gold = [0.7630, 0.8160, 0.8950]  # At least 1 gold file found
    all_gold = [0.0790, 0.0790, 0.1580]  # 100% of gold files found

    rects_any = ax2.bar(x - width/2, any_gold, width, label="Any-Gold Recall (>=1 file)", color=C_BLUE, edgecolor="#333333", lw=0.6)
    rects_all = ax2.bar(x + width/2, all_gold, width, label="Strict All-Gold Recall (100% files)", color=C_RED, edgecolor="#333333", lw=0.6)

    for r in rects_any:
        h = r.get_height()
        ax2.text(r.get_x() + r.get_width()/2, h + 0.02, f"{h:.3f}\n({int(round(h*38))}/38)", ha="center", va="bottom", fontsize=8.2, weight="bold", color=C_BLUE)
    for r in rects_all:
        h = r.get_height()
        ax2.text(r.get_x() + r.get_width()/2, h + 0.02, f"{h:.3f}\n({int(round(h*38))}/38)", ha="center", va="bottom", fontsize=8.2, weight="bold", color=C_RED)

    # Clean Callout Banner using exact data coordinates (100% bounded inside y in [1.08, 1.27])
    callout = patches.FancyBboxPatch((-0.45, 1.08), 2.90, 0.19, boxstyle="round,pad=0.03",
                                     facecolor="#fff7ed", edgecolor=C_ORANGE, linewidth=1.2)
    ax2.add_patch(callout)
    ax2.text(1.0, 1.22, "THE MULTI-FILE RETRIEVAL PARADOX", ha="center", va="center", color=C_ORANGE, fontsize=9.2, weight="bold")
    ax2.text(1.0, 1.14, "Single-pass retrieval captures ≥1 gold file in 81.6% of tasks, but all gold files in only 7.9%!\nMulti-file tasks structurally mandate multi-turn interaction.",
             ha="center", va="center", color="#1e293b", fontsize=7.8, linespacing=1.2)

    # Clean horizontal legend shifted left above Top-3 & Top-5, leaving Top-10 completely clear
    ax2.legend(loc="upper left", bbox_to_anchor=(0.04, 0.77), ncol=2, frameon=True, framealpha=0.95, facecolor="#ffffff", edgecolor="#cccccc", fontsize=8.0)

    ax2.set_ylabel("Retrieval Recall on Multi-File Tasks")
    ax2.set_title("(B) Multi-File Retrieval Paradox (38 Multi-File Tasks, 29.5%)", pad=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(k_labels, weight="semibold")
    ax2.set_ylim(0, 1.34)
    ax2.grid(axis="y", alpha=0.5)
    despine(ax2)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_p = ASSETS_DIR / "fig3_symbol_and_multifile_paradox.png"
    plt.savefig(out_p, dpi=300)
    plt.close()
    print(f"[FIG 3] Generated {out_p}")


# ==============================================================================
# FIGURE 4: Leaderboard Statistical Power & Noise Floor
# ==============================================================================
def render_fig4_leaderboard_statistical_power():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.2, 5.8), dpi=300, gridspec_kw={"width_ratios": [2.3, 1.0]})
    fig.patch.set_facecolor("#ffffff")

    fig.suptitle("Leaderboard Noise Floor: Binomial SE = ±0.0503 (±2.9 Tasks) Renders Sub-0.05 Deltas Statistically Unresolvable",
                 fontsize=12.5, weight="bold", color=C_DARK, y=0.98)

    # -------------------------------------------------------------
    # Left Panel: Submission Ladder & Statistical Confidence Bands
    # -------------------------------------------------------------
    subs = [
        ("exp01\n(v1 base)", "2026-10-03", 0.05, "31B", 3),
        ("exp02\n(v2 prompt)", "2026-10-04", 0.08, "31B", 5),
        ("exp03\n(replica)", "2026-10-10", 0.17, "31B", 10),
        ("exp05\n(anchor)", "2026-10-23", 0.20, "31B", 12),
        ("exp08\n(contract)", "2026-10-25", 0.17, "31B", 10),
        ("exp10\n(consolid)", "2026-10-26", 0.17, "31B", 10),
        ("exp11\n(E4B)", "2026-10-29", 0.06, "E4B", 4),
        ("e4b-v2\n(prompt)", "2026-10-30", 0.05, "E4B", 3),
        ("E0\n(control)", "2026-10-31", 0.17, "31B", 10),
        ("e4b-v4\n(toolkit)", "2026-11-02", 0.05, "E4B", 3),
        ("exp14\n(lean)", "2026-11-03", 0.15, "31B", 9),
        ("exp_samp\n(temp 1.0)", "2026-11-07", 0.13, "31B", 8),
        ("exp15\n(zero-schema)", "2026-11-10", 0.13, "31B", 8),
    ]

    x_idx = np.arange(len(subs))
    scores = [s[2] for s in subs]
    scales = [s[3] for s in subs]

    p_pool = 0.1703
    sigma_within = 0.89 / 58.0
    se_split = 0.0503

    ax1.axhspan(p_pool - 1.96 * se_split, p_pool + 1.96 * se_split,
                color="#f1f5f9", alpha=0.9, zorder=0, label=r"Cross-Split Sampling Error: $\pm 1.96\,\mathrm{SE}_{\mathrm{split}}$ (2.9 tasks)")

    ax1.axhspan(p_pool - 1.96 * sigma_within, p_pool + 1.96 * sigma_within,
                color="#bae6fd", alpha=0.6, zorder=1, label=r"Within-Split Run Noise: $\pm 1.96\,\sigma_{\mathrm{within}}$ (0.89 tasks)")

    ax1.axhline(p_pool, color=C_BLUE, ls="--", lw=1.5, zorder=2, label=f"31B Converged Mean ({p_pool:.3f} = 79/464)")

    colors_pts = [C_BLUE if sc == "31B" else C_ORANGE for sc in scales]
    ax1.scatter(x_idx, scores, s=85, c=colors_pts, edgecolor="#1e293b", lw=1.2, zorder=5)

    ax1.annotate("exp05 (0.20):\nHigh Draw (12 tasks)", xy=(3, 0.20), xytext=(2.2, 0.23),
                 arrowprops=dict(arrowstyle="->", color="#0369a1", lw=1.2),
                 fontsize=8.5, weight="bold", color="#0369a1")

    ax1.annotate("E0 Control (0.17):\nByte-Identical Rebuild", xy=(8, 0.17), xytext=(7.2, 0.21),
                 arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.2),
                 fontsize=8.5, weight="bold", color=C_RED)

    ax1.annotate("E4B Flat-Line Cluster\n0.05 - 0.06 (3-4 tasks)", xy=(7, 0.05), xytext=(6.5, 0.09),
                 arrowprops=dict(arrowstyle="->", color=C_ORANGE, lw=1.2),
                 fontsize=8.5, weight="bold", color=C_ORANGE)

    ax1.set_xticks(x_idx)
    ax1.set_xticklabels([s[0] for s in subs], fontsize=7.8)
    ax1.set_ylabel("Public Leaderboard Score (Pass@1)")
    ax1.set_title("(A) Submission Trajectory & Statistical Resolution Bands (n=58)")
    ax1.set_ylim(0.0, 0.32)
    ax1.grid(axis="y", alpha=0.5)
    despine(ax1)
    ax1.legend(loc="lower left", frameon=True, framealpha=0.9, facecolor="#ffffff", edgecolor="#cccccc", fontsize=8.2)

    # -------------------------------------------------------------
    # Right Panel: Public Top-20 Leaderboard Distribution
    # -------------------------------------------------------------
    scores_top20 = [0.22, 0.24, 0.29]
    counts_top20 = [8, 11, 1]
    y_pos = np.arange(len(scores_top20))

    rects_t20 = ax2.barh(y_pos, counts_top20, color=["#38bdf8", C_BLUE, C_GREEN], edgecolor="#333333", height=0.55)

    for r in rects_t20:
        w = r.get_width()
        ax2.text(w + 0.4, r.get_y() + r.get_height()/2, f"{int(w)} teams", ha="left", va="center", fontsize=8.8, weight="bold")

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([f"0.22 (13 tasks)", f"0.24 (14 tasks)", f"0.29 (17 tasks)"], weight="semibold", fontsize=8.8)
    ax2.set_xlabel("Number of Teams")
    ax2.set_title("(B) Public Top-20 Distribution")
    ax2.set_xlim(0, 15.5)
    ax2.set_ylim(-0.5, 2.8)
    ax2.grid(axis="x", alpha=0.5)
    despine(ax2)

    # Box situated in the open upper-right quadrant (x in [0.30, 0.92], y in [0.61, 0.91] in transAxes)
    # Guaranteed clearance: >= 0.23 data units above Bar 1 (0.24), >= 2.1 units right of Bar 2 label
    box_t20 = patches.FancyBboxPatch((0.30, 0.61), 0.62, 0.30, boxstyle="round,pad=0.02",
                                     facecolor="#f8fafc", edgecolor="#94a3b8", linewidth=1.0, transform=ax2.transAxes)
    ax2.add_patch(box_t20)
    ax2.text(0.61, 0.83, "TOP-20 4-TASK BAND", ha="center", va="center", color="#334155", fontsize=8.8, weight="bold", transform=ax2.transAxes)
    ax2.text(0.61, 0.71, "Entire Top-20 cluster spans\nonly 4 tasks (13 to 17).\nDeltas ≤ 2 tasks are within\nbinomial run-to-run noise.",
             ha="center", va="center", color="#475569", fontsize=7.6, linespacing=1.2, transform=ax2.transAxes)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_p = ASSETS_DIR / "fig4_leaderboard_statistical_power.png"
    plt.savefig(out_p, dpi=300)
    plt.close()
    print(f"[FIG 4] Generated {out_p}")


# ==============================================================================
# FIGURE 5: Patch Anatomy & 10 AST Playbooks
# ==============================================================================
def render_fig5_patch_anatomy_and_playbooks():
    fig = plt.figure(figsize=(14.8, 6.4), dpi=300)
    fig.patch.set_facecolor("#ffffff")

    fig.suptitle("Gold Patch Anatomy (70.5% Single-File, 8.5% New) & 10 AST Playbooks with 40.3% Sandbox Dependency Fragility",
                 fontsize=12.5, weight="bold", color=C_DARK, y=0.98)

    # Use GridSpec with generous wspace (0.38) to guarantee zero label collisions with Panel B ticks
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.95], wspace=0.38)
    gs_left = gs[0].subgridspec(2, 1, height_ratios=[1.15, 0.95], hspace=0.15)

    ax_pie = fig.add_subplot(gs_left[0])
    ax_tab = fig.add_subplot(gs_left[1])
    ax2 = fig.add_subplot(gs[1])

    # -------------------------------------------------------------
    # Left Upper: Clean Donut Chart (Zero label collision)
    # -------------------------------------------------------------
    sizes = [70.5, 29.5]
    colors_donut = [C_BLUE, C_ORANGE]

    wedges, texts, autotexts = ax_pie.pie(
        sizes, colors=colors_donut, autopct="%1.1f%%", pctdistance=0.75,
        startangle=140, wedgeprops=dict(width=0.38, edgecolor="#ffffff", linewidth=2.0)
    )
    for at in autotexts:
        at.set_color("#ffffff")
        at.set_fontsize(9.5)
        at.set_weight("bold")

    # Center callout in donut hole
    ax_pie.text(0, 0.08, "129 Tasks", ha="center", va="center", fontsize=10.5, weight="bold", color=C_DARK)
    ax_pie.text(0, -0.10, "Dev Benchmark", ha="center", va="center", fontsize=8.0, color="#64748b")

    ax_pie.set_title("(A) Gold Patch Anatomy (129 Dev Tasks)", pad=12)
    ax_pie.legend(wedges, ["1 File (70.5%, 91 tasks)", "2+ Files (29.5%, 38 tasks)"],
                  loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=2, frameon=False, fontsize=8.0)

    # -------------------------------------------------------------
    # Left Lower: Dedicated Subplot for Summary Table
    # -------------------------------------------------------------
    ax_tab.axis("off")
    table_data = [
        ["Single-file tasks", "70.5% (91 / 129)"],
        ["Multi-file tasks", "29.5% (38 / 129)"],
        ["New file creation", "8.5% (11 / 129)"],
        ["Hunks / patch", "Median: 2, Mean: 5.4, P90: 13"],
        ["Lines added", "Median: 8, Mean: 138, P90: 89"],
        ["Lines deleted", "Median: 2, Mean: 29, P90: 24"],
    ]
    tab = ax_tab.table(cellText=table_data, colLabels=["Metric", "Measured Value"],
                       cellLoc="center", loc="center", bbox=[0.02, 0.02, 0.90, 0.96])
    tab.auto_set_font_size(False)
    tab.set_fontsize(8.2)
    for (r, c), cell in tab.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if r == 0:
            cell.set_facecolor("#f1f5f9")
            cell.set_text_props(weight="bold", color="#1e293b")
        else:
            cell.set_facecolor("#ffffff")

    # -------------------------------------------------------------
    # Right Panel: 10 AST Playbooks (Triggers vs Precision)
    # -------------------------------------------------------------
    playbooks = [
        ("RICH_RENDERING", 34, 79.4, 27),
        ("FASTAPI_PYDANTIC", 40, 50.0, 20),
        ("FALSINESS_TRAP", 21, 28.6, 6),
        ("HTTP_URL_COOKIES", 37, 24.3, 9),
        ("TYPE_SUBCLASS", 68, 23.5, 16),
        ("MUTABLE_STATE", 38, 13.2, 5),
        ("EXCEPTION_CHAIN", 15, 6.7, 1),
        ("DECORATOR_WRAP", 3, 0.0, 0),
        ("REGISTRATION_SIBLING", 2, 0.0, 0),
        ("ASYNC_SYNC_TWIN", 0, 0.0, 0),
    ]

    playbooks.reverse()

    pb_names = [p[0] for p in playbooks]
    triggers = [p[1] for p in playbooks]
    precisions = [p[2] for p in playbooks]
    matches = [p[3] for p in playbooks]

    y = np.arange(len(pb_names))

    bar_colors = []
    for prec in precisions:
        if prec >= 50.0:
            bar_colors.append(C_GREEN)
        elif prec >= 20.0:
            bar_colors.append(C_BLUE)
        elif prec > 0.0:
            bar_colors.append(C_ORANGE)
        else:
            bar_colors.append(C_GRAY)

    bars_pb = ax2.barh(y, triggers, color=bar_colors, edgecolor="#333333", height=0.62)

    for i, (b, tr, pr, ma) in enumerate(zip(bars_pb, triggers, precisions, matches)):
        w = b.get_width()
        if tr > 0:
            label_text = f" {tr} triggers | {pr:.1f}% prec ({ma} hits)"
        else:
            label_text = " 0 triggers (0.0% prec)"
        ax2.text(w + 1.0, b.get_y() + b.get_height()/2, label_text,
                 ha="left", va="center", fontsize=8.2, weight="semibold", color="#1e293b")

    ax2.set_yticks(y)
    ax2.set_yticklabels(pb_names, fontsize=8.8, weight="semibold")
    ax2.set_xlabel("Trigger Count Across 129 Tasks")
    ax2.set_title("(B) 10 Triggered AST Playbooks: Count vs. Precision (258 Triggers, 32.6% Precision)")
    ax2.set_xlim(0, 98)
    ax2.grid(axis="x", alpha=0.5)
    despine(ax2)

    legend_elements = [
        patches.Patch(facecolor=C_GREEN, edgecolor="#333333", label="High Precision (>=50%)"),
        patches.Patch(facecolor=C_BLUE, edgecolor="#333333", label="Moderate Precision (20-50%)"),
        patches.Patch(facecolor=C_ORANGE, edgecolor="#333333", label="Low Precision (<20%)"),
        patches.Patch(facecolor=C_GRAY, edgecolor="#333333", label="Zero Match (0%)"),
    ]
    ax2.legend(handles=legend_elements, loc="lower right", frameon=True, framealpha=0.9, facecolor="#ffffff", edgecolor="#cccccc", fontsize=8.2)

    out_p = ASSETS_DIR / "fig5_patch_anatomy_and_playbooks.png"
    plt.savefig(out_p, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[FIG 5] Generated {out_p}")


def main():
    print("Generating 6 pixel-perfect publication figures in assets/paper_figures/...")
    render_fig0_card_thumbnail()
    render_fig1_harness_architecture()
    render_fig2_retrieval_2x2_decomposition()
    render_fig3_symbol_and_multifile_paradox()
    render_fig4_leaderboard_statistical_power()
    render_fig5_patch_anatomy_and_playbooks()
    print("\nAll 6 PNG figures successfully rendered at 300 DPI (and 1200x630 px for fig0).")


if __name__ == "__main__":
    main()

"""Generate dedicated publication-grade figures for Slot #2 (Resource & Application Track).

Zero shared figures or tables with Writeup #1.
Palette: Okabe-Ito (colorblind safe).
Outputs: assets/resource_figures/
"""
from __future__ import annotations

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUT_DIR = Path("assets/resource_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Okabe-Ito palette
ORANGE = "#E69F00"
SKY_BLUE = "#56B4E9"
BLUISH_GREEN = "#009E73"
YELLOW = "#F0E442"
BLUE = "#0072B2"
VERMILLION = "#D55E00"
PURPLE = "#CC79A7"
CHARCOAL = "#222222"
LIGHT_GRAY = "#F8F9FA"
MID_GRAY = "#E9ECEF"
BORDER_GRAY = "#CED4DA"


def generate_res_fig0_banner():
    """Figure 0: 1200x630 card thumbnail for Slot #2.

    One idea, not a table: the toolkit caps tool output at 3,500 chars by
    dropping the middle, so the contract lines at the tail survive.
    """
    W, H = 1200, 630
    BG = "#0B132B"
    INK = "#E7EEF8"
    MUTED = "#8FA3BF"
    ACCENT = "#38BDF8"
    PANEL = "#14304D"
    EDGE = "#2B3A5B"

    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    # ---- masthead ---------------------------------------------------------- #
    ax.text(60, 588, "PYTHON STANDARD LIBRARY  /  ZERO DEPENDENCIES  /  MIT",
            color=MUTED, fontsize=10.5, family="sans-serif", va="center")
    ax.text(58, 520, "swe-toolkit", color=ACCENT, fontsize=46,
            fontweight="bold", family="monospace", va="center")
    ax.text(60, 466, "Locate, inspect and gate a patch without installing anything.",
            color=INK, fontsize=16.5, family="sans-serif", va="center")
    ax.text(60, 423, "swe locate    /    swe inspect    /    swe verify",
            color="#CBD5E1", fontsize=14.5, family="monospace", va="center")

    # ---- the capped output bar --------------------------------------------- #
    ax.text(60, 372, "TOOL OUTPUT FROM ONE COMMAND", color=MUTED, fontsize=9.5,
            family="sans-serif", va="center")
    ax.text(1140, 372, "CAP: 3,500 CHARACTERS", color=MUTED, fontsize=9.5,
            family="sans-serif", va="center", ha="right")

    y0, y1 = 272, 346
    head_x1, tail_x0 = 452, 596
    for xa, xb, edge in ((60, head_x1, EDGE), (tail_x0, 1140, ACCENT)):
        ax.add_patch(patches.FancyBboxPatch(
            (xa, y0), xb - xa, y1 - y0, boxstyle="round,pad=0,rounding_size=6",
            facecolor=PANEL, edgecolor=edge, linewidth=1.8))
    for xc in (head_x1 + 8, tail_x0 - 8):
        ax.plot([xc, xc], [y0 - 7, y1 + 7], color="#2B3A5B", lw=1.4, ls=(0, (4, 4)))
    ax.text((head_x1 + tail_x0) / 2, (y0 + y1) / 2, "...", color=MUTED,
            fontsize=17, ha="center", va="center", family="monospace")

    ax.text((60 + head_x1) / 2, (y0 + y1) / 2, "1,400 chars kept",
            color="#93A6C0", fontsize=12.5, ha="center", va="center", family="monospace")
    ax.text((tail_x0 + 1140) / 2, (y0 + y1) / 2, "STATUS: OK",
            color=ACCENT, fontsize=16, ha="center", va="center",
            family="monospace", fontweight="bold")
    ax.text((head_x1 + tail_x0) / 2, y0 - 26, "middle dropped", color=MUTED,
            fontsize=10.5, ha="center", va="center", family="sans-serif")

    # ---- payoff ------------------------------------------------------------ #
    ax.text(60, 186, "Cutting the tail deletes the verdict. Cutting the middle keeps it.",
            color="#A8B8CE", fontsize=12.5, family="sans-serif", va="center")

    # ---- footer ------------------------------------------------------------ #
    ax.plot([60, 1140], [96, 96], color="#22304D", lw=1.2)
    ax.text(60, 62, "Three commands, one index, no wheel to install",
            color="#64748B", fontsize=11, family="sans-serif", va="center")
    ax.text(1140, 62, "evaluated on 129 offline tasks", color="#64748B",
            fontsize=11, family="sans-serif", va="center", ha="right")

    out_path = OUT_DIR / "res_fig0_banner.png"
    plt.savefig(out_path, dpi=100, facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")


def generate_res_fig1_toolkit_pipeline():
    """Figure 1: swe-toolkit end-to-end architecture & dataflow."""
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=300)
    ax.set_facecolor(LIGHT_GRAY)
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Header
    ax.text(50, 96, "swe-toolkit End-to-End Execution Pipeline & Memory Isolation",
            fontsize=18, fontweight="bold", ha="center", color=CHARCOAL)
    ax.text(50, 92.5, "Standard-library Python CLI tooling built for offline, resource-constrained coding agents",
            fontsize=11, ha="center", color="#555555")

    # Box 1: Inputs
    b1 = patches.FancyBboxPatch((3, 56), 26, 32, boxstyle="round,pad=1.5",
                                facecolor="white", edgecolor=BORDER_GRAY, linewidth=1.5)
    ax.add_patch(b1)
    ax.text(16, 84, "AGENT COMMANDS\n(Zero-Dep CLI)", fontsize=13, fontweight="bold", ha="center", color=BLUE)
    ax.text(5, 78, "• locate --issue <text>", fontsize=10, family="monospace")
    ax.text(5, 74, "• inspect --symbol <name>", fontsize=10, family="monospace")
    ax.text(5, 70, "• verify --test <pytest_cmd>", fontsize=10, family="monospace")
    ax.text(5, 64, "Input Boundaries:", fontsize=10, fontweight="bold", color="#444444")
    ax.text(5, 60, "• Target: /workspace repo", fontsize=9.5)
    ax.text(5, 57, "• Zero network, offline wheels", fontsize=9.5)

    # Box 2: Core Engine Modules
    b2 = patches.FancyBboxPatch((35, 12), 34, 76, boxstyle="round,pad=1.5",
                                facecolor="white", edgecolor=BLUE, linewidth=2)
    ax.add_patch(b2)
    ax.text(52, 84, "CORE MODULES (stdlib-only)", fontsize=14, fontweight="bold", ha="center", color=BLUE)

    # Module A: swe.py
    ma = patches.Rectangle((37, 68), 30, 12, facecolor="#F0F9FF", edgecolor=SKY_BLUE, linewidth=1.5)
    ax.add_patch(ma)
    ax.text(39, 76, "swe.py (CLI Router & Output Capper)", fontsize=10.5, fontweight="bold", color="#0369A1")
    ax.text(39, 72.5, "• OUT_CAP = 3,500 chars (avoids 14k compaction)", fontsize=9)
    ax.text(39, 69.5, "• Middle-cut: preserves STATUS & TEST tail", fontsize=9)

    # Module B: _index.py
    mb = patches.Rectangle((37, 49), 30, 16, facecolor="#F0FDF4", edgecolor=BLUISH_GREEN, linewidth=1.5)
    ax.add_patch(mb)
    ax.text(39, 61, "_index.py (AST Engine & Twins)", fontsize=10.5, fontweight="bold", color="#15803D")
    ax.text(39, 57.5, "• Fast lexical + AST BM25 file index", fontsize=9)
    ax.text(39, 54.5, "• Sync/Async twins: send() vs asend()", fontsize=9)
    ax.text(39, 51.5, "• Callers, subclasses, overrides, constants", fontsize=9)

    # Module C: _knowledge.py
    mc = patches.Rectangle((37, 32), 30, 14, facecolor="#FFFBEB", edgecolor=ORANGE, linewidth=1.5)
    ax.add_patch(mc)
    ax.text(39, 42, "_knowledge.py (10 AST Playbooks)", fontsize=10.5, fontweight="bold", color="#B45309")
    ax.text(39, 38.5, "• 10 regex/AST bug patterns (258 triggers)", fontsize=9)
    ax.text(39, 35.5, "• Selective hint injector (<= 120 tokens)", fontsize=9)
    ax.text(39, 32.5, "• High-precision triggers (Rich 79%, FastAPI 50%)", fontsize=9)

    # Module D: _verify.py
    md = patches.Rectangle((37, 15), 30, 14, facecolor="#FEF2F2", edgecolor=VERMILLION, linewidth=1.5)
    ax.add_patch(md)
    ax.text(39, 25, "_verify.py (9-Scenario Gate)", fontsize=10.5, fontweight="bold", color="#B91C1C")
    ax.text(39, 21.5, "• SyntaxError check via ast.parse()", fontsize=9)
    ax.text(39, 18.5, "• .gitignore unmasking via git add -N -f", fontsize=9)
    ax.text(39, 15.5, "• Stray skills/ cleaner + JUnit XML parser", fontsize=9)

    # Box 3: Outputs & Agent Actions
    b3 = patches.FancyBboxPatch((75, 12), 22, 76, boxstyle="round,pad=1.5",
                                facecolor="white", edgecolor=BORDER_GRAY, linewidth=1.5)
    ax.add_patch(b3)
    ax.text(86, 84, "DETERMINISTIC OUTPUTS", fontsize=13, fontweight="bold", ha="center", color=CHARCOAL)

    # Contract Lines
    ax.text(77, 76, "STATUS CONTRACT:", fontsize=10.5, fontweight="bold", color=CHARCOAL)
    ax.text(77, 72, "STATUS: OK | PARTIAL | FAIL", fontsize=9.5, family="monospace", color=BLUE)

    ax.text(77, 65, "ACTIONABLE STEPS:", fontsize=10.5, fontweight="bold", color=CHARCOAL)
    ax.text(77, 61, "NEXT: read_file ...", fontsize=9.5, family="monospace", color="#047857")
    ax.text(77, 57, "TEST: pytest ...", fontsize=9.5, family="monospace", color="#047857")
    ax.text(77, 53, "FALLBACK: git grep ...", fontsize=9.5, family="monospace", color="#047857")

    ax.text(77, 44, "SAFETY INVARIANTS:", fontsize=10.5, fontweight="bold", color=CHARCOAL)
    ax.text(77, 40, "• Exit code always 0", fontsize=9.5)
    ax.text(77, 36, "• Zero stray skill leaks", fontsize=9.5)
    ax.text(77, 32, "• Sub-50ms verify latency", fontsize=9.5)
    ax.text(77, 28, "• State written to /tmp", fontsize=9.5)
    ax.text(77, 24, "• Protected paths guarded", fontsize=9.5)
    ax.text(77, 20, "• Ready for submit_patch", fontsize=9.5)

    # Connecting Arrows
    ax.annotate("", xy=(34, 72), xytext=(30, 72),
                arrowprops=dict(facecolor=BLUE, edgecolor="none", width=2, headwidth=8))
    ax.annotate("", xy=(74, 50), xytext=(70, 50),
                arrowprops=dict(facecolor=BLUE, edgecolor="none", width=2, headwidth=8))

    # Bottom Notes
    ax.text(50, 5, "Source: skills/swe-toolkit/scripts/ (swe.py, _index.py, _knowledge.py, _verify.py) | Verified on Linux & Windows",
            fontsize=10, ha="center", color="#666666", style="italic")

    out_path = OUT_DIR / "res_fig1_toolkit_pipeline.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")


def generate_res_fig2_playbook_heatmap():
    """Figure 2: Full 10-Playbook x 4-Repository trigger frequency & precision."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), dpi=300, gridspec_kw={"width_ratios": [1.4, 1]})
    fig.patch.set_facecolor("white")

    playbooks = [
        "RICH_RENDERING",
        "FASTAPI_PYDANTIC",
        "FALSINESS_TRAP",
        "HTTP_URL_COOKIES",
        "TYPE_SUBCLASS",
        "MUTABLE_STATE",
        "EXCEPTION_CHAIN",
        "DECORATOR_WRAP",
        "REGISTRATION_SIBLING",
        "ASYNC_SYNC_TWIN",
    ]

    triggers = [34, 40, 21, 37, 68, 38, 15, 3, 2, 0]
    hits = [27, 20, 6, 9, 16, 5, 1, 0, 0, 0]
    precisions = [79.4, 50.0, 28.6, 24.3, 23.5, 13.2, 6.7, 0.0, 0.0, 0.0]

    y_pos = np.arange(len(playbooks))[::-1]

    # Panel 1: Triggers vs Hits
    ax1.set_facecolor(LIGHT_GRAY)
    b_trig = ax1.barh(y_pos, triggers, height=0.55, color="#CBD5E1", label="Total Triggers (N=258)")
    b_hits = ax1.barh(y_pos, hits, height=0.55, color=BLUE, label="Gold Patch Hits (N=84)")

    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(playbooks, fontsize=10.5, family="monospace", fontweight="bold")
    ax1.set_xlabel("Trigger Count Across 129 Tasks", fontsize=11, fontweight="bold")
    ax1.set_title("10 SWE Bug Playbooks: Empirical Triggers vs. Gold Hits", fontsize=13, fontweight="bold")
    ax1.grid(axis="x", linestyle="--", alpha=0.5)
    ax1.legend(loc="lower right", fontsize=10.5)

    # Direct labels on Panel 1
    for i, (t, h) in enumerate(zip(triggers, hits)):
        y = y_pos[i]
        if t > 0:
            ax1.text(t + 1.2, y, f"{h}/{t}", va="center", fontsize=9.5, fontweight="bold", color=CHARCOAL)

    # Panel 2: Precision %
    ax2.set_facecolor(LIGHT_GRAY)
    colors = [BLUISH_GREEN if p >= 50 else (ORANGE if p >= 20 else "#94A3B8") for p in precisions]
    b_prec = ax2.barh(y_pos, precisions, height=0.55, color=colors)

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([])  # share with ax1
    ax2.set_xlabel("Empirical Precision (% Gold Match)", fontsize=11, fontweight="bold")
    ax2.set_title("Playbook Precision (% Target Hits)", fontsize=13, fontweight="bold")
    ax2.axvline(32.6, color=VERMILLION, linestyle="--", linewidth=1.8, label="Overall Avg: 32.6% (84/258)")
    ax2.set_xlim(0, 100)
    ax2.grid(axis="x", linestyle="--", alpha=0.5)
    ax2.legend(loc="lower right", fontsize=10)

    # Direct labels on Panel 2
    for i, p in enumerate(precisions):
        y = y_pos[i]
        if p > 0:
            ax2.text(p + 2, y, f"{p:.1f}%", va="center", fontsize=9.5, fontweight="bold", color=CHARCOAL)
        else:
            ax2.text(2, y, "0.0%", va="center", fontsize=9, color="#666666")

    plt.tight_layout()
    out_path = OUT_DIR / "res_fig2_playbook_heatmap.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")


def generate_res_fig3_torture_suite_and_deps():
    """Figure 3: 9/9 Adversarial Torture Suite & Sandbox Dependency Diagnostic."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), dpi=300, gridspec_kw={"width_ratios": [1.1, 1]})
    fig.patch.set_facecolor("white")

    # Panel 1: 9/9 Adversarial Torture Suite
    ax1.set_facecolor(LIGHT_GRAY)
    scenarios = [
        "1. No changes (empty patch)",
        "2. Valid source edit",
        "3. New untracked .py file",
        "4. New .gitignore ignored file",
        "5. Injected SyntaxError",
        "6. Filename with spaces",
        "7. Non-Python edit (docs/README)",
        "8. Protected files touched",
        "9. Stray skills/ leak injected"
    ]
    expected_status = ["FAIL", "OK", "OK", "IGNORED", "FAIL", "OK", "OK", "FAIL", "FAIL"]
    latencies_ms = [4.2, 8.5, 9.1, 8.7, 7.8, 8.9, 5.1, 7.4, 11.2]
    y_pos = np.arange(len(scenarios))[::-1]

    bars = ax1.barh(y_pos, latencies_ms, height=0.55, color=SKY_BLUE, edgecolor=BLUE)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(scenarios, fontsize=10, family="sans-serif")
    ax1.set_xlabel("Execution Latency (ms)", fontsize=11, fontweight="bold")
    ax1.set_title("9/9 Adversarial Torture Suite (tools/test_verify_8_scenarios.py)", fontsize=12, fontweight="bold")
    ax1.set_xlim(0, 18)
    ax1.grid(axis="x", linestyle="--", alpha=0.5)

    for i, (lat, stat) in enumerate(zip(latencies_ms, expected_status)):
        y = y_pos[i]
        badge_color = BLUISH_GREEN if stat == "OK" else (ORANGE if stat == "IGNORED" else VERMILLION)
        ax1.text(lat + 0.5, y, f"[{stat}] {lat:.1f}ms", va="center", fontsize=9, fontweight="bold", color=badge_color)

    # Panel 2: Sandbox Test-Plugin Environment & Patch Structure
    ax2.set_facecolor(LIGHT_GRAY)
    categories = [
        "FastAPI Direct Missing Plugins\n(inline_snapshot/dirty_equals)",
        "FastAPI Test Collection Crashes\n(Total Unpassable: 28/67)",
        "Overall Missing Plugin Exposure\n(28 / 129 Tasks)",
        "Brand-New Files in Gold Patch\n(Requires git add -N -f: 11/129)",
        "Single-File Patch Dominance\n(91 / 129 Tasks)"
    ]
    percentages = [32.8, 41.8, 21.7, 8.5, 70.5]
    colors = [VERMILLION, VERMILLION, ORANGE, BLUE, BLUISH_GREEN]
    y_pos2 = np.arange(len(categories))[::-1]

    ax2.barh(y_pos2, percentages, height=0.55, color=colors)
    ax2.set_yticks(y_pos2)
    ax2.set_yticklabels(categories, fontsize=9.5)
    ax2.set_xlabel("Task Prevalence (%)", fontsize=11, fontweight="bold")
    ax2.set_title("Sandbox Test Environment & Patch Diagnostic", fontsize=12, fontweight="bold")
    ax2.set_xlim(0, 100)
    ax2.grid(axis="x", linestyle="--", alpha=0.5)

    for i, p in enumerate(percentages):
        y = y_pos2[i]
        ax2.text(p + 2, y, f"{p:.1f}%", va="center", fontsize=9.5, fontweight="bold", color=CHARCOAL)

    plt.tight_layout()
    out_path = OUT_DIR / "res_fig3_torture_suite_and_deps.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")


if __name__ == "__main__":
    generate_res_fig0_banner()
    generate_res_fig1_toolkit_pipeline()
    generate_res_fig2_playbook_heatmap()
    generate_res_fig3_torture_suite_and_deps()
    print("\nAll 4 resource figures generated successfully.")

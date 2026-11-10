"""Phase 3 — Top teams (0.22-0.29) public notebooks/discussions vs our harness.

Self-contained: fetches live leaderboard via bearer auth (KAGGLE_KEY/KAGGLE_API_TOKEN/
kaggle.json) because the kaggle CLI 401s on the KGAT token. Reads the two
already-downloaded public notebooks (research/public_intel/kernels/*, top_kernels/*).
Compares harness settings with our exp05 anchor on `main`.

Limitation (stated honestly): individual notebook/discussion pages are JS-rendered
(fetch returns only the page title), and we cannot fetch each top-20 team's notebook
to confirm authorship or read full config. None of the downloaded notebook authors are
confirmed members of the leaderboard top-20.

Outputs: research/direction_checks2/phase3_top_teams.json
         research/direction_checks2/leaderboard_live.csv (refetched live)
"""
from __future__ import annotations

import csv
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
D2 = Path(__file__).resolve().parent
OUT = D2 / "phase3_top_teams.json"
LB_CSV = D2 / "leaderboard_live.csv"
BASE = "https://www.kaggle.com"


def token() -> str:
    t = os.environ.get("KAGGLE_KEY") or os.environ.get("KAGGLE_API_TOKEN")
    if not t:
        import json as _j
        p = Path(os.path.expanduser("~/.kaggle/kaggle.json"))
        if p.is_file():
            t = _j.loads(p.read_text()).get("key")
    if not t:
        raise SystemExit("no bearer token")
    return t


def get(path: str):
    url = path if path.startswith("http") else BASE + path
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token()}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def fetch_leaderboard() -> list[dict]:
    status, body = get("/api/v1/competitions/gemma-4-developer-agent/leaderboard/view")
    rows = []
    if status == 200:
        data = json.loads(body)
        rows = data if isinstance(data, list) else data.get("submissions", [])
    with LB_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        if rows and isinstance(rows[0], dict):
            w.writerow(rows[0].keys())
            for r in rows:
                w.writerow(r.values())
    return rows


OURS = {
    "model": "gemma-4-31b-it-qat-w4a16-ct",
    "tools": "run_command, read_file, edit_file, write_file, get_status, submit_patch, "
    "get_code_neighbors, search_similar_code, get_code_subgraph (9 tools; exp15 drops "
    "the 3 graph tools -> 6 base tools)",
    "temperature": 0.2,
    "top_p": 0.95,
    "max_output_tokens": 8192,
    "thinking_budget": 4096,
    "include_thoughts": True,
    "max_tool_calls": 28,
    "max_time_minutes": 8,
    "max_turns": 80,
    "timeout_seconds": 240,
    "skills": "none declared",
    "patch_gate": "git add -N -f on untracked .py (patch-integrity check)",
    "prompt_len_chars": 5461,
    "source": "bundles/exp05_patch_integrity (anchor; exp15 pending ref 58183079)",
}


def main() -> int:
    rows = fetch_leaderboard()
    teams = []
    for r in rows:
        try:
            score = float(r.get("score", 0) or 0)
        except (ValueError, TypeError):
            continue
        if score >= 0.22:
            teams.append({"team": r.get("teamName"), "score": score, "date": r.get("submissionDate", "")})
    result = {
        "source_leaderboard": "live /leaderboard/view via bearer auth (HTTP 200)",
        "top_teams_score_ge_022": teams,
        "note": (
            "Live /leaderboard/view returns only top-20 best scores. All scores are "
            "multiples of 1/58 (0.29~17/58, 0.24~14/58, 0.22~13/58)."
        ),
        "downloaded_public_notebooks": [],
        "confirmed_top20_match": False,
        "reason_no_match": (
            "No downloaded notebook author is confirmed as a leaderboard top-20 team. "
            "Cannot fetch per-team notebooks (notebook pages JS-rendered; CLI 401s). "
            "Differences below are for the two downloaded notebooks only, NOT attributed "
            "to top-20 teams."
        ),
    }
    nb1 = {
        "file": "research/public_intel/kernels/gemma-4-loop-breaker-adk-agent.ipynb",
        "metadata_author": "prvsiyan/gemma-and-the-shape-of-doubt",
        "note": "metadata id (prvsiyan) conflicts with file content (robinamirbahar loop-breaker); authorship UNVERIFIED",
        "url": "https://www.kaggle.com/code/robinamirbahar/gemma-4-loop-breaker-adk-agent",
        "harness": {
            "model": "gemma-4-31b-it-qat-w4a16-ct",
            "tools": "9 base incl. get_code_neighbors/search_similar_code/get_code_subgraph",
            "temperature": 0.2,
            "top_p": 0.95,
            "max_output_tokens": 8192,
            "thinking_budget": 4096,
            "max_tool_calls": 28,
            "max_time_minutes": 8,
            "max_turns": 80,
            "skills": "none",
            "patch_gate": "not evident in dumped config",
            "prompt_len_chars": "~3,756 (per public notes)",
        },
        "diff_vs_ours": "Same harness as exp05; adds loop-breaker/anti-compaction STATE rule; prompt shorter (~3,756 vs 5,461 chars).",
    }
    result["downloaded_public_notebooks"].append(nb1)
    nb2 = {
        "file": "research/public_intel/top_kernels/lb-0-22-4-config-files-no-training.ipynb",
        "metadata_author": "jocelyndumlao/trace-test-guided-repository-exploration",
        "note": "metadata id (jocelyndumlao) conflicts with leaderboard author (bliverrigpdoge); competition_source=paper track; authorship UNVERIFIED",
        "url": "https://www.kaggle.com/code/bliverrigpdoge/lb-0-22-4-config-files-no-training",
        "harness": {
            "model": "not found inline (references GitHub jcdumlao14/...paper-track results)",
            "tools": "not found inline",
            "temperature": "not found inline",
            "top_p": "not found inline",
            "max_output_tokens": "not found inline",
            "thinking_budget": "not found inline",
            "max_tool_calls": "not found inline",
            "skills": "not found inline",
            "patch_gate": "not found inline",
            "prompt_len_chars": "not found inline",
        },
        "diff_vs_ours": "Harness settings not extractable from downloaded notebook; full config not available.",
    }
    result["downloaded_public_notebooks"].append(nb2)
    OUT.write_text(json.dumps(result, indent=2))
    print("LEADERBOARD top teams (>=0.22):")
    for t in teams:
        print(f"  {t['team']}: {t['score']} ({t['date']})")
    print(f"\nWrote {OUT} and {LB_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

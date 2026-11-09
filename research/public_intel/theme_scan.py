"""Detect mechanism themes across every extracted public payload."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAY = ROOT / "payloads"

THEMES = {
    "batch_searches": r"(batch|combine|one run_command|single run_command|combine independent)",
    "multi_region_read": r"(sed -n|three regions|multi-region|explicit line ranges)",
    "edit_recovery": r"(no match or multiple matches|heredoc|retry with a smaller|failed edit)",
    "no_repeat_call": r"(never repeat|do not repeat|not spend another tool call repeating|repeat an identical)",
    "patch_integrity": r"(git add -N|\.gitignore)",
    "scratch_tmp": r"(/tmp)",
    "docs_src": r"docs_src",
    "timeout_150": r"timeout 150",
    "get_status": r"get_status",
    "call12_deadline": r"(by (your )?(tool call|the) 12|call 12|12th tool call)",
    "loop_break": r"(jaccard|loop[- ]breaker|repetition|CCR)",
    "compact_prompt": r"(compaction|14,?336|state card)",
    "graph_tools_banned": r"(never use .search_similar_code|get_code_neighbors.*return nothing)",
    "lean_6_tools": r"(run_command.*read_file.*edit_file.*write_file.*get_status.*submit_patch)",
    "seed": r"seed:",
}


def main() -> int:
    rows = []
    for d in sorted(PAY.iterdir()):
        if not d.is_dir():
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8")) if (d / "meta.json").exists() else {}
        agent = d / "agent.yaml"
        prompt = d / "prompts" / "system.md"
        if not agent.exists() or not prompt.exists():
            continue
        a = agent.read_text(encoding="utf-8")
        p = prompt.read_text(encoding="utf-8")
        tools = re.findall(r"^\s*-\s*(\w+)\s*$", a, re.M)
        hits = [name for name, pat in THEMES.items() if re.search(pat, p, re.I | re.S) or re.search(pat, a, re.I | re.S)]
        rows.append(
            {
                "kernel": d.name.replace("__", "/"),
                "score": meta.get("bundle_hash", "-"),
                "prompt": len(p),
                "tools": len(tools),
                "themes": hits,
            }
        )
    for r in rows:
        print(f"{r['kernel']:<58} h={r['score'][:10]:<10} p={r['prompt']:<5} t={r['tools']:<2} {','.join(r['themes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

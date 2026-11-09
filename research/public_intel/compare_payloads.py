"""Summarise every extracted public payload: tools, sampling, eval budget, prompt size."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAY = ROOT / "payloads"


def yamlish(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = re.match(r"^(\s*)([A-Za-z_][\w]*):\s*(.*)$", line)
        if m:
            out.setdefault(m.group(2), m.group(3).strip())
    return out


def main() -> int:
    rows = []
    for d in sorted(PAY.iterdir()):
        if not d.is_dir():
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8")) if (d / "meta.json").exists() else {}
        agent = (d / "agent.yaml")
        sampling = (d / "configs" / "sampling.yaml")
        ev = (d / "eval_config.yaml")
        prompt = (d / "prompts" / "system.md")
        tools = []
        model = None
        if agent.exists():
            for line in agent.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*-\s*(\w+)\s*$", line)
                if m:
                    tools.append(m.group(1))
                m2 = re.match(r"^model:\s*(\S+)", line)
                if m2:
                    model = m2.group(1)
        s = yamlish(sampling.read_text(encoding="utf-8")) if sampling.exists() else {}
        e = yamlish(ev.read_text(encoding="utf-8")) if ev.exists() else {}
        pchars = len(prompt.read_text(encoding="utf-8")) if prompt.exists() else None
        rows.append(
            {
                "kernel": d.name.replace("__", "/"),
                "model": model,
                "tools": len(tools),
                "toolset": ",".join(tools),
                "temp": s.get("temperature"),
                "top_p": s.get("top_p"),
                "top_k": s.get("top_k"),
                "max_out": s.get("max_output_tokens"),
                "think": s.get("thinking_budget"),
                "thoughts": s.get("include_thoughts"),
                "calls": e.get("max_tool_calls"),
                "min": e.get("max_time_minutes"),
                "turns": e.get("max_turns"),
                "timeout": e.get("timeout_seconds"),
                "prompt": pchars,
                "members": meta.get("member_count"),
            }
        )
    hdr = f"{'kernel':<58}{'model':<10}{'tl':>3}{'tmp':>5}{'topk':>5}{'mout':>6}{'think':>6}{'calls':>6}{'min':>4}{'turns':>6}{'prompt':>7}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        mm = (r["model"] or "-").replace("gemma-4-", "").replace("-it-qat-w4a16-ct", "")[:9]
        print(
            f"{r['kernel']:<58}{mm:<10}{r['tools']:>3}{str(r['temp'] or '-'):>5}{str(r['top_k'] or '-'):>5}"
            f"{str(r['max_out'] or '-'):>6}{str(r['think'] or '-'):>6}{str(r['calls'] or '-'):>6}"
            f"{str(r['min'] or '-'):>4}{str(r['turns'] or '-'):>6}{str(r['prompt'] or '-'):>7}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

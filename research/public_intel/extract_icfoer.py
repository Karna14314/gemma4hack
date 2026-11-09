"""Extract icfoer's SYSTEM_PROMPT (LoRA-adapter bundle; prompt only, adapter is out of scope)."""
import json
import re
from pathlib import Path

d = Path(__file__).resolve().parent / "pulled" / "icfoer__gemma4-developer-agent-lora-200-test"
nb = json.loads(next(p for p in d.iterdir() if p.suffix == ".ipynb").read_text(encoding="utf-8"))
src = "".join("".join(c["source"]) for c in nb["cells"])
m = re.search(r'SYSTEM_PROMPT = """(.*?)"""', src, re.S)
out = Path(__file__).resolve().parent / "payloads" / d.name
(out / "prompts").mkdir(parents=True, exist_ok=True)
(out / "prompts" / "system.md").write_text(m.group(1), encoding="utf-8", newline="")
print("icfoer prompt chars", len(m.group(1)))

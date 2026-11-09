"""Compute the census-style bundle hash for notebooks in research/public_notebooks."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_payloads import interpret, pick_payload  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "public_notebooks"

for d in sorted(ROOT.iterdir()):
    if not d.is_dir():
        continue
    ip = next((p for p in d.iterdir() if p.suffix == ".ipynb"), None)
    if ip is None:
        continue
    nb = json.loads(ip.read_text(encoding="utf-8"))
    ns: dict = {}
    for c in nb.get("cells", []):
        if c.get("cell_type") == "code":
            interpret("".join(c.get("source", [])), ns)
    name, files = pick_payload(ns)
    if not files:
        print(f"{d.name:<62} no payload")
        continue
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:12]
    prompt = next((v for k, v in files.items() if "system" in k.lower()), "")
    print(f"{d.name:<62} {digest}  members={len(files)} prompt={len(prompt)} var={name}")

"""Extract payloads from research/public_notebooks into research/public_intel/payloads."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_payloads import interpret, pick_payload  # noqa: E402

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "public_notebooks"
OUT = HERE / "payloads"

for d in sorted(SRC.iterdir()):
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
        continue
    files = {k: v for k, v in files.items() if isinstance(k, str) and isinstance(v, str)}
    if not files:
        continue
    outdir = OUT / d.name
    outdir.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        p = outdir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="")
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:12]
    meta = {
        "kernel": d.name,
        "method": "static",
        "payload_var": name,
        "bundle_hash": digest,
        "members": sorted(files),
        "member_count": len(files),
        "total_bytes": sum(len(v) for v in files.values()),
        "prompt_chars": next(
            (len(v) for k, v in files.items() if "system" in k.lower() or "prompt" in k.lower()), None
        ),
    }
    (outdir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"{d.name:<62} {digest} members={len(files)} prompt={meta['prompt_chars']}")

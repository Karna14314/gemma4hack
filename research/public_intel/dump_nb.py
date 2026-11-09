"""Dump every cell of a pulled notebook to a single UTF-8 text file for review."""
import json
import os
import sys
from pathlib import Path

d = Path(sys.argv[1])
ip = next(p for p in d.iterdir() if p.suffix == ".ipynb")
nb = json.loads(ip.read_text(encoding="utf-8"))
parts = []
for i, c in enumerate(nb.get("cells", [])):
    s = "".join(c.get("source", []))
    parts.append("=" * 30 + f" CELL {i} [{c.get('cell_type')}] len={len(s)}")
    parts.append(s)
(d / "_dump.txt").write_text("\n".join(parts), encoding="utf-8")
print(d.name, len("\n".join(parts)))

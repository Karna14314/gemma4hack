"""Print only the markdown cells of a pulled/public notebook (claims, evidence, narrative)."""
import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
ip = next(p for p in d.iterdir() if p.suffix == ".ipynb")
nb = json.loads(ip.read_text(encoding="utf-8"))
for i, c in enumerate(nb.get("cells", [])):
    if c.get("cell_type") != "markdown":
        continue
    s = "".join(c.get("source", []))
    # strip html noise
    import re
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s:
        print(f"--- md cell {i}: {s[:1500]}")

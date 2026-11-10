"""Extract a prompt/config literal from a notebook by variable name and diff it against a reference."""
import json
import re
import sys
from pathlib import Path

nb_path = Path(sys.argv[1])
var = sys.argv[2]
ref = Path(sys.argv[3]) if len(sys.argv) > 3 else None

nb = json.loads(nb_path.read_text(encoding="utf-8"))
src = "\n".join("".join(c.get("source", [])) for c in nb.get("cells", []))
m = re.search(rf'{var}\s*=\s*"""(.*?)"""', src, re.S)
if not m:
    m = re.search(rf'{var}\s*=\s*\'\'\'(.*?)\'\'\'', src, re.S)
if not m:
    print(f"could not find {var}")
    raise SystemExit(1)
text = m.group(1)
out = Path(sys.argv[4]) if len(sys.argv) > 4 else None
if out:
    out.write_text(text, encoding="utf-8", newline="")
print(f"{var}: {len(text)} chars")
if ref:
    a = ref.read_text(encoding="utf-8")
    print(f"reference: {len(a)} chars")
    import difflib
    d = list(difflib.unified_diff(a.splitlines(), text.splitlines(), "reference", var, lineterm="", n=0))
    print(f"diff lines: {len(d)}")
    print("\n".join(d[:40]))

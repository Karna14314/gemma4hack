"""Dump a .ipynb's cells to readable text for research purposes."""
import json
import sys
from pathlib import Path


def dump(path: Path, out_dir: Path) -> None:
    nb = json.loads(path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = []
    for i, cell in enumerate(nb.get("cells", [])):
        src = "".join(cell.get("source", []))
        kind = cell.get("cell_type")
        parts.append(f"\n{'=' * 78}\n### CELL {i} [{kind}]\n{'=' * 78}\n{src}")
    text = "\n".join(parts)
    target = out_dir / (path.stem + ".txt")
    target.write_text(text, encoding="utf-8")
    print(f"{path.name}: {len(nb.get('cells', []))} cells -> {target} ({len(text)} chars)")


if __name__ == "__main__":
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("notes/pulled_txt")
    files = [src] if src.is_file() else sorted(src.rglob("*.ipynb"))
    for f in files:
        dump(f, out)

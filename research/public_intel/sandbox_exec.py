"""Execute a CPU-only, filesystem-writing notebook inside a sandbox temp root.

Used for public notebooks that build `submission.zip` by writing files under
`/kaggle/working` instead of materialising a FILES dict in memory. The notebook source is
rewritten so that the literal `/kaggle/working` prefix points at a temp directory, then
executed with a minimal stdlib shim. Only notebooks that are self-contained CPU builders
should be run through this; research notebooks that read competition data are excluded.

The rewritten source is printed to `<out>/_exec.py` for audit. Nothing outside the temp
root is written.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PULLED = ROOT / "pulled"
OUT = ROOT / "payloads"


def run_kernel(dirpath: Path, temp_root: Path) -> dict:
    ipynb = next(p for p in dirpath.iterdir() if p.suffix == ".ipynb")
    nb = json.loads(ipynb.read_text(encoding="utf-8"))
    parts = []
    for i, c in enumerate(nb.get("cells", [])):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        if not src.strip():
            continue
        parts.append(f"# ---- cell {i} ----\n{src}")
    joined = "\n\n".join(parts)
    rewritten = joined.replace("/kaggle/working", str(temp_root).replace("\\", "/"))

    outdir = OUT / dirpath.name
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "_exec.py").write_text(rewritten, encoding="utf-8")

    g = {"__name__": "__main__", "__file__": str(outdir / "_exec.py")}
    try:
        exec(compile(rewritten, str(outdir / "_exec.py"), "exec"), g)  # noqa: S102 - deliberate, sandboxed
        error = None
    except Exception:
        error = traceback.format_exc(limit=8)

    # Collect everything the notebook wrote under the temp root.
    members = {}
    if temp_root.exists():
        for p in sorted(temp_root.rglob("*")):
            if p.is_file():
                rel = p.relative_to(temp_root).as_posix()
                if rel.endswith("submission.zip"):
                    continue
                # Notebooks that build under `<work>/submission/` zip that directory as
                # the archive root, so strip the leading component.
                parts = rel.split("/")
                if len(parts) > 1 and parts[0] == "submission":
                    rel = "/".join(parts[1:])
                try:
                    members[rel] = p.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    members[rel] = f"<binary {p.stat().st_size} bytes>"
    return {"error": error, "members": members, "log": g.get("_stdout_tail")}


def main() -> int:
    names = sys.argv[1:]
    for name in names:
        d = PULLED / name
        if not d.is_dir():
            print(f"skip {name}: not pulled")
            continue
        temp_root = Path(tempfile.mkdtemp(prefix="nbexec_"))
        try:
            res = run_kernel(d, temp_root)
        finally:
            pass
        outdir = OUT / name
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "meta.json").write_text(
            json.dumps(
                {
                    "kernel": name,
                    "method": "sandbox_exec",
                    "error": res["error"],
                    "members": sorted(res["members"]),
                    "member_count": len(res["members"]),
                    "total_bytes": sum(len(v) for v in res["members"].values()),
                    "temp_root": str(temp_root),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        for rel, text in res["members"].items():
            p = outdir / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8", newline="")
        print(f"{name}: {len(res['members'])} members, error={bool(res['error'])}")
        if res["error"]:
            print(res["error"][-800:])
        shutil.rmtree(temp_root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Compute the census-style files_sha256 for our scored bundles and match to census groups.

The census defines files_sha256 = sha256(json.dumps(FILES, sort_keys=True)) where FILES maps
archive path -> file text. For our bundles the authoritative bytes are the ones inside the
scored submission.zip, so read them from the archive rather than from a working copy.
"""
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent

CANDIDATES = {
    "exp05 scored artifact": REPO / "ckpt" / "exp05" / "submission.zip",
    "exp05 bundle copy": REPO / "ckpt" / "bundles" / "exp05_patch_integrity",
    "exp03 bundle copy": REPO / "ckpt" / "bundles" / "exp03_baseline" if (REPO / "ckpt" / "bundles" / "exp03_baseline").exists() else REPO / "bundles" / "exp05_patch_integrity",
    "exp13_swe_toolkit": REPO / "ckpt" / "bundles" / "exp13_swe_toolkit",
    "exp14_lean_toolkit": REPO / "bundles" / "exp14_lean_toolkit",
    "exp_breakthrough": REPO / "bundles" / "exp_breakthrough",
}

# census groups
rows = list(csv.DictReader((ROOT / "datasets" / "public_config_draws.csv").open(encoding="utf-8")))
groups = {}
for r in rows:
    if r.get("files_sha256"):
        groups.setdefault(r["files_sha256"], []).append(r)


def files_from_zip(path: Path):
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n).decode("utf-8") for n in z.namelist() if not n.endswith("/")}


def files_from_dir(path: Path):
    return {p.relative_to(path).as_posix(): p.read_text(encoding="utf-8") for p in sorted(path.rglob("*")) if p.is_file()}


def h(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:12]


for label, path in CANDIDATES.items():
    if not path.exists():
        print(f"{label:<24} MISSING {path}")
        continue
    try:
        files = files_from_zip(path) if path.is_file() else files_from_dir(path)
    except Exception as e:  # noqa: BLE001
        print(f"{label:<24} ERROR {e}")
        continue
    digest = h(files)
    match = groups.get(digest)
    if match:
        scores = sorted({float(x["public_score"]) for x in match})
        tasks = sum(int(x["tasks_of_58"] or 0) for x in match)
        refs = sorted({x["notebook_ref"] for x in match})
        print(
            f"{label:<24} {digest}  MATCH n={len(match)} draws tasks={tasks} "
            f"mean={tasks/len(match)/58:.3f} distinct={scores} refs={len(refs)}"
        )
        for ref in refs[:6]:
            print(f"{'':<26} {ref}")
    else:
        print(f"{label:<24} {digest}  no census match (members={len(files)})")

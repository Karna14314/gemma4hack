"""Build the deterministic submission.zip for a bundle and print its sha256 + members."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from notebook_lib import validator  # noqa: E402


def collect(bundle: Path) -> dict:
    """Collect bundle members, skipping interpreter caches.

    A benchmark or verifier that imports the bundle's engine writes
    ``__pycache__/*.pyc`` into it. ``.pyc`` is not an allowed submission extension,
    so those files must never reach the archive.
    """
    files = {}
    for p in sorted(bundle.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(bundle).as_posix()
        if "__pycache__" in rel.split("/") or p.suffix == ".pyc":
            continue
        files[rel] = p.read_text(encoding="utf-8")
    return files


def main() -> int:
    bundle = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    files = collect(bundle)
    payload = validator.pack(files)
    digest = hashlib.sha256(payload).hexdigest()
    print(f"bundle      : {bundle}")
    print(f"members     : {len(files)}")
    print(f"unpacked    : {sum(len(v) for v in files.values())} bytes")
    print(f"zip bytes   : {len(payload)}")
    print(f"zip sha256  : {digest}")
    print(f"pack digest : {validator.digest(payload)[:16]}")
    for name in sorted(files):
        print(f"  {len(files[name]):>7}  {name}")
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(payload)
        print(f"wrote       : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

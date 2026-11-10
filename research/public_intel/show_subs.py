"""Fetch and print the live competition submission queue.

Usage:
    python research/public_intel/show_subs.py            # fetch live
    python research/public_intel/show_subs.py FILE       # parse a saved JSON file
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def parse(raw: bytes):
    print("first bytes:", raw[:6], "len:", len(raw))
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            # strict=False: a submission description may contain a literal newline.
            return json.loads(raw.decode(enc), strict=False), enc
        except Exception as e:  # noqa: BLE001
            print(enc, "fail:", str(e)[:90])
    return None, None


def report(d, enc):
    print("decoded with:", enc, "| n =", len(d))
    print(f"{'ref':<10} {'date':<22} {'status':<10} {'pub':<6} {'priv':<6} description / error")
    for x in d:
        print(
            f"{x.get('ref'):<10} {x.get('date',''):<22} {x.get('status',''):<10} "
            f"{str(x.get('publicScore') or ''):<6} {str(x.get('privateScore') or ''):<6} "
            f"{(x.get('description') or '')[:90]}"
        )
        if x.get("errorDescription"):
            print(f"           ERROR: {x['errorDescription'][:300]}")
        if x.get("fileName"):
            print(f"           file: {x['fileName']}  bytes={x.get('totalBytes')}")


def main() -> int:
    if len(sys.argv) > 1:
        d, enc = parse(Path(sys.argv[1]).read_bytes())
    else:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "kaggle_rest.py"), "submissions", "gemma-4-developer-agent"],
            capture_output=True,
            cwd=ROOT,
        )
        if proc.returncode != 0:
            print("kaggle_rest failed:", proc.stderr.decode("utf-8", "replace")[:500])
            return 1
        d, enc = parse(proc.stdout)
    if d is None:
        return 1
    report(d, enc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

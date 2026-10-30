import os
import sys
from pathlib import Path

def find_swe():
    # Prefer sibling
    here = Path(__file__).resolve().parent
    candidate = here / "swe.py"
    if candidate.is_file():
        return candidate
    # Search common roots
    for root in ("/workspace", os.getcwd(), "/"):
        for p in Path(root).rglob("swe.py"):
            if p.name == "swe.py":
                return p
    # fallback find
    import subprocess
    try:
        out = subprocess.run(["find", "/", "-name", "swe.py"], capture_output=True, text=True, timeout=30)
        for line in out.stdout.splitlines():
            p = Path(line.strip())
            if p.is_file():
                return p
    except Exception:
        pass
    return None

if __name__ == "__main__":
    p = find_swe()
    if p is None:
        print("STATUS: DEGRADED")
        print("swe.py not found")
        sys.exit(1)
    print("STATUS: OK")
    print(str(p))

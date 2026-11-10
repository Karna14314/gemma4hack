"""Fetch the raw submission queue and show the tail so a truncation can be diagnosed."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
proc = subprocess.run(
    [sys.executable, str(ROOT / "tools" / "kaggle_rest.py"), "submissions", "gemma-4-developer-agent"],
    capture_output=True,
    cwd=ROOT,
)
print("returncode:", proc.returncode)
print("stdout bytes:", len(proc.stdout))
print("stderr:", proc.stderr.decode("utf-8", "replace")[:300])
print("--- head 300 ---")
print(proc.stdout[:300].decode("utf-8", "replace"))
print("--- tail 400 ---")
print(proc.stdout[-400:].decode("utf-8", "replace"))

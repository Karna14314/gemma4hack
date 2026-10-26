#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
bundle = Path(__file__).resolve().parent / "bundles" / "exp11_e4b"
out = Path(__file__).resolve().parent / "kernel_e4b_submit" / "submission_notebook.ipynb"
r = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "tools" / "build_notebook.py"),
                    "--bundle", str(bundle), "--out", str(out)], capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode != 0:
    print(r.stderr.strip())
    sys.exit(1)
assert out.is_file()
print("E4B VERIFY_NOTEBOOK: ALL CHECKS PASSED")
sys.exit(0)

"""Section 10 — setup: standard-library imports and working-directory resolution.

Runs first as a code cell. Nothing here may raise, because every later cell
depends on it and an exception at this point would abort the whole notebook.
"""

SETUP = '''\
"""Standard-library setup for the submission builder.

Only stdlib plus PyYAML. No pip, no network, no dataset inputs.
"""
import hashlib
import io
import json
import os
import platform
import posixpath
import sys
import textwrap
import traceback
import zipfile
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - PyYAML ships with Kaggle notebooks
    yaml = None
    print("WARNING: PyYAML is unavailable; structural checks will be skipped.")


def _resolve_working() -> Path:
    """Find the directory the submission zip must be written to.

    Kaggle uses /kaggle/working. Off Kaggle (local verification) fall back to an
    override or a temporary directory, so the notebook is runnable anywhere.
    """
    for candidate in (
        os.environ.get("KAGGLE_WORKING_DIR"),
        "/kaggle/working",
        os.getcwd(),
    ):
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_dir() and os.access(path, os.W_OK):
            return path
    import tempfile

    path = Path(tempfile.mkdtemp(prefix="gemma4_submission_"))
    return path


WORKING = _resolve_working()

print(f"python           {sys.version.split()[0]} ({platform.platform()})")
print(f"working directory {WORKING}")
print(f"pyyaml            {'present' if yaml is not None else 'MISSING'}")
print(f"writable          {os.access(WORKING, os.W_OK)}")
'''

def cells() -> list[dict]:
    return [
        {"cell_type": "code", "source": SETUP},
    ]
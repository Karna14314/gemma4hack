"""Create the local harness environment and verify the current bundle.

This is the one-command cold-start path for a fresh clone:

    python tools/bootstrap.py
    python tools/bootstrap.py --notebook      # also build + execute the notebook

What it does, in order:

1. create ``.venv-harness`` on Python 3.12 (via ``uv`` when available, otherwise
   the current interpreter if it is >= 3.11);
2. install ``requirements.txt``;
3. download the three competition wheels from the Kaggle dataset
   ``metric/gemma-4-developer-agent-wheelhouse`` if they are not already in
   ``kaggle_work/gemma-4-developer-agent/research/wheelhouse``;
4. install those wheels with ``--no-deps``;
5. run ``tools/verify_bundle.py`` (and optionally build + execute the notebook).

The wheels are gitignored on purpose: they are competition artefacts, not
source. Re-running the script is safe and skips work that is already done.

Kaggle authentication is only needed for step 3. The Kaggle CLI accepts a
``KAGGLE_API_TOKEN`` bearer token (newer CLI) or a ``~/.kaggle/kaggle.json``
legacy key. If the wheels are already present, the script works fully offline.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv-harness"
WHEELHOUSE = (
    ROOT / "kaggle_work" / "gemma-4-developer-agent" / "research" / "wheelhouse"
)
WHEEL_DATASET = "metric/gemma-4-developer-agent-wheelhouse"
WHEELS = (
    "swegemma-0.2.11-py3-none-any.whl",
    "adk_submission-0.2.13-py3-none-any.whl",
    "adk_eval_core-0.1.0-py3-none-any.whl",
)
REQUIREMENTS = ROOT / "requirements.txt"


def venv_python() -> Path:
    """Return the interpreter inside ``.venv-harness`` for this platform."""
    layout = Path("Scripts") / "python.exe" if os.name == "nt" else Path("bin") / "python"
    return VENV / layout


def run(command: list[str], *, quiet: bool = False) -> None:
    """Run a command, streaming output, and fail loudly on a non-zero exit."""
    shown = " ".join(str(part) for part in command)
    print(f"+ {shown}", flush=True)
    result = subprocess.run(
        [str(part) for part in command],
        cwd=ROOT,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"command failed with exit code {result.returncode}: {shown}")
    if quiet:
        return


def find_uv() -> str | None:
    return shutil.which("uv")


def ensure_venv(force: bool) -> Path:
    if force and VENV.exists():
        print(f"removing {VENV}")
        shutil.rmtree(VENV)
    python = venv_python()
    if python.is_file():
        print(f"using existing venv: {python}")
        return python

    uv = find_uv()
    if uv:
        run([uv, "venv", "--python", "3.12", str(VENV)])
    else:
        if sys.version_info < (3, 11):
            raise SystemExit(
                "adk_eval_core requires Python >= 3.11; install uv or Python 3.12 "
                "and re-run this script"
            )
        run([sys.executable, "-m", "venv", str(VENV)])

    if not python.is_file():
        raise SystemExit(f"venv creation did not produce {python}")
    return python


def install_requirements(python: Path) -> None:
    uv = find_uv()
    if uv:
        run([uv, "pip", "install", "--python", str(python), "-q", "-r", str(REQUIREMENTS)])
    else:
        run([str(python), "-m", "pip", "install", "-q", "--upgrade", "pip"])
        run([str(python), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)])


def download_wheels() -> list[Path]:
    WHEELHOUSE.mkdir(parents=True, exist_ok=True)
    missing = [name for name in WHEELS if not (WHEELHOUSE / name).is_file()]
    if not missing:
        print(f"wheels already present in {WHEELHOUSE}")
        return [WHEELHOUSE / name for name in WHEELS]

    kaggle = shutil.which("kaggle")
    if not kaggle:
        raise SystemExit(
            "missing competition wheels and no `kaggle` CLI on PATH.\n"
            f"Download these files from {WHEEL_DATASET} into {WHEELHOUSE}:\n  "
            + "\n  ".join(missing)
        )

    for name in missing:
        run(
            [
                kaggle,
                "datasets",
                "download",
                "-d",
                WHEEL_DATASET,
                "-f",
                name,
                "-p",
                str(WHEELHOUSE),
                "--unzip",
                "-q",
            ]
        )
    absent = [name for name in WHEELS if not (WHEELHOUSE / name).is_file()]
    if absent:
        raise SystemExit(f"download finished but these wheels are still missing: {absent}")
    return [WHEELHOUSE / name for name in WHEELS]


def install_wheels(python: Path, wheels: list[Path]) -> None:
    uv = find_uv()
    if uv:
        run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(python),
                "-q",
                "--no-deps",
                *[str(path) for path in wheels],
            ]
        )
    else:
        run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "-q",
                "--no-deps",
                *[str(path) for path in wheels],
            ]
        )


def verify(python: Path, notebook: bool) -> None:
    run([str(python), str(ROOT / "tools" / "verify_bundle.py")])
    if notebook:
        out = ROOT / "build" / "submission_notebook.ipynb"
        run([str(python), str(ROOT / "tools" / "build_notebook.py"), "--out", str(out)])
        run(
            [
                str(python),
                str(ROOT / "tools" / "verify_notebook.py"),
                "--notebook",
                str(out),
            ]
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="recreate .venv-harness")
    parser.add_argument(
        "--skip-wheels",
        action="store_true",
        help="do not download the competition wheels (offline mode)",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="install only; do not run verify_bundle.py",
    )
    parser.add_argument(
        "--notebook",
        action="store_true",
        help="also build and execute the submission notebook",
    )
    args = parser.parse_args()

    python = ensure_venv(args.force)
    install_requirements(python)

    if args.skip_wheels:
        wheels = [WHEELHOUSE / name for name in WHEELS]
        absent = [str(path) for path in wheels if not path.is_file()]
        if absent:
            raise SystemExit(f"--skip-wheels given but these are missing: {absent}")
    else:
        wheels = download_wheels()
    install_wheels(python, wheels)

    if not args.skip_verify:
        verify(python, args.notebook)

    print()
    print("=" * 70)
    print("bootstrap complete")
    print(f"  venv:      {python}")
    print(f"  wheelhouse:{WHEELHOUSE}")
    print()
    print("next:")
    print(f"  {python} tools/verify_bundle.py")
    print(f"  {python} tools/build_notebook.py")
    print(f"  {python} tools/verify_notebook.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

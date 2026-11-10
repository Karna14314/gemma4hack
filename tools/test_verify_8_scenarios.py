"""8-scenario torture test suite for _verify.py + skill leak auto-clean test."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_SCRIPTS = Path(os.environ.get("SWE_TEST_SCRIPTS") or (REPO_ROOT / "bundles" / "exp13_swe_toolkit" / "skills" / "swe-toolkit" / "scripts"))

# Importing a bundle's _verify writes __pycache__/*.pyc into the bundle. A .pyc is not an
# allowed submission extension, so the torture suite must not poison the artifact.
sys.dont_write_bytecode = True

sys.path.insert(0, str(BUNDLE_SCRIPTS))
import _verify


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


def make_repo(tmp: Path) -> Path:
    repo = tmp / "scratch"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "probe@example.com")
    git(repo, "config", "user.name", "probe")
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "pkg" / "core.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_core.py").write_text(
        "from pkg.core import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("# demo\n", encoding="utf-8")
    (repo / ".gitignore").write_text("*.log\nbuild/\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    return repo


SCENARIOS = {
    "1_no_changes": (
        lambda r: None,
        lambda out: "STATUS: FAIL" in out and "CHANGED: 0 files" in out,
    ),
    "2_changed_py": (
        lambda r: (r / "pkg" / "core.py").write_text("def add(a, b):\n    return a + b + 0\n", encoding="utf-8"),
        lambda out: "STATUS: OK" in out and "CHANGED: 1 file(s)" in out and "SYNTAX: OK" in out,
    ),
    "3_new_untracked_py": (
        lambda r: (r / "pkg" / "extra.py").write_text("X = 2\n", encoding="utf-8"),
        lambda out: "STATUS: OK" in out and "pkg/extra.py" in out.replace("\\", "/"),
    ),
    "4_new_ignored_py": (
        lambda r: ((r / "build").mkdir(exist_ok=True), (r / "build" / "gen.py").write_text("Y = 3\n", encoding="utf-8")),
        lambda out: "IGNORED:" in out and "build/gen.py" in out.replace("\\", "/"),
    ),
    "5_syntax_error_py": (
        lambda r: (r / "pkg" / "core.py").write_text("def add(a, b):\n    return a +\n", encoding="utf-8"),
        lambda out: "STATUS: FAIL" in out and "SYNTAX: FAIL" in out,
    ),
    "6_filename_with_spaces": (
        lambda r: (r / "pkg" / "my module.py").write_text("Z = 4\n", encoding="utf-8"),
        lambda out: "STATUS: OK" in out and "my module.py" in out,
    ),
    "7_zero_py_changes": (
        lambda r: (r / "README.md").write_text("# demo changed\n", encoding="utf-8"),
        lambda out: "STATUS: OK" in out and "README.md" in out,
    ),
    "8_only_test_and_config": (
        lambda r: (
            (r / "tests" / "test_core.py").write_text("def test_noop():\n    assert True\n", encoding="utf-8"),
            (r / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8"),
        ),
        lambda out: "STATUS: FAIL" in out and "PROTECTED: FAIL" in out,
    ),
    "9_materialized_skill_leak": (
        lambda r: (
            (r / "skills" / "swe-toolkit" / "scripts").mkdir(parents=True, exist_ok=True),
            (r / "skills" / "swe-toolkit" / "scripts" / "swe.py").write_text("# leak test\n", encoding="utf-8"),
            (r / "pkg" / "core.py").write_text("def add(a, b):\n    return a + b + 1\n", encoding="utf-8"),
        ),
        lambda out: (
            "STATUS: FAIL" in out
            and "STRAY" in out
            and "skills/swe-toolkit" in out
            and "core.py" in out
        ),
    ),
}


def main():
    print("Running 9 adversarial torture scenarios on _verify.py...")
    passed = 0
    total = len(SCENARIOS)

    for name, (setup_fn, verify_fn) in SCENARIOS.items():
        with tempfile.TemporaryDirectory() as td:
            repo = make_repo(Path(td))
            setup_fn(repo)
            result = _verify.verify(root=str(repo))
            ok = verify_fn(result)
            status = "PASS" if ok else "FAIL"
            print(f"[{status}] {name}")
            if not ok:
                print("--- Output was: ---")
                print(result)
                print("-------------------")
            else:
                passed += 1

    print(f"\nResult: {passed}/{total} scenarios passed.")
    if passed != total:
        return 1
    print("ALL ADVERSARIAL TORTURE TESTS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

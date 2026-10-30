import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROTECTED = {"conftest.py", "pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini"}


def _root(root=None):
    if root is None:
        root = os.environ.get("SWE_ROOT") or "/workspace"
    return str(root)


def _run_git(args, root):
    try:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True,
        )
    except Exception as e:
        return None


def git_diff_names(root=None):
    root = _root(root)
    out = _run_git(["diff", "--name-only", "_swegemma_baseline"], root)
    if out is None or out.returncode != 0:
        out = _run_git(["diff", "--name-only", "HEAD"], root)
    if out is None:
        return []
    return [l.strip() for l in out.stdout.splitlines() if l.strip()]


def git_diff(root=None):
    root = _root(root)
    out = _run_git(["diff", "_swegemma_baseline"], root)
    if out is None or out.returncode != 0:
        out = _run_git(["diff", "HEAD"], root)
    if out is None:
        return ""
    return out.stdout


def ignored_new_files(root=None):
    root = _root(root)
    out = _run_git(["status", "--porcelain"], root)
    if out is None:
        return []
    res = []
    for line in out.stdout.splitlines():
        if line.startswith("??"):
            res.append(line[3:].strip())
    ignored = []
    for p in res:
        r = _run_git(["check-ignore", p], root)
        if r is not None and r.returncode == 0:
            ignored.append(p)
    return ignored


def syntax_check(files, root=None):
    root = _root(root)
    errors = []
    import ast
    for f in files:
        if not f.endswith(".py"):
            continue
        path = Path(root) / f
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            ast.parse(text)
            compile(text, str(path), "exec")
        except Exception as e:
            errors.append("{}: {}: {}".format(f, type(e).__name__, e))
    return errors


def touched_protected(files):
    out = []
    for f in files:
        name = Path(f).name
        if name in PROTECTED:
            out.append(f)
        if name.startswith("test_") or name.endswith("_test.py"):
            out.append(f)
        if "/tests/" in f or f.startswith("tests/") or f.startswith("test/"):
            out.append(f)
    return sorted(set(out))


def verify(test_expr=None, root=None):
    root = _root(root)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    lines = []
    files = git_diff_names(root)
    lines.append("FILES CHANGED: {}".format(len(files)))
    if not files:
        lines.append("WARNING: empty diff")
    prot = touched_protected(files)
    if prot:
        lines.append("PROTECTED TOUCHED: " + ", ".join(prot))
    ignored = ignored_new_files(root)
    if ignored:
        for p in ignored:
            lines.append("IGNORED NEW FILE: {} -> run: git add -N -f {}".format(p, p))
    errs = syntax_check(files, root)
    if errs:
        lines.append("SYNTAX ERRORS:")
        for e in errs:
            lines.append("  " + e)
    else:
        lines.append("SYNTAX: OK")
    if test_expr:
        args = test_expr.split() if isinstance(test_expr, str) else list(test_expr)
        import shutil
        if shutil.which("pytest"):
            cmd = ["pytest", *args, "-q", "--tb=short", "-p", "no:cacheprovider",
                   "--junitxml=/tmp/swe_junit.xml"]
        else:
            cmd = [sys.executable, "-m", "pytest", *args, "-q", "--tb=short",
                   "-p", "no:cacheprovider", "--junitxml=/tmp/swe_junit.xml"]
        try:
            r = subprocess.run(
                cmd, cwd=root, capture_output=True, text=True, timeout=150,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            lines.append("PYTEST EXIT: {}".format(r.returncode))
            try:
                tree = ET.parse("/tmp/swe_junit.xml")
                rootx = tree.getroot()
                fails = 0
                errors = 0
                passed = 0
                for tc in rootx.iter("testcase"):
                    if tc.find("failure") is not None:
                        fails += 1
                    elif tc.find("error") is not None:
                        errors += 1
                    else:
                        passed += 1
                lines.append("JUNIT: passed={} failures={} errors={}".format(passed, fails, errors))
            except Exception as e:
                lines.append("JUNIT PARSE: {}".format(e))
            tail = (r.stdout + "\n" + r.stderr).splitlines()
            lines.append("OUTPUT TAIL:")
            for l in tail[-20:]:
                lines.append(l)
        except subprocess.TimeoutExpired:
            lines.append("PYTEST: TIMEOUT (150s)")
    return "\n".join(lines)

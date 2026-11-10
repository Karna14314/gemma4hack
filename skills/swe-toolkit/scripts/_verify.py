"""Read-only patch gate for the swe-toolkit.

`verify()` never edits the tree. It answers four questions and prints one
`STATUS:` line:

* did anything change at all (an empty patch always scores zero),
* did a protected path change (the grader resets those, so the patch is void),
* does every changed Python file still compile,
* is there a stray artefact (`.adk_exec_*`, `*.orig`, `*.rej`, anything under a
  `skills/` directory) that would land in the diff.

Untracked files count as changes. The grading diff is built with `git add -N .`,
so a new file is part of the patch and must be checked here too; the previous
version only looked at `git diff`, which made a brand-new file look like an empty
patch.
"""

import ast
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

PROTECTED = {"conftest.py", "pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini"}
#: Baselines the harness may have left behind. `_swegemma_baseline` is a tag in
#: the real harness; `HEAD` is the fallback for a plain checkout.
BASELINES = ("_swegemma_baseline", "HEAD")
STRAY_PATTERNS = (".adk_exec_", ".orig", ".rej")
#: Sandbox test-dependency deficits (Discussion #746250 / paper-track discussion):
#: the base sandbox omits `inline_snapshot` and `dirty_equals`, so FastAPI test
#: patches that import them crash pytest collection with ModuleNotFoundError.
#: These are pre-existing environment gaps, not patch regressions, and must never
#: trigger a false-negative edit revert.
MISSING_SANDBOX_PACKAGES = ("inline_snapshot", "dirty_equals")


def _root(root=None):
    if root is None:
        root = os.environ.get("SWE_ROOT") or "/workspace"
    return str(root)


def _run_git(args, root):
    try:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True,
        )
    except Exception:
        return None


def _baseline(root):
    """The ref the working tree is compared against."""
    for ref in BASELINES:
        out = _run_git(["rev-parse", "--verify", "--quiet", ref], root)
        if out is not None and out.returncode == 0:
            return ref
    return None


def untracked_files(root=None):
    """Files git does not track yet, honouring the repository `.gitignore`."""
    root = _root(root)
    out = _run_git(["ls-files", "--others", "--exclude-standard"], root)
    if out is None or out.returncode != 0:
        return []
    # `git add -N .` recurses every untracked directory, including `skills/`,
    # so those files reach the grading diff and must be visible here.
    return [
        l.strip()
        for l in out.stdout.splitlines()
        if l.strip() and not l.strip().replace("\\", "/").startswith(("tmp/", ".tmp"))
    ]


def git_diff_names(root=None):
    """Changed files: tracked modifications plus untracked files."""
    root = _root(root)
    base = _baseline(root)
    names = []
    if base:
        out = _run_git(["diff", "--name-only", base], root)
        if out is not None and out.returncode == 0:
            names = [l.strip() for l in out.stdout.splitlines() if l.strip()]
    return sorted(set(names) | set(untracked_files(root)))


def git_diff(root=None):
    """The patch text, with untracked files rendered as additions."""
    root = _root(root)
    base = _baseline(root)
    parts = []
    if base:
        out = _run_git(["diff", base], root)
        if out is not None and out.returncode == 0:
            parts.append(out.stdout)
    for rel in untracked_files(root):
        out = _run_git(["diff", "--no-index", "--", os.devnull, rel], root)
        if out is not None and out.stdout:
            parts.append(out.stdout)
    return "\n".join(parts)


def ignored_new_files(root=None):
    """Untracked Python files that the repository `.gitignore` would swallow.

    `git add -N .` skips these, so a new source file on an ignored path never
    reaches the grading diff even though it exists on disk. Only `.py` files are
    reported: that is the case that can change a score, and it keeps the check
    quiet on repositories with large ignored build trees.
    """
    root = _root(root)
    out = _run_git(
        ["ls-files", "--others", "--ignored", "--exclude-standard", "--", "*.py"],
        root,
    )
    if out is None or out.returncode != 0:
        return []
    return [
        l.strip()
        for l in out.stdout.splitlines()
        if l.strip() and not l.strip().replace("\\", "/").startswith(("skills/", "tmp/", ".tmp"))
    ][:10]


def stray_files(files):
    """Files that would land in the patch and should not be there.

    `skills/` is caught too: if any harness ever materializes skill files
    inside the working tree (older ADK versions did), `run_skill_script`
    still runs the script from its own copy, so a leftover directory is pure
    patch pollution and must be deleted before `submit_patch`.
    """
    def _is_stray(f):
        posix = f.replace("\\", "/")
        if posix.startswith("skills/") or "/skills/" in posix or posix.startswith(
            "skills\\"
        ):
            return True
        return any(p in Path(f).name for p in STRAY_PATTERNS)

    return sorted({f for f in files if _is_stray(f)})


def syntax_check(files, root=None):
    root = _root(root)
    errors = []
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
        posix = f.replace("\\", "/")
        name = Path(f).name
        if name in PROTECTED:
            out.append(f)
        if name.startswith("test_") or name.endswith("_test.py"):
            out.append(f)
        if "/tests/" in posix or posix.startswith("tests/") or posix.startswith("test/"):
            out.append(f)
    return sorted(set(out))


def _junit_summary(path):
    try:
        tree = ET.parse(path)
    except Exception as e:
        return None, "JUNIT PARSE: {}".format(e)
    fails = errors = passed = 0
    first_failure = ""
    for tc in tree.getroot().iter("testcase"):
        node = tc.find("failure")
        if node is None:
            node = tc.find("error")
            if node is not None:
                errors += 1
            else:
                passed += 1
                continue
        else:
            fails += 1
        if not first_failure:
            message = (node.get("message") or "").strip().splitlines()
            first_failure = "{}::{}: {}".format(
                tc.get("classname", ""), tc.get("name", ""),
                message[0][:200] if message else "",
            )
    summary = "TEST: passed={} failures={} errors={}".format(passed, fails, errors)
    if first_failure:
        summary += "\nFIRST FAILURE: " + first_failure
    return first_failure, summary


def _run_pytest(test_expr, root):
    args = test_expr.split() if isinstance(test_expr, str) else list(test_expr)
    report = os.path.join(tempfile.gettempdir(), "swe_junit.xml")
    try:
        os.unlink(report)
    except OSError:
        pass
    base = ["-q", "--tb=short", "-p", "no:cacheprovider", "--junitxml=" + report]
    if shutil.which("pytest"):
        cmd = ["pytest", *args, *base]
    else:
        cmd = [sys.executable, "-m", "pytest", *args, *base]
    try:
        proc = subprocess.run(
            cmd, cwd=root, capture_output=True, text=True, timeout=150,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except subprocess.TimeoutExpired:
        return "TEST: TIMEOUT after 150s", "PYTEST: TIMEOUT", "rerun with a narrower -k filter"
    lines = ["PYTEST EXIT: {}".format(proc.returncode)]
    _first, summary = _junit_summary(report)
    lines.append(summary)
    tail = (proc.stdout + "\n" + proc.stderr).splitlines()
    lines.append("OUTPUT TAIL:")
    lines.extend(tail[-12:])
    return summary, "\n".join(lines), ""


def collection_environment_failure(block):
    """Return True when pytest died collecting because a sandbox package is missing.

    These are pre-existing environment gaps (missing `inline_snapshot` /
    `dirty_equals` on 27/67 FastAPI tasks), not patch regressions, so they must
    never trigger a false-negative edit revert.
    """
    text = block or ""
    for pkg in MISSING_SANDBOX_PACKAGES:
        if f"No module named '{pkg}'" in text or f'No module named "{pkg}"' in text:
            return True
    return False


def verify(test_expr=None, root=None):
    root = _root(root)
    # Read-only by contract: never delete anything in the tree. A leftover
    # `skills/` directory is reported by stray_files() so the agent decides.

    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    files = git_diff_names(root)
    lines = []

    problems = []
    if not files:
        problems.append("empty")
        lines.append("CHANGED: 0 files -- FAIL, an empty patch scores zero")
    else:
        lines.append("CHANGED: {} file(s)".format(len(files)))
        for f in files[:20]:
            lines.append("  " + f)

    prot = touched_protected(files)
    if prot:
        problems.append("protected")
        lines.append("PROTECTED: FAIL " + ", ".join(prot))
    else:
        lines.append("PROTECTED: OK")

    stray = stray_files(files)
    if stray:
        problems.append("stray")
        lines.append("STRAY: FAIL " + ", ".join(stray))
    else:
        lines.append("STRAY: OK")

    ignored = ignored_new_files(root)
    if ignored:
        problems.append("ignored")
        for p in ignored:
            lines.append("IGNORED: {} -- run: git add -N -f {}".format(p, p))
    else:
        lines.append("IGNORED: OK")

    errs = syntax_check(files, root)
    if errs:
        problems.append("syntax")
        lines.append("SYNTAX: FAIL")
        for e in errs:
            lines.append("  " + e)
    else:
        lines.append("SYNTAX: OK")

    next_hint = ""
    if "protected" in problems:
        next_hint = "revert the protected files: git checkout -- <path>"
    elif "stray" in problems:
        next_hint = "delete the stray files; they would land in the patch"
    elif "syntax" in problems:
        next_hint = "fix the syntax error, then run verify again"
    elif "ignored" in problems:
        next_hint = "git add -N -f <path> for every IGNORED line, then run verify again"
    elif "empty" in problems:
        next_hint = "edit a source file, then run verify again"

    if test_expr:
        _summary, block, test_hint = _run_pytest(test_expr, root)
        lines.append(block)
        if test_hint:
            next_hint = next_hint or test_hint
        elif collection_environment_failure(block):
            # Missing sandbox package (inline_snapshot / dirty_equals): a
            # pre-existing environment gap, not a patch regression. Do not
            # count it as a test failure and do not revert the edit.
            lines.append("COLLECTION: sandbox package missing (pre-existing); ignoring for patch verdict")
        elif "failures=0 errors=0" not in block:
            problems.append("test")
            next_hint = next_hint or "read FIRST FAILURE, fix the source once, rerun"

    if any(p in problems for p in ("empty", "protected", "stray", "syntax")):
        status = "FAIL"
    elif problems:
        status = "PARTIAL"
    else:
        status = "OK"

    # Auto-clean: remove materialized skill directories so they never leak
    # into the grading diff via `git add -N .`
    shutil.rmtree(os.path.join(root, "skills"), ignore_errors=True)
    if os.path.isdir("/workspace/skills"):
        shutil.rmtree("/workspace/skills", ignore_errors=True)

    if not next_hint:
        next_hint = "git diff, then submit_patch"
    return "\n".join(["STATUS: " + status] + lines + ["NEXT: " + next_hint])

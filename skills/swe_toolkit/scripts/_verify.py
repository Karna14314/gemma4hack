import os, subprocess, sys, xml.etree.ElementTree as ET, re, pathlib
from pathlib import Path

PROTECTED = {"conftest.py","pyproject.toml","pytest.ini","setup.cfg","tox.ini"}

def git_diff_names():
    try:
        out=subprocess.run(["git","diff","--name-only","_swegemma_baseline"],capture_output=True,text=True,cwd="/workspace")
        if out.returncode!=0:
            out=subprocess.run(["git","diff","--name-only","HEAD"],capture_output=True,text=True,cwd="/workspace")
        return [l.strip() for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return []

def git_diff():
    try:
        out=subprocess.run(["git","diff","_swegemma_baseline"],capture_output=True,text=True,cwd="/workspace")
        if out.returncode!=0:
            out=subprocess.run(["git","diff","HEAD"],capture_output=True,text=True,cwd="/workspace")
        return out.stdout
    except Exception as e:
        return f"git diff error: {e}"

def ignored_new_files():
    # find untracked files
    try:
        out=subprocess.run(["git","status","--porcelain"],capture_output=True,text=True,cwd="/workspace")
    except Exception:
        return []
    res=[]
    for line in out.stdout.splitlines():
        if line.startswith("??"):
            p=line[3:].strip()
            res.append(p)
    # check ignored
    ignored=[]
    for p in res:
        r=subprocess.run(["git","check-ignore",p],capture_output=True,text=True,cwd="/workspace")
        if r.returncode==0:
            ignored.append(p)
    return ignored

def syntax_check(files):
    errors=[]
    for f in files:
        if not f.endswith(".py"): continue
        path=Path("/workspace")/f
        if not path.is_file(): continue
        try:
            text=path.read_text(encoding="utf-8", errors="replace")
            ast_mod=__import__("ast")
            ast_mod.parse(text)
            compile(text, str(path), "exec")
        except Exception as e:
            errors.append(f"{f}: {type(e).__name__}: {e}")
    return errors

def touched_protected(files):
    out=[]
    for f in files:
        name=Path(f).name
        if name in PROTECTED: out.append(f)
        if name.startswith("test_") or name.endswith("_test.py"): out.append(f)
        if "/tests/" in f or f.startswith("tests/"): out.append(f)
    return sorted(set(out))

def leftover_scratch(files):
    # any new file not .py/.md etc? simple: files in root not tracked
    return []

def verify(test_expr=None):
    lines=[]
    os.environ["PYTHONDONTWRITEBYTECODE"]="1"
    files=git_diff_names()
    lines.append(f"FILES CHANGED: {len(files)}")
    if not files:
        lines.append("WARNING: empty diff")
    prot=touched_protected(files)
    if prot:
        lines.append("PROTECTED TOUCHED: " + ", ".join(prot))
    ignored=ignored_new_files()
    if ignored:
        for p in ignored:
            lines.append(f"IGNORED NEW FILE: {p} -> run: git add -N -f {p}")
    errs=syntax_check(files)
    if errs:
        lines.append("SYNTAX ERRORS:")
        for e in errs: lines.append("  "+e)
    else:
        lines.append("SYNTAX: OK")
    # test run
    if test_expr:
        cmd=["python","-m","pytest",*test_expr.split(), "-q","--tb=short","-p","no:cacheprovider","--junitxml=/tmp/swe_junit.xml"]
        try:
            r=subprocess.run(cmd, cwd="/workspace", capture_output=True, text=True, timeout=150, env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
            lines.append(f"PYTEST EXIT: {r.returncode}")
            # parse junit
            try:
                tree=ET.parse("/tmp/swe_junit.xml")
                root=tree.getroot()
                fails=0; errors=0; passed=0
                for tc in root.iter("testcase"):
                    if tc.find("failure") is not None: fails+=1
                    elif tc.find("error") is not None: errors+=1
                    else: passed+=1
                lines.append(f"JUNIT: passed={passed} failures={fails} errors={errors}")
            except Exception as e:
                lines.append(f"JUNIT PARSE: {e}")
            tail=(r.stdout+"\n"+r.stderr).splitlines()
            lines.append("OUTPUT TAIL:")
            for l in tail[-20:]:
                lines.append(l)
        except subprocess.TimeoutExpired:
            lines.append("PYTEST: TIMEOUT (150s)")
    return "\n".join(lines)

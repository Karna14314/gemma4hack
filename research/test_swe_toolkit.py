import os, subprocess, tempfile, pathlib, time

SWE="skills/swe-toolkit/scripts/swe.py"

def run(root, *args):
    cmd=["python3", SWE, *args, "--root", str(root)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=200)

def test_empty_repo():
    d=tempfile.mkdtemp()
    r=run(d,"locate","--query","foo")
    assert r.returncode==0
    print("empty repo OK")

def test_missing_baseline():
    d=tempfile.mkdtemp()
    (pathlib.Path(d)/"a.py").write_text("def f():\n    return 1\n")
    r=run(d,"verify")
    assert r.returncode==0
    print("missing baseline OK")

def test_non_utf8():
    d=tempfile.mkdtemp()
    (pathlib.Path(d)/"b.py").write_bytes(b"def f():\n    return '\xff'\n")
    r=run(d,"locate","--query","f")
    assert r.returncode==0
    print("non-utf8 OK")

def test_syntax_error():
    d=tempfile.mkdtemp()
    (pathlib.Path(d)/"c.py").write_text("def f(\n")
    r=run(d,"locate","--query","f")
    assert r.returncode==0
    print("syntax error OK")

def test_symlink_loop():
    d=tempfile.mkdtemp()
    sub=pathlib.Path(d)/"sub"
    sub.mkdir()
    (sub/"loop").symlink_to(d)
    (sub/"x.py").write_text("def f(): pass\n")
    r=run(d,"locate","--query","f")
    assert r.returncode==0
    print("symlink loop OK")

def test_large_file():
    d=tempfile.mkdtemp()
    (pathlib.Path(d)/"big.py").write_text("x=1\n"*200000)
    r=run(d,"locate","--query","x")
    assert r.returncode==0
    print("large file OK")

def test_gitignore_ignored():
    d=tempfile.mkdtemp()
    (pathlib.Path(d)/".gitignore").write_text("ignored.py\n")
    (pathlib.Path(d)/"ignored.py").write_text("def f(): pass\n")
    # init git
    subprocess.run(["git","init"],cwd=d,capture_output=True)
    subprocess.run(["git","add","-A"],cwd=d,capture_output=True)
    subprocess.run(["git","commit","-m","base"],cwd=d,capture_output=True)
    (pathlib.Path(d)/"ignored.py").write_text("def f(): return 2\n")
    r=run(d,"verify")
    assert r.returncode==0
    print("gitignore OK")

def test_hanging_pytest():
    d=tempfile.mkdtemp()
    (pathlib.Path(d)/"test_hang.py").write_text("import time\ndef test_hang():\n    time.sleep(1000)\n")
    subprocess.run(["git","init"],cwd=d,capture_output=True)
    subprocess.run(["git","add","-A"],cwd=d,capture_output=True)
    subprocess.run(["git","commit","-m","base"],cwd=d,capture_output=True)
    r=run(d,"verify","--test","test_hang.py")
    assert r.returncode==0
    print("hanging pytest OK")

if __name__=="__main__":
    for fn in [test_empty_repo,test_missing_baseline,test_non_utf8,test_syntax_error,test_symlink_loop,test_large_file,test_gitignore_ignored,test_hanging_pytest]:
        fn()
    print("ALL ADVERSARIAL TESTS PASSED")

import ast, os, re, sys, json, math
from pathlib import Path

SKIP_DIRS = {".git",".venv","venv","node_modules","build","dist","__pycache__"}
MAX_BYTES = 500*1024

def is_binary(path):
    try:
        with open(path,"rb") as f:
            chunk=f.read(8192)
        if b"\x00" in chunk:
            return True
        chunk.decode("utf-8")
        return False
    except Exception:
        return True

def walk(root):
    out=[]
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p=Path(dirpath)/fn
            try:
                if p.stat().st_size > MAX_BYTES:
                    continue
            except Exception:
                continue
            if is_binary(p):
                continue
            out.append(p)
    return out

def parse_ast(text):
    try:
        with warnings_suppress():
            return ast.parse(text)
    except Exception:
        return None

class _WS:
    def __enter__(self): 
        import warnings; self._w=warnings.catch_warnings(); self._w.__enter__(); warnings.simplefilter("ignore"); return self
    def __exit__(self,*a): self._w.__exit__(*a)

def warnings_suppress():
    return _WS()

def extract_symbols(text, filepath):
    syms=[]
    try:
        tree=ast.parse(text)
    except Exception:
        # regex fallback
        for m in re.finditer(r"^(?:async\s+)?def\s+([A-Za-z_]\w*)", text, re.M):
            syms.append({"qualname":m.group(1),"filepath":filepath,"start_line":None,"end_line":None,"signature":m.group(0),"decorators":[],"bases":[],"calls":[],"strings":[]})
        for m in re.finditer(r"^class\s+([A-Za-z_]\w*)", text, re.M):
            syms.append({"qualname":m.group(1),"filepath":filepath,"start_line":None,"end_line":None,"signature":m.group(0),"decorators":[],"bases":[],"calls":[],"strings":[]})
        return syms
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            calls=set()
            strings=set()
            for c in ast.walk(node):
                if isinstance(c,ast.Call):
                    if isinstance(c.func,ast.Name): calls.add(c.func.id)
                    elif isinstance(c.func,ast.Attribute): calls.add(c.func.attr)
                if isinstance(c,ast.Constant) and isinstance(c.value,str):
                    strings.add(c.value)
            decs=[]
            for d in getattr(node,"decorator_list",[]):
                if isinstance(d,ast.Name): decs.append(d.id)
                elif isinstance(d,ast.Attribute): decs.append(d.attr)
                elif isinstance(d,ast.Call):
                    if isinstance(d.func,ast.Name): decs.append(d.func.id)
                    elif isinstance(d.func,ast.Attribute): decs.append(d.func.attr)
            bases=[]
            for b in getattr(node,"bases",[]):
                if isinstance(b,ast.Name): bases.append(b.id)
                elif isinstance(b,ast.Attribute): bases.append(b.attr)
            sig=f"def {node.name}(...)" if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) else f"class {node.name}"
            syms.append({
                "qualname":node.name,
                "filepath":filepath,
                "start_line":getattr(node,"lineno",None),
                "end_line":getattr(node,"end_lineno",None),
                "signature":sig,
                "decorators":decs,
                "bases":bases,
                "calls":sorted(calls),
                "strings":sorted(strings),
            })
    return syms

def tokenize(s):
    return [t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", s)]

def score_candidate(sym, query_tokens, traceback_tokens):
    text = " ".join([sym["qualname"]]+sym.get("calls",[])+sym.get("strings",[])+sym.get("decorators",[])+sym.get("bases",[]))
    low = text.lower()
    score=0.0
    for t in query_tokens:
        if t in low:
            score+=1.0
    for t in traceback_tokens:
        if t in low:
            score+=2.0
    fp=sym["filepath"].replace("\\","/")
    if "/tests/" in fp or fp.startswith("tests/") or "test_" in Path(fp).name:
        score -= 1.5
    if "/docs/" in fp:
        score -= 1.0
    return score

def locate(root, query, top_n=5):
    files=walk(root)
    allsyms=[]
    for f in files:
        if f.suffix != ".py":
            continue
        try:
            text=f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel=str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        allsyms.extend(extract_symbols(text, rel))
    qtoks=tokenize(query)
    # traceback tokens: file:line suffixes
    ttoks=[]
    for m in re.finditer(r"([\w./-]+\.py):(\d+)", query):
        ttoks.append(m.group(1).split("/")[-1])
    ranked=sorted(allsyms, key=lambda s: score_candidate(s, qtoks, ttoks), reverse=True)
    # dedupe by file for top files
    files_ranked=[]
    seen=set()
    for s in ranked:
        if s["filepath"] not in seen:
            seen.add(s["filepath"]); files_ranked.append(s["filepath"])
    tests=[s for s in ranked if "/tests/" in s["filepath"] or s["filepath"].startswith("tests/") or "test_" in Path(s["filepath"]).name]
    return ranked[:top_n], files_ranked[:top_n], tests[:3]

def twins(root, symbol):
    files=walk(root)
    allsyms=[]
    for f in files:
        if f.suffix != ".py": continue
        try:
            text=f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel=str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        allsyms.extend(extract_symbols(text, rel))
    target=[s for s in allsyms if s["qualname"]==symbol]
    if not target:
        return []
    t=target[0]
    out=[]
    # callers
    for s in allsyms:
        if symbol in s.get("calls",[]):
            out.append(("caller", s))
    # subclass overrides: same qualname in classes with bases
    for s in allsyms:
        if s["qualname"]==symbol and s["filepath"]!=t["filepath"]:
            out.append(("override", s))
    # siblings sharing error strings
    tstr=set(t.get("strings",[]))
    for s in allsyms:
        if s is t: continue
        if tstr and tstr & set(s.get("strings",[])):
            out.append(("twin_string", s))
    return out

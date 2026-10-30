import ast
import math
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", ".venv", "venv", "env", ".env", "node_modules",
    "build", "dist", "__pycache__", ".tox", ".eggs", ".mypy_cache",
}
MAX_BYTES = 500 * 1024
STOPWORDS = {
    "the", "when", "with", "should", "error", "value", "return", "using",
    "does", "not", "from", "this", "that", "and", "for", "are", "was",
    "were", "has", "have", "had", "but", "can", "will", "into", "onto",
    "than", "then", "them", "they", "their", "there", "here", "what",
    "which", "who", "whom", "whose", "how", "why", "where", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "only",
    "own", "same", "too", "very", "just", "now", "also", "after", "before",
    "between", "through", "during", "without", "within", "about", "against",
    "above", "below", "to", "of", "in", "on", "at", "by", "as", "is", "it",
    "be", "or", "an", "a", "if", "so", "no", "up", "out", "off", "over",
    "under", "again", "further", "once", "because", "until", "while",
}


def is_binary(path):
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
        if b"\x00" in chunk:
            return True
        chunk.decode("utf-8")
        return False
    except Exception:
        return True


def walk(root):
    out = []
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if p.stat().st_size > MAX_BYTES:
                    continue
            except Exception:
                continue
            if is_binary(p):
                continue
            out.append(p)
    return out


def split_ident(tok):
    toks = set()
    for part in re.split(r"[_\.]", tok):
        if part:
            toks.add(part.lower())
    for m in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z])|[A-Z]+", tok):
        toks.add(m.lower())
    toks.add(tok.lower())
    return toks


def tokenize(s):
    base = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", s)
    out = set()
    for t in base:
        if t.lower() in STOPWORDS:
            continue
        out |= split_ident(t)
    return out


def extract_symbols(text, filepath):
    syms = []
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except Exception:
        for m in re.finditer(r"^(?:async\s+)?def\s+([A-Za-z_]\w*)", text, re.M):
            syms.append({
                "qualname": m.group(1), "filepath": filepath,
                "start_line": None, "end_line": None,
                "signature": m.group(0), "decorators": [], "bases": [],
                "calls": [], "strings": [], "body": "", "is_async": m.group(0).startswith("async"),
            })
        for m in re.finditer(r"^class\s+([A-Za-z_]\w*)", text, re.M):
            syms.append({
                "qualname": m.group(1), "filepath": filepath,
                "start_line": None, "end_line": None,
                "signature": m.group(0), "decorators": [], "bases": [],
                "calls": [], "strings": [], "body": "", "is_async": False,
            })
        return syms
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            calls = set()
            strings = set()
            for c in ast.walk(node):
                if isinstance(c, ast.Call):
                    if isinstance(c.func, ast.Name):
                        calls.add(c.func.id)
                    elif isinstance(c.func, ast.Attribute):
                        calls.add(c.func.attr)
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    strings.add(c.value)
            decs = []
            for d in getattr(node, "decorator_list", []):
                if isinstance(d, ast.Name):
                    decs.append(d.id)
                elif isinstance(d, ast.Attribute):
                    decs.append(d.attr)
                elif isinstance(d, ast.Call):
                    if isinstance(d.func, ast.Name):
                        decs.append(d.func.id)
                    elif isinstance(d.func, ast.Attribute):
                        decs.append(d.func.attr)
            bases = []
            for b in getattr(node, "bases", []):
                if isinstance(b, ast.Name):
                    bases.append(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.append(b.attr)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig = "def {}(...)" .format(node.name)
            else:
                sig = "class {}".format(node.name)
            sl = getattr(node, "lineno", None)
            el = getattr(node, "end_lineno", None)
            body = ""
            if sl and el:
                body = "\n".join(lines[sl - 1:el])
            syms.append({
                "qualname": node.name,
                "filepath": filepath,
                "start_line": sl,
                "end_line": el,
                "signature": sig,
                "decorators": decs,
                "bases": bases,
                "calls": sorted(calls),
                "strings": sorted(strings),
                "body": body,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            })
    return syms


def parse_query(query):
    trace_files = []
    trace_funcs = []
    for m in re.finditer(r'File "([^"]+)", line \d+, in ([A-Za-z_]\w*)', query):
        trace_files.append(m.group(1).split("/")[-1])
        trace_funcs.append(m.group(2))
    paths = re.findall(r"[A-Za-z0-9_./-]+\.py\b", query)
    modules = re.findall(r"\b[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)+\b", query)
    backticks = re.findall(r"`([^`]+)`", query)
    quotes = re.findall(r'"([^"]+)"', query)
    high_tokens = set()
    exact_syms = set()
    for s in backticks + quotes + paths + modules:
        high_tokens |= tokenize(s)
    for s in backticks + quotes:
        for t in re.findall(r"[A-Za-z_]\w*", s):
            exact_syms.add(t)
    general = tokenize(query)
    return {
        "trace_files": trace_files,
        "trace_funcs": trace_funcs,
        "paths": paths,
        "modules": modules,
        "high_tokens": high_tokens,
        "exact_syms": exact_syms,
        "general": general,
        "backticks": backticks,
    }


def score_candidate(sym, q, idf, N, avgdl, doc_tokens):
    score = 0.0
    fp = sym["filepath"].replace("\\", "/")
    for tf in q["trace_files"]:
        if fp.endswith(tf) or tf in fp:
            score += 40.0
    for tfn in q["trace_funcs"]:
        if sym["qualname"] == tfn or tfn in sym.get("calls", []):
            score += 40.0
    for p in q["paths"] + q["modules"]:
        stem = p.replace(".py", "").split("/")[-1].split(".")[-1]
        if stem and stem.lower() in fp.lower():
            score += 30.0
    for t in q["high_tokens"]:
        if t in doc_tokens:
            score += 4.0
    if sym["qualname"] in q["exact_syms"]:
        score += 80.0
    # BM25 over general tokens
    tf_counts = {}
    for t in doc_tokens:
        tf_counts[t] = tf_counts.get(t, 0) + 1
    dl = len(doc_tokens)
    for t in q["general"]:
        if t not in idf:
            continue
        tf = tf_counts.get(t, 0)
        if tf == 0:
            continue
        idf_t = idf[t]
        denom = tf + 1.5 * (1 - 0.75 + 0.75 * dl / avgdl) if avgdl > 0 else tf
        score += idf_t * (tf * (1.5 + 1)) / (denom if denom else 1)
    if "/tests/" in fp or fp.startswith("tests/") or "test_" in Path(fp).name:
        score -= 1.5
    if "/docs/" in fp:
        score -= 1.0
    return score


def locate(root, query, top_n=5):
    files = walk(root)
    allsyms = []
    for f in files:
        if f.suffix != ".py":
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        allsyms.extend(extract_symbols(text, rel))
    q = parse_query(query)
    docs = []
    for s in allsyms:
        dt = set()
        dt |= tokenize(s["qualname"])
        dt |= tokenize(" ".join(s.get("calls", [])))
        dt |= tokenize(" ".join(s.get("strings", [])))
        dt |= tokenize(" ".join(s.get("decorators", [])))
        dt |= tokenize(" ".join(s.get("bases", [])))
        dt |= tokenize(s["filepath"])
        dt |= tokenize(s.get("body", ""))
        docs.append(dt)
    N = len(docs)
    df = {}
    for dt in docs:
        for t in dt:
            df[t] = df.get(t, 0) + 1
    idf = {}
    if N:
        for t, d in df.items():
            idf[t] = math.log((N - d + 0.5) / (d + 0.5) + 1.0)
    avgdl = (sum(len(d) for d in docs) / N) if N else 1
    for s, dt in zip(allsyms, docs):
        s["_doc"] = dt
    for s in allsyms:
        s["_score"] = score_candidate(s, q, idf, N, avgdl, s["_doc"])

    # file-level aggregation
    file_scores = {}
    file_nodes = {}
    for s in allsyms:
        file_nodes.setdefault(s["filepath"], []).append(s["_score"])
    for fp, ns in file_nodes.items():
        ordered = sorted(ns, reverse=True)
        top = ordered[0] if ordered else 0.0
        rest = sum(ordered[1:4]) if len(ordered) > 1 else 0.0
        file_scores[fp] = top + 0.25 * rest

    ranked_files = sorted(file_scores, key=lambda f: file_scores[f], reverse=True)
    ranked_syms = sorted(allsyms, key=lambda s: s["_score"], reverse=True)

    tests = []
    tseen = set()
    for fp in ranked_files:
        if ("/tests/" in fp or fp.startswith("tests/") or "test_" in Path(fp).name):
            if fp not in tseen:
                tseen.add(fp)
                tests.append({"filepath": fp})
    if len(tests) < 3:
        for s in ranked_syms:
            fp = s["filepath"]
            if ("/tests/" in fp or fp.startswith("tests/") or "test_" in Path(fp).name):
                if fp not in tseen:
                    tseen.add(fp)
                    tests.append({"filepath": fp})
                    if len(tests) >= 3:
                        break

    return ranked_syms[:top_n], ranked_files[:top_n], tests[:3]


def _name_variants(name):
    variants = set()
    low = name.lower()
    variants.add(low)
    if low.startswith("async_"):
        variants.add(low[len("async_"):])
    if low.startswith("sync_"):
        variants.add(low[len("sync_"):])
    if low.startswith("aio_"):
        variants.add(low[len("aio_"):])
    if low.endswith("_async"):
        variants.add(low[:-len("_async")])
    if low.endswith("_sync"):
        variants.add(low[:-len("_sync")])
    return variants


def twins(root, symbol):
    files = walk(root)
    allsyms = []
    for f in files:
        if f.suffix != ".py":
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        allsyms.extend(extract_symbols(text, rel))
    targets = [s for s in allsyms if s["qualname"] == symbol]
    if not targets:
        # try case-insensitive
        targets = [s for s in allsyms if s["qualname"].lower() == symbol.lower()]
    if not targets:
        return []
    t = targets[0]
    out = []
    seen = set()
    def add(kind, s):
        key = (kind, s["filepath"], s.get("start_line"))
        if key in seen:
            return
        seen.add(key)
        out.append((kind, s))

    # direct AST callers
    for s in allsyms:
        if symbol in s.get("calls", []):
            add("caller", s)
    # subclass overrides: same qualname in another file
    for s in allsyms:
        if s["qualname"] == symbol and s["filepath"] != t["filepath"]:
            add("override", s)
    # classes that subclass a target class
    if t is not None:
        for s in allsyms:
            if isinstance(s, dict) and t["qualname"] in s.get("bases", []):
                add("subclass", s)
    # sync/async twins
    t_variants = _name_variants(symbol)
    for s in allsyms:
        if s is t:
            continue
        if _name_variants(s["qualname"]) & t_variants:
            if s["is_async"] != t["is_async"]:
                add("async_twin" if s["is_async"] else "sync_twin", s)
    # same qualname different asyncness
    for s in allsyms:
        if s["qualname"] == symbol and s["is_async"] != t["is_async"]:
            add("async_twin" if s["is_async"] else "sync_twin", s)
    # string-constant twins
    tstr = set(t.get("strings", []))
    if tstr:
        for s in allsyms:
            if s is t:
                continue
            if tstr & set(s.get("strings", [])):
                add("twin_string", s)
    return out

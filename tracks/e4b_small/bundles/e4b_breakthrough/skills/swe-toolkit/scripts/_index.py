import ast
import math
import os
import re
import sys
import time
from pathlib import Path

SKIP_DIRS = {
    ".git", ".venv", "venv", "env", ".env", "node_modules",
    "build", "dist", "__pycache__", ".tox", ".eggs", ".mypy_cache",
}
MAX_BYTES = 500 * 1024
#: Hard cap on files visited by one scan. The largest public repo (fastapi) has
#: ~1.3k Python files, so this only trips on a monorepo.
MAX_FILES = 4000
#: Default cooperative budget for `locate`, in seconds. `swe.py` sets a hard
#: watchdog above this so a partial ranking is always produced before the cut.
LOCATE_BUDGET_SECONDS = 20.0

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


def walk(root, deadline=None, max_files=None, only_py=True):
    """Collect candidate files under `root`.

    Only `.py` files are visited by default. The previous version probed every
    file in the tree for a NUL byte, which on fastapi meant 2,418 opens instead
    of 1,279 and dominated the cold-cache runtime. Python sources are decoded
    with `errors="replace"` later, so the binary probe buys nothing for them.

    `deadline` is a `time.monotonic()` value; `max_files` bounds the scan. Both
    make the caller return a partial list instead of hanging.
    """
    out = []
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if only_py and not fn.endswith(".py"):
                continue
            p = Path(dirpath) / fn
            try:
                if p.stat().st_size > MAX_BYTES:
                    continue
            except Exception:
                continue
            if not only_py and is_binary(p):
                continue
            out.append(p)
            if max_files is not None and len(out) >= max_files:
                return out
        if deadline is not None and time.monotonic() > deadline:
            break
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


def call_sites(query):
    """Extract call-site / attribute-access method names from an issue."""
    names = set()
    for m in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", query):
        names.add(m.group(1))
    for m in re.finditer(r"\.([A-Za-z_]\w*)", query):
        names.add(m.group(1))
    for s in re.findall(r"`([^`]+)`", query) + re.findall(r'"([^"]+)"', query):
        for m in re.finditer(r"[A-Za-z_]\w*", s):
            names.add(m.group(0))
    for m in re.finditer(r", in ([A-Za-z_]\w*)", query):
        names.add(m.group(1))
    return {n for n in names if len(n) >= 3}


def parse_query(query):
    trace_files = []
    trace_funcs = []
    for m in re.finditer(r'File "([^"]+)", line \d+, in ([A-Za-z_]\w*)', query):
        trace_files.append(m.group(1).split("/")[-1])
        trace_funcs.append(m.group(2))
    # Extract .py filenames from the query. Bare identifiers are deliberately
    # NOT treated as paths: the 643c6f4-era experiment appended every
    # meaningful issue word here, each worth a +30 path-substring boost, and
    # that measurably displaced gold files on fastapi's generic-word issues
    # (28-sample A/B plus the v4 full benchmark; see
    # docs/FINAL_HARNESS_COMPARISON.md §1). Explicit `.py` names, dotted
    # modules, backticks and quotes keep their boosts.
    paths = re.findall(r"[A-Za-z0-9_./-]+\.py\b", query)
    modules = re.findall(r"\b[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)+\b", query)
    backticks = re.findall(r"`([^`]+)`", query)
    quotes = re.findall(r'"([^"]+)"', query)
    high_tokens = set()
    exact_syms = set()
    for s in backticks + quotes + paths:
        high_tokens |= tokenize(s)
    for s in backticks + quotes:
        for t in re.findall(r"[A-Za-z_]\w*", s):
            exact_syms.add(t)
    general = tokenize(query)
    # Quoted phrases that look like error text, not identifiers. A file that
    # literally contains one is almost certainly the file that raises it.
    error_strings = []
    for s in backticks + quotes:
        t = s.strip()
        if len(t) < 12:
            continue
        if " " in t or ":" in t or "Error" in t or "error" in t or "Exception" in t:
            error_strings.append(t)
    return {
        "trace_files": trace_files,
        "trace_funcs": trace_funcs,
        "paths": paths,
        "modules": modules,
        "high_tokens": high_tokens,
        "exact_syms": exact_syms,
        "general": general,
        "backticks": backticks,
        "error_strings": error_strings,
        "callsites": call_sites(query),
    }


def is_test_path(filepath):
    """True for test modules. They are never the file the fix belongs in."""
    fp = filepath.replace("\\", "/").lower()
    name = fp.rsplit("/", 1)[-1]
    return (
        "/tests/" in fp
        or fp.startswith("tests/")
        or name.startswith("test_")
        or name.endswith("_test.py")
        or "/testing/" in fp
    )


def is_test_module(filepath):
    """True only for files pytest would collect: `test_*.py` / `*_test.py`.

    `tests/conftest.py` and `tests/compat.py` live under a test directory but are
    not commands you can run, so they are excluded from the `TEST:` suggestion.
    """
    name = filepath.replace("\\", "/").lower().rsplit("/", 1)[-1]
    return name.startswith("test_") or name.endswith("_test.py")



def path_weight(filepath):
    """Multiplicative prior on a source path, before any content score.

    Documentation examples and vendored trees are real fix sites far less often
    than the package itself, but they are not impossible, so they are demoted
    rather than dropped.
    """
    fp = filepath.replace("\\", "/").lower()
    weight = 1.0
    if "/docs_src/" in fp or fp.startswith("docs_src/"):
        weight *= 0.5
    if any(
        seg in fp
        for seg in ("/vendor/", "/vendored/", "/_vendor/", "/third_party/", "/third-party/")
    ):
        weight *= 0.3
    return weight



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
    # call-site / attribute-access boost (v6 lever C)
    csites = q.get("callsites", set())
    if sym["qualname"] in csites:
        score += 60.0
    body_low = (sym.get("body") or "").lower()
    for cn in csites:
        cl = cn.lower()
        if cl in body_low and (cl + "(" in body_low or "." + cl in body_low):
            score += 10.0
            break
    # small member-over-container base bias (v5/v6)
    if not (sym.get("signature") or "").startswith("class"):
        score += 3.0
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
    return score



def locate(root, query, top_n=5, deadline=None, stats=None):
    """Rank the files most likely to need the fix for `query`.

    Returns `(ranked_symbols, ranked_files, test_files)`. `deadline` is a
    `time.monotonic()` value: the scan stops between files and ranks whatever it
    has, so a slow tree yields a partial answer instead of nothing. `stats`, if
    given, is filled with `files_indexed`, `truncated` and `seconds`.
    """
    started = time.monotonic()
    q = parse_query(query)
    files = walk(root, deadline=deadline, max_files=MAX_FILES)
    # Source first: if the deadline cuts the scan short it must not have spent
    # the budget on test modules.
    files.sort(key=lambda f: (0 if not is_test_path(str(f)) else 1, -path_weight(str(f)), str(f)))

    allsyms = []
    file_text = {}
    truncated = False
    for f in files:
        if deadline is not None and time.monotonic() > deadline:
            truncated = True
            break
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        try:
            rel = str(f.relative_to(root))
        except ValueError:
            rel = str(f)
        file_text[rel] = text
        allsyms.extend(extract_symbols(text, rel))

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

    # member-over-container boost (v6 lever B): when a class and its method both
    # match, prefer the method's span over the enclosing class.
    class_spans = [(i, s) for i, s in enumerate(allsyms)
                   if (s.get("signature") or "").startswith("class")]
    for i, s in enumerate(allsyms):
        sig = s.get("signature") or ""
        if sig.startswith("class"):
            continue
        sl, el = s.get("start_line"), s.get("end_line")
        if not sl or not el:
            continue
        for ci, c in class_spans:
            csl, cel = c.get("start_line"), c.get("end_line")
            if csl and cel and csl <= sl and el <= cel:
                if allsyms[ci].get("_score", 0) > 0 and s.get("_score", 0) > 0:
                    s["_score"] = s.get("_score", 0) + 20.0
                break

    # file-level aggregation
    file_scores = {}
    file_nodes = {}
    for s in allsyms:
        file_nodes.setdefault(s["filepath"], []).append(s["_score"])
    trace_names = {t.lower() for t in q["trace_files"]}
    for fp, ns in file_nodes.items():
        ordered = sorted(ns, reverse=True)
        top = ordered[0] if ordered else 0.0
        rest = sum(ordered[1:4]) if len(ordered) > 1 else 0.0
        score = top + 0.25 * rest
        # A test module is never the fix site. Zero it rather than merely
        # penalising it: on the short issues the tests used to fill the top 5.
        weight = 0.0 if is_test_path(fp) else path_weight(fp)
        if weight:
            low = fp.replace("\\", "/").lower()
            base = low.rsplit("/", 1)[-1]
            if trace_names and (base in trace_names or low in trace_names):
                weight *= 6.0
            if q["error_strings"] and any(
                err in file_text.get(fp, "") for err in q["error_strings"]
            ):
                weight *= 4.0
        file_scores[fp] = score * weight

    ranked_files = sorted(
        file_scores,
        key=lambda f: (0 if not is_test_path(f) else 1, -file_scores[f], str(f)),
    )
    ranked_syms = sorted(
        allsyms,
        key=lambda s: (
            -s["_score"],
            s["filepath"],
            s.get("start_line", 0) or 0,
            s["qualname"],
        ),
    )
    tests = [{"filepath": fp} for fp in ranked_files if is_test_path(fp)]

    if stats is not None:
        stats.update(
            {
                "files_indexed": len(file_text),
                "files_found": len(files),
                "truncated": truncated,
                "seconds": round(time.monotonic() - started, 3),
                # Every collectable test module, names only. `swe.py` picks the
                # `TEST:` line from this, because the BM25 top-20 is dominated
                # by docs_src examples on fastapi.
                "test_paths": [fp for fp in ranked_files if is_test_module(fp)],
            }
        )

    return ranked_syms[:top_n], ranked_files[:top_n], tests[:20]



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

    add("def", t)
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

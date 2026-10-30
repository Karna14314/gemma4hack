import ast, os, re, sys, json, math
from pathlib import Path

SKIP_DIRS = {".git",".venv","venv","node_modules","build","dist","__pycache__"}
MAX_BYTES = 500*1024
STOPWORDS = {"the","when","with","should","error","value","return","using","does","not","from","this","that","and","for","are","was","were","has","have","had","but","can","will","into","onto","than","then","them","they","their","there","here","what","which","who","whom","whose","how","why","where","all","any","both","each","few","more","most","other","some","such","only","own","same","too","very","can","just","should","now","also","after","before","between","through","during","without","within","about","against","above","below","to","of","in","on","at","by","as","is","it","be","or","an","a","if","so","no","up","out","off","over","under","again","further","once","because","until","while","about","into","onto","per","via"}

def is_binary(path):
    try:
        with open(path,"rb") as f:
            chunk=f.read(8192)
        if b"\x00" in chunk: return True
        chunk.decode("utf-8"); return False
    except Exception:
        return True

def walk(root):
    out=[]
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p=Path(dirpath)/fn
            try:
                if p.stat().st_size > MAX_BYTES: continue
            except Exception: continue
            if is_binary(p): continue
            out.append(p)
    return out

class _WS:
    def __enter__(self):
        import warnings; self._w=warnings.catch_warnings(); self._w.__enter__(); warnings.simplefilter("ignore"); return self
    def __exit__(self,*a): self._w.__exit__(*a)

def warnings_suppress(): return _WS()

def split_ident(tok):
    toks=set()
    for part in re.split(r'[_\.]', tok):
        if part: toks.add(part.lower())
    for m in re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z])|[A-Z]+', tok):
        toks.add(m.lower())
    toks.add(tok.lower())
    return toks

def tokenize(s):
    base=re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", s)
    out=set()
    for t in base:
        if t.lower() in STOPWORDS: continue
        out |= split_ident(t)
    return out

def extract_symbols(text, filepath):
    syms=[]
    lines=text.splitlines()
    try:
        tree=ast.parse(text)
    except Exception:
        for m in re.finditer(r"^(?:async\s+)?def\s+([A-Za-z_]\w*)", text, re.M):
            syms.append({"qualname":m.group(1),"filepath":filepath,"start_line":None,"end_line":None,"signature":m.group(0),"decorators":[],"bases":[],"calls":[],"strings":[],"body":""})
        for m in re.finditer(r"^class\s+([A-Za-z_]\w*)", text, re.M):
            syms.append({"qualname":m.group(1),"filepath":filepath,"start_line":None,"end_line":None,"signature":m.group(0),"decorators":[],"bases":[],"calls":[],"strings":[],"body":""})
        return syms
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            calls=set(); strings=set()
            for c in ast.walk(node):
                if isinstance(c,ast.Call):
                    if isinstance(c.func,ast.Name): calls.add(c.func.id)
                    elif isinstance(c.func,ast.Attribute): calls.add(c.func.attr)
                if isinstance(c,ast.Constant) and isinstance(c.value,str): strings.add(c.value)
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
            sl=getattr(node,"lineno",None); el=getattr(node,"end_lineno",None)
            body=""
            if sl and el:
                body="\n".join(lines[sl-1:el])
            syms.append({
                "qualname":node.name,
                "filepath":filepath,
                "start_line":sl,
                "end_line":el,
                "signature":sig,
                "decorators":decs,
                "bases":bases,
                "calls":sorted(calls),
                "strings":sorted(strings),
                "body":body,
            })
    return syms

def parse_query(query):
    trace_files=[]; trace_funcs=[]
    for m in re.finditer(r'File "([^"]+)", line \d+, in ([A-Za-z_]\w*)', query):
        trace_files.append(m.group(1).split("/")[-1])
        trace_funcs.append(m.group(2))
    # explicit paths
    paths=re.findall(r'[A-Za-z0-9_./-]+\.py\b', query)
    modules=re.findall(r'\b[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)+\b', query)
    backticks=re.findall(r'`([^`]+)`', query)
    quotes=re.findall(r'"([^"]+)"', query)
    high_tokens=set()
    for s in backticks+quotes+paths+modules:
        high_tokens |= tokenize(s)
    # exact symbol names from backticks/quotes
    exact_syms=set()
    for s in backticks+quotes:
        for t in re.findall(r"[A-Za-z_]\w*", s):
            exact_syms.add(t)
    general=tokenize(query)
    return {
        "trace_files":trace_files,
        "trace_funcs":trace_funcs,
        "paths":paths,
        "modules":modules,
        "high_tokens":high_tokens,
        "exact_syms":exact_syms,
        "general":general,
    }

def score_candidate(sym, q, idf, N, avgdl, doc_tokens):
    score=0.0
    fp=sym["filepath"].replace("\\","/")
    # traceback file
    for tf in q["trace_files"]:
        if fp.endswith(tf) or tf in fp:
            score += 40.0
    # traceback func
    for tfn in q["trace_funcs"]:
        if sym["qualname"]==tfn or tfn in sym.get("calls",[]):
            score += 40.0
    # explicit paths/modules
    for p in q["paths"]+q["modules"]:
        stem=p.replace(".py","").split("/")[-1].split(".")[-1]
        if stem and stem.lower() in fp.lower():
            score += 30.0
    # high tokens
    for t in q["high_tokens"]:
        if t in doc_tokens:
            score += 4.0
    # exact symbol
    if sym["qualname"] in q["exact_syms"]:
        score += 20.0
    # BM25 over general tokens
    tf_counts={}
    for t in doc_tokens:
        tf_counts[t]=tf_counts.get(t,0)+1
    dl=len(doc_tokens)
    for t in q["general"]:
        if t not in idf: continue
        tf=tf_counts.get(t,0)
        if tf==0: continue
        idf_t=idf[t]
        denom=tf + 1.5*(1 - 0.75 + 0.75*dl/avgdl) if avgdl>0 else tf
        score += idf_t * (tf*(1.5+1))/(tf+1.5*(1-0.75+0.75*dl/avgdl))
    # penalties
    if "/tests/" in fp or fp.startswith("tests/") or "test_" in Path(fp).name:
        score -= 1.5
    if "/docs/" in fp:
        score -= 1.0
    return score

def locate(root, query, top_n=5):
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
    q=parse_query(query)
    # build corpus
    docs=[]
    for s in allsyms:
        dt=set()
        dt |= tokenize(s["qualname"])
        dt |= tokenize(" ".join(s.get("calls",[])))
        dt |= tokenize(" ".join(s.get("strings",[])))
        dt |= tokenize(" ".join(s.get("decorators",[])))
        dt |= tokenize(" ".join(s.get("bases",[])))
        dt |= tokenize(s["filepath"])
        dt |= tokenize(s.get("body",""))
        docs.append(dt)
    N=len(docs)
    df={}
    for dt in docs:
        for t in dt:
            df[t]=df.get(t,0)+1
    idf={}
    for t,d in df.items():
        idf[t]=math.log((N - d + 0.5)/(d+0.5)+1.0)
    avgdl=sum(len(d) for d in docs)/N if N else 1
    # attach doc tokens
    for s,dt in zip(allsyms,docs):
        s["_doc"]=dt
    # score
    for s in allsyms:
        s["_score"]=score_candidate(s,q,idf,N,avgdl,s["_doc"])
    ranked=sorted(allsyms, key=lambda s: s["_score"], reverse=True)
    # files
    files_ranked=[]
    seen=set()
    for s in ranked:
        if s["filepath"] not in seen:
            seen.add(s["filepath"]); files_ranked.append(s["filepath"])
    tests=[s for s in ranked if "/tests/" in s["filepath"] or s["filepath"].startswith("tests/") or "test_" in Path(s["filepath"]).name]
    # top 3 unique test files
    tfiles=[]; tseen=set()
    for s in tests:
        if s["filepath"] not in tseen:
            tseen.add(s["filepath"]); tfiles.append(s["filepath"])
    return ranked[:top_n], files_ranked[:top_n], [{"filepath":f} for f in tfiles[:3]]

def twins(root, symbol):
    files=walk(root)
    allsyms=[]
    for f in files:
        if f.suffix != ".py": continue
        try:
            text=f.read_text(encoding="utf-8", errors="replace")
        except Exception: continue
        rel=str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        allsyms.extend(extract_symbols(text, rel))
    target=[s for s in allsyms if s["qualname"]==symbol]
    if not target: return []
    t=target[0]
    out=[]
    for s in allsyms:
        if symbol in s.get("calls",[]): out.append(("caller", s))
    for s in allsyms:
        if s["qualname"]==symbol and s["filepath"]!=t["filepath"]:
            out.append(("override", s))
    tstr=set(t.get("strings",[]))
    for s in allsyms:
        if s is t: continue
        if tstr and tstr & set(s.get("strings",[])):
            out.append(("twin_string", s))
    return out


import os, json, glob, re, math, csv, time, tempfile, shutil, pathlib
base="/kaggle/input/competitions/gemma-4-developer-agent"
out="/kaggle/working"

def filepath_to_module(fp):
    p = fp.strip()
    if p.startswith("a/") or p.startswith("b/"):
        p = p[2:]
    if p.startswith("src/"):
        p = p[4:]
    if p.endswith(".py"):
        p = p[:-3]
    elif p.endswith("/__init__.py"):
        p = p[:-12]
    mod = p.replace("/", ".")
    return mod

def parse_patch_gold(patch):
    files = set()
    for m in re.finditer(r"^diff --git a/(.+?) b/(.+)$", patch, re.M):
        f = m.group(2)
        if f.endswith(".py") and not f.startswith("tests/") and not f.startswith("test/"):
            files.add(f)
    if not files:
        for m in re.finditer(r"^--- a/(.+)$", patch, re.M):
            f = m.group(1)
            if f.endswith(".py") and not f.startswith("tests/") and not f.startswith("test/"):
                files.add(f)
    f_gold = {filepath_to_module(f) for f in files if f}
    syms = set()
    for m in re.finditer(r"@@.*@@.*\b(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", patch, re.M):
        syms.add(m.group(2))
    for m in re.finditer(r"^[+-]\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", patch, re.M):
        syms.add(m.group(1))
    return f_gold, syms, files

def match_file(pred_mod, gold_set):
    for g in gold_set:
        if pred_mod == g or pred_mod.endswith("." + g) or g.endswith("." + pred_mod) or pred_mod in g or g in pred_mod:
            return True
    return False

def match_sym(pred_name, gold_set):
    return pred_name in gold_set

def main():
    tasks_file = base + "/tasks.jsonl"
    if not os.path.exists(tasks_file):
        print("Dataset not present; cannot run.")
        return
    tasks = [json.loads(x) for x in open(tasks_file) if x.strip()]
    file_recalls = {k: [] for k in (1,3,5,10)}
    sym_recalls = {k: [] for k in (1,3,5,10)}
    runtimes = []
    outchars = []
    evaluated = 0
    for t in tasks:
        f_gold, syms_gold, _ = parse_patch_gold(t.get("patch",""))
        gpath = None
        repo_name = t["repo"].split("/")[-1]
        for p in glob.glob(base+"/graphs/*.json"):
            if repo_name in p:
                if t["base_commit"][:8] in p:
                    gpath = p; break
        if not gpath:
            for p in glob.glob(base+"/graphs/*.json"):
                if repo_name in p:
                    gpath = p; break
        if not gpath:
            continue
        g = json.load(open(gpath))
        nodes = g["nodes"]
        # reconstruct virtual repo
        tmp = tempfile.mkdtemp()
        try:
            # group node text by module
            mod_texts = {}
            node_id_to_file = {}
            for n in nodes:
                nid = n["id"]
                mod = nid.split("::")[0].split(":")[0]
                node_id_to_file[nid] = mod
                text = n.get("text","")
                if not text:
                    continue
                mod_texts.setdefault(mod, [])
                mod_texts[mod].append(text)
            for mod, texts in mod_texts.items():
                rel = mod.replace(".", "/") + ".py"
                path = pathlib.Path(tmp) / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n\n".join(texts), encoding="utf-8", errors="replace")
            start = time.time()
            ranked, files, tests = locate(tmp, t.get("problem_statement",""), 10)
            dt = time.time() - start
            runtimes.append(dt)
            # predicted
            pred_files_mod = [filepath_to_module(f) for f in files]
            pred_syms = [s["qualname"] for s in ranked]
            # output char estimate
            outchars.append(len("\n".join(files) + "\n" + "\n".join(pred_syms)))
            # compute recalls
            for k in (1,3,5,10):
                top_files = pred_files_mod[:k]
                if f_gold:
                    hits = sum(1 for g in f_gold if any(match_file(pf, {g}) for pf in top_files))
                    file_recalls[k].append(hits / len(f_gold))
                else:
                    file_recalls[k].append(0.0)
                top_syms = pred_syms[:k]
                if syms_gold:
                    hits = sum(1 for g in syms_gold if g in top_syms)
                    sym_recalls[k].append(hits / len(syms_gold))
                else:
                    sym_recalls[k].append(0.0)
            evaluated += 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    lines = ["# SWE_TOOLKIT 129-task Recall Benchmark\n"]
    lines.append(f"Tasks evaluated: {evaluated}\n")
    lines.append("## File Recall")
    lines.append("| k | Recall |")
    lines.append("|---|---:|")
    for k in (1,3,5,10):
        lines.append(f"| {k} | {sum(file_recalls[k])/len(file_recalls[k]):.4f} |")
    lines.append("\n## Function/Symbol Recall")
    lines.append("| k | Recall |")
    lines.append("|---|---:|")
    for k in (1,3,5,10):
        lines.append(f"| {k} | {sum(sym_recalls[k])/len(sym_recalls[k]):.4f} |")
    lines.append(f"\nAvg runtime (s): {sum(runtimes)/len(runtimes):.3f}")
    lines.append(f"Avg output chars: {sum(outchars)/len(outchars):.0f}")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "SWE_TOOLKIT_BENCHMARK.md"), "w").write("\n".join(lines))
    print("\n".join(lines))

if __name__ == "__main__":
    main()

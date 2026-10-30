import os, json, glob, re, math, csv, time, statistics
import numpy as np

base = "/kaggle/input/competitions/gemma-4-developer-agent"
out = "/kaggle/working"


def filepath_to_module(fp):
    p = fp.strip()
    if p.startswith("a/") or p.startswith("b/"):
        p = p[2:]
    if p.startswith("src/"):
        p = p[4:]
    if p.endswith("/__init__.py"):
        p = p[:-12]
    elif p.endswith(".py"):
        p = p[:-3]
    mod = p.replace("/", ".")
    return mod


def parse_patch_gold(patch):
    files = set()
    for m in re.finditer(r"^diff --git a/(.+?) b/(.+)$", patch, re.M):
        f = m.group(2)
        if f.endswith(".py"):
            files.add(f)
    if not files:
        for m in re.finditer(r"^--- a/(.+)$", patch, re.M):
            f = m.group(1)
            if f.endswith(".py"):
                files.add(f)
    f_gold = {filepath_to_module(f) for f in files if f}

    syms = set()
    for m in re.finditer(r"@@.*@@.*\b(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", patch, re.M):
        syms.add(m.group(2))
    for m in re.finditer(r"^[+-]\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", patch, re.M):
        syms.add(m.group(1))
    return f_gold, syms, files


def identifiers(text):
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text))


def load_graph_and_embeddings(repo, commit):
    repo_name = repo.split("/")[-1].lower()
    gpath = None
    for p in glob.glob(base + "/graphs/*.json"):
        if repo_name in os.path.basename(p).lower():
            if commit[:8].lower() in os.path.basename(p).lower():
                gpath = p
                break
    if not gpath:
        for p in glob.glob(base + "/graphs/*.json"):
            if repo_name in os.path.basename(p).lower():
                gpath = p
                break

    npz_path = None
    for p in glob.glob(base + "/embeddings/*.npz"):
        if repo_name in os.path.basename(p).lower():
            if commit[:8].lower() in os.path.basename(p).lower():
                npz_path = p
                break
    if not npz_path:
        for p in glob.glob(base + "/embeddings/*.npz"):
            if repo_name in os.path.basename(p).lower():
                npz_path = p
                break
    return gpath, npz_path


def cosine_similarity(query_vec, mat):
    norm_q = np.linalg.norm(query_vec)
    if norm_q == 0:
        return np.zeros(mat.shape[0])
    norms_mat = np.linalg.norm(mat, axis=1)
    norms_mat[norms_mat == 0] = 1e-10
    return np.dot(mat, query_vec) / (norms_mat * norm_q)


def node_matches_gold(nid, f_gold, syms_gold):
    for fg in f_gold:
        if nid == fg or nid.startswith(fg + ".") or fg.startswith(nid + "."):
            if syms_gold:
                low = nid.lower()
                if any(s.lower() in low for s in syms_gold):
                    return True
            else:
                return True
    return False


def tokenize(s):
    STOPWORDS = {"the", "when", "with", "should", "error", "value", "return", "using", "does", "not", "from", "this", "that", "and", "for", "are", "was", "were", "has", "have", "had", "but", "can", "will", "into", "onto", "than", "then", "them", "they", "their", "there", "here", "what", "which", "who", "whom", "whose", "how", "why", "where", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "only", "own", "same", "too", "very", "just", "now", "also", "after", "before", "between", "through", "during", "without", "within", "about", "against", "above", "below", "to", "of", "in", "on", "at", "by", "as", "is", "it", "be", "or", "an", "a", "if", "so", "no", "up", "out", "off", "over", "under", "again", "further", "once", "because", "until", "while"}
    base = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", s)
    out = set()
    for t in base:
        if t.lower() in STOPWORDS:
            continue
        out.add(t.lower())
        for part in re.split(r"[_\.]", t):
            if part and part.lower() not in STOPWORDS:
                out.add(part.lower())
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


def tokenize_rich(s):
    base = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", s)
    out = set()
    STOPWORDS = {"the", "when", "with", "should", "error", "value", "return", "using", "does", "not", "from", "this", "that", "and", "for", "are", "was", "were", "has", "have", "had", "but", "can", "will", "into", "onto", "than", "then", "them", "they", "their", "there", "here", "what", "which", "who", "whom", "whose", "how", "why", "where", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "only", "own", "same", "too", "very", "just", "now", "also", "after", "before", "between", "through", "during", "without", "within", "about", "against", "above", "below", "to", "of", "in", "on", "at", "by", "as", "is", "it", "be", "or", "an", "a", "if", "so", "no", "up", "out", "off", "over", "under", "again", "further", "once", "because", "until", "while"}
    for t in base:
        if t.lower() in STOPWORDS:
            continue
        out |= split_ident(t)
    return out


PLAYBOOKS = {
"FALSINESS_TRAP": "Falsy values can be valid inputs.",
"MUTABLE_STATE": "Copy caller dicts and lists at boundaries.",
"TYPE_SUBCLASS": "Use isinstance, not type is.",
"ASYNC_SYNC_TWIN": "Check sync and async twin methods.",
"FASTAPI_PYDANTIC": "Validate Pydantic fields, aliases, defaults.",
"RICH_RENDERING": "Check cell_len and Measurement bounds.",
"HTTP_URL_COOKIES": "Strip auth headers on redirect.",
"DECORATOR_WRAP": "Use functools.wraps on decorators.",
"EXCEPTION_CHAIN": "Match exact exception class and message.",
"REGISTRATION_SIBLING": "Mirror sibling definitions and imports.",
}

KEYWORDS = {
"FALSINESS_TRAP": ["none", "false", "0", "empty", "falsy", "truthy"],
"MUTABLE_STATE": ["cache", "default", "mutable", "state", "global", "list", "dict", "copy"],
"TYPE_SUBCLASS": ["subclass", "isinstance", "type", "bool", "int"],
"ASYNC_SYNC_TWIN": ["async", "await", "sync", "twin"],
"FASTAPI_PYDANTIC": ["fastapi", "pydantic", "model", "field", "alias", "response"],
"RICH_RENDERING": ["rich", "console", "render", "markup", "width", "cell"],
"HTTP_URL_COOKIES": ["url", "cookie", "redirect", "http", "request", "response", "header"],
"DECORATOR_WRAP": ["decorator", "wrap", "functools", "wrapped", "signature"],
"EXCEPTION_CHAIN": ["raise", "exception", "chain", "cause", "from", "error"],
"REGISTRATION_SIBLING": ["register", "dispatch", "option", "__all__", "sibling", "feature"],
}


def select_hints(query, code="", imports=""):
    text = (query + " " + code + " " + imports).lower()
    scores = []
    for name, kw in KEYWORDS.items():
        score = sum(1 for k in kw if k in text)
        scores.append((score, name))
    scores.sort(reverse=True)
    chosen = [name for score, name in scores if score > 0][:2]
    if not chosen:
        chosen = [scores[0][1]]
    out = []
    total_tokens = 0
    for name in chosen[:2]:
        hint = "[{}] {}".format(name, PLAYBOOKS[name])
        hint_tokens = len(hint.split())
        if total_tokens + hint_tokens > 120:
            break
        out.append(hint)
        total_tokens += hint_tokens
    return "\n".join(out)


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
        high_tokens |= tokenize_rich(s) if False else tokenize(s)
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
    if "/tests/" in fp or fp.startswith("tests/") or "test_" in os.path.basename(fp):
        score -= 1.5
    if "/docs/" in fp or "docs_src" in fp:
        score -= 1.0
    return score


def is_traceback_issue(ps):
    if re.search(r'File ".*?"', ps):
        return True
    if re.search(r"\b[\w./-]+\.py\b", ps):
        return True
    return False


def median(xs):
    if not xs:
        return 0.0
    return float(statistics.median(xs))


def mean(xs):
    if not xs:
        return 0.0
    return float(statistics.mean(xs))


def p90(xs):
    if not xs:
        return 0.0
    s = sorted(xs)
    idx = int(0.9 * (len(s) - 1))
    return float(s[idx])


def main():
    tasks_file = base + "/tasks.jsonl"
    tasks = [json.loads(x) for x in open(tasks_file) if x.strip()]

    # accumulators for experiment 1
    methods = ["M1", "M2", "M3", "M4", "M5"]
    method_names = {
        "M1": "Lexical Grep Baseline",
        "M2": "Dense Embedding Retrieval",
        "M3": "1-Hop AST Call Graph Expansion",
        "M4": "swe_toolkit (_index.py)",
        "M5": "Hybrid RRF",
    }

    # metrics grouped by task subset
    # structure: subset -> method -> level(node/file) -> k -> list
    def new_metrics():
        return {m: {"node": {k: [] for k in (1, 3, 5, 10)}, "file": {k: [] for k in (1, 3, 5, 10)}, "mrr_node": [], "mrr_file": [], "latency_ms": [], "chars": []} for m in methods}

    subsets = {
        "all": new_metrics(),
        "in_graph": new_metrics(),
        "traceback": new_metrics(),
        "behavioral": new_metrics(),
    }
    repo_metrics = {}
    per_repo_methods = {}

    m3_cap_exceed = 0
    m3_cap_total = 0

    evaluated = 0
    in_graph_count = 0
    docs_src_lacking = 0

    exp2_rows = []  # per task
    exp3_triggers = {pb: 0 for pb in PLAYBOOKS}
    exp3_matches = {pb: 0 for pb in PLAYBOOKS}
    exp3_total_triggered = 0
    exp3_total_matched = 0

    for t in tasks:
        repo = t["repo"]
        repo_short = repo.split("/")[-1]
        ps = t.get("problem_statement", "")
        f_gold_mods, syms_gold, orig_files = parse_patch_gold(t.get("patch", ""))

        # docs_src lacking check
        gold_py_files = [f for f in orig_files]
        has_docs_src = any("docs_src/" in f or f.startswith("docs/") for f in gold_py_files)

        gpath, npz_path = load_graph_and_embeddings(repo, t["base_commit"])

        graph_available = bool(gpath and os.path.exists(gpath))
        npz_available = bool(npz_path and os.path.exists(npz_path))

        # load graph
        g = None
        nodes = []
        edges = []
        if graph_available:
            g = json.load(open(gpath))
            nodes = g.get("nodes", [])
            edges = g.get("edges", [])

        node_id_to_name = {}
        node_id_to_text = {}
        node_list = []
        for n in nodes:
            nid = n["id"]
            node_list.append(nid)
            node_id_to_name[nid] = n.get("name", "")
            node_id_to_text[nid] = n.get("text", "")

        # Fallback: use embedding keys as nodes when no graph is available
        if not node_list and npz_available:
            try:
                z = np.load(npz_path)
                for k in z.files:
                    node_list.append(k)
                    node_id_to_name[k] = k.split(".")[-1]
                    node_id_to_text[k] = ""
            except Exception:
                pass

        # G_gold
        G_gold = set()
        if node_list:
            for nid in node_list:
                if node_matches_gold(nid, f_gold_mods, syms_gold):
                    G_gold.add(nid)
        if not G_gold and node_list and f_gold_mods:
            for nid in node_list:
                for fg in f_gold_mods:
                    if fg.split(".")[-1] in nid:
                        G_gold.add(nid)
        if not G_gold and node_list:
            # in-graph false
            pass

        in_graph = bool(graph_available and node_list and G_gold)
        if in_graph:
            in_graph_count += 1
        if has_docs_src and not in_graph:
            docs_src_lacking += 1

        F_gold = f_gold_mods if f_gold_mods else {nid for nid in G_gold}

        # adjacency
        adj = {}
        callers = {}  # target -> set sources
        for e in edges:
            s = e.get("source"); tgt = e.get("target")
            adj.setdefault(s, set()).add(tgt)
            adj.setdefault(tgt, set()).add(s)
            callers.setdefault(tgt, set()).add(s)

        # problem identifiers
        problem_toks = identifiers(ps)

        # ---- M1 Lexical ----
        t0 = time.perf_counter()
        lex_scores = []
        for nid in node_list:
            text = node_id_to_name[nid] + " " + node_id_to_text[nid]
            score = sum(1 for tok in problem_toks if tok in text)
            lex_scores.append((score, nid))
        lex_sorted = [nid for sc, nid in sorted(lex_scores, key=lambda x: (-x[0], x[1]))]
        if not lex_sorted:
            lex_sorted = list(node_list)
        # fallback for no graph: empty
        latency_m1 = (time.perf_counter() - t0) * 1000.0

        # ---- M2 Dense Embedding ----
        t0 = time.perf_counter()
        semantic_sorted = []
        if npz_available and node_list:
            try:
                z = np.load(npz_path)
                keys = list(z.files)
                emb = {k: z[k] for k in keys}
                mat = np.array([emb[nid] for nid in node_list if nid in emb], dtype=np.float32)
                valid_nodes = [nid for nid in node_list if nid in emb]
                if len(mat) == len(valid_nodes) and len(valid_nodes) > 0:
                    # query vector via suffix matching
                    q_candidates = []
                    for tok in problem_toks:
                        for k in keys:
                            kl = k.lower()
                            if kl.endswith(tok.lower()) or tok.lower() in kl.split(".") or kl.split(".")[-1] == tok.lower():
                                q_candidates.append(k)
                    q_vecs = [emb[k] for k in q_candidates if k in emb]
                    if not q_vecs:
                        # fallback top lexical embeddings
                        for nid in lex_sorted[:3]:
                            if nid in emb:
                                q_vecs.append(emb[nid])
                    if q_vecs:
                        q_vec = np.mean(np.array(q_vecs, dtype=np.float32), axis=0)
                        sims = cosine_similarity(q_vec, mat)
                        # suffix bonus
                        suffix_bonus = np.zeros(len(valid_nodes))
                        for i, nid in enumerate(valid_nodes):
                            nm = node_id_to_name[nid].lower()
                            for tok in problem_toks:
                                if nm.endswith(tok.lower()):
                                    suffix_bonus[i] += 1.0
                        order = np.argsort(-(sims + 0.05 * suffix_bonus))
                        semantic_sorted = [valid_nodes[i] for i in order]
                    else:
                        semantic_sorted = list(lex_sorted)
            except Exception:
                semantic_sorted = list(lex_sorted)
        if not semantic_sorted:
            semantic_sorted = list(lex_sorted) if lex_sorted else list(node_list)
        latency_m2 = (time.perf_counter() - t0) * 1000.0

        # ---- M3 1-Hop Expansion ----
        t0 = time.perf_counter()
        seed_nodes = lex_sorted[:3] if lex_sorted else node_list[:3]
        graph_expanded = list(seed_nodes)
        cap_exceed_this = 0
        cap_total_this = 0
        for seed in seed_nodes:
            nbrs = adj.get(seed, set())
            cap_total_this += 1
            nbr_text_len = sum(len(node_id_to_text.get(n, "")) for n in nbrs)
            if nbr_text_len > 5000:
                cap_exceed_this += 1
            for neighbor in nbrs:
                if neighbor not in graph_expanded:
                    graph_expanded.append(neighbor)
        for nid in lex_sorted:
            if nid not in graph_expanded:
                graph_expanded.append(nid)
        if not graph_expanded:
            graph_expanded = list(node_list)
        m3_cap_total += cap_total_this
        m3_cap_exceed += cap_exceed_this
        latency_m3 = (time.perf_counter() - t0) * 1000.0

        # ---- M4 swe_toolkit ----
        t0 = time.perf_counter()
        m4_sorted = []
        if node_list:
            # build sym list
            allsyms = []
            for nid in node_list:
                allsyms.append({
                    "qualname": node_id_to_name[nid],
                    "filepath": nid,
                    "calls": [],
                    "strings": [],
                    "decorators": [],
                    "bases": [],
                    "body": node_id_to_text[nid],
                })
            q = parse_query(ps)
            docs = []
            for s in allsyms:
                dt = tokenize_rich(s["qualname"] + " " + s["body"] + " " + s["filepath"])
                docs.append(dt)
            N = len(docs)
            df = {}
            for dt in docs:
                for t2 in dt:
                    df[t2] = df.get(t2, 0) + 1
            idf = {}
            if N:
                for t2, d in df.items():
                    idf[t2] = math.log((N - d + 0.5) / (d + 0.5) + 1.0)
            avgdl = (sum(len(d) for d in docs) / N) if N else 1
            for s, dt in zip(allsyms, docs):
                s["_doc"] = dt
                s["_score"] = score_candidate(s, q, idf, N, avgdl, dt)
            m4_sorted = [s["filepath"] for s in sorted(allsyms, key=lambda x: (-x["_score"], x["filepath"]))]
        if not m4_sorted:
            m4_sorted = list(lex_sorted) if lex_sorted else list(node_list)
        latency_m4 = (time.perf_counter() - t0) * 1000.0

        # ---- M5 Hybrid RRF ----
        t0 = time.perf_counter()
        # ranks (1-based)
        rank_swe = {nid: i + 1 for i, nid in enumerate(m4_sorted)}
        rank_npz = {nid: i + 1 for i, nid in enumerate(semantic_sorted)}
        all_nodes = list(node_list)
        rrf = {}
        for nid in all_nodes:
            rs = rank_swe.get(nid, len(all_nodes) + 1)
            rn = rank_npz.get(nid, len(all_nodes) + 1)
            rrf[nid] = 1.0 / (60 + rs) + 1.0 / (60 + rn)
        # caller edge bonus: top 5 swe seeds
        for seed in m4_sorted[:5]:
            for caller in callers.get(seed, set()):
                if caller in rrf:
                    rrf[caller] += 1.0 / 61.0
        m5_sorted = sorted(all_nodes, key=lambda n: (-rrf.get(n, 0.0), n))
        if not m5_sorted:
            m5_sorted = list(lex_sorted) if lex_sorted else list(node_list)
        latency_m5 = (time.perf_counter() - t0) * 1000.0

        ranked_map = {
            "M1": (lex_sorted, latency_m1),
            "M2": (semantic_sorted, latency_m2),
            "M3": (graph_expanded, latency_m3),
            "M4": (m4_sorted, latency_m4),
            "M5": (m5_sorted, latency_m5),
        }

        # Determine subset labels for this task
        subset_labels = ["all"]
        if in_graph:
            subset_labels.append("in_graph")
        if is_traceback_issue(ps):
            subset_labels.append("traceback")
        else:
            subset_labels.append("behavioral")

        # repo metrics init
        if repo_short not in repo_metrics:
            repo_metrics[repo_short] = {"count": 0, "tasks": 0}
            per_repo_methods[repo_short] = new_metrics()
        repo_metrics[repo_short]["tasks"] += 1

        for m in methods:
            ranked_nodes, lat = ranked_map[m]
            # node recall
            for k in (1, 3, 5, 10):
                topk = set(ranked_nodes[:k])
                rec = (len(topk & G_gold) / len(G_gold)) if G_gold else 0.0
                # file recall
                topk_files_nodes = ranked_nodes[:k]
                hit_count = 0
                for fg in F_gold:
                    if any((nid == fg or nid.startswith(fg + ".") or fg.startswith(nid + ".")) for nid in topk_files_nodes):
                        hit_count += 1
                frec = (hit_count / len(F_gold)) if F_gold else 0.0

                for sl in subset_labels:
                    subsets[sl][m]["node"][k].append(rec)
                    subsets[sl][m]["file"][k].append(frec)
                per_repo_methods[repo_short][m]["node"][k].append(rec)
                per_repo_methods[repo_short][m]["file"][k].append(frec)

            # MRR node: reciprocal rank of first gold node
            rr_node = 0.0
            for idx, nid in enumerate(ranked_nodes, start=1):
                if nid in G_gold:
                    rr_node = 1.0 / idx
                    break
            rr_file = 0.0
            for idx, nid in enumerate(ranked_nodes, start=1):
                if any((nid == fg or nid.startswith(fg + ".") or fg.startswith(nid + ".")) for fg in F_gold):
                    rr_file = 1.0 / idx
                    break
            for sl in subset_labels:
                subsets[sl][m]["mrr_node"].append(rr_node)
                subsets[sl][m]["mrr_file"].append(rr_file)
            per_repo_methods[repo_short][m]["mrr_node"].append(rr_node)
            per_repo_methods[repo_short][m]["mrr_file"].append(rr_file)

            # latency and chars
            top10_text = " ".join(node_id_to_name.get(n, "") + " " + node_id_to_text.get(n, "")[:200] for n in ranked_nodes[:10])
            chars = len(top10_text)
            for sl in subset_labels:
                subsets[sl][m]["latency_ms"].append(lat)
                subsets[sl][m]["chars"].append(chars)
            per_repo_methods[repo_short][m]["latency_ms"].append(lat)
            per_repo_methods[repo_short][m]["chars"].append(chars)

        evaluated += 1

        # ---- Experiment 2: patch anatomy ----
        patch = t.get("patch", "")
        test_patch = t.get("test_patch", "")
        files = set()
        for m in re.finditer(r"^diff --git a/(.+?) b/(.+)$", patch, re.M):
            files.add(m.group(2))
        if not files:
            for m in re.finditer(r"^--- a/(.+)$", patch, re.M):
                files.add(m.group(1))
        added = sum(1 for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
        deleted = sum(1 for line in patch.splitlines() if line.startswith("-") and not line.startswith("---"))
        hunks = sum(1 for line in patch.splitlines() if line.startswith("@@"))
        new_file_set = set()
        cur = None
        for line in patch.splitlines():
            m = re.match(r"^diff --git a/(.+?) b/(.+)$", line)
            if m:
                cur = m.group(2)
                continue
            m2 = re.match(r"^--- a/(.+)$", line)
            if m2:
                cur = m2.group(1)
                continue
            if line.startswith("@@ -0,0 +") and cur:
                new_file_set.add(cur)
        new_files = len(new_file_set)
        exp2_rows.append({
            "repo": repo_short,
            "files": len(files),
            "added": added,
            "deleted": deleted,
            "hunks": hunks,
            "new_files": new_files,
            "files_list": sorted(files),
        })

        # ---- Experiment 3: knowledge audit ----
        # code text from graph nodes matching gold files
        code_text = ""
        if node_list:
            for nid in node_list:
                if node_matches_gold(nid, f_gold_mods, syms_gold):
                    code_text += " " + node_id_to_text.get(nid, "")
        if not code_text:
            code_text = " ".join(node_id_to_text.get(nid, "") for nid in node_list[:20])
        hints = select_hints(ps, code_text, "")
        triggered = []
        for pb in PLAYBOOKS:
            if "[" + pb + "]" in hints:
                triggered.append(pb)
        # fallback: if none, top1
        if not triggered:
            # parse first bracket
            m = re.search(r"\[([A-Z_]+)\]", hints)
            if m and m.group(1) in PLAYBOOKS:
                triggered.append(m.group(1))
        for pb in triggered:
            exp3_triggers[pb] += 1
            exp3_total_triggered += 1
        # precision match
        plow = patch.lower()
        rlow = repo.lower()
        for pb in triggered:
            matched = False
            if pb == "FALSINESS_TRAP":
                matched = ("is none" in plow) or ("is not none" in plow)
            elif pb == "MUTABLE_STATE":
                matched = ("copy()" in plow) or (".copy(" in plow) or ("default=None" in plow) or ("default = None" in plow)
            elif pb == "TYPE_SUBCLASS":
                matched = "isinstance" in plow
            elif pb == "ASYNC_SYNC_TWIN":
                matched = ("async def" in plow) and ("def " in plow)
            elif pb == "FASTAPI_PYDANTIC":
                matched = ("fastapi" in rlow) and (("pydantic" in plow) or ("basemodel" in plow) or ("field(" in plow))
            elif pb == "RICH_RENDERING":
                matched = ("rich" in rlow) and (("console" in plow) or ("render" in plow) or ("cell_len" in plow) or ("measurement" in plow))
            elif pb == "HTTP_URL_COOKIES":
                matched = (("requests" in rlow) or ("httpx" in rlow)) and (("cookie" in plow) or ("redirect" in plow) or ("header" in plow) or ("url" in plow))
            elif pb == "DECORATOR_WRAP":
                matched = ("functools.wraps" in plow) or ("wraps(" in plow)
            elif pb == "EXCEPTION_CHAIN":
                matched = ("raise" in plow) and (" from " in plow)
            elif pb == "REGISTRATION_SIBLING":
                matched = ("__all__" in plow) or ("register" in plow) or ("dispatch" in plow)
            if matched:
                exp3_matches[pb] += 1
                exp3_total_matched += 1

    # cap percentage
    cap_pct = (m3_cap_exceed / m3_cap_total * 100.0) if m3_cap_total else 0.0

    # ---- Build outputs ----
    os.makedirs(out, exist_ok=True)

    def agg(mdata):
        outd = {}
        for m in methods:
            md = mdata[m]
            row = {}
            for k in (1, 3, 5, 10):
                row[f"R@{k}_node"] = round(float(np.mean(md["node"][k])) if md["node"][k] else 0.0, 4)
                row[f"R@{k}_file"] = round(float(np.mean(md["file"][k])) if md["file"][k] else 0.0, 4)
            row["MRR_node"] = round(float(np.mean(md["mrr_node"])) if md["mrr_node"] else 0.0, 4)
            row["MRR_file"] = round(float(np.mean(md["mrr_file"])) if md["mrr_file"] else 0.0, 4)
            row["Latency_ms"] = round(float(np.mean(md["latency_ms"])) if md["latency_ms"] else 0.0, 1)
            row["Chars"] = int(np.mean(md["chars"])) if md["chars"] else 0
            row["N"] = len(md["node"][1])
            outd[m] = row
        return outd

    summary = {}
    for sl in ("all", "in_graph", "traceback", "behavioral"):
        summary[sl] = agg(subsets[sl])

    repo_summary = {}
    for repo, md in per_repo_methods.items():
        repo_summary[repo] = agg(md)
        repo_summary[repo]["count"] = repo_metrics[repo]["tasks"]

    # Save JSON
    result_json = {
        "experiment1": {
            "summary": summary,
            "repo_summary": repo_summary,
            "m3_cap_exceed_pct": round(cap_pct, 2),
            "m3_cap_exceed": m3_cap_exceed,
            "m3_cap_total": m3_cap_total,
            "in_graph_count": in_graph_count,
            "docs_src_lacking": docs_src_lacking,
            "evaluated": evaluated,
        },
    }

    # Experiment 2
    # overall + per repo
    def patch_agg(rows):
        files = [r["files"] for r in rows]
        added = [r["added"] for r in rows]
        deleted = [r["deleted"] for r in rows]
        hunks = [r["hunks"] for r in rows]
        newf = [r["new_files"] for r in rows]
        one_file = sum(1 for r in rows if r["files"] == 1)
        multi = sum(1 for r in rows if r["files"] >= 2)
        any_new = sum(1 for r in rows if r["new_files"] > 0)
        return {
            "N": len(rows),
            "files_median": median(files),
            "files_mean": round(mean(files), 2),
            "files_p90": p90(files),
            "added_median": median(added),
            "added_mean": round(mean(added), 1),
            "added_p90": p90(added),
            "deleted_median": median(deleted),
            "deleted_mean": round(mean(deleted), 1),
            "deleted_p90": p90(deleted),
            "hunks_median": median(hunks),
            "hunks_mean": round(mean(hunks), 1),
            "hunks_p90": p90(hunks),
            "pct_one_file": round(one_file / len(rows) * 100, 1) if rows else 0.0,
            "pct_multi_file": round(multi / len(rows) * 100, 1) if rows else 0.0,
            "pct_new_files": round(any_new / len(rows) * 100, 1) if rows else 0.0,
        }

    exp2_summary = {"overall": patch_agg(exp2_rows)}
    for repo in sorted(set(r["repo"] for r in exp2_rows)):
        exp2_summary[repo] = patch_agg([r for r in exp2_rows if r["repo"] == repo])
    result_json["experiment2"] = exp2_summary

    # Experiment 3
    exp3_total_trig = sum(exp3_triggers.values())
    exp3_total_match = sum(exp3_matches.values())
    exp3_per = {}
    for pb in PLAYBOOKS:
        tr = exp3_triggers[pb]
        ma = exp3_matches[pb]
        exp3_per[pb] = {
            "triggers": tr,
            "trigger_pct": round(tr / len(tasks) * 100, 1),
            "matches": ma,
            "precision": round(ma / tr * 100, 1) if tr else 0.0,
        }
    result_json["experiment3"] = {
        "per_playbook": exp3_per,
        "total_triggers": exp3_total_trig,
        "total_matches": exp3_total_match,
        "overall_precision": round(exp3_total_match / exp3_total_trig * 100, 1) if exp3_total_trig else 0.0,
        "tasks": len(tasks),
    }

    # Experiment 4 static
    ablations = [
        ("exp01", "exp01 (v1)", "31B", 0.05, "e3? no", "baseline v1"),
        ("exp02", "exp02 (v2)", "31B", 0.08, "—", "thinking on, 6 min/60 calls/120 turns"),
        ("exp03", "exp03 baseline replica", "31B", 0.17, "e3be904c…", "byte-exact public 0.17 replica"),
        ("exp04", "exp04 py_compile", "31B", None, "71bf21d6…", "mandatory py_compile (-3pp ablation)"),
        ("exp05", "exp05 patch integrity", "31B", 0.20, "2ba7f9b1…", "pre-submit patch integrity check"),
        ("exp08", "exp08 tool contract prompt", "31B", 0.17, "—", "+554 char tool prose (regression)"),
        ("exp10", "exp10 consolidated", "31B", 0.17, "—", "STATE header + 6 tools"),
        ("57697341", "57697341 31B-fallback", "31B", 0.13, "—", "31B fallback"),
        ("exp12", "exp12 timing buffer", "31B", 0.17, "—", "near-exact exp05 with 9-min buffer"),
        ("exp11_e4b", "exp11_e4b genuine E4B", "E4B", 0.06, "—", "genuine E4B bundle"),
        ("e4b-v2", "e4b-v2 (ref 57806053)", "E4B", None, "—", "temp 0.1 + imperative prompt (pending)"),
    ]
    exp4_rows = []
    for ref, name, scale, score, sha, delta in ablations:
        if score is None:
            resolved = None
            se = None
        else:
            resolved = round(score * 58, 2)
            se = round(math.sqrt(score * (1 - score) / 58), 4)
        exp4_rows.append({
            "ref": ref, "name": name, "scale": scale, "score": score,
            "sha256": sha, "config_delta": delta,
            "resolved_tasks": resolved, "binomial_se": se,
        })
    result_json["experiment4"] = exp4_rows

    # save JSON
    with open(os.path.join(out, "paper_experiments.json"), "w") as f:
        json.dump(result_json, f, indent=2)

    # ---- Markdown tables ----
    lines = []
    lines.append("# PAPER_EXPERIMENTS — Verified 129-Task Benchmarks")
    lines.append("")
    lines.append(f"Tasks evaluated: {evaluated}; In-graph tasks: {in_graph_count}; docs_src tasks lacking graph nodes: {docs_src_lacking}.")
    lines.append("")

    # Experiment 1 tables
    lines.append("## Experiment 1 — 5-Way Localization Benchmark")
    lines.append("")
    def fmt_table(subset_key, title):
        lines.append(f"### {title} (N={summary[subset_key]['M1']['N']})")
        lines.append("| Method | R@1 (node) | R@3 (node) | R@5 (node) | R@10 (node) | MRR (file) | Latency (ms) | Chars |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for m in methods:
            r = summary[subset_key][m]
            lines.append(f"| {m}: {method_names[m]} | {r['R@1_node']} | {r['R@3_node']} | {r['R@5_node']} | {r['R@10_node']} | {r['MRR_file']} | {r['Latency_ms']} | {r['Chars']} |")
        lines.append("")
        lines.append(f"### {title} — File Recall")
        lines.append("| Method | R@1 | R@3 | R@5 | R@10 | MRR |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for m in methods:
            r = summary[subset_key][m]
            lines.append(f"| {m}: {method_names[m]} | {r['R@1_file']} | {r['R@3_file']} | {r['R@5_file']} | {r['R@10_file']} | {r['MRR_file']} |")
        lines.append("")

    fmt_table("all", "All 129 Tasks")
    fmt_table("in_graph", "In-Graph Tasks")
    fmt_table("traceback", "Traceback/Explicit-Path Issues")
    fmt_table("behavioral", "Behavioral/Symptom-Only Issues")

    # Per repo
    lines.append("### Per-Repository Breakdown (In-Graph where applicable)")
    lines.append("| Repository | Tasks | M1 File R@5 | M2 File R@5 | M3 File R@5 | M4 File R@5 | M5 File R@5 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for repo in sorted(repo_summary):
        r = repo_summary[repo]
        lines.append(f"| {repo} | {r['count']} | {r['M1']['R@5_file']} | {r['M2']['R@5_file']} | {r['M3']['R@5_file']} | {r['M4']['R@5_file']} | {r['M5']['R@5_file']} |")
    lines.append("")
    lines.append(f"M3 1-hop neighborhood >5000-char cap exceedance: {m3_cap_exceed}/{m3_cap_total} = {cap_pct:.1f}%")
    lines.append("")

    # Experiment 2
    lines.append("## Experiment 2 — Gold Patch & Test Verification Anatomy")
    lines.append("")
    lines.append("| Repo | N | Files (med/mean/p90) | Added (med/mean/p90) | Deleted (med/mean/p90) | Hunks (med/mean/p90) | %1-file | %2+ | %new files |")
    lines.append("|---|---:|---|---|---|---|---:|---:|---:|")
    for key in ["overall"] + sorted(exp2_summary.keys()):
        if key == "overall":
            label = "ALL"
        else:
            label = key
        r = exp2_summary[key]
        lines.append(f"| {label} | {r['N']} | {r['files_median']}/{r['files_mean']}/{r['files_p90']} | {r['added_median']}/{r['added_mean']}/{r['added_p90']} | {r['deleted_median']}/{r['deleted_mean']}/{r['deleted_p90']} | {r['hunks_median']}/{r['hunks_mean']}/{r['hunks_p90']} | {r['pct_one_file']} | {r['pct_multi_file']} | {r['pct_new_files']} |")
    lines.append("")

    # Experiment 3
    lines.append("## Experiment 3 — Triggered SWE Domain Knowledge Book")
    lines.append("")
    lines.append("| Playbook | Triggers | Trigger % | Matches | Precision |")
    lines.append("|---|---:|---:|---:|---:|")
    for pb in PLAYBOOKS:
        r = result_json["experiment3"]["per_playbook"][pb]
        lines.append(f"| {pb} | {r['triggers']} | {r['trigger_pct']} | {r['matches']} | {r['precision']} |")
    lines.append("")
    lines.append(f"Overall precision: {result_json['experiment3']['overall_precision']}% ({exp3_total_match}/{exp3_total_trig})")
    lines.append("")

    # Experiment 4
    lines.append("## Experiment 4 — Live Leaderboard Ablation & Cross-Scale")
    lines.append("")
    lines.append("| Ref | Name | Scale | Score | SHA-256 | Resolved tasks (score*58) | Binomial SE | Config delta |")
    lines.append("|---|---|---|---:|---|---:|---:|---|")
    for r in exp4_rows:
        score_s = "" if r["score"] is None else f"{r['score']:.2f}"
        resolved_s = "" if r["resolved_tasks"] is None else f"{r['resolved_tasks']}"
        se_s = "" if r["binomial_se"] is None else f"{r['binomial_se']}"
        lines.append(f"| {r['ref']} | {r['name']} | {r['scale']} | {score_s} | {r['sha256']} | {resolved_s} | {se_s} | {r['config_delta']} |")
    lines.append("")

    md_text = "\n".join(lines)
    with open(os.path.join(out, "PAPER_TABLES.md"), "w") as f:
        f.write(md_text)
    with open(os.path.join(out, "PAPER_EXPERIMENTS.md"), "w") as f:
        f.write(md_text)

    print(f"Done. Evaluated {evaluated} tasks; in-graph {in_graph_count}; docs_src lacking {docs_src_lacking}.")


if __name__ == "__main__":
    main()

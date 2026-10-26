import os, json, glob, re, math, csv
import numpy as np

base="/kaggle/input/competitions/gemma-4-developer-agent"
out="/kaggle/working"

def parse_patch(patch):
    files=set()
    for m in re.finditer(r"^diff --git a/(.+?) b/(.+)$", patch, re.M):
        files.add(m.group(2))
    if not files:
        for m in re.finditer(r"^--- a/(.+)$", patch, re.M):
            files.add(m.group(1))
    syms=set()
    for m in re.finditer(r"^[+-].*\b(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", patch, re.M):
        syms.add(m.group(2))
    return files, syms

def identifiers(text):
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text))

tasks=[json.loads(x) for x in open(base+"/tasks.jsonl") if x.strip()]

def load_graph(repo, commit):
    # find graph file by repo prefix? graph filenames include commit hash
    # search
    for p in glob.glob(base+"/graphs/*.json"):
        if repo.split("/")[-1] in p:
            # match commit in filename
            if commit[:8] in p:
                return p
    # fallback: any graph for repo
    for p in glob.glob(base+"/graphs/*.json"):
        if repo.split("/")[-1] in p:
            return p
    return None

lex_recalls={1:[],3:[],5:[],10:[]}
graph_recalls={1:[],3:[],5:[],10:[]}
hybrid_recalls={1:[],3:[],5:[],10:[]}

for t in tasks:
    gf,gs=parse_patch(t.get("patch",""))
    if not gf:
        continue
    gpath=load_graph(t["repo"], t["base_commit"])
    if not gpath:
        continue
    g=json.load(open(gpath))
    nodes=g["nodes"]
    # map node -> file
    node_files=[ (n.get("name",""), n.get("text",""), n.get("id","")) for n in nodes]
    # lexical scores
    toks=identifiers(t.get("problem_statement",""))
    scores=[]
    for name,text,nid in node_files:
        sc=sum(1 for tok in toks if tok in name or tok in text)
        scores.append((sc,name,text,nid))
    # rank files by score
    file_score={}
    for sc,name,text,nid in scores:
        # derive file from id (before last dot?) fallback node name
        f=nid.split("::")[0] if "::" in nid else nid
        # graph node id like module.symbol; file not directly available; use id prefix
        file_score[f]=file_score.get(f,0)+sc
    # We don't have file paths in nodes; use gold file recall on symbol names instead.
    # Compute symbol recall: top-k node names
    scores_sorted=sorted(scores, key=lambda x:-x[0])
    top_names=[x[1].split('.')[-1] for x in scores_sorted]
    def recall_at(k, gold):
        if not gold: return 0.0
        hit=len(set(top_names[:k]) & gold)
        return hit/len(gold)
    for k in (1,3,5,10):
        lex_recalls[k].append(recall_at(k, gs))
    # graph expansion: neighbors of top3 seed nodes
    seed_ids=set(x[3] for x in scores_sorted[:3])
    # build adjacency
    adj={}
    for e in g["edges"]:
        adj.setdefault(e["source"],set()).add(e["target"])
        adj.setdefault(e["target"],set()).add(e["source"])
    expanded=set(seed_ids)
    for sid in list(seed_ids):
        expanded|=adj.get(sid,set())
    expanded_names=set()
    id2name={n["id"]:n["name"] for n in nodes}
    for sid in expanded:
        if sid in id2name:
            expanded_names.add(id2name[sid].split('.')[-1])
    top_expanded=list(expanded_names)[:10]
    def rec_exp(k):
        if not gs: return 0.0
        return len(set(top_expanded[:k]) & gs)/len(gs)
    for k in (1,3,5,10):
        graph_recalls[k].append(rec_exp(k))
    # hybrid: union lexical top5 + expanded
    hybrid_names=list(dict.fromkeys(top_names[:5]+top_expanded))[:10]
    def rec_hyb(k):
        if not gs: return 0.0
        return len(set(hybrid_names[:k]) & gs)/len(gs)
    for k in (1,3,5,10):
        hybrid_recalls[k].append(rec_hyb(k))

# write CSV
with open(os.path.join(out,"recall_summary.csv"),"w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["strategy","R@1","R@3","R@5","R@10"])
    for name,rec in [("lexical",lex_recalls),("graph",graph_recalls),("hybrid",hybrid_recalls)]:
        w.writerow([name]+[round(sum(rec[k])/len(rec[k]),4) for k in (1,3,5,10)])

# markdown
lines=[]
lines.append("# Experiment 1 results (129 tasks)")
lines.append("")
lines.append("| strategy | R@1 | R@3 | R@5 | R@10 |")
lines.append("|---|---:|---:|---:|---:|")
for name,rec in [("lexical",lex_recalls),("graph",graph_recalls),("hybrid",hybrid_recalls)]:
    lines.append(f"| {name} | {sum(rec[1])/len(rec[1]):.4f} | {sum(rec[3])/len(rec[3]):.4f} | {sum(rec[5])/len(rec[5]):.4f} | {sum(rec[10])/len(rec[10]):.4f} |")
lines.append("")
lines.append(f"Tasks evaluated: {len(lex_recalls[1])}")
open(os.path.join(out,"PAPER_TABLES.md"),"w").write("\n".join(lines))
print("done", len(lex_recalls[1]))

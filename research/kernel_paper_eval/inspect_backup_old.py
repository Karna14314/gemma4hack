import json, os
base="/kaggle/input/competitions/gemma-4-developer-agent"
# find a graph
import glob
g=glob.glob(base+"/graphs/*.json")[0]
print("graph", g)
d=json.load(open(g))
print("keys", list(d.keys())[:20])
print("type", type(d))
if isinstance(d, dict):
    for k,v in list(d.items())[:5]:
        print("KEY", k, "TYPE", type(v), "LEN", (len(v) if hasattr(v,'__len__') else v))

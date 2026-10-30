import json, os, glob
base="/kaggle/input/competitions/gemma-4-developer-agent"
# find npz
import numpy as np
npz=glob.glob(base+"/embeddings/*.npz")[0]
z=np.load(npz)
out=[]
out.append("npz="+npz)
out.append("keys="+str(list(z.keys())))
for k in z.keys():
    a=z[k]
    out.append(f"{k}: shape={a.shape} dtype={a.dtype}")
# task repo mapping
import json
tasks=[json.loads(x) for x in open(base+"/tasks.jsonl") if x.strip()]
repos=set(t["repo"] for t in tasks)
out.append("repos="+str(repos))
open("/kaggle/working/inspect.txt","w").write("\n".join(out))

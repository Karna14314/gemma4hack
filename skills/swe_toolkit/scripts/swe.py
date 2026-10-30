import argparse, sys, os, threading, time
sys.path.insert(0, os.path.dirname(__file__))
import _index, _knowledge, _verify

OUT_CAP=4000

def cap(s):
    if len(s)>OUT_CAP:
        return s[:OUT_CAP]+"\n...[truncated]"
    return s

def watchdog(seconds, fn, *a, **k):
    res={"v":None,"e":None}
    def worker():
        try:
            res["v"]=fn(*a,**k)
        except Exception as e:
            res["e"]=e
    t=threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(seconds)
    if t.is_alive():
        return None, TimeoutError("watchdog")
    if res["e"]:
        return None, res["e"]
    return res["v"], None

def do_locate(args):
    root=args.root or "/workspace"
    query=args.query or ""
    v,err=watchdog(25, _index.locate, root, query, 5)
    if err:
        return "STATUS: DEGRADED\nwatchdog timeout"
    ranked, files, tests = v
    lines=["STATUS: OK"]
    lines.append("TOP FILES:")
    for f in files:
        lines.append(f"  {f}")
    lines.append("TOP SYMBOLS:")
    for s in ranked:
        lines.append(f"  {s['qualname']} ({s['filepath']}:{s['start_line']})")
    if tests:
        lines.append("TOP TESTS:")
        for s in tests:
            lines.append(f"  {s['filepath']}")
    # knowledge
    code0 = ""
    try:
        p=__import__("pathlib").Path(root)/ranked[0]["filepath"]
        code0=p.read_text(errors="replace")[:2000] if ranked else ""
    except Exception:
        pass
    hint=_knowledge.select_hints(query, code0)
    lines.append("HINTS:")
    lines.append(hint)
    # cache state
    try:
        import json
        json.dump({"files":files,"tests":[s["filepath"] for s in tests]}, open("/tmp/swe_state.json","w"))
    except Exception:
        pass
    return cap("\n".join(lines))

def do_inspect(args):
    root=args.root or "/workspace"
    sym=args.symbol or ""
    v,err=watchdog(40, _index.twins, root, sym)
    if err:
        return "STATUS: DEGRADED\nwatchdog timeout"
    lines=["STATUS: OK"]
    for kind,s in v:
        lines.append(f"{kind}: {s['qualname']} ({s['filepath']}:{s['start_line']})")
    if not v:
        lines.append("no related symbols")
    return cap("\n".join(lines))

def do_verify(args):
    v,err=watchdog(180, _verify.verify, args.test)
    if err:
        return "STATUS: DEGRADED\nwatchdog timeout"
    return cap("STATUS: OK\n"+v)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?")
    ap.add_argument("--query")
    ap.add_argument("--symbol")
    ap.add_argument("--test")
    ap.add_argument("--root")
    args, unknown = ap.parse_known_args()
    cmd=args.cmd
    if cmd=="locate":
        print(do_locate(args))
    elif cmd=="inspect":
        print(do_inspect(args))
    elif cmd=="verify":
        print(do_verify(args))
    else:
        print("STATUS: OK\nusage: swe.py locate|inspect|verify")

if __name__=="__main__":
    main()

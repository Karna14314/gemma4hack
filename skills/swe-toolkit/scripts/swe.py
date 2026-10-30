import argparse
import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import _index
import _knowledge
import _verify

OUT_CAP = 4000


def _default_root():
    if os.path.isdir("/workspace"):
        return "/workspace"
    return os.getcwd()


def cap(s):
    if len(s) > OUT_CAP:
        return s[:OUT_CAP] + "\n...[truncated]"
    return s


def watchdog(seconds, fn, *a, **k):
    res = {"v": None, "e": None}

    def worker():
        try:
            res["v"] = fn(*a, **k)
        except Exception as e:
            res["e"] = e

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(seconds)
    if t.is_alive():
        return None, TimeoutError("watchdog")
    if res["e"]:
        return None, res["e"]
    return res["v"], None


def do_locate(args):
    root = args.root or _default_root()
    query = args.query or ""
    v, err = watchdog(25, _index.locate, root, query, 5)
    if err:
        return "STATUS: DEGRADED\nwatchdog timeout"
    ranked, files, tests = v
    lines = ["STATUS: OK"]
    lines.append("TOP FILES:")
    for f in files:
        lines.append("  {}".format(f))
    lines.append("TOP SYMBOLS:")
    for s in ranked:
        lines.append("  {} ({}:{})".format(s["qualname"], s["filepath"], s["start_line"]))
    if tests:
        lines.append("TOP TESTS:")
        for s in tests:
            lines.append("  {}".format(s["filepath"]))
    code0 = ""
    try:
        if ranked:
            p = Path(root) / ranked[0]["filepath"]
            code0 = p.read_text(errors="replace")[:2000]
    except Exception:
        pass
    imports = ""
    try:
        if ranked:
            p = Path(root) / ranked[0]["filepath"]
            text = p.read_text(errors="replace")
            imports = " ".join(__import__("re").findall(r"(?:from|import)\s+([\w\.]+)", text))
    except Exception:
        pass
    hint = _knowledge.select_hints(query, code0, imports)
    lines.append("HINTS:")
    lines.append(hint)
    try:
        import json
        json.dump({"files": files, "tests": [s["filepath"] for s in tests]},
                  open("/tmp/swe_state.json", "w"))
    except Exception:
        pass
    return cap("\n".join(lines))


def do_inspect(args):
    root = args.root or _default_root()
    sym = args.symbol or ""
    v, err = watchdog(40, _index.twins, root, sym)
    if err:
        return "STATUS: DEGRADED\nwatchdog timeout"
    lines = ["STATUS: OK"]
    for kind, s in v:
        lines.append("{}: {} ({}:{})".format(kind, s["qualname"], s["filepath"], s["start_line"]))
    if not v:
        lines.append("no related symbols")
    return cap("\n".join(lines))


def do_verify(args):
    root = args.root or _default_root()
    v, err = watchdog(180, _verify.verify, args.test, root)
    if err:
        return "STATUS: DEGRADED\nwatchdog timeout"
    status = "STATUS: OK"
    if "SYNTAX ERRORS" in v or "TIMEOUT" in v:
        status = "STATUS: PARTIAL"
    return cap(status + "\n" + v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?")
    ap.add_argument("--query")
    ap.add_argument("--symbol")
    ap.add_argument("--test")
    ap.add_argument("--root")
    args, unknown = ap.parse_known_args()
    cmd = args.cmd
    if cmd == "locate":
        print(do_locate(args))
    elif cmd == "inspect":
        print(do_inspect(args))
    elif cmd == "verify":
        print(do_verify(args))
    else:
        print("STATUS: OK\nusage: swe.py locate|inspect|verify")


if __name__ == "__main__":
    main()

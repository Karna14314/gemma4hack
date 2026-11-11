import argparse
import atexit
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import _guard
import _index
import _verify

def _cleanup():
    # Safe cleanup: only remove temporary swe-toolkit caches/ephemeral files, never arbitrary user directories
    swe_tmp = Path("/workspace/.swe_tmp")
    if swe_tmp.is_dir():
        shutil.rmtree(swe_tmp, ignore_errors=True)

atexit.register(_cleanup)

#: Hard cap at <= 3,500 chars to avoid spiking prompt tokens toward the 14,336
#: ADK history compaction cliff.
OUT_CAP = 3500
CAP_HEAD = 1400
EXCERPT_CHARS = 1400
SNIPPET_CHARS = 240
SNIPPET_LINES = 6


def _default_root():
    if os.path.isdir("/workspace"):
        return "/workspace"
    return os.getcwd()


def cap(s):
    """Respect OUT_CAP without destroying the contract lines.

    `STATUS:` opens the block and `NEXT:`/`TEST:`/`FALLBACK:` close it, so
    truncating from the end deletes exactly the lines the agent must obey.
    Cut the middle instead: keep the first CAP_HEAD chars and the tail up to
    OUT_CAP, with a marker in between.
    """
    if len(s) <= OUT_CAP:
        return s
    marker = "\n...[truncated {} chars]...\n".format(len(s) - OUT_CAP)
    tail_keep = OUT_CAP - CAP_HEAD - len(marker) - 10
    return s[:CAP_HEAD] + marker + s[len(s) - tail_keep:]


def _read_lines(root, relpath):
    try:
        text = (Path(root) / relpath).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    return text.splitlines()


def _slice(lines, start_line, max_lines, max_chars, lead=12, width=120):
    if not lines:
        return ""
    start = max(0, (start_line or 1) - 1 - lead)
    out = []
    used = 0
    for i in range(start, min(len(lines), start + max_lines)):
        line = lines[i].rstrip()
        if len(line) > width:
            line = line[: width - 3] + "..."
        entry = "{:5d} | {}".format(i + 1, line)
        if used + len(entry) > max_chars:
            break
        out.append(entry)
        used += len(entry) + 1
    return "\n".join(out)


def _pick_test(test_paths, source_path):
    """Choose the test module most likely to exercise the top-ranked source file.

    The raw BM25 ranking puts `docs_src/.../test_main.py` first on fastapi, which
    is never the test to run. Match on the module name instead: `pkg/_compat/v2.py`
    should suggest `tests/test_compat.py`, not the highest-scoring test file.
    """
    if not test_paths:
        return None
    stop = {"src", "lib", "app", "main", "init", "py", "tests", "test", "conftest"}
    source = source_path.replace("\\", "/").lower()
    parts = source.rsplit("/", 1)
    stem = parts[-1].rsplit(".", 1)[0]
    parent = parts[0].rsplit("/", 1)[-1] if len(parts) > 1 else ""
    source_tokens = {
        t
        for t in re.findall(r"[a-z0-9]+", stem + " " + parent)
        if len(t) > 1 and t not in stop
    }
    best = None
    best_score = -99.0
    for fp in test_paths[:400]:
        low = fp.replace("\\", "/").lower()
        name = low.rsplit("/", 1)[-1]
        test_stem = name.rsplit(".", 1)[0]
        name_tokens = {
            t for t in re.findall(r"[a-z0-9]+", test_stem) if t not in stop
        }
        score = 3.0 * len(source_tokens & name_tokens)
        if test_stem == "test_" + stem:
            score += 6.0
        if low.startswith("tests/") or "/tests/" in low:
            score += 1.5
        if "docs_src" in low:
            score -= 4.0
        if "scripts/" in low:
            score -= 1.0
        if score > best_score:
            best, best_score = fp, score
    return best


def _search_term(query):
    """The most specific literal a `git grep` fallback should use."""
    for pattern in (r"`([^`]{3,60})`", r'"([^"]{3,60})"'):
        found = re.findall(pattern, query)
        if found:
            return found[0].strip()
    idents = re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", query)
    skip = {
        "the", "this", "that", "when", "with", "from", "have", "should", "would",
        "there", "which", "about", "error", "issue", "problem", "code", "test",
    }
    for ident in idents:
        if ident.lower() not in skip:
            return ident
    return ""


def do_locate(args):
    root = args.root or _default_root()
    query = args.query or getattr(args, "issue", None) or ""
    top_n = int(getattr(args, "top", None) or 5)
    budget = float(getattr(args, "budget", None) or _index.LOCATE_BUDGET_SECONDS)
    stats = {}
    deadline = _guard.deadline_after(budget)
    value, err = _guard.run(
        budget + 5, _index.locate, root, query, top_n, deadline, stats
    )
    if value is None:
        term = _search_term(query)
        return cap(
            "STATUS: DEGRADED\nlocate failed: {}\n"
            "FALLBACK: git grep -n \"{}\" -- '*.py' | head -20".format(err, term)
        )
    ranked, files, tests = value
    if not files:
        term = _search_term(query)
        return cap(
            "STATUS: EMPTY\nno python files indexed under {}\n"
            "FALLBACK: git grep -n \"{}\" -- '*.py' | head -20".format(root, term)
        )

    status = "STATUS: PARTIAL" if stats.get("truncated") else "STATUS: OK"
    header = "{}  (indexed {}/{} files in {:.1f}s)".format(
        status,
        stats.get("files_indexed", 0),
        stats.get("files_found", 0),
        stats.get("seconds", 0.0),
    )
    lines = [header, "TOP FILES:"]
    for i, fp in enumerate(files, 1):
        lines.append("  {}. {}".format(i, fp))

    top_symbol = None
    for sym in ranked:
        if sym["filepath"] == files[0]:
            top_symbol = sym
            break
    symbol_line = max(1, (top_symbol or {}).get("start_line") or 1)
    lines.append(
        "NEXT: read_file {} offset={} limit=60".format(
            files[0], max(1, symbol_line - 10)
        )
    )
    chosen_test = _pick_test(stats.get("test_paths", []), files[0])
    if chosen_test:
        lines.append("TEST: python -m pytest {} -x -q".format(chosen_test))
    else:
        lines.append("TEST: no test module matched; run one `python -c` assertion")
    term = _search_term(query)
    if term:
        lines.append("FALLBACK: git grep -n \"{}\" -- '*.py' | head -20".format(term))

    lines.append("")
    lines.append("--- 1. {} ---".format(files[0]))
    lines.append(
        _slice(_read_lines(root, files[0]), symbol_line, 40, EXCERPT_CHARS)
    )
    for i, fp in enumerate(files[1:], 2):
        start = 1
        for sym in ranked:
            if sym["filepath"] == fp:
                start = sym.get("start_line") or 1
                break
        lines.append("--- {}. {} ---".format(i, fp))
        lines.append(
            _slice(_read_lines(root, fp), start, SNIPPET_LINES, SNIPPET_CHARS, lead=0)
        )
    return cap("\n".join(lines))


#: One line per related symbol is enough; a popular symbol has hundreds of
#: callers and the list would crowd out everything else.
INSPECT_PER_KIND = 6


def do_inspect(args):
    root = args.root or _default_root()
    sym = args.symbol or ""
    value, err = _guard.run(40, _index.twins, root, sym)
    if err:
        return "STATUS: DEGRADED\ninspect failed: {}".format(err)
    if not value:
        return cap(
            "STATUS: EMPTY\nno symbol named {}\n"
            "NEXT: git grep -n \"{}\" -- '*.py' | head -20".format(sym, sym)
        )
    counts = {}
    shown = {}
    order = []
    lines = ["STATUS: OK"]
    for kind, s in value:
        counts[kind] = counts.get(kind, 0) + 1
        if kind not in order:
            order.append(kind)
        if shown.get(kind, 0) >= INSPECT_PER_KIND:
            continue
        shown[kind] = shown.get(kind, 0) + 1
        lines.append(
            "{}: {} ({}:{})".format(
                kind, s["qualname"], s["filepath"], s["start_line"]
            )
        )
    for kind in order:
        hidden = counts[kind] - shown.get(kind, 0)
        if hidden > 0:
            lines.append("  ... {} more {}".format(hidden, kind))
    target = value[0][1]
    lines.append(
        "NEXT: read_file {} offset={} limit=60".format(
            target["filepath"], max(1, (target.get("start_line") or 1) - 5)
        )
    )
    return cap("\n".join(lines))


def do_verify(args):
    root = args.root or _default_root()
    value, err = _guard.run(180, _verify.verify, args.test, root)
    if err:
        return (
            "STATUS: PARTIAL\nverify exceeded its 180s budget: {}\n"
            "NEXT: rerun with a narrower -k filter, or `python -c` the assertion"
        ).format(err)
    # `_verify.verify` already prints its own STATUS/NEXT contract.
    return cap(value)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?")
    ap.add_argument("--query", "--issue", dest="query")
    ap.add_argument("--symbol")
    ap.add_argument("--test")
    ap.add_argument("--root")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--budget", type=float, default=None)
    args, unknown = ap.parse_known_args()
    cmd = args.cmd
    if not args.query and unknown:
        args.query = " ".join(unknown)
    if args.query:
        args.query = args.query.strip("'\"` \t\r\n")
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

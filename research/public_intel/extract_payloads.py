"""Extract the submission payload (FILES dict / zip members) from pulled public notebooks.

Read-only. Writes one directory per kernel under research/public_intel/payloads/<slug>/
containing every member the notebook would write into submission.zip, plus a meta.json.

The notebooks are untrusted public data. Nothing here executes notebook code. A tiny
expression evaluator handles only literals, names bound in the tracked namespace,
`dict(x)`, `json.loads(<constant>)`, and subscript assignment. Anything else is ignored,
so an exotic notebook yields a partial or empty payload rather than a wrong one.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PULLED = ROOT / "pulled"
OUT = ROOT / "payloads"

DICT_NAME = re.compile(r"(FILES|BUNDLE|PAYLOAD|.*_FILES|FILE_SETS|.*_DICT)$", re.IGNORECASE)


def _safe_eval(node: ast.AST, ns: dict):
    """Evaluate a restricted expression. Returns (ok, value)."""
    if isinstance(node, ast.Constant):
        return True, node.value
    if isinstance(node, ast.Name):
        return (node.id in ns), ns.get(node.id)
    if isinstance(node, ast.Dict):
        d = {}
        for k, v in zip(node.keys, node.values):
            ok_k, kv = _safe_eval(k, ns)
            ok_v, vv = _safe_eval(v, ns)
            if not (ok_k and ok_v):
                return False, None
            d[kv] = vv
        return True, d
    if isinstance(node, ast.List):
        out = []
        for elt in node.elts:
            ok, v = _safe_eval(elt, ns)
            if not ok:
                return False, None
            out.append(v)
        return True, out
    if isinstance(node, ast.Tuple):
        ok, lst = _safe_eval(ast.List(elts=node.elts, ctx=ast.Load()), ns)
        return ok, tuple(lst) if ok else None
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id == "dict" and not node.keywords:
            if len(node.args) == 0:
                return True, {}
            if len(node.args) == 1:
                ok, v = _safe_eval(node.args[0], ns)
                if ok and isinstance(v, dict):
                    return True, dict(v)
                return False, None
            return False, None
        if (
            isinstance(fn, ast.Attribute)
            and fn.attr == "loads"
            and isinstance(fn.value, ast.Name)
            and fn.value.id == "json"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Constant)
        ):
            try:
                return True, json.loads(node.args[0].value)
            except Exception:
                return False, None
        if (
            isinstance(fn, ast.Attribute)
            and fn.attr == "update"
            and isinstance(fn.value, ast.Name)
            and fn.value.id in ns
            and isinstance(ns[fn.value.id], dict)
            and len(node.args) == 1
        ):
            ok, v = _safe_eval(node.args[0], ns)
            if ok and isinstance(v, dict):
                ns[fn.value.id] = {**ns[fn.value.id], **v}
                return True, None
            return False, None
    if isinstance(node, ast.Subscript):
        ok_b, base = _safe_eval(node.value, ns)
        ok_s, sl = _safe_eval(node.slice, ns)
        if ok_b and ok_s and isinstance(base, dict):
            return (sl in base), base.get(sl)
        return False, None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        ok_l, l = _safe_eval(node.left, ns)
        ok_r, r = _safe_eval(node.right, ns)
        if ok_l and ok_r and isinstance(l, str) and isinstance(r, str):
            return True, l + r
        return False, None
    if isinstance(node, ast.JoinedStr):
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(str(v.value))
            elif isinstance(v, ast.FormattedValue):
                ok, val = _safe_eval(v.value, ns)
                if not ok:
                    return False, None
                parts.append(str(val))
            else:
                return False, None
        return True, "".join(parts)
    return False, None


def interpret(cell_src: str, ns: dict) -> None:
    try:
        tree = ast.parse(cell_src)
    except SyntaxError:
        return
    _exec_body(tree.body, ns)


def _exec_body(body, ns: dict) -> None:
    for stmt in body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            tgt = stmt.targets[0]
            ok, val = _safe_eval(stmt.value, ns)
            if not ok:
                continue
            if isinstance(tgt, ast.Name):
                ns[tgt.id] = val
            elif isinstance(tgt, ast.Subscript):
                ok_b, base = _safe_eval(tgt.value, ns)
                ok_s, sl = _safe_eval(tgt.slice, ns)
                if ok_b and ok_s and isinstance(base, dict):
                    base[sl] = val
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            ok, val = _safe_eval(stmt.value, ns)
            if ok and (DICT_NAME.match(stmt.target.id) or isinstance(val, dict)):
                ns[stmt.target.id] = val
        elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Subscript):
            ok_b, base = _safe_eval(stmt.target.value, ns)
            ok_s, sl = _safe_eval(stmt.target.slice, ns)
            ok_v, v = _safe_eval(stmt.value, ns)
            if ok_b and ok_s and ok_v and isinstance(base, dict) and isinstance(v, str) and isinstance(base.get(sl), str):
                base[sl] = base[sl] + v
        elif isinstance(stmt, ast.For):
            ok_iter, it = _safe_eval(stmt.iter, ns)
            if ok_iter and isinstance(it, (list, tuple)):
                for item in it:
                    if isinstance(stmt.target, ast.Name):
                        ns[stmt.target.id] = item
                    elif isinstance(stmt.target, ast.Tuple) and isinstance(item, tuple):
                        for t, v in zip(stmt.target.elts, item):
                            if isinstance(t, ast.Name):
                                ns[t.id] = v
                    _exec_body(stmt.body, ns)
        elif isinstance(stmt, ast.If):
            ok_t, tv = _safe_eval(stmt.test, ns)
            if ok_t:
                _exec_body(stmt.body if tv else stmt.orelse, ns)


def _flatten_variants(ns: dict):
    """Expand `FILE_SETS = {'baseline': {...}, 'combined': {...}}` into ns entries."""
    selected = ns.get("SELECTED_VARIANT") or ns.get("selected_variant")
    for name in list(ns):
        val = ns[name]
        if not isinstance(val, dict):
            continue
        inner = [v for v in val.values() if isinstance(v, dict)]
        if len(inner) >= 2 and any(any(k.endswith("agent.yaml") for k in v) for v in inner):
            for k, v in val.items():
                ns[f"{name}[{k}]"] = v
            if isinstance(selected, str) and selected in val:
                ns["__SELECTED__"] = val[selected]


def pick_payload(ns: dict):
    """Pick the most plausible submission payload dict from the namespace."""
    _flatten_variants(ns)
    if "__SELECTED__" in ns:
        return "__SELECTED__", ns["__SELECTED__"]
    candidates = []
    for name, val in ns.items():
        if not isinstance(val, dict):
            continue
        if name.startswith("__"):
            continue
        strs = [v for v in val.values() if isinstance(v, str)]
        if not strs:
            continue
        keys = [k for k in val if isinstance(k, str)]
        score = 0
        if any(k.endswith("agent.yaml") for k in keys):
            score += 100
        if any("system" in k.lower() or "prompt" in k.lower() for k in keys):
            score += 40
        if any(k.endswith("sampling.yaml") for k in keys):
            score += 30
        if any(k.endswith("eval_config.yaml") for k in keys):
            score += 20
        score += len(val)
        candidates.append((score, name, val))
    if not candidates:
        return None, None
    candidates.sort(key=lambda t: -t[0])
    return candidates[0][1], candidates[0][2]


def extract_kernel(dirpath: Path) -> dict:
    ipynb = next(p for p in dirpath.iterdir() if p.suffix == ".ipynb")
    nb = json.loads(ipynb.read_text(encoding="utf-8"))
    meta = json.loads((dirpath / "kernel-metadata.json").read_text(encoding="utf-8"))

    ns: dict = {}
    zip_cell = None
    digest_re = re.compile(r"([0-9a-f]{12,64})")
    found_digest = None
    for i, c in enumerate(nb.get("cells", [])):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        if not src.strip():
            continue
        interpret(src, ns)
        if "submission.zip" in src and ("writestr" in src or "ZipFile" in src):
            zip_cell = {"cell": i, "src": src}
        if "EXPECTED_DIGEST" in src and not found_digest:
            m = digest_re.search(src.split("EXPECTED_DIGEST")[1][:200])
            if m:
                found_digest = m.group(1)

    name, files = pick_payload(ns)
    files = {k: v for k, v in files.items() if isinstance(v, str)} if files else {}
    outdir = OUT / dirpath.name
    outdir.mkdir(parents=True, exist_ok=True)
    for fname, text in files.items():
        p = outdir / fname
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="")

    prompt_chars = None
    for k, v in files.items():
        if "system" in k.lower() or "prompt" in k.lower():
            prompt_chars = len(v)
            break

    meta_out = {
        "kernel": dirpath.name,
        "title": meta.get("title"),
        "ref": f'{meta.get("id", "").split("/")[0]}/{meta.get("title")}' if meta.get("id") else dirpath.name,
        "payload_var": name,
        "digest": found_digest,
        "members": sorted(files.keys()),
        "member_count": len(files),
        "total_bytes": sum(len(v) for v in files.values()),
        "zip_cell": zip_cell["cell"] if zip_cell else None,
        "prompt_chars": prompt_chars,
    }
    (outdir / "meta.json").write_text(json.dumps(meta_out, indent=2), encoding="utf-8")
    return meta_out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in sorted(PULLED.iterdir()):
        if not d.is_dir():
            continue
        try:
            rows.append(extract_kernel(d))
        except Exception as e:  # noqa: BLE001
            rows.append({"kernel": d.name, "error": f"{type(e).__name__}: {e}"})
    print(f"{'kernel':<62} {'members':>7} {'bytes':>8} {'prompt':>7}  digest")
    for r in rows:
        if r.get("error"):
            print(f"{r['kernel']:<62} ERROR {r['error']}")
            continue
        print(
            f"{r['kernel']:<62} {r['member_count']:>7} {r['total_bytes']:>8} "
            f"{str(r['prompt_chars']):>7}  {r.get('digest') or '-'}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

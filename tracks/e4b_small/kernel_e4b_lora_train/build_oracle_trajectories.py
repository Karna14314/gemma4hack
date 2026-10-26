"""Build oracle-guided SFT trajectories from the competition's public tasks.

Runs 100% offline (no external APIs). Emits one JSON object per task with an
OpenAI-style ``messages`` list; assistant turns carry the tool calls, so the
training kernel can apply the official gemma-4-e4b-it chat template and mask
labels to assistant tokens only (labels=-100 elsewhere).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
from pathlib import Path

STRATA_KEYS = ("fastapi", "rich", "requests", "httpx")


def find_tasks(explicit=None):
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("TASKS_JSONL")
    if env:
        candidates.append(Path(env))
    candidates += [
        Path("published/tasks.jsonl"),
        Path("/kaggle/input/competitions/gemma-4-developer-agent/tasks.jsonl"),
        Path("/kaggle/input/gemma-4-developer-agent/tasks.jsonl"),
        Path("/tmp/published/tasks.jsonl"),
    ]
    for c in candidates:
        if c and c.is_file():
            return c
    return None


def stratum_of(task):
    repo = (task.get("repo") or task.get("repository") or "").lower()
    for k in STRATA_KEYS:
        if k in repo:
            return k
    # fallback: infer from task id / problem statement
    text = (task.get("problem_statement") or task.get("issue") or "").lower()
    for k in STRATA_KEYS:
        if k in text:
            return k
    return "other"


def make_split(tasks, train_n=100, val_n=29, seed=42):
    rng = random.Random(seed)
    groups = {}
    for t in tasks:
        groups.setdefault(stratum_of(t), []).append(t)
    train, val = [], []
    for g, items in groups.items():
        items = sorted(items, key=lambda x: x.get("id") or x.get("task_id") or "")
        rng.shuffle(items)
        # proportional allocation
        n = len(items)
        n_train = round(n * train_n / (train_n + val_n))
        n_train = min(n_train, n)
        train.extend(items[:n_train])
        val.extend(items[n_train:])
    # adjust to exact counts if rounding drifted
    rng.shuffle(train)
    rng.shuffle(val)
    while len(train) > train_n and val:
        val.insert(0, train.pop())
    while len(val) > val_n and train:
        train.insert(0, val.pop())
    # if not enough, pad from the larger
    while len(train) < train_n and len(val) > 0:
        train.append(val.pop(0))
    while len(val) < val_n and len(train) > train_n:
        val.append(train.pop())
    return train, val


def save_split(path, train, val):
    obj = {
        "train_ids": [t.get("id") or t.get("task_id") for t in train],
        "val_ids": [t.get("id") or t.get("task_id") for t in val],
        "train_count": len(train),
        "val_count": len(val),
        "strata": {},
    }
    for t in train:
        obj["strata"].setdefault(stratum_of(t), {"train": 0, "val": 0})
        obj["strata"][stratum_of(t)]["train"] += 1
    for t in val:
        obj["strata"].setdefault(stratum_of(t), {"train": 0, "val": 0})
        obj["strata"][stratum_of(t)]["val"] += 1
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    return obj


def parse_patch(patch):
    files = []
    cur = None
    for line in (patch or "").splitlines():
        if line.startswith("--- "):
            p = line[4:].strip()
            if p.startswith("a/"):
                p = p[2:]
            if p == "/dev/null":
                p = None
            cur = {"path": p, "hunks": []}
            files.append(cur)
        elif line.startswith("@@") and cur is not None:
            m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)", line)
            if m:
                cur["hunks"].append({"old_start": int(m.group(1)), "new_start": int(m.group(2)), "lines": []})
        elif cur is not None and cur["hunks"]:
            if line.startswith("+") and not line.startswith("+++"):
                cur["hunks"][-1]["lines"].append(("add", line[1:]))
            elif line.startswith("-") and not line.startswith("---"):
                cur["hunks"][-1]["lines"].append(("del", line[1:]))
            elif line.startswith(" "):
                cur["hunks"][-1]["lines"].append(("ctx", line[1:]))
            elif line.startswith("\\"):
                pass
    # drop None paths
    return [f for f in files if f["path"]]


def extract_symbols(patch):
    syms = []
    for m in re.finditer(r"^[+-].*\b(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", patch or "", re.M):
        s = m.group(1)
        if s not in syms:
            syms.append(s)
    return syms


def hunk_texts(hunk):
    old = [t for kind, t in hunk["lines"] if kind in ("ctx", "del")]
    new = [t for kind, t in hunk["lines"] if kind in ("ctx", "add")]
    return "\n".join(old), "\n".join(new)


def build_trajectory(task):
    tid = task.get("id") or task.get("task_id") or "task"
    problem = task.get("problem_statement") or task.get("issue") or task.get("description") or ""
    patch = task.get("patch") or task.get("gold_patch") or ""
    files = parse_patch(patch)
    # pick first changed file with a hunk
    chosen = None
    for f in files:
        if f["hunks"]:
            chosen = f
            break
    if chosen is None:
        chosen = {"path": "src/main.py", "hunks": [{"old_start": 1, "new_start": 1, "lines": []}]}
    fpath = chosen["path"]
    hunk = chosen["hunks"][0]
    L = max(1, hunk["old_start"])
    old_text, new_text = hunk_texts(hunk)
    if not old_text.strip():
        old_text = "# (no context)"
    if not new_text.strip():
        new_text = old_text
    syms = extract_symbols(patch)
    sym = syms[0] if syms else (problem.split()[:1] or ["bug"])[0]
    sym = re.sub(r"[^A-Za-z0-9_]", "", sym) or "target"
    fix_desc = f"fix {sym} in {fpath}"

    read_start = max(1, L - 20)
    read_end = L + 35

    state = lambda step: f"STATE: {fpath}:{L} | {fix_desc} | {step}"

    messages = []
    # system minimal (optional)
    messages.append({"role": "system", "content": "You are an autonomous software engineer. Make the smallest correct change."})
    messages.append({"role": "user", "content": problem})

    # Turn 1 localization
    messages.append({
        "role": "assistant",
        "content": f"<think>Bug likely in {sym} in {fpath}; localize with grep.</think>\n{state('locate')}",
        "tool_calls": [{"type": "function", "function": {"name": "run_command",
            "arguments": json.dumps({"command": f"git --no-pager grep -n \"{sym}\" -- ':!tests/*'"})}}],
    })
    messages.append({"role": "tool", "content": f"{fpath}:{L}: {sym}"})

    # Turn 2 surgical read
    messages.append({
        "role": "assistant",
        "content": f"<think>Read the exact hunk before editing.</think>\n{state('locate')}",
        "tool_calls": [{"type": "function", "function": {"name": "read_file",
            "arguments": json.dumps({"file_path": fpath, "start_line": read_start, "end_line": read_end})}}],
    })
    messages.append({"role": "tool", "content": old_text})

    # Turn 3 exact edit
    messages.append({
        "role": "assistant",
        "content": f"<think>Apply the gold fix: replace the buggy hunk with the corrected version.</think>\n{state('edit')}",
        "tool_calls": [{"type": "function", "function": {"name": "edit_file",
            "arguments": json.dumps({"file_path": fpath, "old_string": old_text, "new_string": new_text})}}],
    })
    messages.append({"role": "tool", "content": "Successfully edited file."})

    # Turn 4 verify + submit
    messages.append({
        "role": "assistant",
        "content": f"<think>Syntax-check and run targeted tests.</think>\n{state('verify')}",
        "tool_calls": [{"type": "function", "function": {"name": "run_command",
            "arguments": json.dumps({"command": f"python3 -m py_compile {fpath} && timeout 60 pytest -q 2>&1 | tail -n 80"})}}],
    })
    messages.append({"role": "tool", "content": "py_compile ok; tests passed"})

    messages.append({
        "role": "assistant",
        "content": f"<think>Pre-submit integrity check.</think>\n{state('verify')}",
        "tool_calls": [{"type": "function", "function": {"name": "run_command",
            "arguments": json.dumps({"command": "git checkout -- tests/ test/ testing/ conftest.py 2>/dev/null; git status --short && git --no-pager diff --stat"})}}],
    })
    messages.append({"role": "tool", "content": f"M {fpath}"})

    messages.append({
        "role": "assistant",
        "content": f"<think>Submit the patch.</think>\n{state('submit')}",
        "tool_calls": [{"type": "function", "function": {"name": "submit_patch", "arguments": json.dumps({})}}],
    })
    messages.append({"role": "tool", "content": "patch_size > 0, files_changed: 1"})

    return {"task_id": tid, "messages": messages}


def try_tokenize(records, tokenizer_name):
    try:
        from transformers import AutoTokenizer
    except Exception as e:
        print(f"[tokenize] transformers unavailable: {e}")
        return records
    try:
        tok = AutoTokenizer.from_pretrained(tokenizer_name)
    except Exception as e:
        print(f"[tokenize] could not load tokenizer {tokenizer_name}: {e}")
        return records
    out = []
    for r in records:
        try:
            rendered = tok.apply_chat_template(
                r["messages"], tokenize=True, return_dict=True,
                return_assistant_tokens_mask=True, add_generation_prompt=False,
            )
            ids = rendered["input_ids"]
            mask = rendered.get("assistant_masks") or rendered.get("assistant_tokens_mask")
            if mask is None:
                raise RuntimeError("no assistant mask returned")
            labels = [int(x) if int(m) == 1 else -100 for x, m in zip(ids, mask)]
            r = dict(r)
            r["input_ids"] = [int(x) for x in ids]
            r["labels"] = labels
            r["tokenizer"] = tokenizer_name
        except Exception as e:
            print(f"[tokenize] failed for {r['task_id']}: {e}")
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=None)
    ap.add_argument("--split", default=None, help="path to split json (loaded or created)")
    ap.add_argument("--out", default="oracle_trajectories.jsonl")
    ap.add_argument("--train-only", action="store_true", default=True)
    ap.add_argument("--tokenizer", default="google/gemma-4-e4b-it")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    tasks_path = find_tasks(args.tasks)
    if tasks_path is None:
        raise SystemExit("tasks.jsonl not found; pass --tasks or set TASKS_JSONL")
    tasks = [json.loads(x) for x in tasks_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    print(f"loaded {len(tasks)} tasks from {tasks_path}")

    # split
    split_path = Path(args.split) if args.split else Path(__file__).resolve().parent / "split_100_29.json"
    if split_path.is_file():
        try:
            sp = json.loads(split_path.read_text(encoding="utf-8"))
            idset = set(sp.get("train_ids", []))
            if idset:
                train_tasks = [t for t in tasks if (t.get("id") or t.get("task_id")) in idset]
            else:
                train_tasks = None
        except Exception:
            train_tasks = None
    else:
        train_tasks = None

    if train_tasks is None:
        train, val = make_split(tasks, 100, 29, args.seed)
        save_split(split_path, train, val)
        train_tasks = train
        print(f"created split: {len(train)} train / {len(val)} val -> {split_path}")

    print(f"building trajectories for {len(train_tasks)} train tasks")
    records = [build_trajectory(t) for t in train_tasks]

    records = try_tokenize(records, args.tokenizer)

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} trajectories to {out_path}")


if __name__ == "__main__":
    main()

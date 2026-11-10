"""Fetch the live Gemma 4 public leaderboard via bearer auth (Kaggle REST).

Reuses the same bearer-token scheme as tools/kaggle_rest.py (KAGGLE_KEY / 
KAGGLE_API_TOKEN as Authorization: Bearer) because the kaggle CLI uses basic
auth and 401s on the KGAT_ token installed in this container.

Writes: research/direction_checks/leaderboard_live.json
        research/direction_checks/leaderboard_live.csv
"""
from __future__ import annotations

import csv
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://www.kaggle.com"
OUT = Path(__file__).resolve().parent.parent / "direction_checks"
OUT.mkdir(parents=True, exist_ok=True)


def token() -> str:
    t = os.environ.get("KAGGLE_KEY") or os.environ.get("KAGGLE_API_TOKEN")
    if not t:
        import json as _j
        p = Path(os.path.expanduser("~/.kaggle/kaggle.json"))
        if p.is_file():
            t = _j.loads(p.read_text()).get("key")
    if not t:
        raise SystemExit("no bearer token (KAGGLE_KEY/KAGGLE_API_TOKEN/kaggle.json)")
    return t


def get(path: str):
    url = path if path.startswith("http") else BASE + path
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token()}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main() -> int:
    status, body = get(
        "/api/v1/competitions/gemma-4-developer-agent/leaderboard/view"
    )
    print(f"leaderboard/view -> HTTP {status} ({len(body)} bytes)")
    if status >= 400:
        print(body.decode("utf-8", "replace")[:2000])
        return 1
    data = json.loads(body)
    (OUT / "leaderboard_live.json").write_text(json.dumps(data, indent=2))
    rows = data if isinstance(data, list) else data.get("submissions", [])
    csv_path = OUT / "leaderboard_live.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        if rows and isinstance(rows[0], dict):
            w.writerow(rows[0].keys())
            for r in rows:
                w.writerow(r.values())
    print(f"wrote {csv_path} ({len(rows)} rows)")
    for r in rows[:12]:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

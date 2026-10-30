"""Verify that the Kaggle competition resources this repo depends on exist.

Run with the Python that has the ``kaggle`` package installed (the system
interpreter, not ``.venv-harness``)::

    python tools/check_resources.py
    python tools/check_resources.py --refresh     # re-download the small files
    python tools/check_resources.py --no-download # inventory only

The script checks, against the live Kaggle API:

* authentication works;
* the competition exposes the file groups the harness documentation describes
  (``tasks.jsonl``, ``snapshots/``, ``graphs/``, ``embeddings/``, ``wheels/``,
  ``sample_submission/``, ``docker/``, ``sandbox/`` and ``HARNESS_README.md``);
* the public dev set still has the expected task count and repo mix;
* the wheelhouse dataset still carries the three wheels the verifier needs;
* the paper-track competition is reachable;
* the account's recent submissions and their statuses.

Small public files (``HARNESS_README.md``, ``tasks.jsonl``) are cached under
``kaggle_work/gemma-4-developer-agent/research/competition/``. ``tasks.jsonl``
is gitignored; re-download it with ``--refresh``.

Exit code is 0 when every required resource is present, 1 otherwise. Recorded
hashes are a staleness detector, not a hard requirement: a changed file produces
``[WARN]`` so a future session knows to re-read the docs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "kaggle_work" / "gemma-4-developer-agent" / "research" / "competition"

COMPETITION = "gemma-4-developer-agent"
PAPER_COMPETITION = "gemma-4-developer-agent-paper"
WHEELHOUSE = "metric/gemma-4-developer-agent-wheelhouse"
WHEELHOUSE_DATASET_URL = f"https://www.kaggle.com/datasets/{WHEELHOUSE}"

REQUIRED_WHEELS = (
    "swegemma-0.2.11-py3-none-any.whl",
    "adk_submission-0.2.13-py3-none-any.whl",
    "adk_eval_core-0.1.0-py3-none-any.whl",
)

# Minimum counts observed on 2026-10-30. Exact files must exist exactly once.
REQUIRED_GROUPS: dict[str, int] = {
    "HARNESS_README.md": 1,
    "tasks.jsonl": 1,
    "snapshots/": 100,
    "graphs/": 100,
    "embeddings/": 100,
    "wheels/": 100,
    "sample_submission/": 1,
    "docker/": 1,
    "sandbox/": 1,
}

# Snapshot recorded on 2026-10-30. A mismatch is a warning, not a failure.
EXPECTED_FILES: dict[str, tuple[int, str]] = {
    "HARNESS_README.md": (
        55_940,
        "445000219b803942c469391ec8b69791a31e9cec2f934738c767e34b5ca0aa1f",
    ),
    "tasks.jsonl": (
        1_984_455,
        "e4b3fd60f69dbc2b9213e54eeb9636db78aefe92c1d06269d73d9f5f8f3c8ad6",
    ),
}

FAILURES: list[str] = []
WARNINGS: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {label}" + (f" :: {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)


def warn(label: str, detail: str = "") -> None:
    print(f"[WARN] {label}" + (f" :: {detail}" if detail else ""))
    WARNINGS.append(label)


def info(label: str) -> None:
    print(f"[INFO] {label}")


def human_bytes(value: int) -> str:
    if value >= 2**30:
        return f"{value / 2**30:.1f} GiB"
    if value >= 2**20:
        return f"{value / 2**20:.1f} MiB"
    if value >= 2**10:
        return f"{value / 2**10:.1f} KiB"
    return f"{value} B"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def make_api():
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as error:
        raise SystemExit(
            "the `kaggle` package is not importable. Run this script with the "
            "system Python that has the Kaggle CLI installed, or `pip install kaggle`."
        ) from error
    api = KaggleApi()
    try:
        api.authenticate()
    except Exception as error:  # noqa: BLE001
        raise SystemExit(
            "Kaggle authentication failed. Set KAGGLE_API_TOKEN (preferred) or "
            "KAGGLE_USERNAME + KAGGLE_KEY, or write ~/.kaggle/kaggle.json.\n"
            f"underlying error: {type(error).__name__}: {error}"
        ) from error
    return api


def list_paged(fetch, **kwargs) -> list:
    """Walk every page of a Kaggle list endpoint."""
    items = []
    token = None
    for _ in range(100):
        response = fetch(page_token=token, page_size=200, **kwargs)
        items.extend(response.files)
        token = response.next_page_token
        if not token:
            break
    else:
        raise SystemExit("pagination did not terminate after 100 pages")
    return items


def ensure_file(api, competition: str, name: str, refresh: bool) -> Path | None:
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / name
    if target.is_file() and not refresh:
        return target
    try:
        api.competition_download_file(
            competition, name, path=str(CACHE), force=True, quiet=True
        )
    except Exception as error:  # noqa: BLE001
        warn(f"could not download {name}", f"{type(error).__name__}: {error}")
        return target if target.is_file() else None
    return target if target.is_file() else None


def check_competition_files(api) -> list:
    print(f"\n=== competition files: {COMPETITION} ===")
    try:
        files = list_paged(
            lambda **kw: api.competition_list_files(COMPETITION, **kw)
        )
    except Exception as error:  # noqa: BLE001
        check("list competition files", False, f"{type(error).__name__}: {error}")
        return []
    check("list competition files", True, f"{len(files)} files")

    names = [item.name for item in files]
    counts = Counter()
    for name in names:
        for prefix in REQUIRED_GROUPS:
            if prefix.endswith("/"):
                if name.startswith(prefix):
                    counts[prefix] += 1
            elif name == prefix:
                counts[prefix] += 1

    for prefix, minimum in REQUIRED_GROUPS.items():
        found = counts[prefix]
        check(
            f"resource group {prefix}",
            found >= minimum,
            f"{found} files (minimum {minimum})",
        )

    for name, (expected_size, expected_hash) in EXPECTED_FILES.items():
        matches = [item for item in files if item.name == name]
        if not matches:
            check(f"snapshot file {name}", False, "missing")
            continue
        size = int(matches[0].total_bytes)
        check(
            f"snapshot file {name}",
            size == expected_size,
            f"{human_bytes(size)} ({size:,d} bytes)",
        )
        if size != expected_size:
            warn(
                f"{name} changed size",
                f"recorded {expected_size:,d}; re-read the live file before relying on old notes",
            )
    return names


def check_public_devset(api, refresh: bool) -> None:
    print("\n=== public dev set (tasks.jsonl) ===")
    path = ensure_file(api, COMPETITION, "tasks.jsonl", refresh)
    if path is None or not path.is_file():
        check("tasks.jsonl is available", False, "download failed")
        return

    size = path.stat().st_size
    digest = sha256(path)
    check("tasks.jsonl is available", True, f"{human_bytes(size)} ({size:,d} bytes)")
    expected = EXPECTED_FILES["tasks.jsonl"]
    if (size, digest) != expected:
        warn(
            "tasks.jsonl differs from the 2026-10-30 snapshot",
            f"sha256 {digest[:16]}…; the public dev set may have been updated",
        )
    else:
        info(f"tasks.jsonl sha256 matches the 2026-10-30 snapshot ({digest[:16]}…)")

    try:
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except Exception as error:  # noqa: BLE001
        check("tasks.jsonl parses as JSONL", False, f"{type(error).__name__}: {error}")
        return

    check("tasks.jsonl parses as JSONL", True, f"{len(rows)} tasks")
    repos = Counter(str(row.get("repo", "?")) for row in rows)
    info("repo mix: " + ", ".join(f"{repo}={count}" for repo, count in repos.most_common()))
    ids = {str(row.get("instance_id", "")) for row in rows}
    check("task ids are unique", len(ids) == len(rows), f"{len(ids)} unique ids")
    keys = set(rows[0]) if rows else set()
    for key in ("instance_id", "repo", "problem_statement", "patch", "test_patch"):
        check(f"task field {key}", key in keys)


def check_harness_readme(api, refresh: bool) -> None:
    print("\n=== harness documentation ===")
    path = ensure_file(api, COMPETITION, "HARNESS_README.md", refresh)
    if path is None or not path.is_file():
        check("HARNESS_README.md is available", False, "download failed")
        return
    size = path.stat().st_size
    digest = sha256(path)
    check("HARNESS_README.md is available", True, f"{human_bytes(size)} ({size:,d} bytes)")
    expected_size, expected_hash = EXPECTED_FILES["HARNESS_README.md"]
    if (size, digest) != (expected_size, expected_hash):
        warn(
            "HARNESS_README.md differs from the 2026-10-30 snapshot",
            f"sha256 {digest[:16]}…; re-read it before relying on ckpt/HARNESS_README.md",
        )
    else:
        info(f"HARNESS_README.md sha256 matches the snapshot ({digest[:16]}…)")


def check_wheelhouse(api) -> None:
    print(f"\n=== wheelhouse dataset: {WHEELHOUSE} ===")
    info(WHEELHOUSE_DATASET_URL)
    try:
        files = list_paged(
            lambda **kw: api.dataset_list_files(WHEELHOUSE, **kw)
        )
    except Exception as error:  # noqa: BLE001
        check("list wheelhouse files", False, f"{type(error).__name__}: {error}")
        return
    check("list wheelhouse files", True, f"{len(files)} files")
    total = sum(int(getattr(item, "total_bytes", 0) or 0) for item in files)
    info(f"total size: {human_bytes(total)}")

    names = {item.name for item in files}
    for wheel in REQUIRED_WHEELS:
        check(f"wheel {wheel}", wheel in names)


def check_paper_track(api) -> None:
    print(f"\n=== paper track: {PAPER_COMPETITION} ===")
    try:
        files = list_paged(
            lambda **kw: api.competition_list_files(PAPER_COMPETITION, **kw)
        )
    except Exception as error:  # noqa: BLE001
        check("list paper-track files", False, f"{type(error).__name__}: {error}")
        return
    check("list paper-track files", True, f"{len(files)} files")
    for item in files:
        info(f"  {item.name} ({human_bytes(int(item.total_bytes))})")
    if not any(item.name.upper().startswith("NOTE") for item in files):
        warn("paper track has no NOTE.md", "check the competition page for submission mechanics")


def check_submissions(api) -> None:
    print(f"\n=== recent submissions: {COMPETITION} ===")
    try:
        submissions = api.competition_submissions(COMPETITION)
    except Exception as error:  # noqa: BLE001
        warn("list submissions", f"{type(error).__name__}: {error}")
        return
    if not submissions:
        info("no submissions on this account")
        return
    for item in submissions[:8]:
        score = getattr(item, "public_score", None)
        try:
            score_text = "-" if score in (None, "") else f"{float(score):.2f}"
        except (TypeError, ValueError):
            score_text = str(score)
        description = (item.description or "")[:90]
        info(
            f"  {item.ref}  {str(item.date)[:10]}  {item.status}  "
            f"public={score_text}  {description}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="re-download the cached public files even when present",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="inventory only; do not download missing files",
    )
    args = parser.parse_args()

    api = make_api()
    check("Kaggle authentication", True, "credentials accepted")

    check_competition_files(api)
    if not args.no_download:
        check_public_devset(api, args.refresh)
        check_harness_readme(api, args.refresh)
    else:
        info("--no-download: skipped tasks.jsonl and HARNESS_README.md checks")
    check_wheelhouse(api)
    check_paper_track(api)
    check_submissions(api)

    print("\n" + "=" * 70)
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S):")
        for label in FAILURES:
            print(f"  - {label}")
        return 1
    if WARNINGS:
        print(f"all required resources present; {len(WARNINGS)} warning(s)")
    else:
        print("all required resources present")
    return 0


if __name__ == "__main__":
    sys.exit(main())

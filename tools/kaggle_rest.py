"""Minimal Kaggle REST client for the operations this project needs.

Why this exists instead of the ``kaggle`` CLI: the installed CLI is 1.7.4.5, the
newest version on this box's package index, and it authenticates with HTTP Basic
auth. The account's ``KGAT_...`` token is only accepted as a ``Bearer`` token, so
every authenticated CLI call fails with ``401 Unauthorized`` while anonymous calls
(public dataset downloads) appear to work and quietly succeed. Rather than fight
that, this speaks the same REST endpoints directly using bearer auth.

The request bodies mirror ``kagglesdk``'s serialised types field-for-field, so
this is the official client with the one thing that actually broken swapped out.

Only the standard library is used, so it runs under any interpreter.

Usage::

    python tools/kaggle_rest.py push    kaggle_work/.../exp01_submission_notebook
    python tools/kaggle_rest.py status  narisettichaitanya/gemma4-devagent-exp01
    python tools/kaggle_rest.py output  narisettichaitanya/gemma4-devagent-exp01 runs/exp01
    python tools/kaggle_rest.py get     narisettichaitanya/gemma4-devagent-exp01
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://www.kaggle.com"


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


def credentials() -> tuple[str, str]:
    """Return ``(username, token)`` from the environment or ``kaggle.json``.

    ``KAGGLE_API_TOKEN`` is the bearer token written by newer Kaggle CLI
    versions (``KGAT_...``). ``KAGGLE_KEY`` and ``kaggle.json`` are the legacy
    forms. Only the token is required: every REST call below sends it as
    ``Authorization: Bearer``, and the username is never used on the wire.
    """
    username = os.environ.get("KAGGLE_USERNAME")
    token = os.environ.get("KAGGLE_KEY") or os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        path = Path(os.path.expanduser("~/.kaggle/kaggle.json"))
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            username = username or data.get("username")
            token = token or data.get("key")
    if not token:
        raise SystemExit(
            "no Kaggle credentials: set KAGGLE_API_TOKEN (preferred) or "
            "KAGGLE_KEY, or write ~/.kaggle/kaggle.json"
        )
    return username or "", token


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------


def request(
    method: str,
    path: str,
    body: dict | None = None,
    accept: str = "application/json",
    raw: bool = False,
) -> tuple[int, bytes, str]:
    url = path if path.startswith("http") else BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {credentials()[1]}")
    req.add_header("Accept", accept)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            payload = response.read()
            return response.status, payload, response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as error:
        return error.code, error.read(), error.headers.get("Content-Type", "")
    except urllib.error.URLError as error:
        raise SystemExit(f"network error calling {url}: {error}") from error


def request_form(
    method: str,
    path: str,
    fields: dict,
    accept: str = "application/json",
) -> tuple[int, bytes, str]:
    """POST multipart/form-data.

    `ApiCreateCodeSubmissionRequest` is one of the requests kagglesdk marks as
    form-encoded (`REQUESTS_REQUIRING_FORMS`). A JSON body is accepted by the
    route but every field is ignored, and the server then answers "This
    competition requires an output FileName for Notebook Submissions" no matter
    what was sent — a misleading error that looks like a payload problem.
    """
    url = path if path.startswith("http") else BASE + path
    boundary = f"----kagglehack{os.urandom(12).hex()}"
    parts: list[bytes] = []
    for name, value in fields.items():
        if value is None:
            continue
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8")
        )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {credentials()[1]}")
    req.add_header("Accept", accept)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.status, response.read(), response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as error:
        return error.code, error.read(), error.headers.get("Content-Type", "")
    except urllib.error.URLError as error:
        raise SystemExit(f"network error calling {url}: {error}") from error


def call_json(method: str, path: str, body: dict | None = None) -> dict:
    status, payload, _ = request(method, path, body)
    text = payload.decode("utf-8", "replace")
    if status >= 400:
        raise SystemExit(f"{method} {path} -> HTTP {status}\n{text[:2000]}")
    try:
        return json.loads(text) if text.strip() else {}
    except json.JSONDecodeError:
        return {"_raw": text}


# ---------------------------------------------------------------------------
# Kernel helpers
# ---------------------------------------------------------------------------


def slugify(title: str) -> str:
    """Mirror the slug the Kaggle website derives from a kernel title."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug


def split_ref(ref: str) -> tuple[str, str]:
    if "/" not in ref:
        raise SystemExit(f"expected owner/slug, got {ref!r}")
    owner, slug = ref.split("/", 1)
    return owner, slug


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_push(folder: Path) -> int:
    metadata_path = folder / "kernel-metadata.json"
    if not metadata_path.is_file():
        raise SystemExit(f"missing {metadata_path}")
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))

    code_path = folder / meta["code_file"]
    script = code_path.read_text(encoding="utf-8")

    if meta.get("kernel_type") == "notebook":
        # The server expects one string per cell and no saved outputs.
        document = json.loads(script)
        for cell in document.get("cells", []):
            if cell.get("cell_type") == "code":
                cell["outputs"] = []
            if isinstance(cell.get("source"), list):
                cell["source"] = "".join(cell["source"])
        script = json.dumps(document)

    ref = meta.get("id")
    if not ref:
        raise SystemExit("kernel-metadata.json needs an 'id' of owner/slug")
    owner, slug = split_ref(ref)
    title = meta.get("title", "")

    if slugify(title) != slug.lower():
        print(
            f"WARNING: title {title!r} slugifies to {slugify(title)!r}, "
            f"but the id says {slug!r}. Kaggle will use the id."
        )

    def flag(name: str, default: bool) -> bool:
        value = meta.get(name, default)
        return value if isinstance(value, bool) else str(value).lower() == "true"

    body = {
        # These are the camelCase json names kagglesdk serialises, not the
        # python attribute names. Sending `kernel_type` instead of `kernelType`
        # silently drops the field and the server rejects the run.
        #
        # `id` is the numeric kernel id and is omitted for a new kernel; the
        # owner/slug reference travels in `slug`, exactly as the official client
        # does.
        "slug": ref,
        "newTitle": title,
        "text": script,
        "language": meta.get("language", "python"),
        "kernelType": meta.get("kernel_type", "notebook"),
        "isPrivate": flag("is_private", True),
        "enableGpu": flag("enable_gpu", False),
        "enableTpu": flag("enable_tpu", False),
        "enableInternet": flag("enable_internet", False),
        "datasetDataSources": meta.get("dataset_sources", []),
        "competitionDataSources": meta.get("competition_sources", []),
        "kernelDataSources": meta.get("kernel_sources", []),
        "modelDataSources": meta.get("model_sources", []),
        "categoryIds": meta.get("keywords", []),
    }
    # kagglesdk names these fields *_data_sources on the wire, but the CLI reads
    # the friendlier names from kernel-metadata.json.
    for meta_key, body_key in (
        ("dataset_sources", "dataset_data_sources"),
        ("competition_sources", "competition_data_sources"),
        ("kernel_sources", "kernel_data_sources"),
        ("model_sources", "model_data_sources"),
    ):
        if meta_key in meta and not isinstance(meta[meta_key], list):
            raise SystemExit(f"{meta_key} must be a list")

    attached = [
        name
        for name, key in (
            ("dataset_sources", "datasetDataSources"),
            ("kernel_sources", "kernelDataSources"),
            ("model_sources", "modelDataSources"),
        )
        if body[key]
    ]
    if attached:
        # The notebook genuinely needs no dataset, kernel or model input: it only
        # builds a zip from inlined strings. An attached source would make the run
        # depend on data the organizers may not have available, and internet is
        # off. (A competition source is allowed: the competition demands it, even
        # though the notebook never reads the data.)
        raise SystemExit(
            f"this notebook must attach no dataset/kernel/model sources, but found {attached}"
        )

    result = call_json("POST", "/api/v1/kernels/push", body)
    print(json.dumps(result, indent=2)[:2000])
    version = result.get("kernel_version") or result.get("versionNumber")
    if version is None:
        print("NOTE: no version number in the response; check with 'status'.")
    else:
        print(f"\npushed {owner}/{slug} version {version}")
    return 0


def cmd_status(ref: str) -> int:
    owner, slug = split_ref(ref)
    # kagglesdk serialises GET requests as query parameters, not a JSON body.
    result = call_json(
        "GET",
        f"/api/v1/kernels/status?userName={owner}&kernelSlug={slug}",
    )
    print(json.dumps(result, indent=2)[:2000])
    return 0


def cmd_get(ref: str) -> int:
    owner, slug = split_ref(ref)
    result = call_json("GET", f"/api/v1/kernels/pull?userName={owner}&kernelSlug={slug}")
    print(json.dumps(result, indent=2)[:3000])
    return 0


def cmd_output(ref: str, dest: Path) -> int:
    owner, slug = split_ref(ref)
    dest.mkdir(parents=True, exist_ok=True)

    # Ask for the file listing first: it is the cheapest way to see what the run
    # actually produced, and it tells us whether the run even finished.
    listing = call_json(
        "GET",
        f"/api/v1/kernels/output?userName={owner}&kernelSlug={slug}&pageSize=200",
    )
    print("output listing:")
    print(json.dumps(listing, indent=2)[:4000])

    status, payload, _ = request(
        "GET",
        f"/api/v1/kernels/output/download/{owner}/{slug}",
        accept="application/zip",
    )
    if status >= 400:
        raise SystemExit(
            f"GET output -> HTTP {status}\n{payload.decode('utf-8', 'replace')[:1000]}"
        )
    archive = dest / "output.zip"
    archive.write_bytes(payload)
    print(f"\nwrote {archive} ({len(payload):,d} bytes)")

    import zipfile

    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)
        for name in sorted(zf.namelist()):
            print(f"  {name}")
    return 0


def cmd_submit(
    competition: str, kernel_ref: str, version: str, filename: str, message: str
) -> int:
    """Submit a kernel to a code competition.

    Mirrors ``kaggle competitions submit -c C -k owner/slug -v N -f name -m msg``.
    For a code competition ``filename`` is the *name of the output file the
    kernel produces*, not a local path: the graders read the kernel's output.
    """
    owner, slug = split_ref(kernel_ref)
    body = {
        "competitionName": competition,
        "kernelOwner": owner,
        "kernelSlug": slug,
        "kernelVersion": int(version),
        "fileName": filename,
        "submissionDescription": message,
    }
    status, payload, _ = request_form(
        "POST", f"/api/v1/competitions/submissions/submit-notebook/{competition}", body
    )
    text = payload.decode("utf-8", "replace")
    if status >= 400:
        raise SystemExit(
            f"submit-notebook -> HTTP {status}\n{text[:2000]}"
        )
    result = json.loads(text) if text.strip() else {}
    print(json.dumps(result, indent=2)[:2000])
    print(f"\nsubmitted {competition} from {kernel_ref} version {version}")
    return 0


def cmd_submissions(competition: str) -> int:
    result = call_json(
        "GET", f"/api/v1/competitions/submissions/list/{competition}?page=1"
    )
    # The list is longer than it looks: every entry carries ~15 nullable mirror
    # fields. Truncating the print silently hid the newest entries, which is how a
    # failed submission went unnoticed. Print the whole page.
    print(json.dumps(result, indent=2)[:400000])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    push = sub.add_parser("push", help="push a kernel directory")
    push.add_argument("folder", type=Path)

    status = sub.add_parser("status", help="kernel run status")
    status.add_argument("ref")

    get = sub.add_parser("get", help="kernel metadata")
    get.add_argument("ref")

    output = sub.add_parser("output", help="download kernel output")
    output.add_argument("ref")
    output.add_argument("dest", type=Path)

    submit = sub.add_parser("submit", help="submit a kernel to a code competition")
    submit.add_argument("--competition", required=True)
    submit.add_argument("--kernel", required=True, help="owner/slug")
    submit.add_argument("--version", required=True)
    submit.add_argument("--filename", default="submission.zip")
    submit.add_argument("--message", default="")

    submissions = sub.add_parser("submissions", help="list competition submissions")
    submissions.add_argument("competition")

    args = parser.parse_args()
    if args.command == "push":
        return cmd_push(args.folder)
    if args.command == "status":
        return cmd_status(args.ref)
    if args.command == "get":
        return cmd_get(args.ref)
    if args.command == "output":
        return cmd_output(args.ref, args.dest)
    if args.command == "submit":
        return cmd_submit(
            args.competition, args.kernel, args.version, args.filename, args.message
        )
    if args.command == "submissions":
        return cmd_submissions(args.competition)
    return 1


if __name__ == "__main__":
    sys.exit(main())
"""Push a directory to a Kaggle dataset over REST with bearer auth.

Why this exists instead of ``kaggle datasets create/version``: the installed CLI (1.7.4.5)
authenticates with HTTP Basic, and this account's ``KGAT_`` token is only accepted as a
``Bearer`` token, so every authenticated CLI call returns 401 while anonymous calls keep
working and make the CLI look healthy.

The upload protocol is the one ``kaggle.cli.KaggleApi`` implements, reproduced here:

1. ``POST /api/v1/blobs/upload`` with ``{type, name, content_length,
   last_modified_epoch_seconds}`` -> ``{token, create_url}``.
2. ``PUT`` the raw bytes to ``create_url`` (a GCS resumable session). No Kaggle auth; the
   URL is already a capability.
3. ``POST /api/v1/datasets/create/new`` (first time) or
   ``POST /api/v1/datasets/create/version/{owner}/{slug}``, with one ``{"token": ...}``
   entry per uploaded file.

Note the create/version bodies are form-encoded, because ``kagglesdk`` marks those request
types as form-encoded; posting them as JSON is silently accepted and every field is
dropped.

Usage:
    python3 tools/kaggle_ckpt.py create  <dir> <owner>/<slug> <title> <notes>
    python3 tools/kaggle_ckpt.py version <dir> <owner>/<slug> <notes>
    python3 tools/kaggle_ckpt.py pull   <owner>/<slug> <dest_dir>
"""

import io
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kaggle_rest as kr  # noqa: E402

# ApiBlobType: UNSPECIFIED=0, DATASET=1, MODEL=2, INBOX=3
BLOB_TYPE_DATASET = 1
SKIP_NAMES = {
    'dataset-metadata.json',
    'kernel-metadata.json',
    'old-dataset-metadata.json',
    'model-metadata.json',
}
# Never ship local venvs, caches or prior checkpoints into the checkpoint itself.
SKIP_DIRS = {'.git', '.venv-harness', '.harness', '__pycache__', '.verify_build', 'ckpt'}
MAX_FILE_BYTES = 100 * 1024 * 1024


def plan_(folder: Path) -> list[tuple[str, Path]]:
    """Return ``(upload_name, local_path)`` pairs, one per blob.

    A dataset version is a *flat* list of blobs: ``ApiDatasetNewFile`` carries only a
    token, no path. Uploading ``src/sections/00_header.py`` under the basename
    ``00_header.py`` therefore collides with any other same-named file and the create
    call fails with "Path must be unique". This mirrors what ``kaggle datasets create
    --dir-mode zip`` does: top-level directories are uploaded as a single ``<name>.zip``
    blob, which also keeps the upload to one blob per subtree.
    """
    plan: list[tuple[str, Path]] = []
    for entry in sorted(folder.iterdir()):
        if entry.name in SKIP_NAMES or entry.name in SKIP_DIRS:
            continue
        if entry.is_symlink():
            continue
        if entry.is_dir():
            members = [
                path
                for path in sorted(entry.rglob('*'))
                if path.is_file()
                and not path.is_symlink()
                and path.suffix != '.pyc'
                and '__pycache__' not in path.relative_to(entry).parts
            ]
            if not members:
                continue
            archive = folder / f'.{entry.name}.zip.tmp'
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
                for path in members:
                    bundle.write(path, path.relative_to(entry).as_posix())
            plan.append((f'{entry.name}.zip', archive))
        elif entry.is_file():
            if entry.stat().st_size > MAX_FILE_BYTES:
                raise SystemExit(f'refusing to upload oversized file: {entry.name}')
            plan.append((entry.name, entry))
    return plan


def upload_blob(name: str, path: Path) -> str:
    """Reserve a blob, PUT the bytes to the returned URL, return the opaque token."""
    data = path.read_bytes()
    content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    # ApiStartBlobUploadRequest is NOT in kagglesdk's REQUESTS_REQUIRING_FORMS list, so
    # this one is a plain JSON body.
    body = {
        'type': BLOB_TYPE_DATASET,
        'name': name,
        'contentType': content_type,
        'contentLength': len(data),
        'lastModifiedEpochSeconds': int(os.path.getmtime(path)),
    }
    response = kr.call_json('POST', '/api/v1/blobs/upload', body)
    create_url = response['createUrl']

    upload = urllib.request.Request(
        create_url,
        data=data,
        method='PUT',
        headers={
            'Content-Type': content_type,
            'Content-Length': str(len(data)),
            'X-Goog-Upload-Command': 'upload, finalize',
        },
    )
    try:
        with urllib.request.urlopen(upload, timeout=300) as result:
            result.read()
    except urllib.error.HTTPError as error:
        raise SystemExit(f'blob PUT failed for {name}: HTTP {error.code} {error.read()[:400]}')
    return response['token']


def upload_all(folder: Path) -> list[dict]:
    plan = plan_(folder)
    if not plan:
        raise SystemExit(f'no files to upload in {folder}')
    names = [name for name, _ in plan]
    if len(names) != len(set(names)):
        raise SystemExit(f'internal error: duplicate upload names {names}')
    entries = []
    for name, path in plan:
        token = upload_blob(name, path)
        entries.append({'token': token})
        print(f'  uploaded {name} ({path.stat().st_size:,} bytes)')
    for name, path in plan:
        if path.name.endswith('.zip.tmp'):
            path.unlink()
    return entries


def split_ref(ref: str) -> tuple[str, str]:
    if '/' not in ref:
        raise SystemExit(f'ref must be owner/slug, got {ref!r}')
    owner, slug = ref.split('/', 1)
    return owner, slug


def do_create(folder: Path, ref: str, title: str, notes: str) -> None:
    owner, slug = split_ref(ref)
    print(f'creating dataset {ref}')
    entries = upload_all(folder)
    body = {
        'ownerSlug': owner,
        'title': title,
        'slug': slug,
        'licenseName': 'other',
        'isPrivate': True,
        'files': entries,
    }
    response = kr.call_json('POST', '/api/v1/datasets/create/new', body)
    print(json.dumps(response, indent=2)[:1200])


def do_version(folder: Path, ref: str, notes: str) -> None:
    owner, slug = split_ref(ref)
    print(f'new version of {ref}')
    entries = upload_all(folder)
    body = {
        'versionNotes': notes,
        'files': entries,
        'isPrivate': True,
        'deleteOldVersions': False,
    }
    response = kr.call_json(
        'POST', f'/api/v1/datasets/create/version/{owner}/{slug}', body
    )
    print(json.dumps(response, indent=2)[:1200])


def do_pull(ref: str, dest: Path) -> None:
    owner, slug = split_ref(ref)
    dest.mkdir(parents=True, exist_ok=True)
    stream = urllib.request.Request(
        f'https://www.kaggle.com/api/v1/datasets/download/{owner}/{slug}',
        method='GET',
    )
    token = kr.credentials()[1]
    stream.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(stream, timeout=600) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        archive.extractall(dest)
    # Directories were uploaded as `<name>.zip` blobs, so expand them in place.
    for nested in sorted(dest.glob('*.zip')):
        target = dest / nested.stem
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(nested) as bundle:
            bundle.extractall(target)
        nested.unlink()
    print(f'extracted {len(payload):,} bytes into {dest}')


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    action = sys.argv[1]
    if action == 'create':
        folder, ref, title, notes = sys.argv[2:6]
        do_create(Path(folder), ref, title, notes)
    elif action == 'version':
        folder, ref, notes = sys.argv[2:5]
        do_version(Path(folder), ref, notes)
    elif action == 'pull':
        ref, dest = sys.argv[2:4]
        do_pull(ref, Path(dest))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
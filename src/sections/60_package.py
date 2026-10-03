"""Section 60 — packaging, manifest and final report.

Writes ``submission.zip`` and ``submission_manifest.json``. Every step is
individually guarded, and a final emergency path writes a minimal archive directly
if the shared packager failed for any reason. The closing assertion is the only
intentional failure mode in the whole notebook: a missing artifact must be loud.
"""

INTRO = """\
## Package

`pack()` validates once more, then serialises deterministically: files sorted by
path, directory entries omitted, timestamps pinned, so an unchanged package always
produces a byte-identical archive. It also re-reads its own output and checks every
member round-trips exactly, that there are no directory entries, and that
`agent.yaml` sits at the archive root.
"""

PACK = '''\
SUBMISSION_PATH = WORKING / "submission.zip"
MANIFEST_PATH = WORKING / "submission_manifest.json"
submission_bytes = None

try:
    submission_bytes = pack(SELECTED_FILES)
except Exception:  # noqa: BLE001 - never let packaging abort the notebook
    print("pack() failed, falling back to a direct minimal archive:")
    print(traceback.format_exc())

if submission_bytes is None:
    # Emergency path: bypass the shared packager entirely. Deterministic, minimal,
    # and known to satisfy every harness limit.
    emergency = {
        "agent.yaml": (
            "name: swe_coder\\n"
            "model: gemma-4-31b-it-qat-w4a16-ct\\n"
            "description: Autonomous software engineer that fixes one repository issue.\\n"
            "instruction: You fix one issue in the Python repository at /workspace. "
            "Work with your tools until a minimal source fix is in place, then call "
            "submit_patch(). The working tree is graded even if you never call it, so "
            "never revert a fix you believe in. Never edit test files or pyproject.toml; "
            "they are reset before grading. Find the cause with git grep, confirm it by "
            "reading a narrow line range, make the smallest edit that fixes the reported "
            "behaviour, check it with python3 -m py_compile, and redirect any long "
            "output to /tmp with run_command so you can tail it. Submit before your "
            "budget runs out; a best guess beats no patch.\\n"
            "{problem_description}\\n"
        ),
    }
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for _path in sorted(emergency):
            _info = zipfile.ZipInfo(_path, date_time=(1980, 1, 1, 0, 0, 0))
            _info.compress_type = zipfile.ZIP_DEFLATED
            _info.create_system = 3
            _info.external_attr = 0o644 << 16
            archive.writestr(_info, emergency[_path].encode("utf-8"))
    submission_bytes = stream.getvalue()

SUBMISSION_PATH.write_bytes(submission_bytes)
print(f"wrote {SUBMISSION_PATH} ({len(submission_bytes):,d} bytes)")
'''

MANIFEST = '''\
# A manifest makes the artifact auditable after the fact: what was chosen, why,
# what is inside, and the digest that pins the exact bytes being submitted.
try:
    with zipfile.ZipFile(SUBMISSION_PATH) as archive:
        members = {}
        for name in archive.namelist():
            raw = archive.read(name)
            members[name] = {
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        corrupt = archive.testzip()

    manifest = {
        "submission": SUBMISSION_PATH.name,
        "selected_package": SELECTED_NAME,
        "selection_reason": SELECTION_REASON,
        "submission_sha256": digest(submission_bytes),
        "submission_bytes": len(submission_bytes),
        "zip_crc_check": "clean" if corrupt is None else f"corrupt member {corrupt}",
        "members": members,
        "model": MODEL,
        "adapters": [n for n in SELECTED_FILES if n.startswith("adapters/")],
        "unpacked_bytes": sum(len(v.encode("utf-8")) for v in SELECTED_FILES.values()),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {MANIFEST_PATH}")
except Exception:  # noqa: BLE001
    print("manifest could not be written (it is advisory only):")
    print(traceback.format_exc())
'''

REPORT = '''\
# Final report. Reading the artifact back from disk is the last line of defence:
# these assertions check the file that actually exists, not the bytes in memory.
with zipfile.ZipFile(SUBMISSION_PATH) as archive:
    names = archive.namelist()
    assert archive.testzip() is None, "the written archive is corrupt"
    assert "agent.yaml" in names, "agent.yaml is not at the archive root"
    assert not any(n.endswith("/") for n in names), "the archive has directory entries"
    assert len(names) == len(set(names)), "the archive has duplicate names"
    for name in names:
        assert archive.read(name).decode("utf-8") == SELECTED_FILES[name], (
            f"{name} did not round trip byte-identically"
        )

print()
print("=" * 68)
print(f"  selected package : {SELECTED_NAME}")
print(f"  reason           : {SELECTION_REASON}")
print(f"  archive          : {SUBMISSION_PATH.name}  ({len(submission_bytes):,d} bytes)")
print(f"  sha256           : {digest(submission_bytes)}")
print(f"  members          : {len(names)}")
for name in names:
    print(f"      {name}")
print("=" * 68)
print("submission.zip is written and verified")
'''

CLOSING = """\
### Done

`/kaggle/working/submission.zip` holds a declarative ADK agent package that the
organizers can compile. It declares a single model, ships no adapters, respects the
3 GiB and extension limits, and has a valid `agent.yaml` at its root.
"""


def cells() -> list[dict]:
    return [
        {"cell_type": "markdown", "source": INTRO},
        {"cell_type": "code", "source": PACK},
        {"cell_type": "code", "source": MANIFEST},
        {"cell_type": "code", "source": REPORT},
        {"cell_type": "markdown", "source": CLOSING},
    ]
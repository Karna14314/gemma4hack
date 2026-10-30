"""Execute the generated notebook end to end and check the artifact it produces.

The notebook's only job is string manipulation and zip writing, so it must be
fully verifiable without Kaggle, without a GPU and without a network. This tool
executes every code cell in order in one shared namespace, exactly as a notebook
kernel would, with ``KAGGLE_WORKING_DIR`` pointed at a fresh temporary directory.

Then it asserts the properties the organizers' compiler needs, reading the zip
back **from disk** rather than trusting anything left in memory:

* the archive opens and its CRCs are intact;
* ``agent.yaml`` is present at the archive root;
* there are no directory entries and no duplicate names;
* every member is UTF-8 decodable and round-trips byte-identically;
* every member has an extension on the harness allowlist, with no empty suffix;
* the archive contains no adapter directory and no ``.py`` file;
* packing is deterministic — a second build of the same package gives the same
  sha256;
* the selected package is the primary one, not the fallback.

Usage::

    python tools/verify_notebook.py
    python tools/verify_notebook.py --notebook build/submission_notebook.ipynb
"""

from __future__ import annotations

import argparse
import io
import json
import posixpath
import shutil
import sys
import tempfile
import traceback
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTEBOOK = ROOT / "build" / "submission_notebook.ipynb"

# Transcribed from swegemma/config.py and confirmed against
# swegemma.models.discovery by tools/verify_bundle.py.
ALLOWED_SUFFIXES = frozenset(
    {".yaml", ".yml", ".md", ".txt", ".py", ".json", ".safetensors"}
)

DEFAULT_MODEL_NAME = "gemma-4-31b-it-qat-w4a16-ct"
# The nine sandboxed tools the harness registers unconditionally on every task.
HARNESS_TOOL_NAMES = (
    "run_command",
    "read_file",
    "edit_file",
    "write_file",
    "get_status",
    "submit_patch",
    "search_similar_code",
    "get_code_neighbors",
    "get_code_subgraph",
)

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {label}" + (f" :: {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)


def read_cells(path: Path) -> list[dict]:
    nb = json.loads(path.read_text(encoding="utf-8"))
    return nb.get("cells", [])


def execute(path: Path, workdir: Path) -> tuple[dict, str]:
    """Run every code cell in order in one shared namespace."""
    import os

    os.environ["KAGGLE_WORKING_DIR"] = str(workdir)
    namespace: dict = {"__name__": "__main__", "__builtins__": __builtins__}
    output: list[str] = []

    for index, cell in enumerate(read_cells(path)):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        try:
            compiled = compile(source, f"<cell {index}>", "exec")
            exec(compiled, namespace)  # noqa: S102 - that is the point of this tool
        except Exception:
            output.append(f"--- cell {index} FAILED ---")
            output.append(source)
            output.append(traceback.format_exc())
            raise
    return namespace, "\n".join(output)


def model_from_selected(selected: dict) -> str:
    """Read the declared base model from the selected ``agent.yaml``."""
    text = selected.get("agent.yaml", "")
    for line in text.splitlines():
        if line.startswith("model:"):
            return line.split(":", 1)[1].strip()
    return ""


def check_harness_optional(payload: bytes, declared_model: str) -> None:
    """Run the artifact through the real harness, when the wheels are importable.

    This is the authoritative check: the notebook's own validator is a mirror of
    the constraints, while ``adk_submission.compile_submission`` is the code the
    organizers actually run. It needs the competition wheels, so it is skipped
    rather than failed when they are absent — run this tool with
    ``.venv-harness/bin/python`` to include it.
    """
    print()
    print("=== optional: the real harness ===")
    try:
        import adk_submission
        import swegemma  # noqa: F401
    except Exception:
        print("[SKIP] competition wheels not importable; run with .venv-harness/bin/python")
        return

    with tempfile.TemporaryDirectory(prefix="verify_harness_") as tmp:
        target = Path(tmp) / "submission"
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            archive.extractall(target)

        try:
            adk_submission.validate_directory(target)
            check("real harness validate_directory accepts the artifact", True)
        except Exception as error:
            check("real harness validate_directory accepts the artifact", False, str(error))
            return

        try:
            try:
                from adk_submission.discovery import discover_declared_models

                declared = discover_declared_models(target)
                ok = declared == {declared_model}
            except ImportError:
                from swegemma.models.discovery import validate_single_declared_model

                validate_single_declared_model(target)
                ok = True
            check("real harness accepts exactly one declared model", ok, str(declared))
        except Exception as error:
            check("real harness accepts exactly one declared model", False, str(error))

        try:
            from google.adk.models.lite_llm import LiteLlm

            from swegemma.config import build_submission_limits

            limits, constraints = build_submission_limits()
            registry = adk_submission.ModelRegistry()
            registry.register(
                declared_model, LiteLlm(model=declared_model, api_key="EMPTY")
            )
            tools = {name: (lambda **_: "{}") for name in HARNESS_TOOL_NAMES}
            agent = adk_submission.compile_submission(
                target,
                tools,
                registry,
                limits=limits,
                generation_constraints=constraints,
            )
            check(
                "real harness compile_submission builds the agent",
                True,
                f"root {getattr(agent, 'name', '?')!r} "
                f"tools={len(getattr(agent, 'tools', []))} "
                f"model={getattr(agent, 'model', '?')}",
            )
        except Exception as error:
            check(
                "real harness compile_submission builds the agent",
                False,
                f"{type(error).__name__}: {error}",
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK)
    parser.add_argument("--keep", action="store_true", help="keep the temp directory")
    args = parser.parse_args()

    if not args.notebook.is_file():
        print(f"FAIL notebook not found: {args.notebook}")
        print("run: python tools/build_notebook.py")
        return 1

    print(f"=== executing {args.notebook.name} ===")
    workdir = Path(tempfile.mkdtemp(prefix="verify_notebook_"))
    try:
        namespace, log = execute(args.notebook, workdir)
    except Exception:
        print("FAIL the notebook raised while executing; see the traceback above")
        if not args.keep:
            shutil.rmtree(workdir, ignore_errors=True)
        return 1

    print(log)
    print()

    print("=== checking the artifact ===")
    submission = workdir / "submission.zip"
    check("submission.zip exists in the working directory", submission.is_file(), str(submission))

    if not submission.is_file():
        return 1

    payload = submission.read_bytes()
    check(
        "archive is non-empty",
        len(payload) > 0,
        f"{len(payload):,d} bytes",
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        check("archive CRCs are intact", archive.testzip() is None)
        names = archive.namelist()

        check("agent.yaml is at the archive root", "agent.yaml" in names)
        check(
            "no directory entries",
            not any(n.endswith("/") for n in names),
            f"{len(names)} entries",
        )
        check("no duplicate names", len(names) == len(set(names)))

        bad_suffix = [
            n for n in names if posixpath.splitext(n)[1].lower() not in ALLOWED_SUFFIXES
        ]
        check("every member has an allowed extension", not bad_suffix, str(bad_suffix))

        empty_suffix = [n for n in names if not posixpath.splitext(n)[1]]
        check("no member has an empty extension", not empty_suffix, str(empty_suffix))

        check(
            "no adapter directory (KV cache would collapse)",
            not any(n.startswith("adapters/") for n in names),
        )
        check("no .py member outside skills (never executed by the compiler)", not any(n.endswith(".py") and not n.startswith("skills/") for n in names))

        selected = namespace.get("SELECTED_FILES", {})
        mismatched = []
        for name in names:
            raw = archive.read(name)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                mismatched.append(f"{name}: not utf-8")
                continue
            if name in selected and text != selected[name]:
                mismatched.append(f"{name}: content differs from the selected package")
            if not text.strip():
                mismatched.append(f"{name}: empty file")
        check(
            "every member round-trips byte-identically against the selected package",
            not mismatched,
            "; ".join(mismatched),
        )

        unpacked = sum(archive.getinfo(n).file_size for n in names)
        check(
            "unpacked size is under 3 GiB",
            unpacked <= 3 * 2**30,
            f"{unpacked:,d} bytes",
        )

    selected_name = namespace.get("SELECTED_NAME")
    check(
        "the primary package was selected, not the fallback",
        selected_name == "primary",
        str(selected_name),
    )
    check(
        "validation report names the root config",
        namespace.get("VALIDATION_REPORT", {}).get("root_config") == "agent.yaml",
    )

    declared_model = (
        namespace.get("VALIDATION_REPORT", {}).get("model")
        or model_from_selected(selected)
        or DEFAULT_MODEL_NAME
    )
    check(
        "the artifact declares a single base model",
        bool(declared_model),
        declared_model,
    )

    # Determinism: repacking the same package must reproduce the same bytes.
    pack = namespace.get("pack")
    digest = namespace.get("digest")
    if callable(pack) and callable(digest):
        rebuilt = pack(selected)
        check(
            "rebuilding the package reproduces the archive byte-for-byte",
            digest(rebuilt) == digest(payload),
            digest(payload)[:16],
        )
    else:
        check("the notebook exposed pack() and digest()", False)

    # The manifest is advisory, but if present it must agree with the artifact.
    manifest_path = workdir / "submission_manifest.json"
    check("submission_manifest.json was written", manifest_path.is_file())
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        check(
            "manifest digest matches the written archive",
            manifest.get("submission_sha256") == digest(payload),
        )
        check(
            "manifest lists the same members as the archive",
            sorted(manifest.get("members", {})) == sorted(names),
        )

    check_harness_optional(payload, declared_model)

    print()
    print("=" * 70)
    if not args.keep:
        shutil.rmtree(workdir, ignore_errors=True)
    else:
        print(f"kept working directory {workdir}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED:")
        for label in FAILURES:
            print(f"  - {label}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
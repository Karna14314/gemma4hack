"""Local verification of the submission bundle.

Runs three independent layers of checking:

1. the project's own strict static validator (``src/notebook_lib/validator.py``);
2. the real harness, installed from the competition wheels in
   ``.venv-harness`` — ``adk_submission.validate_directory``,
   ``swegemma.config.build_submission_limits``,
   ``swegemma.models.discovery.validate_single_declared_model`` and
   ``adk_submission.compile_submission``;
3. negative tests that prove the validator actually rejects known-bad bundles.

Layer 2 needs the venv interpreter, so re-exec through it when the harness
wheels are not importable from the current one:

    python tools/verify_bundle.py [--bundle PATH]

    .venv-harness\\Scripts\\python tools\\verify_bundle.py   # Windows
    .venv-harness/bin/python tools/verify_bundle.py        # Linux/macOS

``--bundle PATH`` validates any other bundle directory (the ablation
bundles) with the same three layers, instead of the primary
``src/agent_package``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# venv layout differs per platform: Scripts\python.exe on Windows, bin/python elsewhere
_VENV_PYTHON = (
    Path("Scripts") / "python.exe" if os.name == "nt" else Path("bin") / "python"
)
VENV_PYTHON = ROOT / ".venv-harness" / _VENV_PYTHON
HARNESS_READY = {"adk_submission", "swegemma"}


def _reexec_in_harness_venv() -> None:
    """Restart under the venv interpreter when the harness is not importable."""
    import importlib.util

    if any(
        importlib.util.find_spec(name) is None for name in HARNESS_READY
    ) and VENV_PYTHON.is_file():
        raise SystemExit(
            subprocess.call([str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])
        )
    sys.path.insert(0, str(ROOT / "src"))


_reexec_in_harness_venv()

from notebook_lib import package_source, validator  # noqa: E402

PACKAGE_SRC = package_source.PACKAGE_ROOT

MODEL = validator.MODEL
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {label}" + (f" :: {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)


def layer_static(files: dict) -> None:
    print("\n=== 1. project static validator ===")
    for label, bundle in (
        ("primary bundle", files),
        ("fallback bundle", package_source.FALLBACK_FILES),
    ):
        try:
            report = validator.validate(bundle)
            check(
                f"static validate: {label}",
                True,
                f"root={report['root_config']} files={report['file_count']} "
                f"agents={report['agents']} adapters={report['adapters']} "
                f"skills={report['skills']} bytes={report['unpacked_bytes']}",
            )
        except Exception as error:  # noqa: BLE001
            check(f"static validate: {label}", False, f"{type(error).__name__}: {error}")

    # Determinism: packing twice must produce identical bytes.
    payload_a = validator.pack(files)
    payload_b = validator.pack(files)
    check("pack is deterministic", payload_a == payload_b, validator.digest(payload_a)[:16])


def _alias_is_registered(alias: str) -> bool:
    """Ask the harness's own model registry whether it knows our model alias.

    ``swegemma.models.registry.setup_gemma_model_registry`` existed in the
    audited 0.2.7/1.36.1 wheel pair; the current wheels (swegemma 0.2.11,
    adk_submission 0.2.13) ship the model table as data in
    ``adk_eval_core/budget/models.yaml`` instead. Prefer the live function when
    importable, and fall back to that registry file.
    """
    try:
        from swegemma.models.registry import setup_gemma_model_registry
    except Exception:  # noqa: BLE001
        try:
            import importlib.resources as resources

            text = (
                resources.files("adk_eval_core")
                .joinpath("budget/models.yaml")
                .read_text(encoding="utf-8")
            )
        except Exception:  # noqa: BLE001
            return False
        return any(
            line.strip() == f"{alias}:"
            for line in text.splitlines()
            if not line.strip().startswith("#")
        )
    try:
        registry = setup_gemma_model_registry(
            api_base="http://127.0.0.1:9/v1", api_key="EMPTY"
        )
        return alias in registry.list_available()
    except Exception:  # noqa: BLE001
        return False


def _materialise(files: dict, root: Path) -> Path:
    """The real harness reads a submission from disk, so write it out first."""
    import shutil

    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for name, text in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return root


def layer_real_harness(files: dict) -> None:
    print("\n=== 2. real harness (adk_submission / swegemma) ===")
    try:
        from adk_submission import ModelRegistry, compile_submission, validate_directory
        from swegemma.config import (
            ALLOWED_SUBMISSION_EXTENSIONS,
            MAX_SUBMISSION_SIZE_BYTES,
            build_submission_limits,
        )
    except Exception as error:  # noqa: BLE001
        check(
            "import real harness",
            False,
            f"{type(error).__name__}: {error}. Run with "
            f"{VENV_PYTHON} to enable this layer.",
        )
        return
    check("import real harness", True, sys.executable)

    limits, constraints = build_submission_limits()
    check(
        "our transcribed constants match the harness",
        limits.max_total_size_bytes == MAX_SUBMISSION_SIZE_BYTES
        == validator.MAX_TOTAL_SIZE_BYTES
        and limits.max_file_count == validator.MAX_FILE_COUNT
        and limits.max_yaml_files == validator.MAX_YAML_FILES
        and limits.max_yaml_size_bytes == validator.MAX_YAML_SIZE_BYTES
        and limits.max_skill_size_bytes == validator.MAX_SKILL_SIZE_BYTES
        and limits.max_instruction_chars == validator.MAX_INSTRUCTION_CHARS
        and limits.max_total_instruction_chars == validator.MAX_TOTAL_INSTRUCTION_CHARS
        and limits.max_agents == validator.MAX_AGENTS
        and limits.max_sub_agent_depth == validator.MAX_SUB_AGENT_DEPTH
        and limits.max_skills == validator.MAX_SKILLS
        and limits.allowed_file_extensions == validator.ALLOWED_SUFFIXES,
        f"extensions={sorted(limits.allowed_file_extensions)} "
        f"size={limits.max_total_size_bytes} "
        f"output_tokens={constraints.max_output_tokens} "
        f"thinking={constraints.thinking_budget}",
    )
    check(
        "our model alias is registered by the harness",
        _alias_is_registered(MODEL),
        MODEL,
    )
    # A file with no suffix must be rejected: the competition override omits ""
    # from the allowlist, which silently excludes LICENSE, Makefile and friends.
    check(
        "empty extension is rejected by the harness allowlist",
        "" not in limits.allowed_file_extensions
        and "" not in ALLOWED_SUBMISSION_EXTENSIONS,
        f"allowed={sorted(ALLOWED_SUBMISSION_EXTENSIONS)}",
    )

    for label, bundle in (
        ("primary bundle", files),
        ("fallback bundle", package_source.FALLBACK_FILES),
    ):
        directory = _materialise(bundle, ROOT / ".verify_build" / label.split()[0])
        try:
            validate_directory(directory, limits)
            check(f"validate_directory: {label}", True)
        except Exception as error:  # noqa: BLE001
            check(
                f"validate_directory: {label}",
                False,
                f"{type(error).__name__}: {error}",
            )
        try:
            try:
                from adk_submission.discovery import discover_declared_models

                declared = discover_declared_models(directory)
            except ImportError:
                from swegemma.models.discovery import validate_single_declared_model

                declared = validate_single_declared_model(directory)
            check(
                f"single declared model: {label}",
                declared == {MODEL},
                str(declared),
            )
        except Exception as error:  # noqa: BLE001
            check(
                f"single declared model: {label}",
                False,
                f"{type(error).__name__}: {error}",
            )
        try:
            from google.adk.models.lite_llm import LiteLlm

            registry = ModelRegistry()
            registry.register(MODEL, LiteLlm(model=MODEL, api_key="EMPTY"))
            tools = {name: (lambda **_: "{}") for name in validator.HARNESS_TOOLS}
            agent = compile_submission(
                directory,
                tools,
                registry,
                limits=limits,
                generation_constraints=constraints,
            )
            sub_agents = getattr(agent, "sub_agents", None) or []
            check(
                f"compile_submission: {label}",
                True,
                f"root {agent.name!r} model={agent.model!r} "
                f"tools={len(agent.tools)} sub_agents={[a.name for a in sub_agents]} "
                f"output_tokens={agent.generate_content_config.max_output_tokens}",
            )
        except Exception as error:  # noqa: BLE001
            check(
                f"compile_submission: {label}",
                False,
                f"{type(error).__name__}: {error}\n{traceback.format_exc(limit=4)}",
            )


def layer_negative(files: dict) -> None:
    print("\n=== 3. negative tests (the validator must reject) ===")

    def root_name(bundle: dict) -> str:
        text = bundle.get("agent.yaml", "")
        for line in text.splitlines():
            if line.startswith("name:"):
                return line.split(":", 1)[1].strip()
        return ""

    def sub_agent_path(bundle: dict) -> str | None:
        for name, text in bundle.items():
            if name.startswith("sub_agents/") and name.endswith((".yaml", ".yml")):
                return name
        return None

    def mutate(fn) -> dict:
        bundle = dict(files)
        fn(bundle)
        return bundle

    def drop_root(b):
        del b["agent.yaml"]

    def two_roots(b):
        b["root_agent.yaml"] = b["agent.yaml"]

    def bad_ext(b):
        b["extra.bin"] = "nope"

    def traversal(b):
        b["prompts/../escape.md"] = "x"

    def missing_include(b):
        b["agent.yaml"] = b["agent.yaml"].replace(
            "prompts/system.md", "prompts/nothing.md", 1
        )

    def second_model(b):
        b["sub_agents/other.yaml"] = (
            "name: other\nmodel: gemma-4-9b-it\ninstruction: hello\n"
        )
        b["agent.yaml"] = b["agent.yaml"].rstrip("\n") + (
            "\nsub_agents:\n  - config_path: sub_agents/other.yaml\n"
        )

    def adapter_present(b):
        b["adapters/lora/adapter_config.json"] = "{}"
        b["adapters/lora/adapter_model.safetensors"] = ""
        b["agent.yaml"] = b["agent.yaml"].replace(
            "model: " + MODEL, "model: " + MODEL + "\nadapter: lora", 1
        )

    def no_submit(b):
        b["agent.yaml"] = b["agent.yaml"].replace("  - submit_patch\n", "")

    def unknown_tool(b):
        b["agent.yaml"] = b["agent.yaml"].replace(
            "  - run_command", "  - run_command\n  - rm_rf", 1
        )

    def huge_budget(b):
        b["eval_config.yaml"] = "evaluation:\n  max_time_minutes: 30\n"

    def bad_generation_field(b):
        b["configs/sampling.yaml"] = (
            b["configs/sampling.yaml"].rstrip("\n") + "\nsafety_settings: []\n"
        )

    def stray_placeholder(b):
        b["prompts/system.md"] = b["prompts/system.md"] + "\nUse {repo_name}.\n"

    def root_is_subagent_name(b):
        name = root_name(b)
        if not name:
            return
        b["agent.yaml"] = b["agent.yaml"].replace(
            f"name: {name}", "name: code_analyzer", 1
        )

    def escaping_include(b):
        path = sub_agent_path(b)
        if path is None or "../prompts/" not in b[path]:
            return
        b[path] = b[path].replace("../prompts/", "../../outside_", 1)

    def writer_subagent(b):
        path = sub_agent_path(b)
        if path is None or "  - run_command" not in b[path]:
            return
        b[path] = b[path].replace(
            "  - run_command", "  - run_command\n  - edit_file", 1
        )

    def empty_file(b):
        # Empty any included prompt file, so the case also applies to bundles
        # with only one prompt.
        for name in list(b):
            if name.endswith(".md"):
                b[name] = ""
                return


    def has_sub_agent(bundle: dict) -> bool:
        return sub_agent_path(bundle) is not None

    always = lambda bundle: True  # noqa: E731
    cases = [
        ("no root config", drop_root, always),
        ("two root configs", two_roots, always),
        ("disallowed extension", bad_ext, always),
        ("path traversal", traversal, always),
        ("dangling !include", missing_include, always),
        ("two base models", second_model, always),
        ("LoRA adapter present", adapter_present, always),
        ("root without submit_patch", no_submit, always),
        ("unknown tool name", unknown_tool, always),
        ("per-task budget too large", huge_budget, always),
        ("forbidden generation field", bad_generation_field, always),
        ("unknown state placeholder", stray_placeholder, always),
        ("empty file", empty_file, always),
        # These need a sub-agent in the bundle to collide with or escape from;
        # single-agent bundles (the 0.17 public baseline shape) skip them.
        ("!include escaping the root", escaping_include, has_sub_agent),
        ("sub-agent owns a writer tool", writer_subagent, has_sub_agent),
        ("duplicate agent name", root_is_subagent_name, has_sub_agent),
    ]
    for label, fn, applicable in cases:
        if not applicable(files):
            print(f"[SKIP] rejects {label} :: not applicable to this bundle shape")
            continue
        try:
            bundle = mutate(fn)
            validator.validate(bundle)
        except validator.SubmissionInvalid as error:
            check(f"rejects {label}", True, str(error)[:110])
        except Exception as error:  # noqa: BLE001
            check(
                f"rejects {label}",
                False,
                f"raised {type(error).__name__} instead of SubmissionInvalid: {error}",
            )
        else:
            check(f"rejects {label}", False, "validator accepted a broken bundle")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="bundle directory to validate instead of src/agent_package",
    )
    args = parser.parse_args()
    files = package_source.load_from_disk(args.bundle)
    print(f"bundle: {args.bundle or PACKAGE_SRC}")
    print(f"bundle files: {sorted(files)}")
    layer_static(files)
    layer_real_harness(files)
    layer_negative(files)
    print("\n" + "=" * 60)
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
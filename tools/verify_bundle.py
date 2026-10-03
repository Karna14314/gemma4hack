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

    .venv-harness\\Scripts\\python tools\\verify_bundle.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv-harness" / "Scripts" / "python.exe"
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
    """Ask the harness's own Gemma registry whether it knows our model alias."""
    try:
        from swegemma.models.registry import setup_gemma_model_registry
    except Exception:  # noqa: BLE001
        return False
    registry = setup_gemma_model_registry(
        api_base="http://127.0.0.1:9/v1", api_key="EMPTY"
    )
    return alias in registry.list_available()


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
        from swegemma.models.discovery import validate_single_declared_model
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
            declared = validate_single_declared_model(directory)
            check(f"validate_single_declared_model: {label}", True, str(declared))
        except Exception as error:  # noqa: BLE001
            check(
                f"validate_single_declared_model: {label}",
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

    def escaping_include(b):
        b["sub_agents/code_analyzer.yaml"] = (
            b["sub_agents/code_analyzer.yaml"].replace(
                "../prompts/analyzer.md", "../../outside.md"
            )
        )

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

    def writer_subagent(b):
        b["sub_agents/code_analyzer.yaml"] = (
            b["sub_agents/code_analyzer.yaml"]
            .replace("  - run_command", "  - run_command\n  - edit_file")
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
        b["agent.yaml"] = b["agent.yaml"].replace("name: swe_coder", "name: code_analyzer")

    def empty_file(b):
        b["prompts/analyzer.md"] = ""

    cases = [
        ("no root config", drop_root),
        ("two root configs", two_roots),
        ("disallowed extension", bad_ext),
        ("path traversal", traversal),
        ("!include escaping the root", escaping_include),
        ("dangling !include", missing_include),
        ("two base models", second_model),
        ("LoRA adapter present", adapter_present),
        ("sub-agent owns a writer tool", writer_subagent),
        ("root without submit_patch", no_submit),
        ("unknown tool name", unknown_tool),
        ("per-task budget too large", huge_budget),
        ("forbidden generation field", bad_generation_field),
        ("unknown state placeholder", stray_placeholder),
        ("duplicate agent name", root_is_subagent_name),
        ("empty file", empty_file),
    ]
    for label, fn in cases:
        try:
            validator.validate(mutate(fn))
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
    files = package_source.load_from_disk()
    print(f"primary bundle files: {sorted(files)}")
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
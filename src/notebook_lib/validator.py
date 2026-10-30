"""Static validator and deterministic packager for the swegemma submission bundle.

This module is deliberately self-contained (standard library plus PyYAML) and has
no imports from the rest of the project, because its source text is inlined
verbatim into the generated submission notebook. It must therefore also work
when executed as the only module in that notebook.

The checks mirror every constraint that the competition harness enforces on a
submission directory, plus the failure modes that public write-ups have actually
observed on the leaderboard. Nothing here needs a GPU, a network connection or
the competition data.
"""

from __future__ import annotations

import hashlib
import io
import posixpath
import re
import zipfile

import yaml

# ---------------------------------------------------------------------------
# Harness constants, transcribed from HARNESS_README.md sections 2.4 and 3.
# ---------------------------------------------------------------------------

ALLOWED_MODELS = frozenset({"gemma-4-31b-it-qat-w4a16-ct", "gemma-4-e4b-it-qat-w4a16-ct"})
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
ROOT_CONFIGS = ("agent.yaml", "agent.yml", "root_agent.yaml", "root_agent.yml")
ALLOWED_SUFFIXES = frozenset(
    {".yaml", ".yml", ".md", ".txt", ".py", ".json", ".safetensors"}
)
ADAPTER_SUFFIXES = frozenset({".safetensors"})
MAX_TOTAL_SIZE_BYTES = 3 * 2**30  # 3 GiB unpacked, adapters included
MAX_FILE_COUNT = 10_000
MAX_YAML_FILES = 1_000
MAX_YAML_SIZE_BYTES = 50 * 2**20
MAX_SKILL_SIZE_BYTES = 50 * 2**20
MAX_INSTRUCTION_CHARS = 1_000_000
MAX_TOTAL_INSTRUCTION_CHARS = 10_000_000
MAX_AGENTS = 500
MAX_SUB_AGENT_DEPTH = 50
MAX_SKILLS = 1_000
MAX_LOOP_ITERATIONS = 500
MAX_OUTPUT_TOKENS = 32_768
MAX_THINKING_BUDGET = 32_768

HARNESS_TOOLS = frozenset(
    {
        "run_command",
        "read_file",
        "edit_file",
        "write_file",
        "get_status",
        "submit_patch",
        "search_similar_code",
        "get_code_neighbors",
        "get_code_subgraph",
    }
)
WRITER_TOOLS = frozenset({"edit_file", "write_file", "submit_patch"})
# Fields the generation schema strips; setting them is a validation error.
FORBIDDEN_GENERATION_FIELDS = frozenset(
    {
        "tools",
        "system_instruction",
        "http_options",
        "safety_settings",
        "response_schema",
    }
)
SESSION_VARIABLES = frozenset({"problem_description", "hints"})
ALLOWED_AGENT_CLASSES = frozenset(
    {"LlmAgent", "SequentialAgent", "ParallelAgent", "LoopAgent"}
)
GENERATION_FIELDS = frozenset(
    {
        "temperature",
        "top_p",
        "top_k",
        "max_output_tokens",
        "presence_penalty",
        "frequency_penalty",
        "stop_sequences",
        "response_mime_type",
        "seed",
        "thinking_config",
    }
)


class SubmissionInvalid(Exception):
    """Raised when the bundle violates a competition or harness constraint."""


class _IncludeLoader(yaml.SafeLoader):
    """YAML loader that tolerates the harness' ``!include`` tag."""


_IncludeLoader.add_constructor(
    "!include", lambda loader, node: loader.construct_scalar(node)
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SubmissionInvalid(message)


def _resolve(owner: str, reference: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(owner), reference))


def _load_yaml(name: str, text: str) -> dict:
    data = yaml.load(text, Loader=_IncludeLoader)
    _require(isinstance(data, dict), f"{name}: top level must be a mapping")
    return data


def _resolve_include(owner: str, value, files: dict):
    """Follow a ``!include`` indirection.

    The YAML loader strips the ``!include`` tag and hands back only the scalar
    path, so an included value is indistinguishable from an inline literal by
    type alone. A path is recognised by the fact that it names a file that is
    actually in the package, which is exactly the set of values the harness
    would have read from disk. An included ``.yaml`` is parsed, because the
    harness loads it as structure rather than as text.
    """
    if not isinstance(value, str):
        return value
    candidate = value.strip()
    if not candidate or candidate.startswith(("/", "\\", "!", "{")):
        return value
    if "\n" in candidate or len(candidate) > 300:
        return value
    resolved = _resolve(owner, candidate)
    suffix = posixpath.splitext(resolved)[1].lower()
    if resolved in files and suffix in (".md", ".txt"):
        return files[resolved]
    if resolved in files and suffix in (".yaml", ".yml"):
        return _load_yaml(resolved, files[resolved])
    return value


def _instruction_text(name: str, config: dict, files: dict) -> str:
    raw = _resolve_include(name, config.get("instruction", ""), files)
    return raw if isinstance(raw, str) else ""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(files: dict) -> dict:
    """Validate a ``{posix relative path: text}`` mapping of the submission.

    Returns a small report on success and raises :class:`SubmissionInvalid`
    with a precise message on the first violation found.
    """
    _require(bool(files), "submission is empty")

    roots = [name for name in ROOT_CONFIGS if name in files]
    _require(
        len(roots) == 1,
        f"need exactly one root config among {list(ROOT_CONFIGS)}, found {roots}",
    )

    total_bytes = 0
    yaml_files = 0
    models = set()
    instruction_chars = 0
    seen_agents = set()
    declared_agent_names = set()
    skill_names = []

    for name in sorted(files):
        content = files[name]
        _require(
            isinstance(content, str) and content.strip(),
            f"{name}: file is empty",
        )
        _require(
            name == name.strip() and not name.startswith(("/", "\\", ".")),
            f"{name}: path must be relative and unprefixed",
        )
        _require(
            "\\" not in name and ":" not in name and ".." not in name.split("/"),
            f"{name}: path must be posix style and free of traversal",
        )
        suffix = posixpath.splitext(name)[1].lower()
        _require(
            suffix in ALLOWED_SUFFIXES,
            f"{name}: extension {suffix!r} is not allowed by the harness",
        )
        encoded = len(content.encode("utf-8"))
        total_bytes += encoded
        if suffix in (".yaml", ".yml"):
            yaml_files += 1
            _require(
                encoded <= MAX_YAML_SIZE_BYTES,
                f"{name}: YAML file exceeds 50 MiB",
            )
        if suffix == ".py":
            try:
                compile(content, name, "exec")
            except SyntaxError as error:
                raise SubmissionInvalid(f"{name}: does not compile: {error}") from error

    _require(len(files) <= MAX_FILE_COUNT, "more than 10,000 files")
    _require(yaml_files <= MAX_YAML_FILES, "more than 1,000 YAML files")
    _require(
        total_bytes <= MAX_TOTAL_SIZE_BYTES,
        f"unpacked size {total_bytes} exceeds the 3 GiB archive limit",
    )

    # Adapters, if any, must carry both required files and a safetensors weight.
    for name in files:
        if name.startswith("adapters/"):
            parts = name.split("/")
            _require(len(parts) == 3, f"{name}: unexpected adapter layout")
            _require(
                parts[2] in ("adapter_config.json", "adapter_model.safetensors"),
                f"{name}: unexpected file inside an adapter directory",
            )
            _require(
                posixpath.splitext(name)[1].lower() in ADAPTER_SUFFIXES
                or parts[2] == "adapter_config.json",
                f"{name}: adapter files must be .json plus .safetensors",
            )

    # Skills: one SKILL.md per skill directory, whose front-matter name matches.
    for name in sorted(files):
        if not name.startswith("skills/"):
            continue
        parts = name.split("/")
        _require(len(parts) >= 2, f"{name}: skill file outside a skill directory")
        skill_names.append("/".join(parts[:2]))
        if parts[2:] == ["SKILL.md"]:
            manifest = files[name]
            _require(
                manifest.lstrip().startswith("---"),
                f"{name}: SKILL.md needs YAML front matter",
            )
            _require(
                f"name: {parts[1]}" in manifest,
                f"{name}: front-matter name must equal the directory name {parts[1]!r}",
            )
    for skill in set(skill_names):
        size = sum(
            len(v.encode("utf-8"))
            for k, v in files.items()
            if k == skill or k.startswith(skill + "/")
        )
        _require(size <= MAX_SKILL_SIZE_BYTES, f"{skill}: skill exceeds 50 MiB")
    _require(
        len(set(skill_names)) <= MAX_SKILLS, "more than 1,000 skills declared"
    )

    def check_agent(name: str, depth: int, is_root: bool) -> int:
        _require(name in files, f"{name}: referenced agent config is missing")
        _require(depth <= MAX_SUB_AGENT_DEPTH, "sub-agent nesting exceeds 50 levels")
        _require(name not in seen_agents, f"{name}: agent referenced more than once")
        seen_agents.add(name)
        text = files[name]
        config = _load_yaml(name, text)
        instruction_chars_local = 0

        agent_class = config.get("agent_class", "LlmAgent")
        _require(
            agent_class in ALLOWED_AGENT_CLASSES,
            f"{name}: unsupported agent_class {agent_class!r}",
        )

        # `adapter` is accepted by the schema but deliberately unused: shipping a
        # LoRA collapses the harness KV cache, so the package must not have one.
        _require(
            "adapter" not in config,
            f"{name}: adapters are forbidden in this submission on purpose",
        )

        instruction = _instruction_text(name, config, files)
        if instruction:
            _require(
                len(instruction) <= MAX_INSTRUCTION_CHARS,
                f"{name}: instruction exceeds 1,000,000 characters",
            )
            instruction_chars_local = len(instruction)

            # ADK interpolates every brace-delimited token in an instruction from
            # session state, so an accidental literal brace raises at runtime.
            for match in re.finditer(r"(?<![\$\\{]){+[^{}]*}+", instruction):
                key = match.group().strip("{}").strip().lstrip("!").rstrip("?")
                _require(
                    (not key.isidentifier()) or key in SESSION_VARIABLES,
                    f"{name}: instruction interpolates unknown state {key!r}; "
                    "only {problem_description} and {hints} exist",
                )

        for include in re.findall(r"!include\s+([^\s]+)", text):
            resolved = _resolve(name, include)
            _require(
                resolved in files,
                f"{name}: !include target {include!r} is not in the package",
            )
            # A sub-agent is expected to reach a prompt with a relative parent
            # segment, as the official sample submission does. What the harness
            # blocks is a target that resolves outside the submission root.
            _require(
                not resolved.startswith("..") and not resolved.startswith("/"),
                f"{name}: !include {include!r} resolves to {resolved!r}, "
                "which escapes the submission root",
            )

        declared = {tool for tool in config.get("tools", []) or [] if isinstance(tool, str)}
        _require(
            declared <= HARNESS_TOOLS,
            f"{name}: unknown tools {sorted(declared - HARNESS_TOOLS)}",
        )
        if is_root:
            _require(
                "submit_patch" in declared,
                f"{name}: the root agent must own submit_patch or the task "
                "cannot be completed",
            )
            _require(
                "edit_file" in declared or "write_file" in declared,
                f"{name}: the root agent needs a writer tool",
            )
        else:
            _require(
                not (declared & WRITER_TOOLS),
                f"{name}: a read-only sub-agent must not own {sorted(declared & WRITER_TOOLS)}",
            )

        for skill in config.get("skills") or []:
            _require(
                f"{skill}/SKILL.md" in files,
                f"{name}: skill {skill!r} has no SKILL.md",
            )
            _require(
                not skill.startswith(("/", "\\", ".")) and ".." not in skill.split("/"),
                f"{name}: skill path {skill!r} escapes the submission root",
            )

        for skill in config.get("sub_agents", []) or []:
            _require(
                isinstance(skill, dict) and "config_path" in skill,
                f"{name}: sub_agents entries need a config_path",
            )
            check_agent(_resolve(name, skill["config_path"]), depth + 1, False)

        for tool in config.get("tools", []) or []:
            if isinstance(tool, dict):
                inner = tool.get("agent_tool")
                _require(
                    isinstance(inner, dict) and "config_path" in inner,
                    f"{name}: inline tool mapping must be agent_tool with a config_path",
                )
                check_agent(_resolve(name, inner["config_path"]), depth + 1, False)

        if agent_class == "LoopAgent":
            iterations = config.get("max_iterations", 500)
            _require(
                isinstance(iterations, int) and 1 <= iterations <= MAX_LOOP_ITERATIONS,
                f"{name}: max_iterations must be an int in 1..500",
            )

        generation = _resolve_include(name, config.get("generate_content_config"), files)
        if isinstance(generation, dict):
            _check_generation(name, generation)

        agent_name = config.get("name")
        _require(
            isinstance(agent_name, str) and agent_name.strip(),
            f"{name}: every agent needs a non-empty name",
        )
        _require(
            agent_name not in declared_agent_names,
            f"{name}: agent name {agent_name!r} is already used by another agent; "
            "the runner registers agents by name and duplicates collide",
        )
        declared_agent_names.add(agent_name)

        models.add(str(config.get("model", "")).strip())
        return instruction_chars_local

    instruction_chars += check_agent(roots[0], 0, True)
    _require(
        len(seen_agents) <= MAX_AGENTS, "more than 500 agents in the compiled tree"
    )
    _require(
        instruction_chars <= MAX_TOTAL_INSTRUCTION_CHARS,
        "total instruction size across all agents exceeds 10,000,000 characters",
    )

    # Only the base model may be declared, and the scorer accepts exactly one.
    normalised = {model.split("/")[-1] for model in models if model}
    _require(
        len(normalised) == 1 and normalised.issubset(ALLOWED_MODELS),
        f"every agent must declare only one allowed model among {sorted(ALLOWED_MODELS)}, found {sorted(normalised)}",
    )

    if "eval_config.yaml" in files:
        _check_eval_config("eval_config.yaml", files["eval_config.yaml"])

    return {
        "root_config": roots[0],
        "file_count": len(files),
        "unpacked_bytes": total_bytes,
        "agents": sorted(seen_agents),
        "model": MODEL,
        "adapters": sorted(n for n in files if n.startswith("adapters/")),
        "skills": sorted(set(skill_names)),
    }


def _check_generation(name: str, generation: dict) -> None:
    _require(
        set(generation) <= GENERATION_FIELDS,
        f"{name}: generate_content_config may only hold "
        f"{sorted(GENERATION_FIELDS)}, found {sorted(set(generation) - GENERATION_FIELDS)}",
    )
    for forbidden in FORBIDDEN_GENERATION_FIELDS:
        _require(
            forbidden not in generation,
            f"{name}: {forbidden!r} is stripped from generate_content_config and "
            "would raise a validation error",
        )
    if "max_output_tokens" in generation:
        value = generation["max_output_tokens"]
        _require(
            isinstance(value, int) and 1 <= value <= MAX_OUTPUT_TOKENS,
            f"{name}: max_output_tokens must be an int in 1..{MAX_OUTPUT_TOKENS}",
        )
    thinking = generation.get("thinking_config")
    if isinstance(thinking, dict):
        if "thinking_budget" in thinking:
            value = thinking["thinking_budget"]
            _require(
                isinstance(value, int) and 0 <= value <= MAX_THINKING_BUDGET,
                f"{name}: thinking_budget must be an int in 0..{MAX_THINKING_BUDGET}",
            )
        if "include_thoughts" in thinking:
            _require(
                isinstance(thinking["include_thoughts"], bool),
                f"{name}: include_thoughts must be a boolean",
            )
        if "thinking_level" in thinking:
            _require(
                str(thinking["thinking_level"]).upper()
                in ("MINIMAL", "LOW", "MEDIUM", "HIGH", "NONE"),
                f"{name}: unknown thinking_level {thinking['thinking_level']!r}",
            )
        _require(
            len(thinking) <= 3,
            f"{name}: thinking_config has unexpected keys {sorted(thinking)}",
        )


def _check_eval_config(name: str, text: str) -> None:
    data = _load_yaml(name, text)
    _require("evaluation" in data, f"{name}: missing the 'evaluation' key")
    section = data["evaluation"]
    _require(isinstance(section, dict), f"{name}: 'evaluation' must be a mapping")
    _require(
        set(section) <= {"timeout_seconds", "max_tool_calls", "max_time_minutes", "max_turns"},
        f"{name}: unsupported evaluation keys {sorted(set(section))}",
    )
    if "timeout_seconds" in section:
        _require(
            0 < section["timeout_seconds"] <= 300,
            f"{name}: timeout_seconds must be in 1..300",
        )
    if "max_tool_calls" in section:
        _require(
            0 < section["max_tool_calls"] <= 100,
            f"{name}: max_tool_calls must be in 1..100",
        )
    if "max_turns" in section:
        _require(
            0 < section["max_turns"] <= 500,
            f"{name}: max_turns must be in 1..500",
        )
    if "max_time_minutes" in section:
        value = section["max_time_minutes"]
        _require(
            isinstance(value, (int, float)) and 0 < value <= 60,
            f"{name}: max_time_minutes must be in (0, 60]",
        )
        # Guard rail only, not a harness rule: `swegemma/config.py` imposes no
        # ceiling on this field, and `agent_runner.py` applies it as an
        # `asyncio.timeout` around the agent loop that is cancelled the moment
        # `submit_patch` is called. So it is a ceiling, not a cost: a task the
        # agent finishes early never reaches it. The real risk is the scoring
        # run's 12 hour total across ~120 sequential tasks, which includes
        # container setup and Phase 2 verification that this budget excludes.
        # 10 minutes is the value a published 0.12-scoring bundle used, so a
        # ceiling below that is leaving measured score on the table; above ~12
        # the 12 hour cap has been observed to fail outright.
        _require(
            float(value) <= 10.0,
            f"{name}: max_time_minutes {value} is above the 10 minute ceiling; "
            "a per-task cap beyond that has been measured to exceed the 12 hour "
            "total compute limit for the whole run",
        )


# ---------------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------------


def pack(files: dict) -> bytes:
    """Validate then serialise the bundle into deterministic zip bytes.

    Directory entries are omitted: the harness wants a files-only archive with
    the root config at the top level. Timestamps are pinned so that rebuilding
    an unchanged bundle reproduces the same archive byte for byte.
    """
    validate(files)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Unix
            info.external_attr = 0o644 << 16
            archive.writestr(info, files[name].encode("utf-8"))
    payload = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        _require(archive.testzip() is None, "produced archive is corrupt")
        names = archive.namelist()
        _require(len(names) == len(set(names)), "produced archive has duplicate names")
        _require(
            not any(name.endswith("/") for name in names),
            "produced archive contains directory entries",
        )
        _require("agent.yaml" in names, "produced archive has no agent.yaml at its root")
        for name in names:
            _require(
                archive.read(name).decode("utf-8") == files[name],
                f"round trip mismatch for {name}",
            )
    return payload


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
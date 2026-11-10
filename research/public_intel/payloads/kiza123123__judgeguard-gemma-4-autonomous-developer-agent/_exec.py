# ---- cell 2 ----
# Step 1: Create project directory scaffolding
import os
import shutil
from pathlib import Path

SUBMISSION_DIR = Path("judgeguard_submission")
if SUBMISSION_DIR.exists():
    shutil.rmtree(SUBMISSION_DIR)

for sub_dir in ["configs", "prompts"]:
    (SUBMISSION_DIR / sub_dir).mkdir(parents=True, exist_ok=True)

print(f"✅ Created clean directory structure in: {SUBMISSION_DIR.resolve()}")


# ---- cell 4 ----
# Step 2: Write out all submission files

# 1. Root Agent Config: agent.yaml
agent_yaml = """name: judgeguard_developer_agent
model: gemma-4-31b-it-qat-w4a16-ct
instruction: !include prompts/system.md
tools:
  - run_command
  - read_file
  - edit_file
  - write_file
  - get_status
  - submit_patch
  - get_code_neighbors
  - search_similar_code
  - get_code_subgraph
generate_content_config: !include configs/sampling.yaml
"""
(SUBMISSION_DIR / "agent.yaml").write_text(agent_yaml, encoding="utf-8")

# 2. Evaluation Budget Config: eval_config.yaml
eval_config_yaml = """# JudgeGuard Evaluation Budget Configuration for SWE-bench Inference
# Optimized per-task execution budgets calibrated to 12-hour global scoring limit
evaluation:
  timeout_seconds: 240
  max_tool_calls: 28
  max_time_minutes: 8
  max_turns: 80
"""
(SUBMISSION_DIR / "eval_config.yaml").write_text(eval_config_yaml, encoding="utf-8")

# 3. Sampling & Thinking Config: configs/sampling.yaml
sampling_yaml = """temperature: 0.2
top_p: 0.95
max_output_tokens: 8192
thinking_config:
  thinking_budget: 4096
  include_thoughts: true
"""
(SUBMISSION_DIR / "configs/sampling.yaml").write_text(sampling_yaml, encoding="utf-8")

# 4. Master Coder System Prompt: prompts/system.md
system_md = """You are an autonomous software engineer. Your job: make the smallest correct change to the SOURCE code in /workspace so that the hidden tests for the issue below pass. The hidden tests were written from the issue text, so the exact names, messages, types and behaviours in the issue are the specification.

# HARD LIMITS
- 28 tool calls and 8 minutes in total. When either runs out, the working tree is graded as it is. An edit that exists counts, even if you never call `submit_patch`. An unedited tree always scores zero.
- Never create, modify or delete test files (`test_*.py`, `*_test.py`, anything under `tests/`, `pytest.ini`, `conftest.py`). This is an automatic failure.
- Scratch files go in /tmp only. Any file left under /workspace becomes part of the graded patch.
- Never run a full test suite (bare `pytest`, `pytest .`, `unittest discover`). Always name one test file, and add `-k` when you can.
- Never look outside /workspace. All dependencies are already installed.
- Never use `search_similar_code`, `get_code_neighbors` or `get_code_subgraph`. They return nothing useful.

# CALL PLAN
- Calls 1-8: locate and read. Calls 9-12: edit. You MUST have edited a source file by call 12. If you are unsure, make your best-guess edit in the most likely place now. A wrong edit can still be corrected. Pure reading cannot score.
- Calls 13-20: verify and correct.
- Call 20 onward: no new exploration. Check, fix, submit.
- Always finish with `git diff` followed by `submit_patch`.

# PROCEDURE

## 1. Extract the specification (no tool call)
From the issue, list for yourself: the exact file, function, class or CLI name; the exact error message and exception type; the expected return value or output; the inputs that trigger the bug; every edge case mentioned (None, empty, negative, unicode, duplicates, defaults). Treat every concrete string and name in the issue as a literal that must appear exactly in your code.

## 2. Locate
- Use exact paths from the issue directly. When searches are necessary, combine independent searches for the issue's exact symbols, their callers and relevant test paths into one run_command. Use git grep with fixed-string patterns for literal identifiers and git ls-files for tracked file paths; each result should show its file path and line number where applicable.
- Batch only searches whose inputs are already known. If the next search depends on the first result, inspect that result before searching again. Limit each search to about 20 matching lines and keep total output short; never dump whole files or the repository tree.
- Once the target is located, read the relevant implementation plus one relevant caller or test case. When both paths and line ranges are known, read these small regions in one run_command using sed with explicit line ranges, or use read_file for a single region. Aim for about 40 lines per region and at most three regions per command. Include enough surrounding code to understand signatures, defaults and error handling.
- For a bug: find where the wrong behaviour is produced and use the caller or test to understand the contract before editing.
- For a feature: find the closest existing sibling (a similar function, option, class, or doc example) and copy its pattern, including registration points such as __all__, option lists, dispatch tables and imports.
- Reuse paths and test names already discovered. Do not spend another tool call repeating a search that already answered the question.
- If the issue includes a code snippet that reproduces the problem, you may run it once with python -c (one call, never create a file) to see the real error.

## 3. Edit
- Use edit_file for changes to existing code. Copy old_string exactly from the source, including whitespace, and choose a short unique match. Use write_file only for a genuinely new source file that the issue requires.
- If edit_file reports no match or multiple matches, read the exact source region and retry with a smaller unique snippet. Never repeat an identical failed edit. After two matching failures, use one inline Python script through run_command with a quoted heredoc; assert that the old text occurs exactly once before replacing it and writing the file. Preserve unrelated content and do not rewrite the file from memory.
- Fix the cause, not the symptom. Do not special-case the example from the issue.
- Change only what the issue requires. Keep existing signatures, defaults, and backward compatibility unless the issue says otherwise. Match the style, naming and error-handling idioms of the surrounding code.
- If the same behaviour has parallel implementations (sync and async variants, Client and AsyncClient, several backends or transports, typing overloads, re-exports in `__init__.py` or `__all__`), apply the change to every one of them. Hidden tests often exercise more than one.
- Use the exact exception class and exact message text from the issue. If the issue only describes the error, reuse the wording style of neighbouring error messages.
- Handle every edge case you listed in step 1.
- For documentation-code tasks (for example FastAPI), edit the executable code under `docs_src/`.

## 4. Verify (at most 2 calls)
- Find the test file with `find tests -name "*keyword*.py"`, then run `timeout 150 python -m pytest tests/path/test_x.py -x -q -k keyword`. Use `python3 -m unittest tests.test_x` for unittest projects.
- Failures that come from missing fixtures, missing data, or import errors unrelated to your change are pre-existing. Ignore them. Never repair tests or the environment.
- If a test related to your change fails, read the traceback, fix the source once, and rerun once. If no test can run, do one `python -c` check or `python -m py_compile` on the edited file.

## 5. Final check and submit
- Run `git status --short && git diff` in one call. `git diff` alone hides untracked files, but `submit_patch` includes them. If you see an untracked scratch file or a changed test file, remove it or restore it with `git checkout --` before submitting. Confirm that: only source files changed; every name, message and type from step 1 appears exactly; nothing unrelated was touched; there are no leftover debug prints or stray files.
- Call `submit_patch`. Confirm `patch_size > 0` and `files_changed > 0`. If either is 0, you have not edited anything. Edit now and submit again.
- End with a single-sentence summary of the fix.

# DECISION RULES
- Ambiguous issue: choose the most literal reading of the issue text and act on it. Do not ask questions and do not stall.
- Several possible locations: pick the one where the wrong behaviour is produced, not where it is merely observed.
- Search returned nothing: try one different specific string, then edit your best candidate anyway.
- Stuck after a failed fix: make a different, smaller change. Do not repeat the same edit.
- Never conclude that nothing needs to change. Every task requires a non-empty source patch.
"""
(SUBMISSION_DIR / "prompts/system.md").write_text(system_md, encoding="utf-8")

print("✅ All declarative submission components generated successfully!")
for p in sorted(SUBMISSION_DIR.rglob("*")):
    if p.is_file():
        print(f"  • {p.relative_to(SUBMISSION_DIR)} ({p.stat().st_size:,} bytes)")


# ---- cell 6 ----
# Step 3: Run full in-notebook validation suite
import yaml
from pathlib import Path

ALLOWED_MODELS = {
    "gemma-4-31b-it-qat-w4a16-ct",
    "gemma-4-12b-it-qat-w4a16-ct",
    "gemma-4-e4b-it-qat-w4a16-ct",
    "gemma-4-e2b-it-qat-w4a16-ct",
}

ALLOWED_EXTENSIONS = {
    ".yaml", ".yml", ".md", ".txt", ".py", ".json", ".safetensors"
}

ALLOWED_TOOLS = {
    "run_command", "read_file", "edit_file", "write_file",
    "get_status", "submit_patch", "get_code_neighbors",
    "search_similar_code", "get_code_subgraph", "agent_tool"
}

class SandboxedIncludeLoader(yaml.SafeLoader):
    def __init__(self, stream):
        self._root_dir = Path(getattr(stream, 'name', os.getcwd())).parent
        super().__init__(stream)

def include_constructor(loader, node):
    rel_path = loader.construct_scalar(node)
    target_path = (loader._root_dir / rel_path).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"!include file not found: {rel_path}")
    suffix = target_path.suffix.lower()
    if suffix in [".md", ".txt"]:
        return target_path.read_text(encoding="utf-8")
    elif suffix in [".yaml", ".yml"]:
        with open(target_path, "r", encoding="utf-8") as f:
            return yaml.load(f, Loader=SandboxedIncludeLoader)
    raise ValueError(f"Unsupported extension: {suffix}")

SandboxedIncludeLoader.add_constructor("!include", include_constructor)

def validate_submission(root_dir: Path):
    print("=" * 60)
    print("🔍 VALIDATING SUBMISSION COMPLIANCE")
    print("=" * 60)
    
    # 1. Root config
    root_cfg = root_dir / "agent.yaml"
    assert root_cfg.exists(), "agent.yaml missing at root!"
    print("  [PASS] Root configuration found: agent.yaml")
    
    # 2. Extensions & size
    total_size = 0
    file_count = 0
    for p in root_dir.rglob("*"):
        if p.is_file():
            file_count += 1
            total_size += p.stat().st_size
            ext = p.suffix.lower()
            assert ext in ALLOWED_EXTENSIONS, f"Disallowed extension: {ext} on {p}"
    assert total_size < 3 * 1024 * 1024 * 1024, "Archive exceeds 3 GiB!"
    print(f"  [PASS] File count: {file_count}, Total unpacked size: {total_size:,} bytes")
    
    # 3. Model & tools
    with open(root_cfg, "r", encoding="utf-8") as f:
        root_data = yaml.load(f, Loader=SandboxedIncludeLoader)
    
    declared_models = {root_data["model"]}
    for tool in root_data.get("tools", []):
        if isinstance(tool, str):
            assert tool in ALLOWED_TOOLS, f"Invalid tool: {tool}"
                
    assert len(declared_models) == 1, f"Multiple models declared: {declared_models}"
    model = next(iter(declared_models))
    assert model in ALLOWED_MODELS, f"Model not permitted: {model}"
    print(f"  [PASS] Single base model rule verified: {model}")
    print(f"  [PASS] All tools successfully mapped to closed ToolRegistry")
    print("=" * 60)
    print("🎉 ALL ADK SPECIFICATION CHECKS PASSED!")
    print("=" * 60)

validate_submission(SUBMISSION_DIR)


# ---- cell 8 ----
# Step 4: Package submission.zip and verify
import zipfile
import tempfile
import hashlib

OUTPUT_ZIP = Path("submission.zip")
files_to_pack = {
    "agent.yaml": (SUBMISSION_DIR / "agent.yaml").read_text(encoding="utf-8"),
    "configs/sampling.yaml": (SUBMISSION_DIR / "configs/sampling.yaml").read_text(encoding="utf-8"),
    "eval_config.yaml": (SUBMISSION_DIR / "eval_config.yaml").read_text(encoding="utf-8"),
    "prompts/system.md": (SUBMISSION_DIR / "prompts/system.md").read_text(encoding="utf-8"),
}

with zipfile.ZipFile(OUTPUT_ZIP, "w") as zf:
    for name, content in sorted(files_to_pack.items()):
        info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        zf.writestr(info, content.encode("utf-8"))

print(f"✅ Packaged {OUTPUT_ZIP.name} ({OUTPUT_ZIP.stat().st_size:,} bytes)")
print(f"SHA-256: {hashlib.sha256(OUTPUT_ZIP.read_bytes()).hexdigest()}")

# Test extracting into clean temporary directory
with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_path = Path(tmp_dir)
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as zf:
        zf.extractall(tmp_path)
    validate_submission(tmp_path)

print("\n🚀 submission.zip is 100% verified and ready for scoring on Kaggle!")

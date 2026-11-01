#!/usr/bin/env python3
"""Verifier for tracks/e4b_small/bundles/e4b_v4_swe_toolkit."""
import hashlib
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
BUNDLE = Path(__file__).resolve().parent / "bundles" / "e4b_v4_swe_toolkit"
MODEL = "gemma-4-e4b-it-qat-w4a16-ct"
ANCHOR_SKILLS = REPO / "bundles" / "exp14_lean_toolkit" / "skills" / "swe-toolkit"

files = {p.relative_to(BUNDLE).as_posix(): p.read_bytes()
         for p in BUNDLE.rglob("*") if p.is_file()}
names = sorted(files)
texts = {k: v.decode("utf-8") for k, v in files.items()}

assert names == [
    "agent.yaml", "configs/sampling.yaml", "eval_config.yaml",
    "prompts/system.md", "skills/swe-toolkit/SKILL.md",
    "skills/swe-toolkit/scripts/_guard.py",
    "skills/swe-toolkit/scripts/_index.py",
    "skills/swe-toolkit/scripts/_knowledge.py",
    "skills/swe-toolkit/scripts/_verify.py",
    "skills/swe-toolkit/scripts/swe.py",
], f"unexpected file set: {names}"

ag = texts["agent.yaml"]
assert f"model: {MODEL}" in ag
for t in ["run_command", "read_file", "edit_file", "write_file", "get_status", "submit_patch"]:
    assert f"  - {t}" in ag
for t in ["get_code_neighbors", "search_similar_code", "get_code_subgraph"]:
    assert f"  - {t}" not in ag
assert "skills:" in ag and "  - skills/swe-toolkit" in ag

sampling = yaml.safe_load(texts["configs/sampling.yaml"])
assert sampling["temperature"] == 0.1
assert sampling["top_p"] == 0.95
assert sampling["max_output_tokens"] == 8192
assert sampling["thinking_config"]["thinking_budget"] == 4096
assert sampling["thinking_config"]["include_thoughts"] is True
evalc = yaml.safe_load(texts["eval_config.yaml"])["evaluation"]
assert evalc["timeout_seconds"] == 240
assert evalc["max_tool_calls"] == 35
assert evalc["max_time_minutes"] == 8
assert evalc["max_turns"] == 80

# prompt: e4b_v3 prompt with the locate cold-call updated to <=250-char keywords
V3_PROMPT = Path(__file__).resolve().parent / "bundles" / "e4b_v3_swe_toolkit" / "prompts" / "system.md"
expected = V3_PROMPT.read_text(encoding="utf-8").replace(
    'args=["locate", "--issue", "<the issue text>"]',
    'args=["locate", "--issue", "<keywords/error <=250 chars>"]',
)
prompt = texts["prompts/system.md"]
assert prompt == expected, "prompt is not e4b_v3 with the keyword cold-call update"
assert len(prompt) <= 2200, f"prompt {len(prompt)} > 2200"
assert prompt.count("{") == 1 and prompt.count("}") == 1
assert "{problem_description}" in prompt
assert prompt.rstrip().endswith("{problem_description}")
assert "STATE:" in prompt
assert "git status --short" in prompt
assert "ast.parse" in prompt
assert "git add -N -f" in prompt
LOCATE_CALL = ('run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py", '
               'args=["locate", "--issue", "<keywords/error <=250 chars>"])')
VERIFY_CALL = ('run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py", '
               'args=["verify"])')
assert prompt.count("run_skill_script") == 2
assert LOCATE_CALL in prompt and VERIFY_CALL in prompt

# skill files byte-identical to the upgraded exp14 engine
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

SKILL_FILES = [
    "SKILL.md", "scripts/_guard.py", "scripts/_index.py",
    "scripts/_knowledge.py", "scripts/_verify.py", "scripts/swe.py",
]
for rel in SKILL_FILES:
    bundled = sha(BUNDLE / "skills" / "swe-toolkit" / rel)
    anchor = sha(ANCHOR_SKILLS / rel)
    assert bundled == anchor, f"skill file drift vs exp14 engine: {rel}"

for _name, _content in texts.items():
    assert "gemma-4-31b" not in _content, f"gemma-4-31b leaked into {_name}"
for _name in names:
    assert _name.rsplit("/", 1)[-1].rsplit(".", 1)[-1] in {
        "yaml", "yml", "md", "txt", "py", "json", "safetensors",
    }, f"disallowed extension in {_name}"

print(f"E4B V4 VERIFY_BUNDLE: ALL CHECKS PASSED (prompt {len(prompt)} chars, "
      f"{len(names)} files, skill hashes pinned to upgraded engine)")
sys.exit(0)

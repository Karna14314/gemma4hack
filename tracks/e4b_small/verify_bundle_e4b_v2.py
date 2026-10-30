#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml

BUNDLE = Path(__file__).resolve().parent / "bundles" / "e4b_v2"
MODEL = "gemma-4-e4b-it-qat-w4a16-ct"
files = {p.relative_to(BUNDLE).as_posix(): p.read_text() for p in BUNDLE.rglob("*") if p.is_file()}
assert "agent.yaml" in files
ag = files["agent.yaml"]
assert f"model: {MODEL}" in ag
for t in ["run_command","read_file","edit_file","write_file","get_status","submit_patch"]:
    assert f"  - {t}" in ag
for t in ["get_code_neighbors","search_similar_code","get_code_subgraph"]:
    assert f"  - {t}" not in ag
sampling = yaml.safe_load(files["configs/sampling.yaml"])
assert sampling["temperature"] == 0.1
assert sampling["top_p"] == 0.95
assert sampling["max_output_tokens"] == 8192
assert sampling["thinking_config"]["thinking_budget"] == 4096
assert sampling["thinking_config"]["include_thoughts"] is True
evalc = yaml.safe_load(files["eval_config.yaml"])["evaluation"]
assert evalc["timeout_seconds"] == 240
assert evalc["max_tool_calls"] == 28
assert evalc["max_time_minutes"] == 8
assert evalc["max_turns"] == 80
prompt = files["prompts/system.md"]
assert len(prompt) <= 2500, f"prompt {len(prompt)} > 2500"
assert "{problem_description}" in prompt
assert prompt.rstrip().endswith("{problem_description}")
# braces only problem_description
assert prompt.count("{") == 1 and prompt.count("}") == 1
assert "STATE:" in prompt
assert "git status --short" in prompt
assert "ast.parse" in prompt
assert "git add -N -f" in prompt
for _name, _content in files.items():
    assert "gemma-4-31b" not in _content, f"gemma-4-31b leaked into bundle file {_name}"
print(f"E4B V2 VERIFY_BUNDLE: ALL CHECKS PASSED (prompt {len(prompt)} chars)")
sys.exit(0)

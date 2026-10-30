#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml

BUNDLE = Path(__file__).resolve().parent / "bundles" / "exp11_e4b"
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
assert sampling["temperature"] == 0.2
assert sampling["top_p"] == 0.95
assert sampling["max_output_tokens"] == 8192
assert sampling["thinking_config"]["thinking_budget"] == 4096
assert sampling["thinking_config"]["include_thoughts"] is True
evalc = yaml.safe_load(files["eval_config.yaml"])["evaluation"]
assert evalc["timeout_seconds"] == 240
assert evalc["max_tool_calls"] == 28
assert evalc["max_time_minutes"] == 8
assert evalc["max_turns"] == 80
# prompt is the clean exp05 prompt with the graph-tool ban line removed
exp05_prompt = Path(__file__).resolve().parents[2] / "ckpt" / "bundles" / "exp05_patch_integrity" / "prompts" / "system.md"
assert exp05_prompt.is_file(), "exp05 prompt missing"
graph_line = "- Never use `search_similar_code`, `get_code_neighbors` or `get_code_subgraph`. They return nothing useful.\n"
expected_prompt = exp05_prompt.read_text().replace(graph_line, "")
assert files["prompts/system.md"] == expected_prompt, "prompt not the clean exp05 prompt (graph line removed)"
# hygiene: problem_description present and clean end
prompt = files["prompts/system.md"]
assert "{problem_description}" in prompt
assert prompt.rstrip().endswith("{problem_description}")
assert "EOF" not in prompt.split("## The issue")[-1]
assert "echo written" not in prompt
for _name, _content in files.items():
    assert "gemma-4-31b" not in _content, f"gemma-4-31b leaked into bundle file {_name}"
print("E4B VERIFY_BUNDLE: ALL CHECKS PASSED")
sys.exit(0)

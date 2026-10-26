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
assert "search_similar_code" not in ag
assert "get_code_neighbors" not in ag
assert "get_code_subgraph" not in ag
sampling = yaml.safe_load(files["configs/sampling.yaml"])
assert sampling["temperature"] == 0.1
assert sampling["top_p"] == 0.95
assert sampling["max_output_tokens"] == 5120
assert sampling["thinking_config"]["thinking_budget"] == 3072
evalc = yaml.safe_load(files["eval_config.yaml"])["evaluation"]
assert evalc["timeout_seconds"] == 180
assert evalc["max_tool_calls"] == 36
assert evalc["max_time_minutes"] == 6
assert evalc["max_turns"] == 80
print("E4B VERIFY_BUNDLE: ALL CHECKS PASSED")
sys.exit(0)

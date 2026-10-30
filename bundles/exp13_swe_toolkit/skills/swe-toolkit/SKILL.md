---
name: swe-toolkit
description: "Deterministic SWE helper: locate, inspect, verify."
---
# swe-toolkit
Operations: locate, inspect, verify.
Invoke via ADK: run_skill_script(skill_name="swe-toolkit", script_path="scripts/swe.py", args=["locate","--query","..."])
Direct: python3 $(find / -name swe.py 2>/dev/null | head -1) locate --query "..."
Bootstrap: python3 skills/swe-toolkit/scripts/bootstrap.py
State: /tmp/swe_state.json

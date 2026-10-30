---
name: swe-toolkit
description: "Deterministic SWE helper: inspect, verify."
---
# swe-toolkit
Operations: inspect, verify.
Invoke via ADK: run_skill_script(skill_name="swe-toolkit", script_path="scripts/swe.py", args=["inspect","--symbol","..."])
Direct: python skills/swe-toolkit/scripts/swe.py inspect --symbol NAME --root /workspace
Bootstrap: python skills/swe-toolkit/scripts/bootstrap.py
State: /tmp/swe_state.json

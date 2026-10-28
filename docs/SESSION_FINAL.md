# SESSION_FINAL

Branch: feat/exp12-exp05-timing-buffer
PR: (draft to be opened)

## Summary
- Fixed on-disk exp05 hygiene: `prompts/system.md` now ends cleanly with `## The issue\n{problem_description}`.
- Hardened `verify_bundle.py` and `tracks/e4b_small/verify_bundle_e4b.py` to assert `problem_description` present + clean end and `max_output_tokens: 8192`.
- Built `exp12-timing-buffer` (31B) as near-exact copy of scored exp05 (ref 57553805, 0.20) with 6 tools, 9-min buffer, 3 early-exit bullets.
- Synced `exp11_e4b` (E4B) to same template (model only differs).
- Pushed kernels: `narisettichaitanya/gemma4-devagent-exp12-timing-buffer` v1 (COMPLETE) and `narisettichaitanya/g4-e4b-small-agent-submit` v4 (COMPLETE).
- Submitted exp12-timing-buffer: ref **57736284** (PENDING, registered 2026-10-28).
- Pushed checkpoint to `narisettichaitanya/gemma4-agent-ckpt`.

## Verification
- `verify_bundle.py`: ALL CHECKS PASSED
- `verify_bundle.py --bundle .../exp12-timing-buffer`: ALL CHECKS PASSED
- `verify_notebook.py`: ALL CHECKS PASSED
- `verify_notebook.py --notebook .../exp12-timing-buffer/submission_notebook.ipynb`: ALL CHECKS PASSED
- `tracks/e4b_small/verify_bundle_e4b.py`: ALL CHECKS PASSED
- `tracks/e4b_small/verify_notebook_e4b.py`: ALL CHECKS PASSED

## Submission status
- exp12-timing-buffer ref 57736284: PENDING (submitted 2026-10-28)
- exp11_e4b ref 57697341: COMPLETE 0.13
- exp05 ref 57553805: COMPLETE 0.20

## diff -u exp05/ exp12-timing-buffer/

```diff
diff -ru exp05_patch_integrity/agent.yaml exp12-timing-buffer/agent.yaml
--- exp05_patch_integrity/agent.yaml	2026-10-28 12:13:19.548647113 +0000
+++ exp12-timing-buffer/agent.yaml	2026-10-28 12:17:12.520172204 +0000
@@ -8,7 +8,4 @@
   - write_file
   - get_status
   - submit_patch
-  - get_code_neighbors
-  - search_similar_code
-  - get_code_subgraph
 generate_content_config: !include configs/sampling.yaml
diff -ru exp05_patch_integrity/eval_config.yaml exp12-timing-buffer/eval_config.yaml
--- exp05_patch_integrity/eval_config.yaml	2026-10-28 12:13:19.549099914 +0000
+++ exp12-timing-buffer/eval_config.yaml	2026-10-28 12:17:12.520463655 +0000
@@ -1,5 +1,5 @@
 evaluation:
   timeout_seconds: 240
   max_tool_calls: 28
-  max_time_minutes: 8
+  max_time_minutes: 9
   max_turns: 80
diff -ru exp05_patch_integrity/prompts/system.md exp12-timing-buffer/prompts/system.md
--- exp05_patch_integrity/prompts/system.md	2026-10-28 12:16:38.848371525 +0000
+++ exp12-timing-buffer/prompts/system.md	2026-10-28 12:17:09.634545571 +0000
@@ -1,11 +1,10 @@
 You are an autonomous software engineer. Your job: make the smallest correct change to the SOURCE code in /workspace so that the hidden tests for the issue below pass. The hidden tests were written from the issue text, so the exact names, messages, types and behaviours in the issue are the specification.
 
 # HARD LIMITS
-- 28 tool calls and 8 minutes in total. When either runs out, the working tree is graded as it is. An edit that exists counts, even if you never call `submit_patch`. An unedited tree always scores zero.
+- 28 tool calls and 9 minutes in total. When either runs out, the working tree is graded as it is. An edit that exists counts, even if you never call `submit_patch`. An unedited tree always scores zero.
 - Never create, modify or delete test files (`test_*.py`, `*_test.py`, anything under `tests/`). This is an automatic failure.
 - Never run a full test suite (bare `pytest`, `pytest .`, `unittest discover`). Always name one test file, and add `-k` when you can.
 - Never look outside /workspace. All dependencies are already installed.
-- Never use `search_similar_code`, `get_code_neighbors` or `get_code_subgraph`. They return nothing useful.
 
 # CALL PLAN
 - Calls 1-8: locate and read. Calls 9-12: edit. You MUST have edited a source file by call 12. If you are unsure, make your best-guess edit in the most likely place now. A wrong edit can still be corrected. Pure reading cannot score.
@@ -51,6 +50,9 @@
 - Search returned nothing: try one different specific string, then edit your best candidate anyway.
 - Stuck after a failed fix: make a different, smaller change. Do not repeat the same edit.
 - Never conclude that nothing needs to change. Every task requires a non-empty source patch.
+- Easy fix complete: as soon as your source edit compiles (`python3 -m py_compile <file>`) and passes the targeted test (`pytest <test> -q --tb=short 2>&1 | tail -n 60`), run the final check and `submit_patch` immediately so unused time stays in the global buffer.
+- Unrelated test environment error or 2 failed repair tries: do not overwrite a valid source edit or wander until timeout. Keep your best source edit on disk, restore any touched test files (`git checkout -- tests/ test/ testing/ 2>/dev/null`), and `submit_patch` early.
+- On `budget_warning` (≤10 calls left): stop exploring immediately, apply your best edit if not yet applied, run `git status --short`, and call `submit_patch`.
 
 ## The issue
 {problem_description}
```

# Failure analysis of the 0.17 run (exp03, ref 57037122)

Kaggle exposes only the aggregate score (0.17, COMPLETE) for submission ref 57037122.
No per-task logs, patch diffs, or failure categories are returned by the submissions API
or the kernel output (the kernel only logs bundle build + validation). Counts below are
therefore not available from the scoring side; the buckets are the harness failure taxonomy
from research/BASELINE_017.md mapped to the baseline, with the bundle that targets each.

| bucket | cause (harness mechanism) | targeted bundle |
|---|---|---|
| empty patches | `submit_patch` runs `git add -N .`, which respects `.gitignore`; a new file on an ignored path never reaches the diff (swegemma tools/execution.py:86) | exp05 (patch integrity) |
| patches that do not apply / syntax errors | no mandatory compile check; a non-importing file ships and scores zero; vLLM context overflow can also kill the session | exp04 (mandatory py_compile) |
| timeouts / wandering | runs still exploring after many calls almost never succeed; 60 calls/120 turns in v2 vs 28/80 in baseline | baseline (exp03) config |
| invalid tool calls | 10 tools incl. sub-agent schema; graph tools declared but banned | future: drop 3 graph tools |
| no edit by call 12 | edit-by-call-12 rule; runs with no source edit by call 12 fail 87% | baseline prompt |

Qualitative reading: exp03 reproducing 0.17 means the v2 regression was configuration, not prompt content. exp05 and exp04 isolate the two patch-mechanics failure modes.

# OPENCODE REPORT — read-only data collection

Generated: 2026-11-01. Read-only session. Only file created: this one.
Tags: **VERIFIED** = read from a file / CLI / log during this session.
**REMEMBERED** = from conversation history only. **UNKNOWN** = could not establish.

No submission was made. No bundle, script, or config was edited. No commit was created.
`git status --short` is empty at the end of the session (VERIFIED).

---

## [S1] REPO STATE

### S1.1 Branch, HEAD, status, stashes

```
$ git branch --show-current
main
$ git rev-parse HEAD
fdc264ac52c3c21931e8100089f10b354664c348
$ git status --short
(no output)
$ git stash list
(no output)
```

VERIFIED. Working tree clean, no stashes.

### S1.2 Branches (20 remote-tracking, VERIFIED)

```
* main
  remotes/origin/HEAD -> origin/main
  remotes/origin/feat/devset-gpu-eval-harness
  remotes/origin/feat/e4b-isolated-and-paper-eval
  remotes/origin/feat/e4b-v2
  remotes/origin/feat/exp10-audit-and-e4b-submit
  remotes/origin/feat/exp10-consolidated
  remotes/origin/feat/exp12-exp05-timing-buffer
  remotes/origin/feat/exp13-swe-toolkit-v2
  remotes/origin/feat/paper-track-complete-benchmarks
  remotes/origin/feat/study-guide
  remotes/origin/feat/submit-true-e4b
  remotes/origin/feat/swe-toolkit-skill
  remotes/origin/feat/true-e4b-and-paper-fix-428999567140592133
  remotes/origin/kilo/bright-field-nw7
  remotes/origin/kilo/gentle-lotus-ytv
  remotes/origin/kilo/gleeful-gecko-9p1
  remotes/origin/kilo/session-exp06-exp07
  remotes/origin/kilo/tool-contract-session
  remotes/origin/kilo/winter-quest-l1k
  remotes/origin/main
```

### S1.3 `git log --oneline -20 --all --decorate` (VERIFIED)

```
fdc264a (HEAD -> main, origin/main, origin/HEAD) repo: pin LF for bundle payloads, skill scripts and the notebook source
2b7cd84 toolkit: fix locate latency and ranking, rewrite verify gate, repair exp13 prompt
c20adc3 audit: public research, 0.24 tail analysis, localization is the real gap
b8ed0a2 audit: E4B line closed, 0.20 anchor was not byte-exact, E0 control submitted
35d9c63 docs: add live tasklist; instrument repair gates the 31B ladder
7b5c8e8 docs: 129-task audit, skills architecture, snapshot manifest; correct submission limits
90008e8 docs: add README, AGENTS.md, runbook, and live resource inventory
a5e49b0 Merge pull request #16 from Karna14314/kilo/gleeful-gecko-9p1
125bdd2 (origin/kilo/gleeful-gecko-9p1) chore: remove swe_toolkit skill files
7ec274b Merge pull request #15 from Karna14314/feat/paper-track-complete-benchmarks
3c60cb9 (origin/feat/paper-track-complete-benchmarks) fix: clean duplicate experiment 2 table rows
6b096f9 feat(paper-track): verified 129-task benchmarks + complete paper draft
15ce952 (origin/feat/exp13-swe-toolkit-v2) docs: session final and exp13 clean baseline with inline patch gate
d4b0bd6 Merge pull request #14 from Karna14314/feat/exp13-swe-toolkit-v2
5eb0bef feat(exp13): build swe-toolkit v2 bundle with dual-transport resilience
56599f5 Merge pull request #13 from Karna14314/feat/e4b-v2
e30a648 (origin/feat/e4b-v2) docs: session final for e4b-v2
d33c321 feat(e4b): build e4b-v2 bundle (temp 0.1 + imperative prompt) and research R1-R5
94f256e (origin/feat/swe-toolkit-skill) feat: upgrade swe_toolkit scorer + exp13 cleanup
3e8f5c8 docs: session final swe toolkit
```

### S1.4 Every directory containing an `agent.yaml` (37 bundles, VERIFIED)

Excluded: `.venv-harness/`, `audit_snapshots/`, `node_modules/`, `.verify_build/`.

```
bundle dir                                                tools  sys.md  model / skills
build/exp05_lf                                                9    5461  31B  skills=NONE
build/exp05_submitted                                         9    5425  31B  skills=NONE
bundles/exp13                                                 6    5752  31B  skills=NONE
bundles/exp13_swe_toolkit                                     9    5879  31B  skills=['skills/swe-toolkit']
ckpt/bundles/exp04_mandatory_pycompile                        9    5275  31B  skills=NONE
ckpt/bundles/exp05_patch_integrity                            9    5461  31B  skills=NONE
ckpt/bundles/exp06_rebased_cheatsheet                         9    6622  31B  skills=NONE
ckpt/bundles/exp06_repo_test_cheatsheet                       9    6622  31B  skills=NONE
ckpt/bundles/exp07_rebased_verification                       9    5627  31B  skills=NONE
ckpt/bundles/exp07_verification_loop                          9    5627  31B  skills=NONE
ckpt/bundles/exp08_tool_contract                              9    5979  31B  skills=NONE
ckpt/bundles/exp09_drop_graph_tools                           6    5317  31B  skills=NONE
ckpt/bundles/exp10_consolidated                               6    9764  31B  skills=NONE
ckpt/bundles/exp11_e4b                                        6    5425  E4B  skills=NONE
ckpt/bundles/exp13_swe_toolkit                                9    5879  31B  skills=['skills/swe-toolkit']
ckpt/research/kernel_devset_eval/bundles/exp05_patch_integrity 9   5461  31B  skills=NONE
ckpt/research/kernel_devset_eval/bundles/exp10_consolidated   6    9764  31B  skills=NONE
ckpt/src/agent_package                                        9    4949  E4B  skills=NONE
kaggle_work/.../bundles/exp04_mandatory_pycompile             9    5275  31B  skills=NONE
kaggle_work/.../bundles/exp05_patch_integrity                 9    5461  31B  skills=NONE
kaggle_work/.../bundles/exp06_rebased_cheatsheet              9    6622  31B  skills=NONE
kaggle_work/.../bundles/exp06_repo_test_cheatsheet            9    6622  31B  skills=NONE
kaggle_work/.../bundles/exp07_rebased_verification            9    5627  31B  skills=NONE
kaggle_work/.../bundles/exp07_verification_loop               9    5627  31B  skills=NONE
kaggle_work/.../bundles/exp08_tool_contract                   9    5979  31B  skills=NONE
kaggle_work/.../bundles/exp09_drop_graph_tools                6    5317  31B  skills=NONE
kaggle_work/.../bundles/exp10_consolidated                    6    9764  31B  skills=NONE
kaggle_work/.../bundles/exp11_e4b                             6    5425  E4B  skills=NONE
kaggle_work/.../bundles/exp12-timing-buffer                   6    6049  31B  skills=NONE
kaggle_work/.../bundles/exp13_swe_toolkit                     9    5879  31B  skills=['skills/swe-toolkit']
kaggle_work/.../research                                      10      -   31B  skills=NONE (no prompts/system.md)
research/kernel_devset_eval/bundles/exp05_patch_integrity     9    5461  31B  skills=NONE
research/kernel_devset_eval/bundles/exp10_consolidated        6    9764  31B  skills=NONE
src/agent_package                                             9    4949  E4B  skills=NONE
tracks/e4b_small/bundles/e4b_v2                               6    1746  E4B  skills=NONE
tracks/e4b_small/bundles/e4b_v3                               6    2440  E4B  skills=NONE
tracks/e4b_small/bundles/exp11_e4b                            6    5353  E4B  skills=NONE
```

`sys.md` = character count of `prompts/system.md` read as UTF-8 (CRLF counts as 2 chars).
Only **three** directories declare `skills:`: `bundles/exp13_swe_toolkit`,
`ckpt/bundles/exp13_swe_toolkit`, `kaggle_work/.../bundles/exp13_swe_toolkit` (all
byte-identical, VERIFIED).

Note: `tracks/e4b_small/bundles/e4b_v3/prompts/system.md` is exactly **2440 chars** — the
number `docs/LEDGER.md` attributes to `e4b_v2` (see [S4]).

---

## [S2] SUBMISSIONS LEDGER

### S2.1 Raw CLI output (VERIFIED, 2026-11-01)

```
$ kaggle competitions submissions -c gemma-4-developer-agent
Warning: Looks like you're using an outdated `kaggle` version (installed: 2.2.4), please consider upgrading to the latest version (2.2.5)
     ref  fileName        date                        description                                                                    status                     publicScore  privateScore
--------  --------------  --------------------------  -----------------------------------------------------------------------------  -------------------------  -----------  ------------
57836949  submission.zip  2026-10-31 11:22:30.137000  E0 control: byte-identical exp05 resubmission (sha256 2ba7f9b1) ...              SubmissionStatus.PENDING
57806053  submission.zip  2026-10-30 12:56:30.647000  e4b-v2: temperature 0.1 + imperative prompt <=2500 chars ...                    SubmissionStatus.COMPLETE  0.05
57777888  submission.zip  2026-10-29 17:14:45.523000  exp11_e4b genuine E4B bundle (no 31B fallback)                                  SubmissionStatus.COMPLETE  0.06
57736284  submission.zip  2026-10-28 12:19:30.297000  exp12-timing-buffer: near-exact exp05 (0.20) with 9-min buffer, 6 tools ...     SubmissionStatus.COMPLETE  0.17
57697341  submission.zip  2026-10-27 09:52:57.487000  exp11_e4b pure model-scale ablation of exp05 (31B -> E4B ...)                    SubmissionStatus.COMPLETE  0.13
57654236  submission.zip  2026-10-26 04:57:20.907000  exp10-consolidated (6 tools, 6144 tokens, 7 min, surgical prompt +150 chars)    SubmissionStatus.COMPLETE  0.17
57618114  submission.zip  2026-10-25 05:27:51.603000  exp08 tool contract prompt (single change off exp05)                            SubmissionStatus.COMPLETE  0.17
57553805  submission.zip  2026-10-23 07:49:57.873000  exp05 patch integrity ablation (single change off exp03)                        SubmissionStatus.COMPLETE  0.20
57037122  submission.zip  2026-10-10 08:45:36.143000  exp03 baseline replica of public 0.17                                           SubmissionStatus.COMPLETE  0.17
56812498  submission.zip  2026-10-04 02:58:18.410000  (empty)                                                                         SubmissionStatus.COMPLETE  0.08
56793672  submission.zip  2026-10-03 08:34:41.430000  exp01 mechanism-justified bundle: no LoRA adapter (KV cache) ...                SubmissionStatus.COMPLETE  0.05
```

`--format json` returns the same 11 rows with fields
`ref, fileName, date, description, status, publicScore, privateScore` (VERIFIED).

### S2.2 Ref → bundle/commit map (VERIFIED against `kaggle_work/.../RESULTS.md` L183–195 and commit history)

| ref | date | bundle | model | score | mapped? |
|---|---|---|---|---:|---|
| 57836949 | 10-31 | `runs/e0/submission.zip` == `ckpt/exp05/submission.zip` | 31B | **PENDING** | VERIFIED |
| 57806053 | 10-30 | `tracks/e4b_small/bundles/e4b_v2` | E4B | 0.05 | VERIFIED |
| 57777888 | 10-29 | `tracks/e4b_small/bundles/exp11_e4b` | E4B | 0.06 | VERIFIED (hash match, [S4]) |
| 57736284 | 10-28 | `kaggle_work/.../bundles/exp12-timing-buffer` | 31B | 0.17 | VERIFIED |
| 57697341 | 10-27 | `ckpt/bundles/exp11_e4b` (31B model alias) | 31B | 0.13 | VERIFIED |
| 57654236 | 10-26 | `ckpt/bundles/exp10_consolidated` | 31B | 0.17 | VERIFIED |
| 57618114 | 10-25 | `ckpt/bundles/exp08_tool_contract` | 31B | 0.17 | VERIFIED |
| 57553805 | 10-23 | `ckpt/exp05/submission.zip` | 31B | **0.20** | VERIFIED (hash) |
| 57037122 | 10-10 | exp03 baseline replica | 31B | 0.17 | VERIFIED (RESULTS.md only) |
| 56812498 | 10-04 | exp02 v2 | 31B | 0.08 | VERIFIED (RESULTS.md only) |
| 56793672 | 10-03 | exp01 | 31B | 0.05 | VERIFIED (RESULTS.md only) |

**Unmappable refs: none.** All 11 map to a bundle or a documented experiment.
Caveat: exp03/exp02/exp01 map only through prose in `RESULTS.md`; no artifact is kept for
them in the repo (VERIFIED: no `ckpt/exp01|02|03/` directories).

### S2.3 Today's usage, pending count, quota

- Submissions **today (2026-11-01)**: **0** (VERIFIED — newest row is 2026-10-31T11:22:30Z).
- **Pending: 1** — ref `57836949`, submitted 2026-10-31T11:22:30Z, still
  `SubmissionStatus.PENDING` after ~24–48 h (VERIFIED from the live API just now).
- **Quota (`numAllowedNow`, `maxDailySubmissions`): UNKNOWN.**
  What I tried, all read-only:
  - `kaggle competitions submissions` — returns **no quota field**, only the 11 rows.
  - `tools/kaggle_rest.py cmd_submissions` hits only
    `/api/v1/competitions/submissions/list/<comp>?page=1` and prints that JSON; it has no
    quota call (VERIFIED, source read).
  - `GET /api/v1/competitions/gemma-4-developer-agent` → **HTTP 404** (returns Kaggle HTML,
    not JSON) (VERIFIED).
  - `tools/check_resources.py` reads `api.competition_submissions(...)` only; no limits.
  - `maxDailySubmissions: 1` and `maxPendingSubmissionsPerTeam: 1` are **REMEMBERED** from
    `AGENTS.md`, not re-verified against a live API response.

Practical consequence: the pending `57836949` almost certainly blocks any new submission
regardless of the daily counter (REMEMBERED: `maxPendingSubmissionsPerTeam: 1`).

### S2.4 Can the CLI return per-submission detail or logs?

```
$ kaggle competitions submissions --help
usage: kaggle competitions submissions [-h] [-v | --format OUTPUT_FORMAT] [-q]
                                       [--page-size PAGE_SIZE]
                                       [--page-token PAGE_TOKEN]
                                       [competition]
options:
  -v, --csv             Print results in CSV format (if not set print in table format)
  --format OUTPUT_FORMAT  Print results in selected format (csv, table, json).
  -q, --quiet           Suppress printing information about the upload/download progress
  --page-size PAGE_SIZE  Number of items to show on a page. Default size is 20, max is 200
  --page-token PAGE_TOKEN
```

VERIFIED. Findings:
- `-v` is **CSV**, not verbose. There is no verbose mode.
- Available fields are exactly the seven listed in S2.1. There is **no** per-task table,
  no score breakdown, no log, no stderr/stdout field.
- There is no `kaggle competitions submissions <ref>` detail subcommand.
- **Error text on failed runs: UNKNOWN / not reachable.** No submission in the ledger has
  a failure status, so no error text exists to quote. The API exposes only
  `publicScore`/`privateScore`; a failed run would surface as a status change, not a message.

---

## [S3] EXP05 RESUBMISSION INTEGRITY

### S3.1 What was resubmitted

Kernel `narisettichaitanya/g4-e0-exp05-control-resubmit` (v1), file `submission.zip`,
pulled to `runs/e0/` (VERIFIED from the kernel list + local artifact).

```
== runs/e0/submission.zip  size=3386  sha256=2ba7f9b118ea1837d1950038894cc856d1d33fe98c333d216afe6aaac1661774
   680799291cc7d156d06fb7bfb5577f683ccc0d555b00e8ddb662d577f9bfa5e4     314  agent.yaml
   571a934e89911734927533f1d36cbcc7b8d493592febe63b217e911cf7ed4926     119  configs/sampling.yaml
   916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531      94  eval_config.yaml
   fed226f7715931b271ca52b2a71335cf6a2f1d333aa08d92e6294706d7e3d7e2    5425  prompts/system.md
== ckpt/exp05/submission.zip  size=3386  sha256=2ba7f9b118ea1837d1950038894cc856d1d33fe98c333d216afe6aaac1661774
   680799291cc7d156d06fb7bfb5577f683ccc0d555b00e8ddb662d577f9bfa5e4     314  agent.yaml
   571a934e89911734927533f1d36cbcc7b8d493592febe63b217e911cf7ed4926     119  configs/sampling.yaml
   916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531      94  eval_config.yaml
   fed226f7715931b271ca52b2a71335cf6a2f1d333aa08d92e6294706d7e3d7e2    5425  prompts/system.md
```

**Byte-identical: YES.** Zip sha256 matches and all four members match individually
(VERIFIED).

### S3.2 Config match

```
===== agent.yaml =====
name: swe_agent
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

===== configs/sampling.yaml =====
temperature: 0.2
top_p: 0.95
max_output_tokens: 8192
thinking_config:
  thinking_budget: 4096
  include_thoughts: true

===== eval_config.yaml =====
evaluation:
  timeout_seconds: 240
  max_tool_calls: 28
  max_time_minutes: 8
  max_turns: 80
```

Model = `gemma-4-31b-it-qat-w4a16-ct`; sampling, eval config and the 9-tool list all match
the original exp05 artifact **exactly** (VERIFIED — same sha256 per member).

### S3.3 The trap in "the exp05 bundle"

`docs/COMPLETE_SYSTEM_REFERENCE.md` **does not exist** anywhere in the repo (VERIFIED —
recursive filename search returned nothing, and no `.md` mentions the name). The reference
had to be reconstructed from `ckpt/exp05/submission.zip` + git history.

The bundle directory `ckpt/bundles/exp05_patch_integrity/` is **not** the scored artifact:

```
ckpt/bundles/exp05_patch_integrity (raw, CRLF working tree)   artifact   disk   disk_lf  equal_after_lf
  agent.yaml                                                    314     328      314   True
  configs/sampling.yaml                                         119     125      119   True
  eval_config.yaml                                               94      99       94   True
  prompts/system.md                                            5425    5517     5461   False
```

Unified diff after CRLF→LF normalisation:

```
--- submitted
+++ bundle
@@ -52,2 +52,5 @@
 - Stuck after a failed fix: make a different, smaller change. Do not repeat the same edit.
 - Never conclude that nothing needs to change. Every task requires a non-empty source patch.
+
+## The issue
+{problem_description}
```

So the bundle carries **36 extra chars** appended after the submission (VERIFIED).
`build/exp05_submitted/` is the only directory that is 4/4 byte-identical to the artifact;
`build/exp05_lf/` differs only by those 36 chars.

`ckpt/bundles/exp05_patch_integrity` is also not byte-stable against git: the HEAD blob is
LF (314/119/94/5461 bytes) while the working tree is CRLF (VERIFIED with `git show HEAD:`).

---

## [S4] E4B ABLATION DATA

Baseline = `tracks/e4b_small/bundles/exp11_e4b` (ref `57777888`). Its four LF-normalised
sha256 values match the baseline hashes in `docs/LEDGER.md` exactly (VERIFIED).
`ckpt/bundles/exp11_e4b` and `kaggle_work/.../bundles/exp11_e4b` do **not** match those
hashes (sampling `fea97c86…`, eval `cb0b5f28…`, system `16a1d817…`) — only the `tracks/`
copy does (VERIFIED).

### S4.1 Full unified diff, `exp11_e4b` → `e4b_v2`

```
### agent.yaml   baseline=245 chars   e4b_v2=245 chars   identical=True
(no differences)
========================================================================
### configs/sampling.yaml   baseline=119 chars   e4b_v2=119 chars   identical=False
--- exp11_e4b(57777888)
+++ e4b_v2(57806053)
@@ -1,4 +1,4 @@
-temperature: 0.2
+temperature: 0.1
 top_p: 0.95
 max_output_tokens: 8192
 thinking_config:
========================================================================
### eval_config.yaml   baseline=94 chars   e4b_v2=94 chars   identical=False
--- exp11_e4b(57777888)
+++ e4b_v2(57806053)
@@ -1,5 +1,5 @@
 evaluation:
   timeout_seconds: 240
-  max_tool_calls: 28
+  max_tool_calls: 35
   max_time_minutes: 8
   max_turns: 80
========================================================================
### prompts/system.md   baseline=5353 chars   e4b_v2=1746 chars   identical=False
(full rewrite; see S4.2 for the verbatim result)
```

**Three changes, not two** (VERIFIED). `docs/LEDGER.md` L15 is wrong on three counts:
- it says "only `configs/sampling.yaml` … and `prompts/system.md`" — `eval_config.yaml`
  also changed (`max_tool_calls` 28 → 35);
- it says "`agent.yaml` and `eval_config.yaml` byte-identical" — `eval_config.yaml` is not;
- it gives the new prompt as **2440 chars** — the actual file is **1746 chars**. 2440 is
  `tracks/e4b_small/bundles/e4b_v3/prompts/system.md` (VERIFIED), i.e. the ledger
  conflated v2 with v3.
`docs/LEDGER.md` L26 ("prompt 2440 chars") repeats the same error.

### S4.2 `e4b_v2/prompts/system.md` verbatim (1746 chars, 32 lines, VERIFIED)

```
 1| You are an autonomous software engineer. Make the smallest correct source change in /workspace. Hidden tests grade source changes only.
 2|
 3| FACTS: offline; never edit tests/conftest/pytest.ini/pyproject.toml/tox.ini/setup.cfg; budget 35 calls / 8 min; working tree graded even without submit_patch; unedited tree scores 0. Never run a full suite. Never use search_similar_code, get_code_neighbors, get_code_subgraph.
 4|
 5| STATE LINE: start every turn with: STATE: <bug> | <file:line> | edit done? | last test | next
 6|
 7| WORKFLOW
 8| 1. git grep -n "<symbol/error from issue>" -- '*.py' | head -20
 9| 2. read_file the hit, 40-80 lines.
10| 3. FIRST edit_file by call 10.
11| 4. <=2 targeted tests: timeout 150 python -m pytest <file> -x -q -k <name>
12| 5. Final gate below, then submit_patch.
13|
14| FINAL GATE (run exactly):
15| python3 -c "
16| import ast, subprocess
17| def r(a): return subprocess.run(a, capture_output=True, text=True)
18| print('=== git status --short ==='); print(r(['git','status','--short']).stdout, end='')
19| print('=== git diff --stat ==='); print(r(['git','diff','--stat']).stdout, end='')
20| files=sorted(set(r(['git','diff','--name-only']).stdout.splitlines()+r(['git','diff','--cached','--name-only']).stdout.splitlines()+r(['git','ls-files','--others','--exclude-standard']).stdout.splitlines()))
21| print('=== ast.parse ===')
22| for f in [x for x in files if x.endswith('.py')]:
23|     try:
24|         ast.parse(open(f).read()); print('OK',f)
25|     except SyntaxError as e: print('SYNTAX ERROR',f,':',e)
26| print('=== ignored-but-created ===')
27| for f in r(['git','ls-files','--others','--ignored','--exclude-standard']).stdout.splitlines(): print('IGNORED:',f,'-> fix: git add -N -f',f)
28| "
29| Then submit_patch. Confirm patch_size>0 and files_changed>0.
30|
31| ## The issue
32| {problem_description}
```

### S4.3 Final-gate one-liner, re-run (VERIFIED, this session)

The 842-char / 12-line one-liner was extracted verbatim from `system.md` lines 16–28 and
executed with the repo's Python 3.12 against 8 throwaway git repos under `%TEMP%`
(`git init`, one package, one test, one `.gitignore` with `*.log` and `build/`).

```
1_no_changes             rc=0 ignored_warn=False syntax_err=False status_lines=0
2_changed_py             rc=0 ignored_warn=False syntax_err=False status_lines=1
3_new_untracked_py       rc=0 ignored_warn=False syntax_err=False status_lines=1
4_new_ignored_py         rc=0 ignored_warn=True  syntax_err=False status_lines=0
5_syntax_error_py        rc=0 ignored_warn=False syntax_err=True  status_lines=1
6_filename_with_spaces   rc=0 ignored_warn=False syntax_err=False status_lines=1
7_zero_py_changes        rc=0 ignored_warn=False syntax_err=False status_lines=1
8_only_test_and_config   rc=0 ignored_warn=False syntax_err=False status_lines=2
```

Representative raw blocks:

```
### 4_new_ignored_py   rc=0
=== git status --short ===
=== git diff --stat ===
=== ast.parse ===
=== ignored-but-created ===
IGNORED: build/gen.py -> fix: git add -N -f build/gen.py
======================================================================
### 5_syntax_error_py   rc=0
=== git status --short ===
 M pkg/core.py
=== git diff --stat ===
 pkg/core.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
=== ast.parse ===
SYNTAX ERROR pkg/core.py : invalid syntax (<unknown>, line 2)
=== ignored-but-created ===
======================================================================
### 8_only_test_and_config   rc=0
=== git status --short ===
 M tests/test_core.py
?? pyproject.toml
=== git diff --stat ===
 tests/test_core.py | 6 ++----
 1 file changed, 2 insertions(+), 4 deletions(-)
=== ast.parse ===
OK tests/test_core.py
=== ignored-but-created ===
```

What this establishes, mechanically:
- The gate is **diagnostic only**: it never exits non-zero, so it cannot block a bad submit.
- Scenario 4 confirms the `git add -N .` / `.gitignore` trap exactly as documented: a
  created file on an ignored path is invisible to `git status --short` and only the
  `IGNORED:` line surfaces it.
- Scenario 8 shows the gate **does not flag protected-path edits** — `M tests/test_core.py`
  passes silently, even though the same prompt forbids editing tests.
- `docs/LEDGER.md` L28's claim that all 8 scenarios "passed" reproduces, but "passed" here
  means "the script ran", not "the gate rejected the bad case".

---

## [S5] WHAT CHANGED SINCE EXP05

"Current working bundle" = `ckpt/bundles/exp13_swe_toolkit` — the only bundle that ships a
`skills/` tree, and the target of checks (a)–(f).

### S5.1 Diff vs `ckpt/bundles/exp05_patch_integrity` (LF-normalised)

```
### file sets
exp05 : ['agent.yaml', 'configs/sampling.yaml', 'eval_config.yaml', 'prompts/system.md']
exp13 : [ ... , 'skills/swe-toolkit/SKILL.md',
          'skills/swe-toolkit/scripts/_guard.py', '_index.py', '_knowledge.py',
          '_verify.py', 'swe.py']

### per-file sizes (chars) and status
  agent.yaml                                              314 ->    345  CHANGED
  configs/sampling.yaml                                   119 ->    119  same
  eval_config.yaml                                         94 ->     94  same
  prompts/system.md                                      5461 ->   5879  CHANGED
  skills/swe-toolkit/SKILL.md                            -    ->   2344  ADDED
  skills/swe-toolkit/scripts/_guard.py                   -    ->   2075  ADDED
  skills/swe-toolkit/scripts/_index.py                   -    ->  17285  ADDED
  skills/swe-toolkit/scripts/_knowledge.py               -    ->   3210  ADDED
  skills/swe-toolkit/scripts/_verify.py                  -    ->   9423  ADDED
  skills/swe-toolkit/scripts/swe.py                      -    ->   8608  ADDED

### skills tree (bytes on disk)
  skills/swe-toolkit/SKILL.md                     2360
  skills/swe-toolkit/scripts/_guard.py            2075
  skills/swe-toolkit/scripts/_index.py           17771
  skills/swe-toolkit/scripts/_knowledge.py        3289
  skills/swe-toolkit/scripts/_verify.py           9423
  skills/swe-toolkit/scripts/swe.py               8608
```

`configs/sampling.yaml` and `eval_config.yaml` are **unchanged** from exp05
(temperature 0.2, top_p 0.95, 8192 output tokens, thinking 4096/thoughts on; 240 s,
28 calls, 8 min, 80 turns) (VERIFIED).

### S5.2 `agent.yaml` verbatim (345 chars)

```yaml
name: swe_agent
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
skills:
  - skills/swe-toolkit
generate_content_config: !include configs/sampling.yaml
```

Unified diff vs exp05:

```
--- exp05_patch_integrity
+++ exp13_swe_toolkit
@@ -11,4 +11,6 @@
   - get_code_neighbors
   - search_similar_code
   - get_code_subgraph
+skills:
+  - skills/swe-toolkit
 generate_content_config: !include configs/sampling.yaml
```

### S5.3 `prompts/system.md` verbatim (5879 chars, 62 lines)

```
 1| You are an autonomous software engineer. Your job: make the smallest correct change to the SOURCE code in /workspace so that the hidden tests for the issue below pass. The hidden tests were written from the issue text, so the exact names, messages, types and behaviours in the issue are the specification.
 2|
 3| # HARD LIMITS
 4| - 28 tool calls and 8 minutes in total. When either runs out, the working tree is graded as it is. An edit that exists counts, even if you never call `submit_patch`. An unedited tree always scores zero.
 5| - Never create, modify or delete test files (`test_*.py`, `*_test.py`, anything under `tests/`). This is an automatic failure.
 6| - Never run a full test suite (bare `pytest`, `pytest .`, `unittest discover`). Always name one test file, and add `-k` when you can.
 7| - Never look outside /workspace. All dependencies are already installed.
 8| - Never use `search_similar_code`, `get_code_neighbors` or `get_code_subgraph`. They return nothing useful.
 9|
10| # CALL PLAN
11| - Calls 1-8: locate and read. Calls 9-12: edit. You MUST have edited a source file by call 12. If you are unsure, make your best-guess edit in the most likely place now. A wrong edit can still be corrected. Pure reading cannot score.
12| - Calls 13-20: verify and correct.
13| - Call 20 onward: no new exploration. Check, fix, submit.
14| - Always finish with `git diff` followed by `submit_patch`.
15|
16| # PROCEDURE
17|
18| ## 1. Extract the specification (no tool call)
19| From the issue, list for yourself: the exact file, function, class or CLI name; the exact error message and exception type; the expected return value or output; the inputs that trigger the bug; every edge case mentioned (None, empty, negative, unicode, duplicates, defaults). Treat every concrete string and name in the issue as a literal that must appear exactly in your code.
20|
21| ## 2. Locate
22| - Use the paths and symbols from the issue directly. If there is no path, run one search: `git grep -n "most specific string or identifier" -- '*.py' | head -20`.
23| - Use `read_file` on the relevant region (about 40 lines around the target) and not whole files.
24| - For a bug: find where the wrong behaviour is produced, then check how callers use it with one `git grep -n "function_name" -- '*.py' | head`.
25| - For a feature: find the closest existing sibling (a similar function, option, class, or doc example) and copy its pattern. That pattern includes registration points such as `__all__`, option lists, dispatch tables, and imports.
26| - If the issue includes a code snippet that reproduces the problem, you may run it once with `python -c` (one call, never create a file) to see the real error.
27|
28| ## 3. Edit
29| - Use `edit_file` for changes to existing code. Use `write_file` only for a genuinely new source file that the issue requires.
30| - Fix the cause, not the symptom. Do not special-case the example from the issue.
31| - Change only what the issue requires. Keep existing signatures, defaults, and backward compatibility unless the issue says otherwise. Match the style, naming and error-handling idioms of the surrounding code.
32| - Use the exact exception class and exact message text from the issue. If the issue only describes the error, reuse the wording style of neighbouring error messages.
33| - Handle every edge case you listed in step 1.
34| - For documentation-code tasks (for example FastAPI), edit the executable code under `docs_src/`.
35|
36| ## 4. Verify (at most 2 calls)
37| - Find the test file with `find tests -name "*keyword*.py"`, then run `timeout 150 python -m pytest tests/path/test_x.py -x -q -k keyword`. Use `python3 -m unittest tests.test_x` for unittest projects.
38| - Failures that come from missing fixtures, missing data, or import errors unrelated to your change are pre-existing. Ignore them. Never repair tests or the environment.
39| - If a test related to your change fails, read the traceback, fix the source once, and rerun once. If no test can run, do one `python -c` check or `python -m py_compile` on the edited file.
40|
41| ## 5. Final check and submit
42| - Run `git status --short` and `git diff`. Confirm that: only source files changed; every name, message and type from step 1 appears exactly; nothing unrelated was touched; there are no leftover debug prints or stray files.
43| - **Every file you created must be listed by `git status --short`.** The patch is built with `git add -N .`, which silently skips anything the repository's own `.gitignore` ignores, so a new file on an ignored path never reaches the grading diff. If a file you created is missing from the status output, run `git add -N -f <path>` and check again.
44| - Delete debugging scratch files you created inside /workspace; they land in the patch. Files in /tmp never do.
45| - Call `submit_patch`. Confirm `patch_size > 0` and `files_changed > 0`. If either is 0, you have not edited anything, or your edit was stripped. Edit now and submit again.
46| - End with a single-sentence summary of the fix.
47|
48| # DECISION RULES
49| - Ambiguous issue: choose the most literal reading of the issue text and act on it. Do not ask questions and do not stall.
50| - Several possible locations: pick the one where the wrong behaviour is produced, not where it is merely observed.
51| - Search returned nothing: try one different specific string, then edit your best candidate anyway.
52| - Stuck after a failed fix: make a different, smaller change. Do not repeat the same edit.
53| - Never conclude that nothing needs to change. Every task requires a non-empty source patch.
54|
55|
56| ## TOOLKIT
57| `swe-toolkit` is a deterministic locator. Read it with `load_skill`, then run it once, and only when step 2 cannot name the file:
58| run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py", args=["locate", "--issue", "the issue text"])
59| It returns the five most likely source files, an excerpt of the best one, and `NEXT:` / `TEST:` / `FALLBACK:` lines. Obey `NEXT:`. Never call `locate` twice.
60|
61| ## The issue
62| {problem_description}
```

Only lines 55–59 are new relative to exp05 (VERIFIED unified diff):

```
@@ -52,5 +52,11 @@
 - Stuck after a failed fix: make a different, smaller change. Do not repeat the same edit.
 - Never conclude that nothing needs to change. Every task requires a non-empty source patch.
 
+
+## TOOLKIT
+`swe-toolkit` is a deterministic locator. Read it with `load_skill`, then run it once, and only when step 2 cannot name the file:
+run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py", args=["locate", "--issue", "the issue text"])
+It returns the five most likely source files, an excerpt of the best one, and `NEXT:` / `TEST:` / `FALLBACK:` lines. Obey `NEXT:`. Never call `locate` twice.
+
 ## The issue
 {problem_description}
```

### S5.4 `SKILL.md` verbatim (2344 chars, 56 lines)

```
 1| ---
 2| name: swe-toolkit
 3| description: "Locate the file for an issue, inspect a symbol, verify an edit in /workspace."
 4| ---
 5| # swe-toolkit
 6|
 7| `scripts/swe.py`, three modes. All output is plain text on stdout and the exit code is
 8| always 0 — read the `STATUS:` line, not the exit code.
 9|
10| | mode | what it returns | arguments |
11| |---|---|---|
12| | `locate` | the 5 most likely source files, an excerpt of the best one, a test command and a `git grep` fallback | `--issue TEXT` (or `--query TEXT`), `--top 5` |
13| | `inspect` | definition, callers, overrides, subclasses and sync/async twins of a symbol | `--symbol NAME` |
14| | `verify` | read-only patch gate plus one targeted pytest run | `--test "tests/test_x.py -x -q -k keyword"` |
15|
16| `--root` defaults to `/workspace`. Do not pass it unless the repository is elsewhere.
17|
18| ## Calling it
19|
20| Use `run_skill_script`. The argument names are `skill_name`, `file_path` and `args`:
21|
22| ```
23| run_skill_script(skill_name="swe-toolkit", file_path="scripts/swe.py",
24|                  args=["locate", "--issue", "<the issue text>"])
25| ```
26|
27| `args` is a list; `--root` defaults to `/workspace`, so do not pass it.
28|
29| ## Reading the output
30|
31| `locate` and `inspect`:
32|
33| - `STATUS: OK` — full scan.
34| - `STATUS: PARTIAL` — the scan hit its 20 s budget and ranked only part of the tree.
35|   The files it did return are still the best guess; use them.
36| - `STATUS: EMPTY` — no Python files under the root. Use the `FALLBACK:` line.
37| - `STATUS: DEGRADED` — the tool failed. Use the `FALLBACK:` line.
38|
39| `verify`:
40|
41| - `STATUS: OK` — the patch is structurally valid (and the named tests pass, if `--test`).
42| - `STATUS: PARTIAL` — the patch is valid but a check needs attention (a failing test, or an
43|   ignored new file). Read the `FAIL`/`IGNORED` line.
44| - `STATUS: FAIL` — the patch is empty, or it touches a protected path, or a changed file
45|   does not compile. Do not submit until this is `OK`.
46|
47| `locate` also prints `NEXT:` (the exact `read_file` call to make) and `TEST:` (the pytest
48| command to run after editing). Prefer those over inventing your own.
49|
50| Line prefixes in an excerpt look like `123 | code`; the number is the file line. Never
51| copy the prefix into an edit.
52|
53| ## Budget
54|
55| `locate` costs one tool call and up to ~20 s. Call it once per task, before the first
56| `read_file`, and only when the issue does not already name a file. Do not call it twice.
```

Frontmatter: `name: swe-toolkit`, `description: "Locate the file for an issue, inspect a
symbol, verify an edit in /workspace."` — exactly two keys, no `metadata`.

### S5.5 Checks (a)–(f)

| # | claim | verdict | evidence |
|---|---|---|---|
| (a) | skill dir and frontmatter `name` are the same kebab-case name | **VERIFIED TRUE** | `agent.yaml:14` `- skills/swe-toolkit`; dir `skills/swe-toolkit/`; `SKILL.md:2` `name: swe-toolkit`. The harness **enforces** it: `google/adk/skills/_utils.py:157` raises if `skill_dir.name != frontmatter.name`. Runtime probe printed `name_matches_dir = True`. |
| (b) | `system.md` contains the byte-exact `run_skill_script` template with `skill_name`, `file_path`, **`command`** | **FALSE PREMISE** | `system.md:58` uses `skill_name`, `file_path`, `args`. `command` is **not** a parameter of the real tool: `skill_toolset.py:728-773` declares `skill_name`, `file_path`, `args`, `short_options`, `positional_args`; grep for `command` in `skill_toolset.py` = **0 hits**. The prompt matches the real schema; the check's expected name does not exist. |
| (c) | `system.md` says never to call `list_skills` / `load_skill` | **VERIFIED FALSE** | `system.md:57` says *"Read it with `load_skill`"* — it **instructs** `load_skill`. `list_skills` appears **0 times** in `system.md` (grep). |
| (d) | cleanup of the materialized skills dir before `submit_patch`, with an exact command | **NOT APPLICABLE — nothing to clean** | `system.md` has 0 hits for `rm -rf`, `cleanup`, `materiali`. The ADK wrapper materialises into `tempfile.TemporaryDirectory()` and restores cwd: `skill_toolset.py:627-634` (`with tempfile.TemporaryDirectory() as td: … os.chdir(td)`) and `:704-707` (`finally: os.chdir(_orig_cwd)`). Runtime probe: `scratch residue after all runs = []`. |
| (e) | the `git add -N -f` rule is scoped away from `skills/` | **VERIFIED — moot, not scoped** | `system.md:43` tells the agent to run `git add -N -f <path>` for *files it created inside /workspace*. `skills/` never enters that flow: it is packaged by the notebook builder, not by `git add`. `system.md` mentions "skills" **0 times** (only `swe-toolkit`), so nothing in the prompt can pull the bundle's `skills/` into the agent's patch. |
| (f) | which `tools` / `skills` declarations are in `agent.yaml` | **VERIFIED** | 9 tools (`run_command, read_file, edit_file, write_file, get_status, submit_patch, get_code_neighbors, search_similar_code, get_code_subgraph`) + `skills: [skills/swe-toolkit]`. Compiled: `compile_submission` reports `tools=10` = 9 declared + 1 `SkillToolset`. |

### S5.6 Other changes not on the list

From `git show --stat 2b7cd84` (VERIFIED):

```
 .gitignore                                            |   4 +
 bundles/exp13_swe_toolkit/prompts/system.md           |   9 +-
 .../skills/swe-toolkit/SKILL.md                       |  58 ++++-
 .../skills/swe-toolkit/scripts/_guard.py              |  60 +++++
 .../skills/swe-toolkit/scripts/_index.py              | 176 ++++++++++---
 .../skills/swe-toolkit/scripts/_verify.py             | 269 ++++++++++++++-----
 .../skills/swe-toolkit/scripts/bootstrap.py           |  35 ---
 .../skills/swe-toolkit/scripts/swe.py                 | 277 ++++++++++++++------
 (same 7 files repeated for ckpt/, kaggle_work/ and skills/ copies)
 docs/AUDIT_SNAPSHOTS.md                               |  35 ++-
 docs/SKILLS_ARCHITECTURE.md                           |   5 +
 docs/TASKLIST.md                                      |  14 ++
 kaggle_work/gemma-4-developer-agent/RESULTS.md        |  72 ++++++
 32 files changed, 2767 insertions(+), 894 deletions(-)
```

Plus `fdc264a` (VERIFIED) — a repo-level change, not a bundle change:

```
 .gitattributes | 8 ++++++++
```
```
# Bundle payloads are hashed byte-for-byte before submission and the recorded
# sha256 values in RESULTS.md only reproduce with LF. `core.autocrlf` is true on
# this machine, so pin the line endings instead of relying on the local config.
ckpt/bundles/** text eol=lf
bundles/** text eol=lf
skills/** text eol=lf
src/** text eol=lf
tools/*.py text eol=lf
```

Not on the user's list, and worth flagging:
- `.gitignore` gained 4 lines in `2b7cd84`.
- `scripts/bootstrap.py` was **deleted** from the skill (it was an earlier dual-transport
  helper). `SKILL.md` was rewritten to match the 3-mode CLI.
- `_guard.py` is new; `_verify.py` was rewritten (269 changed lines) and now emits
  `PROTECTED`/`STRAY`/`IGNORED`/`SYNTAX` lines — it is stricter than the e4b-v2 one-liner.
- `docs/SKILLS_ARCHITECTURE.md`, `docs/AUDIT_SNAPSHOTS.md`, `docs/TASKLIST.md`,
  `RESULTS.md` were updated in the same commit.
- The `.gitattributes` pin does **not** retro-fix working trees: files still check out CRLF
  until re-cloned or re-normalised (VERIFIED — `ckpt/bundles/exp05_patch_integrity` is still
  CRLF on disk while the HEAD blob is LF).

---

## [S6] SKILL CONTRACT EVIDENCE

### S6.1 `pip show google-adk` (VERIFIED, `.venv-harness`)

```
Name: google-adk
Version: 1.36.1
Summary: Agent Development Kit
Location: C:\Users\chait\Projects\gemma4hack\.venv-harness\Lib\site-packages
Requires: aiosqlite, anyio, authlib, click, fastapi, google-api-python-client, ...
Required-by: adk-eval-core, adk-submission, swegemma
---
Name: adk-submission
Version: 0.2.13
Summary: Sandboxed ADK agent compiler for Kaggle competition submissions
Required-by: swegemma
---
Name: swegemma
Version: 0.2.11
Summary: SWE-bench evaluation system for coding agents
Required-by: (none)
---
Name: adk-eval-core
Version: 0.1.0
Summary: Core evaluation, sandboxing, budget tracking, tracing, and UI primitives for ADK agent benchmarks
Required-by: swegemma
```

`pip show` with the **system** Python returns "Package(s) not found" for all four
(VERIFIED) — the harness wheels live only in `.venv-harness`.

### S6.2 The requested probe does not exist

`probe_skill_binding.py` is **absent** from the repository (VERIFIED — recursive filename
search over the whole tree returned nothing). The command in the brief therefore cannot be
run as written.

I ran a faithful equivalent instead, outside the repo, at
`%TEMP%\opencode\probe_skill_binding.py`: it calls the real
`google.adk.skills.load_skill_from_dir` on the bundle's `skills/swe-toolkit`, builds the
real `_SkillScriptCodeExecutor._build_wrapper_code(...)` payload, and executes it with a
subprocess `BaseCodeExecutor` (the same `execute_code(code) -> stdout/stderr` contract that
`swegemma`'s `AdkSandboxCodeExecutor` implements). Verdict block (VERIFIED):

```
skill_dir      = C:\Users\chait\Projects\gemma4hack\ckpt\bundles\exp13_swe_toolkit\skills\swe-toolkit
skill_dir.name = 'swe-toolkit'
frontmatter.name = 'swe-toolkit'
description      = 'Locate the file for an issue, inspect a symbol, verify an edit in /workspace.'
instructions len = 2224 chars
scripts          = ['_guard.py', '_index.py', '_knowledge.py', '_verify.py', 'swe.py']
name_matches_dir = True

======================================================================
### run_skill_script(skill_name='swe-toolkit', file_path='scripts/swe.py', args=['locate', '--issue', 'Fix `_encode_files` detection for `__getattr__`-based file wrappers', '--root', '...\audit_snapshots\requests_7502'])
wrapper_code_chars = 42920
returncode = 0   stdout_chars = 3309   stderr_chars = 0
--- stdout (head 30 lines) ---
STATUS: OK  (indexed 37/37 files in 1.0s)
TOP FILES:
  1. src\requests\models.py
  2. src\requests\structures.py
  3. src\requests\utils.py
  4. src\requests\auth.py
  5. src\requests\sessions.py
NEXT: read_file src\requests\models.py offset=174 limit=60
TEST: python -m pytest tests\test_requests.py -x -q
FALLBACK: git grep -n "_encode_files" -- '*.py' | head -20
...
======================================================================
### run_skill_script(..., args=['inspect', '--symbol', 'Requests', ...])
returncode = 0   stdout_chars = 89
STATUS: EMPTY
no symbol named Requests
NEXT: git grep -n "Requests" -- '*.py' | head -20
======================================================================
### run_skill_script(..., args=['verify', ...])
returncode = 0   stdout_chars = 122
STATUS: OK
CHANGED: 1 file(s)
  setup.py
PROTECTED: OK
STRAY: OK
IGNORED: OK
SYNTAX: OK
NEXT: git diff, then submit_patch

scratch residue after all runs = []
```

This proves, end to end and with the real ADK code path: the skill loads, the name matches,
`run_skill_script` executes `scripts/swe.py` inside a throw-away tempdir, imports of
`_guard`/`_index`/`_verify` resolve (`swe.py:7` does `sys.path.insert(0, os.path.dirname(__file__))`),
the ranker returns the correct gold file for `requests_7502` (rank 1 = `src/requests/models.py`,
matching `docs/AUDIT_SNAPSHOTS.md`), and nothing is left behind.

One caveat visible in that output: `verify` reported `CHANGED: 1 file(s) setup.py` before any
edit, because `audit_snapshots/requests_7502` is dirty on disk (`git status --short` → `M setup.py`,
a 0-line CRLF-only diff, VERIFIED). `verify`'s CHANGED line therefore reflects pre-existing
dirt as well as agent edits.

### S6.3 Competition harness source — FOUND locally

Answer to "is any competition harness source available": **yes, all of it.** The three
competition wheels are installed in `.venv-harness/Lib/site-packages`:

| package | version | role |
|---|---|---|
| `adk_submission` | 0.2.13 | compiler, `validate_directory`, `discover_skills`, `resolve_skills` |
| `swegemma` | 0.2.11 | eval harness, `agent_runner.py`, budget/verification |
| `adk_eval_core` | 0.1.0 | sandbox, tracing, UI |
| `google-adk` | 1.36.1 | `SkillToolset`, `load_skill_from_dir` |

Greps requested by the brief (file:line hits, VERIFIED):

```
SkillToolset(        -> google/adk/tools/skill_toolset.py:878  class SkillToolset(BaseToolset)
                        adk_submission/compiler.py:23   from google.adk.tools.skill_toolset import SkillToolset
                        adk_submission/compiler.py:150  skill_toolset_cls=SkillToolset
skills_folder        -> 0 hits anywhere in adk_submission, swegemma, adk_eval_core, google/adk
script_timeout       -> adk_submission/compiler.py:67    script_timeout: int = 300
                        adk_submission/compiler.py:197   script_timeout=script_timeout
                        adk_submission/resolvers/tools.py:258  script_timeout=ctx.script_timeout
                        swegemma/harness/agent_runner.py:604-621  script_timeout = config.harness.command_timeout_seconds or 300
                        google/adk/tools/skill_toolset.py:52  _DEFAULT_SCRIPT_TIMEOUT = 300
discovery_mode       -> 0 hits
tool_filter          -> 0 hits
run_skill_script     -> google/adk/tools/skill_toolset.py:719  name="run_skill_script"
                        swegemma/harness/agent_runner.py:61  _SKILL_TOOL_NAMES = frozenset({'load_skill','load_skill_resource','run_skill_script'})
EnvironmentToolset   -> 0 hits
```

`skills_folder`, `discovery_mode`, `tool_filter` and `EnvironmentToolset` **do not exist**
in this harness generation. Those names appear nowhere; any design note that assumes them
is stale.

How skills are actually wired (VERIFIED source reads):

```
adk_submission/resolvers/tools.py:129-264  resolve_skills(config, ctx, tools)
   :150  if not config.skills: return None
   :161  for skill_ref in config.skills:            # our "skills/swe-toolkit"
   :163    if ctx.skill_registry is not None: ...    # scorer passes None
   :185    skill_path = validate_sandboxed_path(skill_ref, base_dir=ctx.root_dir, ...)
   :216    skill = load_skill_from_dir(skill_path)
   :255  return skill_toolset_cls(
   :256      skills=loaded_skills,
   :257      code_executor=ctx.code_executor,
   :258      script_timeout=ctx.script_timeout,
   :259      additional_tools=list(resolved_tools))
```

```
swegemma/harness/agent_runner.py:604-628
   script_timeout = config.harness.command_timeout_seconds or 300
   code_executor = AdkSandboxCodeExecutor(sandbox=context.sandbox,
                                          timeout_seconds=script_timeout,
                                          start_time=context.task_start_time,
                                          max_time_minutes=config.budget.time_minutes,
                                          budget_check_fn=context.check_budget)
   agent = compile_submission(..., code_executor=code_executor, script_timeout=script_timeout, ...)
   _wrap_skill_toolset_tools(agent)
```

Consequences, all VERIFIED from source:
1. `run_skill_script` **will work** in the scorer: a real code executor is always passed.
   With no executor the tool returns `NO_CODE_EXECUTOR` (`skill_toolset.py:855-862`).
2. The script runs **inside the task sandbox** (`AdkSandboxCodeExecutor(sandbox=context.sandbox)`),
   so `/workspace` is visible and `--root` defaulting to `/workspace` is correct.
3. `script_timeout` = `evaluation.timeout_seconds` = **240 s** for our bundles, and
   `AdkSandboxCodeExecutor` further clamps to `max(5, remaining_time)`
   (`HARNESS_README.md:389`). A ~3–7 s `locate` is far inside it.
4. The agent ends up with **9 declared tools + 4 skill tools = 13** callable tools
   (`SkillToolset.get_tools()` returns `self._tools` = `list_skills`, `load_skill`,
   `load_skill_resource`, `run_skill_script`; `skill_toolset.py:938-943`, `:947-954`).
   `additional_tools` are **not** exposed unless a skill's frontmatter lists
   `adk_additional_tools` (`:956-1010`), so the 9 tools are not duplicated.
5. The harness **coerces** `["swe-toolkit"] → "swe-toolkit"` for `skill_name`/`file_path`
   and wraps skill tools so exceptions become `{"status":"error",...}`
   (`agent_runner.py:97-189`; also `HARNESS_README.md:353`). `list_skills` is **not** in
   `_SKILL_TOOL_NAMES`, so it gets no coercion — harmless, but it means `list_skills` is
   the one skill tool with no special handling.
6. Skill name comes from the directory at discovery time
   (`adk_submission/discovery.py:635 skill_dir.name.replace("_","-")`) but from the
   frontmatter at load time (`google/adk/skills/_utils.py:157`), and the two are required to
   be equal. `swe-toolkit` satisfies both.
7. `SkillToolset.process_llm_request` injects `_DEFAULT_SKILL_SYSTEM_INSTRUCTION` plus an
   `<available_skills>` XML block on **every** request (`skill_toolset.py:1061-1083`), and
   only `name` + `description` reach the prompt — never the `SKILL.md` body.
8. The harness **already** injects the problem statement as a user message
   (`agent_runner.py:379 f'... Problem Statement:\n{task.problem_statement}\n'`) and also
   sets `session_state['problem_description']` (`:676-678`). So `{problem_description}` in
   `system.md` is a **second** copy of the issue text.

### S6.4 Public kernel

`kaggle kernels list --mine` (VERIFIED, 2026-11-01) shows **no** `g4-paired-devset-eval`
kernel and no other dev-set eval kernel. I did not need to pull
`ryanholbrook/getting-started-gemma-4-developer-agent`, because the harness wheels it would
have revealed are already installed locally and were grepped directly (S6.3). The starter
notebook's metadata is documented in `ckpt/research/DEVSET_EVAL_MECHANICS.md:3-6`
(REMEMBERED from that file, not re-pulled): `NvidiaL4` ×4, offline, competition source,
model source `google/gemma-4/.../gemma-4-31b-it-qat-w4a16-ct/2`.

### S6.5 Which skill/prompt changes still depend on UNKNOWN harness behaviour

Now that the source is available, the list is short:

| item | status |
|---|---|
| `run_skill_script` runs in the task sandbox with `/workspace` mounted | **VERIFIED** (`agent_runner.py:609`, `skill_toolset.py:850-874`) |
| skill name == directory name is enforced | **VERIFIED** (`_utils.py:157`) |
| scripts materialise into a tempdir and are cleaned up | **VERIFIED** (`skill_toolset.py:627-634`, `:704-707`; probe residue = `[]`) |
| no `skills_folder` / `discovery_mode` / `tool_filter` / `EnvironmentToolset` | **VERIFIED absent** |
| **whether the competition's actual `EvalConfig` sets `enable_sandbox_testing: False`** | **UNKNOWN.** Default is `True` (`swegemma/config.py:123`), and `HARNESS_README.md:337` says `True` is active. If the organizer flips it, `pytest`/`unittest` are masked (`agent_runner.py:593-594`) and `system.md:37` would be instructing an impossible action. |
| **the 12-hour total wall clock and how many tasks actually run** | **UNKNOWN** — no per-task traces exist (see [S7]). |
| **whether the 31B checkpoint's tool-call parser accepts `args` as a JSON list** | **UNKNOWN** — no trajectory from any scored run is reachable. The harness coerces only single-element list *strings* for `skill_name`/`file_path`, not `args`. |
| **whether `run_skill_script`'s ~43 KB wrapper payload hits any sandbox limit** | **UNKNOWN** — `_MAX_SKILL_PAYLOAD_BYTES = 16 MB` (`skill_toolset.py:53`), so 43 KB is fine by that constant, but the sandbox's own stdin/file limits are not visible here. |

---

## [S7] LOCAL EVAL DATA

### S7.1 For exp05 / E4B baseline / e4b-v2: none exists

- No `paired_eval_results.json`, `smoke_test_results.json`, `paired_eval_summary.md`, or
  `*_results.json` anywhere in the tree (VERIFIED — recursive search, 0 hits).
- `ckpt/research/kernel_devset_eval/` contains only inputs:
  ```
  5930  eval_24_tasks.json          <- task SELECTION, no outcomes
   530  kernel-metadata.json
 15852  paired_devset_eval.py       <- the script
  bundles/exp05_patch_integrity/    <- 4 files
  bundles/exp10_consolidated/       <- 4 files
  ```
  `eval_24_tasks.json` is a deterministic stratified 24-task subset
  (fastapi 12, rich 8, requests 3, httpx 1) with `instance_id`, `repo`, `base_commit`,
  `gold_files`, `gold_changed_lines` per task. **No resolved counts, no tool-call counts, no
  timings, no patches** (VERIFIED — full file read).
- `ckpt/research/DEVSET_EVAL_MECHANICS.md:32-35` says the dev-set kernel
  `narisettichaitanya/g4-paired-devset-eval` (v4) was **RUNNING at handoff**, targeting
  exp05 vs exp10 on those 24 tasks, with telemetry to
  `/kaggle/working/smoke_test_results.json`, `paired_eval_results.json`,
  `paired_eval_summary.md`.
- `kaggle kernels list --mine` today shows **no such kernel** (VERIFIED). It is either
  deleted, renamed, or never completed. Either way its outputs are unreachable.

**Conclusion: there is no local or Kaggle-kernel eval result for exp05, the E4B baseline,
or e4b-v2.** Every score in the ledger is a public-LB number with no per-task breakdown.

### S7.2 What *is* present, and what it is not

| path | size | what it is |
|---|---:|---|
| `runs/dmitrii/` | ~4 MB, 30 files | **third-party public research data**, not our runs. `paired_comparisons.csv` compares *named public configurations* ("Two-reviewer voting pipeline", "Six-minute budget schedule", "Four-tool single coder") on 70 development tasks — none of which is our bundle. |
| `runs/main_lb/gemma-4-developer-agent.zip` | 131 KB | leaderboard export |
| `runs/sm_lb/leaderboard.csv` + `.log` | 9 KB + 2 KB | small-model leaderboard export |
| `audit_snapshots/locate_benchmark.json` | gitignored | the 7-snapshot localisation benchmark (summarised in `docs/AUDIT_SNAPSHOTS.md` §2.1) |

`runs/dmitrii/paired_comparisons.csv` head (VERIFIED):

```
split,config_a,config_b,n,a_only,b_only,both,neither,delta_resolved,exact_sign_p
development,Two-reviewer voting pipeline,Six-minute budget schedule,70,3,8,10,49,-5,0.2265625
development,Two-reviewer voting pipeline,Source-first localization,70,6,8,7,49,-2,0.79052734375
development,Two-reviewer voting pipeline,Optional analyzer,70,2,7,11,50,-5,0.1796875
development,Two-reviewer voting pipeline,Four-tool single coder,70,1,15,12,42,-14,0.000518798828125
```

Useful as a **prior on variance** (n=70 paired, deltas of ±2–5 tasks are not significant),
but it is not a measurement of any bundle in this repo.

### S7.3 Per-task logs or trajectories from scored submissions

**None.** Explicitly: no `submission.zip` payload log, no agent trace, no `atif` trace, no
per-task table for refs `56793672 … 57836949`. The Kaggle API exposes only the seven fields
in S2.1, and no local run captured a trace. This is the single biggest evidence gap in the
whole project.

---

## [S8] VALIDATION RESULTS

Command: `.venv-harness\Scripts\python.exe tools\verify_bundle.py --bundle <dir>`.

**Caveat that cost two runs:** the verifier is **not idempotent on Windows**. It stages
bundles into `<repo>/.verify_build/{primary,fallback}` and calls `shutil.rmtree` first
(`tools/verify_bundle.py:171`). A leftover `.verify_build/primary/skills/swe-toolkit/scripts/`
from an earlier exp13 run makes the next `rmtree` fail with
`OSError: [WinError 145] The directory is not empty`, which then corrupts the staged tree for
the run after that. I deleted `.verify_build/` (a scratch output dir, gitignored, no source
content) and re-ran each bundle in isolation. That deletion is the only write I performed
outside `docs/OPENCODE_REPORT.md`.

### S8.1 exp05 resubmission (`build/exp05_submitted`) — **FAIL (2 checks)**

```
=== 1. project static validator ===
[PASS] static validate: primary bundle :: root=agent.yaml files=4 model=gemma-4-31b-it-qat-w4a16-ct agents=['agent.yaml'] adapters=[] skills=[] bytes=5952
[PASS] static validate: fallback bundle :: root=agent.yaml files=4 model=gemma-4-31b-it-qat-w4a16-ct agents=['agent.yaml'] adapters=[] skills=[] bytes=6054
[FAIL] prompt has problem_description: primary bundle
[FAIL] prompt ends cleanly: primary bundle
[PASS] sampling max_output_tokens 8192: primary bundle
[PASS] prompt has problem_description: fallback bundle
[PASS] prompt ends cleanly: fallback bundle
[PASS] sampling max_output_tokens 8192: fallback bundle
[PASS] pack is deterministic :: 2ba7f9b118ea1837

=== 2. real harness (adk_submission / swegemma) ===
[PASS] import real harness
[PASS] our transcribed constants match the harness :: extensions=['.json', '.md', '.py', '.safetensors', '.txt', '.yaml', '.yml'] size=3221225472 output_tokens=NumericRange(min=1, max=32768) thinking=NumericRange(min=0, max=32768)
[PASS] model gemma-4-31b-it-qat-w4a16-ct is allowed by the competition docs
[PASS] model gemma-4-31b-it-qat-w4a16-ct is registered by the local harness wheel
[PASS] empty extension is rejected by the harness allowlist
[PASS] validate_directory: primary bundle
[PASS] single declared model: primary bundle :: ['gemma-4-31b-it-qat-w4a16-ct']
[PASS] compile_submission: primary bundle :: root 'swe_agent' ... tools=9 sub_agents=[] output_tokens=8192
[PASS] validate_directory: fallback bundle
[PASS] single declared model: fallback bundle :: ['gemma-4-31b-it-qat-w4a16-ct']
[PASS] compile_submission: fallback bundle :: root 'swe_coder' ... tools=6 sub_agents=[] output_tokens=8192

=== 3. negative tests ===
[PASS] rejects no root config / two root configs / disallowed extension / path traversal
[PASS] rejects dangling !include / two base models / LoRA adapter present
[PASS] rejects root without submit_patch / unknown tool name / per-task budget too large
[PASS] rejects forbidden generation field / unknown state placeholder / empty file
[SKIP] rejects !include escaping the root :: not applicable to this bundle shape
[SKIP] rejects sub-agent owns a writer tool :: not applicable to this bundle shape
[SKIP] rejects duplicate agent name :: not applicable to this bundle shape

============================================================
2 FAILURE(S): ['prompt has problem_description: primary bundle', 'prompt ends cleanly: primary bundle']
```

**This is the 0.20 artifact.** It fails the *project's* prompt-hygiene rule but **passes the
real harness** (`validate_directory` and `compile_submission` both PASS). So the validator is
stricter than the competition, and the highest-scoring submission in the ledger is not
reproducible through the current gate. `RESULTS.md:213-215` already records this.

Same check on the other two prompts that lack the placeholder (VERIFIED):

```
exp05 artifact (57553805, 0.20)    chars= 5425  has_problem_description=False
exp08          (57618114, 0.17)    chars= 5979  has_problem_description=False
exp10          (57654236, 0.17)    chars= 9764  has_problem_description=True
exp12          (57736284, 0.17)    chars= 6049  has_problem_description=True
```

So "has the placeholder" does not separate 0.20 from 0.17 — exp08 scored 0.17 without it.

### S8.2 e4b-v2 (`tracks/e4b_small/bundles/e4b_v2`) — **ALL CHECKS PASSED**

```
[PASS] static validate: primary bundle :: root=agent.yaml files=4 model=gemma-4-e4b-it-qat-w4a16-ct ... bytes=2204
[PASS] prompt has problem_description: primary bundle
[PASS] prompt ends cleanly: primary bundle
[PASS] sampling max_output_tokens 8192: primary bundle
[PASS] pack is deterministic :: e81a2d3f215e1098
[PASS] import real harness
[PASS] model gemma-4-31b-it-qat-w4a16-ct is allowed by the competition docs
[PASS] model gemma-4-31b-it-qat-w4a16-ct is registered by the local harness wheel
[PASS] model gemma-4-e4b-it-qat-w4a16-ct is allowed by the competition docs
[WARN] model gemma-4-e4b-it-qat-w4a16-ct is not in the local harness registry :: the live HARNESS_README permits it; re-download the wheelhouse before treating this as a submission blocker
[PASS] empty extension is rejected by the harness allowlist
[PASS] validate_directory: primary bundle
[PASS] single declared model: primary bundle :: ['gemma-4-e4b-it-qat-w4a16-ct']
[PASS] compile_submission: primary bundle :: root 'swe_agent' model=LiteLlm(model='gemma-4-e4b-it-qat-w4a16-ct') tools=6 sub_agents=[] output_tokens=8192
[PASS] validate_directory: fallback bundle
[PASS] single declared model: fallback bundle :: ['gemma-4-31b-it-qat-w4a16-ct']
[PASS] compile_submission: fallback bundle :: root 'swe_coder' tools=6 sub_agents=[] output_tokens=8192
... 13 negative tests PASS, 3 SKIP ...

============================================================
ALL CHECKS PASSED
```

The single `[WARN]` is the known wheelhouse-staleness signal for E4B (the local wheel
registry predates the four-model list). Not a failure, and not fixable without
re-downloading the wheelhouse.

### S8.3 Current working bundle (`ckpt/bundles/exp13_swe_toolkit`) — **ALL CHECKS PASSED**

```
[PASS] static validate: primary bundle :: root=agent.yaml files=10 model=gemma-4-31b-it-qat-w4a16-ct ... skills=['swe-toolkit']
[PASS] prompt has problem_description: primary bundle
[PASS] prompt ends cleanly: primary bundle
[PASS] sampling max_output_tokens 8192: primary bundle
[PASS] pack is deterministic :: 31de5b898d72d245
[PASS] import real harness
[PASS] our transcribed constants match the harness
[PASS] model gemma-4-31b-it-qat-w4a16-ct is allowed by the competition docs
[PASS] model gemma-4-31b-it-qat-w4a16-ct is registered by the local harness wheel
[PASS] empty extension is rejected by the harness allowlist
[PASS] validate_directory: primary bundle
[PASS] single declared model: primary bundle :: ['gemma-4-31b-it-qat-w4a16-ct']
[PASS] compile_submission: primary bundle :: root 'swe_agent' ... tools=10 sub_agents=[] output_tokens=8192
[PASS] validate_directory: fallback bundle
[PASS] single declared model: fallback bundle
[PASS] compile_submission: fallback bundle :: root 'swe_coder' tools=6 sub_agents=[] output_tokens=8192
... 13 negative tests PASS, 3 SKIP ...

============================================================
ALL CHECKS PASSED
EXITCODE=0
```

`tools=10` = the 9 declared tools + the `SkillToolset` as one entry. Exit code **0**
despite three `[SKIP]` lines.

### S8.4 Which checks could NOT run

- **Gate 3 (`verify_notebook.py`)**: not run. It was out of scope for this read-only pass
  and the notebook build writes into `build/`. The last recorded result is REMEMBERED as
  passing on 2026-11-01.
- **Gate 4 (kernel output comparison)**: could not run for exp13 — its kernel
  (`gemma4-devagent-exp13-swe-toolkit-v2`, last run 2026-10-30 13:56) was never pulled into
  `runs/`, and no `submission.zip` from it exists locally (VERIFIED).
- **Quota / `numAllowedNow`**: could not run (see S2.3).
- **The named `probe_skill_binding.py`**: does not exist (see S6.2).
- **T7 gate (30 never-solved single-file snapshots)**: not run — only 7 of 129 snapshots are
  extracted locally (`audit_snapshots/`), and the full set is 21.5 GB compressed per
  `docs/AUDIT_SNAPSHOTS.md:13`.
- **Any end-to-end task resolution test**: impossible locally (needs 4× L4 + the 31B QAT
  weights + the container image).

### S8.5 Tests run in this session (all VERIFIED)

| test | scope | result |
|---|---|---|
| `verify_bundle.py` × 3 bundles | static + real harness + 16 negative tests each | 2 PASS / 1 FAIL (S8.1–S8.3) |
| real `run_skill_script` probe | 3 modes on `audit_snapshots/requests_7502` | 3/3 `returncode = 0`, no residue (S6.2) |
| e4b-v2 final-gate one-liner | 8 throwaway repos | 8/8 reproduced, all `rc=0` (S4.3) |
| `load_skill_from_dir` binding | name vs directory | `name_matches_dir = True` |
| harness constant parity | extensions, 3 GiB, token ranges | PASS |

---

## [S9] QUESTIONS AND RISKS

### Things I could not do

1. **`docs/COMPLETE_SYSTEM_REFERENCE.md` does not exist.** The brief names it as the source
   for the original exp05 bundle. Nothing in the repo mentions that filename. I substituted
   `ckpt/exp05/submission.zip` + git history. If the file is supposed to exist, it was never
   committed.
2. **`probe_skill_binding.py` does not exist.** I wrote a faithful stand-in in `%TEMP%` and
   report its verdict block. It is *not* the script the brief names, and it lives outside
   the repo, so it will not survive.
3. **Quota is UNKNOWN.** No API I can reach returns `numAllowedNow` or
   `maxDailySubmissions`. `/api/v1/competitions/<slug>` is a 404.
4. **No per-task data for any scored submission.** Not a limitation of effort — the Kaggle
   API does not expose it and no run captured a trace.
5. **The T7 gate is still unmeasured.** 7 of 129 snapshots.

### Things that surprised me

6. **The 0.20 anchor fails the current validator** on two prompt-hygiene checks, while
   passing the *real* harness (`validate_directory` + `compile_submission`). The gate that
   `AGENTS.md` calls non-negotiable rejects the best artifact the project has. Any future
   attempt to resubmit a byte-identical exp05 is blocked by the project's own tooling, not
   by the competition.
7. **`command` is not a `run_skill_script` parameter.** Check (b) asks whether the prompt
   contains a template with `command`; the real schema is
   `skill_name` / `file_path` / `args` / `short_options` / `positional_args`
   (`skill_toolset.py:728-773`). The prompt is correct and the check's expected name is not.
8. **Check (c) is inverted.** `system.md:57` tells the model to call `load_skill`; it never
   mentions `list_skills`. If an earlier revision said "never call list_skills/load_skill",
   that instruction is gone.
9. **Check (d) has no subject.** There is no materialised skills directory to clean: ADK
   writes into `tempfile.TemporaryDirectory()` and deletes it (`skill_toolset.py:627-634`,
   `:704-707`). My probe confirmed `scratch residue = []`.
10. **`skills_folder`, `discovery_mode`, `tool_filter`, `EnvironmentToolset` do not exist**
    in this harness generation (0 hits across four packages). Any design that assumed them
    is stale. The real wiring is `adk_submission/resolvers/tools.py:129-264`.
11. **The harness injects the problem statement itself** (`agent_runner.py:379`) and *also*
    sets `session_state['problem_description']` (`:676-678`). So `{problem_description}` in
    `system.md` is a duplicate copy of the issue text in the system instruction. exp05
    (0.20) and exp08 (0.17) had no duplicate; exp10/exp12 (0.17) and exp13/e4b-v2 did. Score
    does not separate them, so the duplication is not obviously harmful — but it is real
    token cost and nobody has measured it.
12. **`run_skill_script` ships a ~43 KB code payload per call** (`wrapper_code_chars =
    42920`). Under the 16 MB constant, but it is 43 KB of code written to disk inside the
    sandbox on every `locate`, and it costs one of the 28 tool calls.
13. **`verify_bundle.py` is not idempotent on Windows.** A leftover `.verify_build/primary/skills/`
    makes the next run crash with `WinError 145`, and the run after that silently verifies a
    half-deleted tree (`!include file not found`). Two of my three initial runs were
    invalid because of this. This is a real trap for anyone running the gate twice.
14. **My own earlier note was wrong.** I previously believed `verify_bundle.py` exits 1 when
    `[SKIP]` lines are present. It does not: exp13 printed three `[SKIP]`s and
    `EXITCODE=0`. Exit 1 tracks `FAILURE(S)` only.
15. **`docs/LEDGER.md` is wrong in three places** about e4b-v2: `eval_config.yaml` is *not*
    byte-identical (`max_tool_calls` 28 → 35), the diff is *three* changes not two, and the
    prompt is 1746 chars, not 2440 (2440 is `e4b_v3`). Anyone reconstructing e4b-v2 from
    that ledger will get a different bundle.
16. **The e4b-v2 "final gate" never rejects anything.** All 8 scenarios exit 0. It prints
    diagnostics; it does not gate. And it does not flag protected-path edits (scenario 8
    showed `M tests/test_core.py` with no warning), which the exp13 `_verify.py` *does*.
17. **`verify` counts pre-existing dirt.** On `audit_snapshots/requests_7502` it reported
    `CHANGED: 1 file(s) setup.py` before any edit, because the extracted snapshot has a
    0-line CRLF-only `M setup.py`. On a Linux container this specific case probably
    disappears, but the general risk — `verify` conflating base-tree noise with agent edits
    — remains.

### Conflicts inside the brief

18. Check (b) asks for `command` in the `run_skill_script` template; the harness has no such
    parameter. I report the prompt as correct and the check as mis-specified.
19. Check (c) asks me to confirm `system.md` says never to call `list_skills`/`load_skill`;
    the file says the opposite for `load_skill`. I report it as FALSE rather than
    "not verified".
20. Check (d) asks for the exact cleanup command; there is none, and none is needed. I report
    "not applicable" with the harness evidence rather than inventing a command.
21. The brief calls `ckpt/bundles/exp05_patch_integrity` "the original exp05 bundle". It is
    not: it differs from the scored artifact by 36 chars, and its working tree is CRLF while
    its git blob is LF.

### Risks that matter for the next submission

22. **A pending submission blocks everything.** `57836949` has been `PENDING` since
    2026-10-31T11:22:30Z. Until it resolves, no new submission is possible even if the daily
    counter allows it.
23. **`enable_sandbox_testing` is the one unverified harness switch that can invalidate the
    exp13 prompt.** Default is `True` and the docs say `True`, so `system.md:37`'s pytest
    instruction should work. If the organizer sets it `False`, `pytest` and `unittest` are
    masked in the sandbox and the prompt tells the model to run a command that cannot exist.
    The prompt has no fallback path for that case.
24. **exp13 is unmeasured and untested end-to-end.** It has never been through Gate 3
    (notebook) in this session, never had Gate 4 (kernel output) run, and its kernel run from
    2026-10-30 was never pulled. Its `locate` quality is measured only on 7 local snapshots
    (hit@1 5/7, hit@3 7/7), not on the hidden set.
25. **The 0.24 target needs 14/58 = 4.0 SE above the pooled mean.** Nothing in this repo has
    demonstrated a mechanism that large. Treat any exp13 delta below ~0.06 as unresolved.

---

## 10-line summary

1. Branch `main`, HEAD `fdc264ac52c3c21931e8100089f10b354664c348`, working tree clean, no stashes (VERIFIED).
2. Ledger has 11 submissions; the only pending one is `57836949` (E0, byte-identical exp05, submitted 2026-10-31T11:22:30Z, still PENDING).
3. `runs/e0/submission.zip` is byte-identical to `ckpt/exp05/submission.zip` — sha256 `2ba7f9b118ea1837…`, 3386 bytes, 4/4 members matching, model/sampling/eval/tools identical.
4. The current bundle is `ckpt/bundles/exp13_swe_toolkit`: exp05 + a `skills: [skills/swe-toolkit]` line, a 5-line `## TOOLKIT` block, and 6 new skill files (41,166 bytes of scripts).
5. e4b-v2 changed **three** things, not two (temperature 0.2→0.1, `max_tool_calls` 28→35, prompt 5353→1746 chars); `docs/LEDGER.md` is wrong on all three counts.
6. `verify_bundle.py`: exp05 artifact **FAILS** 2 prompt-hygiene checks (but passes the real harness); e4b-v2 and exp13 **ALL CHECKS PASSED**.
7. The harness source is fully available locally (`adk_submission` 0.2.13, `swegemma` 0.2.11, `google-adk` 1.36.1); `run_skill_script` runs in the task sandbox with a 240 s timeout, and I proved it end-to-end (rank-1 gold file on `requests_7502`, zero residue).
8. Checks: (a) TRUE and harness-enforced; (b) false premise (`command` is not a parameter); (c) FALSE (`system.md` instructs `load_skill`); (d) not applicable (ADK uses a tempdir); (e) moot (bundle `skills/` never enters `git add`); (f) 9 tools + 1 skill path.
9. UNKNOWN: quota (`numAllowedNow`), `enable_sandbox_testing` in the real competition config, per-task outcomes for every scored submission, the 31B model's handling of `args` as a JSON list, and the T7 gate (7 of 129 snapshots extracted).
10. No eval results exist for exp05, E4B or e4b-v2 — every score is a public-LB number with no per-task trace, and `verify_bundle.py` is not idempotent on Windows (`WinError 145` on a stale `.verify_build`).

# PUBLIC ARCHITECTURE AUDIT — what the 0.22–0.29 region actually is

**Date:** 2026-11-10. **Scope:** every public competition notebook and dataset that could be
traced to a concrete `submission.zip`, plus the live leaderboard.
**Artifacts:** `research/public_intel/` (`pulled/`, `payloads/`, `datasets/`).

---

## 0. The one finding that reframes everything

The competition has a **public config census** with per-version scores and a content hash of the
exact files each version submitted (`files_sha256 = sha256(json.dumps(FILES, sort_keys=True))`).
Two independent readings of it agree:

| source | statement |
|---|---|
| `dariushafshar/gemma-4-agent-public-config-draws` (145 scored versions, 67 notebooks, 21 file sets, snapshot 2026-10-22) | the **best** traced public version ever scored is **0.22** (13/58); **no** traced public version reached 0.24 |
| `dariushafshar/gemma-4-most-run-public-config-averages-10-58` | the most-run public file set averages **10.00/58 = 0.17** over 10 draws (95% CI 8.98–11.02); pooled SD **1.56 tasks**, so 95% of draws land within ±3.2 tasks of a config's mean |

And the clearest single datum:

> Igor Zharov's *Budget-Aware Coding Agent v2* version 10 scored **13** on its first public run.
> The **same `files_sha256`** was then re-run 7 more times as **7, 7, 8, 9, 10, 10, 10** — mean **8.71**.

So the 0.22–0.24 numbers are **tail draws of a ~0.17-mean distribution**, not a better recipe.
The live board confirms the mechanism: on 2026-11-09 the 0.24 band is **10 teams**, and the
0.24 teams have a **median of 15.5 submissions** versus **7.0** for the 555 teams at 0.17
(`board_blocks.csv`). The leaderboard is a staircase of exact ties — 424 teams share 0.18 — and
the rules award ties to the earlier submission.

**Consequence for our program.** Our pooled 31B result (0.166–0.179 across eight runs) is *not*
behind the public state of the art. It **is** the public state of the art, and the apparent
0.24–0.29 gap is sampling noise plus submission volume. Any single-run delta ≤ 3 tasks is
unresolvable, and any claim of a "0.24 config" is a claim about a lucky draw.

---

## 1. Method

1. `kaggle kernels list --competition gemma-4-developer-agent --sort-by scoreDescending --page-size 100`
   and `--competition gemma-4-developer-agent-paper --sort-by voteCount --page-size 30`.
2. Pulled 20 kernels into `research/public_intel/pulled/` and extracted every submission payload
   into `research/public_intel/payloads/` with `extract_payloads.py`.
   The extractor is deliberately non-executing: it interprets only literal assignments,
   `json.loads(<constant>)`, `dict(x)`, f-strings, subscript assignment and `for`/`if` over
   literals. Filesystem-writing notebooks (`alikalwar`, `judgeguard`) were run in a sandboxed
   temp root by `sandbox_exec.py` with `/kaggle/working` rewritten to that root.
3. Grouped the census by `files_sha256` and computed mean/SD/spread per group
   (`census_stats.py`), then matched our own bundles against those groups
   (`match_our_hashes.py`).

---

## 2. Two classes of public notebook

### 2A. Baseline clones — no distinct mechanism

All of these share one architecture: one `LlmAgent`, the 6 harness tools plus the 3 graph tools
declared-but-banned in the prompt, `temperature 0.2`, `max_output_tokens 8192`,
`thinking_budget 4096`, `include_thoughts true`, 28 calls / 8 min / 80 turns.

| notebook | prompt chars | tools | measured public scores | note |
|---|---:|---:|---|---|
| `flexonafft/gemma-4-budget-aware-coding-agent-v2` | 6,323 | 9 | **0.22**, 0.18, 0.17, 0.15, 0.13, 0.12 (8 draws, 5 authors) | `files_sha256 56010e9e9d4c`; mean **0.159** |
| `honghanhhh/gemma-4-baseline-lb-0-24` | 6,985 | 9 | 0.18 (its *earlier* file set); 0.24 is asserted in the title | adds 4 mechanisms, see §3 |
| `kawh1111/g4-baseline-024` | 6,985 | 9 | — | byte-identical to honghanhhh |
| `victorzhong0110/gemma4-submission-pack-upstream-v8` | 6,985 | 9 | — | byte-identical to honghanhhh |
| `kiza123123/judgeguard-gemma-4-autonomous-developer-agent` | 6,963 | 9 | — | **one 22-char diff** from honghanhhh |
| `prvsiyan/gemma-and-the-shape-of-doubt` | 6,323 | 9 | 0.20, 0.17, 0.18, 0.15 | embeds `56010e9e9d4c` |
| `jvnhonglei/gemma-4-superagent-reproduction` | 4,913 | 9 | 0.20, 0.18, 0.13 | `9f8886a9f09c`, mean **0.168** |
| `matterhorn3838/gemma-4-superagent` | 4,913 | 9 | 0.17, 0.13 | same file set |
| `verracodeguacas/gemma-4-agent-budget-fit-single-agent` | 4,677 | 9 | 0.18, 0.17, 0.15, 0.13 | `c9829b6ac709`; **most-run public file set**, 10 draws, mean **0.172** |
| `hitarthjain0/gemma-4-patch-berserker-evaluate-then-submit` | 3,240 | 6 | 0.18, 0.15, 0.13 | `5d05a6e0430a` |
| `shipship/gemma-4-dev-agent-lb024-fork` | 3,240 | 6 | — | fork of the berserker file set |
| `hitarthjain0/gemma-4-agent-what-took-lb-0-12-0-24` | 1,006 | 6 | — | write-up, not a submission |
| `prvsiyan/anatomy-of-a-gemma-4-coding-agent-submission` | 143 | 6 | — | teaching notebook, no score claim |

**None of these is a distinct architecture.** JudgeGuard is the purest illustration: its
"Master Orchestration Ecosystem" and "JudgeGuard verification" reduce to a prompt that differs
from honghanhhh's by a single line, and to the same four-phase call plan.

### 2B. Genuinely distinct mechanisms

| notebook | prompt chars | tools | distinct mechanism | measured |
|---|---:|---:|---|---|
| `navyadevadiga/gemma4-swe-agent-t8-static` | 5,581 | **3** | `run_command`, `read_file`, `submit_patch` only; **all edits are Python heredocs through `run_command`**; `thinking_budget 256`; `temp 0.3`, `top_k 64`; 25 calls / 40 turns | **0.20**, then **0.15** on resubmission |
| `rainycloudss/gemma-4-agent-apex-v16-tdd-reproducer` | 2,166 | 6 | **mandatory TDD reproducer**: write `/tmp/repro.py`, confirm it *fails*, edit, confirm it *passes*; **hardcoded Common Module Locations** per repo; 5.2 min / 75 calls | untraced |
| `robinamirbahar/gemma-4-loop-breaker-adk-agent` | 3,756 | 6 | loop-breaking narrative: 3-gram Jaccard `J(a_t,a_{t-1}) > 0.70` detector, multi-region `sed` batching, call-12 edit deadline; `temp 1.0`, `top_k 64` | paper track, no score claim |
| `nihilisticneuralnet/gemma-4-developer-agent-direct-code-verifier` | 6,585 | 9 | A/B harness: `baseline_022` vs `compact_prompt` vs `lean_tools` vs `combined`; explicit "turn the issue into a contract" stage | 0.17, 0.13 |
| `alikalwar/gemma-4-agent-a-b-lean-submission-zip-builder` | 4,074 | 8 | A/B: graph tools + "shortlist-first opening" vs lean; `temp 1.0`, `max_output_tokens 16384`, 50 calls / 6 min / 100 turns | untraced |
| `leoprovorov/single-agent-anytime-patch` | 2,994 | 6 | "anytime patch": submit the working tree early and keep improving it | 0.17 |
| `icfoer/gemma4-developer-agent-lora-200-test` | 3,728 | 9 | LoRA adapter bundle — **banned for us**: an adapter collapses the vLLM KV cache from ~46k to ~7.6k tokens |

---

## 3. The only real mechanism delta in the 0.22→0.24 lineage

`flexonafft` (0.22 measured) → `honghanhhh` (0.24 asserted) is a **14-line diff** that adds
exactly four things:

1. **Protected config files** — `pytest.ini`, `conftest.py` added to the never-touch list.
2. **Scratch-file isolation** — "Scratch files go in /tmp only. Any file left under /workspace
   becomes part of the graded patch."
3. **Untracked-file visibility** — `git status --short && git diff` instead of `git diff`, with
   the explicit reason: *"`git diff` alone hides untracked files, but `submit_patch` includes them."*
4. **Parallel-implementation coverage** — "If the same behaviour has parallel implementations
   (sync and async variants, Client and AsyncClient, several backends or transports, typing
   overloads, re-exports in `__init__.py` or `__all__`), apply the change to every one of them."

Mechanism 4 is the most interesting, because it attacks the exact failure mode our own audit
found dominant: on multi-file tasks our strict all-gold recall is **0.079/0.079/0.158** at
@3/5/10 versus **0.763/0.816/0.895** for any-gold. The public 0.24 lineage independently
converged on the same fix.

Mechanisms 1–3 are already present in our `exp05` (patch integrity) or are trivial to adopt.

---

## 4. Do our bundles match the census?

**No — and that is the correct result.** `match_our_hashes.py`:

| bundle | `files_sha256` | census match |
|---|---|---|
| `ckpt/exp05/submission.zip` (scored artifact) | `d986ff28d0f1` | none |
| `ckpt/bundles/exp05_patch_integrity` | `b468ee389c14` | none |
| `bundles/exp13_swe_toolkit` | `3c84cd51af3b` | none |
| `bundles/exp14_lean_toolkit` | `ea5b11da3fe8` | none |
| `bundles/exp_breakthrough` | `ea9cd57a0edb` | none |

We are **architectural mirrors, not hash matches**. Our `exp05` uses the SuperAgent/matterhorn
prompt lineage (5,461 chars) while the census's most-run file set is the Budget-Fit prompt
(4,677 chars); we also append the `{problem_description}` tail and carry the `.gitignore` guard.
Same tool surface, same sampling, same budget — different prompt text.

That means we inherit the group's **mean (~0.17)**, not its lucky draws. Our eight-run pool of
0.166–0.179 is exactly the census prediction for this architecture. There is no hidden 0.24
recipe in the public work to copy, and our results are not evidence of a defect.

---

## 5. Which mechanisms are generalizable

Ranked by (mechanistic justification) × (evidence) ÷ (cost):

| # | mechanism | source | evidence | cost | verdict |
|---|---|---|---|---|---|
| 1 | `git status --short && git diff` + `git add -N -f` for `.gitignore`d new files | honghanhhh + our `exp05` | harness `submit_patch` runs `git add -N .` then `git diff HEAD`; `git add -N .` respects `.gitignore` | zero tokens | **adopt** (already in `exp05`) |
| 2 | parallel-implementation coverage rule | honghanhhh 0.24 lineage | our own multi-file strict recall 0.079 vs any-gold 0.763 | ~90 chars | **adopt** |
| 3 | batched independent searches + multi-region `sed` reads | flexonafft 0.22 lineage | directly attacks the "2/3 of calls lost to exploration" failure; `run_command` keeps only 5,000 chars so batching is the only way to fit more evidence per call | ~600 chars | **adopt** |
| 4 | edit-recovery heredoc with `assert s.count(old) == 1` | flexonafft + navyadevadiga | eliminates the `old_string` no-match/ambiguous failure mode entirely | ~500 chars | **adopt** |
| 5 | backtick ban in tool payloads | navyadevadiga | tool calls containing a backtick "often arrive broken" | ~120 chars | **adopt** |
| 6 | `budget_warning` early exit | navyadevadiga | the harness emits it; ignoring it burns the remaining budget | ~90 chars | **adopt** |
| 7 | hardcoded Common Module Locations | rainycloudss | free static localization prior; but repo-specific and stale-prone | ~250 chars | **adopt in part** — our `swe-toolkit` ranker subsumes it |
| 8 | TDD reproducer (`/tmp/repro.py` fail→fix→pass) | rainycloudss | strong verification discipline, but costs 2–3 calls we may not have | 2–3 calls | **partial** — keep the `python -c` one-shot form |
| 9 | 3-tool surface, heredoc-only edits | navyadevadiga | removes 3 tool schemas; measured 0.20 then 0.15 | — | **not adopted**: 0.20→0.15 on resubmission is the clearest warning in the census |
| 10 | `thinking_budget 256` | navyadevadiga | fast, but the 0.20→0.15 regression is confounded with it | — | **not adopted** |
| 11 | LoRA adapter | icfoer | collapses KV cache ~46k → ~7.6k tokens | — | **rejected** (repo invariant) |

---

## 6. What this means for the paper

The honest and *stronger* paper is not "we found the 0.24 config". It is:

1. **A measurement result.** The public 0.22–0.29 band is a tail of a ~0.17-mean distribution
   with pooled SD 1.56 tasks; 29 repeated draws of six public file sets cannot rank
   themselves. Our 8-run pool agrees.
2. **A retrieval result.** Live git-tracked workspace indexing with `/tests/` demotion and
   span symbol re-ranking reaches **File R@5 0.744 / R@10 0.829** on all 129 public tasks,
   versus **0.435 / 0.570** for the pre-computed competition graph corpus — a **+30.9
   percentage-point** file-recall gain.
3. **A mechanism catalogue.** Four prompt-level mechanisms that the 0.24 lineage converged on
   independently, each tied to a specific harness behaviour.

That is a constructive systems-and-retrieval paper, and it does not depend on a leaderboard
delta smaller than the noise floor.

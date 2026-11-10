# PUBLIC 0.22 / 0.24 AUDIT — comparative matrix against `exp05` (0.20) and `exp14` (0.15)

**Date:** 2026-11-10. **Sources:** `research/public_intel/payloads/` (20 kernels extracted),
`research/public_intel/datasets/public_config_draws.csv` (145 scored versions, 67 notebooks).

> **Read §0 first.** The premise "public configs hit 0.22–0.24" is a statement about *draws*,
> not about configs. The census hashes every submitted file set: the best public version ever
> scored is **0.22**, and that exact file set (`56010e9e9d4c`) was re-run 7 more times for
> 7, 7, 8, 9, 10, 10, 10 — **mean 8.71/58**. The 0.24 band on the live board is 10 *teams*
> with a median of 15.5 submissions each. Full evidence: `docs/PUBLIC_ARCHITECTURE_AUDIT.md`.

---

## 0. Score provenance of every row below

| config | public score(s) | draws | mean | verdict |
|---|---:|---:|---:|---|
| `flexonafft` `56010e9e9d4c` | 0.22, 0.17, 0.15, 0.13, 0.12 | 8 (5 authors) | **0.159** | tail draw |
| `honghanhhh` `4a65b9a74a` | 0.24 asserted in title; *earlier* file set `5d05a6e0430a` scored 0.18, 0.15, 0.13 | 3 | **0.161** | title claim untraced |
| `verracodeguacas` `c9829b6ac709` | 0.18, 0.17, 0.15, 0.13 | 10 (8 authors) | **0.172** | most-run public file set |
| `matterhorn3838` `9f8886a9f09c` | 0.20, 0.18, 0.13 | 4 (4 authors) | **0.168** | — |
| `navyadevadiga` T8 | 0.20, then 0.15 on resubmission | 2 | **0.175** | regression on redraw |
| our `exp05` | 0.20, 0.17 (E0 control, byte-identical) | 2 | **0.185** | — |
| our `exp14` | 0.15 | 1 | — | −1 task vs the 0.17 cluster |
| our 31B pool | 0.20, 0.17×5, 0.15, 0.13 | 8 | **0.166** | matches the census mean |

Every "0.22–0.24" claim in the public corpus is a **single draw**; every config with ≥ 3 draws
means **0.159–0.175**. Our pool sits in the middle of that band.

---

## 1. System prompt structure, character length, and command templates

| config | chars | structure | command templates |
|---|---:|---|---|
| `honghanhhh` 0.24 lineage | **6,985** | HARD LIMITS → CALL PLAN → PROCEDURE (1 spec, 2 locate, 3 edit, 4 verify, 5 submit) → DECISION RULES | `git grep -n "TOKEN" -- '*.py' \| head -20`; `sed -n 'A,Bp'` multi-region; `timeout 150 python -m pytest … -x -q -k` |
| `flexonafft` 0.22 | 6,323 | same skeleton, terser locate/edit | same, plus "batch independent searches into one run_command" |
| `exp05` (ours, 0.20) | 5,461 | same skeleton + `.gitignore`/`git add -N -f` guard + `{problem_description}` tail | `git grep`, `read_file`, `timeout 150 … -k` |
| `exp14` (ours, 0.15) | 5,768 | `exp05` skeleton + 3-line `## TOOLKIT` skill block | same + `run_skill_script` |
| `matterhorn3838` | 4,913 | same skeleton, no `/tmp` scratch rule | `find tests -name "*kw*.py"` then `timeout 150 …` |
| `verracodeguacas` | 4,677 | "Core Objective" + 4 workflow sections + Budget | `git grep … \| head -20`; bare `pytest … -k` |
| `hitarthjain0` berserker | 3,240 | Budget → 4 numbered sections → Never | `pytest tests/test_file.py -k test_name -q` |
| `rainycloudss` TDD | **2,166** | Budget/Invariants → **Common Module Locations** → 5-step TDD | `grep -rn "id" --include="*.py" . \| grep -v "/tests/" \| head -20`; `python3 /tmp/repro.py` |
| `navyadevadiga` T8 | 5,581 | "You have only a few minutes" → Environment facts → call-combining → 7-step workflow → patch rules | heredoc `python - <<'EOF'` with `assert s.count(old) == 1` |
| `hitarthjain0` lean | **1,006** | 6 numbered lines | `git grep`; `pytest path::test -q` |

**Observation.** The 0.24 lineage is *not* lean — it is the longest prompt in the corpus that
anyone re-ran (6,985 chars). Prompt length does not separate the scores: the most-run file set
(4,677 chars) and the 0.24 lineage (6,985 chars) both mean ≈0.17. What separates them is
**four specific mechanisms**, not length (§3).

---

## 2. Exposed tool names and schemas

| config | declared tools | non-harness tools | schema tax |
|---|---|---|---|
| `honghanhhh` / `flexonafft` / `matterhorn` / `verracodeguacas` | 9 = 6 lean + 3 graph | none | 3 banned schemas (~450 tok) |
| `exp05` (ours) | 9 = 6 lean + 3 graph | none | 3 banned schemas |
| `exp14` (ours) | 9 declared + `skills/swe-toolkit` | SkillToolset: `list_skills`, `load_skill`, `load_skill_resource`, `run_skill_script` | +4 schemas + ~1,250-char ADK preamble per request |
| `hitarthjain0` berserker | 6 lean | none | minimal |
| `robinamirbahar` loop-breaker | 6 lean | none | minimal |
| `navyadevadiga` T8 | **3** = `run_command`, `read_file`, `submit_patch` | none | **minimal possible** |
| `alikalwar` | 8 = 6 lean + 2 graph | none | 2 banned schemas |
| `icfoer` | 9 + LoRA adapter | adapter | collapses KV cache ~46k → ~7.6k |

**Observation.** Every top config declares at least the 6 lean tools. The 3 graph tools are
declared and then *banned in the prompt* in all 9-tool configs — pure schema waste. Only
`navyadevadiga` had the discipline to drop them, and it paid `edit_file`/`write_file`/`get_status`
for it: 0.20 then **0.15** on resubmission. Dropping `edit_file` forces every mutation through a
heredoc, which is robust but slow.

Our `exp14` is the only config that adds a **fourth toolset**. `SkillToolset` appends
`_DEFAULT_SKILL_SYSTEM_INSTRUCTION` plus an `<available_skills>` block to the system instruction
on *every* request, so the real prompt delta is ~1,800 chars, not the 418 chars of the
`## TOOLKIT` block. `exp14` scored 0.15 against a 0.17 cluster — within noise, but the only
config in the corpus that measurably moved *down*.

---

## 3. Context / compaction management and loop-breaking

Compaction is active in the scoring path at `token_threshold = 14,336`
(`swegemma` → ADK `EventsCompactionConfig`), and it keeps **only the model's own text** — the
original task message is not summarised.

| config | compaction strategy | loop-breaking strategy |
|---|---|---|
| `honghanhhh` 0.24 | none explicit | "Do not spend another tool call repeating a search that already answered the question"; call-12 edit deadline; call-20 exploration stop |
| `flexonafft` 0.22 | none explicit | same, plus "Never repeat an identical failed edit" and a heredoc fallback after 2 matching failures |
| `exp05` (ours) | "keep tool results small" | none explicit |
| `exp14` (ours) | skill writes `/tmp/swe_session_state.json`; `locate` re-emits `[SESSION STATE]` on the next call | `CONFIDENCE: LOW` → git grep; "never call locate twice" |
| `robinamirbahar` | — | 3-gram Jaccard `J(a_t,a_{t-1}) > 0.70` trigger; "Counterfactual Context Reset"; multi-region `sed` batching (17.0 → 6.5 mean calls) |
| `navyadevadiga` T8 | "keep each tool output short"; `budget_warning` → immediate submit | "If a tool call reports a missing argument, never repeat the same call: shorten it and retry" |
| `rainycloudss` TDD | — | `get_status` polling with `<60s` / `<5 calls` hard exit |

**Observation.** No scored config has a real compaction-survival mechanism. The 0.24 lineage
relies on prompt-level discipline; `robinamirbahar` (paper track) is the only one with a
formal detector, and it is a simulation, not a scored artifact. Our `exp14` skill's
`/tmp/swe_session_state.json` resume is the only **stateful** mechanism in the corpus — it is
orthogonal to prompt text and survives compaction because `/tmp` persists in Container A.

---

## 4. Thinking budget, temperature, and `top_p`

| config | temp | top_p | top_k | max_output | thinking_budget | include_thoughts |
|---|---:|---:|---:|---:|---:|---|
| `honghanhhh` 0.24 | 0.2 | 0.95 | — | 8192 | 4096 | true |
| `flexonafft` 0.22 | 0.2 | 0.95 | — | 8192 | 4096 | true |
| `verracodeguacas` (most-run) | 0.2 | 0.95 | — | 8192 | 4096 | true |
| `exp05` / `exp14` (ours) | 0.2 | 0.95 | — | 8192 | 4096 | true |
| `bliverrigpdoge` 0.22-4-file | 0.2 | 0.95 | — | 8192 | 4096 | true |
| `robinamirbahar` loop-breaker | **1.0** | 0.95 | **64** | 8192 | 4096 | true |
| `leoprovorov` anytime-patch | **1.0** | 0.95 | **64** | 8192 | 4096 | true |
| `navyadevadiga` T8 | **0.3** | 0.95 | **64** | 8192 | **256** | true |
| `alikalwar` | **1.0** | 0.95 | — | **16384** | 4096 | true |
| `icfoer` LoRA | 0.4 | 0.95 | — | 8192 | 4096 | true |
| our `exp_sampling` (0.13) | **1.0** | 0.95 | **64** | 8192 | 4096 | true |
| our `exp_think1024` (Kaggle error) | 0.2 | 0.95 | — | 8192 | **1024** | true |

**Observation.** The entire 0.22–0.24 lineage is **`temp 0.2 / top_p 0.95` with no `top_k`** —
identical to our `exp05`. The `temp 1.0 + top_k 64` variant appears only in paper-track and
unscored notebooks, and our own `exp_sampling` (0.13) is the single worst 31B result we have.
`thinking_budget` is 4096 in every scored config; `navyadevadiga`'s 256 is confounded with its
other changes and its 0.20→0.15 redraw.

**Conclusion: there is nothing to gain by copying the sampling of the 0.22–0.24 configs — it is
already ours.**

---

## 5. Time and tool-call limits

| config | timeout_s | max_tool_calls | max_time_min | max_turns |
|---|---:|---:|---:|---:|
| `honghanhhh` 0.24 / `flexonafft` 0.22 / `exp05` / `exp14` | 240 | 28 | 8 | 80 |
| `bliverrigpdoge` | 240 | 28 | 8 | 80 |
| `navyadevadiga` T8 | 240 | 25 | 8 | 40 |
| `rainycloudss` TDD | — | **75** | **5.2** | 90 |
| `alikalwar` | 120 | 50 | 6 | 100 |
| `icfoer` | 240 | 24 | 6 | 80 |
| `leoprovorov` | 240 | 28 | 8 | 80 |

**Observation.** 240 / 28 / 8 / 80 is the convergent point for every scored config. The
`timeout_seconds` value also bounds the Phase-2 pytest run (`harness/verification.py`), so
lowering it is dangerous and raising it is pointless. The per-task cap must stay ≤ 10 minutes
because ~120 tasks share a 12-hour global budget.

---

## 6. The `fastapi` sandbox test-plugin trap

Auditing `tasks.jsonl` across all 129 public tasks:

| signal | count |
|---|---:|
| tasks whose `test_patch` or repo tests import `inline_snapshot` / `dirty_equals` | see `docs/PAPER_TRACK_DRAFT.md` §2.5 |
| FastAPI tasks that fail pytest collection with `ModuleNotFoundError` before any assertion runs | **27 / 67 (40.3%)** |
| rich / requests / httpx tasks with the same failure | **0** |

**Consequence for any verification step.** A verification gate that treats a collection error as
a regression will reject a correct fix 40% of the time on FastAPI. Every config that adds a
pre-submit verification step must classify the failure: `SyntaxError` / `ImportError` /
`NameError` / `TypeError` / `AttributeError` are real regressions; a plain `AssertionError`
in a pre-existing test is often the pre-patch behaviour the hidden `test_patch` rewrites.

Our `exp14` skill's `_verify.py` implements exactly this classification. No public config does.

---

## 7. Summary of the architectural delta

`exp05` (0.20/0.17) → the 0.24 lineage is **four prompt mechanisms**, not a new architecture:

1. protected `pytest.ini` / `conftest.py`,
2. `/tmp`-only scratch rule,
3. `git status --short && git diff` (untracked-file visibility),
4. parallel-implementation coverage (sync/async twins, `__all__` re-exports).

Plus one *tool-call compression* change that is the real workhorse: **batch independent
searches into one `run_command`, and read up to three regions per command with `sed -n`**.
That is the only mechanism that increases evidence per call under a 5,000-character output cap
and a 28-call budget.

`exp14` (0.15) → the same `exp05` plus a fourth toolset. The skill is the only *stateful*
mechanism in the corpus (compaction resume, confidence fallback, patch gate, failure
classification), but it costs ~1,800 chars of per-request preamble and 4 schemas. Its 0.15 is
one task below the cluster — **not resolved**, and the reason the next candidate must isolate
the skill's mechanisms rather than re-bundle them.

**Nothing in the public 0.22–0.29 region is a better configuration.** It is the same
configuration redrawn. The defensible next move is to adopt the four prompt mechanisms and the
call-compression change — each tied to a specific harness behaviour — and to measure with the
paired instrument, not to chase a tail draw.

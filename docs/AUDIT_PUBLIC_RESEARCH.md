# Audit — public research, the 0.24 question, and where the next task actually is

Written 2026-10-31, while E0 (`57836949`) is pending. Everything below is measured from
files in this repo or from named public artifacts; nothing is inferred from a leaderboard
delta smaller than the noise band.

**Question this answers.** Given ~0.05 LB noise, should we expect 0.17? Is a real 0.24+
reachable? What is the next experiment?

---

## 1. The anchor is 0.179. Expect 0.17.

Five scored runs of the 31B budget-fit family: **12, 10, 10, 10, 10** tasks out of 58.

| statistic | value |
|---|---|
| mean | 10.4 / 58 = **0.179** |
| SD across runs | 0.89 tasks |
| max observed | 12 (the 0.20 draw, ref `57553805`) |
| to reach 0.24 | **14 tasks**, i.e. +3.6 = **4.0 SD above the mean**, 2 above the best draw |

0.20 is one high draw in five. The modal expectation is **0.17**, and the 95% band on a
single run is roughly 0.14–0.22.

**Identical bytes do not repeat.** Dmitrii Gluzdov's 2026-10-19 note records the same
archives scoring 0.13 and 0.20 (alternative-prompt), and 0.22 / 0.12 / 0.15 (budget-aware)
across different runs. Our own family spans 0.17–0.20. So the observable spread on *the
same artifact* is 0.12–0.22 = 7 tasks. Any single score, including a 0.24, is one draw.

---

## 2. The public board says 0.24 is a tail, not a recipe

Public board 2026-10-31T12:01:40Z, 4,261 teams:

| score | tasks/58 | teams | share | median submissions |
|---:|---:|---:|---:|---:|
| 0.29 | 17 | 1 | 0.0% | 18 |
| 0.24 | 14 | 6 | 0.1% | 13 |
| 0.22 | 13 | 58 | 1.4% | 16 |
| 0.20 | 12 | 249 | 5.8% | 13 |
| 0.18 | 10 | 626 | 14.7% | 10 |
| 0.17 | 10 | 753 | 17.7% | 7 |
| 0.15 | 9 | 620 | 14.6% | 4 |

Overall median submissions = 4, mean 6.8, max 36. **The 0.22 tier has 58 teams averaging
16.5 submissions each and never reached 14.** If 0.24 were produced by a known recipe, that
tier is where it would show up. It does not. The distribution is a smooth tail, not a second
mode.

---

## 3. The union of every public configuration is ~0.23

From `runs/dmitrii/all_config_eval.csv` (692 runs, 8 configurations, 114 sound tasks):

| quantity | value |
|---|---|
| tasks solved by ≥1 of 8 configs | 50 / 114 = **43.9%** |
| tasks solved by no config | 64 / 114 = 56.1% |
| our config (budget-fit family) | 39 / 114 = 34.1% |
| our config on the LB | 0.179 |

The ratio LB/local is 0.525. Applied to the union: **0.439 × 0.525 ≈ 0.23**. So a single
agent that inherited every win from all eight public configurations would land at about
0.23 — and no single agent can inherit them (they are different prompts, budgets and
architectures). This is the strongest form of the argument that 0.24 is not a config.

**Caveat, and it is a real one.** The four-tool config had the best local rate (34.2%) and
its recorded LB scores are 0.06 and 0.10. Dmitrii's own note on those rows says "archive
differs from the later packaged archive", and the 0.06 row is marked "earlier scorer". So
those two rows are **not** clean measurements of the config that was evaluated locally.
Treat "local rate does not predict the LB" as **unresolved**, not settled.

---

## 4. The 64 never-solved tasks are not a capability wall

Gold-patch structure of the 114 tasks (`tasks.jsonl`), grouped by how many of the 8 configs
solve them:

| bucket | n | ≥2 files | median lines | >100 lines | median issue |
|---|---:|---:|---:|---:|---:|
| never solved | 64 | 42% | 27 | 20% | 278 chars |
| rare (1–2 configs) | 25 | 16% | 7 | 0% | 518 chars |
| common (≥3 configs) | 25 | 8% | 5 | 0% | 815 chars |

The never-solved bucket looks like a wall until it is cut by size:

| subset of the 64 never-solved | n |
|---|---:|
| **1 file, ≤10 lines** | **17** |
| **1 file, ≤30 lines** | **30** |
| 1 file, ≤30 lines, issue ≤300 chars | 21 |
| ≤2 files, ≤30 lines | 34 |
| 1 file, ≤60 lines | 35 |

**30 of the 64 never-solved tasks are single-file patches of 30 lines or fewer, and 21 of
those come with a short issue.** These are not tasks the model cannot write. They are tasks
the model never found. The same pattern appears in the rare bucket: 20 of 25 are one file,
≤30 lines.

This reframes the whole problem. The loss is not patch construction; it is
**localization from a short issue**. A 67-character issue with a 4-line fix
(`requests_7502`) is unsolved by all eight configurations.

---

## 5. The one lever, and why it is not ready

If the LB is a ~50% sample of the same population, +3.6 LB tasks = **+6.9 local tasks**.
Reaching 0.24 therefore requires converting **about 7 of the 30 single-file never-solved
tasks**. That is the target, and it is a localization target.

The built lever is `skills/swe-toolkit/` (`_index.locate`), already packaged as
`ckpt/bundles/exp13_swe_toolkit`. Measured on the 7 audited snapshots:

| task | issue | gold files | rank | top-5 |
|---|---:|---:|---:|---|
| fastapi_14371 | 397 | 4 | 1 | ok |
| fastapi_15280 | 64 | 2 | 2 | ok |
| httpx_3672 | 243 | 7 | 1 | ok |
| requests_7315 | 694 | 1 | 1 | ok |
| requests_7502 | 67 | 1 | **2** | ok |
| rich_3061 | 411 | 1 | 1 | ok |
| rich_3470 | 74 | 1 | **10** | **top 5 are all `tests/`** |

hit@1 4/7, hit@3 6/7. The single miss is the shortest issue, and the failure mode is
diagnostic: **test files crowd out source files**. That is already item 1 of the T2 delta
(demote `tests/` to ×0).

**But the tool is not shippable as it stands.** Measured today:

1. **Latency.** `swe.py locate` on `audit_snapshots/fastapi_14371` (1,279 `.py` files) takes
   **13.5–25.7 s** as a subprocess. The in-process benchmark recorded 3.1 s, so the gap is
   cold page cache plus process startup. The 25 s watchdog **fires**: one run returned
   `STATUS: DEGRADED` with no files at all. 67 of 129 tasks are fastapi. A degraded return
   is a wasted tool call out of 28.
2. **The invocation in exp13 is wrong.** The prompt tells the model to run
   `python3 $(find / -name swe.py 2>/dev/null | head -1)`, which walks the whole
   filesystem, violates the harness rule "do NOT search outside `/workspace`", and is
   exactly the `rglob` pattern T2 item 8 deletes from `bootstrap.py`.
3. **The skill name is wrong.** The prompt says `skill_name="swe_toolkit"`; the registry
   derives the name from the directory, so it is `swe-toolkit`.
4. **`SKILL.md` advertises the wrong operations.** It says "Operations: inspect, verify" and
   omits `locate` — the only operation that matters here. `load_skill` would therefore
   teach the model not to use it.
5. **exp13 is two changes, not one.** Its prompt appends `## The issue` +
   `{problem_description}`, which the 0.20 artifact does not have. The harness already sends
   the problem statement as the user message (`agent_runner.py:677` seeds session state and
   `build_agent_prompt` embeds `Problem Statement:` in the turn), so the append is a
   duplicate, not a fix.

`verify_bundle.py --bundle ckpt/bundles/exp13_swe_toolkit` prints **ALL CHECKS PASSED**, so
none of the above is caught by the gate. It is a quality problem, not a schema problem.

---

## 6. What to do next

**Do not submit exp13.** It would spend a submission-day on a tool that can return nothing
on the majority repository, invoked by a filesystem-wide `find`.

The next action costs no submission and is falsifiable:

1. **Fix T2 items 1, 2 and 7** (test demotion, `locate` output contract, watchdog that
   prints a partial report). Target: `locate` returns in < 5 s on fastapi and never returns
   `DEGRADED` with an empty body.
2. **Expand the snapshot set** from 7 to the 30 single-file never-solved tasks.
3. **Measure hit@3 on those 30.** Gate:
   - **≥ 60% (18/30)** → the lever is real. Build E1 (skill + one prompt paragraph, no
     `{problem_description}` append), gate it on T5, submit.
   - **< 60%** → the lever is dead. Hold the anchor, spend the remaining days on draws of
     the best-known bundle, and do not spend a slot on a localization variant.

**Why the gate is set at 60%.** Converting 7 of 30 needs the right file in the top 3 for
roughly 7/30 = 23% of the bucket *and* the model to then make the edit. If the ranker cannot
place the file in the top 3 for 60% of them, the remaining conversion rate is not plausible.

**Submission plan for the remaining 32 days.**

| when | action |
|---|---|
| now | T2 fixes + 30-task locate benchmark (no submission) |
| E0 resolves | record; if ≤0.13 re-audit the environment before anything else |
| gate passes | E1 on the LB, one change, paired against 0.179 |
| gate fails | no more bundle experiments; hold |
| last 2 days before 2026-11-25 | two draws of the best-mean bundle, selected as final |

Two draws of the anchor is the fallback, not a defeat: at mean 10.4 and SD 0.9, the better
of two draws is ~10.9 tasks ≈ 0.19, and the downside is bounded by the artifact we already
know.

---

## 7. Corrections to earlier notes

| earlier claim | status |
|---|---|
| "local dev-set rate does not predict LB" | **unresolved**, not settled — the two four-tool LB rows are archive-mismatched and one is an earlier scorer |
| "0.24 is arithmetically out of reach" | **wrong** — it needs ~7 of 30 single-file never-solved tasks, which is a localization problem |
| "`{problem_description}` must be in the prompt" | **false for the harness** — the 0.20 artifact has no placeholder and works; the validator rule is local policy |
| "the 0.20 anchor is the frozen bundle" | already corrected in Audit E: the artifact is `ckpt/exp05/submission.zip` |

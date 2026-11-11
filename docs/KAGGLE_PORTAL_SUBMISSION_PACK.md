# Kaggle Paper Track Portal Submission Pack

**Competition**: [Gemma 4 Developer Agent](https://www.kaggle.com/competitions/gemma-4-developer-agent)
**Track**: Paper Track
**Submission deadline**: November 12, 2026 23:59 UTC
**Canonical writeup**: [`docs/MASTER_WRITEUP_FINAL.md`](MASTER_WRITEUP_FINAL.md) — paste verbatim into the writeup editor.

---

## 1. Quick form metadata

| Form field | Exact value | Limit |
|---|---|---|
| **Track** | Paper Track | required |
| **Title** | Finding a File Is Not Finding the Patch: Retrieval, Hazards & Noise in Gemma 4 | 78 / 80 chars |
| **Subtitle** | A 129-task multi-file retrieval study, source- and replay-verified runtime hazards, and N=58 leaderboard uncertainty bounds on Gemma 4. | 135 / 140 chars |
| **Thumbnail** | `assets/paper_figures/fig0_card_thumbnail.png` | 1200x630 |

---

## 2. Media gallery, in upload order

All figures are rendered at 300 dpi from `research/verified_json/*.json` by
`scripts/generate_paper_figures.py`. Insert each one at the marked point in the
writeup body; captions below are the ones to paste under each image.

1. **Figure 1** — insert after Table 1, before §3.
   `assets/paper_figures/fig1_harness_architecture.png`
   *Caption*: Six audited sites across the offline harness — Gemma 4, vLLM serving, the ADK agent loop, the tool surface, and the swegemma grader. Labels separate source-verified quotes, inherited vLLM quotes, and counts of exposure.

2. **Figure 2** — insert after Table 3, before §4.
   `assets/paper_figures/fig2_retrieval_ladder.png`
   *Caption*: File retrieval on the 129-task development set. (A) Any-Gold and Mean-Fraction at k=5 with bootstrap intervals. (B) The one-mechanism ladder, paired by task. (C) B3 recall by candidate budget under the three metric definitions; the gap is definitional at every k.

3. **Figure 3** — insert after Table 5, before §5.
   `assets/paper_figures/fig3_baselines_and_twohop.png`
   *Caption*: (A) Baseline ladder by repository. (B) The budget-matched two-hop expansion on the 38 multi-file tasks: it converts entry-point hits into multi-file hits without adding net coverage.

4. **Figure 4** — insert after Table 6, before §6.
   `assets/paper_figures/fig4_leaderboard_power.png`
   *Caption*: (A) Every logged submission, with the integer count that determines the score. (B) The three estimand rows: level, dispersion across near-baseline bundles, and the sampling error of one 58-task split.

5. **Figure 5** — insert after the §6 body, before the Figures list.
   `assets/paper_figures/fig5_patch_anatomy_exposure.png`
   *Caption*: (A) Gold files touched by each patch across all 129 tasks. (B) Measured exposure for the two counting sites: withheld new files, and bare agent-side pytest under the three defensible denominators.

---

## 3. Attachments and public notebooks

Both are public, return HTTP 200 unauthenticated, and assert every printed value
against the embedded payload (`DONE:` at the end, no `[FAIL]`).

- **Graph benchmark** — https://www.kaggle.com/code/narisettichaitanya/g4-paper-graph-benchmark
  Reproduces the retrieval ladder (Tables 2–3, Figures 2–3): paired per-task deltas,
  per-repository splits, the three metric definitions, and the multi-file gold-set strata.
  Verified run: version 28, status COMPLETE.
- **Noise and MDE** — https://www.kaggle.com/code/narisettichaitanya/g4-paper-noise-mde
  Reproduces the submission ledger, the three estimand rows (Table 6, Figure 4), and the
  runtime hazard exposure counts (Table 4, Figure 5).
  Verified run: version 5, status COMPLETE.

---

## 4. Writeup body

Paste `docs/MASTER_WRITEUP_FINAL.md` in full. It is the only canonical text; this pack
deliberately does not duplicate it, so there is no second copy to drift.

Current state of that file:

- 2,657 whitespace words (target 2,650; hard gate 2,750).
- 124 claims bound to `research/verified_json/*.json` by JSON Pointer.
- 364 visible numeric tokens, all bound or declared structural.
- No placeholder, no withdrawn artifact, no legacy calibrated string.

Re-verify before pasting:

```powershell
.venv-harness\Scripts\python.exe scripts\reproduce_all.py
```

Expected tail:

```
[PASS] every number in the paper resolves to research/verified_json/*.json
[PASS] no forbidden legacy string; 2657 <= 2750 words
```

The same run rewrites `docs/number_audit.csv`, which lists every claim, its JSON
Pointer, and the rendered value.

---

## 5. Pre-submission checklist

- [x] Title and subtitle within the portal character limits.
- [x] Five figures plus the listing card rendered from the verified JSON.
- [x] Both notebooks rebuilt from the same JSON, pushed, COMPLETE, HTTP 200.
- [x] Gate passes: every number bound, no placeholders, word budget respected.
- [x] Legacy calibrated audits quarantined; no active script reads them.
- [ ] **Explicit user approval to submit** — required; do not submit without it.
- [ ] Paste body, attach figures in the order above, attach both notebook links.
- [ ] Submit on the Kaggle writeup page, then record the submission in `RESULTS.md`.

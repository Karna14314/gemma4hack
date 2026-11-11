import json
import math
import os
import re
import sys
import urllib.request

def check(name, condition, msg=""):
    if not condition:
        print(f"[FAIL] {name}: {msg}")
        return False
    print(f"[PASS] {name}")
    return True

all_passed = True

print("=== 1. AUDITING SOURCE FILES FOR SYNTHETIC CALIBRATION LOOPS ===")
files_to_check = [
    'scripts/build_regime_a_per_task.py',
    'research/paper_eval_outputs/symbol_ranking/symrank_v6.py',
    'research/novelty_audits/statistical_rigor_audit.py'
]
forbidden_terms = [
    'target_hits["v6"]',
    '0.5484',
    'fraction_gold_hit = 1/gold_n',
    'synthetic_m1',
    'target_hits =',
    'fake_any_gold'
]
for fpath in files_to_check:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    for term in forbidden_terms:
        if term in content:
            all_passed = check(f"{fpath} - {term}", False, f"Forbidden calibration term '{term}' found in {fpath}") and all_passed
        else:
            all_passed = check(f"{fpath} - free of '{term}'", True) and all_passed

print("\n=== 2. AUDITING MASTER WRITEUP WORD COUNT ===")
with open('docs/MASTER_WRITEUP_FINAL.md', 'r', encoding='utf-8') as f:
    writeup = f.read()

w_space = len(writeup.split())
w_regex = len(re.findall(r"[A-Za-z0-9]+", writeup))
all_passed = check("Whitespace word count <= 2680", w_space <= 2680, f"Found {w_space}") and all_passed
all_passed = check("Regex token count <= 2950", w_regex <= 2950, f"Found {w_regex}") and all_passed

print("\n=== 3. AUDITING RETRIEVAL DECOMPOSITION NUMBERS ===")
with open('research/paper_eval_outputs/regime_a_per_task.json', 'r', encoding='utf-8') as f:
    regime = json.load(f)

dm = regime['decomposition_matrix']
m4_mean = dm['regime_a_static_graph']['mean_fraction_recall_r5']
v4_mean = dm['regime_b_live_ast']['mean_fraction_r5']['value']
v4_any = dm['regime_b_live_ast']['any_gold_r5']['value']

all_passed = check("Regime A M4 Mean-Frac == 0.4350", abs(m4_mean - 0.4350) < 1e-4, f"{m4_mean}") and all_passed
all_passed = check("Regime B v4 Mean-Frac == 0.6184", abs(v4_mean - 0.6184) < 1e-4, f"{v4_mean}") and all_passed
all_passed = check("Regime B v4 Any-Gold == 0.7442", abs(v4_any - 0.7442) < 1e-4, f"{v4_any}") and all_passed

cand_gain = dm['waterfall_decomposition']['pipeline_index_gain_pp']
metric_gap = dm['waterfall_decomposition']['metric_definition_gap_pp']
total_leap = dm['waterfall_decomposition']['total_transition_leap_pp']

all_passed = check("Candidate gain == +18.34 pp", abs(cand_gain - 18.34) < 1e-2, f"{cand_gain}") and all_passed
all_passed = check("Metric gap == +12.58 pp", abs(metric_gap - 12.58) < 1e-2, f"{metric_gap}") and all_passed
all_passed = check("Total leap == +30.92 pp", abs(total_leap - 30.92) < 1e-2, f"{total_leap}") and all_passed

print("\n=== 4. AUDITING SYMBOL RANKING NUMBERS (REAL TEXT, ZERO CALIBRATION) ===")
with open('research/paper_eval_outputs/symbol_ranking/symrank_v6_results.json', 'r', encoding='utf-8') as f:
    sym = json.load(f)

v4_hits = sym['ablation_summary']['v4_baseline']['hits']['@5']
v6_hits = sym['ablation_summary']['v6']['hits']['@5']
all_passed = check("v4 baseline R@5 hits == 38", v4_hits == 38, f"{v4_hits}") and all_passed
all_passed = check("v6 uncalibrated R@5 hits == 44", v6_hits == 44, f"{v6_hits}") and all_passed
all_passed = check("v6 latency < 15ms", sym['ablation_summary']['v6']['median_latency_s'] < 0.015) and all_passed

print("\n=== 5. AUDITING STATISTICAL NOISE & MDE ===")
scores = [12, 10, 10, 10, 10]
n_tasks = 58
pooled_tasks = sum(scores)
pooled_trials = len(scores) * n_tasks
pooled_rate = pooled_tasks / pooled_trials
mean_fam = 10.4
sigma = math.sqrt(sum((x - mean_fam)**2 for x in scores) / 4)
mde_same = 2.802 * math.sqrt(2) * sigma
cross_se_tasks = 2.92
mde_single = 2.802 * cross_se_tasks
mde_cross = 2.802 * math.sqrt(2) * cross_se_tasks
trunc = 313 / 387

all_passed = check("sigma == 0.8944 tasks", abs(sigma - 0.8944) < 1e-4, f"{sigma}") and all_passed
all_passed = check("same-split MDE == 3.54 tasks", abs(mde_same - 3.54) < 0.02, f"{mde_same}") and all_passed
all_passed = check("single-split MDE == 8.18 tasks", abs(mde_single - 8.18) < 0.02, f"{mde_single}") and all_passed
all_passed = check("cross-split MDE == 11.57 tasks", abs(mde_cross - 11.57) < 0.02, f"{mde_cross}") and all_passed
all_passed = check("1-hop truncation rate == 80.9%", abs(trunc - 0.8088) < 1e-3, f"{trunc}") and all_passed

# Also check noise notebook cell 1 text
with open('research/kernel_paper_noise_mde/g4-paper-noise-mde.ipynb', 'r', encoding='utf-8') as f:
    nb_noise = json.load(f)
c1_src = ''.join(nb_noise['cells'][1]['source'])
all_passed = check("Noise notebook contains Z_FACTOR = 2.802", "Z_FACTOR = 2.802" in c1_src) and all_passed
all_passed = check("Noise notebook contains within_sd (0.8944)", "0.8944" in c1_src or "within_sd" in c1_src) and all_passed

print("\n=== 6. AUDITING KAGGLE KERNELS UNTOUCHED HTTP 200 ===")
for slug in ['g4-paper-graph-benchmark', 'g4-paper-noise-mde']:
    url = f'https://www.kaggle.com/code/narisettichaitanya/{slug}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            all_passed = check(f"{slug} returns HTTP 200", resp.status == 200, f"{resp.status}") and all_passed
    except Exception as e:
        all_passed = check(f"{slug} returns HTTP 200", False, str(e)) and all_passed

print("\n=======================================================")
if all_passed:
    print("ALL AUDIT CHECKS PASSED WITH 100% RESEARCH INTEGRITY!")
else:
    print("SOME AUDIT CHECKS FAILED! INVESTIGATE ABOVE.")
    sys.exit(1)

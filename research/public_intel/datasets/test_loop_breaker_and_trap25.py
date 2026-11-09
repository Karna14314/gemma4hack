"""
Standalone Pytest & Unittest Verification Suite for:
  - `loop_breaker.py` (Type-I Error Stagnation, Type-II Patch Oscillation, Type-III Entropy Collapse)
  - `<NEGATIVE_CONSTRAINT_LEDGER>` Counterfactual Context Reset (`prune_messages`)
  - Phase-Adaptive `<|think|>` Budget & Temperature Controller (`_select_sampling_policy`)
  - All 25 `Trap-25` 3-state Python bug-repair tasks (`buggy_code`, `trap_patch`, `gold_patch`)
  - All 129 `swegemma` repository code graphs (`swegemma_repo_code_graphs_129.csv`)
  - Cumulative 6-module ablation (`swegemma_6module_ablation.csv`)
  - 100-trajectory / 937-turn telemetry & 4-arm `run_full_ablation_suite` (`evaluate_benchmark.py`)

Run directly via:
  pytest -v test_loop_breaker_and_trap25.py
or:
  python test_loop_breaker_and_trap25.py
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

try:
    from loop_breaker import (
        AgentPhase,
        LoopBreakerEngine,
        TurnRecord,
        compute_action_entropy,
        compute_diff_similarity,
        extract_error_signature,
    )
    from evaluate_benchmark import (
        execute_patch_in_sandbox,
        extract_python_code_from_response,
        run_full_ablation_suite,
    )
except ImportError:
    from gemma4_loop_breaker import (
        AgentPhase,
        LoopBreakerEngine,
        TurnRecord,
        compute_action_entropy,
        compute_diff_similarity,
        execute_patch_in_sandbox,
        extract_error_signature,
        extract_python_code_from_response,
        run_full_ablation_suite,
    )


def _find_data_file(filename: str) -> Path:
    for candidate in (
        HERE / filename,
        HERE / "benchmarks" / filename,
        HERE.parent / "benchmarks" / filename,
        HERE.parent / filename,
    ):
        if candidate.exists():
            return candidate
    matches = list(Path("/kaggle/input").rglob(filename)) if Path("/kaggle/input").exists() else []
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Could not locate {filename}")


class TestGemma4LoopBreakerAndTrap25(unittest.TestCase):
    def test_01_error_signature_extraction_normalizes_memory_addresses(self) -> None:
        tb1 = "E   AssertionError: Object at 0x7f9a1c2b3d40 failed invariant check"
        tb2 = "E   AssertionError: Object at 0x112233445566 failed invariant check"
        sig1 = extract_error_signature(tb1)
        sig2 = extract_error_signature(tb2)
        self.assertIsNotNone(sig1)
        self.assertEqual(sig1, sig2)
        self.assertIn("0xADDR", sig1 or "")

    def test_02_diff_similarity_and_action_entropy_primitives(self) -> None:
        patch_a = "def fix(x):\n    return x + 1\n"
        patch_b = "def fix(x):\n    return x + 1  # retry\n"
        patch_c = "def completely_different(a, b, c):\n    return {k: v for k, v in zip(a, b)}\n"
        self.assertGreaterEqual(compute_diff_similarity(patch_a, patch_b), 0.82)
        self.assertLess(compute_diff_similarity(patch_a, patch_c), 0.50)

        low_entropy_seq = [
            TurnRecord(i, "edit_file", "a.py", "p", "err", True, "AssertionError: fail", 100)
            for i in range(1, 5)
        ]
        high_entropy_seq = [
            TurnRecord(1, "search_similar_code", "a.py", "p1", "ok", False, None, 100),
            TurnRecord(2, "read_file", "b.py", "p2", "ok", False, None, 100),
            TurnRecord(3, "edit_file", "c.py", "p3", "ok", False, None, 100),
            TurnRecord(4, "pytest", "test_c.py", "p4", "ok", False, None, 100),
        ]
        self.assertEqual(compute_action_entropy(low_entropy_seq, window=4), 0.0)
        self.assertGreaterEqual(compute_action_entropy(high_entropy_seq, window=4), 1.5)

    def test_03_type_i_error_stagnation_triggers_ccr_and_negative_constraint_ledger(self) -> None:
        engine = LoopBreakerEngine(max_consecutive_same_error=2)
        d1 = engine.record_turn(
            tool_name="edit_file",
            target_file="httpx/_models.py",
            action_payload="def normalize(h): return h.lower()",
            tool_output="E   AssertionError: Multi-header list lost on duplicate key",
            is_error_or_test_failure=True,
        )
        self.assertFalse(d1.loop_detected)
        self.assertEqual(d1.recommended_policy.phase, AgentPhase.SYNTHESIZE_PATCH)

        d2 = engine.record_turn(
            tool_name="edit_file",
            target_file="httpx/_models.py",
            action_payload="def normalize(h): return h.strip().lower()",
            tool_output="E   AssertionError: Multi-header list lost on duplicate key",
            is_error_or_test_failure=True,
        )
        self.assertTrue(d2.loop_detected)
        self.assertEqual(d2.loop_type, "REPEATED_TEST_FAILURE_SIGNATURE")
        self.assertEqual(d2.recommended_policy.phase, AgentPhase.LOOP_RECOVERY)
        self.assertEqual(d2.recommended_policy.thinking_budget, 6144)
        self.assertEqual(d2.recommended_policy.temperature, 0.75)
        self.assertEqual(len(engine.constraints), 1)
        ledger = engine.render_negative_constraint_ledger()
        self.assertIn("<NEGATIVE_CONSTRAINT_LEDGER>", ledger)
        self.assertIn("NC-01", ledger)

    def test_04_type_ii_patch_oscillation_triggers_ccr(self) -> None:
        engine = LoopBreakerEngine(max_consecutive_same_error=3, diff_similarity_threshold=0.82)
        engine.record_turn(
            tool_name="edit_file",
            target_file="fastapi/routing.py",
            action_payload="def resolve_route(path: str):\n    return path.rstrip('/') or '/'\n",
            tool_output="E   AssertionError: Mount prefix stripped incorrectly",
            is_error_or_test_failure=True,
        )
        d2 = engine.record_turn(
            tool_name="edit_file",
            target_file="fastapi/routing.py",
            action_payload="def resolve_route(path: str):\n    return path.rstrip('/') or '/' # v2\n",
            tool_output="E   ValueError: Empty sub-mount path raised ValueError",
            is_error_or_test_failure=True,
        )
        self.assertTrue(d2.loop_detected)
        self.assertEqual(d2.loop_type, "OSCILLATING_CODE_EDIT")
        self.assertGreaterEqual(d2.max_diff_similarity, 0.82)

    def test_05_type_iii_entropy_collapse_triggers_ccr(self) -> None:
        engine = LoopBreakerEngine(entropy_window=4, min_entropy_threshold=0.55)
        for idx in range(3):
            d = engine.record_turn(
                tool_name="read_file",
                target_file="requests/sessions.py",
                action_payload=f"read_file requests/sessions.py lines {idx*10}..{idx*10+10}",
                tool_output="def merge_setting(request_setting, session_setting): ...",
                is_error_or_test_failure=False,
            )
            self.assertFalse(d.loop_detected)
        d4 = engine.record_turn(
            tool_name="read_file",
            target_file="requests/sessions.py",
            action_payload="read_file requests/sessions.py lines 30..40",
            tool_output="def merge_hooks(request_hooks, session_hooks): ...",
            is_error_or_test_failure=False,
        )
        self.assertTrue(d4.loop_detected)
        self.assertEqual(d4.loop_type, "LOW_ACTION_ENTROPY_STAGNATION")
        self.assertLess(d4.action_entropy, 0.55)

    def test_06_prune_messages_reduces_context_and_pins_negative_constraint_ledger(self) -> None:
        engine = LoopBreakerEngine(max_consecutive_same_error=2)
        engine.record_turn(
            tool_name="edit_file",
            target_file="rich/cells.py",
            action_payload="def cell_len(t): return len(t)",
            tool_output="E   AssertionError: ZWJ emoji sequence width mismatch",
            is_error_or_test_failure=True,
        )
        engine.record_turn(
            tool_name="edit_file",
            target_file="rich/cells.py",
            action_payload="def cell_len(t): return len(t.strip())",
            tool_output="E   AssertionError: ZWJ emoji sequence width mismatch",
            is_error_or_test_failure=True,
        )
        messages = [
            {"role": "system", "content": "You are a Gemma 4 coding agent."},
            {"role": "user", "content": "Fix cell_len ZWJ handling in rich/cells.py."},
            {"role": "assistant", "content": "Turn 1 attempt A " * 120},
            {"role": "user", "content": "Turn 1 traceback A " * 120},
            {"role": "assistant", "content": "Turn 2 attempt B " * 120},
            {"role": "user", "content": "Turn 2 traceback B " * 120},
            {"role": "assistant", "content": "Turn 3 latest state"},
            {"role": "user", "content": "Turn 3 latest pytest output"},
        ]
        pruned = engine.prune_messages(messages, keep_head=2, keep_tail=2)
        self.assertEqual(len(pruned), 5)
        self.assertTrue(any("<NEGATIVE_CONSTRAINT_LEDGER>" in m["content"] for m in pruned))
        self.assertLess(sum(len(m["content"]) for m in pruned), sum(len(m["content"]) for m in messages))

    def test_07_all_25_trap_tasks_three_state_sandbox_verification(self) -> None:
        trap_path = _find_data_file("trap_tasks_25.jsonl")
        tasks = [json.loads(line) for line in trap_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(tasks), 25)
        domains = set()
        for t in tasks:
            domains.add(t["repo_domain"])
            ok_buggy, _ = execute_patch_in_sandbox(t["buggy_code"], t["test_code"])
            ok_trap, _ = execute_patch_in_sandbox(t["trap_patch"], t["test_code"])
            ok_gold, out_gold = execute_patch_in_sandbox(t["gold_patch"], t["test_code"])
            self.assertFalse(ok_buggy, f"{t['task_id']} buggy_code must fail test_code")
            self.assertFalse(ok_trap, f"{t['task_id']} trap_patch must fail test_code")
            self.assertTrue(ok_gold, f"{t['task_id']} gold_patch must pass test_code: {out_gold}")
        self.assertEqual(domains, {"httpx", "requests", "fastapi", "rich", "sci_compute"})

    def test_08_129_swegemma_repo_code_graphs_and_6module_ablation(self) -> None:
        graphs_path = _find_data_file("swegemma_repo_code_graphs_129.csv")
        mod6_path = _find_data_file("swegemma_6module_ablation.csv")
        with graphs_path.open("r", encoding="utf-8") as f:
            graph_rows = list(csv.DictReader(f))
        self.assertEqual(len(graph_rows), 129)
        with mod6_path.open("r", encoding="utf-8") as f:
            mod6_rows = list(csv.DictReader(f))
        self.assertEqual(len(mod6_rows), 7)
        self.assertEqual(float(mod6_rows[0]["public_lb_score"]), 0.121)
        self.assertEqual(float(mod6_rows[-1]["public_lb_score"]), 0.241)

    def test_09_end_to_end_4arm_ablation_harness(self) -> None:
        trap_path = _find_data_file("trap_tasks_25.jsonl")
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            summary = run_full_ablation_suite(
                benchmark_path=trap_path,
                results_dir=out_dir,
                backend="gemma-4-qat-ast-verified",
            )
            self.assertEqual(summary["baseline_static"]["resolution_rate_pct"], 16.0)
            self.assertEqual(summary["naive_subagent"]["resolution_rate_pct"], 20.0)
            self.assertEqual(summary["ccr_only"]["resolution_rate_pct"], 72.0)
            self.assertEqual(summary["ccr_adaptive_ours"]["resolution_rate_pct"], 96.0)

    def test_10_perozzi_talk_like_a_graph_encoding_ablation(self) -> None:
        p = _find_data_file("perozzi_talk_like_a_graph_encoding_ablation.csv")
        with p.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 90)
        schemes = {r["graph_encoding_scheme"] for r in rows}
        self.assertIn("G_CCR_1Hop_EgoNet_Plus_Contract_Ledger", schemes)
        self.assertIn("TalkLikeAGraph_Incidence_List", schemes)
        self.assertIn("Unindexed_Schema_Tool_Adv", schemes)

    def test_11_galkin_ultra_relational_contract_transfer_129(self) -> None:
        p = _find_data_file("galkin_ultra_relational_contract_transfer_129.csv")
        with p.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 129)
        avg_s1 = sum(float(r["stage1_contract_parser_recall_at_3"]) for r in rows) / len(rows)
        avg_unidx = sum(float(r["unindexed_graph_tool_recall_at_3"]) for r in rows) / len(rows)
        self.assertGreater(avg_s1, avg_unidx)

    def test_12_markowitz_tree_of_traversals_two_container_audit_129(self) -> None:
        p = _find_data_file("markowitz_tree_of_traversals_two_container_audit_129.csv")
        with p.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 129)
        self.assertTrue(all(int(r["call_12_deadline_compliant"]) == 1 for r in rows))
        pass_count = sum(1 for r in rows if r["container_b_junit_verdict"] == "PASS")
        self.assertEqual(pass_count, 31)


if __name__ == "__main__":
    unittest.main(verbosity=2)

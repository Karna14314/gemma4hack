"""
Gemma 4 Loop-Breaker: Graph-Guided Counterfactual Context Reset (G-CCR) &
Phase-Adaptive Thinking Engine.

Addresses multi-turn trajectory degeneration ("The 15-Minute Cliff") in quantized
open-weights coding agents (e.g., gemma-4-31b-it-qat-w4a16-ct, gemma-4-12b-it-qat-w4a16-ct)
operating over repository-level code graphs (search_similar_code, get_code_neighbors,
get_code_subgraph).
"""

from __future__ import annotations

import dataclasses
import difflib
import hashlib
import math
import re
from collections import Counter
from enum import Enum
from typing import Any


class AgentPhase(str, Enum):
    """Execution phase of the coding agent trajectory."""

    LOCALIZE = "LOCALIZE"               # Initial fault localization & code-graph search
    INSPECT = "INSPECT"                 # Routine file reading / 1-hop graph neighbor inspection
    SYNTHESIZE_PATCH = "SYNTHESIZE"     # Drafting & applying code edits
    VERIFY_TEST = "VERIFY_TEST"         # Running targeted pytest / test verification
    LOOP_RECOVERY = "LOOP_RECOVERY"     # Triggered immediately after a G-CCR loop reset


@dataclasses.dataclass
class SamplingPolicy:
    """Dynamic generation parameters for Gemma 4 native thinking & tool calling."""

    phase: AgentPhase
    thinking_budget: int
    temperature: float
    top_p: float
    reason: str


@dataclasses.dataclass
class TurnRecord:
    """Telemetry record for a single agent-environment interaction turn."""

    turn_idx: int
    tool_name: str
    target_file: str | None
    action_payload: str
    tool_output: str
    is_error_or_test_failure: bool
    error_signature: str | None = None
    tokens_consumed: int = 0


@dataclasses.dataclass
class NegativeConstraint:
    """Structured memory entry replacing pruned dead-end trajectory turns."""

    constraint_id: str
    turns_collapsed: list[int]
    target_file: str
    attempted_change_summary: str
    failure_signature: str
    directive: str


@dataclasses.dataclass
class LoopDiagnostic:
    """Telemetry diagnostic emitted at each turn for paper evaluation & logging."""

    turn_idx: int
    loop_detected: bool
    loop_type: str | None
    action_entropy: float
    max_diff_similarity: float
    consecutive_same_error: int
    tokens_saved_by_reset: int
    recommended_policy: SamplingPolicy


def extract_error_signature(output: str) -> str | None:
    """Extract a canonical traceback/assertion signature from pytest or shell output."""
    if not output:
        return None
    patterns = [
        r"(E\s+(?:AssertionError|TypeError|ValueError|KeyError|AttributeError|IndexError|ImportError|ZeroDivisionError|RuntimeError)[^\n]*)",
        r"((?:AssertionError|TypeError|ValueError|KeyError|AttributeError|IndexError|ImportError|ZeroDivisionError|RuntimeError):[^\n]*)",
        r"(FAILED\s+[^\s]+\s+-\s+[^\n]*)",
        r"(SyntaxError:[^\n]*)",
    ]
    matches: list[str] = []
    for pat in patterns:
        found = re.findall(pat, output)
        if found:
            matches.extend(m.strip() for m in found[:2])
    if matches:
        normalized = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", " | ".join(matches))
        return normalized[:240]
    if "FAILED" in output or "Traceback (most recent call last)" in output or "Error" in output:
        lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
        tail = lines[-1] if lines else "UNKNOWN_ERROR"
        return tail[:200]
    return None


def compute_diff_similarity(payload_a: str, payload_b: str) -> float:
    """Compute normalized sequence similarity [0.0, 1.0] between two code edits/actions."""
    if not payload_a and not payload_b:
        return 1.0
    if not payload_a or not payload_b:
        return 0.0
    norm_a = re.sub(r"\s+", " ", payload_a.strip())
    norm_b = re.sub(r"\s+", " ", payload_b.strip())
    return difflib.SequenceMatcher(None, norm_a, norm_b).ratio()


def compute_action_entropy(turns: list[TurnRecord], window: int = 4) -> float:
    """
    Compute Shannon entropy (in bits) over recent (tool_name, target_file, error_signature)
    tuples. Low entropy (< 0.55 bits) over a window >= 4 indicates trajectory stagnation.
    """
    recent = turns[-window:] if len(turns) >= window else turns
    if len(recent) <= 1:
        return 2.0
    keys = [
        f"{t.tool_name}:{t.target_file or ''}:{t.error_signature or 'OK'}"
        for t in recent
    ]
    counts = Counter(keys)
    total = len(keys)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    return round(entropy, 4)


class LoopBreakerEngine:
    """
    Core engine implementing:
    1. Multi-Turn Degeneration Detection (Diff Similarity + Error Signature + Action Entropy)
    2. Graph-Guided Counterfactual Context Reset (G-CCR) with Negative Constraint Ledger
       synthesis and 1-hop/2-hop repository code-graph expansion directives
       (get_code_neighbors, get_code_subgraph, search_similar_code)
    3. Phase-Adaptive Thinking Budget Scheduling
    """

    GRAPH_SEARCH_TOOLS = {"search_similar_code", "get_code_neighbors", "get_code_subgraph"}
    INSPECT_TOOLS = {"read_file", "grep", "find_by_name", "list_dir"} | GRAPH_SEARCH_TOOLS
    EDIT_TOOLS = {"edit_file", "write_file", "apply_patch", "str_replace_editor", "bash_edit"}

    def __init__(
        self,
        diff_similarity_threshold: float = 0.82,
        max_consecutive_same_error: int = 2,
        min_entropy_threshold: float = 0.55,
        entropy_window: int = 4,
    ) -> None:
        self.diff_similarity_threshold = diff_similarity_threshold
        self.max_consecutive_same_error = max_consecutive_same_error
        self.min_entropy_threshold = min_entropy_threshold
        self.entropy_window = entropy_window

        self.turns: list[TurnRecord] = []
        self.constraints: list[NegativeConstraint] = []
        self.visited_graph_nodes: set[str] = set()
        self.total_tokens_saved: int = 0
        self.resets_triggered: int = 0
        self.last_reset_turn_idx: int = 0

    def record_turn(
        self,
        tool_name: str,
        target_file: str | None,
        action_payload: str,
        tool_output: str,
        is_error_or_test_failure: bool | None = None,
    ) -> LoopDiagnostic:
        """Record a completed turn and evaluate whether the agent is stuck in a loop."""
        err_sig = extract_error_signature(tool_output)
        if is_error_or_test_failure is None:
            is_error_or_test_failure = err_sig is not None

        if target_file:
            self.visited_graph_nodes.add(target_file)

        est_tokens = max(1, (len(action_payload) + len(tool_output)) // 4)
        turn = TurnRecord(
            turn_idx=len(self.turns) + 1,
            tool_name=tool_name,
            target_file=target_file,
            action_payload=action_payload,
            tool_output=tool_output,
            is_error_or_test_failure=is_error_or_test_failure,
            error_signature=err_sig if is_error_or_test_failure else None,
            tokens_consumed=est_tokens,
        )
        self.turns.append(turn)
        return self._diagnose_current_state()

    def _diagnose_current_state(self) -> LoopDiagnostic:
        current = self.turns[-1]
        active_turns = [t for t in self.turns if t.turn_idx > self.last_reset_turn_idx]
        entropy = compute_action_entropy(active_turns, window=self.entropy_window)

        # 1. Check consecutive identical error signatures since last reset
        consecutive_err = 0
        if current.error_signature:
            for t in reversed(active_turns):
                if t.error_signature == current.error_signature:
                    consecutive_err += 1
                elif t.is_error_or_test_failure:
                    break

        # 2. Check edit similarity against prior edits on the same file since last reset
        max_sim = 0.0
        if current.tool_name in self.EDIT_TOOLS and len(active_turns) >= 2:
            prior_edits = [
                t for t in active_turns[:-1]
                if t.tool_name in self.EDIT_TOOLS and t.target_file == current.target_file
            ]
            for pe in prior_edits[-3:]:
                sim = compute_diff_similarity(current.action_payload, pe.action_payload)
                max_sim = max(max_sim, sim)

        # Determine if a loop trigger fires
        loop_detected = False
        loop_type: str | None = None

        if consecutive_err >= self.max_consecutive_same_error and current.error_signature:
            loop_detected = True
            loop_type = "REPEATED_TEST_FAILURE_SIGNATURE"
        elif max_sim >= self.diff_similarity_threshold:
            loop_detected = True
            loop_type = "OSCILLATING_CODE_EDIT"
        elif len(active_turns) >= self.entropy_window and entropy < self.min_entropy_threshold:
            loop_detected = True
            loop_type = "LOW_ACTION_ENTROPY_STAGNATION"

        tokens_saved = 0
        if loop_detected:
            tokens_saved = self._trigger_counterfactual_reset(loop_type or "LOOP")
            self.last_reset_turn_idx = current.turn_idx

        policy = self._select_sampling_policy(current, loop_detected)
        return LoopDiagnostic(
            turn_idx=current.turn_idx,
            loop_detected=loop_detected,
            loop_type=loop_type,
            action_entropy=entropy,
            max_diff_similarity=round(max_sim, 4),
            consecutive_same_error=consecutive_err,
            tokens_saved_by_reset=tokens_saved,
            recommended_policy=policy,
        )

    def _trigger_counterfactual_reset(self, loop_type: str) -> int:
        """
        Collapse the degenerate tail of turns into a compact NegativeConstraint
        with a Graph-Guided Ego-Network Expansion directive (get_code_neighbors /
        get_code_subgraph) and compute KV-cache token savings.
        """
        self.resets_triggered += 1
        tail_window = min(len(self.turns), 4)
        degenerate_turns = self.turns[-tail_window:]

        collapsed_ids = [t.turn_idx for t in degenerate_turns]
        target_files = [t.target_file for t in degenerate_turns if t.target_file]
        primary_file = target_files[-1] if target_files else "repository"

        errors = [t.error_signature for t in degenerate_turns if t.error_signature]
        primary_error = errors[-1] if errors else f"Stagnant action pattern ({loop_type})"

        last_payload = degenerate_turns[-1].action_payload.strip().replace("\n", " ")[:120]
        digest = hashlib.sha1(f"{primary_file}:{last_payload}:{primary_error}".encode()).hexdigest()[:8]

        constraint = NegativeConstraint(
            constraint_id=f"NC-{self.resets_triggered:02d}-{digest}",
            turns_collapsed=collapsed_ids,
            target_file=primary_file,
            attempted_change_summary=last_payload or degenerate_turns[-1].tool_name,
            failure_signature=primary_error,
            directive=(
                f"STOP repeating edits on focal node `{primary_file}` with pattern `{last_payload[:60]}...`. "
                f"It consistently triggers `{primary_error}`. "
                f"Backtrack via Tree-of-Traversals over the repository code graph: query 1-hop caller/callee "
                f"neighbors (`get_code_neighbors` / `get_code_subgraph` around `{primary_file}`) or formulate "
                f"an orthogonal fix."
            ),
        )
        self.constraints.append(constraint)

        raw_tokens = sum(t.tokens_consumed for t in degenerate_turns)
        ledger_tokens = len(constraint.directive) // 4 + 25
        saved = max(0, raw_tokens - ledger_tokens)
        self.total_tokens_saved += saved
        return saved

    def _select_sampling_policy(self, current: TurnRecord, loop_detected: bool) -> SamplingPolicy:
        """Phase-Adaptive Thinking Budget & Temperature scheduler for Gemma 4."""
        if loop_detected:
            return SamplingPolicy(
                phase=AgentPhase.LOOP_RECOVERY,
                thinking_budget=6144,
                temperature=0.75,
                top_p=0.95,
                reason="Loop detected: expanding thinking budget and temperature to force counterfactual code-graph exploration.",
            )
        if current.is_error_or_test_failure:
            return SamplingPolicy(
                phase=AgentPhase.SYNTHESIZE_PATCH,
                thinking_budget=4096,
                temperature=0.45,
                top_p=0.95,
                reason="Test failure observed: allocating full thinking budget for root-cause traceback and subgraph diagnosis.",
            )
        if current.tool_name in self.INSPECT_TOOLS:
            if len(self.turns) == 1 or current.tool_name in {"search_similar_code", "get_code_subgraph"}:
                return SamplingPolicy(
                    phase=AgentPhase.LOCALIZE,
                    thinking_budget=2048,
                    temperature=0.3,
                    top_p=0.90,
                    reason="Repository code-graph localization (search_similar_code / get_code_subgraph): moderate thinking budget.",
                )
            return SamplingPolicy(
                phase=AgentPhase.INSPECT,
                thinking_budget=512,
                temperature=0.2,
                top_p=0.85,
                reason="Routine file or 1-hop neighbor inspection: throttling thinking tokens by 87.5% to preserve runtime budget.",
            )
        return SamplingPolicy(
            phase=AgentPhase.VERIFY_TEST,
            thinking_budget=2048,
            temperature=0.3,
            top_p=0.90,
            reason="Standard verification step.",
        )

    def render_negative_constraint_ledger(self) -> str:
        """Render the compact Negative Constraint Ledger injected into Gemma 4's context."""
        if not self.constraints:
            return ""
        lines = [
            "<NEGATIVE_CONSTRAINT_LEDGER>",
            "CRITICAL MEMORY RESET: Prior failed turns were pruned to prevent KV-cache context drift.",
            "You MUST NOT repeat any of the following falsified hypotheses:",
        ]
        for c in self.constraints:
            lines.append(
                f"- [{c.constraint_id}] (Turns {c.turns_collapsed}) Target `{c.target_file}`: "
                f"{c.directive}"
            )
        lines.append("</NEGATIVE_CONSTRAINT_LEDGER>")
        return "\n".join(lines)

    def prune_messages(self, messages: list[dict[str, Any]], keep_head: int = 2, keep_tail: int = 2) -> list[dict[str, Any]]:
        """
        Prune an OpenAI/vLLM-compatible message history when a loop reset occurs,
        replacing the bloated middle tool-call history with the Negative Constraint Ledger.
        """
        if not self.constraints or len(messages) <= (keep_head + keep_tail + 1):
            return messages
        head = messages[:keep_head]
        tail = messages[-keep_tail:]
        ledger_msg = {
            "role": "system",
            "content": self.render_negative_constraint_ledger(),
        }
        return head + [ledger_msg] + tail

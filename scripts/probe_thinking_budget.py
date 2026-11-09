"""Phase-2 payload proof: does ``thinking_budget`` reach the outgoing vLLM request?

Runs the REAL harness (``adk_submission.compile_submission`` +
``swegemma.config.build_submission_limits``) on two bundles, then performs a
1-turn stub model call with ``litellm.acompletion`` monkey-patched to capture
the exact ``completion_args`` that would be sent to vLLM's OpenAI-compatible
endpoint on 127.0.0.1:8000/v1.

Proves:
  a) ``thinking_budget: N`` (sampling.yaml) -> outgoing ``extra_body.thinking_token_budget: N``
     (+ ``extra_body.chat_template_kwargs.enable_thinking: true``)
  b) the two bundles differ ONLY in that field (no silent no-op).

Run:
  .venv-harness\\Scripts\\python.exe scripts/probe_thinking_budget.py
"""
from __future__ import annotations

import asyncio
import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILD = REPO / "build" / "probe_payloads"

BUNDLES = {
    "exp_think1024": REPO
    / "kaggle_work/gemma-4-developer-agent/bundles/exp_think1024",
    "exp05": REPO
    / "kaggle_work/gemma-4-developer-agent/bundles/exp05_patch_integrity",
}

TOOLS = {name: (lambda **_: "{}") for name in (
    "run_command", "read_file", "edit_file", "write_file", "get_status",
    "submit_patch", "search_similar_code", "get_code_neighbors",
    "get_code_subgraph",
)}


class _Captured(Exception):
    """Raised after the stub captures completion_args (no network needed)."""

    def __init__(self, payload: dict):
        super().__init__("captured outgoing request")
        self.payload = payload


async def probe_bundle(bundle_dir: Path) -> dict:
    from google.genai import types
    from google.adk.models import lite_llm as lite_llm_mod
    from google.adk.models.llm_request import LlmRequest
    from google.adk.models.lite_llm import LiteLlm
    import litellm

    from adk_submission import ModelRegistry, compile_submission, validate_directory
    from adk_submission.discovery import discover_declared_models
    from swegemma.config import build_submission_limits

    # Parity with the scorer: swegemma sets litellm.drop_params = True
    litellm.drop_params = True

    limits, constraints = build_submission_limits()
    validate_directory(bundle_dir, limits)
    declared = sorted(discover_declared_models(bundle_dir))
    assert len(declared) == 1, f"expected one declared model: {declared}"
    alias = declared[0]

    registry = ModelRegistry()
    registry.register(
        alias,
        LiteLlm(
            model=alias,
            api_key="EMPTY",
            api_base="http://127.0.0.1:8000/v1",  # scorer endpoint (README §3)
            num_retries=5,
        ),
    )
    agent = compile_submission(
        bundle_dir, TOOLS, registry,
        limits=limits, generation_constraints=constraints,
    )

    gen_cfg = agent.generate_content_config
    resolved = gen_cfg.model_dump(exclude_none=True)
    model = agent.model
    additional_args = copy.deepcopy(model._additional_args)

    # --- 1-turn stub call: capture the exact outgoing completion_args -------
    async def _capture(**kwargs):
        raise _Captured(kwargs)  # capture BEFORE litellm/vLLM see anything

    original = model.llm_client.acompletion
    model.llm_client.acompletion = _capture  # the exact call site (lite_llm.py:2467)
    try:
        llm_request = LlmRequest(
            contents=[types.Content(role="user", parts=[types.Part(text="probe")])]
        )
        # mirrors google/adk/flows/llm_flows/basic.py:49-53 exactly
        llm_request.config = gen_cfg.model_copy(deep=True)
        async for _ in model.generate_content_async(llm_request):  # raises _Captured
            pass
    except _Captured as captured:
        payload = captured.payload
    finally:
        model.llm_client.acompletion = original

    messages = payload.get("messages") or []
    summary = []
    for msg in messages:
        content = msg.get("content")
        summary.append({
            "role": msg.get("role"),
            "content_chars": len(content) if isinstance(content, str) else None,
            "keys": sorted(k for k in msg.keys() if k != "tool_calls"),
            "head": (content[:180] + "…") if isinstance(content, str) and len(content) > 180 else content,
        })

    request_summary = {
        key: payload[key]
        for key in sorted(payload.keys())
        if key not in {"messages", "tools", "response_format"}
    }
    tools = payload.get("tools")
    tool_names = []
    if tools:
        for tool in tools:
            function = (tool or {}).get("function") or {}
            tool_names.append(function.get("name"))

    return {
        "bundle": bundle_dir.name,
        "declared_model": alias,
        "resolved_generate_content_config": resolved,
        "compiled_model_object": {
            "class": type(model).__name__,
            "model": model.model,
            "api_base": additional_args.get("api_base"),
            "num_retries": additional_args.get("num_retries"),
            "_additional_args": additional_args,
        },
        "outgoing_request": {
            "model": payload.get("model"),
            "api_base": payload.get("api_base"),
            "temperature": payload.get("temperature"),
            "top_p": payload.get("top_p"),
            "max_completion_tokens": payload.get("max_completion_tokens"),
            "extra_body": payload.get("extra_body"),
            "drop_params": payload.get("drop_params"),
            "all_keys": sorted(payload.keys()),
            "messages_summary": summary,
            "tool_count": len(tool_names),
            "tool_names": tool_names,
        },
        "raw_completion_args": payload,
        "thinking_config_via_llm_request": (
            llm_request.config.thinking_config.model_dump(exclude_none=True)
            if getattr(llm_request.config, "thinking_config", None) else None
        ),
    }


def _mask(raw: dict) -> dict:
    """Copy raw completion_args with messages masked (for diffing)."""
    masked = json.loads(json.dumps(raw, default=str))
    if isinstance(masked.get("messages"), list):
        masked["messages"] = [
            {"role": (m or {}).get("role"), "content": "__MASKED__"}
            for m in masked["messages"]
        ]
    if masked.get("tools"):
        masked["tools"] = "__MASKED__"
    return masked


def main() -> int:
    results = {}
    for label, directory in BUNDLES.items():
        assert directory.exists(), f"missing bundle: {directory}"
        results[label] = asyncio.run(probe_bundle(directory))

    BUILD.mkdir(parents=True, exist_ok=True)
    for label, result in results.items():
        target = BUILD / f"{label}.json"
        target.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"[SAVED] {target}")

    for label, result in results.items():
        out = result["outgoing_request"]
        args_ = result["compiled_model_object"]["_additional_args"]
        extra_body = out.get("extra_body") or args_.get("extra_body")
        print(f"\n=== {label} ===")
        print(f"  declared model        : {result['declared_model']}")
        print(f"  bundled thinking_budget: {result['resolved_generate_content_config'].get('thinking_config')}")
        print(f"  compiled extra_body    : {json.dumps(extra_body)}")
        print(f"  outgoing thinking_token_budget: {out.get('extra_body', {}).get('thinking_token_budget')}")
        print(f"  outgoing temperature/top_p/max_completion_tokens: "
              f"{out.get('temperature')}/{out.get('top_p')}/{out.get('max_completion_tokens')}")
        print(f"  outgoing request keys  : {out.get('all_keys')}")
        print(f"  messages: {len(out.get('messages_summary') or [])}, tools: {out.get('tool_count')}")

    think = results["exp_think1024"]
    base = results["exp05"]
    print("\n=== verdict ===")
    ok = True
    try:
        assert think["outgoing_request"]["extra_body"] == {
            "chat_template_kwargs": {"enable_thinking": True},
            "thinking_token_budget": 1024,
        }, think["outgoing_request"]["extra_body"]
        assert base["outgoing_request"]["extra_body"] == {
            "chat_template_kwargs": {"enable_thinking": True},
            "thinking_token_budget": 4096,
        }, base["outgoing_request"]["extra_body"]
        left, right = _mask(think["raw_completion_args"]), _mask(base["raw_completion_args"])
        diffs = {
            key: (left.get(key), right.get(key))
            for key in sorted(set(left) | set(right))
            if left.get(key) != right.get(key)
        }
        interesting = {
            k: v for k, v in diffs.items()
            if k not in {"extra_body", "_adk_include_thoughts"}
        }
        if interesting:
            print(f"[DIFF] other-than-budget differences: {json.dumps(interesting, default=str)}")
            ok = False
        else:
            print("[PROOF] outgoing payloads identical except extra_body.thinking_token_budget")
        print("[PROOF] thinking_budget 1024 (exp_think1024) and 4096 (exp05) both reach the "
              "outgoing vLLM request as extra_body.thinking_token_budget")
    except AssertionError as error:
        print(f"[FAIL] {error}")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

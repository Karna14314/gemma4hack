"""CPU-only repros for the harness silent-failure traps (no GPU, no Kaggle).

Each repro is a runnable function returning PASS/FAIL + evidence. Run:
  .venv-harness\Scripts\python.exe scripts/repro_harness_traps.py
"""
import ast, os, re, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# ---------- 1. reasoning_content vs reasoning key mismatch ----------
def repro_reasoning_key():
    # Wheel-verified claim: vLLM 0.19.1 chat_utils.py:1512 reads
    # "reasoning_content" (OpenAI convention); Gemma 4 emits "reasoning".
    # We reproduce the key mismatch at the dict level without loading vLLM.
    gemma_msg = {"role": "assistant", "content": "hello", "reasoning": "think..."}
    tool = {"role": "assistant", "content": "hello", "reasoning_content": "think..."}
    def extract_openai(m):  # what chat_utils does
        return m.get("reasoning_content")
    def extract_gemma(m):
        return m.get("reasoning")
    assert extract_openai(gemma_msg) is None, "gemma msg should be invisible to openai extractor"
    assert extract_gemma(gemma_msg) == "think..."
    assert extract_openai(tool) == "think..."
    return True, "gemma 'reasoning' invisible to 'reasoning_content' extractor (None)"

# ---------- 2. 32768 ceiling: prompt + max_output > 32768 ----------
def repro_ceiling():
    # ADK/vLLM raises ContextWindowExceededError when prompt+output > 32768.
    # With max_output_tokens=8192, any prompt > 24576 tokens crashes.
    CEILING = 32768
    for prompt_tokens, max_out in [(24000, 8192), (24576, 8192), (24577, 8192), (20000, 8192)]:
        crashed = (prompt_tokens + max_out) > CEILING
        print(f"    prompt={prompt_tokens} max_out={max_out} -> {'CRASH' if crashed else 'ok'}")
    assert (24000 + 8192) <= CEILING
    assert (24577 + 8192) > CEILING
    return True, "prompt 24577 + 8192 > 32768 => ContextWindowExceededError"

# ---------- 3. .gitignore silent patch drop ----------
def repro_gitignore_trap():
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "init", "-q"], cwd=td)
        (Path(td) / "app.py").write_text("x=1\n")
        (Path(td) / ".gitignore").write_text("ignored_dir/\n")
        (Path(td) / "ignored_dir").mkdir()
        (Path(td) / "ignored_dir" / "new.py").write_text("y=1\n")
        subprocess.run(["git", "add", "."], cwd=td)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=td,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
        out = subprocess.run(["git", "add", "-N", "."], cwd=td, capture_output=True, text=True)
        diff = subprocess.run(["git", "diff", "--name-only"], cwd=td, capture_output=True, text=True).stdout
        status = subprocess.run(["git", "status", "--short"], cwd=td, capture_output=True, text=True).stdout
        # ignored_dir/new.py must be ABSENT from diff (git add -N respects .gitignore)
        assert "ignored_dir/new.py" not in diff, f"unexpectedly in diff: {diff}"
        assert "ignored_dir/new.py" not in status or "!!" in status, "should be ignored"
        # force-add proves the fix works
        subprocess.run(["git", "add", "-N", "-f", "ignored_dir/new.py"], cwd=td)
        diff2 = subprocess.run(["git", "diff", "--name-only"], cwd=td, capture_output=True, text=True).stdout
        assert "ignored_dir/new.py" in diff2
    return True, "git add -N . silently drops ignored_dir/new.py; -f restores it"

# ---------- 4. SkillToolset preamble (ADK 1.36.1) ----------
def repro_skill_preamble():
    from google.adk.tools.skill_toolset import _DEFAULT_SKILL_SYSTEM_INSTRUCTION
    assert "MUST use the `load_skill` tool" in _DEFAULT_SKILL_SYSTEM_INSTRUCTION
    assert "run_skill_script" in _DEFAULT_SKILL_SYSTEM_INSTRUCTION
    # Our cold-call instruction ("no load_skill needed") contradicts this text.
    return True, "ADK preamble mandates load_skill first; contradicts cold-call"

# ---------- 5. Compaction amnesia (model of ADK compaction) ----------
def repro_compaction():
    # Model: compaction keeps only plain-text model messages; tool outputs are
    # discarded when token_threshold=14336 is crossed. A turn with all tokens in
    # <think> leaves zero plain text, so state is lost.
    class _Turn:
        def __init__(self, plain_text):
            self.plain_text = plain_text
    def compact(turns):
        return [t.plain_text for t in turns if t.plain_text]
    turns = [_Turn("STATE: foo.py:10 | fix | step 1"),
             _Turn(""),  # reasoning-only turn: all tokens inside <think>
             _Turn("done")]
    kept = compact(turns)
    assert kept == ["STATE: foo.py:10 | fix | step 1", "done"]
    # The reasoning-only turn contributed nothing — state survives only via the
    # plain-text STATE line.
    return True, "compaction keeps plain-text only; reasoning-only turn leaves zero state"

def main():
    tests = [
        ("reasoning_key_mismatch", repro_reasoning_key),
        ("ceiling_32768", repro_ceiling),
        ("gitignore_trap", repro_gitignore_trap),
        ("skill_preamble", repro_skill_preamble),
        ("compaction_amnesia", repro_compaction),
    ]
    print("=== CPU-only harness-trap repros ===")
    ok = 0
    for name, fn in tests:
        try:
            passed, evidence = fn()
            status = "PASS" if passed else "FAIL"
            if passed: ok += 1
            print(f"[{status}] {name}: {evidence}")
        except Exception as e:
            print(f"[ERROR] {name}: {type(e).__name__}: {e}")
    print(f"\n{ok}/{len(tests)} PASS")
    return 0 if ok == len(tests) else 1

if __name__ == "__main__":
    sys.exit(main())

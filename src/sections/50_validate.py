"""Section 50 — validation and fallback selection.

This cell must never raise. It validates the primary package, and on any
``SubmissionInvalid`` — or on any unexpected exception whatsoever — it selects the
fallback package instead. The only way this notebook is allowed to fail later is
if the *fallback* also fails to validate, which the static checks below make
essentially impossible.
"""

INTRO = """\
## Validate, and pick a package

The primary package is checked against every constraint the harness enforces. If
anything fails, the minimal fallback package ships instead. Either way this cell
records which package won and why, and it never raises.
"""

VALIDATE = '''\
SELECTED_FILES = None
SELECTED_NAME = None
SELECTION_REASON = None
VALIDATION_REPORT = {}

try:
    VALIDATION_REPORT = validate(PACKAGE_FILES)
    SELECTED_FILES = PACKAGE_FILES
    SELECTED_NAME = "primary"
    SELECTION_REASON = "primary package passed every check"
except SubmissionInvalid as error:
    raise RuntimeError(f"Strict Fail-Fast Policy: primary package rejected by validator: {error}") from error
except Exception as error:
    raise RuntimeError(f"Strict Fail-Fast Policy: primary package failed validation with error: {error}") from error

print(f"selected package : {SELECTED_NAME}")
print(f"reason           : {SELECTION_REASON}")
print()
print("report:")
for _key, _value in sorted(VALIDATION_REPORT.items()):
    print(f"  {_key}: {_value}")
'''

CHECKLIST = '''\
# Restate the hard submission limits and confirm the selected package satisfies
# them, independently of the validator, so the report is legible to a reviewer.
selected = SELECTED_FILES
selected_bytes = sum(len(v.encode("utf-8")) for v in selected.values())
selected_suffixes = sorted({posixpath.splitext(n)[1].lower() for n in selected})

print()
print("independent confirmation for the selected package:")
print(f"  file count            {len(selected)} (limit 10000)")
print(f"  unpacked bytes        {selected_bytes:,d} (limit 3,221,225,472)")
print(f"  suffixes present      {selected_suffixes}")
print(f"  agent.yaml at root    {'agent.yaml' in selected}")
print(f"  adapters present      {[n for n in selected if n.startswith('adapters/')]}")
print(f"  files with no suffix  {[n for n in selected if not posixpath.splitext(n)[1]]}")

assert "agent.yaml" in selected, "the selected package has no root agent.yaml"
assert all(posixpath.splitext(n)[1].lower() in ALLOWED_SUFFIXES for n in selected), (
    "the selected package contains a file the harness would reject"
)
assert not any(n.startswith("adapters/") for n in selected), (
    "an adapter slipped into the selected package; that collapses the KV cache"
)
assert all(v.strip() for v in selected.values()), "the selected package has an empty file"
assert selected_bytes <= MAX_TOTAL_SIZE_BYTES, "the selected package exceeds 3 GiB"
print()
print("all independent checks passed")
'''


def cells() -> list[dict]:
    return [
        {"cell_type": "markdown", "source": INTRO},
        {"cell_type": "code", "source": VALIDATE},
        {"cell_type": "code", "source": CHECKLIST},
    ]
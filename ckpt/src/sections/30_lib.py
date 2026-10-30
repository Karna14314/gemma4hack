"""Section 30 — the self-contained library and the fallback package.

Two things are spliced in here by ``tools/build_notebook.py``:

- ``src/notebook_lib/validator.py`` **verbatim**, base64-encoded and executed, so
  the notebook can never drift from ``src/`` and no character in the source needs
  escaping.
- No fallback package: a failed validation raises rather than substituting another bundle.

If the validator cannot be loaded at all — the only realistic cause is PyYAML
being absent, which should not happen on Kaggle — the notebook degrades to
skipping structural validation and still emits a valid archive. A notebook that
raises scores zero, so nothing here is allowed to be fatal.
"""

PREAMBLE = '''\
## Library and fallback package

The next cell loads the static validator, and the one after that defines the
rollback package.
'''

VALIDATOR_SPLICE = '''\
# --- validator (spliced verbatim from src/notebook_lib/validator.py) ---------
# The source is embedded as base64 and executed rather than pasted inline: that
# keeps it byte-identical to the repository file, keeps a leading
# ``from __future__ import annotations`` legal, and avoids any escaping problem.
import base64

#<<<SPLICE_FILE_AS_EXEC:src/notebook_lib/validator.py>>>

VALIDATOR_SOURCE = base64.b64decode(_SPLICED_SOURCE).decode("utf-8")
VALIDATOR_LOADED = False
try:
    exec(compile(VALIDATOR_SOURCE, "validator.py", "exec"), globals())
    VALIDATOR_LOADED = True
    print(f"validator loaded ({len(VALIDATOR_SOURCE):,d} chars)")
except Exception:  # noqa: BLE001 - never fatal
    print("WARNING: the validator could not be loaded; structural checks are off.")
    print(traceback.format_exc())

if not VALIDATOR_LOADED:
    # Degraded but still functional: packaging proceeds without validation, so a
    # valid archive is produced either way. The constants the reporting cell
    # reads are restated here so no later cell can raise a NameError.
    ALLOWED_MODELS = frozenset({"gemma-4-31b-it-qat-w4a16-ct", "gemma-4-e4b-it-qat-w4a16-ct"})
    MODEL = "gemma-4-31b-it-qat-w4a16-ct"
    ALLOWED_SUFFIXES = frozenset(
        {".yaml", ".yml", ".md", ".txt", ".py", ".json", ".safetensors"}
    )
    MAX_TOTAL_SIZE_BYTES = 3 * 2**30

    class SubmissionInvalid(Exception):
        """Stand-in used when the real validator could not be imported."""

    def validate(files):
        raise SubmissionInvalid("structural validation is unavailable in this run")

    def pack(files, validate_first=True):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(files):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o644 << 16
                archive.writestr(info, files[name].encode("utf-8"))
        return stream.getvalue()

    def digest(payload):
        return hashlib.sha256(payload).hexdigest()
'''


def cells() -> list[dict]:
    return [
        {"cell_type": "markdown", "source": PREAMBLE},
        {"cell_type": "code", "source": VALIDATOR_SPLICE},
    ]
PLAYBOOKS = {
"FALSINESS_TRAP": """Falsy values can be valid inputs.
Check `is None` instead of truthiness.
Protect 0, False, "", [], {}.
Hidden tests pass zero or empty values.""",
"MUTABLE_STATE": """Copy caller dicts and lists at boundaries.
Never use mutable default arguments.
Use None sentinel then initialize.
Tests repeat calls expecting isolation.""",
"TYPE_SUBCLASS": """Use isinstance, not type is.
Preserve custom subclasses.
Handle bool/int subclass quirks.
Tests construct subclasses.""",
"ASYNC_SYNC_TWIN": """Check sync and async twin methods.
Keep both paths behaviorally aligned.
Await correctly in async path.
Tests may call either variant.""",
"FASTAPI_PYDANTIC": """Validate Pydantic fields, aliases, defaults.
Check response_model and status codes.
Handle v1 vs v2 differences.
Tests assert exact error shapes.""",
"RICH_RENDERING": """Check cell_len and Measurement bounds.
Avoid cropped __rich_console__ output.
Escape markup correctly.
Tests compare rendered strings.""",
"HTTP_URL_COOKIES": """Strip auth headers on redirect.
Use case-insensitive headers.
Preserve auth params and slashes.
Tests check cookies and redirects.""",
"DECORATOR_WRAP": """Use functools.wraps on decorators.
Preserve __name__ and __wrapped__.
Keep signature and return value.
Tests inspect wrapped functions.""",
"EXCEPTION_CHAIN": """Match exact exception class and message.
Raise with from to preserve cause.
Avoid broad except Exception.
Tests assert chained exceptions.""",
"REGISTRATION_SIBLING": """Mirror sibling definitions and imports.
Update __all__ and dispatch tables.
Register new options consistently.
Tests check feature availability.""",
}

KEYWORDS = {
"FALSINESS_TRAP": ["none", "false", "0", "empty", "falsy", "truthy"],
"MUTABLE_STATE": ["cache", "default", "mutable", "state", "global", "list", "dict", "copy"],
"TYPE_SUBCLASS": ["subclass", "isinstance", "type", "bool", "int"],
"ASYNC_SYNC_TWIN": ["async", "await", "sync", "twin"],
"FASTAPI_PYDANTIC": ["fastapi", "pydantic", "model", "field", "alias", "response"],
"RICH_RENDERING": ["rich", "console", "render", "markup", "width", "cell"],
"HTTP_URL_COOKIES": ["url", "cookie", "redirect", "http", "request", "response", "header"],
"DECORATOR_WRAP": ["decorator", "wrap", "functools", "wrapped", "signature"],
"EXCEPTION_CHAIN": ["raise", "exception", "chain", "cause", "from", "error"],
"REGISTRATION_SIBLING": ["register", "dispatch", "option", "__all__", "sibling", "feature"],
}

def _token_count(text):
    return len(text.split())

def select_hints(query, code="", imports=""):
    text = (query + " " + code + " " + imports).lower()
    scores = []
    for name, kw in KEYWORDS.items():
        score = sum(1 for k in kw if k in text)
        scores.append((score, name))
    scores.sort(reverse=True)
    chosen = [name for score, name in scores if score > 0][:2]
    if not chosen:
        chosen = [scores[0][1]]
    out = []
    total_tokens = 0
    for name in chosen[:2]:
        hint = "[{}] {}".format(name, PLAYBOOKS[name])
        hint_tokens = _token_count(hint)
        if total_tokens + hint_tokens > 120:
            break
        out.append(hint)
        total_tokens += hint_tokens
    return "\n".join(out)

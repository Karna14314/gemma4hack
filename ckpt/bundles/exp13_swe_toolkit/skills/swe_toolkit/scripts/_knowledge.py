PLAYBOOKS = {
"FALSINESS_TRAP": "Falsy values like 0, '', [], {} can be valid; check `is None` instead of truthiness. Hidden tests often pass zero/empty inputs.",
"MUTABLE_STATE": "Mutable default args or shared caches leak across calls; use None sentinel and copy. Tests repeat calls expecting isolation.",
"TYPE_SUBCLASS": "isinstance checks and subclass coercion; ensure subclass overrides and base behavior align. Watch bool/int subclass quirks.",
"ASYNC_SYNC_TWIN": "Async and sync twin functions must stay consistent; fix both paths and await correctly. Tests may call either.",
"FASTAPI_PYDANTIC": "Pydantic validation/serialization: field types, aliases, defaults, and response models. Check status codes and error shapes.",
"RICH_RENDERING": "Rich console/render: markup escaping, width, and object repr. Tests often compare rendered strings exactly.",
"HTTP_URL_COOKIES": "URL join, query params, cookies, redirects, and encoding. Preserve trailing slashes and case sensitivity.",
"DECORATOR_WRAP": "Decorator must preserve __name__, __wrapped__, signature, and return value. Tests inspect functools.wraps.",
"EXCEPTION_CHAIN": "Raise with `from` to preserve cause; match exception type/message exactly. Tests assert chained exceptions.",
"REGISTRATION_SIBLING": "New feature must register in __all__, dispatch tables, option lists, imports. Missing registration fails hidden tests.",
}

KEYWORDS = {
"FALSINESS_TRAP": ["none","false","0","empty","falsy","truthy"],
"MUTABLE_STATE": ["cache","default","mutable","state","global","list","dict"],
"TYPE_SUBCLASS": ["subclass","isinstance","type","bool","int"],
"ASYNC_SYNC_TWIN": ["async","await","sync","twin"],
"FASTAPI_PYDANTIC": ["fastapi","pydantic","model","field","alias"],
"RICH_RENDERING": ["rich","console","render","markup","width"],
"HTTP_URL_COOKIES": ["url","cookie","redirect","http","request","response"],
"DECORATOR_WRAP": ["decorator","wrap","functools","__wrapped__"],
"EXCEPTION_CHAIN": ["raise","exception","chain","cause","from"],
"REGISTRATION_SIBLING": ["register","dispatch","option","__all__","sibling"],
}

def select_hints(query, code="", imports=""):
    text=(query+" "+code+" "+imports).lower()
    scores=[]
    for name, kw in KEYWORDS.items():
        s=sum(1 for k in kw if k in text)
        scores.append((s,name))
    scores.sort(reverse=True)
    chosen=[n for s,n in scores if s>0][:2]
    if not chosen:
        chosen=[scores[0][1]]
    out=[]
    for n in chosen[:2]:
        out.append(f"[{n}] {PLAYBOOKS[n]}")
    return "\n".join(out)

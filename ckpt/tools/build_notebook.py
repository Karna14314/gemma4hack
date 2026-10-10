"""Build the submission notebook from the section modules in ``src/sections``.

The notebook is generated, never hand-edited. Two properties matter:

* **No drift.** Sections may contain splice markers, and the builder replaces them
  with the current text of the referenced file, directory or Python literal. So
  ``src/notebook_lib/validator.py`` and ``src/agent_package/`` have exactly one
  copy in the repository and the notebook cannot lag behind them.
* **A missing splice is a build failure.** If a marker survives substitution, the
  build raises rather than emitting a notebook containing a literal marker.

Usage::

    python tools/build_notebook.py
    python tools/build_notebook.py --out build/submission_notebook.ipynb
    python tools/build_notebook.py --bundle kaggle_work/.../bundles/exp04_x \
        --out kaggle_work/.../experiments/exp04/submission_notebook.ipynb

``--bundle DIR`` splices a bundle other than the primary ``src/agent_package``
(used to build the ablation kernels) with no other change.
"""

from __future__ import annotations

import argparse
import base64
import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS_DIR = ROOT / "src" / "sections"
DEFAULT_OUT = ROOT / "build" / "submission_notebook.ipynb"

# #<<<SPLICE_FILE:relative/path>>>
SPLICE_FILE = re.compile(r"^#<<<SPLICE_FILE:(?P<path>[^>]+)>>>[ \t]*$", re.MULTILINE)
# #<<<SPLICE_FILE_AS_EXEC:relative/path>>> - the file's text, embedded base64 and
# executed, so a source file containing quotes, backslashes or a __future__
# import is spliced with no escaping risk at all.
SPLICE_FILE_AS_EXEC = re.compile(
    r"^#<<<SPLICE_FILE_AS_EXEC:(?P<path>[^>]+)>>>[ \t]*$", re.MULTILINE
)
# #<<<SPLICE_DIR_LITERAL:relative/dir:VARIABLE_NAME>>>
SPLICE_DIR_LITERAL = re.compile(
    r"^#<<<SPLICE_DIR_LITERAL:(?P<path>[^:>]+):(?P<var>[A-Za-z_][A-Za-z0-9_]*)>>>[ \t]*$",
    re.MULTILINE,
)
# #<<<SPLICE_PY_LITERAL:module.path:ATTR:VARIABLE_NAME>>>
SPLICE_PY_LITERAL = re.compile(
    r"^#<<<SPLICE_PY_LITERAL:(?P<module>[A-Za-z_][\w.]*):(?P<attr>[A-Za-z_][A-Za-z0-9_]*)"
    r":(?P<var>[A-Za-z_][A-Za-z0-9_]*)>>>[ \t]*$",
    re.MULTILINE,
)
ANY_SPLICE = re.compile(r"#<<<SPLICE_[A-Z_]+:")


def _iter_source_files(base: Path) -> list[Path]:
    return sorted(
        p for p in base.rglob("*") if p.is_file() and not p.is_symlink()
    )


def _render_dir_literal(relative: str, var: str) -> str:
    """Render a whole directory as a ``{posix path: text}`` dict literal.

    Sorted by path so the generated cell is stable across runs and across
    platforms. Every file in the package is ``.yaml``, ``.md`` or ``.txt``, so no
    file here can have a suffix the harness would reject.
    """
    base = ROOT / relative
    if not base.is_dir():
        raise SystemExit(f"splice target is not a directory: {relative}")
    lines = [f"{var} = {{"]
    for path in _iter_source_files(base):
        rel = path.relative_to(base).as_posix()
        lines.append(f"    {rel!r}: {path.read_text(encoding='utf-8')!r},")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _render_py_literal(module: str, attr: str, var: str) -> str:
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    imported = importlib.import_module(module)
    if not hasattr(imported, attr):
        raise SystemExit(f"splice target has no attribute {module}:{attr}")
    return f"{var} = {getattr(imported, attr)!r}\n"


def _render_exec_literal(relative: str) -> str:
    """Render a source file as base64 plus an ``exec`` of its decoded text.

    Base64 means the file's exact bytes survive regardless of quotes, backslashes
    or non-ASCII characters in the source. Executing rather than inlining also
    keeps a leading ``from __future__ import annotations`` legal, since it stays
    the first statement of its own compiled unit.
    """
    path = ROOT / relative
    if not path.is_file():
        raise SystemExit(f"splice target is not a file: {relative}")
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"_SPLICED_SOURCE = {payload!r}\n"


def resolve_splices(source: str, where: str, bundle_root: Path | None = None) -> str:
    """Replace every splice marker in ``source`` with generated content.

    ``bundle_root`` overrides the directory spliced by the
    ``SPLICE_DIR_LITERAL`` marker for the agent package, so the same section
    modules can build a kernel for any bundle directory.
    """

    def sub_file(match: re.Match) -> str:
        path = ROOT / match.group("path")
        if not path.is_file():
            raise SystemExit(f"splice target is not a file: {match.group('path')}")
        return path.read_text(encoding="utf-8").rstrip("\n")

    def sub_exec(match: re.Match) -> str:
        return _render_exec_literal(match.group("path")).rstrip("\n")

    def sub_dir(match: re.Match) -> str:
        target = match.group("path")
        if bundle_root is not None and target == "src/agent_package":
            target = str(bundle_root)
        return _render_dir_literal(target, match.group("var")).rstrip("\n")

    def sub_py(match: re.Match) -> str:
        return _render_py_literal(
            match.group("module"), match.group("attr"), match.group("var")
        ).rstrip("\n")

    source = SPLICE_FILE.sub(sub_file, source)
    source = SPLICE_FILE_AS_EXEC.sub(sub_exec, source)
    source = SPLICE_DIR_LITERAL.sub(sub_dir, source)
    source = SPLICE_PY_LITERAL.sub(sub_py, source)

    leftover = ANY_SPLICE.search(source)
    if leftover:
        raise SystemExit(
            f"unresolved splice marker in {where}: {source[leftover.start():leftover.start() + 80]!r}"
        )
    return source


def load_sections() -> list[tuple[str, list[dict]]]:
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    package = ROOT / "src" / "sections" / "__init__.py"
    if not package.exists():
        package.write_text('"""Notebook section modules."""\n', encoding="utf-8")
    modules = sorted(
        p for p in SECTIONS_DIR.glob("*.py") if not p.name.startswith("_")
    )
    if not modules:
        raise SystemExit(f"no section modules found in {SECTIONS_DIR}")
    sections = []
    for path in modules:
        name = f"sections.{path.stem}"
        module = importlib.import_module(name)
        cells = module.cells()
        if not isinstance(cells, list) or not cells:
            raise SystemExit(f"{name}.cells() must return a non-empty list")
        sections.append((path.name, cells))
    return sections


def build(out_path: Path, bundle_root: Path | None = None) -> Path:
    import nbformat

    nb = nbformat.v4.new_notebook()
    nb.cells = []

    for section_name, cells in load_sections():
        for index, cell in enumerate(cells):
            kind = cell.get("cell_type")
            if kind not in ("markdown", "code"):
                raise SystemExit(f"{section_name} cell {index}: bad cell_type {kind!r}")
            source = resolve_splices(
                cell.get("source", ""), f"{section_name} cell {index}", bundle_root
            )
            if not source.strip():
                raise SystemExit(f"{section_name} cell {index}: empty source")
            if kind == "markdown":
                nb.cells.append(nbformat.v4.new_markdown_cell(source))
            else:
                nb.cells.append(nbformat.v4.new_code_cell(source))

    nb.metadata.update(
        {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        }
    )

    # Validate before writing, then validate again after a round trip so that a
    # malformed notebook can never reach disk.
    nbformat.validate(nb)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, str(out_path))

    reloaded = nbformat.read(str(out_path), as_version=4)
    nbformat.validate(reloaded)
    if len(reloaded.cells) != len(nb.cells):
        raise SystemExit("cell count changed across the write/read round trip")

    code_cells = sum(1 for c in reloaded.cells if c.cell_type == "code")
    md_cells = len(reloaded.cells) - code_cells
    print(f"wrote {out_path}")
    print(f"  cells: {len(reloaded.cells)} ({code_cells} code, {md_cells} markdown)")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="bundle directory to splice instead of src/agent_package",
    )
    args = parser.parse_args()
    build(args.out, args.bundle)


if __name__ == "__main__":
    main()
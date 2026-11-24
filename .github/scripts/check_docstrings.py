"""Check that the docstrings of the packages are in Google style.

CONTRIBUTING.md asks for Google style. ruff checks the format of the Google
sections it knows, but reads anything else as plain text. This means that ruff
does not catch cases where you accidentally mix documentation styles.

This script thus attempts to catch most common errors when errors styles:

- a Google section under another of its names, such as `Params:` for `Args:`
- a NumPy section: a title underlined with dashes
- a Sphinx field such as `:param name:`, a reST directive such as `.. note::`,
  and a Sphinx role such as `:class:`

Code in a fenced block or a doctest is not checked. A docstring is the string
that starts a module, a class or a function, and the string below a field.

Run it from the repository root. It needs only the standard library, and takes
files to check instead of every package source file:

    python .github/scripts/check_docstrings.py [file ...]
"""

import ast
import os
import re
import sys
from pathlib import Path

# The other names griffe reads a section under, or a name it does not read,
# and the one to write instead.
RENAMED = {
    "Arguments": "Args",
    "Params": "Args",
    "Parameters": "Args",
    "Keyword Args": "Other Parameters",
    "Keyword Arguments": "Other Parameters",
    "Other Args": "Other Parameters",
    "Other Arguments": "Other Parameters",
    "Other Params": "Other Parameters",
    "Return": "Returns",
    "Yield": "Yields",
    "Exceptions": "Raises",
    "Example": "Examples",
    "Warns": "Warning",
    "Warnings": "Warning",
}

# The Google section for each NumPy section.
NUMPY_SECTIONS = {
    "Parameters": "Args",
    "Other Parameters": "Other Parameters",
    "Returns": "Returns",
    "Yields": "Yields",
    "Raises": "Raises",
    "Examples": "Examples",
    "Notes": "Note",
    "Warnings": "Warning",
    "See Also": "See Also",
}

SECTION = re.compile(r"^\s*(?P<name>[A-Z][A-Za-z ]*?)\s*:\s*$")
TITLE = re.compile(r"^\s*(?P<name>[A-Z][A-Za-z ]*?)\s*$")
UNDERLINE = re.compile(r"^\s*-{3,}\s*$")
FIELD = re.compile(
    r"^\s*:(param|parameter|arg|argument|key|keyword|type|raises?|except"
    r"|exception|returns?|rtype|yields?|ytype|var|ivar|cvar|vartype)\b[^:]*:"
)
# The Google section for each kind of Sphinx field. An attribute field has none.
FIELD_SECTIONS = {
    "param": "Args",
    "parameter": "Args",
    "arg": "Args",
    "argument": "Args",
    "key": "Args",
    "keyword": "Args",
    "type": "Args",
    "raise": "Raises",
    "raises": "Raises",
    "except": "Raises",
    "exception": "Raises",
    "return": "Returns",
    "returns": "Returns",
    "rtype": "Returns",
    "yield": "Yields",
    "yields": "Yields",
    "ytype": "Yields",
}
DIRECTIVE = re.compile(r"^\s*\.\. [\w:-]+::")
ROLE = re.compile(r":(?:py:)?(?:class|meth|func|attr|exc|obj|mod|data|const|ref):(?=`)")
FENCE = re.compile(r"^\s*(?:`{3,}|~{3,})")
OPENING_QUOTES = re.compile(r"^\s*[rbuRBU]*(?:\"\"\"|'''|\"|')")
SCOPES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def source_files() -> list[Path]:
    return sorted(Path("src").glob("*/src/**/*.py"))


def docstrings(tree: ast.Module) -> list[ast.Expr]:
    return [
        statement
        for node in ast.walk(tree)
        if isinstance(node, SCOPES)
        for statement in node.body
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    ]


def problems(lines: list[str]) -> list[tuple[int, str]]:
    """Returns the offset of each line with a problem, and the problem."""
    found = []
    in_fence = False
    previous = ""
    for offset, raw in enumerate(lines):
        line = raw if offset else OPENING_QUOTES.sub("", raw)
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or line.lstrip().startswith((">>>", "...")):
            continue
        if (section := SECTION.match(line)) and section["name"] in RENAMED:
            name = section["name"]
            found.append((offset, f"write `{RENAMED[name]}:` instead of `{name}:`"))
        if UNDERLINE.match(line) and (title := TITLE.match(previous)):
            name = title["name"]
            google = NUMPY_SECTIONS.get(name)
            advice = f"`{google}:`" if google else "a Google section"
            found.append((offset - 1, f"NumPy section `{name}`: write it as {advice}"))
        if field := FIELD.match(line):
            section = FIELD_SECTIONS.get(field[1])
            advice = (
                f"write it under `{section}:`"
                if section
                else "describe the attribute in a string below it"
            )
            found.append((offset, f"Sphinx field `{field[0].strip()}`: {advice}"))
        if directive := DIRECTIVE.match(line):
            found.append(
                (
                    offset,
                    f"reST directive `{directive.group(0).strip()}`: write a "
                    "remark, such as `Note:`",
                )
            )
        found.extend(
            (offset, f"Sphinx role `{role.group(0)}`: write the name in backticks")
            for role in ROLE.finditer(line)
        )
        previous = line
    return found


def main() -> int:
    files = [Path(name) for name in sys.argv[1:]] or source_files()
    located = []
    for path in files:
        source = path.read_text()
        lines = source.splitlines()
        for docstring in docstrings(ast.parse(source, filename=str(path))):
            start = docstring.lineno - 1
            end = docstring.end_lineno or docstring.lineno
            for offset, message in problems(lines[start:end]):
                located.append((str(path), start + offset + 1, message))

    annotate = os.environ.get("GITHUB_ACTIONS") == "true"
    for path, line, message in sorted(located):
        if annotate:
            print(f"::error file={path},line={line}::{message}")
        else:
            print(f"{path}:{line}: {message}")

    if located:
        print(f"{len(located)} docstring problems in {len(files)} files.")
        return 1
    print(f"The docstrings of all {len(files)} files are in Google style.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

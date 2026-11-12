"""Run mypy, pyright and pyrefly on the fixtures in `typecheck/`.

A fixture marks every line the type checkers must reject with `# error:`.
Each checker must report an error on exactly those lines, which shows both
that the typed API rejects what it should and that correct use type-checks
without plugins or ignores.
"""

import json
import os
import re
import subprocess
import sys
import tokenize
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

import pytest

PACKAGE_DIR = Path(__file__).parent.parent
FIXTURES = sorted((Path(__file__).parent / "typecheck").glob("*.py"))
MARKER = "# error:"


def expected_lines(fixture: Path) -> set[int]:
    with fixture.open() as source:
        return {
            token.start[0]
            for token in tokenize.generate_tokens(source.readline)
            if token.type == tokenize.COMMENT and token.string.startswith(MARKER)
        }


def run(*command: str) -> str:
    completed = subprocess.run(
        command, cwd=PACKAGE_DIR, capture_output=True, text=True, check=False
    )
    assert completed.stdout, f"{command[2]} wrote no report:\n{completed.stderr}"
    return completed.stdout


def mypy_error_lines(fixture: Path) -> set[int]:
    output = run(
        sys.executable,
        "-m",
        "mypy",
        "--strict",
        "--no-error-summary",
        "--cache-dir",
        os.devnull,
        str(fixture),
    )
    pattern = re.compile(rf"^.*{re.escape(fixture.name)}:(\d+): error:", re.MULTILINE)
    return {int(line) for line in pattern.findall(output)}


class PyrightPosition(TypedDict):
    line: int


class PyrightRange(TypedDict):
    start: PyrightPosition


class PyrightDiagnostic(TypedDict):
    severity: str
    range: PyrightRange


class PyrightReport(TypedDict):
    generalDiagnostics: list[PyrightDiagnostic]


def pyright_error_lines(fixture: Path) -> set[int]:
    output = run(
        sys.executable,
        "-m",
        "pyright",
        "--outputjson",
        "--pythonpath",
        sys.executable,
        str(fixture),
    )
    report: PyrightReport = json.loads(output)
    return {
        diagnostic["range"]["start"]["line"] + 1
        for diagnostic in report["generalDiagnostics"]
        if diagnostic["severity"] == "error"
    }


class PyreflyError(TypedDict):
    severity: str
    line: int


class PyreflyReport(TypedDict):
    errors: list[PyreflyError]


def pyrefly_error_lines(fixture: Path) -> set[int]:
    output = run(
        sys.executable,
        "-m",
        "pyrefly",
        "check",
        str(fixture),
        "--output-format",
        "json",
        "-o",
        "-",
    )
    report: PyreflyReport = json.loads(output)
    return {error["line"] for error in report["errors"] if error["severity"] == "error"}


CHECKERS: dict[str, Callable[[Path], set[int]]] = {
    "mypy": mypy_error_lines,
    "pyright": pyright_error_lines,
    "pyrefly": pyrefly_error_lines,
}


@pytest.mark.parametrize(
    "fixture", FIXTURES, ids=[fixture.stem for fixture in FIXTURES]
)
@pytest.mark.parametrize("checker", CHECKERS)
def test_checker_rejects_exactly_the_marked_lines(fixture: Path, checker: str) -> None:
    assert expected_lines(fixture), f"{fixture.name} marks no line with {MARKER!r}"

    assert CHECKERS[checker](fixture) == expected_lines(fixture)

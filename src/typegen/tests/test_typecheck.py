"""Run mypy, pyright and pyrefly on the goldens and on `typecheck/usage.py`,
which uses the golden of the shared fixture through the typed API.

The goldens must type-check without errors. The usage file marks every line
the type checkers must reject with `# error:`, and each checker must report
an error on exactly those lines.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

PACKAGE_DIR = Path(__file__).parent.parent
TESTS = Path(__file__).parent
USAGE = TESTS / "typecheck" / "usage.py"
GOLDENS = sorted((TESTS / "goldens").glob("*_schema.py"))
MARKER = "# error:"


def expected_lines(source_file: Path) -> set[int]:
    with source_file.open() as source:
        return {
            token.start[0]
            for token in tokenize.generate_tokens(source.readline)
            if token.type == tokenize.COMMENT and token.string.startswith(MARKER)
        }


def run(*command: str) -> str:
    completed = subprocess.run(
        command, cwd=PACKAGE_DIR, capture_output=True, text=True, check=False
    )
    assert completed.stdout or completed.returncode == 0, (
        f"{command[2]} wrote no report:\n{completed.stderr}"
    )
    return completed.stdout


def mypy_errors(source_file: Path) -> set[int]:
    output = run(
        sys.executable,
        "-m",
        "mypy",
        "--strict",
        "--no-error-summary",
        "--cache-dir",
        os.devnull,
        str(source_file.relative_to(PACKAGE_DIR)),
    )
    pattern = re.compile(
        rf"^.*{re.escape(source_file.name)}:(\d+): error:", re.MULTILINE
    )
    return {int(line) for line in pattern.findall(output)}


class PyrightPosition(TypedDict):
    line: int


class PyrightRange(TypedDict):
    start: PyrightPosition


class PyrightDiagnostic(TypedDict):
    file: str
    severity: str
    range: PyrightRange


class PyrightReport(TypedDict):
    generalDiagnostics: list[PyrightDiagnostic]


def pyright_errors(source_file: Path) -> set[int]:
    output = run(
        sys.executable,
        "-m",
        "pyright",
        "--outputjson",
        "--pythonpath",
        sys.executable,
        str(source_file.relative_to(PACKAGE_DIR)),
    )
    report: PyrightReport = json.loads(output)
    return {
        diagnostic["range"]["start"]["line"] + 1
        for diagnostic in report["generalDiagnostics"]
        if diagnostic["severity"] == "error"
        and Path(diagnostic["file"]).name == source_file.name
    }


class PyreflyError(TypedDict):
    path: str
    severity: str
    line: int


class PyreflyReport(TypedDict):
    errors: list[PyreflyError]


def pyrefly_errors(source_file: Path) -> set[int]:
    output = run(
        sys.executable,
        "-m",
        "pyrefly",
        "check",
        str(source_file.relative_to(PACKAGE_DIR)),
        "--output-format",
        "json",
        "-o",
        "-",
    )
    report: PyreflyReport = json.loads(output)
    return {
        error["line"]
        for error in report["errors"]
        if error["severity"] == "error" and Path(error["path"]).name == source_file.name
    }


CHECKERS: dict[str, Callable[[Path], set[int]]] = {
    "mypy": mypy_errors,
    "pyright": pyright_errors,
    "pyrefly": pyrefly_errors,
}


@pytest.mark.parametrize("golden", GOLDENS, ids=[golden.stem for golden in GOLDENS])
@pytest.mark.parametrize("checker", CHECKERS)
def test_golden_type_checks(golden: Path, checker: str) -> None:
    assert CHECKERS[checker](golden) == set()


@pytest.mark.parametrize("checker", CHECKERS)
def test_checker_rejects_exactly_the_marked_lines(checker: str) -> None:
    assert expected_lines(USAGE)

    assert CHECKERS[checker](USAGE) == expected_lines(USAGE)

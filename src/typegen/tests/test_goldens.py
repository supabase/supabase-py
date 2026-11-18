"""The modules generated from the shared `GeneratorMetadata` fixture and the
hostile fixture match the committed goldens, are formatted and lint clean,
and import.

Run with `UPDATE_GOLDENS=1` to rewrite the goldens after an intended change
of the output, then review their diff.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel

from supabase_typegen import __version__, generate, parse_generator_metadata
from supabase_typegen._generator import _BASE_MODEL_ATTRIBUTES

from .hostile_fixture import hostile_metadata

TESTS = Path(__file__).parent
GOLDENS = TESTS / "goldens"
FIXTURES = {
    "supabase_schema": (TESTS / "fixtures" / "generator_metadata.json").read_text(),
    "hostile_schema": json.dumps(hostile_metadata()),
}
VERSION_HEADER = f"supabase_typegen {__version__} from"


def without_version(module: str) -> str:
    """`module` with the version of the generator in its header blanked, so a
    release does not change the goldens."""
    return re.sub(
        r"supabase_typegen \S+ from", "supabase_typegen <version> from", module
    )


@pytest.mark.parametrize("name", FIXTURES)
def test_generated_module_matches_the_golden(name: str) -> None:
    generated = generate(parse_generator_metadata(FIXTURES[name]))
    golden = GOLDENS / f"{name}.py"
    if os.environ.get("UPDATE_GOLDENS"):
        golden.write_text(generated)

    assert VERSION_HEADER in generated
    assert without_version(generated) == without_version(golden.read_text())


def ruff(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ruff", *arguments, "--isolated", str(GOLDENS)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_goldens_are_formatted() -> None:
    result = ruff("format", "--check", "--diff")

    assert result.returncode == 0, result.stdout + result.stderr


def test_goldens_are_lint_clean() -> None:
    result = ruff("check", "--target-version", "py312", "--select", "F,I,UP,B")

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name", FIXTURES)
def test_golden_imports(name: str) -> None:
    importlib.import_module(f"tests.goldens.{name}")


def test_no_field_shadows_an_attribute_of_base_model() -> None:
    public = {name for name in dir(BaseModel) if not name.startswith("_")}

    assert public <= _BASE_MODEL_ATTRIBUTES

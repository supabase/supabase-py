"""`python -m supabase_typegen` reads the document on standard input, writes
the module to standard output, and exits with 64 or 65 when it cannot."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from supabase_typegen import MetadataError, generate, parse_generator_metadata

from .hostile_fixture import hostile_metadata

FIXTURE = (Path(__file__).parent / "fixtures" / "generator_metadata.json").read_text()


def run(document: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "supabase_typegen"],
        input=document,
        capture_output=True,
        text=True,
        check=False,
    )


def test_writes_the_module_to_standard_output() -> None:
    result = run(FIXTURE)

    assert result.returncode == 0, result.stderr
    assert result.stdout == generate(parse_generator_metadata(FIXTURE))
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ("not json", "The document is not JSON"),
        ("[]", "not a JSON object with a version"),
        (json.dumps({**json.loads(FIXTURE), "version": 2}), "version 2"),
        (json.dumps({**json.loads(FIXTURE), "tables": [{"id": "1"}]}), "shape"),
        (json.dumps({**json.loads(FIXTURE), "version": True}), "version true"),
    ],
    ids=["not json", "not an object", "version 2", "wrong shape", "version true"],
)
def test_rejects_a_document_it_cannot_read(document: str, message: str) -> None:
    result = run(document)

    assert result.returncode == 65
    assert message in result.stderr
    assert result.stdout == ""


def test_rejects_a_document_with_nothing_to_generate() -> None:
    empty: dict[str, object] = {
        **hostile_metadata(),
        "columns": [],
        "types": [],
        "rpcFunctions": [],
    }

    result = run(json.dumps(empty))

    assert result.returncode == 65
    assert "nothing to generate" in result.stderr


def test_warns_about_a_document_without_rpc_functions() -> None:
    document = json.loads(FIXTURE)
    del document["rpcFunctions"]

    result = run(json.dumps(document))

    assert result.returncode == 0
    assert '"rpcFunctions"' in result.stderr
    assert "class Functions" not in result.stdout


def test_ignores_fields_it_does_not_read() -> None:
    document = json.loads(FIXTURE)
    document["tables"][0]["added_later"] = {"any": "value"}
    document["added_later"] = []

    assert parse_generator_metadata(json.dumps(document)) == parse_generator_metadata(
        FIXTURE
    )


def test_parse_raises_metadata_error() -> None:
    with pytest.raises(MetadataError, match="version null"):
        parse_generator_metadata('{"version": null}')

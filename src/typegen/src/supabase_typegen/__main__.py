"""`python -m supabase_typegen`: reads a `GeneratorMetadata` document on
standard input and writes the generated module to standard output.

Exits with 64 when standard input is a terminal and with 65 when the
document is not one this version reads, or describes nothing to generate.
"""

from __future__ import annotations

import argparse
import sys
from typing import Final

from ._generator import describes_nothing, generate
from ._metadata import MetadataError, parse_generator_metadata
from .version import __version__

EXIT_USAGE: Final = 64
EXIT_DATA_ERROR: Final = 65


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m supabase_typegen",
        description=(
            "Generates the typed tables and functions of a Supabase database "
            "from the GeneratorMetadata document that `supabase gen types "
            "--lang python` pipes in on standard input, and writes the module "
            "to standard output."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"supabase_typegen {__version__}"
    )
    parser.parse_args(arguments)

    if sys.stdin.isatty():
        return _fail(
            EXIT_USAGE,
            "Expected a GeneratorMetadata document on standard input. Run "
            "`supabase gen types --lang python` to generate types.",
        )
    try:
        metadata = parse_generator_metadata(sys.stdin.buffer.read())
    except MetadataError as error:
        return _fail(EXIT_DATA_ERROR, str(error))
    if describes_nothing(metadata):
        return _fail(
            EXIT_DATA_ERROR,
            "The document describes no tables, views, enums or functions, so "
            "there is nothing to generate.",
        )
    if metadata.rpc_functions is None and metadata.functions:
        sys.stderr.write(
            'The document has no "rpcFunctions" collection, so no function '
            "calls are generated. Upgrade the Supabase CLI to generate them.\n"
        )
    sys.stdout.write(generate(metadata))
    return 0


def _fail(exit_code: int, message: str) -> int:
    sys.stderr.write(f"{message}\n")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

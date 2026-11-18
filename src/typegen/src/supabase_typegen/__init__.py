"""Generates the typed tables and functions of a Supabase database for the
typed API of supabase-py, from the `GeneratorMetadata` document that
`supabase gen types --lang python` pipes in."""

from __future__ import annotations

from ._generator import generate
from ._metadata import GeneratorMetadata, MetadataError, parse_generator_metadata
from .version import __version__

__all__ = [
    "GeneratorMetadata",
    "MetadataError",
    "__version__",
    "generate",
    "parse_generator_metadata",
]

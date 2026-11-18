"""Python source text, written the way the Ruff and Black formatters write it,
so formatting the generated module leaves it as it is."""

from __future__ import annotations

import re
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

LINE_LENGTH: Final = 88
INDENT: Final = "    "

LINE_TERMINATORS: Final = re.compile("\r\n?|[\n\x0b\x0c\x1c-\x1e\x85\u2028\u2029]")
_CONTROL_CHARACTERS: Final = re.compile("[\x00-\x09\x0e-\x1f\x7f-\x9f]")
_ESCAPES: Final = {"\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def string(value: str) -> str:
    """`value` as a Python string literal: in double quotes, unless it holds
    more double quotes than single quotes."""
    quote = "'" if value.count('"') > value.count("'") else '"'
    escaped = "".join(_escaped(character, quote) for character in value)
    return f"{quote}{escaped}{quote}"


def _escaped(character: str, quote: str) -> str:
    if character == quote:
        return f"\\{quote}"
    if character in _ESCAPES:
        return _ESCAPES[character]
    if _CONTROL_CHARACTERS.match(character) or LINE_TERMINATORS.match(character):
        code = ord(character)
        return f"\\x{code:02x}" if code < 0x100 else f"\\u{code:04x}"
    return character


def docstring(*parts: str | None, indent: str) -> list[str]:
    """The lines of a docstring of the paragraphs `parts`, none when every
    part is empty.

    Line terminators other than `\\n` and control characters become spaces,
    every paragraph is dedented, and lines longer than the line length are
    wrapped at spaces.
    """
    paragraphs = [_paragraph(part) for part in parts if part]
    text = "\n\n".join(paragraph for paragraph in paragraphs if paragraph)
    if not text:
        return []
    if text.endswith('"'):
        text = f'{text[:-1]}\\"'
    if "\n" not in text and len(f'{indent}"""{text}"""') <= LINE_LENGTH:
        return [f'{indent}"""{text}"""']
    width = LINE_LENGTH - len(indent)
    lines = [
        wrapped
        for number, line in enumerate(text.split("\n"))
        for wrapped in _wrapped(line, width - 3 if number == 0 else width)
    ]
    return [
        f'{indent}"""{lines[0]}',
        *(f"{indent}{line}" if line else "" for line in lines[1:]),
        f'{indent}"""',
    ]


def escape_docstring(text: str) -> str:
    """`text` with its backslashes escaped, and its triple quotes, which would
    end the docstring."""
    return text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')


def _paragraph(text: str) -> str:
    text = LINE_TERMINATORS.sub("\n", text).replace("\t", " ")
    text = _CONTROL_CHARACTERS.sub(" ", text)
    lines = [line.rstrip() for line in escape_docstring(text).split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    if not lines:
        return ""
    first, rest = lines[0].strip(), textwrap.dedent("\n".join(lines[1:]))
    return f"{first}\n{rest}" if rest else first


def _wrapped(line: str, width: int) -> list[str]:
    """`line` broken at spaces into lines of at most `width` characters
    where it can be, each indented like `line`."""
    if len(line) <= width:
        return [line]
    indent = line[: len(line) - len(line.lstrip())]
    return textwrap.wrap(
        line,
        width,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


@dataclass(frozen=True)
class Group:
    """A bracketed list of items after `head`, such as the arguments of a
    call, `f(a, b)`, or the elements of a tuple, `(a, b)`.

    It is written on one line when that fits, else with each item on a line
    of its own, followed by a comma, which keeps a formatter from joining
    them again. A single item that fits on a line of its own goes there
    without a comma, as a formatter writes it.
    """

    head: str
    items: Sequence[str | Group]
    brackets: str = "()"
    is_tuple: bool = False
    """Whether the group is a tuple, whose single item a comma follows."""
    is_signature: bool = False
    """Whether the group is the parameters of a `def`, whose single
    parameter a comma follows when it goes on a line of its own."""
    explode: bool = False
    """Whether the items always go on lines of their own."""

    def inline(self) -> str:
        opening, closing = self.brackets
        items = [
            item if isinstance(item, str) else item.inline() for item in self.items
        ]
        joined = ", ".join(items)
        if self.is_tuple and len(items) == 1:
            joined += ","
        return f"{self.head}{opening}{joined}{closing}"

    def lines(self, indent: str, trailer: str = "") -> list[str]:
        """The group at `indent`, followed by `trailer`."""
        single = f"{indent}{self.inline()}{trailer}"
        if not self.explode and (not self.items or len(single) <= LINE_LENGTH):
            return [single]
        opening, closing = self.brackets
        inner = indent + INDENT
        first, last = f"{indent}{self.head}{opening}", f"{indent}{closing}{trailer}"
        if len(self.items) == 1 and not (
            self.explode or self.is_tuple or self.is_signature
        ):
            (item,) = self.items
            if isinstance(item, Group):
                return [first, *item.lines(inner), last]
            if not item.startswith("*") and len(inner + item) <= LINE_LENGTH:
                return [first, inner + item, last]
        body = [
            line
            for item in self.items
            for line in (
                [f"{inner}{item},"] if isinstance(item, str) else item.lines(inner, ",")
            )
        ]
        return [first, *body, last]


def from_import(module: str, names: Sequence[str]) -> list[str]:
    """`from module import names`, in parentheses when it does not fit."""
    line = f"from {module} import {', '.join(names)}"
    if len(line) <= LINE_LENGTH:
        return [line]
    return [f"from {module} import (", *(f"{INDENT}{name}," for name in names), ")"]

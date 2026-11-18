"""How database names become Python identifiers."""

from __future__ import annotations

import keyword
import re
import unicodedata
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

_LOWERCASE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def words(name: str) -> list[str]:
    """The words of `name`, split at every character an identifier cannot
    hold, at underscores and at camel humps: `createdAt` and `created_at`
    are both `created` and `At` or `at`. The name is NFKC normalized first,
    as Python normalizes identifiers."""
    found: list[str] = []
    word = ""
    for character in unicodedata.normalize("NFKC", name):
        if character == "_" or not f"a{character}".isidentifier():
            found.append(word)
            word = ""
            continue
        if word and character.isupper() and (word[-1].islower() or word[-1].isdigit()):
            found.append(word)
            word = ""
        word += character
    found.append(word)
    return [word for word in found if word]


def _identifier(text: str, digit_prefix: str) -> str:
    """`text`, with `digit_prefix` before a leading digit or anything else an
    identifier cannot start with."""
    return text if text.isidentifier() else f"{digit_prefix}{text}"


def pascal_case(name: str) -> str:
    """`name` in PascalCase, `author_stats` as `AuthorStats`. A name that
    starts with a digit gets `N`, `2024_sales` as `N2024Sales`."""
    parts = words(name)
    if not parts:
        return "Unnamed"
    return _identifier(
        "".join(word[0].upper() + word[1:].lower() for word in parts), "N"
    )


def snake_case(name: str) -> str:
    """`name` in snake_case, `createdAt` as `created_at`. A name that starts
    with a digit gets `n_`, `2fa` as `n_2fa`."""
    parts = words(name)
    if not parts:
        return "unnamed"
    return _identifier("_".join(word.lower() for word in parts), "n_")


def member_name(name: str) -> str:
    """`name` as an attribute, parameter or method name: snake_case, with a
    trailing underscore for a keyword, `class` as `class_`."""
    identifier = snake_case(name)
    return f"{identifier}_" if keyword.iskeyword(identifier) else identifier


def constant_name(name: str) -> str:
    """`name` as an enum member name, `very happy` as `VERY_HAPPY`."""
    parts = words(name)
    if not parts:
        return "UNNAMED"
    return _identifier("_".join(word.upper() for word in parts), "N_")


def claim(used: set[str], candidate: str) -> str:
    """`candidate`, with trailing underscores until it is no keyword and no
    name in `used` has it, added to `used`."""
    name = candidate
    while name in used or keyword.iskeyword(name):
        name = f"{name}_"
    used.add(name)
    return name


def unique_names(
    names: Iterable[str],
    *,
    reserved: Iterable[str] = (),
    identifier: Callable[[str], str] = member_name,
    aliased: bool = False,
) -> dict[str, str]:
    """The identifier of each of `names`, apart from each other and from
    `reserved`. With `aliased`, a name is also sent as an alias of its
    identifier, so no identifier equals another one of `names`.

    Of several names converting to the same identifier, one in lowercase
    keeps it and every other one gets its own spelling as a suffix, `name`
    and `name_Name` for the columns `name` and `Name`, so adding a column
    never renames one in lowercase. Names are claimed in sorted order, so
    the result does not depend on their order in the database.
    """
    distinct = list(dict.fromkeys(names))
    identifiers = {name: identifier(name) for name in distinct}
    counts = Counter(identifiers.values())
    used = set(reserved)
    claimed: dict[str, str] = {}
    for name in sorted(distinct):
        candidate = (
            f"{identifiers[name]}_{_suffix(name)}"
            if counts[identifiers[name]] > 1 and not _LOWERCASE_NAME.match(name)
            else identifiers[name]
        )
        others = set(distinct) - {name} if aliased else set[str]()
        claimed[name] = claim(used | others, candidate)
        used.add(claimed[name])
    return {name: claimed[name] for name in distinct}


def _suffix(name: str) -> str:
    """`name`, NFKC normalized, with every character an identifier cannot
    hold as `_`."""
    return "".join(
        character if f"a{character}".isidentifier() else "_"
        for character in unicodedata.normalize("NFKC", name)
    )

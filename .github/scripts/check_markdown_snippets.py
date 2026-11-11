"""Type-check the Python snippets of the Markdown files with pyrefly.

Every ```python block in a Markdown file tracked by git, apart from the
changelogs, is checked against the installed workspace packages, so the READMEs
and MIGRATION.md cannot show code that does not match the API.

A block is the body of an async function, so it can use `await` and
`async with`. It imports what it uses, as the code a user copies has to. The
names a file's snippets share, such as the client its README creates once, are
declared in PRELUDES. A block fenced as ```python skip is not checked, for
example v2 code shown as "before" or a fragment that only shows a shape.

Run it from the repository root in an environment with every package and extra
installed:

    uv sync --all-packages --all-extras
    uv run python .github/scripts/check_markdown_snippets.py
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

LANGUAGES = {"python", "py", "python3"}
FENCE = re.compile(r"^(?P<indent>\s*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")

PRELUDES = {
    "MIGRATION.md": [
        "from supabase import Client",
        "from supabase_auth import SyncSupportedStorage",
        "client: Client",
        "url: str",
        "key: str",
        "my_storage: SyncSupportedStorage",
        "account_id: str",
    ],
    "src/supabase/README.md": [
        "from supabase import Client",
        "supabase: Client",
    ],
    "src/auth/README.md": [
        "from supabase_auth import SyncSupabaseAuthClient",
        "client: SyncSupabaseAuthClient",
    ],
    "src/postgrest/README.md": [
        "from postgrest import AsyncPostgrestClient",
        "client: AsyncPostgrestClient",
    ],
    "src/realtime/README.md": [
        "from realtime import RealtimeClient",
        "client: RealtimeClient",
    ],
    "src/storage/README.md": [
        "from storage3 import AsyncStorageClient",
        "storage_client: AsyncStorageClient",
    ],
}

PYREFLY_CONFIG = """\
python-version = "3.12"

[errors]
deprecated = "error"
"""


@dataclass(frozen=True)
class Snippet:
    markdown: str
    first_line: int
    lines: list[str]


def markdown_files() -> list[str]:
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return sorted(
        path
        for path in output.splitlines()
        if Path(path).name != "CHANGELOG.md" and not Path(path).is_symlink()
    )


def python_snippets(markdown: str) -> list[Snippet]:
    snippets: list[Snippet] = []
    lines = Path(markdown).read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        opening = FENCE.match(lines[index])
        index += 1
        if opening is None:
            continue
        fence = opening["fence"]
        indent = len(opening["indent"])
        words = opening["info"].split()
        first_line = index + 1
        body: list[str] = []
        while index < len(lines):
            closing = FENCE.match(lines[index])
            index += 1
            if (
                closing is not None
                and closing["fence"].startswith(fence)
                and not closing["info"].strip()
            ):
                break
            body.append(lines[index - 1][indent:])
        if words and words[0] in LANGUAGES and "skip" not in words[1:]:
            snippets.append(Snippet(markdown, first_line, body))
    return snippets


def module_source(snippet: Snippet) -> tuple[str, int]:
    """Return the module that wraps the snippet and the number of lines before
    the snippet's first line."""
    header = [
        *PRELUDES.get(snippet.markdown, []),
        "",
        "",
        "async def _snippet() -> None:",
    ]
    body = [f"    {line}" if line.strip() else "" for line in snippet.lines]
    if not any(line.strip() for line in body):
        body = ["    pass"]
    return "\n".join([*header, *body, ""]), len(header)


def main() -> int:
    snippets = [
        snippet
        for markdown in markdown_files()
        for snippet in python_snippets(markdown)
    ]
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "pyrefly.toml").write_text(PYREFLY_CONFIG, encoding="utf-8")
        modules: dict[str, tuple[Snippet, int]] = {}
        for number, snippet in enumerate(snippets):
            source, header_lines = module_source(snippet)
            module = root / f"snippet_{number}.py"
            module.write_text(source, encoding="utf-8")
            modules[module.name] = (snippet, header_lines)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyrefly",
                "check",
                "--config",
                str(root / "pyrefly.toml"),
                "--output-format",
                "json",
                *(str(root / name) for name in modules),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        try:
            errors = json.loads(result.stdout)["errors"]
        except (json.JSONDecodeError, KeyError):
            sys.stderr.write(result.stdout + result.stderr)
            return result.returncode or 1

    located: list[tuple[str, int, str]] = []
    for error in errors:
        snippet, header_lines = modules[Path(error["path"]).name]
        line = snippet.first_line + error["line"] - header_lines - 1
        located.append(
            (snippet.markdown, line, f"{error['description']} [{error['name']}]")
        )

    annotate = os.environ.get("GITHUB_ACTIONS") == "true"
    for markdown, line, message in sorted(located):
        if annotate:
            print(f"::error file={markdown},line={line}::{message}")
        else:
            print(f"{markdown}:{line}: {message}")

    if errors:
        print(f"{len(errors)} errors in {len(snippets)} Python snippets.")
        return 1
    print(f"All {len(snippets)} Python snippets type-check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

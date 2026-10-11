"""Keep the documented top-level auth imports public to typed consumers."""

import ast
from pathlib import Path

AUTH_INIT = (
    Path(__file__).resolve().parents[1] / "src" / "supabase_auth" / "__init__.py"
)
PUBLIC_CLASSES = {
    "AsyncGoTrueAdminAPI",
    "AsyncGoTrueClient",
    "AsyncMemoryStorage",
    "AsyncSupportedStorage",
    "SyncGoTrueAdminAPI",
    "SyncGoTrueClient",
    "SyncMemoryStorage",
    "SyncSupportedStorage",
}


def test_top_level_auth_classes_are_explicit_public_reexports() -> None:
    module = ast.parse(AUTH_INIT.read_text())
    exports = {
        alias.name
        for node in module.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.name == alias.asname
    }
    assert PUBLIC_CLASSES <= exports

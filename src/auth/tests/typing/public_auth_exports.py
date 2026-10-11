"""Pyright smoke fixture for the public auth class imports.

Run: npx --yes pyright --pythonpath .venv/bin/python src/auth/tests/typing/public_auth_exports.py
"""

# pyright: reportPrivateImportUsage=error
from supabase_auth import (
    AsyncGoTrueAdminAPI,
    AsyncGoTrueClient,
    AsyncMemoryStorage,
    AsyncSupportedStorage,
    SyncGoTrueAdminAPI,
    SyncGoTrueClient,
    SyncMemoryStorage,
    SyncSupportedStorage,
)

__all__ = [
    "AsyncGoTrueAdminAPI",
    "AsyncGoTrueClient",
    "AsyncMemoryStorage",
    "AsyncSupportedStorage",
    "SyncGoTrueAdminAPI",
    "SyncGoTrueClient",
    "SyncMemoryStorage",
    "SyncSupportedStorage",
]

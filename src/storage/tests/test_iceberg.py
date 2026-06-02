import builtins
import importlib

import pytest
from storage3._iceberg import load_rest_catalog


def _block_pyiceberg_import(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def import_without_pyiceberg(
        name: str,
        globals=None,
        locals=None,
        fromlist=(),
        level: int = 0,
    ) -> object:
        if name.startswith("pyiceberg"):
            raise ImportError("No module named 'pyiceberg'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_without_pyiceberg)


def test_analytics_modules_import_without_pyiceberg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_pyiceberg_import(monkeypatch)

    import storage3._async.analytics as async_analytics
    import storage3._sync.analytics as sync_analytics

    importlib.reload(async_analytics)
    importlib.reload(sync_analytics)


def test_load_rest_catalog_includes_iceberg_extra_install_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_pyiceberg_import(monkeypatch)

    with pytest.raises(ImportError, match=r"pip install storage3\[iceberg\]"):
        load_rest_catalog()

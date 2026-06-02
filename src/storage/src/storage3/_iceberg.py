from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyiceberg.catalog.rest import RestCatalog


def load_rest_catalog() -> "type[RestCatalog]":
    try:
        from pyiceberg.catalog.rest import RestCatalog
    except ImportError as exc:
        raise ImportError(
            "pyiceberg is required for Storage analytics catalog support. "
            "Install it with `pip install storage3[iceberg]`."
        ) from exc

    return RestCatalog

from typing import override

from pyiceberg.catalog import PropertiesUpdateSummary
from pyiceberg.catalog.rest import RestCatalog
from pyiceberg.typedef import EMPTY_DICT, Identifier, Properties


class SupabaseRestCatalog(RestCatalog):
    """pyiceberg's REST catalog without the calls Supabase Storage has no route for.

    Storage's `/v1/config` advertises no `endpoints`, so pyiceberg assumes its
    default set, sends these requests anyway and reports Storage's 404 as a
    missing namespace.
    """

    @override
    def update_namespace_properties(
        self,
        namespace: str | Identifier,
        removals: set[str] | None = None,
        updates: Properties = EMPTY_DICT,
    ) -> PropertiesUpdateSummary:
        """Raise NotImplementedError, since Supabase Storage has no route for it."""
        raise NotImplementedError(
            "Supabase Storage does not support updating namespace properties"
        )

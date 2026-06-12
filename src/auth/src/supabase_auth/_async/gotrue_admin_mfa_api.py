from typing import TYPE_CHECKING

from ..types import (
    AuthMFAAdminDeleteFactorParams,
    AuthMFAAdminDeleteFactorResponse,
    AuthMFAAdminListFactorsParams,
    AuthMFAAdminListFactorsResponse,
)

if TYPE_CHECKING:
    from .gotrue_admin_api import AsyncGoTrueAdminAPI


class AsyncGoTrueAdminMFAAPI:
    """
    Contains the full multi-factor authentication administration API.
    """

    def __init__(self, root: "AsyncGoTrueAdminAPI"):
        self._root = root

    async def list_factors(
        self,
        params: AuthMFAAdminListFactorsParams,
    ) -> AuthMFAAdminListFactorsResponse:
        """
        Lists all factors attached to a user.
        """
        return await self._root._list_factors(params)

    async def delete_factor(
        self,
        params: AuthMFAAdminDeleteFactorParams,
    ) -> AuthMFAAdminDeleteFactorResponse:
        """
        Deletes a factor on a user. This will log the user out of all active
        sessions (if the deleted factor was verified). There's no need to delete
        unverified factors.
        """
        return await self._root._delete_factor(params)

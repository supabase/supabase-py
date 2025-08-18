from typing import Any, Dict, List, Optional

from .channel import RealtimeChannelOptions, SyncRealtimeChannel

NOT_IMPLEMENTED_MESSAGE = "This feature isn't available in the sync client. You can use the realtime feature in the async client only."


class SyncRealtimeClient:
    def __init__(
        self,
        url: str,
        token: str,
        auto_reconnect: bool = True,
        params: Optional[Dict[str, Any]] = None,
        hb_interval: int = 30,
        max_retries: int = 5,
        initial_backoff: float = 1.0,
    ) -> None:
        """
        Initialize a RealtimeClient instance for WebSocket communication.

        :param url: WebSocket URL of the Realtime server. Starts with `ws://` or `wss://`.
                    Also accepts default Supabase URL: `http://` or `https://`.
        :param token: Authentication token for the WebSocket connection.
        :param auto_reconnect: If True, automatically attempt to reconnect on disconnection. Defaults to False.
        :param params: Optional parameters for the connection. Defaults to an empty dictionary.
        :param hb_interval: Interval (in seconds) for sending heartbeat messages to keep the connection alive. Defaults to 30.
        :param max_retries: Maximum number of reconnection attempts. Defaults to 5.
        :param initial_backoff: Initial backoff time (in seconds) for reconnection attempts. Defaults to 1.0.
        """

    def channel(
        self, topic: str, params: Optional[RealtimeChannelOptions] = None
    ) -> SyncRealtimeChannel:
        """
        :param topic: Initializes a channel and creates a two-way association with the socket
        :return: Channel
        """
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    def get_channels(self) -> List[SyncRealtimeChannel]:
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    def remove_channel(self, channel: SyncRealtimeChannel) -> None:
        """
        Unsubscribes and removes a channel from the socket
        :param channel: Channel to remove
        :return: None
        """
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    def remove_all_channels(self) -> None:
        """
        Unsubscribes and removes all channels from the socket
        :return: None
        """
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    def set_auth(self, token: Optional[str]) -> None:
        """
        Set the authentication token for the connection and update all joined channels.

        This method updates the access token for the current connection and sends the new token
        to all joined channels. This is useful for refreshing authentication or changing users.

        Args:
            token (Optional[str]): The new authentication token. Can be None to remove authentication.

        Returns:
            None
        """

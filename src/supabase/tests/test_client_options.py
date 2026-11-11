import dataclasses

import pytest
from supabase_auth import SyncMemoryStorage
from supabase_utils.http.retry import RetryPolicy

from supabase import (
    AuthClientOptions,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    StorageClientOptions,
)
from supabase.types import _ServiceClientOptions

SERVICE_OPTIONS = [
    PostgrestClientOptions,
    AuthClientOptions,
    StorageClientOptions,
    FunctionsClientOptions,
]


class TestClientOptions:
    def test_postgrest_options_default_to_the_public_schema(self) -> None:
        assert PostgrestClientOptions().schema == "public"

    def test_auth_options_defaults(self) -> None:
        options = AuthClientOptions()

        assert options.auto_refresh_token is True
        assert options.session_storage is None
        assert options.flow_type == "pkce"

    def test_dataclasses_replace_keeps_the_other_fields(self) -> None:
        storage = SyncMemoryStorage()
        options = AuthClientOptions(session_storage=storage, request_timeout=10)

        updated = dataclasses.replace(options, flow_type="implicit")

        assert updated.session_storage is storage
        assert updated.request_timeout == 10
        assert updated.flow_type == "implicit"
        assert options.flow_type == "pkce"

    def test_realtime_options_default_to_realtime_defaults(self) -> None:
        assert RealtimeClientOptions() == RealtimeClientOptions(
            heartbeat_interval=25, heartbeat_timeout=5
        )

    def test_realtime_options_accept_fractional_seconds(self) -> None:
        realtime = RealtimeClientOptions(heartbeat_interval=7.5, heartbeat_timeout=2.5)

        assert realtime.heartbeat_interval == 7.5
        assert realtime.heartbeat_timeout == 2.5

    @pytest.mark.parametrize(
        ("heartbeat_interval", "heartbeat_timeout", "message"),
        [
            (0, 5, "heartbeat_interval must be positive"),
            (25, -1, "heartbeat_timeout must be positive"),
            (float("nan"), 5, "heartbeat_interval must be positive"),
        ],
    )
    def test_realtime_options_reject_non_positive_durations(
        self, heartbeat_interval: float, heartbeat_timeout: float, message: str
    ) -> None:
        with pytest.raises(ValueError, match=message):
            RealtimeClientOptions(
                heartbeat_interval=heartbeat_interval,
                heartbeat_timeout=heartbeat_timeout,
            )

    @pytest.mark.parametrize("options_class", SERVICE_OPTIONS)
    def test_service_options_are_frozen(
        self, options_class: type[_ServiceClientOptions]
    ) -> None:
        options = options_class()

        with pytest.raises(dataclasses.FrozenInstanceError):
            options.request_timeout = 10  # pyrefly: ignore[read-only]

    @pytest.mark.parametrize("options_class", SERVICE_OPTIONS)
    def test_service_options_are_keyword_only(
        self, options_class: type[_ServiceClientOptions]
    ) -> None:
        with pytest.raises(TypeError):
            options_class(10)  # pyrefly: ignore[bad-argument-count]

    @pytest.mark.parametrize("options_class", SERVICE_OPTIONS)
    def test_request_timeout_defaults_to_none(
        self, options_class: type[_ServiceClientOptions]
    ) -> None:
        assert options_class().request_timeout is None

    @pytest.mark.parametrize("options_class", SERVICE_OPTIONS)
    def test_retry_defaults_to_none(
        self, options_class: type[_ServiceClientOptions]
    ) -> None:
        assert options_class().retry is None
        policy = RetryPolicy(max_retries=1)
        assert options_class(retry=policy).retry is policy

    @pytest.mark.parametrize("options_class", SERVICE_OPTIONS)
    @pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
    def test_request_timeout_must_be_positive(
        self, options_class: type[_ServiceClientOptions], timeout: float
    ) -> None:
        with pytest.raises(ValueError, match="positive number of seconds"):
            options_class(request_timeout=timeout)

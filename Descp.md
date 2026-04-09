Fix Query Builder Immutability
Description
This Pull Request resolves an issue where query builder objects in postgrest were carrying mutable state. Previously, calling filter methods (such as .in_(), .eq(), etc.) on a base query object resulted in the base query's parameters being mutated. This caused unintended side effects when developers attempted to reuse a base query to fork off multiple distinct queries.

This PR ensures that query builders are immutable and properly isolated so that creating a subsequent query from a base instance correctly instantiates new underlying connection parameters without bleeding state into other queries.

Changes
Improved parameter immutability inside the postgrest request builders so that method chains operate on isolated state copies.
Added explicit test coverage to verify that parameters across different forks of a base query remain independent.
Testing
Comprehensive unit and integration tests have been implemented across both the sync and async client implementations.

Tests Added:
Unit Tests (Builder parameter inspection)

tests/_async/test_request_builder.py -> test_builder_is_immutable
tests/_sync/test_request_builder.py -> test_builder_is_immutable
Integration Tests (Live tests hitting actual endpoints without state mixing)

tests/_async/test_filter_request_builder_integration.py -> test_immutability
tests/_sync/test_filter_request_builder_integration.py -> test_immutability
All tests pass cleanly against the local Docker test infrastructure.
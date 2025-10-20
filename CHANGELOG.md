# Changelog

## [2.22.0](https://github.com/supabase/supabase-py/compare/v2.21.1...v2.22.0) (2025-10-08)


### Features

* **realtime:** add support for broadcast replay configuration ([#1235](https://github.com/supabase/supabase-py/issues/1235)) ([bc2cf08](https://github.com/supabase/supabase-py/commit/bc2cf081b453af1bb322a0612673e1f91c449a44))


### Bug Fixes

* do not mutate httpx client inside storage, postgrest and functions ([#1249](https://github.com/supabase/supabase-py/issues/1249)) ([0543b91](https://github.com/supabase/supabase-py/commit/0543b912b19e37cec26b54fc4fd938a27272d211))

## [2.21.1](https://github.com/supabase/supabase-py/compare/v2.21.0...v2.21.1) (2025-10-03)


### Bug Fixes

* **ci:** fix ci action to reference output of release-please job ([#1242](https://github.com/supabase/supabase-py/issues/1242)) ([db0e152](https://github.com/supabase/supabase-py/commit/db0e1524c4c904a224dff744192e83010e42f8c5))

## [2.21.0](https://github.com/supabase/supabase-py/compare/v2.20.0...v2.21.0) (2025-10-03)


### Features

* **functions:** add region as forceFunctionRegion query parameter ([#1236](https://github.com/supabase/supabase-py/issues/1236)) ([8b4b56c](https://github.com/supabase/supabase-py/commit/8b4b56c1ac1c313d717551304e3684261d00d717))
* **postgrest:** fix postgrest typing ([#1231](https://github.com/supabase/supabase-py/issues/1231)) ([82f60b9](https://github.com/supabase/supabase-py/commit/82f60b9d77a759622e50854ff63aee0f59b95515))
* **realtime:** add presence enabled flag on join payload ([#1229](https://github.com/supabase/supabase-py/issues/1229)) ([6be6c0c](https://github.com/supabase/supabase-py/commit/6be6c0cdbbbd70259c4919f3b3b442358c0778f9))


### Bug Fixes

* unify changelogs ([#1241](https://github.com/supabase/supabase-py/issues/1241)) ([33038ba](https://github.com/supabase/supabase-py/commit/33038ba0e075a62ce4eaf0cfd240d93a10322ad3))

## CHANGELOG

## v.2.20.0 (and lower)

For version 2.20.0 or lower, please consult `src/{package}/CHANGELOG.md` for individual packages changes. Since version 2.21.0, the changelogs for all subpackages have been unified into this single file, for their versions are unified into a single one.

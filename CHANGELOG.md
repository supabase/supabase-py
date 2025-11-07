# Changelog

## [2.24.0](https://github.com/supabase/supabase-py/compare/v2.23.3...v2.24.0) (2025-11-07)


### Features

* add more workspace linting rules ([#1304](https://github.com/supabase/supabase-py/issues/1304)) ([31704ac](https://github.com/supabase/supabase-py/commit/31704aceae8757c08fe314925337202337f6adb1))

## [2.23.3](https://github.com/supabase/supabase-py/compare/v2.23.2...v2.23.3) (2025-11-06)


### Bug Fixes

* mypy supabase ([#1298](https://github.com/supabase/supabase-py/issues/1298)) ([185a149](https://github.com/supabase/supabase-py/commit/185a14951048900a9d9c1b4559fb189cf03c45e6))
* **realtime:** cancel timeout task if a successful response arrives ([#1300](https://github.com/supabase/supabase-py/issues/1300)) ([7e3b81a](https://github.com/supabase/supabase-py/commit/7e3b81a5e2f49583eea405ca4c04ea0f6aa68b51))

## [2.23.2](https://github.com/supabase/supabase-py/compare/v2.23.1...v2.23.2) (2025-11-03)


### Bug Fixes

* **storage:** read _base_url instead of _client.base_url inside signed url creation ([#1295](https://github.com/supabase/supabase-py/issues/1295)) ([a81b074](https://github.com/supabase/supabase-py/commit/a81b0746fef6e06c0f405fd75c6d2a862fce1682))

## [2.23.1](https://github.com/supabase/supabase-py/compare/v2.23.0...v2.23.1) (2025-11-03)


### Bug Fixes

* **auth:** pass ConfigDict into with_config instead of kwargs ([#1292](https://github.com/supabase/supabase-py/issues/1292)) ([78b6d53](https://github.com/supabase/supabase-py/commit/78b6d533f03a1d577fdf23da14911e20c500ea4e))

## [2.23.0](https://github.com/supabase/supabase-py/compare/v2.22.4...v2.23.0) (2025-10-31)


### Features

* **auth:** add OAuth 2.1 client admin endpoints ([#1240](https://github.com/supabase/supabase-py/issues/1240)) ([9ab912b](https://github.com/supabase/supabase-py/commit/9ab912b7b3363af4576e78c76ce8c6f2721cc039))


### Bug Fixes

* **auth:** more linting rules ([#1289](https://github.com/supabase/supabase-py/issues/1289)) ([a892c43](https://github.com/supabase/supabase-py/commit/a892c43701b0809eb4e3face210cc44866a77bed))
* **auth:** return auth_response from exchange_code_for_session instead of response dict ([#1288](https://github.com/supabase/supabase-py/issues/1288)) ([7159116](https://github.com/supabase/supabase-py/commit/715911654ece1c326785e0c62fde5572ba3dcd74))
* **storage:** add upsert option for signed bucket ([#1283](https://github.com/supabase/supabase-py/issues/1283)) ([ce4381a](https://github.com/supabase/supabase-py/commit/ce4381aa5a20c7ea8f748d885a447b52223bc1c9))

## [2.22.4](https://github.com/supabase/supabase-py/compare/v2.22.3...v2.22.4) (2025-10-30)


### Bug Fixes

* **auth:** mypy auth ([#1282](https://github.com/supabase/supabase-py/issues/1282)) ([5c07a73](https://github.com/supabase/supabase-py/commit/5c07a73df1f40c30aa6ae695b57de99220d9f612))

## [2.22.3](https://github.com/supabase/supabase-py/compare/v2.22.2...v2.22.3) (2025-10-28)


### Bug Fixes

* **supabase:** pin dependencies versions ([#1273](https://github.com/supabase/supabase-py/issues/1273)) ([5f65227](https://github.com/supabase/supabase-py/commit/5f65227ddec8fee13693b108f3c7048b4e66fcdf))

## [2.22.2](https://github.com/supabase/supabase-py/compare/v2.22.1...v2.22.2) (2025-10-24)


### Bug Fixes

* **storage:** reconstruct path back instead of returning a tuple ([#1267](https://github.com/supabase/supabase-py/issues/1267)) ([557f1b2](https://github.com/supabase/supabase-py/commit/557f1b2b5e84da52815e7a4abce76034ca2facc0))

## [2.22.1](https://github.com/supabase/supabase-py/compare/v2.22.0...v2.22.1) (2025-10-21)


### Bug Fixes

* evaluate output of release-please correctly ([#1259](https://github.com/supabase/supabase-py/issues/1259)) ([c2a306e](https://github.com/supabase/supabase-py/commit/c2a306e12cb3ed268fd96e90350963e0425b2c8e))
* **postgrest:** fix execute type definition ([#1262](https://github.com/supabase/supabase-py/issues/1262)) ([bc74c0d](https://github.com/supabase/supabase-py/commit/bc74c0decabbd0e25df38bbd2ea43cafd6bd45a4))

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

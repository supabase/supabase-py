# CHANGELOG

## [2.20.0](https://github.com/supabase/supabase-py/compare/v2.19.0...v2.20.0) (2025-09-22)


### Features

* include postgrest in monorepo, finalize monorepo switch ([#1213](https://github.com/supabase/supabase-py/issues/1213)) ([2533ba1](https://github.com/supabase/supabase-py/commit/2533ba1f3b3f97f561ea7240c2c5ef8f9ee29ee0))
* **postgrest:** implement max_affected method ([#1222](https://github.com/supabase/supabase-py/issues/1222)) ([3f75daf](https://github.com/supabase/supabase-py/commit/3f75daf450af8ed9e85fe51a26faf2ed44362273))

## [2.19.0](https://github.com/supabase/supabase-py/compare/v2.18.1...v2.19.0) (2025-09-16)

### Features

* move postgrest from original repository to supabase-py monorepo ([#1213](https://github.com/supabase/supabase-py/pull/1213)). 
* NOTE: the version was bumped to 2.19.0 to have all the package versions in the monorepo be the same, simplifying version constraints. No changes were introduced in the package itself.

## [1.1.1](https://github.com/supabase/postgrest-py/compare/v1.1.0...v1.1.1) (2025-06-23)


### Bug Fixes

* remove jwt key validation to allow new api keys ([#612](https://github.com/supabase/postgrest-py/issues/612)) ([af63482](https://github.com/supabase/postgrest-py/commit/af634822dac7b0a7f12973c01de2750de5723490))

## [1.1.0](https://github.com/supabase/postgrest-py/compare/v1.0.2...v1.1.0) (2025-06-19)


### Features

* allow injection of httpx client ([#591](https://github.com/supabase/postgrest-py/issues/591)) ([635a4ba](https://github.com/supabase/postgrest-py/commit/635a4ba421457ce0967c3efc332ae883b693ef71))


### Bug Fixes

* **pydantic:** model_validate_json causing code break with pydantic v1 ([#609](https://github.com/supabase/postgrest-py/issues/609)) ([587dcc8](https://github.com/supabase/postgrest-py/commit/587dcc82835afd0290c0c83f3c38ff6b8de123a2))
* remove reliance on SyncClient and use Client directly from httpx ([#607](https://github.com/supabase/postgrest-py/issues/607)) ([021f1b6](https://github.com/supabase/postgrest-py/commit/021f1b65fd728116c715b33504df7c37847e6bf2))

## [1.0.2](https://github.com/supabase/postgrest-py/compare/v1.0.1...v1.0.2) (2025-05-21)


### Bug Fixes

* pass params as query params for get/head requests ([#593](https://github.com/supabase/postgrest-py/issues/593)) ([576a5b8](https://github.com/supabase/postgrest-py/commit/576a5b84e19c0a379ef10df24f3325c0519d406e))
* validate JSON input for APIError ([#597](https://github.com/supabase/postgrest-py/issues/597)) ([3c8bdae](https://github.com/supabase/postgrest-py/commit/3c8bdae4135f79dcf903d0bd75f02c097db0b855))

## [1.0.1](https://github.com/supabase/postgrest-py/compare/v1.0.0...v1.0.1) (2025-03-24)


### Bug Fixes

* order using foreign table ([#581](https://github.com/supabase/postgrest-py/issues/581)) ([66477dd](https://github.com/supabase/postgrest-py/commit/66477dd82580544c3ed238cc82080c7ca91ee226))

## [1.0.0](https://github.com/supabase/postgrest-py/compare/v0.19.3...v1.0.0) (2025-03-11)


### ⚠ BREAKING CHANGES

* schema method persisting only on current query ([#575](https://github.com/supabase/postgrest-py/issues/575))

### Bug Fixes

* schema method persisting only on current query ([#575](https://github.com/supabase/postgrest-py/issues/575)) ([b0dd496](https://github.com/supabase/postgrest-py/commit/b0dd496e1793c07ac1081fb59b3c2c8f9feb2984))

## [0.19.3](https://github.com/supabase/postgrest-py/compare/v0.19.2...v0.19.3) (2025-01-24)


### Bug Fixes

* client is sending a body in a GET and HEAD requests ([#562](https://github.com/supabase/postgrest-py/issues/562)) ([6947a53](https://github.com/supabase/postgrest-py/commit/6947a5391b1b2178c4d4a2f13a9592e996f4fa6e))

## [0.19.2](https://github.com/supabase/postgrest-py/compare/v0.19.1...v0.19.2) (2025-01-08)


### Bug Fixes

* _cleaned_columns function now works with python multiline and typings ([#556](https://github.com/supabase/postgrest-py/issues/556)) ([4127576](https://github.com/supabase/postgrest-py/commit/412757633e9319a4e55e00bdc09464aa807db1b9))

## [0.19.1](https://github.com/supabase/postgrest-py/compare/v0.19.0...v0.19.1) (2024-12-30)


### Bug Fixes

* head=True breaking count ([#545](https://github.com/supabase/postgrest-py/issues/545)) ([576987b](https://github.com/supabase/postgrest-py/commit/576987bb2512f6e18360008316377b8d4f2f255b))

## [0.19.0](https://github.com/supabase/postgrest-py/compare/v0.18.0...v0.19.0) (2024-11-22)


### Features

* Check if token is a JWT ([#529](https://github.com/supabase/postgrest-py/issues/529)) ([ed892c4](https://github.com/supabase/postgrest-py/commit/ed892c45346b3f866df0fc0afb997f292c17cbf2))

## [0.18.0](https://github.com/supabase/postgrest-py/compare/v0.17.2...v0.18.0) (2024-10-31)


### Features

* Check if url is an HTTP URL ([#526](https://github.com/supabase/postgrest-py/issues/526)) ([eb7f319](https://github.com/supabase/postgrest-py/commit/eb7f3193b35a8e727511b290c3f5bd7a8a19b9c8))

## [0.17.2](https://github.com/supabase/postgrest-py/compare/v0.17.1...v0.17.2) (2024-10-18)


### Bug Fixes

* bump minimal version of Python to 3.9 ([#522](https://github.com/supabase/postgrest-py/issues/522)) ([11da550](https://github.com/supabase/postgrest-py/commit/11da55084fdd22d0e081aee5867b946337783d73))
* **deps:** install strenum package only with Python 3.10 and older ([#519](https://github.com/supabase/postgrest-py/issues/519)) ([9dfefd0](https://github.com/supabase/postgrest-py/commit/9dfefd0bd2e31775e4ff423654797cf40b1940fe))
* Types to use Option[T] ([#514](https://github.com/supabase/postgrest-py/issues/514)) ([645b677](https://github.com/supabase/postgrest-py/commit/645b677715b8ff338047240bf48dd19dd86b71b4))

## [0.17.1](https://github.com/supabase/postgrest-py/compare/v0.17.0...v0.17.1) (2024-10-02)


### Bug Fixes

* httpx minimum version update ([#512](https://github.com/supabase/postgrest-py/issues/512)) ([5107584](https://github.com/supabase/postgrest-py/commit/5107584f4f49d46bf7df6567109a3edce820c726))

## [0.17.0](https://github.com/supabase/postgrest-py/compare/v0.16.11...v0.17.0) (2024-09-28)


### Features

* Proxy support ([#508](https://github.com/supabase/postgrest-py/issues/508)) ([8629f6f](https://github.com/supabase/postgrest-py/commit/8629f6f8d194d54efb8944f9fe5811ee8190cbf1))
* select all columns by default ([#509](https://github.com/supabase/postgrest-py/issues/509)) ([ffb304f](https://github.com/supabase/postgrest-py/commit/ffb304fbc102ed9efa431e5ccfd8027d4d5c3f54))


### Bug Fixes

* **deps:** bump pydantic from 2.8.2 to 2.9.2 ([#506](https://github.com/supabase/postgrest-py/issues/506)) ([ccf2885](https://github.com/supabase/postgrest-py/commit/ccf28850fe0a0888accc09d2dedf42f7d9242e2e))

## [0.16.11](https://github.com/supabase/postgrest-py/compare/v0.16.10...v0.16.11) (2024-08-22)


### Bug Fixes

* fixed the 'order' method for 'BaseSelectRequestBuilder' ([#495](https://github.com/supabase/postgrest-py/issues/495)) ([97d520e](https://github.com/supabase/postgrest-py/commit/97d520ea339fcf7f706d679d06e8111f0cfdec19))

## [0.16.10](https://github.com/supabase/postgrest-py/compare/v0.16.9...v0.16.10) (2024-08-14)


### Bug Fixes

* revert sanitize_pattern_param in like and ilike ([#481](https://github.com/supabase/postgrest-py/issues/481)) ([18ed416](https://github.com/supabase/postgrest-py/commit/18ed4162cd8eeb6910b87ee7d06bcfba298bca72))

## v0.16.9 (2024-07-16)

### Chore

* chore(deps-dev): bump zipp from 3.18.1 to 3.19.1 (#470) ([`a0bbb4f`](https://github.com/supabase-community/postgrest-py/commit/a0bbb4f0a17a8e1b4aed0c3893517955d9dede63))

* chore(deps-dev): bump python-semantic-release from 9.8.3 to 9.8.5 (#469) ([`61be87c`](https://github.com/supabase-community/postgrest-py/commit/61be87cb8cea268b340c88b97bcbe7ffcbd02945))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.3 to 9.8.5 (#468) ([`7a62fde`](https://github.com/supabase-community/postgrest-py/commit/7a62fdef8ddaf0614149713a0584c2a715cd46f5))

* chore(deps): bump certifi from 2024.2.2 to 2024.7.4 (#467) ([`f7eb0f4`](https://github.com/supabase-community/postgrest-py/commit/f7eb0f43b0284bd5bf40f31492fe317f58429348))

* chore(deps): bump pydantic from 2.7.4 to 2.8.2 (#464) ([`b7c425d`](https://github.com/supabase-community/postgrest-py/commit/b7c425d3786bca9aa802dc72d0787e9e5c2982bf))

* chore(deps-dev): bump python-semantic-release from 9.8.0 to 9.8.3 (#460) ([`ce704b3`](https://github.com/supabase-community/postgrest-py/commit/ce704b32393c8e8be95b66ce9fb1ecf20aed9041))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.1 to 9.8.3 (#459) ([`87995dd`](https://github.com/supabase-community/postgrest-py/commit/87995dda60eb8f69da5cbd82e31cc2318741fb4f))

* chore(deps-dev): bump urllib3 from 2.2.1 to 2.2.2 (#458) ([`27b16fa`](https://github.com/supabase-community/postgrest-py/commit/27b16fabc8676f38acca9ac383cef13ed25806b7))

* chore(deps): bump codecov/codecov-action from 4.4.1 to 4.5.0 (#455) ([`9d6bf07`](https://github.com/supabase-community/postgrest-py/commit/9d6bf07fa6ef10db9c46799d0cdd2f425eda56ae))

* chore(deps): bump pydantic from 2.7.2 to 2.7.4 (#454) ([`6b1b003`](https://github.com/supabase-community/postgrest-py/commit/6b1b0034249230f3c0005eb3a527cc68d7dafda0))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.0 to 9.8.1 (#452) ([`73eb0cf`](https://github.com/supabase-community/postgrest-py/commit/73eb0cf8d91b32fe9a17193a487c9d4799844868))

* chore(deps-dev): bump pytest from 8.2.1 to 8.2.2 (#450) ([`f2f3d4f`](https://github.com/supabase-community/postgrest-py/commit/f2f3d4fa5955b69fbc108627298d18aebca4fe46))

### Fix

* fix: version bump (#471) ([`b509b3a`](https://github.com/supabase-community/postgrest-py/commit/b509b3ad0d69f7ab34d3043350bbc7eb579ab029))

### Unknown

* Fix 830 (#461) ([`ea791f4`](https://github.com/supabase-community/postgrest-py/commit/ea791f44406c57be3096ba44a14271e65cb2df30))

* Enable HTTP2 (#462) ([`0ea293d`](https://github.com/supabase-community/postgrest-py/commit/0ea293d5cd632ec8032ce7bf008cfa05f50b5685))

## v0.16.8 (2024-06-04)

### Chore

* chore(release): bump version to v0.16.8 ([`3871911`](https://github.com/supabase-community/postgrest-py/commit/38719110badf6dd985beb77b5e8a25f413b69abd))

* chore(deps): bump pydantic from 2.7.1 to 2.7.2 (#447) ([`3161d15`](https://github.com/supabase-community/postgrest-py/commit/3161d154cae451449e30c0bb7e7c7b53672d30b0))

### Fix

* fix: add &#34;verify&#34; flag to the creation of client ([`ffe9e28`](https://github.com/supabase-community/postgrest-py/commit/ffe9e28aede84f5e3906c2429bfed945a18ca8f5))

### Unknown

* Follow redirects (#449) ([`bb851bf`](https://github.com/supabase-community/postgrest-py/commit/bb851bfae70d36f40d75a85da58274e75e19eadb))

## v0.16.7 (2024-06-01)

### Chore

* chore(release): bump version to v0.16.7 ([`bc2fc64`](https://github.com/supabase-community/postgrest-py/commit/bc2fc648c709dd2099740d75e5c2b9ade97b57d5))

### Fix

* fix: add get, head and count parameters to the rpc method. (#444) ([`b1d48bc`](https://github.com/supabase-community/postgrest-py/commit/b1d48bca84e707c802448a851608d623c080d72a))

## v0.16.6 (2024-06-01)

### Chore

* chore(release): bump version to v0.16.6 ([`465232a`](https://github.com/supabase-community/postgrest-py/commit/465232aef70545484ca6c35ceacfaa3aa976b391))

### Fix

* fix: convert None to a string null for the is method (#446) ([`9970ac3`](https://github.com/supabase-community/postgrest-py/commit/9970ac379f06ebb56d5532ab6730b9330fcccc40))

## v0.16.5 (2024-06-01)

### Chore

* chore(release): bump version to v0.16.5 ([`901108a`](https://github.com/supabase-community/postgrest-py/commit/901108a11dcba0549d63efa96b40a837b58c54ec))

* chore(deps-dev): bump python-semantic-release from 9.7.3 to 9.8.0 (#443) ([`d8ce53a`](https://github.com/supabase-community/postgrest-py/commit/d8ce53a2b3b66fa42af3c28594749029b0f70b2e))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.7.3 to 9.8.0 (#442) ([`42a4a32`](https://github.com/supabase-community/postgrest-py/commit/42a4a3226ee129ed8e51fe58347266181d8165bb))

* chore(deps-dev): bump requests from 2.31.0 to 2.32.0 (#440) ([`9fe1070`](https://github.com/supabase-community/postgrest-py/commit/9fe1070e0b446d8f1a0d5c4b312b5d4c8659926c))

* chore: code style fixes (#425) ([`11076da`](https://github.com/supabase-community/postgrest-py/commit/11076dae41d3bc6172799245f491f8a1e50dc9ca))

* chore(deps-dev): bump jinja2 from 3.1.3 to 3.1.4 (#428) ([`d786fc7`](https://github.com/supabase-community/postgrest-py/commit/d786fc7667e3074dc29a0513eccbc18edf850358))

* chore(deps): bump codecov/codecov-action from 4.3.0 to 4.4.1 (#437) ([`fe50d11`](https://github.com/supabase-community/postgrest-py/commit/fe50d111cd7ad4831fc9772113fff85cdc926bd9))

* chore(deps-dev): bump pytest-asyncio from 0.23.6 to 0.23.7 (#439) ([`f41e7af`](https://github.com/supabase-community/postgrest-py/commit/f41e7afd112b9f76c6f0fb3ec02676333c9d7513))

* chore(deps-dev): bump pytest from 8.1.1 to 8.2.1 (#438) ([`9722855`](https://github.com/supabase-community/postgrest-py/commit/9722855535dc1d85506b499b07c7adad060b12ae))

* chore(deps-dev): bump python-semantic-release from 9.7.1 to 9.7.3 (#434) ([`7cc3c38`](https://github.com/supabase-community/postgrest-py/commit/7cc3c380628e719c055879df63cec48bc31f86a9))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.5.0 to 9.7.3 (#436) ([`6115096`](https://github.com/supabase-community/postgrest-py/commit/6115096e9371be0fd0b7a4ff5b7a32d927f17813))

* chore(deps-dev): bump black from 24.3.0 to 24.4.2 (#416) ([`5dceb98`](https://github.com/supabase-community/postgrest-py/commit/5dceb982315773d72a5e46de6429157a6b1af3d8))

* chore(deps-dev): bump python-semantic-release from 9.5.0 to 9.7.1 (#430)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`56f7f5d`](https://github.com/supabase-community/postgrest-py/commit/56f7f5dea3649a9eb5e9e25beba562d81d32e562))

* chore(deps): bump furo from 2024.1.29 to 2024.5.6 (#431)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`4692500`](https://github.com/supabase-community/postgrest-py/commit/46925008794dd12de8823cc94116e99802d0a5a6))

### Fix

* fix: update overlaps to work with timestamp range (#445) ([`b39f332`](https://github.com/supabase-community/postgrest-py/commit/b39f3326566c998dc517089a7053fb4d5d44d128))

### Unknown

* Update .pre-commit-config.yaml (#424) ([`82a9e9b`](https://github.com/supabase-community/postgrest-py/commit/82a9e9ba6e503a1797ea565b84003de4f944de7d))

* Add stale bot (#422) ([`44f3672`](https://github.com/supabase-community/postgrest-py/commit/44f36724b6366aabee0177f795f8fe386df3d7e5))

## v0.16.4 (2024-04-29)

### Chore

* chore(release): bump version to v0.16.4 ([`b2bd803`](https://github.com/supabase-community/postgrest-py/commit/b2bd8032c17a32f3094a03b5d9414f4d5767d19e))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.4.1 to 9.5.0 (#414) ([`059aceb`](https://github.com/supabase-community/postgrest-py/commit/059aceb78f1efbed03014ddbc328bed65563d387))

* chore(deps-dev): bump python-semantic-release from 9.4.1 to 9.5.0 (#413) ([`5444cda`](https://github.com/supabase-community/postgrest-py/commit/5444cdaf76103ca3ab97b0603c033967c6432158))

* chore(deps): bump pydantic from 2.7.0 to 2.7.1 (#412) ([`0e08ecb`](https://github.com/supabase-community/postgrest-py/commit/0e08ecbc214515e9bccdbcbaf5f98599963666be))

* chore(deps): bump pydantic from 2.6.4 to 2.7.0 (#408) ([`4b3a664`](https://github.com/supabase-community/postgrest-py/commit/4b3a664abf2c35b7a08919ae7bf71c90f3fa9ef8))

* chore(deps): bump idna from 3.6 to 3.7 (#407) ([`9046f41`](https://github.com/supabase-community/postgrest-py/commit/9046f417b2c6dec2a450c538d0dd0193230c25ed))

* chore(deps): bump codecov/codecov-action from 4.1.0 to 4.3.0 (#406) ([`a496a78`](https://github.com/supabase-community/postgrest-py/commit/a496a78c90a4bd7981109d6ae67a0a11a1850e4c))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.3.1 to 9.4.1 (#405) ([`e153778`](https://github.com/supabase-community/postgrest-py/commit/e153778b0a5acfe7864e5cbfa8b69cd87dab99ee))

* chore(deps-dev): bump python-semantic-release from 9.3.0 to 9.4.1 (#404) ([`364a9a9`](https://github.com/supabase-community/postgrest-py/commit/364a9a951d0a52174a9e263a24f7032821c46f44))

* chore(deps-dev): bump pytest-cov from 4.1.0 to 5.0.0 (#394) ([`64e8819`](https://github.com/supabase-community/postgrest-py/commit/64e88199bc8abdab884c76618e6197f1cd4fe748))

### Fix

* fix: increase timeout (#417) ([`a387471`](https://github.com/supabase-community/postgrest-py/commit/a3874712ab1440915a7ccd3788fe11289febcc00))

## v0.16.3 (2024-04-13)

### Chore

* chore(release): bump version to v0.16.3 ([`980d262`](https://github.com/supabase-community/postgrest-py/commit/980d2624fda078544ff0a9da1001cb3e00dca483))

* chore(deps): bump codecov/codecov-action from 4.1.0 to 4.1.1 (#396) ([`dcadb43`](https://github.com/supabase-community/postgrest-py/commit/dcadb436d48445fdea1d7870b483ea77bda0927a))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.3.0 to 9.3.1 (#393) ([`eabf30c`](https://github.com/supabase-community/postgrest-py/commit/eabf30c390b259c285eeab28c6a6d1e64bb0ea9f))

* chore(deps): bump python-semantic-release/python-semantic-release from 8.0.0 to 9.3.0 (#390)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`47e262e`](https://github.com/supabase-community/postgrest-py/commit/47e262e8154d1989f327b4c944bf350c5657f0b5))

### Fix

* fix: upsert and insert with default_to_null boolean argument (#398) ([`ae5f80a`](https://github.com/supabase-community/postgrest-py/commit/ae5f80a7dc350afc69808f36f62b732739685739))

### Unknown

* Revert &#34;chore(deps): bump codecov/codecov-action from 4.1.0 to 4.1.1&#34; (#397) ([`b4c740d`](https://github.com/supabase-community/postgrest-py/commit/b4c740d3e6cbe1709b18cdd56d89b8e592785ec7))

## v0.16.2 (2024-03-23)

### Chore

* chore(release): bump version to v0.16.2 ([`90d6906`](https://github.com/supabase-community/postgrest-py/commit/90d690672324c00628adfcaa95350f0690666efc))

* chore(deps-dev): bump black from 23.12.1 to 24.3.0 (#385)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`b10e114`](https://github.com/supabase-community/postgrest-py/commit/b10e1146fe87087315c038309b531ef87d7c5ce1))

* chore(deps): bump pydantic from 2.6.2 to 2.6.4 (#384)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9bd4fb1`](https://github.com/supabase-community/postgrest-py/commit/9bd4fb1d6eec03c0c006eb06ef37fb62e83f9e7c))

* chore(deps): bump furo from 2023.9.10 to 2024.1.29 (#383)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`7eec5ce`](https://github.com/supabase-community/postgrest-py/commit/7eec5ced4c33fa604ab09aa1d64a708e52928a5d))

* chore(deps-dev): bump pytest-asyncio from 0.23.5 to 0.23.5.post1 (#382)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ae09035`](https://github.com/supabase-community/postgrest-py/commit/ae090355aa07065e4ee37c4a39dd1b853b0de63d))

### Fix

* fix: update dependencies and tests (#392) ([`d04d76c`](https://github.com/supabase-community/postgrest-py/commit/d04d76caa914afd5efffa9efd6481a38429742e8))

## v0.16.1 (2024-02-29)

### Chore

* chore(release): bump version to v0.16.1 ([`6d8b32a`](https://github.com/supabase-community/postgrest-py/commit/6d8b32a5210846081cb4d6f2f54dd8e8100129c4))

* chore(deps): bump pydantic from 2.5.3 to 2.6.2 (#374)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`b858685`](https://github.com/supabase-community/postgrest-py/commit/b858685c52291aba780d2db3626c6d618b826d1a))

### Fix

* fix: explain functionality to show results (#371)

Co-authored-by: Rodrigo Mansueli Nunes &lt;rodrigo@mansueli.com&gt; ([`3e0ea2e`](https://github.com/supabase-community/postgrest-py/commit/3e0ea2ef54fb2b50d4e5cb5619abc1c96471836f))

### Test

* test: remove skip from rpc with range test (#376) ([`a3fc560`](https://github.com/supabase-community/postgrest-py/commit/a3fc56044ed26eefdde3dea18353ad7cc2f03b2c))

### Unknown

* Bump action versions (#377) ([`602d66e`](https://github.com/supabase-community/postgrest-py/commit/602d66e6e40402281aa388a3bb9e8ddef6d5c718))

## v0.16.0 (2024-02-27)

### Chore

* chore(release): bump version to v0.16.0 ([`3dc51d4`](https://github.com/supabase-community/postgrest-py/commit/3dc51d4859721c99a8c7c69d4fe144ff37d9e16f))

### Feature

* feat: Add RPC request builder class for additional filters (#372) ([`0002e8f`](https://github.com/supabase-community/postgrest-py/commit/0002e8f7ec32b6787b44996079b4c2f43fc43717))

## v0.15.1 (2024-02-27)

### Chore

* chore(release): bump version to v0.15.1 ([`6d55e49`](https://github.com/supabase-community/postgrest-py/commit/6d55e49b461fd0b52e9267a6b1e47038756bfd7f))

### Fix

* fix: update range to use query parameters instead of headers (#375) ([`eae612c`](https://github.com/supabase-community/postgrest-py/commit/eae612ce0548b392d574e9afc12c11f73e54cf8f))

## v0.15.0 (2024-01-15)

### Chore

* chore(release): bump version to v0.15.0 ([`0faa8c3`](https://github.com/supabase-community/postgrest-py/commit/0faa8c3f37cb1f360f65dcef075479c297029844))

* chore(deps-dev): bump pytest-asyncio from 0.18.3 to 0.23.3 (#344)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e9f49a5`](https://github.com/supabase-community/postgrest-py/commit/e9f49a57b13c7f8f53ca2a5fc2d41377e980959b))

### Feature

* feat: add like_any_of, like_all_of, ilike_any_of and ilike_all_of filters (#358) ([`d4e3f57`](https://github.com/supabase-community/postgrest-py/commit/d4e3f57aafd75138272b558f4ce507b2bef70e37))

## v0.14.0 (2024-01-15)

### Chore

* chore(release): bump version to v0.14.0 ([`9f8a2a5`](https://github.com/supabase-community/postgrest-py/commit/9f8a2a54319795523efe5d41f5dcd327ba465a69))

* chore: add alias for range methods (#350) ([`83ca3cd`](https://github.com/supabase-community/postgrest-py/commit/83ca3cd0a791513ed4c1fe45d3ed125a3c3d96e3))

### Feature

* feat: add or filter along with tests (#355)

Co-authored-by: sourcery-ai[bot] &lt;58596630+sourcery-ai[bot]@users.noreply.github.com&gt; ([`e302009`](https://github.com/supabase-community/postgrest-py/commit/e302009ac93ba3703a7b5f9e394e1d867704cea7))

### Unknown

* update ci for publishing package (#349) ([`496d95a`](https://github.com/supabase-community/postgrest-py/commit/496d95a227c8412a064a8f31a365e758d8c7d844))

## v0.13.2 (2024-01-11)

### Chore

* chore(release): bump version to v0.13.2 ([`bef118f`](https://github.com/supabase-community/postgrest-py/commit/bef118f164fe31b2f372436339807867a7d4c648))

### Fix

* fix: add missing RPCFilterRequestBuilder and MaybeSingleRequestBuilder exports ([`3ab20e4`](https://github.com/supabase-community/postgrest-py/commit/3ab20e4682a16b31b414fa7e5f2e1a565828f60e))

## v0.13.1 (2024-01-04)

### Chore

* chore(release): bump version to v0.13.1 ([`9b1b44e`](https://github.com/supabase-community/postgrest-py/commit/9b1b44e31fc0ed980f6fa335f03b4156b8b113de))

* chore(deps): bump pydantic from 2.4.2 to 2.5.0 (#332)

Bumps [pydantic](https://github.com/pydantic/pydantic) from 2.4.2 to 2.5.0.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v2.4.2...v2.5.0)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`fb0b8c2`](https://github.com/supabase-community/postgrest-py/commit/fb0b8c2590a3d53f67c84e9f52917768a13d7153))

* chore(deps-dev): bump pytest from 7.4.2 to 7.4.3 (#329)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.4.2 to 7.4.3.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.4.2...7.4.3)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`85826ea`](https://github.com/supabase-community/postgrest-py/commit/85826ea3473cc6e4c7ebe3a0b8068b89ae917101))

* chore(deps): bump pydantic from 2.1.1 to 2.4.2 (#314)

Bumps [pydantic](https://github.com/pydantic/pydantic) from 2.1.1 to 2.4.2.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v2.1.1...v2.4.2)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9579d03`](https://github.com/supabase-community/postgrest-py/commit/9579d03480e2f28ad670d205e4e89ab2a768c4c6))

* chore(deps-dev): bump gitpython from 3.1.35 to 3.1.37 (#320)

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.35 to 3.1.37.
- [Release notes](https://github.com/gitpython-developers/GitPython/releases)
- [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES)
- [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.35...3.1.37)

---
updated-dependencies:
- dependency-name: gitpython
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`0e6e8b0`](https://github.com/supabase-community/postgrest-py/commit/0e6e8b0f0be6564a5a0a7fd4b86cd107c1f439d2))

* chore(deps-dev): bump urllib3 from 2.0.4 to 2.0.7 (#324)

Bumps [urllib3](https://github.com/urllib3/urllib3) from 2.0.4 to 2.0.7.
- [Release notes](https://github.com/urllib3/urllib3/releases)
- [Changelog](https://github.com/urllib3/urllib3/blob/main/CHANGES.rst)
- [Commits](https://github.com/urllib3/urllib3/compare/2.0.4...2.0.7)

---
updated-dependencies:
- dependency-name: urllib3
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ffa552f`](https://github.com/supabase-community/postgrest-py/commit/ffa552fa18a87c21de5b1b4ec7b54f27e99179d5))

* chore(deps-dev): bump python-semantic-release from 8.1.1 to 8.3.0 (#327)

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 8.1.1 to 8.3.0.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v8.1.1...v8.3.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3f2eebb`](https://github.com/supabase-community/postgrest-py/commit/3f2eebb729d65648b81676be4932a1635aaba70a))

* chore(deps-dev): bump black from 23.10.0 to 23.10.1 (#328)

Bumps [black](https://github.com/psf/black) from 23.10.0 to 23.10.1.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/23.10.0...23.10.1)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`32d3abf`](https://github.com/supabase-community/postgrest-py/commit/32d3abfe34f3b895c9b88cc3b423101535cafe24))

### Fix

* fix: update httpx and other dev dependencies ([`bfc6714`](https://github.com/supabase-community/postgrest-py/commit/bfc6714dc05a21374b67b0c84c0029e1143b3a99))

## v0.13.0 (2023-10-22)

### Chore

* chore(release): bump version to v0.13.0 ([`f7f786b`](https://github.com/supabase-community/postgrest-py/commit/f7f786bd19194c3878adbe899213dceb67ffb29d))

* chore(deps-dev): bump black from 23.9.1 to 23.10.0 (#325)

Bumps [black](https://github.com/psf/black) from 23.9.1 to 23.10.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/23.9.1...23.10.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`193c8df`](https://github.com/supabase-community/postgrest-py/commit/193c8df842616c12e897aceb342df9db64c55264))

### Feature

* feat: add offset (#326)

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`7cd6751`](https://github.com/supabase-community/postgrest-py/commit/7cd67512705853f6e4488cfa34491ae97c526041))

## v0.12.1 (2023-10-17)

### Chore

* chore(release): bump version to v0.12.1 ([`e2d2f0e`](https://github.com/supabase-community/postgrest-py/commit/e2d2f0eef49d0309d8af5091712a2ea10c3d51e8))

* chore(deps-dev): bump pre-commit from 3.3.3 to 3.5.0 (#323)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 3.3.3 to 3.5.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v3.3.3...v3.5.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`1209139`](https://github.com/supabase-community/postgrest-py/commit/120913914ee958087c1f65d9292a23408fbe6227))

* chore: add python 3.12 to CI (#319)

* chore: add python 3.12 to CI

* chore: update autoflake hook

* chore: add myself to codeowners

* fix: make doc requirements optional ([`d1ee0bb`](https://github.com/supabase-community/postgrest-py/commit/d1ee0bbaf41f357322a31987cbdb016aee372b25))

### Fix

* fix: make rpc function sync (#322) ([`04f4980`](https://github.com/supabase-community/postgrest-py/commit/04f49804db614427b2545414b934b93baef91a71))

## v0.12.0 (2023-10-06)

### Chore

* chore(release): bump version to v0.12.0 ([`89b370f`](https://github.com/supabase-community/postgrest-py/commit/89b370fb1089a06d7d85dee6da37defbbaaf5a02))

### Feature

* feat: add csv() modifier (#316)

* fix: cast to correct type

* feat: add csv() modifier

* chore: export SingleRequestBuilder

* chore: write tests for csv()

* &#39;Refactored by Sourcery&#39; (#317)

Co-authored-by: Sourcery AI &lt;&gt;

---------

Co-authored-by: sourcery-ai[bot] &lt;58596630+sourcery-ai[bot]@users.noreply.github.com&gt; ([`4f6e9d9`](https://github.com/supabase-community/postgrest-py/commit/4f6e9d9a8f340dd25d47f2399218873c7b9abc01))

## v0.11.0 (2023-09-28)

### Chore

* chore(release): bump version to v0.11.0 ([`5ae0f99`](https://github.com/supabase-community/postgrest-py/commit/5ae0f99732ee416cf1a3b59ebe28937344fefd1a))

* chore(deps-dev): bump python-semantic-release from 7.34.6 to 8.1.1 (#311)

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 7.34.6 to 8.1.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v7.34.6...v8.1.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`d5a32d4`](https://github.com/supabase-community/postgrest-py/commit/d5a32d42f768d096d16d2d834775889af373dd79))

* chore(deps-dev): bump pytest from 7.4.0 to 7.4.2 (#304)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.4.0 to 7.4.2.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.4.0...7.4.2)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`488721a`](https://github.com/supabase-community/postgrest-py/commit/488721a33435aab79d8527e35ccbb9740c470395))

* chore(deps-dev): bump black from 23.7.0 to 23.9.1 (#303)

Bumps [black](https://github.com/psf/black) from 23.7.0 to 23.9.1.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/23.7.0...23.9.1)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9e99b11`](https://github.com/supabase-community/postgrest-py/commit/9e99b110984599343599e737d53906db14b46edd))

* chore(deps): bump furo from 2023.7.26 to 2023.9.10 (#298)

Bumps [furo](https://github.com/pradyunsg/furo) from 2023.7.26 to 2023.9.10.
- [Release notes](https://github.com/pradyunsg/furo/releases)
- [Changelog](https://github.com/pradyunsg/furo/blob/main/docs/changelog.md)
- [Commits](https://github.com/pradyunsg/furo/compare/2023.07.26...2023.09.10)

---
updated-dependencies:
- dependency-name: furo
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`39aa5c9`](https://github.com/supabase-community/postgrest-py/commit/39aa5c94afa39326406297998040725d2601f0a4))

* chore(deps): bump sphinx from 7.0.1 to 7.1.2 (#281)

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 7.0.1 to 7.1.2.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v7.0.1...v7.1.2)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c7a77a1`](https://github.com/supabase-community/postgrest-py/commit/c7a77a1a78004bc30ae54a1286245edc31a89e64))

* chore(deps-dev): bump gitpython from 3.1.34 to 3.1.35 (#296)

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.34 to 3.1.35.
- [Release notes](https://github.com/gitpython-developers/GitPython/releases)
- [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES)
- [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.34...3.1.35)

---
updated-dependencies:
- dependency-name: gitpython
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`324fa53`](https://github.com/supabase-community/postgrest-py/commit/324fa53cbde8616b4fcfdb50a6768437c00a321b))

* chore(deps-dev): bump gitpython from 3.1.32 to 3.1.34 (#295)

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.32 to 3.1.34.
- [Release notes](https://github.com/gitpython-developers/GitPython/releases)
- [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES)
- [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.32...3.1.34)

---
updated-dependencies:
- dependency-name: gitpython
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ed6928a`](https://github.com/supabase-community/postgrest-py/commit/ed6928afb3b200e82cb55d36fedfe916da5e2eef))

### Feature

* feat: generic query builders (#309)

* feat: make all query builders generic

* feat: return generic request builders from client methods

* chore: use typing.List instead of builtin

* chore: use typing.List

* fix: correct type of APIResponse.data

* feat: make RPCFilterRequestBuilder

This makes sure the return types of rpc() and other
query methods are correct.
See https://gist.github.com/anand2312/93d3abf401335fd3310d9e30112303bf
for an explanation.

* chore: use typing.List

* feat: make get_origin_and_cast

This fixes the type-checker error raised while accessing
RequestBuilder[T].__origin__

* fix: use typing.List ([`ba9ad8d`](https://github.com/supabase-community/postgrest-py/commit/ba9ad8dc92778a31a25fa14218545f82b1885329))

* feat: update semver, add CODEOWNERS (#299)

* Update ci.yml

* chore: add CODEOWNERS

---------

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`18b5838`](https://github.com/supabase-community/postgrest-py/commit/18b58383e4c5651a0e1b773af1d4d1ee04050505))

### Fix

* fix: pre-commit hook to stop checks on md files (#315)

* fix: pre-commit hook to stop checks on md files

* fix(ci): using correct token to publish a release

* fix: correct semantic release variable names ([`e8fbe61`](https://github.com/supabase-community/postgrest-py/commit/e8fbe61b0c2904f46461171fc35cf8cab3ea771b))

* fix: update upsert type (#307)

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`3329234`](https://github.com/supabase-community/postgrest-py/commit/332923432c20a5898f6f27702a59abb6144676cb))

* fix: add semver (#297)

* fix: add semver

* fix: add environ and perms

---------

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`166fa7c`](https://github.com/supabase-community/postgrest-py/commit/166fa7c24004e769eb36283682be2889a695c539))

* fix: maybe_single with no matching rows returns None (#289) ([`a5efce6`](https://github.com/supabase-community/postgrest-py/commit/a5efce6acd932b6a9922ccf4882ea79606f97175))

### Unknown

* re-enable pydantic 1.9 (#283) ([`8d1f249`](https://github.com/supabase-community/postgrest-py/commit/8d1f249c4ed89e6ed6843647177c6ae4d3edf601))

## v0.10.8 (2023-08-04)

### Chore

* chore: bump httpx to 0.24.1 (#277)

* fix: use new httpx parameter encoding in tests

httpx changed how it formats query parameters in 0.24.0 - see here
https://github.com/encode/httpx/blob/master/CHANGELOG.md#0240-6th-april-2023

* chore: bump version

* &#39;Refactored by Sourcery&#39; (#280)

Co-authored-by: Sourcery AI &lt;&gt;

---------

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt;
Co-authored-by: sourcery-ai[bot] &lt;58596630+sourcery-ai[bot]@users.noreply.github.com&gt; ([`561548e`](https://github.com/supabase-community/postgrest-py/commit/561548ea4c17d89cef1777d2843176efe6ead614))

## v0.10.7 (2023-08-04)

### Chore

* chore: bump postgrest version (#279)

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`abb074f`](https://github.com/supabase-community/postgrest-py/commit/abb074f4a2ca1239ff4ab17c632a648e01fada84))

* chore(deps): bump sphinx from 7.0.1 to 7.1.2 (#275)

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 7.0.1 to 7.1.2.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v7.0.1...v7.1.2)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`398610e`](https://github.com/supabase-community/postgrest-py/commit/398610ec55d1d0ccd82a922ad5ed177361fcd189))

* chore(deps): bump strenum from 0.4.10 to 0.4.15 (#272)

Bumps [strenum](https://github.com/irgeek/StrEnum) from 0.4.10 to 0.4.15.
- [Release notes](https://github.com/irgeek/StrEnum/releases)
- [Commits](https://github.com/irgeek/StrEnum/compare/v0.4.10...v0.4.15)

---
updated-dependencies:
- dependency-name: strenum
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c20a7d9`](https://github.com/supabase-community/postgrest-py/commit/c20a7d95bdb1fff3e590fa65ca23172c7dae4405))

* chore(deps): bump sphinx from 4.3.2 to 7.0.1 (#263)

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 4.3.2 to 7.0.1.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v4.3.2...v7.0.1)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3bda953`](https://github.com/supabase-community/postgrest-py/commit/3bda9534a630600538f45ddc34d9c7eebdb19767))

* chore(deps): bump pydantic from 1.10.9 to 2.0.3 (#270)

Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.9 to 2.0.3.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v1.10.9...v2.0.3)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`043cf2f`](https://github.com/supabase-community/postgrest-py/commit/043cf2fa7248ca4e9ddeb5e2a1a615a154ecb6cd))

* chore(deps-dev): bump pre-commit from 3.2.0 to 3.3.3 (#255)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 3.2.0 to 3.3.3.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v3.2.0...v3.3.3)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c56878f`](https://github.com/supabase-community/postgrest-py/commit/c56878f37b3be9638b403b6d35a52514c6a81f63))

* chore(deps-dev): bump black from 23.1.0 to 23.3.0 (#256)

Bumps [black](https://github.com/psf/black) from 23.1.0 to 23.3.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/23.1.0...23.3.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3fde0fd`](https://github.com/supabase-community/postgrest-py/commit/3fde0fd58b66c02f6a9e6c44ccfc65e40806c2ca))

* chore(deps): bump sphinx from 4.3.2 to 7.0.1 (#253)

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 4.3.2 to 7.0.1.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v4.3.2...v7.0.1)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`7e18b17`](https://github.com/supabase-community/postgrest-py/commit/7e18b17430564f1fa974803cba8cc424cf96fad1))

* chore(deps): bump strenum from 0.4.9 to 0.4.10 (#234)

Bumps [strenum](https://github.com/irgeek/StrEnum) from 0.4.9 to 0.4.10.
- [Release notes](https://github.com/irgeek/StrEnum/releases)
- [Commits](https://github.com/irgeek/StrEnum/compare/v0.4.9...v0.4.10)

---
updated-dependencies:
- dependency-name: strenum
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`1a8a2ad`](https://github.com/supabase-community/postgrest-py/commit/1a8a2ade080d2a107e7edfef01b49b73fb5e2e16))

* chore(deps): bump cryptography from 39.0.1 to 41.0.0 (#246)

Bumps [cryptography](https://github.com/pyca/cryptography) from 39.0.1 to 41.0.0.
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/39.0.1...41.0.0)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`779d827`](https://github.com/supabase-community/postgrest-py/commit/779d827494568fa9764f20189851cb4f0b492a97))

* chore(deps-dev): bump pytest from 7.2.2 to 7.3.2 (#252)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.2.2 to 7.3.2.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.2.2...7.3.2)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`120786e`](https://github.com/supabase-community/postgrest-py/commit/120786e8d4905ae6ae3d153a11ea8d72ea79352a))

* chore(deps): bump furo from 2022.12.7 to 2023.5.20 (#243)

Bumps [furo](https://github.com/pradyunsg/furo) from 2022.12.7 to 2023.5.20.
- [Release notes](https://github.com/pradyunsg/furo/releases)
- [Changelog](https://github.com/pradyunsg/furo/blob/main/docs/changelog.md)
- [Commits](https://github.com/pradyunsg/furo/compare/2022.12.07...2023.05.20)

---
updated-dependencies:
- dependency-name: furo
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ed7719c`](https://github.com/supabase-community/postgrest-py/commit/ed7719cdbab13c3717dcbdeaa2c91647676379e7))

* chore(deps-dev): bump python-semantic-release from 7.33.2 to 7.34.6 (#250)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.33.2 to 7.34.6.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.33.2...v7.34.6)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`f2931f9`](https://github.com/supabase-community/postgrest-py/commit/f2931f9aa1fba763d1371aab42ca0016af727479))

* chore(deps): bump pydantic from 1.10.5 to 1.10.9 (#247)

Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.5 to 1.10.9.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v1.10.5...v1.10.9)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`371c73d`](https://github.com/supabase-community/postgrest-py/commit/371c73d22e95702c367dc2afd02a05d1a5fe1374))

* chore(deps): bump requests from 2.28.2 to 2.31.0 (#244)

Bumps [requests](https://github.com/psf/requests) from 2.28.2 to 2.31.0.
- [Release notes](https://github.com/psf/requests/releases)
- [Changelog](https://github.com/psf/requests/blob/main/HISTORY.md)
- [Commits](https://github.com/psf/requests/compare/v2.28.2...v2.31.0)

---
updated-dependencies:
- dependency-name: requests
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9153733`](https://github.com/supabase-community/postgrest-py/commit/9153733f6267a4e2e742d3f6d3149aac5458e871))

* chore(deps-dev): bump pre-commit from 3.1.0 to 3.2.0 (#235)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 3.1.0 to 3.2.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v3.1.0...v3.2.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`b319f64`](https://github.com/supabase-community/postgrest-py/commit/b319f64435054f91f4588adcb13e6baffa42d963))

* chore(deps-dev): bump pytest from 7.2.1 to 7.2.2 (#229)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.2.1 to 7.2.2.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.2.1...7.2.2)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`67572ba`](https://github.com/supabase-community/postgrest-py/commit/67572ba52ec1f49769b93446a2faba4c2135ffeb))

### Feature

* feat: add py.typed (#258)

* feat: add py.typed

* fix: remove trailing line

---------

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`39ae07d`](https://github.com/supabase-community/postgrest-py/commit/39ae07dfc3fc32bd54518676fd8444305993c2d4))

### Unknown

* Migrate postgrest-py from pydantic v1 to v2. (#276)

* Update package to pydantic 2.1

* Update poetry.lock

* Specify pydantic minor version

* isort fix

* Update poetry lock

* lock hash update ([`85ff406`](https://github.com/supabase-community/postgrest-py/commit/85ff4063d25ae859155fa42a152268c6cc138deb))

* feat explain (#241) ([`5be79ec`](https://github.com/supabase-community/postgrest-py/commit/5be79ec1499648705fb30c052c308bfdae4630a1))

* `maybe_single` with no matching rows returns None (#231) ([`d148298`](https://github.com/supabase-community/postgrest-py/commit/d148298195ea34c0048ea8e11b8a903f5a6f2342))

## v0.10.6 (2023-02-26)

### Chore

* chore: bump version to 0.10.6 (#225)

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`167c401`](https://github.com/supabase-community/postgrest-py/commit/167c40125b179f5c698e92cfe831837cf3017d65))

* chore(deps-dev): bump pre-commit from 3.0.4 to 3.1.0 (#224)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 3.0.4 to 3.1.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v3.0.4...v3.1.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a98883e`](https://github.com/supabase-community/postgrest-py/commit/a98883e979161a5c50095af421c1252b5c5d0370))

* chore(deps): bump sphinx from 5.3.0 to 6.1.3 (#221)

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 5.3.0 to 6.1.3.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v5.3.0...v6.1.3)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a2cdd3e`](https://github.com/supabase-community/postgrest-py/commit/a2cdd3ea37337db49834d73be610af90765f06e6))

### Unknown

* Fix sanitize_params to correctly resolve nested columns (#222)

* Add test for sanitize_params in utils

* Remove dot character from sanitize_params util

* Add tests for filter queries that include special characters in column name

* Add missing test for equals operator ([`36a0702`](https://github.com/supabase-community/postgrest-py/commit/36a070262444832d3f43af0d82803ab3a953ac77))

## v0.10.5 (2023-02-19)

### Chore

* chore: bump version (#220)

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`ea579fd`](https://github.com/supabase-community/postgrest-py/commit/ea579fd782e7d4ef13820356c8cc7fba0a4bec86))

* chore(deps): bump furo from 2022.9.29 to 2022.12.7 (#216)

Bumps [furo](https://github.com/pradyunsg/furo) from 2022.9.29 to 2022.12.7.
- [Release notes](https://github.com/pradyunsg/furo/releases)
- [Changelog](https://github.com/pradyunsg/furo/blob/main/docs/changelog.md)
- [Commits](https://github.com/pradyunsg/furo/compare/2022.09.29...2022.12.07)

---
updated-dependencies:
- dependency-name: furo
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c1fb15f`](https://github.com/supabase-community/postgrest-py/commit/c1fb15ff353ea0979218fba22221a9ac6c502c8b))

* chore(deps): bump pydantic from 1.10.4 to 1.10.5 (#217)

Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.4 to 1.10.5.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/v1.10.5/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v1.10.4...v1.10.5)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`bb3318e`](https://github.com/supabase-community/postgrest-py/commit/bb3318ee618595588268f048fa7b709c851f0e38))

* chore(deps): bump sphinx from 4.3.2 to 5.3.0 (#214)

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 4.3.2 to 5.3.0.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v4.3.2...v5.3.0)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`6646131`](https://github.com/supabase-community/postgrest-py/commit/6646131c727251c3aed199913d8d46ad58525bbd))

* chore(deps): bump cryptography from 39.0.0 to 39.0.1 (#213)

Bumps [cryptography](https://github.com/pyca/cryptography) from 39.0.0 to 39.0.1.
- [Release notes](https://github.com/pyca/cryptography/releases)
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/39.0.0...39.0.1)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`08c5cf7`](https://github.com/supabase-community/postgrest-py/commit/08c5cf752e97bf50922f8e7e81563a11c3334320))

* chore(deps-dev): bump pre-commit from 2.21.0 to 3.0.4 (#212)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 2.21.0 to 3.0.4.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v2.21.0...v3.0.4)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`da41692`](https://github.com/supabase-community/postgrest-py/commit/da4169208c8c17e4de97cca0f4d4e058c888c866))

* chore(deps-dev): bump isort from 5.11.5 to 5.12.0 (#211)

Bumps [isort](https://github.com/pycqa/isort) from 5.11.5 to 5.12.0.
- [Release notes](https://github.com/pycqa/isort/releases)
- [Changelog](https://github.com/PyCQA/isort/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pycqa/isort/compare/5.11.5...5.12.0)

---
updated-dependencies:
- dependency-name: isort
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`f10e569`](https://github.com/supabase-community/postgrest-py/commit/f10e569d67dc73cfdadf8101940c00170a50694e))

* chore(deps-dev): bump black from 22.12.0 to 23.1.0 (#208)

Bumps [black](https://github.com/psf/black) from 22.12.0 to 23.1.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/22.12.0...23.1.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`261f8ce`](https://github.com/supabase-community/postgrest-py/commit/261f8ce315279bc8166026b0bc3452c99f3273a4))

* chore: update pre-commit (#209)

* chore: update pre-commit

* fix: convert to string

* fix: drop py37

* &#39;Refactored by Sourcery&#39; (#210)

Co-authored-by: Sourcery AI &lt;&gt;

---------

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt;
Co-authored-by: sourcery-ai[bot] &lt;58596630+sourcery-ai[bot]@users.noreply.github.com&gt; ([`4f451a3`](https://github.com/supabase-community/postgrest-py/commit/4f451a39fb03924fa499a82b9cf8403911e9fb35))

* chore: bump version (#197)

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`0fa4e4e`](https://github.com/supabase-community/postgrest-py/commit/0fa4e4eeaa76dd7575b75d36ec7a04c04b4c0917))

* chore: bump ci poetry version (#186)

* chore: bump poetry lock

* fix: bump ci poetry version

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`95db586`](https://github.com/supabase-community/postgrest-py/commit/95db5866b281e509541c75f66be55d8645a38500))

* chore(deps-dev): bump isort from 5.10.1 to 5.11.4 (#180)

Bumps [isort](https://github.com/pycqa/isort) from 5.10.1 to 5.11.4.
- [Release notes](https://github.com/pycqa/isort/releases)
- [Changelog](https://github.com/PyCQA/isort/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pycqa/isort/compare/5.10.1...5.11.4)

---
updated-dependencies:
- dependency-name: isort
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`4afd352`](https://github.com/supabase-community/postgrest-py/commit/4afd352cfa16e5d5288f0678275996bd1422e3eb))

* chore(deps): bump wheel from 0.37.1 to 0.38.1 (#173)

Bumps [wheel](https://github.com/pypa/wheel) from 0.37.1 to 0.38.1.
- [Release notes](https://github.com/pypa/wheel/releases)
- [Changelog](https://github.com/pypa/wheel/blob/main/docs/news.rst)
- [Commits](https://github.com/pypa/wheel/compare/0.37.1...0.38.1)

---
updated-dependencies:
- dependency-name: wheel
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`1448861`](https://github.com/supabase-community/postgrest-py/commit/1448861c3e65fe9dd01f818cff6469257105b938))

* chore(deps): bump certifi from 2022.9.24 to 2022.12.7 (#171)

Bumps [certifi](https://github.com/certifi/python-certifi) from 2022.9.24 to 2022.12.7.
- [Release notes](https://github.com/certifi/python-certifi/releases)
- [Commits](https://github.com/certifi/python-certifi/compare/2022.09.24...2022.12.07)

---
updated-dependencies:
- dependency-name: certifi
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`745be97`](https://github.com/supabase-community/postgrest-py/commit/745be979676f82c9e941f1c7814cec4994b99873))

* chore(deps): bump httpx from 0.23.0 to 0.23.3 (#175)

Bumps [httpx](https://github.com/encode/httpx) from 0.23.0 to 0.23.3.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.23.0...0.23.3)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9d3a3d5`](https://github.com/supabase-community/postgrest-py/commit/9d3a3d5819a07c9d6dfd47dcad0a67e6f1899672))

### Feature

* feat: add text_search (#215)

* feat: add text_search

* fix: run pre-commit hooks

* test: add tests for text search

* fix: run black

* fix: update poetry deps

---------

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`0d16b47`](https://github.com/supabase-community/postgrest-py/commit/0d16b47d90a55544e3c296bf48b7efbec71e3e42))

* feat: upsert with on-conflict support (#142)

* feat: upsert with on-conflict support

* fix: lint

* Update postgrest/base_request_builder.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt;

* chore: docs

* chore: docs

---------

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`ecc6e79`](https://github.com/supabase-community/postgrest-py/commit/ecc6e796b94e1995362823a124e3a34918cec46f))

* feat: add support for 3.11 (#188)

* fix: add StrEnum

* fix: add 3.11 to ci

* fix: run black and autoflake

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`08f156a`](https://github.com/supabase-community/postgrest-py/commit/08f156a74c82b69137de57160077a456a2e9f598))

### Fix

* fix: handle Py311 Validation errors (#219)

* fix: handle NoneType response

* fix: add default error message for non JSONDecodable objects

* fix: rename message -&gt; details

* fix: handle exception instead of checking for no content

---------

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`29cb042`](https://github.com/supabase-community/postgrest-py/commit/29cb0425ab6b2d36e25284a4ca00777636d6c2eb))

* fix: update types for insert (#187)

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`228fe53`](https://github.com/supabase-community/postgrest-py/commit/228fe53009df3c46d8568e72b811e2013145e834))

### Unknown

* Update README.md ([`7e87364`](https://github.com/supabase-community/postgrest-py/commit/7e873646da5b37279708c651fd8bcb759ff658e9))

* Implementation of `maybe_single` (#118)

* add initial implementation on maybe_single

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* add sync maybe_single and fix error implementation

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* use relative import

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* implement new design for sync method

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* remove error from APIResponse

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* shift changes to async part

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* change class design to factory pattern

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* black and isort

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* fix: CI errors

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* fix tests and add additional test

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* fix new test

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* revamp class design

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* fix CI test

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* fix CI test 2

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* fix unasync error and add typing

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* make tests for new methods

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* generate code and test for sync

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* fix docstring

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* fix docstring and remove unwanted changes

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* fix tests on CI

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

* remove single ok tests

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt;

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt; ([`5d17f81`](https://github.com/supabase-community/postgrest-py/commit/5d17f81054d9b753c117b342528ab41cc8b7f9f7))

## v0.10.3 (2022-10-11)

### Chore

* chore(deps-dev): bump flake8 from 4.0.1 to 5.0.4 (#157)

Bumps [flake8](https://github.com/pycqa/flake8) from 4.0.1 to 5.0.4.
- [Release notes](https://github.com/pycqa/flake8/releases)
- [Commits](https://github.com/pycqa/flake8/compare/4.0.1...5.0.4)

---
updated-dependencies:
- dependency-name: flake8
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`28145b1`](https://github.com/supabase-community/postgrest-py/commit/28145b179936a92fb2e01bcf7f0e8c3be18c5b66))

* chore(deps): bump pydantic from 1.9.1 to 1.10.2 (#159)

Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.9.1 to 1.10.2.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v1.9.1...v1.10.2)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`8dec08f`](https://github.com/supabase-community/postgrest-py/commit/8dec08f064c1a41de7845775a3b8952c76d3a39b))

* chore(deps-dev): bump pytest from 7.1.2 to 7.1.3 (#158)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.1.2 to 7.1.3.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.1.2...7.1.3)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`56ddf21`](https://github.com/supabase-community/postgrest-py/commit/56ddf2103a69b1be7a61f6899e977f8ad37546cd))

* chore(deps-dev): bump pytest-cov from 3.0.0 to 4.0.0 (#156)

Bumps [pytest-cov](https://github.com/pytest-dev/pytest-cov) from 3.0.0 to 4.0.0.
- [Release notes](https://github.com/pytest-dev/pytest-cov/releases)
- [Changelog](https://github.com/pytest-dev/pytest-cov/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest-cov/compare/v3.0.0...v4.0.0)

---
updated-dependencies:
- dependency-name: pytest-cov
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`1e47d6d`](https://github.com/supabase-community/postgrest-py/commit/1e47d6dbc129b7b240f6230a34c3428f2542d770))

* chore(deps-dev): bump black from 22.3.0 to 22.10.0 (#155)

Bumps [black](https://github.com/psf/black) from 22.3.0 to 22.10.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/22.3.0...22.10.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`7636691`](https://github.com/supabase-community/postgrest-py/commit/763669140cbf3eb53f1974401b1bf81339e20f92))

* chore(deps-dev): bump python-semantic-release from 7.28.1 to 7.32.1 (#154)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.28.1 to 7.32.1.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.28.1...v7.32.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`4eb490a`](https://github.com/supabase-community/postgrest-py/commit/4eb490a856e4d2f0fd36814d5d8c8b39d9d5483c))

* chore(deps-dev): bump pre-commit from 2.19.0 to 2.20.0 (#138)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 2.19.0 to 2.20.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v2.19.0...v2.20.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`6d948a7`](https://github.com/supabase-community/postgrest-py/commit/6d948a76e6b38b7265fe51904100a094b59f00af))

* chore(deps): bump furo from 2022.6.4.1 to 2022.9.15 (#152)

Bumps [furo](https://github.com/pradyunsg/furo) from 2022.6.4.1 to 2022.9.15.
- [Release notes](https://github.com/pradyunsg/furo/releases)
- [Changelog](https://github.com/pradyunsg/furo/blob/main/docs/changelog.md)
- [Commits](https://github.com/pradyunsg/furo/compare/2022.06.04.1...2022.09.15)

---
updated-dependencies:
- dependency-name: furo
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`d1e50a2`](https://github.com/supabase-community/postgrest-py/commit/d1e50a2a83e55b2895fd4de19b0da11c34de09d8))

* chore(deps): bump furo from 2022.4.7 to 2022.6.4.1 (#130)

Bumps [furo](https://github.com/pradyunsg/furo) from 2022.4.7 to 2022.6.4.1.
- [Release notes](https://github.com/pradyunsg/furo/releases)
- [Changelog](https://github.com/pradyunsg/furo/blob/main/docs/changelog.md)
- [Commits](https://github.com/pradyunsg/furo/compare/2022.04.07...2022.06.04.1)

---
updated-dependencies:
- dependency-name: furo
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`09142ab`](https://github.com/supabase-community/postgrest-py/commit/09142ab374f51a5ff7b339f071fc8d369c14f144))

* chore(deps): bump httpx from 0.22.0 to 0.23.0 (#127)

Bumps [httpx](https://github.com/encode/httpx) from 0.22.0 to 0.23.0.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.22.0...0.23.0)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`0daf278`](https://github.com/supabase-community/postgrest-py/commit/0daf278b290d63565443737f6e1939b0fb040e08))

* chore(deps): bump pydantic from 1.9.0 to 1.9.1 (#126)

Bumps [pydantic](https://github.com/samuelcolvin/pydantic) from 1.9.0 to 1.9.1.
- [Release notes](https://github.com/samuelcolvin/pydantic/releases)
- [Changelog](https://github.com/samuelcolvin/pydantic/blob/v1.9.1/HISTORY.md)
- [Commits](https://github.com/samuelcolvin/pydantic/compare/v1.9.0...v1.9.1)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e13a6e0`](https://github.com/supabase-community/postgrest-py/commit/e13a6e0ea4b9761fde2d66e343a4b527761748f5))

* chore(deps-dev): bump pre-commit from 2.18.1 to 2.19.0 (#124)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 2.18.1 to 2.19.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v2.18.1...v2.19.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`5c0c128`](https://github.com/supabase-community/postgrest-py/commit/5c0c12874576728e9ffc13e97435d6fb0a4fbf76))

* chore(deps-dev): bump pytest from 7.1.1 to 7.1.2 (#117)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.1.1 to 7.1.2.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.1.1...7.1.2)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`36b7328`](https://github.com/supabase-community/postgrest-py/commit/36b732893710d3c5440a889d3027feb5a0ef2ad2))

### Fix

* fix: update version (#160)

Co-authored-by: joel@joellee.org &lt;joel@joellee.org&gt; ([`c1105dc`](https://github.com/supabase-community/postgrest-py/commit/c1105dc33d99d034fad0d9081ee59796ab990441))

### Unknown

* limit and order on foreign tables (#120)

* limit and order on foreign tables

* Apply suggestions from code review

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt;

* Updated docstrings for order and limit

* Changed limit modifier to use limit param instead of range headers

Co-authored-by: privaterepo &lt;hauntedanon420@gmail.com&gt;
Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`bf27b85`](https://github.com/supabase-community/postgrest-py/commit/bf27b850367a8126d8262fc5921e2e4f57bc6d60))

## v0.10.2 (2022-04-18)

### Chore

* chore(release): bump version to v0.10.2

Automatically generated by python-semantic-release ([`f30e688`](https://github.com/supabase-community/postgrest-py/commit/f30e6880f3a6dd125557aa67a631ef56120605f4))

* chore(deps-dev): bump python-semantic-release from 7.28.0 to 7.28.1 (#115)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.28.0 to 7.28.1.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.28.0...v7.28.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`29e91a2`](https://github.com/supabase-community/postgrest-py/commit/29e91a2123d1363963c1ba50c87fce38f0bef263))

* chore(deps-dev): bump pre-commit from 2.17.0 to 2.18.1 (#110)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 2.17.0 to 2.18.1.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v2.17.0...v2.18.1)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c4fbd29`](https://github.com/supabase-community/postgrest-py/commit/c4fbd29f84fbb1baa806cfb9018a368954d4d91d))

* chore(deps-dev): bump python-semantic-release from 7.27.0 to 7.28.0 (#113)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.27.0 to 7.28.0.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.27.0...v7.28.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`89177f2`](https://github.com/supabase-community/postgrest-py/commit/89177f26e2f6d3b98408c61a91ed37b1c3a3e0cc))

### Documentation

* docs: remove rtd config file

this seems to conflict with the config set in the dashboard; we can add this back later if we need more fine-grained control ([`14100a1`](https://github.com/supabase-community/postgrest-py/commit/14100a15a7d9c526df3e504a676d2d1018be3e04))

### Fix

* fix: include source directory name (#116)

Poetry by default looks for a directory with the same name as the
project as the source directory. However as our project is named
postgrest-py, but we migrated to the postgrest namespace, we need to
explicitly tell poetry where to look for the source code. ([`18334f8`](https://github.com/supabase-community/postgrest-py/commit/18334f880d5e4e769a9e843007bc2f46b597a777))

### Unknown

* Namespace change (#114)

* docs: add rtd config

* chore: move to the postgrest namespace

* chore: move constants to its own file

* chore: pass headers/params down builders

We were earlier modifying session.headers/session.params for every
query. Instead of this we follow what postgrest-js does and add
headers and params as arguments to the query builders, and pass them
down the chain of builders, and finally pass it to the execute method.

* docs: add examples

* fix: order of filters in examples

* docs: add example for closing the client ([`6493154`](https://github.com/supabase-community/postgrest-py/commit/64931544f4d2c8a8bbfb5e133c7e5b761ad5a10a))

* Add documentation (#111)

* deps: add furo

* docs: document public classes

* docs: setup sphinx + furo

* docs: fix bullet point

* fix: remove test file

* tests: check if params purged after execute

* fix: remove the `asyncio` mark from sync tests

* docs: add project version

* docs: add rtd config ([`442a45a`](https://github.com/supabase-community/postgrest-py/commit/442a45a5638253888d7675f3c664e01c1e61d7d3))

## v0.10.1 (2022-04-07)

### Chore

* chore(release): bump version to v0.10.1

Automatically generated by python-semantic-release ([`9ddc6f5`](https://github.com/supabase-community/postgrest-py/commit/9ddc6f5e186c7670db417bafdb2f7bc8a5610c4f))

* chore(deps-dev): bump black from 22.1.0 to 22.3.0 (#107)

Bumps [black](https://github.com/psf/black) from 22.1.0 to 22.3.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/22.1.0...22.3.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`05d2e01`](https://github.com/supabase-community/postgrest-py/commit/05d2e01f7a60e8141f5a37ea9e47b44eb2f653a6))

* chore(deps-dev): bump pytest-asyncio from 0.18.2 to 0.18.3 (#106)

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.18.2 to 0.18.3.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Changelog](https://github.com/pytest-dev/pytest-asyncio/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.18.2...v0.18.3)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`cf0d3ac`](https://github.com/supabase-community/postgrest-py/commit/cf0d3acfe3e02fde914fa034f21ebf34c28db254))

* chore(deps-dev): bump pytest from 7.1.0 to 7.1.1 (#105)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.1.0 to 7.1.1.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.1.0...7.1.1)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`f8ad56e`](https://github.com/supabase-community/postgrest-py/commit/f8ad56e2083b925773a06331579f3cfff7182185))

* chore(deps-dev): bump python-semantic-release from 7.26.0 to 7.27.0 (#104)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.26.0 to 7.27.0.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.26.0...v7.27.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`36b861c`](https://github.com/supabase-community/postgrest-py/commit/36b861cedaf8a381291a9add47e14eca7db6d38d))

* chore(deps-dev): bump pytest from 7.0.1 to 7.1.0 (#103)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.0.1 to 7.1.0.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.0.1...7.1.0)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`8abde61`](https://github.com/supabase-community/postgrest-py/commit/8abde6117f62dd920bb9c7a690fb856cadfd9273))

### Fix

* fix: escape chars only when necessary (#108)

* fix: escape chars only when necessary

* fix: escape column names

* deps: upgrade black in pre-commit ([`53f7d18`](https://github.com/supabase-community/postgrest-py/commit/53f7d18807aa292aa7326af573bd55828a3bb6e4))

## v0.10.0 (2022-03-13)

### Chore

* chore(release): bump version to v0.10.0

Automatically generated by python-semantic-release ([`cbbdf5c`](https://github.com/supabase-community/postgrest-py/commit/cbbdf5cb6e6ad9380242b6b4fa6ff29867fe6e03))

### Feature

* feat: add .contains and .contained_by operators to match JS client (#100)

* Add .contains and .contained_by operators to match JS client

* Fix whitespace

* Add tests

* Describe percent-encoded strings ([`7189e09`](https://github.com/supabase-community/postgrest-py/commit/7189e095bd792fcbc5b89e4f03ef7174e1dd30b7))

## v0.9.2 (2022-03-12)

### Chore

* chore(release): bump version to v0.9.2

Automatically generated by python-semantic-release ([`7d156b3`](https://github.com/supabase-community/postgrest-py/commit/7d156b33d8dd78e45ad0c727e5c5e4bd9c89b1e3))

* chore(deps-dev): bump python-semantic-release from 7.25.2 to 7.26.0 (#98)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.25.2 to 7.26.0.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.25.2...v7.26.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`796687d`](https://github.com/supabase-community/postgrest-py/commit/796687d5f5fcf72c7b4f824f6d1ce3b255232c22))

### Fix

* fix: make api error properties optionals (#101)

For avoid linter error ([`eb92326`](https://github.com/supabase-community/postgrest-py/commit/eb92326db0088fbf2d96bb68b206160b03e63747))

## v0.9.1 (2022-03-08)

### Chore

* chore(release): bump version to v0.9.1

Automatically generated by python-semantic-release ([`d4204ef`](https://github.com/supabase-community/postgrest-py/commit/d4204ef4dc33a9fccf8684dc13c90df3e843c1c9))

* chore(deps-dev): bump pytest-asyncio from 0.18.1 to 0.18.2 (#96)

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.18.1 to 0.18.2.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.18.1...v0.18.2)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`8cf3de1`](https://github.com/supabase-community/postgrest-py/commit/8cf3de18b787d5c2407be5264f981381d747ea8b))

* chore(deps-dev): bump python-semantic-release from 7.25.1 to 7.25.2 (#95)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.25.1 to 7.25.2.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.25.1...v7.25.2)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`392845d`](https://github.com/supabase-community/postgrest-py/commit/392845d698570d48f8412f7c7396c41d0987d5cc))

* chore(deps-dev): bump python-semantic-release from 7.25.0 to 7.25.1 (#93)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.25.0 to 7.25.1.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.25.0...v7.25.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a7cee63`](https://github.com/supabase-community/postgrest-py/commit/a7cee6309a37f310fd6cf2079ec2142a05db71b6))

### Fix

* fix: fix APIError (#97) ([`ff29024`](https://github.com/supabase-community/postgrest-py/commit/ff290240cf9364902ffca19e854604d6a40770f9))

## v0.9.0 (2022-02-19)

### Chore

* chore(release): bump version to v0.9.0

Automatically generated by python-semantic-release ([`032fc5e`](https://github.com/supabase-community/postgrest-py/commit/032fc5ef89e16bc42eaf7c4dff335930394448a2))

### Feature

* feat: export APIError and APIResponse ([`83e7799`](https://github.com/supabase-community/postgrest-py/commit/83e77991101c8e8aec42552344b02ce8db6bd04a))

### Unknown

* Export APIResponse and APIError (#92)

* Export APIResponse and APIError

* Reorder imports ([`b237d62`](https://github.com/supabase-community/postgrest-py/commit/b237d62eaa825e72b9069b0a6cc40c6da58f0ab4))

* Bump python-semantic-release from 7.24.0 to 7.25.0 (#91)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.24.0 to 7.25.0.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.24.0...v7.25.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3a9419c`](https://github.com/supabase-community/postgrest-py/commit/3a9419c212b5892a03b67969d789981a83352e5a))

* Bump pytest from 7.0.0 to 7.0.1 (#90)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.0.0 to 7.0.1.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.0.0...7.0.1)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`1b6c6a5`](https://github.com/supabase-community/postgrest-py/commit/1b6c6a574796dc14b67774de54d9c1bd67dc09d4))

* Bump pytest-asyncio from 0.17.2 to 0.18.1 (#89)

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.17.2 to 0.18.1.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.17.2...v0.18.1)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`eda1892`](https://github.com/supabase-community/postgrest-py/commit/eda189204895c26d336d5f68900c05acfefa3c33))

* Bump pytest from 6.2.5 to 7.0.0 (#87)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 6.2.5 to 7.0.0.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/6.2.5...7.0.0)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`f12ffa5`](https://github.com/supabase-community/postgrest-py/commit/f12ffa5d0e6b24099a5bed89fb1976edf8b05a5c))

* Bump black from 21.12b0 to 22.1.0 (#85)

Bumps [black](https://github.com/psf/black) from 21.12b0 to 22.1.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/commits/22.1.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`7bf8b47`](https://github.com/supabase-community/postgrest-py/commit/7bf8b47a0b9be3adb3305488f07a4afebe65b141))

## v0.8.2 (2022-01-30)

### Chore

* chore(release): bump version to v0.8.2

Automatically generated by python-semantic-release ([`34fd1bd`](https://github.com/supabase-community/postgrest-py/commit/34fd1bda6893782a955340e39bcdba6633034a69))

### Fix

* fix: Add-response-model ([`4c0259d`](https://github.com/supabase-community/postgrest-py/commit/4c0259d1658c07bf3e78fe03d98b304f7a6f0c7a))

### Unknown

* Add-response-model (#64)

* add poetry dependency

* create APIResponse model

* return APIResponse model in execute method

* sort imports

* mypy bug workaround (https://github.com/python/mypy/issues/9319)

* split logic, validate error existance and better type APIResponse

* Implement APIError

* add missing black config in pre-commit config

* type APIError properties

* fix: rm unused code and use returning param in update

* refactor: reorder lines

* chore: rebuild sync

* chore: rebuild poetry.lock

* fix: remove wrong parameter

* chore: format

* Chore: add missing return types

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt;

* chore: replace builtin dict by Dict to support python &lt; 3.9

* chore: update precommit hooks

* chore: apply format

* update return type in execute method

* use relative import

* add link to mypy issue

* switch super init by class init to avoid future errors

* chore: apply future annotations notation to return

* chore: rebuild sync

* tests: Add tests for response model (#74)

* initial commit

* tests: add fixtures for APIResponse

* tests: [WIP] Test methods that don&#39;t interact with RequestResponse

* tests: replace builtin type by typing type and add type annotations

* tests: add requests Response fixtures

* chore: change return order to improve readability

* tests: add tests for left methods

Co-authored-by: Joel Lee &lt;joel@joellee.org&gt;
Co-authored-by: Dani Reinón &lt;dani@dribo.es&gt;

* chore: modify ValueError with ValidationError

* chore: add &#34;_&#34; to internal methods

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt;
Co-authored-by: Lee Yi Jie Joel &lt;lee.yi.jie.joel@gmail.com&gt;
Co-authored-by: Joel Lee &lt;joel@joellee.org&gt; ([`07ef4d4`](https://github.com/supabase-community/postgrest-py/commit/07ef4d4c03f014207ec1707786e601aa7f21b97d))

* Bump httpx from 0.21.3 to 0.22.0 (#84)

Bumps [httpx](https://github.com/encode/httpx) from 0.21.3 to 0.22.0.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.21.3...0.22.0)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e190621`](https://github.com/supabase-community/postgrest-py/commit/e1906211c42bc6e3f7918f5e0c4bf342690f64d8))

* Bump python-semantic-release from 7.23.0 to 7.24.0 (#82)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.23.0 to 7.24.0.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.23.0...v7.24.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`0cefdc7`](https://github.com/supabase-community/postgrest-py/commit/0cefdc7895319ab0fdba25662d62fc54bcaffc7e))

## v0.8.1 (2022-01-22)

### Chore

* chore(release): bump version to v0.8.1

Automatically generated by python-semantic-release ([`1560d8f`](https://github.com/supabase-community/postgrest-py/commit/1560d8f27b7a9466da834f60b309b26e8b897d27))

* chore: set upload_to_repository to true ([`c65fe95`](https://github.com/supabase-community/postgrest-py/commit/c65fe9553dcc2b42f404d0cb350eb4b704cdf59c))

### Fix

* fix: order filter ([`094dbad`](https://github.com/supabase-community/postgrest-py/commit/094dbadb26bef4238536579ede71d46a4ef67899))

### Unknown

* Bump pre-commit from 2.16.0 to 2.17.0 (#79)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 2.16.0 to 2.17.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/master/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v2.16.0...v2.17.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`542bd95`](https://github.com/supabase-community/postgrest-py/commit/542bd95ae84f5522cde9ee2ed286de901198c02e))

* Bump pytest-asyncio from 0.17.1 to 0.17.2 (#77)

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.17.1 to 0.17.2.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.17.1...v0.17.2)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`5150c17`](https://github.com/supabase-community/postgrest-py/commit/5150c17ef80ca75b164f91ca7e1d61f38eaf271d))

* Bump pytest-asyncio from 0.17.0 to 0.17.1 (#76)

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.17.0 to 0.17.1.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.17.0...v0.17.1)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`1d80268`](https://github.com/supabase-community/postgrest-py/commit/1d80268f62b3e196f4a56a1930d34644b5a3d1e8))

## v0.8.0 (2022-01-16)

### Chore

* chore(release): bump version to v0.8.0

Automatically generated by python-semantic-release ([`828de1a`](https://github.com/supabase-community/postgrest-py/commit/828de1a6ee5564492469f4f09717e2993e4e2776))

* chore: filter deploy section by repo owner (#69)

* fix: interpolations erros and other things reported by sourcery-ai

* chore: filter deploy section by repo owner ([`82820e4`](https://github.com/supabase-community/postgrest-py/commit/82820e45d84b511a55ddc5115b1c7f7b2a95264a))

* chore: add ignore md rules to dev container and fix changelog (#67)

* fix: interpolations erros and other things reported by sourcery-ai

* chore: add ignore md rules to dev container and fix changelog ([`19c949d`](https://github.com/supabase-community/postgrest-py/commit/19c949d1757763ecfb299932e75fec33b0920c71))

### Feature

* feat: add timeout as a parameter of clients (#75)

* feat: add timeout as a parameter of clients

This feature is for evicting the use of the default timeout of httpx.

* feat: use union and constants default value for timeout ([`1ea965a`](https://github.com/supabase-community/postgrest-py/commit/1ea965a6cb32dacb5f41cd1198f8a970a24731b6))

### Unknown

* Bump pytest-asyncio from 0.16.0 to 0.17.0 (#73)

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.16.0 to 0.17.0.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.16.0...v0.17.0)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`7897d97`](https://github.com/supabase-community/postgrest-py/commit/7897d97bde394a16b8de9c76f1e57813bfc32daf))

* Bump httpx from 0.21.2 to 0.21.3 (#71)

Bumps [httpx](https://github.com/encode/httpx) from 0.21.2 to 0.21.3.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.21.2...0.21.3)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`6d54ba4`](https://github.com/supabase-community/postgrest-py/commit/6d54ba477d19ff4badcdcd1c0746a1e26166c01b))

* Bump httpx from 0.21.1 to 0.21.2 (#70)

Bumps [httpx](https://github.com/encode/httpx) from 0.21.1 to 0.21.2.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.21.1...0.21.2)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`cc9bd9e`](https://github.com/supabase-community/postgrest-py/commit/cc9bd9e766c53c96235af155489e380a64acbd67))

* Fix codecov badge (#68) ([`5697d8e`](https://github.com/supabase-community/postgrest-py/commit/5697d8e677f48044a963b3bc44df757d4a3219d1))

## v0.7.1 (2022-01-04)

### Chore

* chore(release): bump version to v0.7.1

Automatically generated by python-semantic-release ([`c80c3ff`](https://github.com/supabase-community/postgrest-py/commit/c80c3ff377852380aa78ce190eb98f86f0699075))

### Performance

* perf: sync configurations with gotrue-py (#66)

* fix: interpolations errors and other things reported by sourcery-ai

* perf: sync configurations with gotrue-py

* fix: warning of precommits rules ([`d5a97da`](https://github.com/supabase-community/postgrest-py/commit/d5a97daad42a431b2d36f16e3969b38b9dded288))

### Unknown

* add poetry local config to gitignore (#63) ([`031cb5f`](https://github.com/supabase-community/postgrest-py/commit/031cb5f4863a25b5be87f047133d293956377d46))

* delete poetry.toml file from repo (#62) ([`8b04ae0`](https://github.com/supabase-community/postgrest-py/commit/8b04ae07047ec6a33e36d84b37c99ac9fb07834f))

* fix-sanitize_param-double-quote-error (#61)

* replace utf-8 character by character

* avoid escaping characters by using single quotes

* fix tests ([`0eb871a`](https://github.com/supabase-community/postgrest-py/commit/0eb871a53b91bca5edc68f9cc3ba67e83e7ae0a0))

## v0.7.0 (2022-01-02)

### Chore

* chore: bump version to v0.7.0 (#60)

* fix: interpolations erros and other things reported by sourcery-ai

* chore: bump version to v0.7.0 ([`a936820`](https://github.com/supabase-community/postgrest-py/commit/a93682082283f2dbaef679705fd71a5620150f90))

### Feature

* feat: non str arguments to filters (#58)

* fix: interpolations erros and other things reported by sourcery-ai

* feat: non str arguments to filters ([`46802db`](https://github.com/supabase-community/postgrest-py/commit/46802db317b4313d9f0241809bcc75312404aac3))

* feat: add return mode like a parameter (#59)

* fix: interpolations erros and other things reported by sourcery-ai

* feat: add return mode like a parameter

* chore: change constants.py by types.py ([`8728ee8`](https://github.com/supabase-community/postgrest-py/commit/8728ee8e840a453332a814d00d622d76589fb2a8))

### Fix

* fix: query params are immutable when using order (#57)

* fix: interpolations erros and other things reported by sourcery-ai

* fix: query params are immutable when using order ([`d1254a6`](https://github.com/supabase-community/postgrest-py/commit/d1254a60697f67fbf5c837afd1fe047b3ef4ea6e))

* fix: params and headers of session are shared between queries (#55)

* fix: interpolations erros and other things reported by sourcery-ai

* fix: params and headers of session are shared between queries

* fix: suggestion of sourcery

* fix: suggestion of sourcery ([`b631e3b`](https://github.com/supabase-community/postgrest-py/commit/b631e3be6ae2e47477813feae85780219c6c6baf))

## v0.6.0 (2022-01-01)

### Chore

* chore: update versions (#50)

Co-authored-by: Joel Lee &lt;joel@joellee.org&gt; ([`c8ba57a`](https://github.com/supabase-community/postgrest-py/commit/c8ba57af60202e5cb98a5388a11cda9954cfd75d))

### Feature

* feat: implement async sync with `unasync-cli` (#30)

Co-authored-by: Dani Reinón &lt;dani@dribo.es&gt; ([`b1423b5`](https://github.com/supabase-community/postgrest-py/commit/b1423b5e026399b038348a4f25914bf4bdb4e8f4))

### Fix

* fix: interpolations erros and other things reported by sourcery-ai (#37) ([`2fc29b2`](https://github.com/supabase-community/postgrest-py/commit/2fc29b272323203bfa0b4f5f59ae12bde08dc530))

### Performance

* perf: use inheritance to improve our code base (#47)

* fix: interpolations erros and other things reported by sourcery-ai

* feat: use inheritance to improve the code base

* fix: sourcery refactored

* chore: update pre commit rules

* fix: remove noqa F401 comments

* fix: remove duplicate and unused imports in base_client.py

* feat: use enum instance literals in base_request_builder.py

* pref: cast session only once in __init__

* pref: remove unnecesary cast

* tests: update tests

* chore: generate sync code

* feat: add support for upsert

* Rm cast from rpc in async client

* Rm cast from rpc in sync client

* Add table method as an alias for from_

Co-authored-by: dreinon &lt;67071425+dreinon@users.noreply.github.com&gt;
Co-authored-by: Dani Reinón &lt;dani@dribo.es&gt; ([`315f596`](https://github.com/supabase-community/postgrest-py/commit/315f596386e26974595f15f34dad930b37d08e15))

### Unknown

* Bump black from 21.11b1 to 21.12b0

Bumps [black](https://github.com/psf/black) from 21.11b1 to 21.12b0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/commits)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7a54d58`](https://github.com/supabase-community/postgrest-py/commit/7a54d580350ef12480d9df207561bd6a70dd08d8))

* Bump mypy from 0.910 to 0.930 (#52)

Bumps [mypy](https://github.com/python/mypy) from 0.910 to 0.930.
- [Release notes](https://github.com/python/mypy/releases)
- [Commits](https://github.com/python/mypy/compare/v0.910...v0.930)

---
updated-dependencies:
- dependency-name: mypy
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`f7217d5`](https://github.com/supabase-community/postgrest-py/commit/f7217d5bfb6ca2c2ab378555c3c3330c007d24ba))

* Bump black from 21.10b0 to 21.11b1 (#46) ([`3934fb2`](https://github.com/supabase-community/postgrest-py/commit/3934fb2bd7c755962fa2fe490419d3e967e3555a))

* Bump pre-commit from 2.15.0 to 2.16.0 (#45) ([`8788c18`](https://github.com/supabase-community/postgrest-py/commit/8788c184e0fed98aa5b613a7d68d5756372543e8))

* Bump httpx from 0.20.0 to 0.21.1 (#44)

Bumps [httpx](https://github.com/encode/httpx) from 0.20.0 to 0.21.1.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.20.0...0.21.1)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`60ef2ce`](https://github.com/supabase-community/postgrest-py/commit/60ef2ce661448f3ee740e297713c213f75b60427))

* Revert &#34;Add Sourcery to pre-commit (#38)&#34; (#41)

This reverts commit 25f23586774f5a73661c9da92d0035e667d0df2c. ([`f019aaa`](https://github.com/supabase-community/postgrest-py/commit/f019aaaafeb9a899052cd406f1900c9c0b8611ac))

* Add Sourcery to pre-commit (#38) ([`25f2358`](https://github.com/supabase-community/postgrest-py/commit/25f23586774f5a73661c9da92d0035e667d0df2c))

* Bump black from 21.7b0 to 21.10b0 (#33)

Bumps [black](https://github.com/psf/black) from 21.7b0 to 21.10b0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/commits)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ba83ba4`](https://github.com/supabase-community/postgrest-py/commit/ba83ba43c6cfba906fbb710d3913e5dc070fdde3))

* Bump pytest-cov from 2.12.1 to 3.0.0 (#34)

Bumps [pytest-cov](https://github.com/pytest-dev/pytest-cov) from 2.12.1 to 3.0.0.
- [Release notes](https://github.com/pytest-dev/pytest-cov/releases)
- [Changelog](https://github.com/pytest-dev/pytest-cov/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest-cov/compare/v2.12.1...v3.0.0)

---
updated-dependencies:
- dependency-name: pytest-cov
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`8af95a7`](https://github.com/supabase-community/postgrest-py/commit/8af95a7dacff9d40e36d2274dcce34a527595a0a))

* Bump pytest from 6.2.4 to 6.2.5 (#15)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 6.2.4 to 6.2.5.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/6.2.4...6.2.5)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`fc0434d`](https://github.com/supabase-community/postgrest-py/commit/fc0434d067876d859410f2849cf7db6a405efd1e))

* Bump pytest-asyncio from 0.15.1 to 0.16.0 (#32)

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.15.1 to 0.16.0.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.15.1...v0.16.0)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`765046e`](https://github.com/supabase-community/postgrest-py/commit/765046ef3f17cbe5ea8ed2567b09e7254ed42d2c))

* Bump httpx from 0.19.0 to 0.20.0 (#31)

Bumps [httpx](https://github.com/encode/httpx) from 0.19.0 to 0.20.0.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.19.0...0.20.0)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`36408d7`](https://github.com/supabase-community/postgrest-py/commit/36408d78b2b1fe0f37495cd9a6df1b052561d647))

* Bump mypy from 0.902 to 0.910 (#12)

Bumps [mypy](https://github.com/python/mypy) from 0.902 to 0.910.
- [Release notes](https://github.com/python/mypy/releases)
- [Commits](https://github.com/python/mypy/compare/v0.902...v0.910)

---
updated-dependencies:
- dependency-name: mypy
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`7d5bf09`](https://github.com/supabase-community/postgrest-py/commit/7d5bf095f6a4be9b328ff1b2ab8c8b19b6c3974f))

* Fix 3.10 pipelines ([`457b70c`](https://github.com/supabase-community/postgrest-py/commit/457b70cf24f4db3e9c59b8d997d65cc70270c080))

* Add pre-commit (#28) ([`c5032b5`](https://github.com/supabase-community/postgrest-py/commit/c5032b5ae6c9f80f3801193d706f56820a98f70b))

* Update and reformat README.md, docker-compose.yaml ([`7188fa2`](https://github.com/supabase-community/postgrest-py/commit/7188fa2063c09a68e8b40c0db559fb9b6b89f567))

* Add docker-compose setup for local development (#22) ([`1cb42a1`](https://github.com/supabase-community/postgrest-py/commit/1cb42a14e8cbec9c0d4d79f5ba03b81435f91eca))

* Add Python 3.10 to the build matrix ([`3632d75`](https://github.com/supabase-community/postgrest-py/commit/3632d7521df70ce564a356024450c7a5e5d65fe1))

* Implement counting feature (#26) ([`735cefd`](https://github.com/supabase-community/postgrest-py/commit/735cefd9aa6ecea99a392c0bdfa1ef3b633a6067))

* Fix bug on sanitizing params (#24) ([`3e7b60e`](https://github.com/supabase-community/postgrest-py/commit/3e7b60eb645f08239d8fb37653f62fbf827e7a12))

* Add Code of Conduct and Contributing guide (#23)

Co-authored-by: Joel Lee &lt;joel@joellee.org&gt; ([`9031297`](https://github.com/supabase-community/postgrest-py/commit/903129738dd782cad495f1c747df8dd694f32328))

* Add Match Command (#18)

Co-authored-by: Joel Lee &lt;joel@joellee.org&gt; ([`9eadbe1`](https://github.com/supabase-community/postgrest-py/commit/9eadbe1275f8c4154ab021f600a57ec2d6f926eb))

## v0.5.0 (2021-09-09)

### Unknown

* Bump version to 0.5.0 ([`1144895`](https://github.com/supabase-community/postgrest-py/commit/11448957a18eca506ade0430b0c1d5ac554b41cb))

* Improve PostgrestClient.auth() (#14) ([`6321ffe`](https://github.com/supabase-community/postgrest-py/commit/6321ffeac7b3bb15e52a8881c4f527479bf885a6))

* Update httpx to v0.19.0 (#13) ([`71456e5`](https://github.com/supabase-community/postgrest-py/commit/71456e5382d0062168e5045f3065a69a31fc0e60))

* Add dependabot.yml ([`d83fa15`](https://github.com/supabase-community/postgrest-py/commit/d83fa15b8c7d53e3321213d95dbf257db98610ab))

* Allow setting headers in PostgrestClient&#39;s constructor (#10) ([`1737e69`](https://github.com/supabase-community/postgrest-py/commit/1737e698d1ab5c8b740acef8d506dfc56cac9ca9))

* Update Python workflow ([`3ffb7fb`](https://github.com/supabase-community/postgrest-py/commit/3ffb7fb20f1f8b5c9f10b8c7d08980d7bb3016dd))

* Upgrade dependencies ([`cf743d9`](https://github.com/supabase-community/postgrest-py/commit/cf743d95a2d045eebeff5eafc1941e1db1e18a79))

## v0.4.0 (2021-09-09)

### Unknown

* Bump version to 0.4.0 ([`7efa19c`](https://github.com/supabase-community/postgrest-py/commit/7efa19c63f1b16b87db8ace9513165b2327de66f))

* Revert the last 2 commits. Drop Python 3.6 support

This reverts commit 899f75bd6a477a95eef47f2aabb8fdce7cbba200. ([`b3e7df2`](https://github.com/supabase-community/postgrest-py/commit/b3e7df2459218a3fde775e921a0cad54755d5148))

* Lower minimum required Python version to 3.6 ([`a3164bd`](https://github.com/supabase-community/postgrest-py/commit/a3164bd20d65281858f257bfbd47bde75d87ad4c))

* Add Python 3.6 to build matrix ([`899f75b`](https://github.com/supabase-community/postgrest-py/commit/899f75bd6a477a95eef47f2aabb8fdce7cbba200))

* Update tests for httpx v0.16.x (#4) ([`dd90a57`](https://github.com/supabase-community/postgrest-py/commit/dd90a573d99bdce6f2b39bd660208f46c1429d0e))

* Upgrade httpx to v0.16.1 ([`cac7fe2`](https://github.com/supabase-community/postgrest-py/commit/cac7fe235e009430b54220c4f0ea84e7c4a0566c))

* Allow multivalued query parameters (#2) ([`4f588f8`](https://github.com/supabase-community/postgrest-py/commit/4f588f800b303c04f2cebafaf1576e8409aafbce))

* Add some tests ([`275c233`](https://github.com/supabase-community/postgrest-py/commit/275c2332a1d9ce0cd64e23ab618e9cc7b18810ca))

* Rename some symbols ([`71c3a33`](https://github.com/supabase-community/postgrest-py/commit/71c3a33c06d8df1bf032e17709394d5c651083ab))

* Code refactoring ([`8f4a702`](https://github.com/supabase-community/postgrest-py/commit/8f4a7023df6207fa90673e2ad746a3d55fcba50f))

* Add tests for RequestBuilder ([`4f0ed78`](https://github.com/supabase-community/postgrest-py/commit/4f0ed783d1aa7e994358dba2e835171f07d61775))

## v0.3.2 (2020-08-20)

### Documentation

* docs: adds enterprise sponsors ([`9df43d5`](https://github.com/supabase-community/postgrest-py/commit/9df43d59954b191128dd755057190ca62762d404))

### Unknown

* Bump version to 0.3.2 ([`7d00675`](https://github.com/supabase-community/postgrest-py/commit/7d0067552ecafb698b5a651e2b7fe5af5ff950b8))

* Move to supabase/postgrest-py ([`84c847f`](https://github.com/supabase-community/postgrest-py/commit/84c847fe8e3ff32015ab41bd0caf170f39186964))

* Merge remote-tracking branch &#39;supabase/master&#39; into master ([`12e268b`](https://github.com/supabase-community/postgrest-py/commit/12e268b2f1516949991f3153b314716d734cb756))

* Add badges to README.md ([`9d328d8`](https://github.com/supabase-community/postgrest-py/commit/9d328d8cdc71f34bc29af428668ec9e3794874b1))

## v0.3.1 (2020-08-19)

### Unknown

* Bump version to 0.3.1 ([`71c6ea6`](https://github.com/supabase-community/postgrest-py/commit/71c6ea64730979bf76142d1dad944ba58fbb51db))

* Remove dummy test cases and PyPy3 from Travis CI ([`a185327`](https://github.com/supabase-community/postgrest-py/commit/a18532780b0ab5d4ba0b37c63c4c60727a093687))

## v0.3.0 (2020-08-19)

### Unknown

* Bump version to 0.3.0 ([`67dc8d3`](https://github.com/supabase-community/postgrest-py/commit/67dc8d3d19075be18aa20e799dffb71be5f3db62))

* Add .travis.yml ([`4e39921`](https://github.com/supabase-community/postgrest-py/commit/4e3992199d12898842d1bfd4888d2f4af52fee67))

* Fix PostgrestClient.schema() not work. Add tests for PostgrestClient ([`20a0120`](https://github.com/supabase-community/postgrest-py/commit/20a0120e5b61e6027e150892092b1686eea0ec27))

* Add pytest ([`d8d9e2c`](https://github.com/supabase-community/postgrest-py/commit/d8d9e2ce1cc36188bb8da65605e066359376c120))

* Support multi-criteria ordering ([`5066c58`](https://github.com/supabase-community/postgrest-py/commit/5066c58345237f787ce119a60f62ae8163975c26))

* Code refactoring ([`0803e65`](https://github.com/supabase-community/postgrest-py/commit/0803e658bacce2c3c370a15df856b9710c6bc3c8))

* Update RequestBuilder ([`d115f0d`](https://github.com/supabase-community/postgrest-py/commit/d115f0de857b5dd03ac67b81caf6b331db3eee62))

* Rename project ([`12734e1`](https://github.com/supabase-community/postgrest-py/commit/12734e198935f14316d07572fe7ca5e857af2798))

## v0.2.0 (2020-08-11)

### Unknown

* Bump version to 0.2.0 ([`5cfc52b`](https://github.com/supabase-community/postgrest-py/commit/5cfc52b66606e6e6b18e5d37bb414d6ecf84fe14))

* Deprecate PostgrestClient.from_table() ([`32f9fba`](https://github.com/supabase-community/postgrest-py/commit/32f9fbac53ba5a151baec751eae91a631e32a35c))

* Update ([`4f2accb`](https://github.com/supabase-community/postgrest-py/commit/4f2accb2871e6b783c68115455d1fe80dc15ef49))

* Update README and TODO ([`2d8fcbf`](https://github.com/supabase-community/postgrest-py/commit/2d8fcbf7fa071f90e58cdbb0e4e4eb50c7c3c687))

* RequestBuilder.select() now accepts columns as *args ([`8901f86`](https://github.com/supabase-community/postgrest-py/commit/8901f86244f4885c7033316deef47ae912d39043))

* Rename Client to PostgrestClient and deprecate the old name ([`1200265`](https://github.com/supabase-community/postgrest-py/commit/1200265737b51c5b0d861cd635ee13512b082471))

* Support RPC ([`040ad6c`](https://github.com/supabase-community/postgrest-py/commit/040ad6c6e5a5431e18184c29258608c26f98cf47))

* Support basic authentication ([`1e8166d`](https://github.com/supabase-community/postgrest-py/commit/1e8166da1ac9c50003dad051dd82c1fbf311b078))

* Remove dead code ([`f9ee777`](https://github.com/supabase-community/postgrest-py/commit/f9ee777f1cc90a99ad1d187ed31825862111ecdc))

## v0.1.1 (2020-08-07)

### Unknown

* Bump version to 0.1.1 ([`25da534`](https://github.com/supabase-community/postgrest-py/commit/25da5340f74565170b71decc40837c0f735c25c5))

## v0.1.0 (2020-08-07)

### Unknown

* Bump version to 0.1.0 ([`82e7f55`](https://github.com/supabase-community/postgrest-py/commit/82e7f5529ec2a01e6426dc40a20fe8b8094958ba))

* Complete basic features ([`96fed3a`](https://github.com/supabase-community/postgrest-py/commit/96fed3a3d2d9e921c0ce9f8225dfa7948fa60f2b))

* Add GET only filters ([`3c1cbf2`](https://github.com/supabase-community/postgrest-py/commit/3c1cbf291151d3eb1380d6cc3bbdd392eaff22f0))

* Code refactoring ([`4379b7f`](https://github.com/supabase-community/postgrest-py/commit/4379b7fc760707d025143f218e6cee7391c781b1))

* Build a basic structure of the project ([`57e90da`](https://github.com/supabase-community/postgrest-py/commit/57e90dabd32e065b8651d74742817b48b366498a))

* Rename project to avoid collision ([`a5ff81b`](https://github.com/supabase-community/postgrest-py/commit/a5ff81bde0f38452b4d52c64c41b08b468deb80d))

* Update README.md and things ([`c77c5ea`](https://github.com/supabase-community/postgrest-py/commit/c77c5ea9d40d32fb8da3c6f21192c00687268e36))

* Poetry init ([`ec3df47`](https://github.com/supabase-community/postgrest-py/commit/ec3df475c35857cc5879c1cc0efd7305ee833a5f))

* Initial commit ([`d18b594`](https://github.com/supabase-community/postgrest-py/commit/d18b59465456b0b240d89dfe7236ad93f98c64bd))

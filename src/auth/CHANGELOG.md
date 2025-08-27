# CHANGELOG

## [2.12.3](https://github.com/supabase/auth-py/compare/v2.12.2...v2.12.3) (2025-07-03)


### Bug Fixes

* add missing email_redirect_to option ([#728](https://github.com/supabase/auth-py/issues/728)) ([7e63772](https://github.com/supabase/auth-py/commit/7e637729af6442ec64a9cff1785e7b099c1b4007))
* add missing nonce to the update_user method ([#731](https://github.com/supabase/auth-py/issues/731)) ([9db842a](https://github.com/supabase/auth-py/commit/9db842aba268c128db1d59a08de77c2c2c197aa3))

## [2.12.2](https://github.com/supabase/auth-py/compare/v2.12.1...v2.12.2) (2025-06-23)


### Bug Fixes

* add py.typed marker for type-checking support ([#721](https://github.com/supabase/auth-py/issues/721)) ([59fddd4](https://github.com/supabase/auth-py/commit/59fddd4faffca19f9f9d5523b72179ee32c90aa6))
* remove unused jwt key validation ([#725](https://github.com/supabase/auth-py/issues/725)) ([13008b3](https://github.com/supabase/auth-py/commit/13008b3977b1e9ad688c4c8b7f0f6b79523ebca3))
* sms mfa failure due to missing totp field ([#723](https://github.com/supabase/auth-py/issues/723)) ([8b81588](https://github.com/supabase/auth-py/commit/8b81588638f3cb4c972ba386ddf8d46c38ff712b))

## [2.12.1](https://github.com/supabase/auth-py/compare/v2.12.0...v2.12.1) (2025-05-15)


### Bug Fixes

* validate uuid on admin methods and fix wrong factor in delete_factor method ([#706](https://github.com/supabase/auth-py/issues/706)) ([1649956](https://github.com/supabase/auth-py/commit/1649956c3aca418eaa10b2434292b17f40565a8b))

## [2.12.0](https://github.com/supabase/auth-py/compare/v2.11.4...v2.12.0) (2025-03-26)


### Features

* add `get_claims` method ([#681](https://github.com/supabase/auth-py/issues/681)) ([f5c9926](https://github.com/supabase/auth-py/commit/f5c992608452b264d2b90277e384bd65fee98ee7))


### Bug Fixes

* enroll mfa totp ([#693](https://github.com/supabase/auth-py/issues/693)) ([ca9fcf3](https://github.com/supabase/auth-py/commit/ca9fcf3a1a0fbf99987e7e032a0eae542e4fd659))

## [2.11.4](https://github.com/supabase/auth-py/compare/v2.11.3...v2.11.4) (2025-02-18)


### Bug Fixes

* Remove unused deprecated files ([#675](https://github.com/supabase/auth-py/issues/675)) ([961628a](https://github.com/supabase/auth-py/commit/961628ada82c0ac4476e8cb89553b8502b506d81))

## [2.11.3](https://github.com/supabase/auth-py/compare/v2.11.2...v2.11.3) (2025-01-30)


### Bug Fixes

* move redirect_to into metadata for SSO authentication ([#671](https://github.com/supabase/auth-py/issues/671)) ([6226426](https://github.com/supabase/auth-py/commit/6226426c59449d2cd57765b9dfd199e83089dd8c))
* sign_out not clearing session when exception raised ([#665](https://github.com/supabase/auth-py/issues/665)) ([81a9d9e](https://github.com/supabase/auth-py/commit/81a9d9e5de91a515766d79a4e0a13d9f89cbfaf4))

## [2.11.2](https://github.com/supabase/auth-py/compare/v2.11.1...v2.11.2) (2025-01-24)


### Bug Fixes

* use query params for all httpx requests ([#662](https://github.com/supabase/auth-py/issues/662)) ([a7a9cea](https://github.com/supabase/auth-py/commit/a7a9cea1ceab302aabd07610244a54ce84221006))

## [2.11.1](https://github.com/supabase/auth-py/compare/v2.11.0...v2.11.1) (2024-12-30)


### Bug Fixes

* add email_address_invalid error code ([#644](https://github.com/supabase/auth-py/issues/644)) ([4926bd5](https://github.com/supabase/auth-py/commit/4926bd51cb616d7c974f7c6ad34471f2d38c3c88))
* set timer to be use daemon thread ([#647](https://github.com/supabase/auth-py/issues/647)) ([98de380](https://github.com/supabase/auth-py/commit/98de380bf5b90e594ef6560267d2c14a6001e3da))

## [2.11.0](https://github.com/supabase/auth-py/compare/v2.10.0...v2.11.0) (2024-11-22)


### Features

* Check if token is a JWT ([#623](https://github.com/supabase/auth-py/issues/623)) ([f435736](https://github.com/supabase/auth-py/commit/f435736de16dfa68543e76861c2742ca46c05cf6))

## [2.10.0](https://github.com/supabase/auth-py/compare/v2.9.3...v2.10.0) (2024-11-03)


### Features

* Check if url is an HTTP URL ([#620](https://github.com/supabase/auth-py/issues/620)) ([f0ccae5](https://github.com/supabase/auth-py/commit/f0ccae5fe6a8c012b8bcaf89bfc767d63feecbae))

## [2.9.3](https://github.com/supabase/auth-py/compare/v2.9.2...v2.9.3) (2024-10-18)


### Bug Fixes

* bump minimal version of Python to 3.9 ([#612](https://github.com/supabase/auth-py/issues/612)) ([30938a6](https://github.com/supabase/auth-py/commit/30938a6db97c5ee3eb4c27fd8d38b7437bc07fd7))
* Types to use Option[T] ([#609](https://github.com/supabase/auth-py/issues/609)) ([4484ea0](https://github.com/supabase/auth-py/commit/4484ea0f61149c75caff879161f63d390bf1ff1c))

## [2.9.2](https://github.com/supabase/auth-py/compare/v2.9.1...v2.9.2) (2024-10-06)


### Bug Fixes

* httpx minimum version update ([#606](https://github.com/supabase/auth-py/issues/606)) ([28be757](https://github.com/supabase/auth-py/commit/28be757561977f2138639089e29888e2be6d871e))

## [2.9.1](https://github.com/supabase/auth-py/compare/v2.9.0...v2.9.1) (2024-09-30)


### Bug Fixes

* mfa challenge channel field not required ([#603](https://github.com/supabase/auth-py/issues/603)) ([38a8696](https://github.com/supabase/auth-py/commit/38a8696058c4cc770a2a99b0ea1cf9649b2cea8c))

## [2.9.0](https://github.com/supabase/auth-py/compare/v2.8.1...v2.9.0) (2024-09-28)


### Features

* Proxy support ([#600](https://github.com/supabase/auth-py/issues/600)) ([574d615](https://github.com/supabase/auth-py/commit/574d615d6c0b93e455cfcb16560f409c021471f1))


### Bug Fixes

* **deps:** bump pydantic from 2.9.0 to 2.9.2 ([#598](https://github.com/supabase/auth-py/issues/598)) ([c865a98](https://github.com/supabase/auth-py/commit/c865a98cf10248433dff23c3f6a67fc3683766b0))

## [2.8.1](https://github.com/supabase/auth-py/compare/v2.8.0...v2.8.1) (2024-09-08)


### Bug Fixes

* **deps-dev:** bump cryptography from 43.0.0 to 43.0.1 ([#592](https://github.com/supabase/auth-py/issues/592)) ([79829d3](https://github.com/supabase/auth-py/commit/79829d3332c7d71c11dbc3adcdb8a89626144c4d))

## [2.8.0](https://github.com/supabase/auth-py/compare/v2.7.0...v2.8.0) (2024-09-02)


### Features

* add MFA Phone ([#578](https://github.com/supabase/auth-py/issues/578)) ([b2bb7a1](https://github.com/supabase/auth-py/commit/b2bb7a149b42da0460ace211f6a640d9fa9f13b5))
* add reauthenticate method ([#586](https://github.com/supabase/auth-py/issues/586)) ([d54feeb](https://github.com/supabase/auth-py/commit/d54feeb21006bfd5e5e1bdc039fac0aadab24e65))
* add resend method ([#587](https://github.com/supabase/auth-py/issues/587)) ([536ad2c](https://github.com/supabase/auth-py/commit/536ad2c28e1815a8a2f48821081bfca009e198f2))


### Bug Fixes

* update invite user by email option type ([#588](https://github.com/supabase/auth-py/issues/588)) ([2510230](https://github.com/supabase/auth-py/commit/2510230c4eaa45303b269d029cfe9a0ece6e8a4e))
* update password reset method name to match js lib ([#584](https://github.com/supabase/auth-py/issues/584)) ([d47daf1](https://github.com/supabase/auth-py/commit/d47daf1a0208c2df1a8993d37991f283f81f3221))

## [2.7.0](https://github.com/supabase/auth-py/compare/v2.6.2...v2.7.0) (2024-08-16)


### Features

* add error codes ([#556](https://github.com/supabase/auth-py/issues/556)) ([05dfb8a](https://github.com/supabase/auth-py/commit/05dfb8aadeb3a3321fbcc01c0e3fe8ce49f3cccd))

## v2.6.2 (2024-08-09)

### Chore

* chore(deps-dev): bump faker from 26.0.0 to 26.1.0 (#557) ([`86ce4c1`](https://github.com/supabase/auth-py/commit/86ce4c1cbc458aa506b8c2ad8e2f01dfdf6cb68b))

* chore: update ci pipeline ([`06de3ac`](https://github.com/supabase/auth-py/commit/06de3acb7815c4b50e766bab2299cb31d8312529))

* chore(deps-dev): bump pytest from 8.3.1 to 8.3.2 (#555) ([`8a3362a`](https://github.com/supabase/auth-py/commit/8a3362a1813f01958182b0c2dde1fb3a9134df2a))

* chore(deps-dev): bump pytest from 8.3.1 to 8.3.2

Bumps [pytest](https://github.com/pytest-dev/pytest) from 8.3.1 to 8.3.2.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/8.3.1...8.3.2)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`02fbbfe`](https://github.com/supabase/auth-py/commit/02fbbfe92bb903444770971b9764dd22b9d773fb))

### Ci

* ci: revert PAT changes (#568) ([`a5f5a4b`](https://github.com/supabase/auth-py/commit/a5f5a4bc4661a357e059907f54d0f473fcebc46c))

* ci: remove PAT (#566) ([`69610cf`](https://github.com/supabase/auth-py/commit/69610cfe89cb4d3fd99a8c908f07bdcd06ea097a))

* ci: remove PAT ([`4b5a3b5`](https://github.com/supabase/auth-py/commit/4b5a3b56d6cbc4fcf8b1f7eb59b8186bbca81506))

* ci: remove PAT (#565) ([`c2b20e0`](https://github.com/supabase/auth-py/commit/c2b20e07f0682d53f424c58a64bb80963efe046f))

### Fix

* fix: update ci pipeline (#559) ([`c914dd3`](https://github.com/supabase/auth-py/commit/c914dd32706257fe37072580760f69fb3ea174d6))

* fix: update types (#558) ([`486f3e0`](https://github.com/supabase/auth-py/commit/486f3e04845e1f323ae12617c2d1d18847f658bc))

* fix: add role, password_hash &amp; id types to admin user attributes ([`2adcd7f`](https://github.com/supabase/auth-py/commit/2adcd7f349a86e4af55961ff48e374e7c8221148))

* fix: add fly, linkedin_oidc and slack_oidc provider type ([`c13e2c7`](https://github.com/supabase/auth-py/commit/c13e2c78522dc77f0e3591cff2c71f9b793526a1))

### Unknown

* update docker compose command call ([`41cefcf`](https://github.com/supabase/auth-py/commit/41cefcf441dedd78d5e0531160588705b8da560b))

## v2.6.1 (2024-07-24)

### Chore

* chore(release): bump version to v2.6.1 ([`4b5aa15`](https://github.com/supabase/auth-py/commit/4b5aa15996797ee908b5ab652757dbeca37a9aad))

* chore(deps-dev): bump pytest from 8.2.2 to 8.3.1 (#551) ([`964826c`](https://github.com/supabase/auth-py/commit/964826c2ae6baf823d491c38b30cba6392b4aa77))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.5 to 9.8.6 (#552) ([`fd92320`](https://github.com/supabase/auth-py/commit/fd923204c5da0cae480636ac12d3286e292f88ee))

* chore(deps-dev): bump python-semantic-release from 9.8.5 to 9.8.6 (#550) ([`625f4af`](https://github.com/supabase/auth-py/commit/625f4af3b773f242483e4ba10f67e7e0452c28cc))

* chore(deps-dev): bump pytest-asyncio from 0.23.7 to 0.23.8 (#549) ([`0a7a766`](https://github.com/supabase/auth-py/commit/0a7a76691e4597a9417afcbc016d24642329bcc9))

### Fix

* fix: add is_anonymous type to the user model (#553) ([`c37913f`](https://github.com/supabase/auth-py/commit/c37913f013be27231bb3347d29334d6af8024eb3))

## v2.6.0 (2024-07-17)

### Chore

* chore(release): bump version to v2.6.0 ([`0899975`](https://github.com/supabase/auth-py/commit/0899975e9d964ba3ab525bca89fa487ca99b90d5))

### Feature

* feat: add sign_in_with_id_token method (#548) ([`b7e2c2c`](https://github.com/supabase/auth-py/commit/b7e2c2c2b9dd949aa0931c3b90ed66b5de46825e))

## v2.5.5 (2024-07-14)

### Chore

* chore(release): bump version to v2.5.5 ([`79a24f0`](https://github.com/supabase/auth-py/commit/79a24f0d52b07693102812fa0934ae03b9bed898))

* chore(deps-dev): bump zipp from 3.18.1 to 3.19.1 (#546) ([`1c807cb`](https://github.com/supabase/auth-py/commit/1c807cb21ebc88cb95c98c8c12ca9b4e71c6da9d))

* chore(deps-dev): bump zipp from 3.18.1 to 3.19.1

Bumps [zipp](https://github.com/jaraco/zipp) from 3.18.1 to 3.19.1.
- [Release notes](https://github.com/jaraco/zipp/releases)
- [Changelog](https://github.com/jaraco/zipp/blob/main/NEWS.rst)
- [Commits](https://github.com/jaraco/zipp/compare/v3.18.1...v3.19.1)

---
updated-dependencies:
- dependency-name: zipp
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`4052673`](https://github.com/supabase/auth-py/commit/4052673857464876d5703d3c73c9af0b0653d4dc))

* chore(deps-dev): bump python-semantic-release from 9.8.3 to 9.8.5 (#544) ([`ff1046e`](https://github.com/supabase/auth-py/commit/ff1046ef2b78c14d6175e511e78cb6e80091425b))

* chore(deps-dev): bump python-semantic-release from 9.8.3 to 9.8.5

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.8.3 to 9.8.5.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.8.3...v9.8.5)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`dd38cdc`](https://github.com/supabase/auth-py/commit/dd38cdc39dc147850851953017f20ff568621a87))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.3 to 9.8.5 (#545) ([`32ac690`](https://github.com/supabase/auth-py/commit/32ac690dbb8a70550cfec8b5b12c8b74b79c69b5))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.8.3 to 9.8.5.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.8.3...v9.8.5)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`07042e6`](https://github.com/supabase/auth-py/commit/07042e603adcce30dc76f1fd78b1c8b4209a0a31))

* chore(deps): bump certifi from 2024.2.2 to 2024.7.4 (#542) ([`d960b0f`](https://github.com/supabase/auth-py/commit/d960b0f6feb91415c27b805bf1fe09453df9660c))

* chore(deps): bump certifi from 2024.2.2 to 2024.7.4

Bumps [certifi](https://github.com/certifi/python-certifi) from 2024.2.2 to 2024.7.4.
- [Commits](https://github.com/certifi/python-certifi/compare/2024.02.02...2024.07.04)

---
updated-dependencies:
- dependency-name: certifi
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`95f06c3`](https://github.com/supabase/auth-py/commit/95f06c326118febd77a8464eadc0726c6a274c75))

* chore(deps): bump pydantic from 2.7.4 to 2.8.2 (#539) ([`d0798d6`](https://github.com/supabase/auth-py/commit/d0798d69fc45e6abc20754be253d037265d7733c))

* chore(deps): bump pydantic from 2.7.4 to 2.8.2

Bumps [pydantic](https://github.com/pydantic/pydantic) from 2.7.4 to 2.8.2.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/v2.8.2/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v2.7.4...v2.8.2)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`e22a177`](https://github.com/supabase/auth-py/commit/e22a1777225a64c283e4dfd261e8ad3efbf5be0e))

* chore(deps-dev): bump faker from 25.9.1 to 26.0.0 (#535) ([`f2fa2a9`](https://github.com/supabase/auth-py/commit/f2fa2a9eeaac2119e1fa2c6dc646649e926e32b1))

* chore(deps-dev): bump faker from 25.9.1 to 26.0.0

Bumps [faker](https://github.com/joke2k/faker) from 25.9.1 to 26.0.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v25.9.1...v26.0.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`1fe332f`](https://github.com/supabase/auth-py/commit/1fe332fa783f71a25c67f7db42484cb029d77bfb))

### Fix

* fix: enable HTTP2 (#534) ([`73ea013`](https://github.com/supabase/auth-py/commit/73ea0131dc326df85adc927c1f908ba11adf4d25))

## v2.5.4 (2024-06-23)

### Chore

* chore(release): bump version to v2.5.4 ([`ca6e6c9`](https://github.com/supabase/auth-py/commit/ca6e6c97c1071fc13f7efa58269b936065d2395e))

### Fix

* fix: add await to async call for anonymous sign in request (#532) ([`45cfe25`](https://github.com/supabase/auth-py/commit/45cfe25f10cb63134cd297b34bae419687cb64b6))

### Unknown

* add missing await ([`412449a`](https://github.com/supabase/auth-py/commit/412449ac83d72ad05415cbfb63f91821555ed997))

* add await ([`5520ad8`](https://github.com/supabase/auth-py/commit/5520ad839ea8071801e00e5c10294958b31dd3e4))

* add await to async call for anonymous sign in request ([`4734d0d`](https://github.com/supabase/auth-py/commit/4734d0df974d2a24a8cd9f468584343d5f7ea9c3))

## v2.5.3 (2024-06-23)

### Chore

* chore(release): bump version to v2.5.3 ([`b194f07`](https://github.com/supabase/auth-py/commit/b194f07c5cbe5e7b813e968a928e99cc5c6070e0))

### Fix

* fix: update property name for should_create_user (#531) ([`388fcba`](https://github.com/supabase/auth-py/commit/388fcbac63bc96119c3c3ece91f28578e384a38b))

### Unknown

* update peoperty name for should_create_user ([`4bc09ef`](https://github.com/supabase/auth-py/commit/4bc09ef2f61ec55e01485dfa606a9d6631e607a5))

## v2.5.2 (2024-06-21)

### Chore

* chore(release): bump version to v2.5.2 ([`00a04c6`](https://github.com/supabase/auth-py/commit/00a04c6637ccd2fb84700cea13dd4aaf705cc443))

* chore(deps-dev): bump faker from 25.8.0 to 25.9.1 (#529) ([`c530238`](https://github.com/supabase/auth-py/commit/c530238b2574921545980fc0bf170b21b6bef20c))

* chore(deps-dev): bump faker from 25.8.0 to 25.9.1

Bumps [faker](https://github.com/joke2k/faker) from 25.8.0 to 25.9.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v25.8.0...v25.9.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`1651b74`](https://github.com/supabase/auth-py/commit/1651b74b63b61511ddd0a473002cf438c07285b5))

### Fix

* fix: link identity methods now working ([`2e95db8`](https://github.com/supabase/auth-py/commit/2e95db8bcf0ba323b330ef56f1928f72523e0b0e))

### Unknown

* fix all link identity methods ([`3570ace`](https://github.com/supabase/auth-py/commit/3570aced5ebcb22f448e987d4a157e7b6d2f0b29))

## v2.5.1 (2024-06-20)

### Chore

* chore(release): bump version to v2.5.1 ([`6563daf`](https://github.com/supabase/auth-py/commit/6563daf5bd249718a73872a33421b773076e05e7))

* chore(deps-dev): bump python-semantic-release from 9.8.1 to 9.8.3 (#526) ([`b7d5755`](https://github.com/supabase/auth-py/commit/b7d5755318c3a7929c057ef8a4ce0f9ac765389c))

* chore(deps-dev): bump python-semantic-release from 9.8.1 to 9.8.3

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.8.1 to 9.8.3.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.8.1...v9.8.3)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`8e5ec68`](https://github.com/supabase/auth-py/commit/8e5ec68f61613bfe60c704b0f393a1bdf6c1b276))

* chore(deps-dev): bump faker from 25.4.0 to 25.8.0 (#519) ([`e4fc889`](https://github.com/supabase/auth-py/commit/e4fc8891bcafc94688e75a305dfc85d9fbbb60e9))

* chore(deps-dev): bump faker from 25.4.0 to 25.8.0

Bumps [faker](https://github.com/joke2k/faker) from 25.4.0 to 25.8.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v25.4.0...v25.8.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`c730281`](https://github.com/supabase/auth-py/commit/c7302817c2fca068811fa507d582ce9ce7465494))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.1 to 9.8.3 (#527) ([`eda2715`](https://github.com/supabase/auth-py/commit/eda2715283b589942ce85c0a83708190fa595d0b))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.8.1 to 9.8.3.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.8.1...v9.8.3)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`941a87b`](https://github.com/supabase/auth-py/commit/941a87b3a62bb249fe01683e814a6f3700cc24f5))

* chore(deps-dev): bump urllib3 from 2.2.1 to 2.2.2 (#525) ([`8137d24`](https://github.com/supabase/auth-py/commit/8137d241a12f24e0dac3554c1ec7f34e504aaf87))

* chore(deps-dev): bump urllib3 from 2.2.1 to 2.2.2

Bumps [urllib3](https://github.com/urllib3/urllib3) from 2.2.1 to 2.2.2.
- [Release notes](https://github.com/urllib3/urllib3/releases)
- [Changelog](https://github.com/urllib3/urllib3/blob/main/CHANGES.rst)
- [Commits](https://github.com/urllib3/urllib3/compare/2.2.1...2.2.2)

---
updated-dependencies:
- dependency-name: urllib3
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`097d3ac`](https://github.com/supabase/auth-py/commit/097d3ac788e4650358753dde48d93c3204940029))

* chore(deps): bump pydantic from 2.7.3 to 2.7.4 (#521) ([`0647d43`](https://github.com/supabase/auth-py/commit/0647d43940df2fc387dde01092cb0ea018711082))

* chore(deps): bump pydantic from 2.7.3 to 2.7.4

Bumps [pydantic](https://github.com/pydantic/pydantic) from 2.7.3 to 2.7.4.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v2.7.3...v2.7.4)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`f7c60e7`](https://github.com/supabase/auth-py/commit/f7c60e727830bb1644416789a32ca0d3173658bc))

* chore(deps-dev): bump pytest from 8.2.1 to 8.2.2 (#516) ([`2c40cd6`](https://github.com/supabase/auth-py/commit/2c40cd6fdbfae74ac9c104d307a91d6dc5b21195))

* chore(deps-dev): bump pytest from 8.2.1 to 8.2.2

Bumps [pytest](https://github.com/pytest-dev/pytest) from 8.2.1 to 8.2.2.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/8.2.1...8.2.2)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`e2f6c0a`](https://github.com/supabase/auth-py/commit/e2f6c0ab7bb962e2ed57a992d90bea91f91b2dd6))

### Fix

* fix: add channel to sign_in and sign_up options ([`498640d`](https://github.com/supabase/auth-py/commit/498640dfa8804257bb62675078dc0487aacc879d))

### Unknown

* Update supabase_auth/_sync/gotrue_client.py

Co-authored-by: Joel Lee &lt;lee.yi.jie.joel@gmail.com&gt; ([`1df49ef`](https://github.com/supabase/auth-py/commit/1df49ef55ed64cce0a9afa3295e7c8c56b9fd450))

* Update supabase_auth/_async/gotrue_client.py

Co-authored-by: Joel Lee &lt;lee.yi.jie.joel@gmail.com&gt; ([`f44450d`](https://github.com/supabase/auth-py/commit/f44450dc7294ab0bf25e16f81b5ef8423120264d))

* format with pre-commit formatter ([`97b534b`](https://github.com/supabase/auth-py/commit/97b534b9e5fd1ec5a04c0f7520aa078029de76a0))

* change option name from `redirect_to` to `email_redirect_to` ([`019da4f`](https://github.com/supabase/auth-py/commit/019da4fdbcc4ae92f227322ebd7a3485479d9943))

* add sync version ([`4814aeb`](https://github.com/supabase/auth-py/commit/4814aeb4b8c446dacc1086300260dcfefac76210))

* add channel to sign_in and sign_up options ([`5a1c44a`](https://github.com/supabase/auth-py/commit/5a1c44afebe5d01b31bacd25423f456baab35ef8))

## v2.5.0 (2024-06-20)

### Chore

* chore(release): bump version to v2.5.0 ([`a92ec80`](https://github.com/supabase/auth-py/commit/a92ec8068d8751d0864a7cde2cdb62bfb39c7071))

* chore(deps-dev): bump python-semantic-release from 9.8.0 to 9.8.1 (#515) ([`98006ed`](https://github.com/supabase/auth-py/commit/98006ed08d07bb2414b261ba3c926f29c0de3645))

* chore(deps-dev): bump python-semantic-release from 9.8.0 to 9.8.1

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.8.0 to 9.8.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.8.0...v9.8.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`f28f6a2`](https://github.com/supabase/auth-py/commit/f28f6a29175a4af0dd00963b9718c65eda5d937a))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.0 to 9.8.1 (#514) ([`4458982`](https://github.com/supabase/auth-py/commit/445898229a3c504324a33a67d2bd9709bb8048ea))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.8.0 to 9.8.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.8.0...v9.8.1)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`960d593`](https://github.com/supabase/auth-py/commit/960d593f28be3cca582812a07d1fcfda6a3bb911))

### Feature

* feat: add anonymous sign in ([`2406d7d`](https://github.com/supabase/auth-py/commit/2406d7d90394cf69bf772916c2232ae8aa8afe13))

### Unknown

* update postgres version for infra ([`ad2179b`](https://github.com/supabase/auth-py/commit/ad2179b1c042c8faf1b1cdc322d8c9f9d5aae9e7))

* update async client and type naming ([`85f94f2`](https://github.com/supabase/auth-py/commit/85f94f27320af3438748fe261a752a29b03a2c24))

* Add Anonymous login ([`f3d35c7`](https://github.com/supabase/auth-py/commit/f3d35c72d3dc334d5963d4f9a57137eeacdff873))

## v2.4.4 (2024-06-04)

### Chore

* chore(release): bump version to v2.4.4 ([`1ed3dd7`](https://github.com/supabase/auth-py/commit/1ed3dd7389499ff2f8793f70adf51250cfe55964))

* chore(deps): bump pydantic from 2.7.2 to 2.7.3 (#513) ([`4a5e21e`](https://github.com/supabase/auth-py/commit/4a5e21e93f14a76d9a46b218163a2e9538537440))

* chore(deps): bump pydantic from 2.7.2 to 2.7.3

Bumps [pydantic](https://github.com/pydantic/pydantic) from 2.7.2 to 2.7.3.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v2.7.2...v2.7.3)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7b5269c`](https://github.com/supabase/auth-py/commit/7b5269c4254d598a41507f45ec4893cfa20a14ac))

* chore(deps-dev): bump faker from 25.3.0 to 25.4.0 (#512) ([`daafb74`](https://github.com/supabase/auth-py/commit/daafb74a4970a6fcbd9dc36ef757079616d1f150))

* chore(deps-dev): bump faker from 25.3.0 to 25.4.0

Bumps [faker](https://github.com/joke2k/faker) from 25.3.0 to 25.4.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v25.3.0...v25.4.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`35a8b14`](https://github.com/supabase/auth-py/commit/35a8b14dc5f6657e63d21de29dd2b60a29f07eed))

* chore(deps-dev): bump faker from 25.2.0 to 25.3.0 (#510) ([`e7fdc2d`](https://github.com/supabase/auth-py/commit/e7fdc2d978c95638dfc7a27676aabcba44d2a80d))

* chore(deps-dev): bump faker from 25.2.0 to 25.3.0

Bumps [faker](https://github.com/joke2k/faker) from 25.2.0 to 25.3.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v25.2.0...v25.3.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`0e55988`](https://github.com/supabase/auth-py/commit/0e55988f74c908c0fee5b629939a8fab3305052c))

### Fix

* fix: follow redirects ([`1fa7fd2`](https://github.com/supabase/auth-py/commit/1fa7fd24c84594a6d63322a685aeccdc4e301af1))

### Unknown

* Fix code style ([`4a18e21`](https://github.com/supabase/auth-py/commit/4a18e212fd5f9b9f25e516735ab92232bf49e5d7))

* Fix code style ([`55a415b`](https://github.com/supabase/auth-py/commit/55a415b993e503bed5a564b8db1490a26e6ad51f))

* Fix code style ([`645560d`](https://github.com/supabase/auth-py/commit/645560d940243bee5f2b15e59a3b50cd0ca11c5c))

* ReSync, fix merges ([`96129b6`](https://github.com/supabase/auth-py/commit/96129b65d3c5438aac5a67852978a7f7cf0b20dd))

## v2.4.3 (2024-06-01)

### Chore

* chore(release): bump version to v2.4.3 ([`7316cf5`](https://github.com/supabase/auth-py/commit/7316cf56dce5db188690c58f8a30e0cd4568105b))

* chore(deps): bump pydantic from 2.7.1 to 2.7.2 (#509) ([`5d433fe`](https://github.com/supabase/auth-py/commit/5d433fe665fcc08dad5dc49c4225a0d53b5fa7e6))

* chore(deps): bump pydantic from 2.7.1 to 2.7.2

Bumps [pydantic](https://github.com/pydantic/pydantic) from 2.7.1 to 2.7.2.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v2.7.1...v2.7.2)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`9f80a51`](https://github.com/supabase/auth-py/commit/9f80a51c2550e305c79eac312d582c1b8a516bee))

* chore(ci): bump python-semantic-release/python-semantic-release from 9.7.3 to 9.8.0 (#508) ([`a3037d9`](https://github.com/supabase/auth-py/commit/a3037d94cdfe0b419b2d8b3785783f36c843196c))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.7.3 to 9.8.0.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.7.3...v9.8.0)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7b21e47`](https://github.com/supabase/auth-py/commit/7b21e47fdc240d30add37ca1612105fac8777e4e))

* chore(deps-dev): bump python-semantic-release from 9.7.3 to 9.8.0 (#507) ([`fe033c5`](https://github.com/supabase/auth-py/commit/fe033c5b803a64637acc819d84a83be939cbfffd))

* chore(deps-dev): bump python-semantic-release from 9.7.3 to 9.8.0

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.7.3 to 9.8.0.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.7.3...v9.8.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`859379b`](https://github.com/supabase/auth-py/commit/859379bd86a763ebe8f82a2eb4492078b71fcd8a))

* chore(deps-dev): bump requests from 2.31.0 to 2.32.0 (#502) ([`16e571f`](https://github.com/supabase/auth-py/commit/16e571fc19168314d82074523de6f246bdd74960))

* chore(deps-dev): bump pytest from 8.1.1 to 8.2.1 (#501) ([`56a3842`](https://github.com/supabase/auth-py/commit/56a3842928e942b8d35946de27d99050c277de9b))

* chore(deps-dev): bump pytest from 8.1.1 to 8.2.1

Bumps [pytest](https://github.com/pytest-dev/pytest) from 8.1.1 to 8.2.1.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/8.1.1...8.2.1)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`1e32b5c`](https://github.com/supabase/auth-py/commit/1e32b5ccedd7d1c77bcadaf01ab1a871f3d326eb))

* chore(deps-dev): bump pytest-asyncio from 0.23.6 to 0.23.7 (#500) ([`c0c17f8`](https://github.com/supabase/auth-py/commit/c0c17f86e8f1048818a23ef92bfcd08a8bd16879))

* chore(deps-dev): bump pytest-asyncio from 0.23.6 to 0.23.7

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.23.6 to 0.23.7.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.23.6...v0.23.7)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`8a72775`](https://github.com/supabase/auth-py/commit/8a72775dc968a9c81a18342422fa710b7987a651))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.5.0 to 9.7.3 (#499) ([`1b1fc19`](https://github.com/supabase/auth-py/commit/1b1fc19f28934c1d716e37153953a237b56a8bd0))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.5.0 to 9.7.3.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.5.0...v9.7.3)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`29ee762`](https://github.com/supabase/auth-py/commit/29ee76258bba9a0b4a1dd2249f3493c8d30e211e))

* chore(deps-dev): bump python-semantic-release from 9.5.0 to 9.7.3 (#498) ([`1b6fadf`](https://github.com/supabase/auth-py/commit/1b6fadf02f8d6d77bee9bfedaca5a85731173c67))

* chore(deps-dev): bump python-semantic-release from 9.5.0 to 9.7.3

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.5.0 to 9.7.3.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.5.0...v9.7.3)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`039d6a5`](https://github.com/supabase/auth-py/commit/039d6a5c5ec28cb4d9025020e33bf3f9bef801d5))

* chore(deps-dev): bump faker from 24.14.1 to 25.2.0 (#497) ([`67b6a58`](https://github.com/supabase/auth-py/commit/67b6a581d45e027a815b8b3f7bc6b3c9068f47b4))

* chore(deps-dev): bump faker from 24.14.1 to 25.2.0

Bumps [faker](https://github.com/joke2k/faker) from 24.14.1 to 25.2.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v24.14.1...v25.2.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`ce825c8`](https://github.com/supabase/auth-py/commit/ce825c80646943078d54743cdebe3e2f4f38fde9))

* chore(deps-dev): bump jinja2 from 3.1.3 to 3.1.4 (#491) ([`a030a33`](https://github.com/supabase/auth-py/commit/a030a33675ad08d37a729a9835c619e8550acbd2))

* chore(deps-dev): bump jinja2 from 3.1.3 to 3.1.4

Bumps [jinja2](https://github.com/pallets/jinja) from 3.1.3 to 3.1.4.
- [Release notes](https://github.com/pallets/jinja/releases)
- [Changelog](https://github.com/pallets/jinja/blob/main/CHANGES.rst)
- [Commits](https://github.com/pallets/jinja/compare/3.1.3...3.1.4)

---
updated-dependencies:
- dependency-name: jinja2
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`71f1a6e`](https://github.com/supabase/auth-py/commit/71f1a6ef3cd8ed0595f0e7f4b588227f225cad31))

* chore(deps-dev): bump faker from 24.9.0 to 24.14.1 (#480) ([`9776d6a`](https://github.com/supabase/auth-py/commit/9776d6adcce8d8ca28e826d14b05743a1a63e132))

* chore(deps-dev): bump faker from 24.9.0 to 24.14.1

Bumps [faker](https://github.com/joke2k/faker) from 24.9.0 to 24.14.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v24.9.0...v24.14.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`e7e3b58`](https://github.com/supabase/auth-py/commit/e7e3b58bb855145bc8b7aa1cf36065e7da3ea849))

* chore(deps-dev): bump black from 24.3.0 to 24.4.2 (#478) ([`ac8339b`](https://github.com/supabase/auth-py/commit/ac8339bee847677fdf1bc8cbe5c67098e8651afd))

* chore(deps-dev): bump black from 24.3.0 to 24.4.2

Bumps [black](https://github.com/psf/black) from 24.3.0 to 24.4.2.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/24.3.0...24.4.2)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`db0d0e9`](https://github.com/supabase/auth-py/commit/db0d0e999fddfeca3684d46fcbba3ebe5d015ab3))

* chore(deps): bump pydantic from 2.7.0 to 2.7.1 (#476) ([`339155a`](https://github.com/supabase/auth-py/commit/339155a60d3047c85fef907961a409ec5113e2b2))

* chore(deps): bump pydantic from 2.7.0 to 2.7.1

Bumps [pydantic](https://github.com/pydantic/pydantic) from 2.7.0 to 2.7.1.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v2.7.0...v2.7.1)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`e0c7dac`](https://github.com/supabase/auth-py/commit/e0c7dac96076ff5d30b85a7f4982f690512cb89e))

* chore(deps-dev): bump python-semantic-release from 9.4.1 to 9.5.0 (#475) ([`8900536`](https://github.com/supabase/auth-py/commit/8900536a649aa40badb9331f4ee304d8cfaa83d9))

* chore(deps-dev): bump python-semantic-release from 9.4.1 to 9.5.0

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.4.1 to 9.5.0.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.4.1...v9.5.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`aced040`](https://github.com/supabase/auth-py/commit/aced040ce04afd520c34e6f8502a995f847e9838))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.4.1 to 9.5.0 (#474) ([`1d951b6`](https://github.com/supabase/auth-py/commit/1d951b6ed982a92ca85abed4eaedefd7ac0e1017))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.4.1 to 9.5.0.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.4.1...v9.5.0)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`d28719f`](https://github.com/supabase/auth-py/commit/d28719fae2529c5b781954264387b82e96022405))

* chore(deps-dev): bump faker from 24.4.0 to 24.9.0 (#469) ([`9ae0b1d`](https://github.com/supabase/auth-py/commit/9ae0b1d51bb08b3396e0c1b66526d63565f108a3))

* chore(deps-dev): bump faker from 24.4.0 to 24.9.0

Bumps [faker](https://github.com/joke2k/faker) from 24.4.0 to 24.9.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v24.4.0...v24.9.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`8db5aab`](https://github.com/supabase/auth-py/commit/8db5aab39588e66f8a2fd51bb1644cb6fd103925))

* chore(deps): bump pydantic from 2.6.4 to 2.7.0 (#468) ([`6cee4e2`](https://github.com/supabase/auth-py/commit/6cee4e28d7ef97f736fa0f260dfc65c203676e85))

* chore(deps): bump pydantic from 2.6.4 to 2.7.0

Bumps [pydantic](https://github.com/pydantic/pydantic) from 2.6.4 to 2.7.0.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v2.6.4...v2.7.0)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`1b888da`](https://github.com/supabase/auth-py/commit/1b888da2bf670cdd9017b26ac57eb3760e9d3c77))

* chore(deps): bump idna from 3.6 to 3.7 (#467) ([`75feed7`](https://github.com/supabase/auth-py/commit/75feed766c44dd5581989fb3244ab74cc5f088d3))

* chore(deps): bump idna from 3.6 to 3.7

Bumps [idna](https://github.com/kjd/idna) from 3.6 to 3.7.
- [Release notes](https://github.com/kjd/idna/releases)
- [Changelog](https://github.com/kjd/idna/blob/master/HISTORY.rst)
- [Commits](https://github.com/kjd/idna/compare/v3.6...v3.7)

---
updated-dependencies:
- dependency-name: idna
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`e9fe838`](https://github.com/supabase/auth-py/commit/e9fe838da1ba1e6c095231e8197b726aa2e7af5f))

* chore(deps-dev): bump python-semantic-release from 9.4.0 to 9.4.1 (#464) ([`d659e82`](https://github.com/supabase/auth-py/commit/d659e8248242671648d3d2c1e69af9afea47a77f))

* chore(deps-dev): bump python-semantic-release from 9.4.0 to 9.4.1

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.4.0 to 9.4.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.4.0...v9.4.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`13feeae`](https://github.com/supabase/auth-py/commit/13feeae252b6a11c2a67a3724b2cca44f4e57688))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.4.0 to 9.4.1 (#463) ([`066014e`](https://github.com/supabase/auth-py/commit/066014e59ce2e4e8364aeb10352d263846a6902f))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.4.0 to 9.4.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.4.0...v9.4.1)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`b536cf6`](https://github.com/supabase/auth-py/commit/b536cf6676fbdd4d7bd4eb0a5beb6f98e6f7bcc2))

* chore(deps-dev): bump python-semantic-release from 9.3.1 to 9.4.0 (#462) ([`abf77ea`](https://github.com/supabase/auth-py/commit/abf77ea9702425f43b3efef9053b045dd6ca34c9))

* chore(deps-dev): bump python-semantic-release from 9.3.1 to 9.4.0

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.3.1 to 9.4.0.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.3.1...v9.4.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`05b6f2d`](https://github.com/supabase/auth-py/commit/05b6f2da2059cf79e579e8274e2ba260388b3409))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.3.1 to 9.4.0 (#461) ([`d11910c`](https://github.com/supabase/auth-py/commit/d11910cc387fc907c10ace25fc09db935b039386))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.3.1 to 9.4.0.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.3.1...v9.4.0)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`4031e43`](https://github.com/supabase/auth-py/commit/4031e43a322a759c5ffb3b626cb43c575b2378ec))

* chore(deps-dev): bump pytest-cov from 4.1.0 to 5.0.0 (#458) ([`17e6587`](https://github.com/supabase/auth-py/commit/17e658735512d3dfe1ea021ea24a48bd4e716b5f))

* chore(deps-dev): bump pytest-cov from 4.1.0 to 5.0.0

Bumps [pytest-cov](https://github.com/pytest-dev/pytest-cov) from 4.1.0 to 5.0.0.
- [Changelog](https://github.com/pytest-dev/pytest-cov/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest-cov/compare/v4.1.0...v5.0.0)

---
updated-dependencies:
- dependency-name: pytest-cov
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`10b44fe`](https://github.com/supabase/auth-py/commit/10b44fe5795ddfe015807880b68c875ac57fea58))

* chore(deps): bump abatilo/actions-poetry from 2 to 3 (#460) ([`4376a7a`](https://github.com/supabase/auth-py/commit/4376a7ae7d259991c97da019cdbe39dcb0a35a2b))

* chore(deps): bump abatilo/actions-poetry from 2 to 3

Bumps [abatilo/actions-poetry](https://github.com/abatilo/actions-poetry) from 2 to 3.
- [Release notes](https://github.com/abatilo/actions-poetry/releases)
- [Changelog](https://github.com/abatilo/actions-poetry/blob/master/.releaserc)
- [Commits](https://github.com/abatilo/actions-poetry/compare/v2...v3)

---
updated-dependencies:
- dependency-name: abatilo/actions-poetry
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`cac82ad`](https://github.com/supabase/auth-py/commit/cac82adc513e9217fcc5e24c45f1cb7f804abad0))

* chore(deps): bump actions/cache from 3 to 4 (#459) ([`67bc67f`](https://github.com/supabase/auth-py/commit/67bc67fb005e1d318fdbe2979afd22e689492044))

* chore(deps): bump actions/cache from 3 to 4

Bumps [actions/cache](https://github.com/actions/cache) from 3 to 4.
- [Release notes](https://github.com/actions/cache/releases)
- [Changelog](https://github.com/actions/cache/blob/main/RELEASES.md)
- [Commits](https://github.com/actions/cache/compare/v3...v4)

---
updated-dependencies:
- dependency-name: actions/cache
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7e1f6f7`](https://github.com/supabase/auth-py/commit/7e1f6f707e545be93bf8479520450fb1e2c59aef))

* chore(deps-dev): bump faker from 23.3.0 to 24.4.0 (#456) ([`1562b15`](https://github.com/supabase/auth-py/commit/1562b15aaddc5aa7bfb0043b4fcc4db0dda91779))

* chore(deps-dev): bump faker from 23.3.0 to 24.4.0

Bumps [faker](https://github.com/joke2k/faker) from 23.3.0 to 24.4.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v23.3.0...v24.4.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`d44b0ea`](https://github.com/supabase/auth-py/commit/d44b0ea2143154dca08b4554a337a024c80ddf2f))

### Fix

* fix: add &#34;verify&#34; flag to the creation of client ([`12f2396`](https://github.com/supabase/auth-py/commit/12f239668a5e49723e6fc92f4f1b07cf7d8f0c87))

### Unknown

* Fix #320 ([`e3862b9`](https://github.com/supabase/auth-py/commit/e3862b951cb16dd7c80617925f93febf7be57cd8))

* Fix #320 ([`e6203f6`](https://github.com/supabase/auth-py/commit/e6203f68ef91b74830c438575bd1ec89bae159cb))

* Fix #320 ([`d3ee089`](https://github.com/supabase/auth-py/commit/d3ee08910db712c729ddf05c27ef3e41a8fc7951))

* Fix #320 ([`339fb59`](https://github.com/supabase/auth-py/commit/339fb591d855612da451266d4f9daeab973865f6))

* Fix #320 ([`05d9fe9`](https://github.com/supabase/auth-py/commit/05d9fe9683699038df9007fa7b0f9ba763c81fed))

* Fix #320 ([`eba8528`](https://github.com/supabase/auth-py/commit/eba8528d749f7887f853072e586494dceace64a7))

* Fix #320 ([`2940262`](https://github.com/supabase/auth-py/commit/29402627fea628329018718e6434c761ae3375f6))

* Fix #320 ([`cf2f9be`](https://github.com/supabase/auth-py/commit/cf2f9be0c39b841ea6971e223b12cb580e32dd09))

* 

---
updated-dependencies:
- dependency-name: requests
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`a2423da`](https://github.com/supabase/auth-py/commit/a2423da474b3abf5bb5512b98c9aef508f6d5722))

* Fixes and style (#488) ([`7856d01`](https://github.com/supabase/auth-py/commit/7856d014fbec6a49264d57e579701f50bf434239))

* Fixes and style ([`4f723eb`](https://github.com/supabase/auth-py/commit/4f723eb7be48c1dda251918b4c3241f8ff6c78e7))

* Fixes and style ([`0165846`](https://github.com/supabase/auth-py/commit/01658461ab7c1fe20c21e6093a5871b2da4f51c7))

* Update .pre-commit-config.yaml (#487) ([`e00452c`](https://github.com/supabase/auth-py/commit/e00452c242b1b313bd80262238bb5166c3a16874))

* Update .pre-commit-config.yaml ([`9824403`](https://github.com/supabase/auth-py/commit/9824403d785269340cc29dc49e840b743a2d2974))

* Update .pre-commit-config.yaml ([`d0ceba0`](https://github.com/supabase/auth-py/commit/d0ceba0fac7bab61c76f49e6958ef31ae76ed361))

* Update .pre-commit-config.yaml ([`e2470f0`](https://github.com/supabase/auth-py/commit/e2470f0e60c0c6ee6b1e091616b4a2c794656ef4))

* Update .pre-commit-config.yaml ([`d0757be`](https://github.com/supabase/auth-py/commit/d0757be5ab3a5762d59f33ccd129ea862d4f3180))

* Update .pre-commit-config.yaml ([`da1c0cd`](https://github.com/supabase/auth-py/commit/da1c0cdedf35dcb3aa4005bab606f36b28b812c8))

* Update .pre-commit-config.yaml ([`f0890cb`](https://github.com/supabase/auth-py/commit/f0890cbbb3d0c949c6bb529d7e127c9c16aa2e6a))

* Update .pre-commit-config.yaml ([`17a4db5`](https://github.com/supabase/auth-py/commit/17a4db52f253bac7c7b839c3c7e3bcba9782d511))

* Update .pre-commit-config.yaml ([`83e6021`](https://github.com/supabase/auth-py/commit/83e6021dbbc4818db65840bea261d0798885d9d5))

* Add follow_redirects=True ([`fab26ac`](https://github.com/supabase/auth-py/commit/fab26ac5bd8eca3d2aa5a3413943bfbb4aca6417))

* Add follow_redirects=True ([`5eea191`](https://github.com/supabase/auth-py/commit/5eea191bcb26a7faf2b5c3496eabd00ccb3ae1c8))

* Add follow_redirects=True ([`7b38f75`](https://github.com/supabase/auth-py/commit/7b38f7544b090029b6105a51f5099eee7de59d61))

* Add stale bot (#484) ([`7059504`](https://github.com/supabase/auth-py/commit/7059504d95ffccc3d9cef0dad130de28543772bf))

* Add stale bot ([`87b27b6`](https://github.com/supabase/auth-py/commit/87b27b63db1f99a64601de4ed16213c0e7ec7d63))

## v2.4.2 (2024-03-26)

### Chore

* chore(release): bump version to v2.4.2 ([`bdabba3`](https://github.com/supabase/auth-py/commit/bdabba35d7703ac1370964cea2502499ed9f0c28))

* chore(deps-dev): bump black from 23.10.1 to 24.3.0 (#446) ([`4850a9f`](https://github.com/supabase/auth-py/commit/4850a9fad7384fae24d9fcec8b89bdaf94eab47b))

* chore(deps-dev): bump black from 23.10.1 to 24.3.0

Bumps [black](https://github.com/psf/black) from 23.10.1 to 24.3.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/23.10.1...24.3.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`5a2ab10`](https://github.com/supabase/auth-py/commit/5a2ab106d9167ddc7d5c51afc37b5f94d22e3f33))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.1.1 to 9.3.1 (#452) ([`31a67fd`](https://github.com/supabase/auth-py/commit/31a67fdc2e852c8fa38f56e1a88f0b37bfa68ae6))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.1.1 to 9.3.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.1.1...v9.3.1)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`1b1ce42`](https://github.com/supabase/auth-py/commit/1b1ce429ce9836c7937fae474b1001f0951acf8b))

* chore: rename package to supabase_auth (#455) ([`3b63cd6`](https://github.com/supabase/auth-py/commit/3b63cd6dc7fd7e136c88e849c032da696fa977cf))

* chore(deps): bump httpx from 0.25.0 to 0.27.0 (#431) ([`3914bb6`](https://github.com/supabase/auth-py/commit/3914bb675e09189418caabb6ca2af6aacaea6582))

* chore(deps): bump httpx from 0.25.0 to 0.27.0

Bumps [httpx](https://github.com/encode/httpx) from 0.25.0 to 0.27.0.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.25.0...0.27.0)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`60da4b5`](https://github.com/supabase/auth-py/commit/60da4b5b124755ced7ed570c4b7551904a94306c))

* chore(deps-dev): bump pytest from 8.0.2 to 8.1.0 (#443) ([`de90b46`](https://github.com/supabase/auth-py/commit/de90b462a9e49b36e6a5298ae3119bc94ec9fba1))

* chore(deps-dev): bump pytest from 8.0.2 to 8.1.0

Bumps [pytest](https://github.com/pytest-dev/pytest) from 8.0.2 to 8.1.0.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/8.0.2...8.1.0)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`91f26fa`](https://github.com/supabase/auth-py/commit/91f26fa55cc8cad38ecab55ccebf61691d01980a))

* chore: bump fixed version of poetry (#438) ([`9344e79`](https://github.com/supabase/auth-py/commit/9344e796cb93b803fb395710e678a0bf6801f7ca))

* chore(deps-dev): bump faker from 19.12.1 to 23.3.0 (#436) ([`6a9e1ce`](https://github.com/supabase/auth-py/commit/6a9e1ce5ecdf060a086f91a5f7a0f0733be4c6f8))

* chore(deps-dev): bump faker from 19.12.1 to 23.3.0

Bumps [faker](https://github.com/joke2k/faker) from 19.12.1 to 23.3.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v19.12.1...v23.3.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7bd2a71`](https://github.com/supabase/auth-py/commit/7bd2a712c562f638322ddc38de6c5178625bb660))

* chore(deps-dev): bump pytest from 7.4.3 to 8.0.2 (#439) ([`cb5f6a6`](https://github.com/supabase/auth-py/commit/cb5f6a6104944e0e0fa0b8afa48f989f1fe30e80))

* chore(deps-dev): bump pytest from 7.4.3 to 8.0.2

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.4.3 to 8.0.2.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.4.3...8.0.2)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`0c04828`](https://github.com/supabase/auth-py/commit/0c04828812369a772d9bd1be1ed2da5ac5e78ece))

* chore(deps-dev): bump cryptography from 42.0.0 to 42.0.4

Bumps [cryptography](https://github.com/pyca/cryptography) from 42.0.0 to 42.0.4.
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/42.0.0...42.0.4)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`9066970`](https://github.com/supabase/auth-py/commit/90669704b42d9dd4e8a242d7b57b301ca197534a))

* chore(deps-dev): bump python-semantic-release from 8.3.0 to 9.1.1 (#440) ([`0d41e57`](https://github.com/supabase/auth-py/commit/0d41e5735e6e573c77783fd29f71fae6c08b5d63))

* chore(deps-dev): bump python-semantic-release from 8.3.0 to 9.1.1

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 8.3.0 to 9.1.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v8.3.0...v9.1.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7f2e12d`](https://github.com/supabase/auth-py/commit/7f2e12d7691aa41c77f4791c974511ebda69d430))

* chore(deps): bump python-semantic-release/python-semantic-release from 8.3.0 to 9.1.1 (#435) ([`a9789f7`](https://github.com/supabase/auth-py/commit/a9789f726ed82f06f74649c997f0ed40731d1c3c))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 8.3.0 to 9.1.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v8.3.0...v9.1.1)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7468b29`](https://github.com/supabase/auth-py/commit/7468b29b4240104c61578f158a98907c9777c94c))

* chore(deps-dev): bump pytest-asyncio from 0.21.1 to 0.23.5 (#424) ([`262547b`](https://github.com/supabase/auth-py/commit/262547b4acb652963033e2daab7ee283983d2f20))

* chore(deps-dev): bump pytest-asyncio from 0.21.1 to 0.23.5

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.21.1 to 0.23.5.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.21.1...v0.23.5)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`f88b538`](https://github.com/supabase/auth-py/commit/f88b5384c7b7ba1dbf440f67680ed307a7040845))

* chore(deps): bump pydantic from 2.4.2 to 2.6.3 (#437) ([`0de3da7`](https://github.com/supabase/auth-py/commit/0de3da7a6d78fa700324abf673b89568ab2fddec))

* chore(deps): bump pydantic from 2.4.2 to 2.6.3

Bumps [pydantic](https://github.com/pydantic/pydantic) from 2.4.2 to 2.6.3.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v2.4.2...v2.6.3)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`4d1984d`](https://github.com/supabase/auth-py/commit/4d1984db5ecabc4d7ace6fc7fa183e1aeddc7b5b))

* chore(deps): bump codecov/codecov-action from 3 to 4 (#415) ([`f374e91`](https://github.com/supabase/auth-py/commit/f374e916809777c44e86984fa3d4b57d477a5996))

* chore(deps): bump codecov/codecov-action from 3 to 4

Bumps [codecov/codecov-action](https://github.com/codecov/codecov-action) from 3 to 4.
- [Release notes](https://github.com/codecov/codecov-action/releases)
- [Changelog](https://github.com/codecov/codecov-action/blob/main/CHANGELOG.md)
- [Commits](https://github.com/codecov/codecov-action/compare/v3...v4)

---
updated-dependencies:
- dependency-name: codecov/codecov-action
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`db2307a`](https://github.com/supabase/auth-py/commit/db2307a155a4692c90503da78ef959268f0e3db1))

* chore(deps): bump abatilo/actions-poetry from 2.3.0 to 3.0.0 (#405) ([`63e028d`](https://github.com/supabase/auth-py/commit/63e028dbf62922de2ec8cf886942c3e80922b9d7))

* chore(deps): bump abatilo/actions-poetry from 2.3.0 to 3.0.0

Bumps [abatilo/actions-poetry](https://github.com/abatilo/actions-poetry) from 2.3.0 to 3.0.0.
- [Release notes](https://github.com/abatilo/actions-poetry/releases)
- [Changelog](https://github.com/abatilo/actions-poetry/blob/master/.releaserc)
- [Commits](https://github.com/abatilo/actions-poetry/compare/v2.3.0...v3.0.0)

---
updated-dependencies:
- dependency-name: abatilo/actions-poetry
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`f52f7e2`](https://github.com/supabase/auth-py/commit/f52f7e2793ca37ee7943bfe6e38510ec8bc1ca31))

### Fix

* fix: new minor version release (#457) ([`b831bb1`](https://github.com/supabase/auth-py/commit/b831bb1c1dcd316983ce2b8d15d4dac7c6280a6b))

### Unknown

* package release ([`fd971bd`](https://github.com/supabase/auth-py/commit/fd971bd84d7431d67b15940659e81382e622ba4b))

* update formatting ([`54a5bc1`](https://github.com/supabase/auth-py/commit/54a5bc146789b6421a9fc30be1f26d1e2749f2d1))

* rename package to supabase_auth ([`55a0f06`](https://github.com/supabase/auth-py/commit/55a0f06b59c932925f4689bebafc1dc26e9c2797))

* update ci to include python 3.12 in tests (#451) ([`cacb4b6`](https://github.com/supabase/auth-py/commit/cacb4b623ba85b8a65509298fd83a11f8f4ab3cc))

* Update project description and repository links ([`9bd18d1`](https://github.com/supabase/auth-py/commit/9bd18d1e86a2969be11b1fd321d55ab4d6bd87e7))

* update ci to include python 3.12 in tests ([`2350d43`](https://github.com/supabase/auth-py/commit/2350d4379460adf677dd3b6ecdd1031243087d07))

* Update manual_pypi_publish.yml ([`af2d2e5`](https://github.com/supabase/auth-py/commit/af2d2e51d59f3e0f3d8ead126e06beabd99030dd))

* feat (deps-dev): bump cryptography from 42.0.0 to 42.0.4 (#430) ([`26de4cb`](https://github.com/supabase/auth-py/commit/26de4cbbade04cece7af71d43752833496359ee6))

## v2.4.1 (2024-02-09)

### Chore

* chore(release): bump version to v2.4.1 ([`1c8cd12`](https://github.com/supabase/auth-py/commit/1c8cd1240c5f7cbcd03f54924c91590fa6f7f2ca))

* chore(deps-dev): bump cryptography from 41.0.6 to 42.0.0 (#416) ([`f03e518`](https://github.com/supabase/auth-py/commit/f03e5182a850607000717944bfb390b181294080))

* chore(deps-dev): bump cryptography from 41.0.6 to 42.0.0

Bumps [cryptography](https://github.com/pyca/cryptography) from 41.0.6 to 42.0.0.
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/41.0.6...42.0.0)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7d91ca2`](https://github.com/supabase/auth-py/commit/7d91ca2c612a29ccbcfc16d4ff8b030aa5e72d05))

### Fix

* fix: add AuthOtpResponse (#419) ([`130bdb1`](https://github.com/supabase/auth-py/commit/130bdb1ba47f8e18800ee052cb1d1e1538482ed4))

* fix: move changes to _async ([`7810bbd`](https://github.com/supabase/auth-py/commit/7810bbd868f202adf2bef1e0a8573973f8b415be))

* fix: add AuthOtpResponse ([`8d64ca4`](https://github.com/supabase/auth-py/commit/8d64ca450b37f7063b7fc701ee3156d1677d4fc3))

### Unknown

* formatting ([`97c4713`](https://github.com/supabase/auth-py/commit/97c47138215ee04af14478d913300032964f7a8e))

* revert changes to parse_auth_response ([`face521`](https://github.com/supabase/auth-py/commit/face52175ce75bcb074680c9a464fbb0ee320ae5))

## v2.4.0 (2024-01-31)

### Chore

* chore(release): bump version to v2.4.0 ([`640d0c1`](https://github.com/supabase/auth-py/commit/640d0c1cf37edca0b69a189c2b4b637c09b047d0))

* chore(deps-dev): bump jinja2 from 3.1.2 to 3.1.3 (#403) ([`0d58002`](https://github.com/supabase/auth-py/commit/0d580021af269a2e18e4a7864a88462c37334ecd))

* chore(deps-dev): bump jinja2 from 3.1.2 to 3.1.3

Bumps [jinja2](https://github.com/pallets/jinja) from 3.1.2 to 3.1.3.
- [Release notes](https://github.com/pallets/jinja/releases)
- [Changelog](https://github.com/pallets/jinja/blob/main/CHANGES.rst)
- [Commits](https://github.com/pallets/jinja/compare/3.1.2...3.1.3)

---
updated-dependencies:
- dependency-name: jinja2
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`f439d3f`](https://github.com/supabase/auth-py/commit/f439d3f4baf4edb301fa0e66c40b350dc2112597))

* chore(deps-dev): bump gitpython from 3.1.40 to 3.1.41 (#401) ([`8c8cd65`](https://github.com/supabase/auth-py/commit/8c8cd65ae7506c32d0fd040ea146c8cd2a15c73e))

* chore(deps-dev): bump gitpython from 3.1.40 to 3.1.41

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.40 to 3.1.41.
- [Release notes](https://github.com/gitpython-developers/GitPython/releases)
- [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES)
- [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.40...3.1.41)

---
updated-dependencies:
- dependency-name: gitpython
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`a60428c`](https://github.com/supabase/auth-py/commit/a60428ca97985a0b1210a08eee0866e8eca24fe2))

### Feature

* feat: add new identity linking methods release in LWX (#395) ([`96d18be`](https://github.com/supabase/auth-py/commit/96d18becda00478bacd08f32b61e75adc07d48fe))

* feat: add sso (#358) ([`c250f93`](https://github.com/supabase/auth-py/commit/c250f93cf5e50049629e5bb8f7d6b5c3fd408a42))

* feat: add docstring ([`dba16fb`](https://github.com/supabase/auth-py/commit/dba16fbc2a3ec688587abb75bad541da8055c016))

* feat: move skip_http_redirect to options ([`0547a2a`](https://github.com/supabase/auth-py/commit/0547a2a740bbf7620331cf371b12f42a3dacc801))

* feat: skip http redirects ([`8dca4a5`](https://github.com/supabase/auth-py/commit/8dca4a555718f463c54dba22aa77f77b748dc472))

* feat: add sso ([`99c9409`](https://github.com/supabase/auth-py/commit/99c9409ef2398b10bb7563ca3cbde0b0204ec88d))

* feat: add pydantic type ([`1308119`](https://github.com/supabase/auth-py/commit/1308119b80b3685852a20ec322fd8bea4315fd75))

* feat: add get_user_identities ([`2de717a`](https://github.com/supabase/auth-py/commit/2de717aa1785585ff872e4f94df891673b16858a))

* feat: link and unlink ([`6103511`](https://github.com/supabase/auth-py/commit/6103511a459d13713b55713161f634df30a40ca4))

### Fix

* fix: run black ([`89bcd15`](https://github.com/supabase/auth-py/commit/89bcd155c560ac404bc9f5e649027d3873661b0f))

* fix: apply sourcery suggestions ([`e225504`](https://github.com/supabase/auth-py/commit/e22550464d209e817118259caa06a06e3c494a42))

* fix: update types ([`51566e4`](https://github.com/supabase/auth-py/commit/51566e420002f965e29bcc9bf71510a144aa7e3c))

### Unknown

* Merge branch &#39;main&#39; into j0/add_linking_methods ([`ed9edab`](https://github.com/supabase/auth-py/commit/ed9edab57179fcf0e9a4cb11d615f6c137e9e8da))

* Update gotrue/_async/gotrue_base_api.py ([`72eeb1e`](https://github.com/supabase/auth-py/commit/72eeb1ebd2fbe6d7b66a7fccd08d5b538b742508))

* Merge branch &#39;main&#39; of github.com:supabase-community/gotrue-py into j0/add_linking_methods ([`851e523`](https://github.com/supabase/auth-py/commit/851e5233070b96dd022cc2a78c074fb0789f3c11))

## v2.3.0 (2024-01-12)

### Chore

* chore(release): bump version to v2.3.0 ([`17fa5d2`](https://github.com/supabase/auth-py/commit/17fa5d23daab9344c1f1b47b30c69e62803f7e06))

* chore: update to pull auth instead of gotrue ([`38977a6`](https://github.com/supabase/auth-py/commit/38977a6596f426805cf5fb106e7fdbbae311394c))

* chore: pull latest postgres image instead ([`e1877b2`](https://github.com/supabase/auth-py/commit/e1877b230f960d5eda7b1ad6b11b8a87a7513487))

### Feature

* feat: add sync methods ([`7c9f642`](https://github.com/supabase/auth-py/commit/7c9f642c9a6448707683fe6b54d3be4102aa8506))

* feat: add sync methods ([`280dc40`](https://github.com/supabase/auth-py/commit/280dc406c4e031b6c4681c56a36a9c9ddefd15d9))

* feat: pin version ([`5a90fff`](https://github.com/supabase/auth-py/commit/5a90fff802ff2c4860694d472243d69e8bedce1e))

### Fix

* fix: add linking methods ([`987adf2`](https://github.com/supabase/auth-py/commit/987adf2c112398be252d1fd9563cc8763dfc0b6f))

* fix: add linking methods ([`a29083a`](https://github.com/supabase/auth-py/commit/a29083a840200d984e9b969569eeb16185e5b598))

* fix: fix build by updating error message in test (#404) ([`ac94c60`](https://github.com/supabase/auth-py/commit/ac94c60529984d7cf82b422f0c65bc3b01e43732))

* fix: update error message in tests ([`6718dcd`](https://github.com/supabase/auth-py/commit/6718dcd19f3707647077ccd5cfa413bcbe718fd4))

### Unknown

* Merge branch &#39;j0/add_linking_methods&#39; of github.com:supabase-community/gotrue-py into j0/add_linking_methods ([`fa834cf`](https://github.com/supabase/auth-py/commit/fa834cfaca27cadcc7e536ee41d68702c6ae33b5))

* Update MAINTAINERS.md ([`5681011`](https://github.com/supabase/auth-py/commit/568101128a27280600da86780590fce62025410e))

## v2.2.0 (2023-12-13)

### Chore

* chore(release): bump version to v2.2.0 ([`6db7cc2`](https://github.com/supabase/auth-py/commit/6db7cc25cbca86e9908d2f268a46fd5f066aa5e3))

* chore(deps): bump actions/setup-python from 4 to 5 (#382) ([`55c04e2`](https://github.com/supabase/auth-py/commit/55c04e2121948b26ecd6af63c07e643892f05b45))

* chore(deps): bump actions/setup-python from 4 to 5

Bumps [actions/setup-python](https://github.com/actions/setup-python) from 4 to 5.
- [Release notes](https://github.com/actions/setup-python/releases)
- [Commits](https://github.com/actions/setup-python/compare/v4...v5)

---
updated-dependencies:
- dependency-name: actions/setup-python
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`c6f378a`](https://github.com/supabase/auth-py/commit/c6f378a409489f136f5808d1b6aeb859ac95636f))

### Feature

* feat: update docs (#386) ([`1bb53b0`](https://github.com/supabase/auth-py/commit/1bb53b060c7716c6d99e540f3a400f7f83d551e0))

* feat: update docs ([`d2c9693`](https://github.com/supabase/auth-py/commit/d2c969338f7e4685782947d696d547ffe4da45ee))

### Unknown

* Update README.md ([`62983ac`](https://github.com/supabase/auth-py/commit/62983ac31011b2fd1a810f1f2583632f88f3526c))

## v2.1.0 (2023-12-07)

### Chore

* chore(release): bump version to v2.1.0 ([`a1f060c`](https://github.com/supabase/auth-py/commit/a1f060c55d3a18fae8a616d2b4f7cd3cd2afc867))

### Feature

* feat: add sign_out() scope option (#381) ([`4ec8842`](https://github.com/supabase/auth-py/commit/4ec884227c57da32774dc107a2469d36befe4e8d))

* feat: add sign_out() scope option ([`3818dba`](https://github.com/supabase/auth-py/commit/3818dba635705d747b7da84fe8ab4dc2c5dcc9ab))

### Unknown

* Update to use query property of the request method ([`34a3ddf`](https://github.com/supabase/auth-py/commit/34a3ddfe8b9343c15b6959338a353aeb5e530b70))

## v2.0.0 (2023-11-30)

### Breaking

* feat: exchange code for session now fully async

BREAKING CHANGE: change async method on_auth_state_change to sync only. ([`a249ba0`](https://github.com/supabase/auth-py/commit/a249ba03cc7d99b2d1805480ca89ee457ad865f1))

### Chore

* chore(release): bump version to v2.0.0 ([`1440dd6`](https://github.com/supabase/auth-py/commit/1440dd6099cb5c7f8220223ea3a0e4d966e8ce60))

* chore(deps-dev): bump cryptography from 41.0.5 to 41.0.6 (#377) ([`e6b3d46`](https://github.com/supabase/auth-py/commit/e6b3d46fba5f24631fdd5fdb1b8d1688a1087053))

* chore(deps-dev): bump cryptography from 41.0.5 to 41.0.6

Bumps [cryptography](https://github.com/pyca/cryptography) from 41.0.5 to 41.0.6.
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/41.0.5...41.0.6)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`424a5df`](https://github.com/supabase/auth-py/commit/424a5df56f91ac30fab056bd9128d4dac004c565))

### Feature

* feat: exchange code for session now fully async (#378) ([`c294568`](https://github.com/supabase/auth-py/commit/c2945684a8ad4d8710ca72428b4ec16aab87bad1))

### Unknown

* bug fix: use pydantic v2 model.model_rebuild (#373) ([`fd94314`](https://github.com/supabase/auth-py/commit/fd94314c4412d49610acf8d3166abe660f6a4ee4))

* bug fix: use pydantic v2 model.model_rebuild not rebuild_model ([`9d723df`](https://github.com/supabase/auth-py/commit/9d723df7637fb501f83aad3562a49e2ed24bb9a2))

* add soft delete support to &#34;delete user&#34; (#376) ([`08bada3`](https://github.com/supabase/auth-py/commit/08bada3692f230cf1bd793a7eb60a12d62fec0c6))

* add soft delete support to &#34;delete user&#34; ([`5471167`](https://github.com/supabase/auth-py/commit/54711675533ce58fdf3017f250e92a88db719aad))

## v1.3.1 (2023-11-29)

### Chore

* chore(release): bump version to v1.3.1 ([`ede20fe`](https://github.com/supabase/auth-py/commit/ede20fea097fd900df2efc6231c14ea86f486087))

### Fix

* fix: remove unnecessary async to on_auth_state_change (#374) ([`574c739`](https://github.com/supabase/auth-py/commit/574c739500dd304aa6d09c69122373b6e4a5be01))

* fix: remove unnecessary async to on_auth_state_change

Somehow this got reverted on a refactor (https://github.com/supabase-community/gotrue-py/commit/e7ebc64112d970673265c7b314a1e8820fc0f7e1)

This causes problems when using the supabase client, since it&#39;s not being awaited:
https://github.com/supabase-community/supabase-py/blob/main/supabase/_async/client.py#L90 ([`7548d02`](https://github.com/supabase/auth-py/commit/7548d0290199bdb1053564b953932c53aabdea29))

## v1.3.0 (2023-11-01)

### Chore

* chore(release): bump version to v1.3.0 ([`abe3e2a`](https://github.com/supabase/auth-py/commit/abe3e2a871d97df4a91f2c4ae3a3c05e56e6e083))

* chore: update CI config with PAT (#361) ([`fbddd6d`](https://github.com/supabase/auth-py/commit/fbddd6dbbeb67895f6d804f6a9fd804247ccf0c4))

* chore: update CI config with PAT ([`1fffc1f`](https://github.com/supabase/auth-py/commit/1fffc1fdebca39c35a9e69ea3d25240e13eb73b7))

* chore(deps-dev): bump pygithub from 1.59.1 to 2.1.1 (#337) ([`160b671`](https://github.com/supabase/auth-py/commit/160b671de0ecab9d40a6caf4c6553d8808974b1f))

* chore(deps-dev): bump pygithub from 1.59.1 to 2.1.1

Bumps [pygithub](https://github.com/pygithub/pygithub) from 1.59.1 to 2.1.1.
- [Release notes](https://github.com/pygithub/pygithub/releases)
- [Changelog](https://github.com/PyGithub/PyGithub/blob/main/doc/changes.rst)
- [Commits](https://github.com/pygithub/pygithub/compare/v1.59.1...v2.1.1)

---
updated-dependencies:
- dependency-name: pygithub
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`264e773`](https://github.com/supabase/auth-py/commit/264e77314e5a50e0b325d906e11998be933339d2))

* chore: update dependencies (#357) ([`a5d4a81`](https://github.com/supabase/auth-py/commit/a5d4a812d1cc4bb8624a33853088a1710b1a501d))

* chore: update dependencies ([`dc67de1`](https://github.com/supabase/auth-py/commit/dc67de1b9e56fd7d07e98cba73969ec458ce4d3c))

* chore(deps-dev): bump urllib3 from 2.0.4 to 2.0.7 (#350) ([`4ea73e4`](https://github.com/supabase/auth-py/commit/4ea73e42892f63a3065e3fc9cc059ae940cefdc1))

* chore(deps-dev): bump urllib3 from 2.0.4 to 2.0.7

Bumps [urllib3](https://github.com/urllib3/urllib3) from 2.0.4 to 2.0.7.
- [Release notes](https://github.com/urllib3/urllib3/releases)
- [Changelog](https://github.com/urllib3/urllib3/blob/main/CHANGES.rst)
- [Commits](https://github.com/urllib3/urllib3/compare/2.0.4...2.0.7)

---
updated-dependencies:
- dependency-name: urllib3
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`2400229`](https://github.com/supabase/auth-py/commit/240022942e7513b67e5db3e26e4f9a9be77f7f83))

* chore(deps): bump python-semantic-release/python-semantic-release from 8.0.8 to 8.3.0 (#354) ([`a385575`](https://github.com/supabase/auth-py/commit/a385575e960426090c5aa6b8395c43c706015f72))

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 8.0.8 to 8.3.0.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v8.0.8...v8.3.0)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`3fbe6fc`](https://github.com/supabase/auth-py/commit/3fbe6fcbefde561833a45c07df565ad00c448669))

* chore(deps): bump httpx from 0.24.1 to 0.25.0

Bumps [httpx](https://github.com/encode/httpx) from 0.24.1 to 0.25.0.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.24.1...0.25.0)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`a5b2f85`](https://github.com/supabase/auth-py/commit/a5b2f85c68a4157c41eec606fcd041f89969b08e))

### Feature

* feat: add OAuth PKCE (#331) ([`8fe633e`](https://github.com/supabase/auth-py/commit/8fe633e5cfff20d748e8eb5dfdb82c2cbd9390fd))

* feat: allow dev to pass in code_verifier ([`f33bf3e`](https://github.com/supabase/auth-py/commit/f33bf3ed43b930f8ef43756693c3af514ddfaa62))

### Fix

* fix: add latest semantic-release dependency (#360) ([`81e63ea`](https://github.com/supabase/auth-py/commit/81e63ea56b2b0a611852609c03abee79e2bda6ef))

* fix: add latest semantic-release dependency ([`251a4f4`](https://github.com/supabase/auth-py/commit/251a4f49f85a9489362833c02f932dad06f4d8ec))

* fix: fix typo ([`72ee18d`](https://github.com/supabase/auth-py/commit/72ee18db05b8d1ea2b916a4bfea074459df9ecf0))

* fix: update imports ([`66759da`](https://github.com/supabase/auth-py/commit/66759da715a1d1511cf2518b5a1119bdfa205088))

### Unknown

* patch: read from storage ([`364292c`](https://github.com/supabase/auth-py/commit/364292c0bb1c8362f6da4a198ea6a2fe2d98fd8e))

* Merge branch &#39;j0/pkce&#39; of github.com:supabase-community/gotrue-py into j0/pkce ([`1c40ed7`](https://github.com/supabase/auth-py/commit/1c40ed76ddeb1916278bb7b4827d8631b7749066))

* Merge branch &#39;main&#39; into j0/pkce ([`4c44238`](https://github.com/supabase/auth-py/commit/4c4423859375b2d796f6527689e1ebace36860e3))

* Merge pull request #325 from supabase-community/dependabot/pip/main/httpx-0.25.0

chore(deps): bump httpx from 0.24.1 to 0.25.0 ([`89019fb`](https://github.com/supabase/auth-py/commit/89019fb8ecf2d7b1609bf4d0114b552ec9062e6d))

* Merge pull request #352 from fbeutel/urlsafe_b64decode

Use urlsafe_b64decode to properly handle URL-encoded JWTs ([`7541ade`](https://github.com/supabase/auth-py/commit/7541ade5e09349b477d64afc5a80774fd4be0f07))

* Use urlsafe_b64decode to properly handle URL-encoded JWTs ([`0034af1`](https://github.com/supabase/auth-py/commit/0034af1816b54c043079ef251df6ac2f76d5b41b))

## v1.2.0 (2023-10-05)

### Chore

* chore(release): bump version to v1.2.0 ([`8da1032`](https://github.com/supabase/auth-py/commit/8da10323c27adf9976c1eaab4ac82aca560ee578))

* chore(deps-dev): bump cryptography from 41.0.3 to 41.0.4

Bumps [cryptography](https://github.com/pyca/cryptography) from 41.0.3 to 41.0.4.
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/41.0.3...41.0.4)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`4aa7224`](https://github.com/supabase/auth-py/commit/4aa7224e414df9c7ddc822d29d79e0db777dd7d3))

### Feature

* feat: Add exception to handle API errors on signout ([`59b90d5`](https://github.com/supabase/auth-py/commit/59b90d545f59cb00b08b3a5c02edcd9a4a229538))

### Fix

* fix: patch imports ([`3b61aff`](https://github.com/supabase/auth-py/commit/3b61aff1574a6adbbc49cd9ef81e86ff3b35535d))

* fix: run pre-commit ([`754c7ab`](https://github.com/supabase/auth-py/commit/754c7abe6f30d429d2606a24b3f63667fc96c530))

* fix: add pkce ([`02f7c05`](https://github.com/supabase/auth-py/commit/02f7c05c24c656d079c4be149d98140411445c37))

### Unknown

* Merge pull request #342 from supabase-community/silentworks/sign-out-exception-handling

feat: Add exception to handle API errors on signout ([`708859c`](https://github.com/supabase/auth-py/commit/708859c1fe12535910ef5d8385f42a6aabda2613))

* Update to use suppress instead of try except ([`2d964ad`](https://github.com/supabase/auth-py/commit/2d964ad892e3a40204904319d499f7da9aa9289a))

* Merge pull request #341 from supabase-community/silentworks/add-correct-semantic-release-vars

Add correct variables for semantic release ([`5155312`](https://github.com/supabase/auth-py/commit/5155312a31fd669a6f62616ea75036386a2fc004))

* Get pre-commit to ignore changelog ([`738602e`](https://github.com/supabase/auth-py/commit/738602ea6ba013ff9071115ee65842c26f4098cf))

* Add correct variables for semantic release ([`80b0e30`](https://github.com/supabase/auth-py/commit/80b0e30cc5ddf510f2ea1891aab247bde7c01ccc))

* Merge pull request #330 from supabase-community/dependabot/pip/cryptography-41.0.4

chore(deps-dev): bump cryptography from 41.0.3 to 41.0.4 ([`1bf3e5d`](https://github.com/supabase/auth-py/commit/1bf3e5dc03f9d0da1f939001ec120e1ef0c69420))

* Merge pull request #332 from supabase-community/sourcery/j0/pkce

feat: add OAuth PKCE (Sourcery refactored) ([`b331d04`](https://github.com/supabase/auth-py/commit/b331d043ce056a9a09355e14989e036e86db9c59))

* &#39;Refactored by Sourcery&#39; ([`af4f842`](https://github.com/supabase/auth-py/commit/af4f842d8fdf59fcef04b853660627b6b24a18a4))

## v1.1.1 (2023-09-22)

### Chore

* chore(deps): bump python-semantic-release/python-semantic-release

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 8.0.0 to 8.0.8.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v8.0.0...v8.0.8)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`8f094df`](https://github.com/supabase/auth-py/commit/8f094df3e6d8ba21f2c429b8c8c208c42e18f68c))

* chore(deps-dev): bump pytest from 7.4.0 to 7.4.2

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`cb41e8b`](https://github.com/supabase/auth-py/commit/cb41e8ba11c913411a4fd5ce19ec597ef04ff3d5))

* chore(deps-dev): bump pre-commit from 3.3.3 to 3.4.0

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 3.3.3 to 3.4.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v3.3.3...v3.4.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`133eca2`](https://github.com/supabase/auth-py/commit/133eca2d76c8e69d5be439a2f0067a767377b83a))

* chore(deps-dev): bump black from 23.7.0 to 23.9.1

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`5617a6a`](https://github.com/supabase/auth-py/commit/5617a6a8443db03aa829ae8ba4129b7341d11442))

* chore(deps-dev): bump faker from 19.3.0 to 19.6.1

Bumps [faker](https://github.com/joke2k/faker) from 19.3.0 to 19.6.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v19.3.0...v19.6.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`ab39f66`](https://github.com/supabase/auth-py/commit/ab39f668f3128810baef1d7db49ad6f0cfaa8521))

### Fix

* fix: add verify token hash ([`da51e8e`](https://github.com/supabase/auth-py/commit/da51e8ea262fa113da7bd77c4e67ba14c7262851))

### Refactor

* refactor: remove unused v1 files ([`e9005e4`](https://github.com/supabase/auth-py/commit/e9005e4c3ee4e4a9a344993c6e3120dc30832eac))

### Unknown

* 1.1.1

Automatically generated by python-semantic-release ([`152ed06`](https://github.com/supabase/auth-py/commit/152ed06f65369ad1f15e6d105bd9d93d1b79da12))

* Merge pull request #328 from supabase-community/feat/add-verify-token-hash

fix: add verify token hash ([`ccb2173`](https://github.com/supabase/auth-py/commit/ccb2173eb694622be100eec36942ec8a69b151a7))

* Fixed formatting ([`82a04aa`](https://github.com/supabase/auth-py/commit/82a04aaee7c6cb1047091789007f6366bbe1a535))

* Merge pull request #303 from supabase-community/dependabot/github_actions/main/python-semantic-release/python-semantic-release-8.0.8

chore(deps): bump python-semantic-release/python-semantic-release from 8.0.0 to 8.0.8 ([`cb6abab`](https://github.com/supabase/auth-py/commit/cb6abab03286a9305e480c1754c4ddfcde649196))

* Merge pull request #310 from supabase-community/dependabot/pip/main/pytest-7.4.2

chore(deps-dev): bump pytest from 7.4.0 to 7.4.2 ([`1df12a7`](https://github.com/supabase/auth-py/commit/1df12a7d5078b5ffb8bf611ae14e18da0609e9f6))

* Merge pull request #323 from supabase-community/j0/remove_unused_v1

refactor: remove unused v1 files ([`817fafb`](https://github.com/supabase/auth-py/commit/817fafb2720f4f201f940cf37f6e4262743241e8))

* Merge pull request #305 from supabase-community/dependabot/pip/main/pre-commit-3.4.0

chore(deps-dev): bump pre-commit from 3.3.3 to 3.4.0 ([`687c52d`](https://github.com/supabase/auth-py/commit/687c52daa2ef2aa4dd35348eaff83e6891f98750))

* Merge pull request #317 from supabase-community/dependabot/pip/main/black-23.9.1

chore(deps-dev): bump black from 23.7.0 to 23.9.1 ([`b0144ef`](https://github.com/supabase/auth-py/commit/b0144ef0ab12e07eea5526822a5cd0a7a3548097))

* Merge pull request #318 from supabase-community/dependabot/pip/main/faker-19.6.1

chore(deps-dev): bump faker from 19.3.0 to 19.6.1 ([`2cc68f9`](https://github.com/supabase/auth-py/commit/2cc68f944e03c61962d4da559da174f592717f18))

* Merge pull request #315 from jantznick/main

fix get_user calls fail when no session or jwt is available ([`2a562a7`](https://github.com/supabase/auth-py/commit/2a562a749c12866c42dc16c9783e8b36823b253b))

* changelog changed from precommit hooks ([`5cf279e`](https://github.com/supabase/auth-py/commit/5cf279e6711c4e235e4b83dea874fa1eea2a6695))

* update return type for get_user calls ([`ddeb595`](https://github.com/supabase/auth-py/commit/ddeb5951cb5a8f7b2fc8c5157d74feb1f339be3d))

* return None when no session or jwt on get_user calls ([`50fa8b0`](https://github.com/supabase/auth-py/commit/50fa8b00000d1a4dd54506fba4dc6c90cd893006))

## v1.1.0 (2023-09-08)

### Chore

* chore(deps): bump actions/checkout from 3 to 4

Bumps [actions/checkout](https://github.com/actions/checkout) from 3 to 4.
- [Release notes](https://github.com/actions/checkout/releases)
- [Changelog](https://github.com/actions/checkout/blob/main/CHANGELOG.md)
- [Commits](https://github.com/actions/checkout/compare/v3...v4)

---
updated-dependencies:
- dependency-name: actions/checkout
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`2a51fff`](https://github.com/supabase/auth-py/commit/2a51fff932e6eb9773614cf4cd5a72400c9c2aef))

* chore(deps-dev): bump gitpython from 3.1.32 to 3.1.35

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.32 to 3.1.35.
- [Release notes](https://github.com/gitpython-developers/GitPython/releases)
- [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES)
- [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.32...3.1.35)

---
updated-dependencies:
- dependency-name: gitpython
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7b0fb17`](https://github.com/supabase/auth-py/commit/7b0fb1711c030697cc724900034e504ca97dc324))

* chore: run formatting on CHANGELOG to correct for mix line endings ([`3f47338`](https://github.com/supabase/auth-py/commit/3f47338c81c95cc89d349b73d4e080eebf708cfa))

### Feature

* feat: support pagination for admin list_users ([`e7cbd9f`](https://github.com/supabase/auth-py/commit/e7cbd9f17a3c5690d77954b2b57c267ea5382afd))

### Unknown

* 1.1.0

Automatically generated by python-semantic-release ([`ff35a92`](https://github.com/supabase/auth-py/commit/ff35a928ef5c5cb8a5559a122fe55a868be0c023))

* Merge pull request #307 from supabase-community/dependabot/github_actions/main/actions/checkout-4

chore(deps): bump actions/checkout from 3 to 4 ([`64c0c66`](https://github.com/supabase/auth-py/commit/64c0c66f452f5d149fcbe61dc88c74baf9056584))

* Merge pull request #312 from supabase-community/dependabot/pip/gitpython-3.1.35

chore(deps-dev): bump gitpython from 3.1.32 to 3.1.35 ([`9b62e68`](https://github.com/supabase/auth-py/commit/9b62e6861d579ea437f450065a456c3a0a8eacab))

* Merge pull request #304 from connorlurring/admin-list-users-pagination

feat: support pagination for auth admin list_users ([`1b88c51`](https://github.com/supabase/auth-py/commit/1b88c51bf29f69dc066377f94fe38dadb66b12cb))

* Merge pull request #311 from supabase-community/j0/lint_changelog

chore: run formatting on CHANGELOG to correct for mix line endings ([`8684125`](https://github.com/supabase/auth-py/commit/86841257aefbbbc986e6ec4779a2c9373cf61c85))

## v1.0.4 (2023-08-23)

### Chore

* chore: add contents permission ([`a2a4912`](https://github.com/supabase/auth-py/commit/a2a49127a59b759e1a7336d9caf33bf277cf8a7f))

* chore: upgrade smenatic release ([`0cf22c2`](https://github.com/supabase/auth-py/commit/0cf22c2709f294d404549e141cae64d6c240fde5))

* chore(deps-dev): bump faker from 19.2.0 to 19.3.0

Bumps [faker](https://github.com/joke2k/faker) from 19.2.0 to 19.3.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v19.2.0...v19.3.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`29f1a1e`](https://github.com/supabase/auth-py/commit/29f1a1e1d10182c2c3e3fc837beff0371457cac2))

* chore(deps-dev): bump faker from 18.13.0 to 19.2.0

Bumps [faker](https://github.com/joke2k/faker) from 18.13.0 to 19.2.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v18.13.0...v19.2.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`0a03065`](https://github.com/supabase/auth-py/commit/0a030658bcc6b3bd3b522dec576174c1dc56a1ad))

### Fix

* fix: update more pyproject.toml config options ([`3c38c2b`](https://github.com/supabase/auth-py/commit/3c38c2bb252e45d1d7a9f0b856134e269ac5db4c))

* fix: convert version_toml to array ([`d9c555d`](https://github.com/supabase/auth-py/commit/d9c555d334aa7eaf15ea1a73109e76ed6e86abd0))

* fix: add relevant pypi info and permissions ([`875484e`](https://github.com/supabase/auth-py/commit/875484ede1f71e2a87992bc52381bc2c649f7966))

* fix: add new providers ([`b4c1681`](https://github.com/supabase/auth-py/commit/b4c16818ba781fe597766d81816c2be5a8a8265e))

* fix: add type definitions for new providers ([`e033cee`](https://github.com/supabase/auth-py/commit/e033cee2e42ae318614dd59a9ba02b8f15ce5600))

### Unknown

* 1.0.4

Automatically generated by python-semantic-release ([`5cc198b`](https://github.com/supabase/auth-py/commit/5cc198b631189a0622a23b71e8d5a4acba1de005))

* Merge pull request #299 from supabase-community/j0/fix_version_toml

chore: add contents permission ([`7561df9`](https://github.com/supabase/auth-py/commit/7561df9a8b7b0279763e318f2a48b54693278c9b))

* Merge pull request #298 from supabase-community/j0/fix_version_toml

fix: update version options ([`b66f958`](https://github.com/supabase/auth-py/commit/b66f9589be39526340152c8523c5130dde90ea0f))

* Merge pull request #297 from supabase-community/j0/fix_semantic_release

fix: fix semantic release ([`3c9984b`](https://github.com/supabase/auth-py/commit/3c9984b2f89828f304b8f4fa1702b209ef5243bf))

* Merge pull request #290 from supabase-community/dependabot/pip/main/faker-19.3.0

chore(deps-dev): bump faker from 19.2.0 to 19.3.0 ([`52474bc`](https://github.com/supabase/auth-py/commit/52474bc1237ef0e2562f09b09aadb73e90e706e0))

* Merge pull request #293 from supabase-community/or/pydantic-v1-v2-support

Support for pydantic v1 &amp; v2 ([`6765f07`](https://github.com/supabase/auth-py/commit/6765f0778ec16afe66cddccd7067af0451838b7a))

* revert TypeAdapter to parse_obj_as for pydantic v1 support ([`79cd743`](https://github.com/supabase/auth-py/commit/79cd7438b1482742fd832044b90a51953609944d))

* run tests with pydantic v1 under CI ([`9c4aa2a`](https://github.com/supabase/auth-py/commit/9c4aa2abe4d8d711a7d85b4a9a6ccc6e93b02eab))

* pydantic v1 &amp; v2 compatibility ([`45456c8`](https://github.com/supabase/auth-py/commit/45456c8e4c29d5a2846cd74679091c6f055f8158))

* Merge pull request #289 from yuvanist/main

Specify minor version of pydantic to avoid dependency issue ([`c2ed950`](https://github.com/supabase/auth-py/commit/c2ed950516e4b9bee6eb8f066969049b9a361a28))

* Update lock file ([`9258777`](https://github.com/supabase/auth-py/commit/92587777ea9d1d844e25d5c4905ff8f24d50b369))

* specify minor version of pydantic ([`2b0bdb4`](https://github.com/supabase/auth-py/commit/2b0bdb4e347aaba33820dcf9b404da448148b004))

* Merge pull request #288 from supabase-community/dependabot/pip/main/faker-19.2.0

chore(deps-dev): bump faker from 18.13.0 to 19.2.0 ([`69f5994`](https://github.com/supabase/auth-py/commit/69f59947e62e4ec808376595bbffc53170f49aae))

## v1.0.3 (2023-08-03)

### Chore

* chore: bump ci file ([`cfe3acb`](https://github.com/supabase/auth-py/commit/cfe3acbba295d30b1360269f891449ca2fe7fa13))

* chore(deps-dev): bump pygithub from 1.58.0 to 1.59.0

Bumps [pygithub](https://github.com/pygithub/pygithub) from 1.58.0 to 1.59.0.
- [Release notes](https://github.com/pygithub/pygithub/releases)
- [Changelog](https://github.com/PyGithub/PyGithub/blob/main/doc/changes.rst)
- [Commits](https://github.com/pygithub/pygithub/compare/v1.58.0...v1.59.0)

---
updated-dependencies:
- dependency-name: pygithub
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`57ae5f7`](https://github.com/supabase/auth-py/commit/57ae5f79261545977d97c39f76d2cc9e868b65b1))

* chore(deps-dev): bump pytest-asyncio from 0.20.3 to 0.21.1

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.20.3 to 0.21.1.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.20.3...v0.21.1)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`d5f937f`](https://github.com/supabase/auth-py/commit/d5f937f3c2d377336c93537d46cc53969ad1f1f6))

* chore(deps-dev): bump python-semantic-release from 7.33.2 to 7.34.6

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`9ac7669`](https://github.com/supabase/auth-py/commit/9ac7669f42fc709b3e4d59b4aa2d1dbfff0b93a6))

* chore(deps): bump cryptography from 39.0.1 to 41.0.0

Bumps [cryptography](https://github.com/pyca/cryptography) from 39.0.1 to 41.0.0.
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/39.0.1...41.0.0)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`461aa75`](https://github.com/supabase/auth-py/commit/461aa75350e8214b942f869ccd8d719e4313eb36))

### Feature

* feat: release new version ([`0cf8072`](https://github.com/supabase/auth-py/commit/0cf80722fc7fd69c8adf93ce83fa11f68f531b8e))

### Fix

* fix: revert semantic release ([`aea52c2`](https://github.com/supabase/auth-py/commit/aea52c251664ee1496f9af875dc2ab09f823d467))

* fix: bump version ([`da8be6f`](https://github.com/supabase/auth-py/commit/da8be6fc3b9ee9ada78acfc110bdb7c8ec354b91))

### Unknown

* Merge pull request #287 from supabase-community/j0/release_new_ver

feat: release v1.0.3 ([`a6f8fd6`](https://github.com/supabase/auth-py/commit/a6f8fd6d9af1572abacb73a10471c7a6bfa160aa))

* Revert &#34;chore: bump ci file&#34;

This reverts commit cfe3acbba295d30b1360269f891449ca2fe7fa13. ([`baa692c`](https://github.com/supabase/auth-py/commit/baa692c46b2270dfec2697dbe26f58fb016bf593))

* Merge pull request #279 from supabase-community/dependabot/pip/main/pygithub-1.59.0

chore(deps-dev): bump pygithub from 1.58.0 to 1.59.0 ([`86b9648`](https://github.com/supabase/auth-py/commit/86b9648683af94e314d2c0c8f6d3c4a49be81b8a))

* Merge pull request #286 from yuvanist/main

Upgrade gotrue-py to pydantic &gt; 2.1.x ([`86ac440`](https://github.com/supabase/auth-py/commit/86ac4405b266e6c33f10888352316fd7c5c917a5))

* change lock file ([`6ca5a7d`](https://github.com/supabase/auth-py/commit/6ca5a7dbfc7cb8c56b7b9c430745b370954ce109))

* Change pydantic version to 2.1 ([`1daebe0`](https://github.com/supabase/auth-py/commit/1daebe01db2e309ae76c4d7f50d39e05536afca6))

* reformat ([`3aa81c7`](https://github.com/supabase/auth-py/commit/3aa81c75c1edccb73b8ad8c845afd2ae58fa1522))

* change to model_rebuild ([`cd053cc`](https://github.com/supabase/auth-py/commit/cd053ccc1e377cad73b2b6858ba3eb802a8ce2db))

* update poetry lock ([`e99b5b5`](https://github.com/supabase/auth-py/commit/e99b5b5236ad8040387014dcc9a83ea98382d90d))

* root_validator to model_validator ([`0dee34e`](https://github.com/supabase/auth-py/commit/0dee34e493c199c38691c7c3a88ee3315f6b3f3d))

* Upgrade to Pydantic V2 - Initial Changes ([`e59bb96`](https://github.com/supabase/auth-py/commit/e59bb96ccb3ca4db9b25ebb6c20c40f488e53a47))

* Merge pull request #284 from supabase-community/dependabot/pip/main/pytest-asyncio-0.21.1

chore(deps-dev): bump pytest-asyncio from 0.20.3 to 0.21.1 ([`743d6c1`](https://github.com/supabase/auth-py/commit/743d6c1e38966100d8d05c1abfc650cdc2b9e530))

* Merge pull request #278 from supabase-community/dependabot/pip/main/python-semantic-release-7.34.6

chore(deps-dev): bump python-semantic-release from 7.33.2 to 7.34.6 ([`aa12b1b`](https://github.com/supabase/auth-py/commit/aa12b1b98c56e8e371c00b9f2534187cbd196d48))

* Merge pull request #280 from supabase-community/j0/update_version

fix: bump __init__ version to 1.02 ([`99b9907`](https://github.com/supabase/auth-py/commit/99b9907018f3ecdd8bda91fd794f2e4d6fd4fb7b))

* Merge pull request #275 from supabase-community/dependabot/pip/cryptography-41.0.0

chore(deps): bump cryptography from 39.0.1 to 41.0.0 ([`6b0b687`](https://github.com/supabase/auth-py/commit/6b0b687d2a896bba179e5cd445a7a255ee2f37a8))

## v1.0.2 (2023-06-01)

### Chore

* chore(deps-dev): bump pytest from 7.2.2 to 7.3.1

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.2.2 to 7.3.1.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.2.2...7.3.1)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`9c334f2`](https://github.com/supabase/auth-py/commit/9c334f23d1d529f29de26a1a99d16b00a457a263))

* chore(deps-dev): bump black from 23.1.0 to 23.3.0

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`0c26730`](https://github.com/supabase/auth-py/commit/0c2673043d453c680a034f452ed3a5cb957aaac7))

* chore(deps): bump pydantic from 1.10.5 to 1.10.8

Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.5 to 1.10.8.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/v1.10.8/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v1.10.5...v1.10.8)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`8a8aba2`](https://github.com/supabase/auth-py/commit/8a8aba2ba0c2370b9697fa854a8e1be3fd28b7b4))

* chore(deps): bump requests from 2.28.2 to 2.31.0

Bumps [requests](https://github.com/psf/requests) from 2.28.2 to 2.31.0.
- [Release notes](https://github.com/psf/requests/releases)
- [Changelog](https://github.com/psf/requests/blob/main/HISTORY.md)
- [Commits](https://github.com/psf/requests/compare/v2.28.2...v2.31.0)

---
updated-dependencies:
- dependency-name: requests
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`883c218`](https://github.com/supabase/auth-py/commit/883c218172eaee7264625a004c17c033471218a7))

* chore(deps): bump httpx from 0.23.3 to 0.24.1

Bumps [httpx](https://github.com/encode/httpx) from 0.23.3 to 0.24.1.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.23.3...0.24.1)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`f184d7a`](https://github.com/supabase/auth-py/commit/f184d7a6f6185b0861677b9835b4f4fe1b467a33))

* chore(deps-dev): bump pre-commit from 3.1.1 to 3.2.2

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 3.1.1 to 3.2.2.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v3.1.1...v3.2.2)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`5c5e384`](https://github.com/supabase/auth-py/commit/5c5e384fe14eae908796e5f9df4dc56efd1682b6))

### Feature

* feat: update README ([`a0a0d79`](https://github.com/supabase/auth-py/commit/a0a0d79d4e1608dce31093b69eed48fd8bd664f8))

### Fix

* fix: parse_auth_response to handle cases when data is an empty dictionary ([`71f1b07`](https://github.com/supabase/auth-py/commit/71f1b072bc9959618870996991b621ef7463f20e))

### Refactor

* refactor: parse_auth_response handles cases when data does not have key user ([`f533b92`](https://github.com/supabase/auth-py/commit/f533b922d0c99007d1fe56ee99c6852c48a51403))

### Unknown

* Merge pull request #273 from supabase-community/j0/release_1_0_2

feat: update README, release v1.0.2 ([`8477576`](https://github.com/supabase/auth-py/commit/84775765f46accc81eed8da8cddf408a51afba58))

* Merge pull request #267 from supabase-community/dependabot/pip/main/pytest-7.3.1

chore(deps-dev): bump pytest from 7.2.2 to 7.3.1 ([`29fb30b`](https://github.com/supabase/auth-py/commit/29fb30b0105dfcb2176be73b94e0d37ed0db3577))

* Merge pull request #258 from supabase-community/dependabot/pip/main/black-23.3.0

chore(deps-dev): bump black from 23.1.0 to 23.3.0 ([`a5beade`](https://github.com/supabase/auth-py/commit/a5beadeed6ed9605a5c64def1025c1fc49d7776c))

* Merge pull request #269 from supabase-community/dependabot/pip/main/pydantic-1.10.8

chore(deps): bump pydantic from 1.10.5 to 1.10.8 ([`4845101`](https://github.com/supabase/auth-py/commit/4845101ef546e30fe6f01eb1b90d9ada2bed645e))

* Merge pull request #268 from supabase-community/dependabot/pip/requests-2.31.0

chore(deps): bump requests from 2.28.2 to 2.31.0 ([`15f2dbd`](https://github.com/supabase/auth-py/commit/15f2dbd7db45b1c7631a818538ce5cf4c1b3a5d6))

* Merge pull request #264 from lmoj/double-urlencode

fix issue #246 ([`dca7d9a`](https://github.com/supabase/auth-py/commit/dca7d9a4219230d3f99b69d00b84bcd84f0dd12f))

* fix import ([`034da90`](https://github.com/supabase/auth-py/commit/034da901685a6022e6f16a8588386d54c43b2594))

* fix url double encode ([`69a4f4a`](https://github.com/supabase/auth-py/commit/69a4f4a6a03ab30ea0c0d9862fa7c15191588f21))

* Merge pull request #266 from supabase-community/dependabot/pip/main/httpx-0.24.1

chore(deps): bump httpx from 0.23.3 to 0.24.1 ([`0efdd9d`](https://github.com/supabase/auth-py/commit/0efdd9d1e206fcac8aa9b62b45b86e2120f835d1))

* Merge pull request #265 from lmoj/optional-last_sign_in_at

optional last_sign_in_at in UserIdentity type ([`99d4567`](https://github.com/supabase/auth-py/commit/99d45678572b4ea7ad91c2340a5753a263a40703))

* optional last_sign_in_at in UserIdentity type ([`6fef36a`](https://github.com/supabase/auth-py/commit/6fef36a583018c113f72e927a6598adf4948669b))

* Merge pull request #261 from hgseo16/main

fix: parse_auth_response to handle cases when data is an empty dictio… ([`633c4ab`](https://github.com/supabase/auth-py/commit/633c4ab5207d12991d0e97c35786ed699ac175b9))

* Merge pull request #260 from supabase-community/dependabot/pip/main/pre-commit-3.2.2

chore(deps-dev): bump pre-commit from 3.1.1 to 3.2.2 ([`736f334`](https://github.com/supabase/auth-py/commit/736f3342f2f379728ea578b4804f3f919f7a476b))

## v1.0.1 (2023-04-03)

### Chore

* chore(deps-dev): bump faker from 18.3.0 to 18.3.1

Bumps [faker](https://github.com/joke2k/faker) from 18.3.0 to 18.3.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v18.3.0...v18.3.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`11c55d5`](https://github.com/supabase/auth-py/commit/11c55d56c67ccec3d2a69fd0918cd8a5a65d9e52))

* chore(deps-dev): bump faker from 17.6.0 to 18.3.0

Bumps [faker](https://github.com/joke2k/faker) from 17.6.0 to 18.3.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v17.6.0...v18.3.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`cff3a01`](https://github.com/supabase/auth-py/commit/cff3a0113c8fca149a21a3b8feb0f512ceb992c3))

* chore(deps-dev): bump python-semantic-release from 7.33.1 to 7.33.2

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.33.1 to 7.33.2.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.33.1...v7.33.2)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`70c4ed6`](https://github.com/supabase/auth-py/commit/70c4ed670927eaba03a323752b2539f7be35f5e1))

* chore(deps-dev): bump faker from 17.3.0 to 17.6.0

Bumps [faker](https://github.com/joke2k/faker) from 17.3.0 to 17.6.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v17.3.0...v17.6.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`8ba18fd`](https://github.com/supabase/auth-py/commit/8ba18fd6d16bf98fbd8fb5cff186ec4322ce6189))

* chore(deps): bump abatilo/actions-poetry from 2.2.0 to 2.3.0

Bumps [abatilo/actions-poetry](https://github.com/abatilo/actions-poetry) from 2.2.0 to 2.3.0.
- [Release notes](https://github.com/abatilo/actions-poetry/releases)
- [Changelog](https://github.com/abatilo/actions-poetry/blob/master/.releaserc)
- [Commits](https://github.com/abatilo/actions-poetry/compare/v2.2.0...v2.3.0)

---
updated-dependencies:
- dependency-name: abatilo/actions-poetry
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`e28fd25`](https://github.com/supabase/auth-py/commit/e28fd25a03f09468237a08accc7546210461d4ea))

* chore(deps-dev): bump pytest from 7.2.1 to 7.2.2

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`fc53e5b`](https://github.com/supabase/auth-py/commit/fc53e5b659e0bfbf27f6276e4450565722097e12))

* chore(deps-dev): bump faker from 17.0.0 to 17.3.0

Bumps [faker](https://github.com/joke2k/faker) from 17.0.0 to 17.3.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v17.0.0...v17.3.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`ee32bd9`](https://github.com/supabase/auth-py/commit/ee32bd90bdf4e2e598dbaf777d747dedb98e02ff))

* chore(deps-dev): bump pre-commit from 3.1.0 to 3.1.1

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 3.1.0 to 3.1.1.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v3.1.0...v3.1.1)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`2bf3dce`](https://github.com/supabase/auth-py/commit/2bf3dcee6dab4287e03d16905891a51b1a79fab9))

* chore(deps-dev): bump pre-commit from 3.0.4 to 3.1.0

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`c9b9f95`](https://github.com/supabase/auth-py/commit/c9b9f959f158c808ac1cbe0576dd53f5e798f654))

* chore(deps-dev): bump pygithub from 1.57 to 1.58.0

Bumps [pygithub](https://github.com/pygithub/pygithub) from 1.57 to 1.58.0.
- [Release notes](https://github.com/pygithub/pygithub/releases)
- [Changelog](https://github.com/PyGithub/PyGithub/blob/master/doc/changes.rst)
- [Commits](https://github.com/pygithub/pygithub/compare/v1.57...v1.58.0)

---
updated-dependencies:
- dependency-name: pygithub
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`c6f0b49`](https://github.com/supabase/auth-py/commit/c6f0b49d971ac5aaa0a77eccf13c623f6d23e5f2))

* chore(deps-dev): bump faker from 16.8.1 to 17.0.0

Bumps [faker](https://github.com/joke2k/faker) from 16.8.1 to 17.0.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v16.8.1...v17.0.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`911f5cb`](https://github.com/supabase/auth-py/commit/911f5cba28f0ccd0b1194ec414d08d0db416dbdf))

* chore(deps): bump pydantic from 1.10.4 to 1.10.5 (#233)

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
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a785e16`](https://github.com/supabase/auth-py/commit/a785e16c79a76d9a897d58dbc17f370a014038b0))

* chore(deps-dev): bump faker from 16.7.0 to 16.8.1

Bumps [faker](https://github.com/joke2k/faker) from 16.7.0 to 16.8.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v16.7.0...v16.8.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`e7088a7`](https://github.com/supabase/auth-py/commit/e7088a72d647483841857d00d6c33153ed39de51))

* chore(deps): bump cryptography from 39.0.0 to 39.0.1

Bumps [cryptography](https://github.com/pyca/cryptography) from 39.0.0 to 39.0.1.
- [Release notes](https://github.com/pyca/cryptography/releases)
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/39.0.0...39.0.1)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`c84f04d`](https://github.com/supabase/auth-py/commit/c84f04d42f8e25e0fd492861b82d03c6d0ec98a5))

* chore(deps-dev): bump faker from 16.6.1 to 16.7.0

Bumps [faker](https://github.com/joke2k/faker) from 16.6.1 to 16.7.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v16.6.1...v16.7.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7d5cbfc`](https://github.com/supabase/auth-py/commit/7d5cbfcf2a94533dc106db4fbda20aa0e0d14070))

### Feature

* feat: bump version to 1.0.1 ([`0056efc`](https://github.com/supabase/auth-py/commit/0056efccd35b824f952b53d6a42a73fffb42553f))

### Fix

* fix: run black ([`a37afe3`](https://github.com/supabase/auth-py/commit/a37afe39c3930c022010d018647d325d8d583d33))

* fix: patch padding for base64 ([`4ae0a21`](https://github.com/supabase/auth-py/commit/4ae0a2114e202f525ad9d992cd65c5297b7a934d))

### Unknown

* Merge pull request #259 from supabase-community/j0/bump_version

feat: bump version to 1.0.1 ([`359a003`](https://github.com/supabase/auth-py/commit/359a003b3b98e2e14902bb2658a97f27417469df))

* Merge pull request #256 from supabase-community/dependabot/pip/main/faker-18.3.1

chore(deps-dev): bump faker from 18.3.0 to 18.3.1 ([`578734e`](https://github.com/supabase/auth-py/commit/578734e896b46af9cf8c4991bdcce4e6caa40103))

* Merge pull request #254 from supabase-community/j0/patch_padding_for_base64

fix: patch padding for base64 ([`f77663a`](https://github.com/supabase/auth-py/commit/f77663ac11f6303f95677f4913c12f7765bd07f5))

* Update helpers.py ([`e1ba5e2`](https://github.com/supabase/auth-py/commit/e1ba5e2ab79484beda860c27961336771f73b15b))

* Merge pull request #252 from supabase-community/dependabot/pip/main/faker-18.3.0

chore(deps-dev): bump faker from 17.6.0 to 18.3.0 ([`5d075d2`](https://github.com/supabase/auth-py/commit/5d075d2649ac4c2942dfdc3cfad3459d43868a1e))

* Merge pull request #235 from supabase-community/dependabot/pip/main/python-semantic-release-7.33.2

chore(deps-dev): bump python-semantic-release from 7.33.1 to 7.33.2 ([`3476384`](https://github.com/supabase/auth-py/commit/3476384e75fd29b8efbc32b886c0c845d6b62e89))

* Merge pull request #244 from supabase-community/dependabot/pip/main/faker-17.6.0

chore(deps-dev): bump faker from 17.3.0 to 17.6.0 ([`03ba918`](https://github.com/supabase/auth-py/commit/03ba918d82c891d0ddcdda35f8c19c155403f9d4))

* Merge pull request #240 from supabase-community/dependabot/github_actions/main/abatilo/actions-poetry-2.3.0

chore(deps): bump abatilo/actions-poetry from 2.2.0 to 2.3.0 ([`3ec751b`](https://github.com/supabase/auth-py/commit/3ec751bbc97f6917fd7c3aace24dfb67e23efbda))

* Merge pull request #245 from supabase-community/dependabot/pip/main/pytest-7.2.2

chore(deps-dev): bump pytest from 7.2.1 to 7.2.2 ([`ad3b366`](https://github.com/supabase/auth-py/commit/ad3b3669bf2078725dbe660e0bb4a471b17ca6aa))

* Merge pull request #239 from supabase-community/dependabot/pip/main/faker-17.3.0

chore(deps-dev): bump faker from 17.0.0 to 17.3.0 ([`20fcfbd`](https://github.com/supabase/auth-py/commit/20fcfbd123d7ba495de492b1bd5384c6d9117ac3))

* Merge pull request #241 from supabase-community/dependabot/pip/main/pre-commit-3.1.1

chore(deps-dev): bump pre-commit from 3.1.0 to 3.1.1 ([`9a511ea`](https://github.com/supabase/auth-py/commit/9a511ea744cbb5c2e34cd2c14379b536520bc7bc))

* Merge pull request #238 from supabase-community/dependabot/pip/main/pre-commit-3.1.0

chore(deps-dev): bump pre-commit from 3.0.4 to 3.1.0 ([`5561e94`](https://github.com/supabase/auth-py/commit/5561e94cdbb697e02c0261ebae3f717d46dddbd9))

* Merge pull request #236 from supabase-community/dependabot/pip/main/pygithub-1.58.0

chore(deps-dev): bump pygithub from 1.57 to 1.58.0 ([`6c1247c`](https://github.com/supabase/auth-py/commit/6c1247c23302a81cfb33177f297f619d91a5fbb0))

* Merge pull request #232 from supabase-community/dependabot/pip/main/faker-17.0.0

chore(deps-dev): bump faker from 16.8.1 to 17.0.0 ([`d47b7c1`](https://github.com/supabase/auth-py/commit/d47b7c102c8e9ac7c46eda9b7fe977ff7c3beb0f))

* Merge pull request #230 from supabase-community/dependabot/pip/main/faker-16.8.1

chore(deps-dev): bump faker from 16.7.0 to 16.8.1 ([`9699606`](https://github.com/supabase/auth-py/commit/9699606e307d12f4e3b50461d62b0ba5e3e456e4))

* Merge pull request #228 from supabase-community/dependabot/pip/cryptography-39.0.1

chore(deps): bump cryptography from 39.0.0 to 39.0.1 ([`af1a7f0`](https://github.com/supabase/auth-py/commit/af1a7f064a3be09e1ca74e6f31328160c7c4db77))

* Merge pull request #229 from supabase-community/dependabot/pip/main/faker-16.7.0

chore(deps-dev): bump faker from 16.6.1 to 16.7.0 ([`db484db`](https://github.com/supabase/auth-py/commit/db484dbe0d1dbf959a219dc7f727fe43de6cdef3))

## v1.0.0 (2023-02-05)

### Chore

* chore(deps-dev): bump pre-commit from 2.21.0 to 3.0.4

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`c67fbda`](https://github.com/supabase/auth-py/commit/c67fbdac96ea2939a36d7f5cb2d7605b670bee07))

* chore(deps-dev): bump python-semantic-release from 7.33.0 to 7.33.1

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.33.0 to 7.33.1.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.33.0...v7.33.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`6423f19`](https://github.com/supabase/auth-py/commit/6423f19594cc324a029a9dc53e0dd7e9be3cdce2))

* chore(deps-dev): bump black from 22.12.0 to 23.1.0

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`3b2fd7f`](https://github.com/supabase/auth-py/commit/3b2fd7f2cea8ffd80a401c9f4f3d5031c3f3fddd))

* chore: update ci ([`dc3573c`](https://github.com/supabase/auth-py/commit/dc3573c466b139fc7fdb89670f0a2de08da38830))

* chore(deps-dev): bump faker from 16.6.0 to 16.6.1

Bumps [faker](https://github.com/joke2k/faker) from 16.6.0 to 16.6.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v16.6.0...v16.6.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`55bccec`](https://github.com/supabase/auth-py/commit/55bccec3816feda0d63809a4b625ffaecc3e623b))

* chore(deps-dev): bump faker from 15.3.4 to 16.6.0

Bumps [faker](https://github.com/joke2k/faker) from 15.3.4 to 16.6.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v15.3.4...v16.6.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`db13e78`](https://github.com/supabase/auth-py/commit/db13e785b995a3e8f8a18033e955388e7e277a14))

* chore: include 3.11 ([`f74c31f`](https://github.com/supabase/auth-py/commit/f74c31f5b413ebbabb37463d2c8ae2184aa90b81))

* chore: adjust ci poetry version ([`4d4685b`](https://github.com/supabase/auth-py/commit/4d4685bbcfeb81ec61fea86ffa404b5849a2fa1d))

* chore(deps): bump pydantic from 1.10.2 to 1.10.4

Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.2 to 1.10.4.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/v1.10.4/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v1.10.2...v1.10.4)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`be56f07`](https://github.com/supabase/auth-py/commit/be56f07810d726329884ddc1a3664fb4c3c57d7b))

* chore(deps-dev): bump pre-commit from 2.20.0 to 2.21.0

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 2.20.0 to 2.21.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v2.20.0...v2.21.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7116357`](https://github.com/supabase/auth-py/commit/711635725ff9143fb57e2652da448c5bd49e84fc))

* chore(deps): bump gitpython from 3.1.27 to 3.1.30

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.27 to 3.1.30.
- [Release notes](https://github.com/gitpython-developers/GitPython/releases)
- [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES)
- [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.27...3.1.30)

---
updated-dependencies:
- dependency-name: gitpython
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`8a1b4dd`](https://github.com/supabase/auth-py/commit/8a1b4dd2510feb731b8862a4971b32642ae9f8de))

* chore(deps): bump wheel from 0.37.1 to 0.38.1

Bumps [wheel](https://github.com/pypa/wheel) from 0.37.1 to 0.38.1.
- [Release notes](https://github.com/pypa/wheel/releases)
- [Changelog](https://github.com/pypa/wheel/blob/main/docs/news.rst)
- [Commits](https://github.com/pypa/wheel/compare/0.37.1...0.38.1)

---
updated-dependencies:
- dependency-name: wheel
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`ff9818c`](https://github.com/supabase/auth-py/commit/ff9818c960499b69a3863f5e19bfb7079d810566))

* chore(deps-dev): bump isort from 5.11.1 to 5.11.4

Bumps [isort](https://github.com/pycqa/isort) from 5.11.1 to 5.11.4.
- [Release notes](https://github.com/pycqa/isort/releases)
- [Changelog](https://github.com/PyCQA/isort/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pycqa/isort/compare/5.11.1...5.11.4)

---
updated-dependencies:
- dependency-name: isort
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`ba7cdc6`](https://github.com/supabase/auth-py/commit/ba7cdc6f4490e01ebcafad4768050998ea9a7307))

* chore(deps): bump httpx from 0.23.1 to 0.23.3

Bumps [httpx](https://github.com/encode/httpx) from 0.23.1 to 0.23.3.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.23.1...0.23.3)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`32ce139`](https://github.com/supabase/auth-py/commit/32ce139d602503287fe5a6846f2983cbcc42f8bb))

* chore(deps-dev): bump isort from 5.10.1 to 5.11.1 (#195)

Bumps [isort](https://github.com/pycqa/isort) from 5.10.1 to 5.11.1.
- [Release notes](https://github.com/pycqa/isort/releases)
- [Changelog](https://github.com/PyCQA/isort/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pycqa/isort/compare/5.10.1...5.11.1)

---
updated-dependencies:
- dependency-name: isort
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`d12d0c5`](https://github.com/supabase/auth-py/commit/d12d0c57e2111e3e4547a36761bd91749f856205))

* chore(deps-dev): bump black from 22.10.0 to 22.12.0

Bumps [black](https://github.com/psf/black) from 22.10.0 to 22.12.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/22.10.0...22.12.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`2207e09`](https://github.com/supabase/auth-py/commit/2207e095cb43648082bbad2e513e29a23920e0c1))

* chore(deps): bump certifi from 2022.6.15 to 2022.12.7 (#192)

Bumps [certifi](https://github.com/certifi/python-certifi) from 2022.6.15 to 2022.12.7.
- [Release notes](https://github.com/certifi/python-certifi/releases)
- [Commits](https://github.com/certifi/python-certifi/compare/2022.06.15...2022.12.07)

---
updated-dependencies:
- dependency-name: certifi
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`841083e`](https://github.com/supabase/auth-py/commit/841083e36c7098def95303d3e9eff3a94949b8c7))

* chore(deps-dev): bump pytest-asyncio from 0.20.2 to 0.20.3 (#193)

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.20.2 to 0.20.3.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Changelog](https://github.com/pytest-dev/pytest-asyncio/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.20.2...v0.20.3)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`2b8b03a`](https://github.com/supabase/auth-py/commit/2b8b03ab9c971a08c7e56ff2a41cbf976ce54b2a))

* chore(deps-dev): bump faker from 15.3.3 to 15.3.4 (#191)

Bumps [faker](https://github.com/joke2k/faker) from 15.3.3 to 15.3.4.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v15.3.3...v15.3.4)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`5773bf0`](https://github.com/supabase/auth-py/commit/5773bf0b97bf6fbc2a2adb61175d73941915bfa9))

* chore(deps): bump abatilo/actions-poetry from 2.1.6 to 2.2.0 (#190)

Bumps [abatilo/actions-poetry](https://github.com/abatilo/actions-poetry) from 2.1.6 to 2.2.0.
- [Release notes](https://github.com/abatilo/actions-poetry/releases)
- [Changelog](https://github.com/abatilo/actions-poetry/blob/master/.releaserc)
- [Commits](https://github.com/abatilo/actions-poetry/compare/v2.1.6...v2.2.0)

---
updated-dependencies:
- dependency-name: abatilo/actions-poetry
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ad040d1`](https://github.com/supabase/auth-py/commit/ad040d1428d5419e4a62b993e9946e872ecf5904))

* chore(deps-dev): bump faker from 15.3.2 to 15.3.3 (#189)

Bumps [faker](https://github.com/joke2k/faker) from 15.3.2 to 15.3.3.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v15.3.2...v15.3.3)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ab1f0da`](https://github.com/supabase/auth-py/commit/ab1f0dab02d57c2387b85016ddeb4103f7a0db55))

* chore(deps): bump httpx from 0.23.0 to 0.23.1 (#188)

Bumps [httpx](https://github.com/encode/httpx) from 0.23.0 to 0.23.1.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.23.0...0.23.1)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`dd04ad2`](https://github.com/supabase/auth-py/commit/dd04ad2eff2da019f65b1a37119d6f612fc4e5e4))

* chore(deps-dev): bump faker from 15.3.1 to 15.3.2 (#186)

Bumps [faker](https://github.com/joke2k/faker) from 15.3.1 to 15.3.2.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v15.3.1...v15.3.2)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`8d75f1c`](https://github.com/supabase/auth-py/commit/8d75f1cee71f74349a90922b945a82343f68963b))

* chore(deps): bump cryptography from 37.0.4 to 38.0.3 (#185)

Bumps [cryptography](https://github.com/pyca/cryptography) from 37.0.4 to 38.0.3.
- [Release notes](https://github.com/pyca/cryptography/releases)
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/37.0.4...38.0.3)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`6e0df2f`](https://github.com/supabase/auth-py/commit/6e0df2f2c357aef1d1384604d7012704a447217a))

* chore(deps-dev): bump pytest-asyncio from 0.20.1 to 0.20.2 (#184)

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.20.1 to 0.20.2.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Changelog](https://github.com/pytest-dev/pytest-asyncio/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.20.1...v0.20.2)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`bebb22f`](https://github.com/supabase/auth-py/commit/bebb22fe7b5ef2862388916e873b6db17dcb41f3))

* chore(deps-dev): bump faker from 15.1.3 to 15.3.1 (#183)

Bumps [faker](https://github.com/joke2k/faker) from 15.1.3 to 15.3.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v15.1.3...v15.3.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ae2043a`](https://github.com/supabase/auth-py/commit/ae2043ad8a0e1f1f0b4e2e7fd173f8277e15db6a))

* chore: update lock ([`9dd42b4`](https://github.com/supabase/auth-py/commit/9dd42b4c516879e208ca2d15d5934d682f9e4481))

* chore(deps-dev): bump faker from 15.1.1 to 15.1.3 (#182)

Bumps [faker](https://github.com/joke2k/faker) from 15.1.1 to 15.1.3.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v15.1.1...v15.1.3)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`2c15513`](https://github.com/supabase/auth-py/commit/2c15513f5986ff27448eba04e4c8e75140e96441))

* chore: fix EOL ([`44a4f25`](https://github.com/supabase/auth-py/commit/44a4f2573deb61ecdae704ec67f9e65c1dc25bd2))

* chore(deps-dev): bump pytest from 7.1.3 to 7.2.0 (#179)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.1.3 to 7.2.0.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.1.3...7.2.0)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`73df32a`](https://github.com/supabase/auth-py/commit/73df32a75e4621218db4a7a95cf5d5c123157a0b))

* chore(deps-dev): bump python-semantic-release from 7.32.1 to 7.32.2 (#177)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.32.1 to 7.32.2.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.32.1...v7.32.2)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`5aae844`](https://github.com/supabase/auth-py/commit/5aae8441185febd2db0439d486735e3724e3b437))

* chore(deps-dev): bump pytest-asyncio from 0.19.0 to 0.20.1

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.19.0 to 0.20.1.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Changelog](https://github.com/pytest-dev/pytest-asyncio/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.19.0...v0.20.1)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`89f1336`](https://github.com/supabase/auth-py/commit/89f133619118f4fbf8eaa9ef4b05283397fbfefd))

* chore: remove PyGithub as dep ([`08231ba`](https://github.com/supabase/auth-py/commit/08231baf14e72772e19f9d70ddd29e1b7387587e))

* chore: gen sync files ([`01385ea`](https://github.com/supabase/auth-py/commit/01385eac0c0ae79ae583b4ade84ab985f5933d20))

* chore: implement clients and utils for testing ([`6fbd3de`](https://github.com/supabase/auth-py/commit/6fbd3de4247f38ddd4af76422729658a8f0fb2da))

* chore(deps-dev): bump faker from 15.0.0 to 15.1.1

Bumps [faker](https://github.com/joke2k/faker) from 15.0.0 to 15.1.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v15.0.0...v15.1.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`69c7c4e`](https://github.com/supabase/auth-py/commit/69c7c4e0e9434a16195c7cc9fb2c29bd119362ca))

* chore(deps): fix poetry lock file ([`5148277`](https://github.com/supabase/auth-py/commit/514827788828799817ea47f3f89f442c163ba5be))

* chore(deps-dev): bump black from 22.8.0 to 22.10.0 (#170)

Bumps [black](https://github.com/psf/black) from 22.8.0 to 22.10.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/22.8.0...22.10.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`be6a2b3`](https://github.com/supabase/auth-py/commit/be6a2b330c8234b48b5af5e5a3e6586ab76a51d5))

* chore(deps-dev): bump python-semantic-release from 7.32.0 to 7.32.1 (#171)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.32.0 to 7.32.1.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.32.0...v7.32.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`6a02950`](https://github.com/supabase/auth-py/commit/6a0295001b5cd476e27b72fb77b34c6c2a1dee98))

* chore(deps-dev): bump pytest-cov from 3.0.0 to 4.0.0 (#168)

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
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`57ae3b3`](https://github.com/supabase/auth-py/commit/57ae3b33c925252fd2ec2faa2efbc911434393fa))

* chore(deps-dev): bump faker from 14.2.1 to 15.0.0 (#167)

Bumps [faker](https://github.com/joke2k/faker) from 14.2.1 to 15.0.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v14.2.1...v15.0.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`cc918f9`](https://github.com/supabase/auth-py/commit/cc918f90e57288f32ed081555c4b104947837340))

* chore(deps-dev): bump python-semantic-release from 7.31.4 to 7.32.0 (#165)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.31.4 to 7.32.0.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.31.4...v7.32.0)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`b8a9944`](https://github.com/supabase/auth-py/commit/b8a99441c82b450b667741b1c05830e92eb63b4a))

* chore(deps-dev): bump faker from 14.2.0 to 14.2.1

Bumps [faker](https://github.com/joke2k/faker) from 14.2.0 to 14.2.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v14.2.0...v14.2.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`a16f952`](https://github.com/supabase/auth-py/commit/a16f95240d5215e07f330befa138f7aa6d329fc2))

* chore(deps): bump pydantic from 1.10.1 to 1.10.2 (#162)

Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.1 to 1.10.2.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v1.10.1...v1.10.2)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`4666845`](https://github.com/supabase/auth-py/commit/46668453b0fbb0411af78f171b0dae80c5e2c23f))

* chore(deps-dev): bump pytest from 7.1.2 to 7.1.3 (#161)

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
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`b93c9d7`](https://github.com/supabase/auth-py/commit/b93c9d7d3f3f52f60effe5ffd17bfa400d46cd3c))

* chore(deps-dev): bump black from 22.6.0 to 22.8.0 (#159)

Bumps [black](https://github.com/psf/black) from 22.6.0 to 22.8.0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/compare/22.6.0...22.8.0)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`b552dea`](https://github.com/supabase/auth-py/commit/b552dea77b8d8cc058d6ba856f37f0f1d26d3480))

* chore(deps-dev): bump faker from 14.1.1 to 14.2.0 (#158)

Bumps [faker](https://github.com/joke2k/faker) from 14.1.1 to 14.2.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v14.1.1...v14.2.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`214353e`](https://github.com/supabase/auth-py/commit/214353e69e8da96ee628e87deac7c7f856e85c03))

* chore(deps): bump pydantic from 1.10.0 to 1.10.1 (#160)

Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.0 to 1.10.1.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v1.10.0...v1.10.1)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a322dce`](https://github.com/supabase/auth-py/commit/a322dce65f54de8a98d54c02dce0a12fdd5201c2))

* chore(deps): bump dev dependencies ([`93aabbe`](https://github.com/supabase/auth-py/commit/93aabbe1f5f130677b9a3765c998936940b75dc2))

* chore: format docstring to avoid linter warning ([`6a200fe`](https://github.com/supabase/auth-py/commit/6a200fead8b18cb06fe4fcf93c37b65345b48372))

* chore: update dependencies ([`6b15a50`](https://github.com/supabase/auth-py/commit/6b15a50466f82b87aae67823e08770c25cb352f6))

### Feature

* feat: bump to 1.0.0 ([`ac012cd`](https://github.com/supabase/auth-py/commit/ac012cda87d33f44fcc648fca0e166693f890ad3))

* feat: switch from flake8-&gt;ruff ([`19cdde0`](https://github.com/supabase/auth-py/commit/19cdde0867f9f1e5b7ef996fd162bbd3dc4e1a39))

* feat: move sphinx into doc group ([`173399b`](https://github.com/supabase/auth-py/commit/173399bb859bffd68b59bb7ff87d33501c92df62))

* feat: add docs ([`afc563a`](https://github.com/supabase/auth-py/commit/afc563add7782efeeab2ca967ca85e7476c864f3))

* feat: mfa challenge and verify and refresh session ([`b714206`](https://github.com/supabase/auth-py/commit/b7142060c99d06270bdcde9ecc2f823c33cf11b4))

* feat: add mfa ([`4c2b443`](https://github.com/supabase/auth-py/commit/4c2b4437d0b99c6f19ec251e245909d86ca69f8f))

* feat: implement decode_jwt_payload in helpers ([`c3ff22a`](https://github.com/supabase/auth-py/commit/c3ff22a0a8758585ee77a68381041b77ac25a234))

### Fix

* fix: adjust timer units and drop * 1000 since timer takes in seconds and not miliseconds ([`78ed6d2`](https://github.com/supabase/auth-py/commit/78ed6d224bc73cd89defb26b84a8ccf9c95dc68c))

* fix: reinstate 3.8 ([`58db1be`](https://github.com/supabase/auth-py/commit/58db1be7939c7aae1d50e7e29dee3a8f110775e4))

* fix: bump isort and python version ([`7f50501`](https://github.com/supabase/auth-py/commit/7f505016f04c1befc9db75a7f2dd71089b224eb4))

* fix: move dependency ([`1e51fce`](https://github.com/supabase/auth-py/commit/1e51fce51b32cada87d94efc8cf11f6a1aa6b282))

* fix: regenerate lock ([`34b8fb1`](https://github.com/supabase/auth-py/commit/34b8fb1aaf383a149efaa8f5832cbc82782b91d4))

* fix: add jwt package ([`36e8d12`](https://github.com/supabase/auth-py/commit/36e8d12e10f5f8494a7e5b00bf443678f6db0e47))

* fix: revert poetry.lock to original main files ([`df4ab8f`](https://github.com/supabase/auth-py/commit/df4ab8fa9ddbcf966026e98a9617f652f1f91179))

* fix: checkout main poetry.lock and poetry.toml ([`c8aeabc`](https://github.com/supabase/auth-py/commit/c8aeabc06dd6208f13e7934e0d70bf7bac8ea487))

* fix: remove ruff ([`ef21730`](https://github.com/supabase/auth-py/commit/ef21730997d23f51c9f52123742436c53dc96d29))

* fix: comment out sphinx ([`d46cf0d`](https://github.com/supabase/auth-py/commit/d46cf0d195b293f2f285190a726208c033a4722c))

* fix: remove group from pyproject.toml ([`41349d2`](https://github.com/supabase/auth-py/commit/41349d2cebf239a3529d92c2d848ca1cf78cc4f3))

* fix: revert dependency group ([`a923e52`](https://github.com/supabase/auth-py/commit/a923e52ecebc5706c210135b0bfeaaccf78fffd8))

* fix: stray EOLS ([`33cefba`](https://github.com/supabase/auth-py/commit/33cefba743b326647aee7c8639f000894dd609e9))

* fix: include modules page ([`8dab491`](https://github.com/supabase/auth-py/commit/8dab491fc1ce754f9d5aa27eab0e4c938b1342cd))

* fix: patch merge conflicts on next ([`fb033e4`](https://github.com/supabase/auth-py/commit/fb033e44208be7f3ae611eefd83d48d379909c44))

* fix: bugs in admin api and finish tests implementation ([`9db7ce6`](https://github.com/supabase/auth-py/commit/9db7ce680326c149730ef84cbe9540ad8a735676))

* fix: list users method of admin api ([`a973a1c`](https://github.com/supabase/auth-py/commit/a973a1cce3ea90e3c3ece0def70626c68727ae0d))

* fix: respect EXPIRY_MARGIN on getSession ([`45afb35`](https://github.com/supabase/auth-py/commit/45afb351ebe960a292edb77d4ea77bc235ee1563))

* fix: use literal from typing extensions ([`ec6618b`](https://github.com/supabase/auth-py/commit/ec6618b0c4e1ac0137f98debbc02b98e61e8ef60))

* fix: insert default content type header ([`332f782`](https://github.com/supabase/auth-py/commit/332f782db88921ef30a5362e054fd39d26166d2d))

* fix: implement the reset_password_email method ([`6ffa532`](https://github.com/supabase/auth-py/commit/6ffa53227d991c2135b5a1fd5202fea97e8d6097))

### Refactor

* refactor: migrate to implementation as similar as possible to the implementation of gotrue-js

The tests still need to be implemented. ([`4cb7713`](https://github.com/supabase/auth-py/commit/4cb771352e7f4065b2aac5de1c2b1260a0771268))

### Test

* test: add test to user fetch methods of admin api ([`8c076f0`](https://github.com/supabase/auth-py/commit/8c076f0d23411b0ee1861b91739f45069275c630))

### Unknown

* Merge pull request #227 from supabase-community/j0/new_release

feat: bump to 1.0.0 ([`b5cdd36`](https://github.com/supabase/auth-py/commit/b5cdd3687eab5923f117c3d2bcfd824f5d8ee842))

* Merge pull request #226 from supabase-community/dependabot/pip/main/pre-commit-3.0.4

chore(deps-dev): bump pre-commit from 2.21.0 to 3.0.4 ([`53c1fef`](https://github.com/supabase/auth-py/commit/53c1fefc057292fc8aec564e2849b6fcc2f011cd))

* Merge pull request #225 from supabase-community/dependabot/pip/main/python-semantic-release-7.33.1

chore(deps-dev): bump python-semantic-release from 7.33.0 to 7.33.1 ([`527d8a0`](https://github.com/supabase/auth-py/commit/527d8a0a631d05f84d44a89b179e9fd4255a9abd))

* Merge pull request #223 from supabase-community/dependabot/pip/main/black-23.1.0

chore(deps-dev): bump black from 22.12.0 to 23.1.0 ([`2941512`](https://github.com/supabase/auth-py/commit/2941512c479ea6fb4c2e0344f4d46f1de366d0d6))

* Merge pull request #220 from supabase-community/j0/fix_timer_units

fix: adjust timer units and drop * 1000 ([`758fb2f`](https://github.com/supabase/auth-py/commit/758fb2fd32c858181442f4b117a54d16b70ea519))

* Merge pull request #148 from supabase-community/next

next release - feature parity - high testing coverage ([`b79e2a8`](https://github.com/supabase/auth-py/commit/b79e2a842cc6a49d1831a2690f13283db3b5ed4c))

* Merge pull request #219 from supabase-community/j0/patch_conflicts_on_next

chore: patch merge conflicts on next ([`66f3f3a`](https://github.com/supabase/auth-py/commit/66f3f3aad672cb8c8f33e02f25d164311a4e688b))

* Merge branch &#39;main&#39; of github.com:supabase-community/gotrue-py into j0/patch_conflicts_on_next ([`1682747`](https://github.com/supabase/auth-py/commit/1682747cad333b1731841d18eee748ee16361420))

* Merge pull request #218 from supabase-community/dependabot/pip/main/faker-16.6.1

chore(deps-dev): bump faker from 16.6.0 to 16.6.1 ([`52d4c8d`](https://github.com/supabase/auth-py/commit/52d4c8db450de015f04a18d80d80ec41991a88f4))

* Merge pull request #213 from supabase-community/dependabot/pip/main/faker-16.6.0

chore(deps-dev): bump faker from 15.3.4 to 16.6.0 ([`2217833`](https://github.com/supabase/auth-py/commit/2217833bc80629288d980dbff22ade936b696b6d))

* Merge pull request #214 from supabase-community/j0/bump-poetry

chore: adjust ci poetry version ([`a43f38b`](https://github.com/supabase/auth-py/commit/a43f38b81a9f87ebc6b00f130f07041f5faaf77b))

* Merge pull request #203 from supabase-community/dependabot/pip/main/pydantic-1.10.4

chore(deps): bump pydantic from 1.10.2 to 1.10.4 ([`cf1faed`](https://github.com/supabase/auth-py/commit/cf1faedc712bf379ebf32a2f88c79480fc2a28bb))

* Merge pull request #200 from supabase-community/dependabot/pip/main/pre-commit-2.21.0

chore(deps-dev): bump pre-commit from 2.20.0 to 2.21.0 ([`9711f54`](https://github.com/supabase/auth-py/commit/9711f5440b9452d487366d99b340e1956f0c1f47))

* Merge pull request #206 from supabase-community/dependabot/pip/gitpython-3.1.30

chore(deps): bump gitpython from 3.1.27 to 3.1.30 ([`5861c0c`](https://github.com/supabase/auth-py/commit/5861c0cfe0fd38bc664657a0bb9fd13fb547fcd9))

* Merge pull request #201 from supabase-community/dependabot/pip/wheel-0.38.1

chore(deps): bump wheel from 0.37.1 to 0.38.1 ([`26c1eea`](https://github.com/supabase/auth-py/commit/26c1eeac67dfee01352f019d9f140c10ff6eb426))

* Merge pull request #199 from supabase-community/dependabot/pip/main/isort-5.11.4

chore(deps-dev): bump isort from 5.11.1 to 5.11.4 ([`80f2cf2`](https://github.com/supabase/auth-py/commit/80f2cf27e7e4efd7a57ed7fcb9529f5025dd822b))

* Merge pull request #205 from supabase-community/dependabot/pip/main/httpx-0.23.3

chore(deps): bump httpx from 0.23.1 to 0.23.3 ([`b8ae350`](https://github.com/supabase/auth-py/commit/b8ae350047aef889e11dd042425af9691b0533cb))

* Merge pull request #180 from supabase-community/j0/add_docs

feat: add docs for GoTrue ([`f7eade8`](https://github.com/supabase/auth-py/commit/f7eade84b66e0cbe4143d47181cc053d1b46e159))

* revert: remove ruff from ci ([`34535dd`](https://github.com/supabase/auth-py/commit/34535ddeb4e3577a0231a098f9abdd3475ed6467))

* Merge pull request #194 from supabase-community/dependabot/pip/main/black-22.12.0

chore(deps-dev): bump black from 22.10.0 to 22.12.0 ([`dff74c6`](https://github.com/supabase/auth-py/commit/dff74c6abc9da6939dc7c384e5ec4e2ea270e13a))

* Merge branch &#39;j0/add_docs&#39; of github.com:supabase-community/gotrue-py into j0/add_docs ([`7c5ea9c`](https://github.com/supabase/auth-py/commit/7c5ea9cbf957e0b37be0fcc09c71d922bdca8480))

* Merge branch &#39;main&#39; into j0/add_docs ([`24fbb46`](https://github.com/supabase/auth-py/commit/24fbb46852bb1f311cb7f8358b2806834ca80be3))

* Merge branch &#39;j0/add_docs&#39; of github.com:supabase-community/gotrue-py into j0/add_docs ([`798ef1c`](https://github.com/supabase/auth-py/commit/798ef1cd86751de8fd55fd1aeef30ad6ef1548be))

* Merge pull request #181 from supabase-community/sourcery/j0/add_docs

feat: add docs for GoTrue (Sourcery refactored) ([`7482f1a`](https://github.com/supabase/auth-py/commit/7482f1a6c42103e5b7a410f8326d596e61846a3e))

* &#39;Refactored by Sourcery&#39; ([`d26ff18`](https://github.com/supabase/auth-py/commit/d26ff1880cc55fe467beae0a3b59f629d79a212e))

* Merge pull request #178 from supabase-community/dependabot/pip/main/pytest-asyncio-0.20.1

chore(deps-dev): bump pytest-asyncio from 0.19.0 to 0.20.1 ([`e20893a`](https://github.com/supabase/auth-py/commit/e20893a9a9dc0be47883962396d91378ab2de81d))

* tests: add python 3.11 and update poetry version ([`33756af`](https://github.com/supabase/auth-py/commit/33756af49f995017cf3d9fdfd581b4974f13003c))

* tests: add tests for create user in admin api ([`30fd751`](https://github.com/supabase/auth-py/commit/30fd7512221145363f1ac5fb44fed86cdb08eb6d))

* Merge remote-tracking branch &#39;remotes/origin/next&#39; into next ([`20638fe`](https://github.com/supabase/auth-py/commit/20638fe9b8388367ce72669817c2590070ad60d6))

* &#39;Refactored by Sourcery&#39; (#176)

Co-authored-by: Sourcery AI &lt;&gt; ([`d5a0920`](https://github.com/supabase/auth-py/commit/d5a092095145459c4c67321915cabfb723170909))

* &#39;Refactored by Sourcery&#39; (#175)

Co-authored-by: Sourcery AI &lt;&gt; ([`9e4a1f2`](https://github.com/supabase/auth-py/commit/9e4a1f2c7caba255cb9e31eb546f28a9a469b205))

* Merge branch &#39;main&#39; into next ([`4e3be99`](https://github.com/supabase/auth-py/commit/4e3be993dd11dcaad542bae2177783c37a8e165c))

* Merge pull request #174 from supabase-community/dependabot/pip/main/faker-15.1.1

chore(deps-dev): bump faker from 15.0.0 to 15.1.1 ([`dbe13b7`](https://github.com/supabase/auth-py/commit/dbe13b7355b6767f4412e74be283f2abe8277091))

* &#39;Refactored by Sourcery&#39; (#172)

Co-authored-by: Sourcery AI &lt;&gt; ([`20b882c`](https://github.com/supabase/auth-py/commit/20b882cc2501ac39dce5b6fe622d0fd27d946eea))

* Merge branch &#39;main&#39; into next ([`9f80bbc`](https://github.com/supabase/auth-py/commit/9f80bbcdefdec2d9af3a895a3752956b158887c9))

* Merge pull request #164 from supabase-community/dependabot/pip/main/faker-14.2.1

chore(deps-dev): bump faker from 14.2.0 to 14.2.1 ([`7c5a665`](https://github.com/supabase/auth-py/commit/7c5a665aec69acc905588fb6a61019281a3de70a))

* Merge branch &#39;main&#39; into next ([`971b816`](https://github.com/supabase/auth-py/commit/971b816646268d7740b40a4c018af27a38aaa4b9))

## v0.5.4 (2022-08-31)

### Chore

* chore: setup version 0.5.4 for new release (#157)

* chore: setup version 0.5.4 for new release

* chore: update version of __init__.py

* chore: update changelog ([`d559e2d`](https://github.com/supabase/auth-py/commit/d559e2dedfbadde1e604087d8677cdb8aa63d7d6))

* chore(deps-dev): bump faker from 14.1.0 to 14.1.1 (#154)

Bumps [faker](https://github.com/joke2k/faker) from 14.1.0 to 14.1.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v14.1.0...v14.1.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`272ad56`](https://github.com/supabase/auth-py/commit/272ad56d212ed37b6a6a60c8ce2c6613d2cb9ec1))

* chore(deps): bump pydantic from 1.9.2 to 1.10.0 (#153)

Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.9.2 to 1.10.0.
- [Release notes](https://github.com/pydantic/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
- [Commits](https://github.com/pydantic/pydantic/compare/v1.9.2...v1.10.0)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`913e014`](https://github.com/supabase/auth-py/commit/913e0142d92cf4c77e42624314577d5e29deed69))

* chore(deps): bump abatilo/actions-poetry from 2.1.5 to 2.1.6 (#152)

Bumps [abatilo/actions-poetry](https://github.com/abatilo/actions-poetry) from 2.1.5 to 2.1.6.
- [Release notes](https://github.com/abatilo/actions-poetry/releases)
- [Changelog](https://github.com/abatilo/actions-poetry/blob/master/.releaserc)
- [Commits](https://github.com/abatilo/actions-poetry/compare/v2.1.5...v2.1.6)

---
updated-dependencies:
- dependency-name: abatilo/actions-poetry
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`62311f3`](https://github.com/supabase/auth-py/commit/62311f3598fb57f2559483f175fb2ff8b4c0f154))

* chore: add github action ecosystem to dependabot ([`76d9114`](https://github.com/supabase/auth-py/commit/76d91148e9e9bac13e3f771a9f09a98fbd9986b9))

* chore(deps-dev): bump python-semantic-release from 7.31.3 to 7.31.4 (#151)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.31.3 to 7.31.4.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.31.3...v7.31.4)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`62adb59`](https://github.com/supabase/auth-py/commit/62adb5918229335af6998ebe4084f6ed0b56cd3d))

* chore(deps-dev): bump python-semantic-release from 7.31.2 to 7.31.3 (#150)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.31.2 to 7.31.3.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.31.2...v7.31.3)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a9c110d`](https://github.com/supabase/auth-py/commit/a9c110d37f7c6f732681e0a15676dfc0ac3c9af8))

* chore: change made by pyupgrade pre-commit ([`68ed829`](https://github.com/supabase/auth-py/commit/68ed829b33db91a95ef5fef28b344f84f1ecaccd))

* chore: add sourcery config file ([`5be3c33`](https://github.com/supabase/auth-py/commit/5be3c335822c7963b95dbce98db6ae4d5ae24d1c))

* chore: implement script to sync config of infra ([`896a40c`](https://github.com/supabase/auth-py/commit/896a40c06f6800b0f0b3eb81a386cf00219f793c))

* chore: upgrade dependencies ([`41ee2dd`](https://github.com/supabase/auth-py/commit/41ee2dd79eb02c65c20554f327b595ffb4bb936c))

* chore(deps-dev): bump faker from 14.0.0 to 14.1.0 (#147)

Bumps [faker](https://github.com/joke2k/faker) from 14.0.0 to 14.1.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v14.0.0...v14.1.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`0c85e7e`](https://github.com/supabase/auth-py/commit/0c85e7ed8e7c79187200b19d151bba63251d1c71))

* chore(deps-dev): bump faker from 13.15.1 to 14.0.0 (#146)

Bumps [faker](https://github.com/joke2k/faker) from 13.15.1 to 14.0.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v13.15.1...v14.0.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`2374b04`](https://github.com/supabase/auth-py/commit/2374b04c17b1ab30f3d4996b5c01bcb2ebda5a9b))

* chore(deps): bump pydantic from 1.9.1 to 1.9.2 (#145)

Bumps [pydantic](https://github.com/samuelcolvin/pydantic) from 1.9.1 to 1.9.2.
- [Release notes](https://github.com/samuelcolvin/pydantic/releases)
- [Changelog](https://github.com/pydantic/pydantic/blob/v1.9.2/HISTORY.md)
- [Commits](https://github.com/samuelcolvin/pydantic/compare/v1.9.1...v1.9.2)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`db929b4`](https://github.com/supabase/auth-py/commit/db929b4f91846f83e7a72c8d32d455c533e79d14))

* chore(deps-dev): bump flake8 from 5.0.3 to 5.0.4 (#144)

Bumps [flake8](https://github.com/pycqa/flake8) from 5.0.3 to 5.0.4.
- [Release notes](https://github.com/pycqa/flake8/releases)
- [Commits](https://github.com/pycqa/flake8/compare/5.0.3...5.0.4)

---
updated-dependencies:
- dependency-name: flake8
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`456c818`](https://github.com/supabase/auth-py/commit/456c818ac6b9c0ddc822d586fa774f32b32891f9))

* chore(deps-dev): bump flake8 from 5.0.1 to 5.0.3 (#143)

Bumps [flake8](https://github.com/pycqa/flake8) from 5.0.1 to 5.0.3.
- [Release notes](https://github.com/pycqa/flake8/releases)
- [Commits](https://github.com/pycqa/flake8/compare/5.0.1...5.0.3)

---
updated-dependencies:
- dependency-name: flake8
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`d84e005`](https://github.com/supabase/auth-py/commit/d84e005173014ceaa09be9106e83145f5770da64))

* chore(deps-dev): bump python-semantic-release from 7.31.1 to 7.31.2 (#141)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.31.1 to 7.31.2.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.31.1...v7.31.2)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`b08ccf7`](https://github.com/supabase/auth-py/commit/b08ccf7fd2394735964b0aca9f90d474c7b0e50d))

* chore(deps-dev): bump flake8 from 4.0.1 to 5.0.1 (#142)

Bumps [flake8](https://github.com/pycqa/flake8) from 4.0.1 to 5.0.1.
- [Release notes](https://github.com/pycqa/flake8/releases)
- [Commits](https://github.com/pycqa/flake8/compare/4.0.1...5.0.1)

---
updated-dependencies:
- dependency-name: flake8
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`4c62d77`](https://github.com/supabase/auth-py/commit/4c62d77da0f1c281c24aabb0a90acc87861c1825))

* chore(deps-dev): bump python-semantic-release from 7.30.2 to 7.31.1 (#140)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.30.2 to 7.31.1.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.30.2...v7.31.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`8aba5b5`](https://github.com/supabase/auth-py/commit/8aba5b56d0e7177d3edbb2ee1535592eb05ffbb6))

* chore(deps-dev): bump python-semantic-release from 7.30.1 to 7.30.2 (#139)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.30.1 to 7.30.2.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.30.1...v7.30.2)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`93aa22b`](https://github.com/supabase/auth-py/commit/93aa22b9d4de65ad10983d7254076048b926b265))

* chore(deps-dev): bump python-semantic-release from 7.29.7 to 7.30.1 (#138)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.29.7 to 7.30.1.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.29.7...v7.30.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`4e464eb`](https://github.com/supabase/auth-py/commit/4e464eb16737cf77d24de95185d6ac772b14f178))

* chore(deps-dev): bump faker from 13.15.0 to 13.15.1 (#136)

Bumps [faker](https://github.com/joke2k/faker) from 13.15.0 to 13.15.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v13.15.0...v13.15.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`606f158`](https://github.com/supabase/auth-py/commit/606f158cbe900165757bae2d8624dc5c90d8b533))

* chore(deps-dev): bump python-semantic-release from 7.29.5 to 7.29.7 (#137)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.29.5 to 7.29.7.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.29.5...v7.29.7)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`74a9410`](https://github.com/supabase/auth-py/commit/74a9410067e302040eff3aba064b230ccf2a9216))

* chore: upgrade pytest-asyncio ([`1fc2fa9`](https://github.com/supabase/auth-py/commit/1fc2fa968851c42947f9733f1ad7a169d475be2c))

### Fix

* fix: use str type instead of uuid type in id property of identity model (#156) ([`460208d`](https://github.com/supabase/auth-py/commit/460208d16db5a49f682563c29dcfdf138d384c23))

### Unknown

* &#39;Refactored by Sourcery&#39; (#149)

Co-authored-by: Sourcery AI &lt;&gt; ([`07f897e`](https://github.com/supabase/auth-py/commit/07f897ed3eddd93c9411f8f23f83948ed71bf674))

* Merge remote-tracking branch &#39;origin/main&#39; ([`dde85fb`](https://github.com/supabase/auth-py/commit/dde85fbf5e404d3787c1da55cf216cf75f0578d8))

## v0.5.3 (2022-07-17)

### Chore

* chore: bump version to 0.5.3 ([`7d7d43e`](https://github.com/supabase/auth-py/commit/7d7d43e7f284e8916515b4d4ef79bcc0174df58b))

* chore(deps-dev): bump python-semantic-release from 7.29.4 to 7.29.5 (#131)

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.29.4 to 7.29.5.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/relekang/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.29.4...v7.29.5)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c506308`](https://github.com/supabase/auth-py/commit/c506308603ebaca0a54d6ab4517f0116cb7f07b9))

### Fix

* fix: set total false to user attributes typed dict ([`b21d6e3`](https://github.com/supabase/auth-py/commit/b21d6e385d72d0d94729d2427ab3bdcf178a1efb))

## v0.5.2 (2022-07-13)

### Chore

* chore: upgrade changelog ([`b72f7e9`](https://github.com/supabase/auth-py/commit/b72f7e9cebeb42206b02e29f49f64051312a18e2))

* chore: bump version to 0.5.2 in __init__.py ([`345e978`](https://github.com/supabase/auth-py/commit/345e9782733fb0a6fd916026fe47a859a4742e0f))

* chore: bump version to 0.5.2 ([`95e8fdd`](https://github.com/supabase/auth-py/commit/95e8fddf4892d8bb8e7584d5f2455de7a6c708c4))

* chore(deps-dev): bump pre-commit from 2.19.0 to 2.20.0 (#128)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`76fad56`](https://github.com/supabase/auth-py/commit/76fad56d7eb0ad7966569389fa6639d4b6c9995d))

* chore(deps-dev): bump faker from 13.14.0 to 13.15.0 (#127)

Bumps [faker](https://github.com/joke2k/faker) from 13.14.0 to 13.15.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v13.14.0...v13.15.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`0f2e0e5`](https://github.com/supabase/auth-py/commit/0f2e0e51cf3356c84a1a9cf87f435688b69a315c))

### Feature

* feat: change `.update` method to also allow dictionaries (#130)

* Allow users to send a dict instead of UserAttributes model

* Add tests

* Check Python version before trying to import TypedDict

* Remove `TypedDict` from the main `typing` import

* Change format

* Change format of types

* &#39;Refactored by Sourcery&#39;

Co-authored-by: odiseo0 &lt;pedro.esserweb@gmail.com&gt;
Co-authored-by: Sourcery AI &lt;&gt; ([`df3f69e`](https://github.com/supabase/auth-py/commit/df3f69ea18599a651715271d546b684555933286))

## v0.5.1 (2022-07-05)

### Chore

* chore: implement github action for manual release ([`cd8a590`](https://github.com/supabase/auth-py/commit/cd8a590effe65fa5ce1eb1fe3eef265e6f5fd655))

* chore: setup release ([`0a9ca44`](https://github.com/supabase/auth-py/commit/0a9ca445c7042057be0025562da85aceed22e8e3))

* chore(deps-dev): bump python-semantic-release from 7.28.0 to 7.28.1 (#110)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`8a19b39`](https://github.com/supabase/auth-py/commit/8a19b3941d4a0eb06e5f2d3479a3c99b3cced0fd))

* chore(deps-dev): bump pre-commit from 2.17.0 to 2.18.1 (#107)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`d0abb73`](https://github.com/supabase/auth-py/commit/d0abb73ccccc0eefbd0dfcea95766bb29ae96be7))

* chore(deps-dev): bump black from 22.1.0 to 22.3.0 (#105)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`d2e6761`](https://github.com/supabase/auth-py/commit/d2e676150b2a5d72bf9464bfb44442401f452605))

* chore(deps-dev): bump faker from 13.3.3 to 13.3.4 (#106)

Bumps [faker](https://github.com/joke2k/faker) from 13.3.3 to 13.3.4.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v13.3.3...v13.3.4)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a309526`](https://github.com/supabase/auth-py/commit/a309526dc6302a791b780476b12428d8ad1d7781))

* chore(deps-dev): bump python-semantic-release from 7.27.0 to 7.28.0 (#109)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`8042862`](https://github.com/supabase/auth-py/commit/804286224c86a45163f722aae42ac18deb05293e))

* chore(deps-dev): bump pytest-asyncio from 0.18.2 to 0.18.3 (#104)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`270bd1e`](https://github.com/supabase/auth-py/commit/270bd1e6b267f36a3b944ba3588bbc7d48feb09c))

* chore(deps-dev): bump faker from 13.3.2 to 13.3.3 (#103)

Bumps [faker](https://github.com/joke2k/faker) from 13.3.2 to 13.3.3.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v13.3.2...v13.3.3)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`bea6573`](https://github.com/supabase/auth-py/commit/bea65739c558e25a842c2b399d413724a00cd113))

* chore(deps-dev): bump pytest from 7.1.0 to 7.1.1 (#102)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c0d06af`](https://github.com/supabase/auth-py/commit/c0d06af7b870e2c1085a4034738a32856a384306))

* chore(deps-dev): bump python-semantic-release from 7.26.0 to 7.27.0 (#101)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3bfe980`](https://github.com/supabase/auth-py/commit/3bfe980ffb6b743fab101a981695ecb10196d9a8))

* chore(deps-dev): bump faker from 13.3.1 to 13.3.2 (#100)

Bumps [faker](https://github.com/joke2k/faker) from 13.3.1 to 13.3.2.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v13.3.1...v13.3.2)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`feb9bc6`](https://github.com/supabase/auth-py/commit/feb9bc6938f1995299fb88c0a085f795f0440e1f))

* chore(deps-dev): bump pytest from 7.0.1 to 7.1.0

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`c8181d2`](https://github.com/supabase/auth-py/commit/c8181d2bc6076599611b9e17203c81d8650584c3))

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`aaddf78`](https://github.com/supabase/auth-py/commit/aaddf78696aa599264a0dd665458ec491cc57c32))

* chore(deps-dev): bump faker from 13.3.0 to 13.3.1 (#97)

Bumps [faker](https://github.com/joke2k/faker) from 13.3.0 to 13.3.1.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v13.3.0...v13.3.1)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`26428de`](https://github.com/supabase/auth-py/commit/26428de8aa1c1202adc65ca4e1c4687fd62badf5))

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`6e7b257`](https://github.com/supabase/auth-py/commit/6e7b257023497e6fecd79d396cfc106762f4785c))

* chore(deps-dev): bump faker from 13.2.0 to 13.3.0 (#95)

Bumps [faker](https://github.com/joke2k/faker) from 13.2.0 to 13.3.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v13.2.0...v13.3.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`627404c`](https://github.com/supabase/auth-py/commit/627404cd5dc93fb0ecb4f594922360d9fd048a68))

* chore(deps-dev): bump python-semantic-release from 7.25.1 to 7.25.2 (#94)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3273350`](https://github.com/supabase/auth-py/commit/327335056f1c82684019436aafde129573bc91a8))

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c2e54a6`](https://github.com/supabase/auth-py/commit/c2e54a698de49581c6e72dea1f918b4745cd67dc))

* chore(deps-dev): bump faker from 13.0.0 to 13.2.0 (#92)

Bumps [faker](https://github.com/joke2k/faker) from 13.0.0 to 13.2.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v13.0.0...v13.2.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e0156bc`](https://github.com/supabase/auth-py/commit/e0156bc214d1bcd5229f83190e084c1b8b1cf551))

* chore(deps-dev): bump python-semantic-release from 7.24.0 to 7.25.0 (#91)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9b30df6`](https://github.com/supabase/auth-py/commit/9b30df6872f3b36e8cdd277ae84161233e6bd3c3))

* chore(deps-dev): bump faker from 12.3.3 to 13.0.0 (#90)

Bumps [faker](https://github.com/joke2k/faker) from 12.3.3 to 13.0.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v12.3.3...v13.0.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ff1653e`](https://github.com/supabase/auth-py/commit/ff1653eb9ab98b99e6200d3bfbea7a36dbadf079))

* chore(deps-dev): bump faker from 12.3.0 to 12.3.3 (#89)

Bumps [faker](https://github.com/joke2k/faker) from 12.3.0 to 12.3.3.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v12.3.0...v12.3.3)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`da7c173`](https://github.com/supabase/auth-py/commit/da7c173353b683bd682b8f84325d47b9a2818b6c))

* chore(deps-dev): bump pytest from 7.0.0 to 7.0.1 (#88)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ec198b0`](https://github.com/supabase/auth-py/commit/ec198b07e200cfd98c8e7f8e3e946a1bcd3cbf97))

* chore(deps-dev): bump faker from 12.2.0 to 12.3.0 (#87)

Bumps [faker](https://github.com/joke2k/faker) from 12.2.0 to 12.3.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v12.2.0...v12.3.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3addee0`](https://github.com/supabase/auth-py/commit/3addee0a7b9f4af834f11bab86b7dc4480f6635c))

* chore(deps-dev): bump pytest-asyncio from 0.17.2 to 0.18.1 (#86)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`f14e19d`](https://github.com/supabase/auth-py/commit/f14e19d1a31a1f61fd192f48d68684f591f08a02))

* chore(deps-dev): bump faker from 12.1.0 to 12.2.0 (#85)

Bumps [faker](https://github.com/joke2k/faker) from 12.1.0 to 12.2.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v12.1.0...v12.2.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`df71a96`](https://github.com/supabase/auth-py/commit/df71a964f56172a4fd6292defc76f52a812f8a88))

* chore(deps-dev): bump faker from 12.0.0 to 12.1.0 (#83)

Bumps [faker](https://github.com/joke2k/faker) from 12.0.0 to 12.1.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v12.0.0...v12.1.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`809b75d`](https://github.com/supabase/auth-py/commit/809b75d2c02b489e7b4a2fe4c7944343b97a6912))

* chore(deps-dev): bump pytest from 6.2.5 to 7.0.0 (#82)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`7a749ac`](https://github.com/supabase/auth-py/commit/7a749ac3227ba0825a211dd85503e81a89f9708b))

* chore(deps-dev): bump faker from 11.3.0 to 12.0.0 (#81)

Bumps [faker](https://github.com/joke2k/faker) from 11.3.0 to 12.0.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v11.3.0...v12.0.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`f54751a`](https://github.com/supabase/auth-py/commit/f54751a7baba7dd250d16193efd4eb7522454cf1))

* chore(deps-dev): bump black from 21.12b0 to 22.1.0 (#80)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a284212`](https://github.com/supabase/auth-py/commit/a28421291f145c11cbc36c6a2c46c86803a7e848))

* chore(deps): bump httpx from 0.21.3 to 0.22.0 (#79)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9e2101d`](https://github.com/supabase/auth-py/commit/9e2101dfd657f30a0b6665943dfbd51b51299deb))

* chore(deps-dev): bump python-semantic-release from 7.23.0 to 7.24.0 (#78)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`84c6071`](https://github.com/supabase/auth-py/commit/84c60712cae9fe2277530ef525960d795d52f7be))

### Fix

* fix: upgrade dependencies and fix tests (#126)

* fix: upgrade dependencies

* fix: update docker-compose of infra

* chore: upgrade pre-commit config

* chore: upgrade github action for ci ([`c9f2bde`](https://github.com/supabase/auth-py/commit/c9f2bde349f3f4e415366966ce0a39a1ac2084f2))

### Unknown

* Merge pull request #99 from supabase-community/dependabot/pip/main/pytest-7.1.0

chore(deps-dev): bump pytest from 7.0.1 to 7.1.0 ([`657f07b`](https://github.com/supabase/auth-py/commit/657f07b8dc6a7a49ef0badf11e6e97d143a3250a))

## v0.5.0 (2022-01-20)

### Chore

* chore(release): bump version to v0.5.0

Automatically generated by python-semantic-release ([`888ba1b`](https://github.com/supabase/auth-py/commit/888ba1b9bcb8c4c89c3910408213053afac8e553))

* chore: set upload_to_repository to true ([`6316827`](https://github.com/supabase/auth-py/commit/63168276afd5e7786c8c55baadceef6ad60ab14f))

* chore(deps-dev): bump pytest-asyncio from 0.17.1 to 0.17.2 (#73)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c6d4d09`](https://github.com/supabase/auth-py/commit/c6d4d09deac00bf0c58b3a4f7da6a7303c423790))

* chore(deps-dev): bump pre-commit from 2.16.0 to 2.17.0 (#74)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`150ae9d`](https://github.com/supabase/auth-py/commit/150ae9d71c9d034d0f86d43683203e1702266f57))

* chore(deps-dev): bump pytest-asyncio from 0.17.0 to 0.17.1 (#72)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`bc6f391`](https://github.com/supabase/auth-py/commit/bc6f391f07ba22467503cf25be3db48bebd58c14))

### Documentation

* docs: add maintainers file ([`2f5f005`](https://github.com/supabase/auth-py/commit/2f5f005235e90127cb7effde7396bb55088b815f))

### Feature

* feat: add create user param to sign in (#75)

* feat: add create user param to sign in

ref: https://github.com/supabase/gotrue/pull/318

* &#39;Refactored by Sourcery&#39; (#76)

Co-authored-by: Sourcery AI &lt;&gt;

* chore: format code

* chore: format code

Co-authored-by: sourcery-ai[bot] &lt;58596630+sourcery-ai[bot]@users.noreply.github.com&gt; ([`57ec6d8`](https://github.com/supabase/auth-py/commit/57ec6d8efe1233c1b90a8585045e6f85a4a3c17b))

## v0.4.0 (2022-01-17)

### Chore

* chore(release): bump version to v0.4.0

Automatically generated by python-semantic-release ([`d2e138c`](https://github.com/supabase/auth-py/commit/d2e138c8143cceab47dc6cd67089a53c0f259be9))

### Feature

* feat: add notion to enum of providers (#70)

* feat: add notion to enum of providers

* &#39;Refactored by Sourcery&#39; (#71)

Co-authored-by: Sourcery AI &lt;&gt;

Co-authored-by: sourcery-ai[bot] &lt;58596630+sourcery-ai[bot]@users.noreply.github.com&gt; ([`a8f2c45`](https://github.com/supabase/auth-py/commit/a8f2c45b25c9d008de7a5e1e6f18cc47a259c73c))

## v0.3.5 (2022-01-15)

### Chore

* chore(release): bump version to v0.3.5

Automatically generated by python-semantic-release ([`5034285`](https://github.com/supabase/auth-py/commit/50342856e4823136890b98d38d306cd8a83708c2))

* chore(deps-dev): bump pytest-asyncio from 0.16.0 to 0.17.0 (#67)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e1acdf3`](https://github.com/supabase/auth-py/commit/e1acdf3036883bf7cabcb6cac9e7b9f5ac99a651))

### Fix

* fix: delete_user returns Exception event if response is Ok (#68)

* fix: delete_user returns Exception event if response is Ok

* &#39;Refactored by Sourcery&#39; (#69)

Co-authored-by: Sourcery AI &lt;&gt;

* chore: format code

Co-authored-by: sourcery-ai[bot] &lt;58596630+sourcery-ai[bot]@users.noreply.github.com&gt; ([`23c167e`](https://github.com/supabase/auth-py/commit/23c167e7082c5ddb4dd64b958aa55065c2b3e468))

## v0.3.4 (2022-01-13)

### Chore

* chore(release): bump version to v0.3.4

Automatically generated by python-semantic-release ([`4b5ce2f`](https://github.com/supabase/auth-py/commit/4b5ce2f583ca84a972445a7cd08ffd44bbbb03c9))

* chore: fix http warning use ([`19005e2`](https://github.com/supabase/auth-py/commit/19005e2b9715075a9fb9bb0a75b7b786b9710aac))

* chore: fix http warning use (#61)

because the intention is good but instead receives an annoying print. ([`ae20a8e`](https://github.com/supabase/auth-py/commit/ae20a8ea7bd0979cd48e06b426a2c8534efea93c))

* chore: fix config ([`2f94bfd`](https://github.com/supabase/auth-py/commit/2f94bfdbc2cf20ef50ec777bbda03face1da3e85))

### Fix

* fix: string formatting in `delete_user` (#64)

* fix: string formatting (vs. javascript style) ([`d783015`](https://github.com/supabase/auth-py/commit/d783015b5d2472fe95a83f5d42efe97f79331516))

## v0.3.3 (2022-01-08)

### Chore

* chore(release): bump version to v0.3.3

Automatically generated by python-semantic-release ([`d355393`](https://github.com/supabase/auth-py/commit/d355393bacc339678543b2637dcc9295c41bc8b7))

* chore(deps): upgrade dependencies ([`029bcd4`](https://github.com/supabase/auth-py/commit/029bcd49c7d986ee2454e8517474f212f996d9c5))

* chore(deps): bump httpx from 0.21.2 to 0.21.3 (#60)

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

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`328f2bb`](https://github.com/supabase/auth-py/commit/328f2bb52c4cff4d5f0ced91861e574eec3242ad))

* chore: remove skip of tests (#59)

* chore: remove skip of tests in async version

* chore: remove skip of tests in sync version ([`70b1286`](https://github.com/supabase/auth-py/commit/70b128680588c8bb96ec0d0e1a2a66820a590222))

* chore(deps-dev): bump faker from 11.1.0 to 11.3.0

Bumps [faker](https://github.com/joke2k/faker) from 11.1.0 to 11.3.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v11.1.0...v11.3.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`67a52e8`](https://github.com/supabase/auth-py/commit/67a52e8ad178695367bda26d01fc7c469803487e))

* chore(deps): bump httpx from 0.21.1 to 0.21.2

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`52c9a4a`](https://github.com/supabase/auth-py/commit/52c9a4ae593fe80471a37e0e3a328345816fac53))

* chore: filter deploy section by repo owner ([`c28e6c7`](https://github.com/supabase/auth-py/commit/c28e6c76152fc81882b514b108e629c1aea3504f))

* chore: add ignore md rules to dev container and fix changelog ([`2638c1b`](https://github.com/supabase/auth-py/commit/2638c1b5bc1da97826812546b4e7902111b46fa9))

* chore: update poetry version in ci github action ([`a1e765d`](https://github.com/supabase/auth-py/commit/a1e765d87331638ac038c76f6a4f3f8d538571f4))

* chore: add python versions badge to readme ([`cb407bd`](https://github.com/supabase/auth-py/commit/cb407bd4e00c8e1c3fdfab7773a61ee797bae60f))

* chore: fix rule in makefile ([`455d0ce`](https://github.com/supabase/auth-py/commit/455d0cefe2163f24f3246a8673a03ab10730bc19))

### Unknown

* Merge pull request #57 from supabase-community/dependabot/pip/main/faker-11.3.0

chore(deps-dev): bump faker from 11.1.0 to 11.3.0 ([`2ffcd22`](https://github.com/supabase/auth-py/commit/2ffcd22050a977c8b852445cd12f493a03695fd5))

* Merge pull request #58 from supabase-community/dependabot/pip/main/httpx-0.21.2

chore(deps): bump httpx from 0.21.1 to 0.21.2 ([`79cc984`](https://github.com/supabase/auth-py/commit/79cc98453e2cebdffab7ebcdf86e6b59a98c32fd))

* Merge pull request #56 from leynier/main

chore: filter deploy section by repo owner ([`b07bd7b`](https://github.com/supabase/auth-py/commit/b07bd7ba73be931569e176daef073b53edfc356f))

* Merge pull request #55 from leynier/chore/add-ignore-md-rules-to-dev-container-and-fix-changelog

chore: add ignore md rules to dev container and fix changelog ([`b74576d`](https://github.com/supabase/auth-py/commit/b74576d7e20d9a5dffaac66572243aa02120f4da))

* Merge pull request #53 from supabase-community/chore/add-python-versions-badge-to-readme

chore: add python versions badge to readme ([`ad2e2ea`](https://github.com/supabase/auth-py/commit/ad2e2ea0a7b3b6b27ef99dcf6c157e90fd750244))

* Merge pull request #54 from supabase-community/chore/fix-rule-in-makefile

chore: fix rule in makefile ([`56fd621`](https://github.com/supabase/auth-py/commit/56fd621474f2c25f96924b9f4e666864e32fd28f))

## v0.3.2 (2022-01-04)

### Chore

* chore(release): bump version to v0.3.2

Automatically generated by python-semantic-release ([`4183894`](https://github.com/supabase/auth-py/commit/41838949e87bd52c9c6a6522f477c93bfa0c21ca))

* chore(deps): bump pydantic from 1.8.2 to 1.9.0

Bumps [pydantic](https://github.com/samuelcolvin/pydantic) from 1.8.2 to 1.9.0.
- [Release notes](https://github.com/samuelcolvin/pydantic/releases)
- [Changelog](https://github.com/samuelcolvin/pydantic/blob/master/HISTORY.md)
- [Commits](https://github.com/samuelcolvin/pydantic/compare/v1.8.2...v1.9.0)

---
updated-dependencies:
- dependency-name: pydantic
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`92b3b94`](https://github.com/supabase/auth-py/commit/92b3b944fde4507877c1e2dada5eb77a1b8209cc))

### Fix

* fix: deploy action ([`467fa3f`](https://github.com/supabase/auth-py/commit/467fa3f6b9e09295806cbac3e8c4fcfe05c3147d))

### Unknown

* Merge pull request #52 from leynier/fix/deploy-action

fix: deploy action ([`4c05816`](https://github.com/supabase/auth-py/commit/4c058169fa6c43721dd03afa0dca65dcdac2f94c))

* Merge pull request #51 from supabase-community/dependabot/pip/main/pydantic-1.9.0

chore(deps): bump pydantic from 1.8.2 to 1.9.0 ([`293065c`](https://github.com/supabase/auth-py/commit/293065cf895bc5b458431769faba5ed870c251a8))

## v0.3.1 (2022-01-02)

### Chore

* chore: bumping version to v0.3.1 ([`9498105`](https://github.com/supabase/auth-py/commit/9498105ed63903a5a04c427cf345d15235fef1e3))

### Unknown

* Merge pull request #49 from supabase-community/inherit-from-exception

Inherit from Exception ([`f415aa0`](https://github.com/supabase/auth-py/commit/f415aa0a7a2cdb4a54cd2c61e5aa2db6221aa05e))

* Inherit from Exception

Inherit from Exception instead of from BaseException.
More info: [https://docs.python.org/3/tutorial/errors.html#tut-userexceptions](https://docs.python.org/3/tutorial/errors.html#tut-userexceptions) ([`3347136`](https://github.com/supabase/auth-py/commit/33471366b95b32303314c6b4d3938cd768a28fc4))

## v0.3.0 (2021-12-29)

### Chore

* chore(deps-dev): bump faker from 11.0.0 to 11.1.0

Bumps [faker](https://github.com/joke2k/faker) from 11.0.0 to 11.1.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v11.0.0...v11.1.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`2802b80`](https://github.com/supabase/auth-py/commit/2802b80d0e6169117f169cb26df88dd532954205))

* chore(deps-dev): bump faker from 10.0.0 to 11.0.0

Bumps [faker](https://github.com/joke2k/faker) from 10.0.0 to 11.0.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v10.0.0...v11.0.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`fe56fa2`](https://github.com/supabase/auth-py/commit/fe56fa2d4427746797cfba01982193adea67f164))

* chore(deps-dev): bump commitizen from 2.20.2 to 2.20.3

Bumps [commitizen](https://github.com/commitizen-tools/commitizen) from 2.20.2 to 2.20.3.
- [Release notes](https://github.com/commitizen-tools/commitizen/releases)
- [Changelog](https://github.com/commitizen-tools/commitizen/blob/master/CHANGELOG.md)
- [Commits](https://github.com/commitizen-tools/commitizen/compare/v2.20.2...v2.20.3)

---
updated-dependencies:
- dependency-name: commitizen
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`1f7ecb8`](https://github.com/supabase/auth-py/commit/1f7ecb8a44f77b14552e678fc244c78f38b41b73))

* chore(deps-dev): bump sphinx from 4.3.1 to 4.3.2

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 4.3.1 to 4.3.2.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/4.x/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v4.3.1...v4.3.2)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`57c73f3`](https://github.com/supabase/auth-py/commit/57c73f338e5135f38f09d88d6e60442848a59bbb))

* chore(deps-dev): bump faker from 9.8.2 to 10.0.0

Bumps [faker](https://github.com/joke2k/faker) from 9.8.2 to 10.0.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v9.8.2...v10.0.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`d012ae8`](https://github.com/supabase/auth-py/commit/d012ae88341accfa9b79666d3b9e1a68cdf594f4))

* chore(deps): update poetry.lock ([`882388f`](https://github.com/supabase/auth-py/commit/882388f0b162cd4dae714623c3c5dde5a4ab8b72))

* chore(deps-dev): bump commitizen from 2.20.0 to 2.20.2

Bumps [commitizen](https://github.com/commitizen-tools/commitizen) from 2.20.0 to 2.20.2.
- [Release notes](https://github.com/commitizen-tools/commitizen/releases)
- [Changelog](https://github.com/commitizen-tools/commitizen/blob/master/CHANGELOG.md)
- [Commits](https://github.com/commitizen-tools/commitizen/compare/v2.20.0...v2.20.2)

---
updated-dependencies:
- dependency-name: commitizen
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`4210dba`](https://github.com/supabase/auth-py/commit/4210dba0050667cd2d7d2dac52c8a1430d08d3a5))

* chore: add noqa comment ([`360cc0d`](https://github.com/supabase/auth-py/commit/360cc0da2ad3a552964a61578f05ec77f87021ad))

* chore: add --remove-orphans to clean_infra and increase sleep time ([`ad504ae`](https://github.com/supabase/auth-py/commit/ad504ae1a2a5037d5f0d33a9fab2a67ace56c320))

* chore(deps): update poetry.lock ([`3130b5a`](https://github.com/supabase/auth-py/commit/3130b5afd13ad2655b90655aa3be5f5e5c381db7))

* chore(deps-dev): bump black from 21.11b1 to 21.12b0

Bumps [black](https://github.com/psf/black) from 21.11b1 to 21.12b0.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/commits)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`bbc76f5`](https://github.com/supabase/auth-py/commit/bbc76f50ceb54a105f32c14c25d57e2d9caf0727))

* chore(deps-dev): bump faker from 9.9.0 to 10.0.0

Bumps [faker](https://github.com/joke2k/faker) from 9.9.0 to 10.0.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v9.9.0...v10.0.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`475e9f6`](https://github.com/supabase/auth-py/commit/475e9f6eba17b3a67d1ca1c4cf566832658ce480))

* chore: update dependencies ([`59635a9`](https://github.com/supabase/auth-py/commit/59635a9c1e66109fa1ac1d54812d6e88f2b845b2))

* chore(deps-dev): bump pre-commit from 2.15.0 to 2.16.0

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 2.15.0 to 2.16.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/master/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v2.15.0...v2.16.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7b8f8f7`](https://github.com/supabase/auth-py/commit/7b8f8f77ca5b9e39e7fe2cc9f72f7c49596f2954))

* chore(deps-dev): bump sphinx from 4.3.0 to 4.3.1

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 4.3.0 to 4.3.1.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/4.x/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v4.3.0...v4.3.1)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`5d64552`](https://github.com/supabase/auth-py/commit/5d6455266eced8dbb31ae868450ed98e71c072a1))

* chore: fix ci action with ignore chore commits ([`baa0acf`](https://github.com/supabase/auth-py/commit/baa0acfa1f93896e5d36694ba8abb595b20f88c2))

* chore(deps-dev): bump faker from 9.8.2 to 9.9.0

Bumps [faker](https://github.com/joke2k/faker) from 9.8.2 to 9.9.0.
- [Release notes](https://github.com/joke2k/faker/releases)
- [Changelog](https://github.com/joke2k/faker/blob/master/CHANGELOG.md)
- [Commits](https://github.com/joke2k/faker/compare/v9.8.2...v9.9.0)

---
updated-dependencies:
- dependency-name: faker
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`a905349`](https://github.com/supabase/auth-py/commit/a9053499ff1616b05cd3cf40b843a3b774ae9719))

* chore(deps-dev): bump pre-commit from 2.15.0 to 2.16.0

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 2.15.0 to 2.16.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/master/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v2.15.0...v2.16.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`fc369d6`](https://github.com/supabase/auth-py/commit/fc369d6001ed570fafbef4e8275a3e2c43f552ef))

* chore: add make rules for generate html report and clean infra ([`e4a1405`](https://github.com/supabase/auth-py/commit/e4a1405bbc101ecdb5c9d3f5cbe1b38f82b8fadd))

* chore: remove html report for try fix the gh action ([`f717a9f`](https://github.com/supabase/auth-py/commit/f717a9f45bcf5f7a1310d028f35cb528e7ce3404))

* chore: add html report to make rul ([`26783b5`](https://github.com/supabase/auth-py/commit/26783b583b28be8c35eb0d865242a60bd0567973))

* chore: add test ci and codecov badges ([`38597b3`](https://github.com/supabase/auth-py/commit/38597b37be5a16027186e719583d6477fd505367))

* chore: add badges to README.md ([`a74a0bf`](https://github.com/supabase/auth-py/commit/a74a0bfdf93b8efe3fd3a71e179e3a37181c54c6))

* chore: add pragma no cover comments ([`1256518`](https://github.com/supabase/auth-py/commit/1256518d534a0d84785a7fd60174fe25795dffd0))

* chore(deps): bump httpx from 0.20.0 to 0.21.1

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`3145377`](https://github.com/supabase/auth-py/commit/3145377da08dc4d595d4e01995fec16717f04661))

* chore(deps-dev): bump flake8 from 3.9.2 to 4.0.1

Bumps [flake8](https://github.com/pycqa/flake8) from 3.9.2 to 4.0.1.
- [Release notes](https://github.com/pycqa/flake8/releases)
- [Commits](https://github.com/pycqa/flake8/compare/3.9.2...4.0.1)

---
updated-dependencies:
- dependency-name: flake8
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`acde964`](https://github.com/supabase/auth-py/commit/acde9649bdb2fd5f198c30f039c38851c5f66abe))

* chore(deps-dev): bump black from 21.10b0 to 21.11b1

Bumps [black](https://github.com/psf/black) from 21.10b0 to 21.11b1.
- [Release notes](https://github.com/psf/black/releases)
- [Changelog](https://github.com/psf/black/blob/main/CHANGES.md)
- [Commits](https://github.com/psf/black/commits)

---
updated-dependencies:
- dependency-name: black
  dependency-type: direct:development
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`415f7d9`](https://github.com/supabase/auth-py/commit/415f7d93559111097ee6e8ddccd137423239f0b1))

* chore: remove unused noqa comment ([`fdc6318`](https://github.com/supabase/auth-py/commit/fdc6318c90bbd1b9696e8e521e8a60f2741862f2))

* chore: update dependencies ([`83e8f5e`](https://github.com/supabase/auth-py/commit/83e8f5e79d8465015b0796955e37b32dcd62552d))

* chore: remove Python 3.10 for unknow error ([`a261996`](https://github.com/supabase/auth-py/commit/a261996b9bfedb66f4bfc64f7ab5ad69ab13e6ce))

* chore: add Python 3.10 to GitHub Action ([`d782994`](https://github.com/supabase/auth-py/commit/d7829948628eff686d0836ffba7047abab1cf3a0))

* chore: remove noqa comments ([`8d2c74e`](https://github.com/supabase/auth-py/commit/8d2c74e5592f6f64dccd40116661ccfc97c88f0e))

* chore: revert to use single _ in &#34;private&#34; methods ([`45dbc4f`](https://github.com/supabase/auth-py/commit/45dbc4fde3c44993080400eb9217da1fa186b230))

* chore: changes by run pre-commit ([`f5b0b01`](https://github.com/supabase/auth-py/commit/f5b0b010cc8c338167956ece326745d54c057aa5))

* chore: split some make rules ([`843008b`](https://github.com/supabase/auth-py/commit/843008b9382adf2b595c8c6e24c1afc060417ef3))

* chore: add logs ([`068fe0d`](https://github.com/supabase/auth-py/commit/068fe0d4c65309b2be9fa1ed63864b79df6a3e84))

* chore: run ci in all branches ([`b3cba71`](https://github.com/supabase/auth-py/commit/b3cba7129d2c4bcb0120b79a7dab0f5f1caf26b2))

* chore: regenerate sync client ([`72b85b5`](https://github.com/supabase/auth-py/commit/72b85b59ccfe79f9cd56a730866931cee4379bbe))

* chore: separate tests rule in multiples rules ([`5815566`](https://github.com/supabase/auth-py/commit/5815566afe4cf56350e586ffde2dc7525b20098d))

* chore: add dependencies for code coverage and fix tests command ([`3ab70a5`](https://github.com/supabase/auth-py/commit/3ab70a5aded79520dd0ec3931f39764d7c24b5b4))

* chore: format code by pre-commit ([`2fbcb70`](https://github.com/supabase/auth-py/commit/2fbcb705f7be07e2d03471c004a2b3ed043f9b5a))

* chore: regenerate sync client ([`8ddd940`](https://github.com/supabase/auth-py/commit/8ddd940343e72ce3c9fd9eafa57ee160249ed50f))

* chore: format code of sync client ([`bfc5fab`](https://github.com/supabase/auth-py/commit/bfc5fabdd94e1826774f90a2fd4322848a9f719d))

* chore: add doc to on_auth_state_change ([`267c62c`](https://github.com/supabase/auth-py/commit/267c62ca3376c73be4202db368539b55c5096b51))

* chore: fix name of ci test job ([`2ac3930`](https://github.com/supabase/auth-py/commit/2ac3930946f8ff28fa2a1f68e6a36c95c52faf27))

* chore: change order of strategy parameter ([`ae0ba3f`](https://github.com/supabase/auth-py/commit/ae0ba3f2dc2363197404ba169ea0f74552eec240))

* chore: fix name of ci test job ([`112ce71`](https://github.com/supabase/auth-py/commit/112ce71e7180fec0f055e68b940290497b0d3e62))

* chore: format conftest.py ([`3400431`](https://github.com/supabase/auth-py/commit/34004311d70913b2d53e8a22f05dcedba1c48518))

* chore: formatting code ([`f9ff600`](https://github.com/supabase/auth-py/commit/f9ff600f82f14ee43be0a15d7eec91ce5079db2a))

* chore: fix warnings of markdown files ([`8992382`](https://github.com/supabase/auth-py/commit/8992382916932a064c208b4affbe8ed7b5d53892))

* chore: add poetry files (pyproject.toml and poetry.lock)

Remove requirements.txt and setup.py ([`01aea7f`](https://github.com/supabase/auth-py/commit/01aea7f611690c007983d6f418d1ecf215f9b3e7))

* chore: merge .gitignore files ([`7ce2d11`](https://github.com/supabase/auth-py/commit/7ce2d1176d955949adc51d0337acabf3e12c4e1d))

* chore: fix title of license ([`d82dc5c`](https://github.com/supabase/auth-py/commit/d82dc5cd491e633108b816637718ba2f3ea8f51b))

* chore: add code of conduct and license ([`a3dcc00`](https://github.com/supabase/auth-py/commit/a3dcc0027b3c66328ac8c302638bb6a6c0e28e3c))

* chore: update docker image &amp; remove lib from imports ([`71ce191`](https://github.com/supabase/auth-py/commit/71ce1918f5ad0372557036a99d0b5ea40a85ea46))

* chore: update gitignore to allow lib ([`2b46d3a`](https://github.com/supabase/auth-py/commit/2b46d3af24330af131ac0c4fa3c035bf408512ba))

* chore: unpeg requests ([`80486d1`](https://github.com/supabase/auth-py/commit/80486d14c6c1966c212a3656fa8f5173ab4a8c31))

* chore: update deps ([`c8c138b`](https://github.com/supabase/auth-py/commit/c8c138bb65748e61534a267e41f3041fe31212c2))

### Documentation

* docs: update some info of readme ([`20235fe`](https://github.com/supabase/auth-py/commit/20235fe1fcb04f5496bfeafc22fd43749d143173))

* docs: add description to aud field of User model ([`283bd9f`](https://github.com/supabase/auth-py/commit/283bd9f687f3f50af315cb7b7a33551df944a918))

* docs: add comment for email preferences over phone ([`e900c49`](https://github.com/supabase/auth-py/commit/e900c49587c2d96bcda43c05ca80de0b7d99eaf1))

### Feature

* feat: add job to github action for auto deploy ([`2f6bcf2`](https://github.com/supabase/auth-py/commit/2f6bcf2f85f7831319c0c86faf16027a02e50058))

* feat: add pre-commit hook for conventional commit ([`3eebc95`](https://github.com/supabase/auth-py/commit/3eebc95e325efa4162750661e25cb750bffb17f3))

* feat: add devcontainer.json for use github codespaces ([`0e78b62`](https://github.com/supabase/auth-py/commit/0e78b627c6175a177f6676082287b6cf739b9261))

* feat: add X-Client-Info to default headers ([`ec2c893`](https://github.com/supabase/auth-py/commit/ec2c893e275877a9fce8c327b454821b21cef4d1))

* feat: allow providing custom api and http client implementation

For follow dependency injection pattern

https://github.com/supabase/gotrue-js/pull/168 ([`c60718c`](https://github.com/supabase/auth-py/commit/c60718c0d413ea35a6c9c5076b2c0e843f068029))

* feat: add create_user and list_users

https://github.com/supabase/gotrue-js/pull/166 ([`72f05e2`](https://github.com/supabase/auth-py/commit/72f05e27248597590d96d5a423f3213e7dbc6341))

* feat: add datetime and uuid types ([`455794f`](https://github.com/supabase/auth-py/commit/455794fdca1a2c5cbad58dcc60e62043e96f6f2a))

* feat: add pyupgrade pre-commit hook ([`eaeae46`](https://github.com/supabase/auth-py/commit/eaeae46a23842833118516028de26687af1a8324))

* feat: migrate types to pydantic models ([`a0e4008`](https://github.com/supabase/auth-py/commit/a0e40088e329388d4f45ad0e53e13f2c09963198))

* feat: unify logic of __recover_session and __recover_and_refresh ([`b2eb4f2`](https://github.com/supabase/auth-py/commit/b2eb4f292ac62b9b37b9b037bdb33ead7b56bd69))

* feat: uuid4().hex instead of str(uuid4()) in _sync client ([`b91e556`](https://github.com/supabase/auth-py/commit/b91e5569dcf6edeeb8ea59f3ca69e31cf225dcf6))

* feat: uuid4().hex instead of str(uuid4())

Co-authored-by: dreinon &lt;67071425+dreinon@users.noreply.github.com&gt; ([`08565ac`](https://github.com/supabase/auth-py/commit/08565ac1cf89b4c4395927fba9a8a5320f972899))

* feat: add --ignore-init-module-imports to .pre-commit-config.yaml

Co-authored-by: dreinon &lt;67071425+dreinon@users.noreply.github.com&gt; ([`9c7a18c`](https://github.com/supabase/auth-py/commit/9c7a18c7bf74093d70e56b4e988f427c17d4133d))

* feat: add end-of-file-fixer to .pre-commit-config.yaml

Co-authored-by: dreinon &lt;67071425+dreinon@users.noreply.github.com&gt; ([`3ef3707`](https://github.com/supabase/auth-py/commit/3ef3707023d710d1f02cc4d2c35e17fed475b919))

* feat: use asdict of dataclasses for to_dicts ([`3333813`](https://github.com/supabase/auth-py/commit/3333813b6ed32d9d1129b4ab57ecc699be227386))

* feat: use annotations from __future__ ([`b16356d`](https://github.com/supabase/auth-py/commit/b16356ddd974fc8cfef7b4ec49b2d85e1b278922))

* feat: add identities to User

Reason: https://github.com/supabase/gotrue/commit/e3a52e64e3ae89e93984cdcbe822413f53a37484 ([`d042152`](https://github.com/supabase/auth-py/commit/d042152ce9731e6cd304a6c512880c3ea998d263))

* feat: use reflection for parsing dataclasses ([`3d226f5`](https://github.com/supabase/auth-py/commit/3d226f50d5aefde62566921ef30e2a23a030cc74))

* feat: implement and use cli for unasync ([`f70fdd2`](https://github.com/supabase/auth-py/commit/f70fdd200c2b676069e262d18a4d3f1cb8b4d99a))

* feat: force the use of keyword parameters ([`4cb8330`](https://github.com/supabase/auth-py/commit/4cb83308cd3185df4708904ef04f7858227c3009))

* feat: generate tests for sync client ([`46373e4`](https://github.com/supabase/auth-py/commit/46373e4233853bf2744c0c9e61d8dcc06cfea17d))

* feat: add Make rule for infra ([`6ac5334`](https://github.com/supabase/auth-py/commit/6ac533462173bde3776dd2fe481fae7b9268aa55))

* feat: add pre-commit system for check Pythonic style ([`09f9b47`](https://github.com/supabase/auth-py/commit/09f9b47c07c0b77cc5b9a031715c708d119b2d73))

* feat: add context manager support ([`42619ea`](https://github.com/supabase/auth-py/commit/42619eadfb6705c863377082a3ea77064f42d773))

* feat: implement sync/async support with httppx and unasync

The &#34;_sync&#34; folder is generated automatically with the
&#34;make build_sync&#34; command.

All scripts in the &#34;_async&#34; folder will be translated into their
synchronous form using &#34;unasync&#34; behind the scenes. ([`da10e87`](https://github.com/supabase/auth-py/commit/da10e875aaf34ecccc6066827e06e2b1c0e86370))

* feat: add poetry to CI action and add dependabot config file ([`ee916c2`](https://github.com/supabase/auth-py/commit/ee916c2760c9be7e60e52b6a126deb372423bf1a))

* feat: synchronize implementation of GoTrueClient ([`0a669de`](https://github.com/supabase/auth-py/commit/0a669de64170fe7074bd7e65742308be2c3ff869))

* feat: add CookieOptions to constructor of GoTrueApi ([`4ef1b55`](https://github.com/supabase/auth-py/commit/4ef1b55608135f88ee0ebf784fb234b28c405aa7))

* feat: implement SupportedStorage abstract storage and MemoryStorage storage ([`044efe8`](https://github.com/supabase/auth-py/commit/044efe828737eea26c1f1f62152e7676c9374063))

* feat: implement Subscription type ([`8c64876`](https://github.com/supabase/auth-py/commit/8c64876d61e3fc3b5806085fa9ec1e0885210ace))

* feat: implement AuthChangeEvent enum ([`a6dacaf`](https://github.com/supabase/auth-py/commit/a6dacaf4aca4c9f7b5ea801a0840ab7a3f6c118d))

* feat: implement CookieOptions type ([`930273f`](https://github.com/supabase/auth-py/commit/930273f28ec9e3b89954859c3ff299c406d17b67))

* feat: add types to API class and align implementation with gotrue-js ([`1ed9754`](https://github.com/supabase/auth-py/commit/1ed9754d932c34e3fcffafd4b63474802f22ae43))

* feat: add new types, implement to_dicts and align files with gotrue-js ([`25e223b`](https://github.com/supabase/auth-py/commit/25e223b7f92984239e343b02995aa86527320cc6))

* feat: implement dataclasses with methods for parsing ([`82d1d6c`](https://github.com/supabase/auth-py/commit/82d1d6c48626b7a4eabd9d513634eec102c9e004))

### Fix

* fix: error in from_dict of APIError ([`ef250f5`](https://github.com/supabase/auth-py/commit/ef250f5985337809c8c068ceca3c5bbca72ce1ed))

* fix: merged default headers instead of replace

Also add argument for replace or not default headers ([`96d390c`](https://github.com/supabase/auth-py/commit/96d390cd304baf9ceb73361bdaf8d2905af264b4))

* fix: error in recovery_mode of get_session_from_url ([`041406a`](https://github.com/supabase/auth-py/commit/041406aee3753e023a7ffad42a54cf9238384bce))

* fix: error in get_session_from_url ([`5f65e47`](https://github.com/supabase/auth-py/commit/5f65e472174eedbd0fb211ffa769cc21d6886b2a))

* fix: add a new TOKEN_REFRESHED event

https://github.com/supabase/gotrue-js/commit/0add6956a22c51c785d9d735edf38cac8a2c2368 ([`e702835`](https://github.com/supabase/auth-py/commit/e7028356cda625fff435c69d9772c85c0b072b4a))

* fix: get recovery mode before notify sign in event

https://github.com/supabase/gotrue-js/commit/9c0f42b50e60fac00bf52c30ad3548906cf49b0a ([`4ef96ce`](https://github.com/supabase/auth-py/commit/4ef96ce77861b62aec345f443af1e7b8710df83a))

* fix: remove duplicate var env in docker-compose.yml ([`6e501c9`](https://github.com/supabase/auth-py/commit/6e501c99ea115dbd537157c5da13945a17d10f15))

* fix: use str for declare Python 3.10 ([`2350250`](https://github.com/supabase/auth-py/commit/235025008437e3e2e07fd868632a276b90e42de1))

* fix: use expires_in var for avoid typing warning ([`4c7003e`](https://github.com/supabase/auth-py/commit/4c7003e6a2740f3a5c24db1a13d269ef72cfa82b))

* fix: use typing annotations ([`6905d45`](https://github.com/supabase/auth-py/commit/6905d451fcd6fa8448cfd9619f39e0ddc06dc45f))

* fix: use directly parse_obj instead of lambdas ([`177b619`](https://github.com/supabase/auth-py/commit/177b6194b8547590b1714931144ea2a1f8ff35a2))

* fix: use parse_obj ([`383298a`](https://github.com/supabase/auth-py/commit/383298a141093bbb00feeb3799e46526db008957))

* fix: set prefix __ instead of _ for private methods ([`c2d37fb`](https://github.com/supabase/auth-py/commit/c2d37fb40f7bdf24d8a072bc070ce88f462ffb65))

* fix: .pre-commit-config.yaml format ([`747f411`](https://github.com/supabase/auth-py/commit/747f411e26aed397e2a7a28858179991e75130b9))

* fix: change Api by API ([`13cc086`](https://github.com/supabase/auth-py/commit/13cc0865482fe72f129a4bc47e325519475ec831))

* fix: change ApiError by APIError in docstrings ([`55c03a6`](https://github.com/supabase/auth-py/commit/55c03a682aa875bae1456f6d17ae6f53d4f75218))

* fix: change ApiError by APIError

For follow https://www.python.org/dev/peps/pep-0008/#descriptive-naming-styles ([`98e27af`](https://github.com/supabase/auth-py/commit/98e27af6b656b78d96bb395906a3c85781ef909f))

* fix: add Optional to identities of User ([`21d7bda`](https://github.com/supabase/auth-py/commit/21d7bda2953f8db2d3d676939470981a144dbe05))

* fix: add slack adn spotify to Provider

Reason:

https://github.com/supabase/gotrue/commit/fc82846862435fdb96367a95b7b22503397ac0e0

https://github.com/supabase/gotrue/commit/79f2d6a741150a9a868fadbb1de87a2cd09da920 ([`73df8d7`](https://github.com/supabase/auth-py/commit/73df8d78573ff5599343f5f604caba56ecf3d526))

* fix: remove Optional to user_metadata of User

Reason: https://github.com/supabase/gotrue/commit/62e7ccd13cd41cd5571f75c4baae5ac0fb187e7c ([`dab27ce`](https://github.com/supabase/auth-py/commit/dab27ce49345c9ab043ae91e04e460042bc49b95))

* fix: remove email_change_confirm_status from User

Reason: https://github.com/supabase/gotrue/commit/df96c0678027515e5c4eb330efd0d26048aea6c6 ([`1859aa3`](https://github.com/supabase/auth-py/commit/1859aa37b2e55a1f65a4fdd6cb5c0175f20f40b1))

* fix: some fixes and changes requested ([`d224ec1`](https://github.com/supabase/auth-py/commit/d224ec14eeb59bb5b4d81dd2ad1e5c3cd86433b9))

* fix: some tipe hints ([`d1f5fc7`](https://github.com/supabase/auth-py/commit/d1f5fc774fd33283cfb4f465a39ac142b4e0b867))

* fix: error in client update ([`a653408`](https://github.com/supabase/auth-py/commit/a65340850db288a6f5e25d9c8370a6ad0c7de350))

* fix: errors in helpers and types ([`9870078`](https://github.com/supabase/auth-py/commit/98700789ab469059beb04d62617f79df0e749994))

* fix: ci github action ([`1ee2946`](https://github.com/supabase/auth-py/commit/1ee2946c119f9867930beab9dd6baf25c91919d6))

* fix: remove unnecessary async to on_auth_state_change ([`e7ebc64`](https://github.com/supabase/auth-py/commit/e7ebc64112d970673265c7b314a1e8820fc0f7e1))

* fix: error in remove_item of memory storage ([`9c12bd1`](https://github.com/supabase/auth-py/commit/9c12bd10d79680842cd324a50ce2ad2cee52c8a1))

* fix: cycle of references between helpers and types ([`fcad1af`](https://github.com/supabase/auth-py/commit/fcad1af6e0940986256678ae6059fabffdb60ec4))

* fix: use environ vars only if present ([`700129e`](https://github.com/supabase/auth-py/commit/700129e9f4731058506d4647ab77ed24d188cfb8))

* fix: reinstate lib __init__.py ([`b268219`](https://github.com/supabase/auth-py/commit/b268219db586f877e006fb7863b0504e10760e69))

* fix: reinstate lib.constants ([`edb9bb4`](https://github.com/supabase/auth-py/commit/edb9bb4217abd42b2c4db7b80d9a152c8fe1f3ae))

* fix: readjust indent in ci.yml ([`ca713c9`](https://github.com/supabase/auth-py/commit/ca713c9f58a94ae3d2bfd1137a42e44493524ba1))

### Test

* test: fix docker-compose and perf ci ([`5360967`](https://github.com/supabase/auth-py/commit/53609677568216e2eae789d4416a5848269cdd0f))

* test: add more tests to client layer ([`a2ca372`](https://github.com/supabase/auth-py/commit/a2ca372434865675afc46582c4ca919e50fab72b))

* test: change message

https://github.com/supabase/gotrue/commit/92abe187fd3d96645331542b477b37487cafce07 ([`4ec0e07`](https://github.com/supabase/auth-py/commit/4ec0e075cafd9e72369afb9c8313a71923455489))

* test: increases coverage

https://github.com/supabase/gotrue-js/commit/98300a0717c36197484873e53befc5fd25c57772 ([`367a09b`](https://github.com/supabase/auth-py/commit/367a09bb59180872667b8b213c4405733eb95998))

* test: fix test sign up the same user twice should throw an error ([`0ea666a`](https://github.com/supabase/auth-py/commit/0ea666ab8a008284e2e03fd0a67b57db6000e640))

* test: fix test_sign_up_the_same_user_twice_should_throw_an_error test

Reason: https://github.com/supabase/gotrue/commit/5bc665be3927b2ff4763c8315ee641093781ff98 ([`eb86078`](https://github.com/supabase/auth-py/commit/eb86078ea8929878d458c7d3b9324681b9780a3d))

* test: add various Python versions to CI ([`96eb94b`](https://github.com/supabase/auth-py/commit/96eb94bf0592587bfe34f27a9d5e6751b44eb31e))

* test: fix expected error message ([`1e65cc3`](https://github.com/supabase/auth-py/commit/1e65cc3bca5cd9f7f8838a20c4e7a2726515b30d))

* test: fix error in provider ([`e575d9b`](https://github.com/supabase/auth-py/commit/e575d9bafa66dc2318e2c9e6b7dbaa13995fc5e0))

* test: client with auto confirm enabled ([`b758dba`](https://github.com/supabase/auth-py/commit/b758dbae431146f0c0269ab44150904c5c899c64))

* test: use fixtures of pytest ([`c8daa2a`](https://github.com/supabase/auth-py/commit/c8daa2a871bcfaf306559bcbd888e303d408a39a))

* test: client with auto confirm disabled ([`c407a63`](https://github.com/supabase/auth-py/commit/c407a63ec79c47edc4905d08684083b77d7be091))

* test: client with sign ups disabled ([`08d2558`](https://github.com/supabase/auth-py/commit/08d2558557ab963ab4ed2c52153ee01489429fd2))

* test: handle exceptions and use context manager ([`b8330c0`](https://github.com/supabase/auth-py/commit/b8330c0c1c7193bcafe8d37dcfa4832660254160))

* test: implement tests for api with auto confirm disabled ([`0c29382`](https://github.com/supabase/auth-py/commit/0c29382b4f919d7a0dd8403a3bec11e7b81a8e18))

* test: ignore build_sync.py and conftest.py in Coverage ([`71a2c8f`](https://github.com/supabase/auth-py/commit/71a2c8f9b035bf12bcd1f2743b2791023bab7f26))

* test: implement provider and subscriptions tests

Comment test_gotrue.py mean while ([`67ecf57`](https://github.com/supabase/auth-py/commit/67ecf57439e4a95d1334661d52d9a1bb05c9e87d))

### Unknown

* Merge pull request #48 from supabase-community/dependabot/pip/main/faker-11.1.0

chore(deps-dev): bump faker from 11.0.0 to 11.1.0 ([`4590472`](https://github.com/supabase/auth-py/commit/459047270f1fc76e4103d8dc1814766ead3c3eb9))

* Merge pull request #47 from supabase-community/dependabot/pip/main/faker-11.0.0

chore(deps-dev): bump faker from 10.0.0 to 11.0.0 ([`116d9ba`](https://github.com/supabase/auth-py/commit/116d9ba296158ac8a705556287a04006167bb046))

* Merge pull request #46 from leynier/main

chore(deps-dev): bump sphinx from 4.3.0 to 4.3.2 and commitizen from 2.20.0 to 2.20.3 ([`544d8f1`](https://github.com/supabase/auth-py/commit/544d8f160100ab9e104ac3adf509c572c3eb7f53))

* Merge pull request #10 from leynier/dependabot/pip/main/commitizen-2.20.3

chore(deps-dev): bump commitizen from 2.20.2 to 2.20.3 ([`5846912`](https://github.com/supabase/auth-py/commit/5846912d6e832b851bf26fca4821e2228fdf7e9f))

* Merge pull request #11 from leynier/dependabot/pip/main/sphinx-4.3.2

chore(deps-dev): bump sphinx from 4.3.1 to 4.3.2 ([`308380b`](https://github.com/supabase/auth-py/commit/308380b8685d68d57d6c0bf34d8eff61f3d38dd2))

* Merge pull request #37 from leynier/main

fix: error in recovery_mode of get_session_from_url ([`740d866`](https://github.com/supabase/auth-py/commit/740d866ff0e4080c80f2cd5d1d199337ca236266))

* Merge remote-tracking branch &#39;remotes/upstream/main&#39; ([`0f05aa8`](https://github.com/supabase/auth-py/commit/0f05aa84da19088776c48cd9f0c7289ea45d58f2))

* Merge pull request #39 from supabase-community/dependabot/pip/main/faker-10.0.0

chore(deps-dev): bump faker from 9.8.2 to 10.0.0 ([`3878d91`](https://github.com/supabase/auth-py/commit/3878d910f8abbb9d92a88bfbb476d3a482fe538f))

* Merge pull request #9 from leynier/dependabot/pip/main/commitizen-2.20.2

chore(deps-dev): bump commitizen from 2.20.0 to 2.20.2 ([`838b136`](https://github.com/supabase/auth-py/commit/838b1369591a83a55a7731189f8c87d783b75b58))

* Merge pull request #8 from leynier/dependabot/pip/main/faker-10.0.0

chore(deps-dev): bump faker from 9.9.0 to 10.0.0 ([`31b537a`](https://github.com/supabase/auth-py/commit/31b537acdda45748f9c0370702242f14d9c1345f))

* Merge branch &#39;main&#39; into dependabot/pip/main/faker-10.0.0 ([`7408f5f`](https://github.com/supabase/auth-py/commit/7408f5f5d15e98602200bf3220000c52c4d80074))

* Merge pull request #7 from leynier/dependabot/pip/main/black-21.12b0

chore(deps-dev): bump black from 21.11b1 to 21.12b0 ([`7629707`](https://github.com/supabase/auth-py/commit/7629707b061a23d3ab90266855f0bf8b9679c840))

* Merge remote-tracking branch &#39;remotes/upstream/main&#39; ([`669d9df`](https://github.com/supabase/auth-py/commit/669d9dfa10122933873f35eb1aadb7d22339e16c))

* Merge pull request #36 from supabase-community/dependabot/pip/main/pre-commit-2.16.0

chore(deps-dev): bump pre-commit from 2.15.0 to 2.16.0 ([`8f6c12f`](https://github.com/supabase/auth-py/commit/8f6c12f4c122700956210cd674e7490342c2e186))

* Merge pull request #4 from leynier/dependabot/pip/main/sphinx-4.3.1

chore(deps-dev): bump sphinx from 4.3.0 to 4.3.1 ([`adb5201`](https://github.com/supabase/auth-py/commit/adb52015157a28b75021b863926042886d5df01c))

* Merge pull request #5 from leynier/dependabot/pip/main/faker-9.9.0

chore(deps-dev): bump faker from 9.8.2 to 9.9.0 ([`6d8c9f0`](https://github.com/supabase/auth-py/commit/6d8c9f0357016e437945666596727f7b1e689540))

* Merge pull request #6 from leynier/dependabot/pip/main/pre-commit-2.16.0

chore(deps-dev): bump pre-commit from 2.15.0 to 2.16.0 ([`6d21ae4`](https://github.com/supabase/auth-py/commit/6d21ae4aa65087ee6ad2cf3870751981cff81b8a))

* bump: version 0.2.0 → 0.3.0 ([`7313b7b`](https://github.com/supabase/auth-py/commit/7313b7b45fd0c5660b0b2306df984bd8221e5490))

* Merge pull request #32 from leynier/feat/add-pre-commit-hook-for-conventional-commit

feat: add pre-commit hook and action for conventional commit and semantic release ([`05f493d`](https://github.com/supabase/auth-py/commit/05f493dc8fa7a92692debf03fafb47954363c832))

* Merge branch &#39;supabase-community:main&#39; into feat/add-pre-commit-hook-for-conventional-commit ([`19f4556`](https://github.com/supabase/auth-py/commit/19f4556f9210b7fcca67445b4d7ddc03af6733d9))

* Merge pull request #28 from leynier/chore/add-badges-to-readme

chore: add badges to README.md ([`9e38a6a`](https://github.com/supabase/auth-py/commit/9e38a6af245b194ee8f77ca0c6e7c03640bca4ee))

* Update README.md ([`2044be7`](https://github.com/supabase/auth-py/commit/2044be7e59004055c82337bd19b6049bdeefe824))

* Merge pull request #29 from leynier/chore/improve-coverage

chore: improve coverage ([`d35d971`](https://github.com/supabase/auth-py/commit/d35d971edda95b9e8dbc89d7f1c1cd1d570383d6))

*  chore: add pragma no cover comments ([`547e245`](https://github.com/supabase/auth-py/commit/547e2455b306e205f8b94d4fc2049cd6510c0e5f))

* Merge pull request #26 from supabase-community/dependabot/pip/main/httpx-0.21.1

chore(deps): bump httpx from 0.20.0 to 0.21.1 ([`4889b38`](https://github.com/supabase/auth-py/commit/4889b3871f5c5af4d5c425d4f3d697313dad0a2f))

* Merge pull request #25 from supabase-community/dependabot/pip/main/flake8-4.0.1

chore(deps-dev): bump flake8 from 3.9.2 to 4.0.1 ([`f129103`](https://github.com/supabase/auth-py/commit/f1291037a97b7e0679efa64c211866a4a224dc72))

* Merge pull request #24 from supabase-community/dependabot/pip/main/black-21.11b1

chore(deps-dev): bump black from 21.10b0 to 21.11b1 ([`4259e38`](https://github.com/supabase/auth-py/commit/4259e3852ec723ba5c84e1d1649cdeef08aa40e2))

* Merge pull request #23 from leynier/feat/dataclasses

Add dataclasses, sync/async, feature-parity with the js-client and tests ([`fb10c5c`](https://github.com/supabase/auth-py/commit/fb10c5ca6bc44dcc70ff9c10eeb8be8e4add853d))

* Switch isort mirror by isort pre-commit hook ([`427d5d4`](https://github.com/supabase/auth-py/commit/427d5d452c6d86b2cd1cee4cc8884286fcbe40bc))

* Fix typo in README.md

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`ec0bdb5`](https://github.com/supabase/auth-py/commit/ec0bdb5b64f13115cf8fb52c73445527504ffccc))

* Use latest actions-poetry ([`ce47032`](https://github.com/supabase/auth-py/commit/ce4703277726ec77ea4d2b190d23e93d095260c6))

* Use pydantic parse_obj_as helper method ([`64162f6`](https://github.com/supabase/auth-py/commit/64162f6b03cc901edef3c4d6d1261ad49a332313))

* Add python 3.10 to GH Actions fix ([`57473a2`](https://github.com/supabase/auth-py/commit/57473a20fa92f36d5f35abcd106b9efd3fe40ebf))

* Formatting ([`0f3210f`](https://github.com/supabase/auth-py/commit/0f3210f9fccbc9ba27a2dc951b20c665fdfd5721))

* Add parse_response method to custom pydantic base model ([`cb4624d`](https://github.com/supabase/auth-py/commit/cb4624d7822575e03a47726a2b6bc8e25cbc3162))

* deps: add pydantic dependency ([`9df4927`](https://github.com/supabase/auth-py/commit/9df49274405a88e201959eda9e54c6288222c51b))

* Merge pull request #19 from leynier/feat/use-poetry

Use poetry for dependency and environment management ([`9ba3192`](https://github.com/supabase/auth-py/commit/9ba3192dbdccd2f02a4819b52dd6cf51095af7e7))

* Merge pull request #16 from leynier/fix/title-of-license

chore: fix title of license ([`f57b99e`](https://github.com/supabase/auth-py/commit/f57b99ea3f0a8528883c9e73a028ee2cc1b3b2fb))

* Merge pull request #14 from bariqhibat/bariqhibat/support-phone-otp

Add support for phone otp ([`f237f15`](https://github.com/supabase/auth-py/commit/f237f1584cf04d1f5cb53524ad2f72e9bd0def47))

* fix comments

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt; ([`202346a`](https://github.com/supabase/auth-py/commit/202346a62940c55883e24b4efd1604e690a9e9a6))

* add new tests for signup by phone and verify otp

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt; ([`7162a47`](https://github.com/supabase/auth-py/commit/7162a472194fc59ae3647bd89722df50cb8ea72a))

* create new api for signup with phone

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt; ([`1870b54`](https://github.com/supabase/auth-py/commit/1870b544435ecc05da61965f4dfbe5dd4732126c))

* create client for otp functions

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt; ([`68f699b`](https://github.com/supabase/auth-py/commit/68f699bf28a86ff892de36fac4af2259f2733862))

* create api for otp functions

Signed-off-by: Bariq &lt;bariqhibat@gmail.com&gt; ([`83031ad`](https://github.com/supabase/auth-py/commit/83031adee23cd74ab6fa9c6d09ce6b286a04e4f0))

* Merge pull request #13 from supabase-community/j0_hacktoberfest

chore: add code of conduct and license ([`0320f45`](https://github.com/supabase/auth-py/commit/0320f451e660ea62daaf2be6d0b030c5ba8d3afa))

* Create CONTRIBUTING.md ([`2dea30f`](https://github.com/supabase/auth-py/commit/2dea30fe0507ad36bdc28b8906ab49802a6629f4))

* Merge pull request #6 from supabase/j0_fix_build

Reinstate lib and fix build ([`ac53ea8`](https://github.com/supabase/auth-py/commit/ac53ea86e0a783e12ea55f09882928db6c97dd53))

* Merge pull request #3 from lawrencecchen/main

add set_auth to gotrue client ([`49c092e`](https://github.com/supabase/auth-py/commit/49c092e3a4a6d7bb5e1c08067a4c42cc2f74b5cc))

* remove lib from gitignore ([`757714b`](https://github.com/supabase/auth-py/commit/757714bdd53d4a0eb8a2d33b1999470f1648d543))

* add set_auth to gotrue client ([`87a6e68`](https://github.com/supabase/auth-py/commit/87a6e68f6e29a8755e031a83d2022106e216d69e))

* Merge pull request #5 from supabase/j0_deps

Update dependencies ([`8189c49`](https://github.com/supabase/auth-py/commit/8189c49c2f2e75db5fc34ac271af375f5a2ecb36))

* Merge pull request #1 from fedden/main

Bring closer to pairity with supabase/gotrue-js ([`38eddcb`](https://github.com/supabase/auth-py/commit/38eddcb51e8a59e068a358971c09425138dd852e))

* remove env vars ([`608c2b1`](https://github.com/supabase/auth-py/commit/608c2b19d675361d54a4a03dfa0ff9116cc0d1ea))

* add return statements in documentation ([`3ad5781`](https://github.com/supabase/auth-py/commit/3ad5781db4dddf79824d3bdf15cfbea0835a8303))

* Update gotrue/client.py

Co-authored-by: Lee Yi Jie Joel &lt;lee.yi.jie.joel@gmail.com&gt; ([`289b184`](https://github.com/supabase/auth-py/commit/289b1846a4e9bd5b88528ca2a0aff71a42d43b1e))

* Update gotrue/api.py

Co-authored-by: Lee Yi Jie Joel &lt;lee.yi.jie.joel@gmail.com&gt; ([`f0e77aa`](https://github.com/supabase/auth-py/commit/f0e77aaa9a1dd6a6862879be1b53cb38ec3a2a6d))

* Update gotrue/api.py

Co-authored-by: Lee Yi Jie Joel &lt;lee.yi.jie.joel@gmail.com&gt; ([`1828117`](https://github.com/supabase/auth-py/commit/1828117d628078ed4e8d96083e5050a2f85394a5))

* correct version ([`68ed44b`](https://github.com/supabase/auth-py/commit/68ed44b0e379b9884becc5fbfd4d6a6a7c8768f4))

* enable simple install that works for non-poetry envs ([`7cdf326`](https://github.com/supabase/auth-py/commit/7cdf3261fedbe0e279fc44d272a614c935e54926))

* updating the pyproject.toml ([`a7be2da`](https://github.com/supabase/auth-py/commit/a7be2da61269bb63382e9a18bc46e0767536fee0))

* add another todo ([`94470db`](https://github.com/supabase/auth-py/commit/94470db34e564fce3cff1e7808ed6757fbb2b199))

* ensuring tests pass ([`337746c`](https://github.com/supabase/auth-py/commit/337746cc82f0b256a823464f262b15bbd4741be1))

* document the tests ([`2b74646`](https://github.com/supabase/auth-py/commit/2b74646a7206d8aad08aa16e0f2f84a956636cdf))

* hopefully ensure the test ci works ([`7dea900`](https://github.com/supabase/auth-py/commit/7dea9002f11286a7945128453d8a93afb32eeb1f))

* link to js-client ([`44fc9da`](https://github.com/supabase/auth-py/commit/44fc9da6d387b61ed2167ff8bf4a748fcce6bcf1))

* add some basic documentation in README ([`3309684`](https://github.com/supabase/auth-py/commit/33096840e7545977a8237ba25b107dc3d6648ef0))

* cleanup tests etc ([`4808a34`](https://github.com/supabase/auth-py/commit/4808a3481b7b790410815a7362423f3ef3e0c446))

* add for working tests ([`c970dfe`](https://github.com/supabase/auth-py/commit/c970dfe99e498d18d434f257c37f469e5133e438))

* updates to get tests passing ([`8b3dc48`](https://github.com/supabase/auth-py/commit/8b3dc488deff62f4acdde54ff63260c83fd65aea))

* wrap up response cleanly into a dict for users ([`29e35ed`](https://github.com/supabase/auth-py/commit/29e35ed9115328c57dd89b7601b2c3e8dd411a4d))

* add gitignoire ([`d620032`](https://github.com/supabase/auth-py/commit/d620032ed3eae549f152e44193ee5ae8b4130813))

* rm crap ([`93f984b`](https://github.com/supabase/auth-py/commit/93f984bdcbb5ee9754a168028ba93b016950fbaa))

* sort typos ([`1a3bef2`](https://github.com/supabase/auth-py/commit/1a3bef2dd75128b008206cfb9596f591902c8718))

* add contstants ([`645136a`](https://github.com/supabase/auth-py/commit/645136a73558070331157928ab90bdca0dae7960))

* bringing closer to pairity with gotrue js ([`e753927`](https://github.com/supabase/auth-py/commit/e7539278fbcbef3a05971856d20a2a1587a9049e))

* Resolve merge conflicts ([`a34bea1`](https://github.com/supabase/auth-py/commit/a34bea153dee52044f6ce5e238c24aa5b3a96a2a))

* Update README.md ([`0201f09`](https://github.com/supabase/auth-py/commit/0201f090c06bd10703bd73c2678bbba795dd0d85))

* Allow headers and lint with black ([`d9c9533`](https://github.com/supabase/auth-py/commit/d9c9533d3f78d1f51fbab83e89846042cc4bf751))

* decrease minimum py version required ([`d768579`](https://github.com/supabase/auth-py/commit/d768579e3e9d7463e3df93c0b6b9360a1beaeb53))

* Update README.md ([`3a36696`](https://github.com/supabase/auth-py/commit/3a36696550805796daf5c9f5d0e2d04247aad01c))

* Remove user and admin ([`5aca335`](https://github.com/supabase/auth-py/commit/5aca335b7c4c6d5f72aa0a3e2b951356fafe9562))

* Add documentation ([`b575640`](https://github.com/supabase/auth-py/commit/b5756408790097425c0d78f9a5871ecf2a2daecd))

* Add usage component to README.md ([`8a8d3eb`](https://github.com/supabase/auth-py/commit/8a8d3ebd6bbdc9ed40b0d022ee744f1335204683))

* Switch .rst file to .md ([`b73f7ef`](https://github.com/supabase/auth-py/commit/b73f7ef2ec04db30ea75824bba1dee1d96fe2110))

* Add jsonify ([`18230a8`](https://github.com/supabase/auth-py/commit/18230a8cd0eb34d5f209f5fada624e939e5ad82b))

* Add grant token method ([`629d12b`](https://github.com/supabase/auth-py/commit/629d12b88c7159387d8325444ce2e01a35252f26))

* Add more methods ([`e77ef0d`](https://github.com/supabase/auth-py/commit/e77ef0d28ee0192643aa5a560bce257ffa6fc1f4))

* Add more methods ([`eff88f3`](https://github.com/supabase/auth-py/commit/eff88f33f192cf94bb78deb4d1bc9dbc271d9fd9))

* Support incremental testing ([`dda60f3`](https://github.com/supabase/auth-py/commit/dda60f327990a586f37802421f2a1fbc7b62fe1a))

* Add tests for settings route ([`3aa54d5`](https://github.com/supabase/auth-py/commit/3aa54d52729e32cd1ecf204eb66e050e3409035f))

* Restructure to support publishing to poetry ([`65d4b1c`](https://github.com/supabase/auth-py/commit/65d4b1cab978a2a221ce5f59aa1f36701127de65))

* Remove flake8 test for now ([`8d7502e`](https://github.com/supabase/auth-py/commit/8d7502e8a5499372b01bb9adf090c0e1374bc3b3))

* Fix indent level again ([`388e339`](https://github.com/supabase/auth-py/commit/388e339721d00df59644e92a78e523734d529f88))

* Fix indent level ([`2f8bd02`](https://github.com/supabase/auth-py/commit/2f8bd02ea011edf2fb9e2d7658944cd5ec18bbaf))

* Add previously removed part of ci test ([`d6c0f87`](https://github.com/supabase/auth-py/commit/d6c0f872c56569b9d693ba0a8f9adabdd6d5b085))

* Add placeholder test ([`b76c1cf`](https://github.com/supabase/auth-py/commit/b76c1cfaebb414f51bfe2fd1a091c73d0b7a1a64))

* fix branch name master-&gt;main ([`1bb5dc9`](https://github.com/supabase/auth-py/commit/1bb5dc9a456233ada58e90bcce24a1a655518a2b))

* Add pytest portion of workflow ([`3aeb728`](https://github.com/supabase/auth-py/commit/3aeb728e0a1a575ed4a8a513941ceffad9879252))

* Remove additional steps ([`2c1f4c3`](https://github.com/supabase/auth-py/commit/2c1f4c3d53926cf3645bd790375aeefca2c3a90e))

* Fix indentation level ([`949a33d`](https://github.com/supabase/auth-py/commit/949a33dc90e8b2fa7bcdbacb6d5319e8982ac6a9))

* Add .github dir ([`a958afe`](https://github.com/supabase/auth-py/commit/a958afef51270221ddff33aa2d716ad0aaa6c19d))

* add preliminary CI ([`5cfcae7`](https://github.com/supabase/auth-py/commit/5cfcae7814999481bc194c610472633357ade876))

* Test initial stubs against gotrue-example site ([`583da03`](https://github.com/supabase/auth-py/commit/583da03cfd76fe2061f4748f95775d771f6d1eb5))

* Update README ([`0e4fbd0`](https://github.com/supabase/auth-py/commit/0e4fbd0e1b2ef54ec3dab745dc18ae690bc04705))

* Restructure repository ([`4d4e554`](https://github.com/supabase/auth-py/commit/4d4e55474fdd131e8711c2d62cbaade0b5a14fb7))

* Initial commit ([`3d87285`](https://github.com/supabase/auth-py/commit/3d87285a1d503cdb88a91cfa3e430fac546d2564))

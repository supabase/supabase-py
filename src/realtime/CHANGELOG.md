# CHANGELOG

## [2.20.0](https://github.com/supabase/supabase-py/compare/v2.19.0...v2.20.0) (2025-09-22)


### Features

* include postgrest in monorepo, finalize monorepo switch ([#1213](https://github.com/supabase/supabase-py/issues/1213)) ([2533ba1](https://github.com/supabase/supabase-py/commit/2533ba1f3b3f97f561ea7240c2c5ef8f9ee29ee0))

## [2.19.0](https://github.com/supabase/supabase-py/compare/v2.18.1...v2.19.0) (2025-09-16)

### Features

* move realtime from original repository to supabase-py monorepo ([#1190](https://github.com/supabase/supabase-py/pull/1190)). 
* NOTE: the version was bumped to 2.19.0 to have all the package versions in the monorepo be the same, simplifying version constraints. No changes were introduced in the package itself.

## [2.7.0](https://github.com/supabase/realtime-py/compare/v2.6.0...v2.7.0) (2025-07-28)


### Features

* validate server message ([#345](https://github.com/supabase/realtime-py/issues/345)) ([8c6066e](https://github.com/supabase/realtime-py/commit/8c6066e6d7125a0762ca9311df97eb209442fcf4))

## [2.6.0](https://github.com/supabase/realtime-py/compare/v2.5.3...v2.6.0) (2025-07-10)


### Features

* improve typing definitions, introduce mypy in CI ([#338](https://github.com/supabase/realtime-py/issues/338)) ([513ae3a](https://github.com/supabase/realtime-py/commit/513ae3aac8d0077c2a357ef4383209749c2d9312))


### Bug Fixes

* Do not supress callback exceptions ([#332](https://github.com/supabase/realtime-py/issues/332)) ([f978d39](https://github.com/supabase/realtime-py/commit/f978d39181d6b5a94f2aad311b7ea8220ea8673f))

## [2.5.3](https://github.com/supabase/realtime-py/compare/v2.5.2...v2.5.3) (2025-06-26)


### Bug Fixes

* postgres_changes triggering multiple times ([#325](https://github.com/supabase/realtime-py/issues/325)) ([eb130ab](https://github.com/supabase/realtime-py/commit/eb130ab4361ab5cfd76500243a0bf034e67b5371))

## [2.5.2](https://github.com/supabase/realtime-py/compare/v2.5.1...v2.5.2) (2025-06-24)


### Bug Fixes

* remove jwt validation to allow new api keys ([#322](https://github.com/supabase/realtime-py/issues/322)) ([78705e2](https://github.com/supabase/realtime-py/commit/78705e28c6841cddf78424385c88f18298e9bdec))

## [2.5.1](https://github.com/supabase/realtime-py/compare/v2.5.0...v2.5.1) (2025-06-19)


### Bug Fixes

* **deps:** bump aiohttp from 3.11.18 to 3.12.13 ([#318](https://github.com/supabase/realtime-py/issues/318)) ([0db041f](https://github.com/supabase/realtime-py/commit/0db041f7b043b05552f14a1dcd47638364628909))
* **deps:** bump typing-extensions from 4.13.2 to 4.14.0 ([#316](https://github.com/supabase/realtime-py/issues/316)) ([fe5d0c2](https://github.com/supabase/realtime-py/commit/fe5d0c2f5f7e67b7da2ce2e78cc5b7884ff49f76))

## [2.5.0](https://github.com/supabase/realtime-py/compare/v2.4.3...v2.5.0) (2025-05-15)


### Features

* **websockets:** bump websockets from 14.2 to 15.0.1 ([#285](https://github.com/supabase/realtime-py/issues/285)) ([925bbf1](https://github.com/supabase/realtime-py/commit/925bbf1a36c0bc8a21cfcc4e2e4f658ac9cf4f12))

## [2.4.3](https://github.com/supabase/realtime-py/compare/v2.4.2...v2.4.3) (2025-04-28)


### Bug Fixes

* reconnect when send message fails ([#295](https://github.com/supabase/realtime-py/issues/295)) ([8941d17](https://github.com/supabase/realtime-py/commit/8941d171ce15756acc47a5b8eabc58c19d918e4c))

## [2.4.2](https://github.com/supabase/realtime-py/compare/v2.4.1...v2.4.2) (2025-03-25)


### Bug Fixes

* cleanup current heartbeat and listen tasks before creating a new one ([#290](https://github.com/supabase/realtime-py/issues/290)) ([70778e5](https://github.com/supabase/realtime-py/commit/70778e5a3df77859eec65d0bc1f6a14526764b56))

## [2.4.1](https://github.com/supabase/realtime-py/compare/v2.4.0...v2.4.1) (2025-02-26)


### Bug Fixes

* revert client to handle bc changes ([#281](https://github.com/supabase/realtime-py/issues/281)) ([54fb4a1](https://github.com/supabase/realtime-py/commit/54fb4a19503a10282aa086dd49738e00d36c4d60))

## [2.4.0](https://github.com/supabase/realtime-py/compare/v2.3.0...v2.4.0) (2025-02-19)


### Features

* remove the need of calling listen method ([#274](https://github.com/supabase/realtime-py/issues/274)) ([0a96f70](https://github.com/supabase/realtime-py/commit/0a96f709db5f2c6dc04b246bc637368b0df11674))


### Bug Fixes

* Set default heartbeat interval to 25s ([#276](https://github.com/supabase/realtime-py/issues/276)) ([09c6269](https://github.com/supabase/realtime-py/commit/09c6269f7bab8654865a942244951cedccd78bbb))

## [2.3.0](https://github.com/supabase/realtime-py/compare/v2.2.0...v2.3.0) (2025-01-29)


### Features

* **deps:** bump websockets from 13.1 to 14.2 ([#261](https://github.com/supabase/realtime-py/issues/261)) ([7e9429f](https://github.com/supabase/realtime-py/commit/7e9429f26c0c8bf19a930f7382e6835838f71f8f))

## [2.2.0](https://github.com/supabase/realtime-py/compare/v2.1.0...v2.2.0) (2025-01-22)


### Features

* add support for  `system` event ([#264](https://github.com/supabase/realtime-py/issues/264)) ([0396c7b](https://github.com/supabase/realtime-py/commit/0396c7b759842ce8f029e606ab59b6eb91bc4145))


### Bug Fixes

* send correct payload to channel on reconnect ([#262](https://github.com/supabase/realtime-py/issues/262)) ([66db32e](https://github.com/supabase/realtime-py/commit/66db32e571df505561b97e1ddcedfaca516c648c))

## [2.1.0](https://github.com/supabase/realtime-py/compare/v2.0.6...v2.1.0) (2024-12-30)


### Features

* Check if url is a WS URL ([#227](https://github.com/supabase/realtime-py/issues/227)) ([f82597e](https://github.com/supabase/realtime-py/commit/f82597e4be1e567df4f28ffc81186a82ad3218ea))


### Bug Fixes

* default mutable arguments ([#216](https://github.com/supabase/realtime-py/issues/216)) ([093f84d](https://github.com/supabase/realtime-py/commit/093f84d5f230667337b2ef22c1e8474ea7ab19b8))
* Fix heartbeat ([#248](https://github.com/supabase/realtime-py/issues/248)) ([9477bd0](https://github.com/supabase/realtime-py/commit/9477bd0c736661e1628a37973a5a04eb6062917a))
* prevent sending expired tokens ([#244](https://github.com/supabase/realtime-py/issues/244)) ([74ad7da](https://github.com/supabase/realtime-py/commit/74ad7da0e7036262ed6d445af9202cb37ea30ccd))

## [2.0.6](https://github.com/supabase/realtime-py/compare/v2.0.5...v2.0.6) (2024-10-16)


### Bug Fixes

* correctly setup logging ([#215](https://github.com/supabase/realtime-py/issues/215)) ([f9eb04c](https://github.com/supabase/realtime-py/commit/f9eb04c5c5d63fcdc98ced26411c81a5a41e763a))
* **deps:** bump aiohttp from 3.10.6 to 3.10.9 ([#220](https://github.com/supabase/realtime-py/issues/220)) ([1802e30](https://github.com/supabase/realtime-py/commit/1802e304ffe8e79f821a8bf44ee8286d81aea390))
* Types to use Option[T] ([#223](https://github.com/supabase/realtime-py/issues/223)) ([b5041c3](https://github.com/supabase/realtime-py/commit/b5041c32d880e840ffc550601b2097bdf0820f4a))

## [2.0.5](https://github.com/supabase/realtime-py/compare/v2.0.4...v2.0.5) (2024-09-28)


### Bug Fixes

* schedule timeout should not be async ([#210](https://github.com/supabase/realtime-py/issues/210)) ([0a3c720](https://github.com/supabase/realtime-py/commit/0a3c7207852010c25f083f1e2ae7b684466a626e))

## [2.0.4](https://github.com/supabase/realtime-py/compare/v2.0.3...v2.0.4) (2024-09-26)


### Bug Fixes

* add missing arg on on_join_push_timeout ([#208](https://github.com/supabase/realtime-py/issues/208)) ([de77c12](https://github.com/supabase/realtime-py/commit/de77c12f196bfdaac34b7ac58354e3e09525b721))

## [2.0.3](https://github.com/supabase/realtime-py/compare/v2.0.2...v2.0.3) (2024-09-26)


### Bug Fixes

* **deps:** bump aiohttp from 3.10.5 to 3.10.6 ([#207](https://github.com/supabase/realtime-py/issues/207)) ([e743b85](https://github.com/supabase/realtime-py/commit/e743b854ec45cc7c987d4ce9324a53f59eaa6d8a))
* **deps:** bump websockets from 12.0 to 13.1 ([#205](https://github.com/supabase/realtime-py/issues/205)) ([2ce6efb](https://github.com/supabase/realtime-py/commit/2ce6efb12e158c6df2bd4cda5d3b2a958d580c56))
* update broken method calls ([#203](https://github.com/supabase/realtime-py/issues/203)) ([b162e00](https://github.com/supabase/realtime-py/commit/b162e0076df4e7b20f1f669e7e79012e6274df7e))

## [2.0.2](https://github.com/supabase/realtime-py/compare/v2.0.1...v2.0.2) (2024-08-20)


### Bug Fixes

* set realtime as not implemented in the sync client ([#193](https://github.com/supabase/realtime-py/issues/193)) ([73d6275](https://github.com/supabase/realtime-py/commit/73d6275802f53a98fedfd20e11ce7657445dd83a))

## [2.0.1](https://github.com/supabase/realtime-py/compare/v2.0.0...v2.0.1) (2024-08-17)


### Bug Fixes

* remove ensure connect on set_auth ([#189](https://github.com/supabase/realtime-py/issues/189)) ([31c01ed](https://github.com/supabase/realtime-py/commit/31c01eda8bed92f7ce4089877dd9ab4bf1c28fcf))

## [2.0.0](https://github.com/supabase/realtime-py/compare/v1.0.6...v2.0.0) (2024-08-16)


### ⚠ BREAKING CHANGES

* realtime v2 ([#178](https://github.com/supabase/realtime-py/issues/178))

### Features

* add set_auth method ([#175](https://github.com/supabase/realtime-py/issues/175)) ([5859c72](https://github.com/supabase/realtime-py/commit/5859c729590ffd1673cc626d8276b5366ff11ede))


### Bug Fixes

* realtime v2 ([#178](https://github.com/supabase/realtime-py/issues/178)) ([981a5d0](https://github.com/supabase/realtime-py/commit/981a5d0d3c10a60430810a6a0505bf751d931e61))

## v1.0.6 (2024-06-15)

### Build

* build(deps-dev): bump black from 24.3.0 to 24.4.2 (#127) ([`cedc610`](https://github.com/supabase-community/realtime-py/commit/cedc610462a4840d6fcb0636aa5a023794f2dde4))

### Chore

* chore(deps): bump typing-extensions from 4.12.0 to 4.12.2 (#159) ([`bc8ed99`](https://github.com/supabase-community/realtime-py/commit/bc8ed990731b49012fda05f5edca877d2abe8a6d))

* chore(deps): bump python-semantic-release/python-semantic-release (#157) ([`6fd84c1`](https://github.com/supabase-community/realtime-py/commit/6fd84c135cb0931936e3ae1e54353c1a4c55fa2a))

* chore(deps-dev): bump python-semantic-release from 9.8.0 to 9.8.1 (#156) ([`90aa6d9`](https://github.com/supabase-community/realtime-py/commit/90aa6d92a9208d96ed67ef1da9e9b30cd1f72811))

* chore(deps-dev): bump pytest from 8.2.1 to 8.2.2 (#155) ([`77ab4fc`](https://github.com/supabase-community/realtime-py/commit/77ab4fc93b9334213e11e977e0da513ec0f68b6a))

* chore(deps-dev): bump requests in the pip group across 1 directory (#153)

Bumps the pip group with 1 update in the / directory: [requests](https://github.com/psf/requests).

Updates `requests` from 2.31.0 to 2.32.2
- [Release notes](https://github.com/psf/requests/releases)
- [Changelog](https://github.com/psf/requests/blob/main/HISTORY.md)
- [Commits](https://github.com/psf/requests/compare/v2.31.0...v2.32.2) ([`72fec0e`](https://github.com/supabase-community/realtime-py/commit/72fec0e9503331f44d33be0ffbbe6eaaac8c9f88))

* chore(deps-dev): bump python-semantic-release from 9.4.1 to 9.8.0 (#152) ([`acd62f5`](https://github.com/supabase-community/realtime-py/commit/acd62f58900f948d83edbc4b0bd6836307fbeb8f))

* chore(deps): bump typing-extensions from 4.11.0 to 4.12.0 (#150) ([`36f7d31`](https://github.com/supabase-community/realtime-py/commit/36f7d31230e1f9847685a6d12fbb623d4ed50bf8))

* chore(deps): bump python-semantic-release/python-semantic-release (#151) ([`f6040fd`](https://github.com/supabase-community/realtime-py/commit/f6040fde199e6feaffad3573d60d7a426e7b930c))

* chore(deps-dev): bump pytest from 8.1.1 to 8.2.1 (#147) ([`86d889f`](https://github.com/supabase-community/realtime-py/commit/86d889f30678a87e29fc7c6672650375ccb2a29e))

### Fix

* fix: Fixes for ciclomatic complexity (#148) ([`883d051`](https://github.com/supabase-community/realtime-py/commit/883d0511b543a49b424ce4bb466aeb7fcd7cb4aa))


## v1.0.5 (2024-05-29)

### Chore

* chore(release): bump version to v1.0.5 ([`9b8d0c0`](https://github.com/supabase-community/realtime-py/commit/9b8d0c0be12201350db852ae60f3e3bd043c126f))

### Fix

* fix: gracefully close the socket ([`9c0ffd1`](https://github.com/supabase-community/realtime-py/commit/9c0ffd13bd94aeb3d36dc7f93897d9673a522dfd))

### Unknown

* Update .pre-commit-config.yaml (#132)

* Update .pre-commit-config.yaml

* Update .pre-commit-config.yaml

* Update .pre-commit-config.yaml

* Update .pre-commit-config.yaml

* Update .pre-commit-config.yaml

* Update .pre-commit-config.yaml

* Update .pre-commit-config.yaml

* Update .pre-commit-config.yaml ([`8bcf6da`](https://github.com/supabase-community/realtime-py/commit/8bcf6da63e161d7127292a079887952d2c8a2722))

* Add stale bot (#131) ([`5d1906a`](https://github.com/supabase-community/realtime-py/commit/5d1906aa564f8c50567d3ea61a7b35a2b3ef9274))


## v1.0.4 (2024-04-13)

### Build

* build(deps-dev): bump idna from 3.4 to 3.7 (#118) ([`364de4e`](https://github.com/supabase-community/realtime-py/commit/364de4eeb154344e197ab9bcbf59e7191d92c23a))

* build(deps-dev): bump python-semantic-release from 9.3.1 to 9.4.1 (#115) ([`88e8a30`](https://github.com/supabase-community/realtime-py/commit/88e8a3010fb87f2360a39bf346f0e1525f0a56c1))

* build(deps): bump typing-extensions from 4.10.0 to 4.11.0 (#114) ([`910616a`](https://github.com/supabase-community/realtime-py/commit/910616a0fd0a0a79f783480a30ad1661658333d5))

* build(deps): bump python-semantic-release/python-semantic-release (#116)

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 9.3.1 to 9.4.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.3.1...v9.4.1)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`6e07a0c`](https://github.com/supabase-community/realtime-py/commit/6e07a0cf0d3025693bf702346807e753bc68f9b0))

### Chore

* chore(release): bump version to v1.0.4 ([`a7dc820`](https://github.com/supabase-community/realtime-py/commit/a7dc8200cc4c14cbd32763810aa4a6f2ebcc7230))

### Fix

* fix: version bump (#119) ([`228d466`](https://github.com/supabase-community/realtime-py/commit/228d466a1467e916a9670bdf7801f95fcba2c872))

### Unknown

* Update connection.py (#117) ([`c5915e5`](https://github.com/supabase-community/realtime-py/commit/c5915e511517d097b7c716be89d55f37ff64a5e4))


## v1.0.3 (2024-03-26)

### Build

* build(deps-dev): bump python-semantic-release from 9.1.1 to 9.3.1 (#109) ([`acc5af2`](https://github.com/supabase-community/realtime-py/commit/acc5af2e662ae71fabfd6c79e01836c32773d129))

* build(deps): bump python-semantic-release/python-semantic-release (#107) ([`fc381db`](https://github.com/supabase-community/realtime-py/commit/fc381db0e9607efd1663c145a1ee1275f6559143))

* build(deps-dev): bump black from 23.11.0 to 24.3.0 (#105) ([`7c2bc90`](https://github.com/supabase-community/realtime-py/commit/7c2bc9072ce4757b8e004c4688e7f710a77c9048))

* build(deps-dev): bump black from 23.11.0 to 24.3.0 (#103) ([`aa068c0`](https://github.com/supabase-community/realtime-py/commit/aa068c00cc182e6111f940f79c8ed8bb0b4be124))

* build(deps-dev): bump pytest from 8.0.2 to 8.1.1 (#101) ([`f3ac93a`](https://github.com/supabase-community/realtime-py/commit/f3ac93a60be24ed98416b8a903c96582e2f4d381))

* build(deps): bump python-dateutil from 2.8.2 to 2.9.0.post0 (#100) ([`36875c7`](https://github.com/supabase-community/realtime-py/commit/36875c766423e6d9e2220815c9f329a617405807))

* build(deps): bump websockets from 11.0.3 to 12.0 (#97) ([`859a7e7`](https://github.com/supabase-community/realtime-py/commit/859a7e72241cd174b15e7ee90260ebc062ac0c75))

* build(deps-dev): bump isort from 5.12.0 to 5.13.2 (#94) ([`1938958`](https://github.com/supabase-community/realtime-py/commit/19389585f602db864b4604c0cac0fc4ba2eecdbe))

* build(deps): bump typing-extensions from 4.7.1 to 4.10.0 (#96)

Bumps [typing-extensions](https://github.com/python/typing_extensions) from 4.7.1 to 4.10.0.
- [Release notes](https://github.com/python/typing_extensions/releases)
- [Changelog](https://github.com/python/typing_extensions/blob/main/CHANGELOG.md)
- [Commits](https://github.com/python/typing_extensions/compare/4.7.1...4.10.0)

---
updated-dependencies:
- dependency-name: typing-extensions
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9b610d7`](https://github.com/supabase-community/realtime-py/commit/9b610d781d5987c4293366f96ec286e0b39e46f8))

* build(deps-dev): bump python-semantic-release from 8.3.0 to 9.1.1 (#95)

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`99a0c48`](https://github.com/supabase-community/realtime-py/commit/99a0c48498e1a16bfbd026fb13bff8e4ce2098a3))

* build(deps): bump actions/setup-python from 2 to 5 (#89)

Bumps [actions/setup-python](https://github.com/actions/setup-python) from 2 to 5.
- [Release notes](https://github.com/actions/setup-python/releases)
- [Commits](https://github.com/actions/setup-python/compare/v2...v5)

---
updated-dependencies:
- dependency-name: actions/setup-python
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`d7f13aa`](https://github.com/supabase-community/realtime-py/commit/d7f13aa7e28caa73de7e4bd49d3ac54ae2d760aa))

* build(deps-dev): bump pytest from 7.4.0 to 8.0.2 (#93)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.4.0 to 8.0.2.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.4.0...8.0.2)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`64f7e8e`](https://github.com/supabase-community/realtime-py/commit/64f7e8ef3b4eb8c709f206fba5c74c9f028ac082))

* build(deps): bump abatilo/actions-poetry from 2.2.0 to 3.0.0 (#91)

Bumps [abatilo/actions-poetry](https://github.com/abatilo/actions-poetry) from 2.2.0 to 3.0.0.
- [Release notes](https://github.com/abatilo/actions-poetry/releases)
- [Changelog](https://github.com/abatilo/actions-poetry/blob/master/.releaserc)
- [Commits](https://github.com/abatilo/actions-poetry/compare/v2.2.0...v3.0.0)

---
updated-dependencies:
- dependency-name: abatilo/actions-poetry
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3fb37a5`](https://github.com/supabase-community/realtime-py/commit/3fb37a575d6ce338a55aac1a8ca44dee08b5e77d))

* build(deps): bump python-semantic-release/python-semantic-release (#92)

Bumps [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 8.0.0 to 9.1.1.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v8.0.0...v9.1.1)

---
updated-dependencies:
- dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`2f6776e`](https://github.com/supabase-community/realtime-py/commit/2f6776ead4cd8db54626180e5d1e01d667ce33db))

* build(deps): bump actions/checkout from 2 to 4 (#90)

Bumps [actions/checkout](https://github.com/actions/checkout) from 2 to 4.
- [Release notes](https://github.com/actions/checkout/releases)
- [Changelog](https://github.com/actions/checkout/blob/main/CHANGELOG.md)
- [Commits](https://github.com/actions/checkout/compare/v2...v4)

---
updated-dependencies:
- dependency-name: actions/checkout
  dependency-type: direct:production
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`f6001b5`](https://github.com/supabase-community/realtime-py/commit/f6001b578e2bc88468d8a13603d0b15d53043237))

* build(deps-dev): bump jinja2 from 3.1.2 to 3.1.3 (#84)

Bumps [jinja2](https://github.com/pallets/jinja) from 3.1.2 to 3.1.3.
- [Release notes](https://github.com/pallets/jinja/releases)
- [Changelog](https://github.com/pallets/jinja/blob/main/CHANGES.rst)
- [Commits](https://github.com/pallets/jinja/compare/3.1.2...3.1.3)

---
updated-dependencies:
- dependency-name: jinja2
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`30699c9`](https://github.com/supabase-community/realtime-py/commit/30699c9bc0a150f7ffcc095e3d4e9c4989871964))

* build(deps-dev): bump gitpython from 3.1.40 to 3.1.41 (#83)

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.40 to 3.1.41.
- [Release notes](https://github.com/gitpython-developers/GitPython/releases)
- [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES)
- [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.40...3.1.41)

---
updated-dependencies:
- dependency-name: gitpython
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`1bfd2c1`](https://github.com/supabase-community/realtime-py/commit/1bfd2c112604217f818266f29788e4055dbfc96d))

### Chore

* chore(release): bump version to v1.0.3 ([`1079275`](https://github.com/supabase-community/realtime-py/commit/1079275f158b5ddc3e5adef20075f97298e1cbc3))

### Fix

* fix: package release (#110) ([`fde31f3`](https://github.com/supabase-community/realtime-py/commit/fde31f3efda3836486e1fdad53bf1278e61c1543))

### Unknown

* Create dependabot.yml &amp; update code-owners (#88)

* Create dependabot.yml

* Create dependabot.yml

* Delete .github/.github directory

* Create CODEOWNERS ([`5fdb923`](https://github.com/supabase-community/realtime-py/commit/5fdb923b26e418d21299e8cbd8e9b4558457bf33))


## v1.0.2 (2023-12-02)

### Chore

* chore(release): bump version to v1.0.2 ([`8897feb`](https://github.com/supabase-community/realtime-py/commit/8897feb605ec643de89cf0e1d9944860b23b6038))

### Fix

* fix: update README.md (#77) ([`c5d9afb`](https://github.com/supabase-community/realtime-py/commit/c5d9afb610651b2981361ff01a8a593399809c7f))


## v1.0.1 (2023-12-02)

### Chore

* chore(release): bump version to v1.0.1 ([`7f185e9`](https://github.com/supabase-community/realtime-py/commit/7f185e993735afbefde823577586f4c24fe88eee))

* chore: update CI to use correct branch (#76) ([`07b1b8b`](https://github.com/supabase-community/realtime-py/commit/07b1b8b3c5d586cca576b728deba0930dc1f681e))

* chore: update github workflow with correct branch (#74) ([`13688c4`](https://github.com/supabase-community/realtime-py/commit/13688c4e86ba5da938b52a04c74bf10cc8250cf3))

* chore: Remove unused import of &#39;cast&#39; ([`593815f`](https://github.com/supabase-community/realtime-py/commit/593815ffa84661b74fa83627fe1dfb39c4731e50))

### Fix

* fix: use shared types (#75) ([`233392a`](https://github.com/supabase-community/realtime-py/commit/233392a7626ddd9e750e0f0bf0e45d72626740a7))

* fix: add github action workflow (#73) ([`f29d8b3`](https://github.com/supabase-community/realtime-py/commit/f29d8b3d4eff08e146bcf4049e26eac806475374))

* fix: replace cast method with consistent type hinting and direct assignment of value ([`1d822b5`](https://github.com/supabase-community/realtime-py/commit/1d822b5704c2b2b63caee8ac1d95a5eb4639af66))

* fix: correct type argument for cast method during socket initialisation ([`283af0a`](https://github.com/supabase-community/realtime-py/commit/283af0a5e9285e10aa7a6c5f6fb5f2189b3d0603))

### Unknown

* Merge pull request #70 from markyao6275/update-websockets-pytest

Update websockets + pytest versions ([`bf9ae1c`](https://github.com/supabase-community/realtime-py/commit/bf9ae1c073e3a3544bd536c308d99792661f196f))

* Update websockets + pytest versions ([`9af9807`](https://github.com/supabase-community/realtime-py/commit/9af980788a6a8494b4ef10c3a6ce8516382c6e01))

* Merge pull request #65 from odiseo0/master

Remove additional `Any` ([`0934023`](https://github.com/supabase-community/realtime-py/commit/0934023fe002357a2558f3b48d1c5000c4b00382))

* Remove additional `Any` ([`803203b`](https://github.com/supabase-community/realtime-py/commit/803203b06045d47b03abec2b3d54a74d3d74b695))

* Revert &#34;Update dependencies&#34;

This reverts commit 4cdcde406eb38b73f84349a39c079ff2eaf375b7.
I meant to push this to another branch and then open a PR, sorry! ([`6b2a320`](https://github.com/supabase-community/realtime-py/commit/6b2a3200427e78b5382b11aecb1d020c36a893c5))

* Update dependencies ([`4cdcde4`](https://github.com/supabase-community/realtime-py/commit/4cdcde406eb38b73f84349a39c079ff2eaf375b7))

* Merge pull request #60 from dhaneshsabane/bug-58-type-correction

fix: correct type argument for cast method during socket initialisation ([`e40a359`](https://github.com/supabase-community/realtime-py/commit/e40a359e68837360392dd87868fafbb9d582aecb))

* Update README.md ([`5f4afad`](https://github.com/supabase-community/realtime-py/commit/5f4afad859f444d1d5b6d19d4947dd2df940410a))


## v1.0.0 (2023-02-05)

### Build

* build: update websockets version ([`5a243e1`](https://github.com/supabase-community/realtime-py/commit/5a243e1b4886365eab87b70c8915f18eabdc0a5b))

### Chore

* chore: build 0.0.5 ([`1b653b7`](https://github.com/supabase-community/realtime-py/commit/1b653b7633ad226edadf8e946d23a38bfc5b9a91))

### Feature

* feat: add new release, drop support for 3.7 ([`28225cd`](https://github.com/supabase-community/realtime-py/commit/28225cdcfcac1b5f27ca33e9a66e35e3945a6439))

### Fix

* fix: update version ([`0e8699a`](https://github.com/supabase-community/realtime-py/commit/0e8699a7bb12c583a7802dd39a863e75ee324714))

* fix: update package name in test ([`689de0b`](https://github.com/supabase-community/realtime-py/commit/689de0b35625c8e661b6784c73440a8b080b3612))

* fix: wildcard event is not handled correctly ([`88e4e58`](https://github.com/supabase-community/realtime-py/commit/88e4e58655206cb175936716888de4f367d5f209))

### Unknown

* Merge pull request #57 from supabase-community/j0/new_release

feat: add new release, drop support for 3.7, add 3.11 to CI ([`3b4f40f`](https://github.com/supabase-community/realtime-py/commit/3b4f40fbeeb624ca4db6bc9684370fdf3615b446))

* Merge pull request #46 from bramvdbruggen/socket-auto-reconnect

Reconnect to websocket ([`02ca2cf`](https://github.com/supabase-community/realtime-py/commit/02ca2cf1b332b805c41a6ea0cc44fd4f0336c247))

* Merge pull request #34 from supabase-community/sourcery/pull-33

fix: wildcard event is not handled correctly (Sourcery refactored) ([`e256ccd`](https://github.com/supabase-community/realtime-py/commit/e256ccdcd1d2cae4e387af1078d0415f799194d9))

* Merge pull request #48 from kavalerov/remove-dataclasses

Remove `dataclasses` dependency ([`c5e1599`](https://github.com/supabase-community/realtime-py/commit/c5e1599a160fb3b2cae6e4399fe42f3768cfb9da))

* Remove dataclasses dependency ([`cdb7570`](https://github.com/supabase-community/realtime-py/commit/cdb7570c721a5c894f217d1deb557a04e435c1c0))

* Reconnect to websocket

Added the ability to specify if you want the socket to automatic try reconnecting and rejoining the channels. ([`2d81e72`](https://github.com/supabase-community/realtime-py/commit/2d81e729969cf51671364b670735dfcf87102fd7))

* Merge pull request #44 from supabase-community/j0_add_0.0.5

chore: release version 0.0.5 ([`4c808b0`](https://github.com/supabase-community/realtime-py/commit/4c808b000bfa3384678ad4aaa5e78f99d5ad89be))

* Merge pull request #45 from supabase-community/sourcery/j0_add_0.0.5

chore: release version 0.0.5 (Sourcery refactored) ([`86e2048`](https://github.com/supabase-community/realtime-py/commit/86e20480dcc9357941f738591c3a00e8c79ca2bc))

* &#39;Refactored by Sourcery&#39; ([`e12c165`](https://github.com/supabase-community/realtime-py/commit/e12c1657cb93e3a4f335386d031defd8421dc561))

* Merge pull request #18 from RizkyRajitha/add-ghaction

Add github action with trivial test cases with pytest ([`b787354`](https://github.com/supabase-community/realtime-py/commit/b787354225c3ac2f0df20fa17065b18d87b07ea6))

* Merge branch &#39;master&#39; into add-ghaction ([`966f986`](https://github.com/supabase-community/realtime-py/commit/966f98605842099364c8e14ee1e1fae3067167b4))

* Merge pull request #42 from nielsrolf/master

fix spelling mistake: set_chanel-&gt;set_channel ([`d475aea`](https://github.com/supabase-community/realtime-py/commit/d475aea4a3929698e8a891e7b1cd7f678564dd8e))

* fix spelling mistake: set_chanel-&gt;set_channel ([`25dc1bc`](https://github.com/supabase-community/realtime-py/commit/25dc1bc8571368549f9ac47e96c2472439599ae0))

* Merge pull request #37 from odiseo0/master

♻️ Standardize types and improve consistency ([`e30529e`](https://github.com/supabase-community/realtime-py/commit/e30529efb56250d34aca69d8739f73fa8a60879e))

* ♻️ Use `typing-extensions` directly ([`189f8b9`](https://github.com/supabase-community/realtime-py/commit/189f8b9b6c9b97fb843e2246f2aed6565e80b315))

* ♻️ Declare types in file instead of importing from `types.py` ([`d81682a`](https://github.com/supabase-community/realtime-py/commit/d81682a8d2c95c2881ec433731eefa6d748359c8))

* ➕ Add `typing-extensions` ([`0fe4287`](https://github.com/supabase-community/realtime-py/commit/0fe42875a4e753e19592a10b16a48a3c838b4e17))

* ♻️ Standardize types and improve consistency ([`dd71d42`](https://github.com/supabase-community/realtime-py/commit/dd71d42467432d1094e0149dc9e49526483d74cc))

* Merge pull request #36 from Matthew-Burkard/master

build: update websockets version ([`e0ef5b1`](https://github.com/supabase-community/realtime-py/commit/e0ef5b1149db6a6960082c8d298149421fdc8705))

* &#39;Refactored by Sourcery&#39; ([`f270cb1`](https://github.com/supabase-community/realtime-py/commit/f270cb1119134f9037390377e47ccb7d60dd5b05))


## v0.0.4 (2022-01-01)

### Chore

* chore: update dependencies ([`b917727`](https://github.com/supabase-community/realtime-py/commit/b917727ab3a9bdc41cb2b5e43e0c9410a447a67a))

* chore: update version ([`5453baa`](https://github.com/supabase-community/realtime-py/commit/5453baa939173bcf1a5ad0726a9b5ccd9369c18d))

* chore: rename realtime_py to realtime ([`5334bd9`](https://github.com/supabase-community/realtime-py/commit/5334bd9d50ffe54fce865746d7bb2d41901d4b73))

* chore: update versions ([`a810aa3`](https://github.com/supabase-community/realtime-py/commit/a810aa37ab040f1f63cf88c8ea206ba4a3b1818d))

* chore: use annotations future import ([`68ee73b`](https://github.com/supabase-community/realtime-py/commit/68ee73b8aa6cc8f1f24a065274483d76d5517212))

* chore: fix return annotations ([`03667af`](https://github.com/supabase-community/realtime-py/commit/03667af4b690588fc9aa21418c11b5daf3915622))

* chore: remove unused imports, bugfix ([`592a563`](https://github.com/supabase-community/realtime-py/commit/592a5638eb93ff5c00665c8a4a1d5b2798d739fa))

* chore: update websockets to 9.1 ([`86f05d3`](https://github.com/supabase-community/realtime-py/commit/86f05d3957f2a9e96e48005d3812db2d98a748b7))

* chore: add .md files for hacktoberfest ([`c7e31a1`](https://github.com/supabase-community/realtime-py/commit/c7e31a1ca3080df603849abf5f282180639425ea))

* chore: add transformers as an import in __init__ ([`eb04ae9`](https://github.com/supabase-community/realtime-py/commit/eb04ae9883e2a99f04019c8b368218098cd7503b))

* chore: update README

Add details to help a user  connect to the Supabase realtime endpoint using the library. ([`460e0c9`](https://github.com/supabase-community/realtime-py/commit/460e0c97f5f54b0875b9e71b294b2d3c643ca870))

* chore: refactor code ([`d1b8621`](https://github.com/supabase-community/realtime-py/commit/d1b8621cd39f506623ec829255f7040403c014f1))

### Feature

* feat: added logging ([`c614de3`](https://github.com/supabase-community/realtime-py/commit/c614de3840d49fc83b49d777efe70cd156ee1d0e))

### Fix

* fix: incorrect typehints ([`e999d48`](https://github.com/supabase-community/realtime-py/commit/e999d48cb22d16ad07d625d563e8981b579e1ce9))

### Refactor

* refactor: Extract transfomer to separate PR ([`e5f3457`](https://github.com/supabase-community/realtime-py/commit/e5f3457620c76ab67532e396ffdaa5cfc50be32b))

### Unknown

* Merge pull request #24 from supabase-community/sourcery/pull-23

Bug fixes and parsing timestamptz (Sourcery refactored) ([`6945872`](https://github.com/supabase-community/realtime-py/commit/694587212bb76132d595e93be6f2f85c8e9347cb))

* Merge pull request #27 from supabase-community/jl--update-realtime-version

Update Realtime Version ([`ac90f6c`](https://github.com/supabase-community/realtime-py/commit/ac90f6c5e7dd6b374ee3d8a15738582084de4699))

* &#39;Refactored by Sourcery&#39; ([`05920c6`](https://github.com/supabase-community/realtime-py/commit/05920c64124ddd322d31cc47181995b04db850a1))

* Merge remote-tracking branch &#39;orig/master&#39; ([`7299676`](https://github.com/supabase-community/realtime-py/commit/729967636d76b2730ec71a4683fc3d6712f5a680))

* Removing redundant comment ([`5c2b318`](https://github.com/supabase-community/realtime-py/commit/5c2b31838d24ca471eed9347bbf605c7a02a7c0b))

* quick fixes ([`e577e73`](https://github.com/supabase-community/realtime-py/commit/e577e73c3a6db2b342b2a4554f99c11aa799d75e))

* Merge pull request #1 from RizkyRajitha/ci-test

Ci test ([`428e2bd`](https://github.com/supabase-community/realtime-py/commit/428e2bdb2bbdd12368fb4f1892a8b0c64901b3d4))

* upgrade websockets to v 10.1 ([`d5b9dc7`](https://github.com/supabase-community/realtime-py/commit/d5b9dc74195385e9cf14b73fa19a0bc8f84215e8))

* rename pythonV to python-version ([`9afe2f4`](https://github.com/supabase-community/realtime-py/commit/9afe2f46f3e53f86f1978dcf7d86c8455dd3e861))

* added matrix strategy for python 3.x ([`e0ea64e`](https://github.com/supabase-community/realtime-py/commit/e0ea64e893f4331d591815ddf24c909e63808d5f))

* Merge pull request #20 from supabase-community/j0_release_new_ver

Release Version 1.3 ([`5e5b539`](https://github.com/supabase-community/realtime-py/commit/5e5b539c5f6beb8a7b232ec2c46a6abae34a9e75))

* Merge pull request #19 from anand2312/update-websockets

Update websockets ([`7f44217`](https://github.com/supabase-community/realtime-py/commit/7f442177e172c94694fe8861d9443709227d8194))

* add poetry run pytest with poetry ([`e66e554`](https://github.com/supabase-community/realtime-py/commit/e66e554afb98d7a8e0ee0c51fd897e533dc53531))

* remove matrix test , run pytest with poetry ([`6a41ef5`](https://github.com/supabase-community/realtime-py/commit/6a41ef538006e8c5a440211d576de465fa914dff))

* added gh actions for ci ([`0a60297`](https://github.com/supabase-community/realtime-py/commit/0a60297c9cce91b316355fa95eb4f25031b08a24))

* Merge pull request #17 from supabase-community/j0_hacktoberfest

Add.md files for hacktoberfest ([`70acd89`](https://github.com/supabase-community/realtime-py/commit/70acd89bde1ddd0aeb606304fb08af7fb8ec8e9e))

* Update README.md ([`83cfac7`](https://github.com/supabase-community/realtime-py/commit/83cfac7385da31a42aa588a9c044bbaeb63935cb))

* Merge pull request #13 from supabase/j0_add_transformer

Extract Transformer ([`ae7345c`](https://github.com/supabase-community/realtime-py/commit/ae7345ce191c1577660ced00d5dff6a14eb61d25))

* Update dependencies ([`dd44f66`](https://github.com/supabase-community/realtime-py/commit/dd44f66c18c74a16d87f838b484c918126189ea7))

* bump version ([`7c5ad32`](https://github.com/supabase-community/realtime-py/commit/7c5ad32d4b45f53cf7359b445f7f8b366998835f))

* Merge pull request #10 from supabase/j0_add_transformers

Add transformers ([`43d0c1c`](https://github.com/supabase-community/realtime-py/commit/43d0c1c4403751c128df2c40a326d4eda89e5f05))

* Resolve merge conflicts ([`093b224`](https://github.com/supabase-community/realtime-py/commit/093b2243517a6eb2b42cd8e65a04559d928ee832))

* Update requirements.txt ([`5472ac2`](https://github.com/supabase-community/realtime-py/commit/5472ac285a749844c7361d52da42db3451f0934f))

* Implement convert_column ([`f3c5a13`](https://github.com/supabase-community/realtime-py/commit/f3c5a13bf1caa95a8fa67b0587e829a4a5b5fb35))

* Add timestamp conversion ([`3a046b9`](https://github.com/supabase-community/realtime-py/commit/3a046b95f05128d8ecb968d1de2f7b1486bb8bd0))

* Add initial transformers lib ([`e88ff3e`](https://github.com/supabase-community/realtime-py/commit/e88ff3e172d95e364a0aa291dbaab3a1e8e0674c))

* Merge pull request #8 from supabase/j0_use_poetry

Change package management tool ([`5911b2c`](https://github.com/supabase-community/realtime-py/commit/5911b2ca6cf64aecddd015c2c6455924266d18b4))

* Merge pull request #9 from supabase/j0_allow_chaining

allow chaining with channel/on ([`450da56`](https://github.com/supabase-community/realtime-py/commit/450da5651f655bc6a75c44f90a5b39c0c8d4433f))

* allow chaining with channel/on ([`242675b`](https://github.com/supabase-community/realtime-py/commit/242675bec29e773033daa375b14919c50643c80a))

* Refactor to use poetry ([`0fd7719`](https://github.com/supabase-community/realtime-py/commit/0fd77193d58bb37f9236a42ec33d4deebdb0fd82))

* Merge pull request #7 from prettyirrelevant/master

refactored code and added logging ([`26e3146`](https://github.com/supabase-community/realtime-py/commit/26e31461b7ff1b3ba1ca4ee33ec6c7ed532d48a1))

* Merge pull request #6 from lionellloh/fix/dependencies

Fix/dependencies ([`a0579c4`](https://github.com/supabase-community/realtime-py/commit/a0579c41550abff6c02395d0e1506d18055d0823))

* include dataclasses in requirements.txt ([`06390ed`](https://github.com/supabase-community/realtime-py/commit/06390edb6ce96af4e2e48bfb19785abc263c846f))

* readme update ([`6add91f`](https://github.com/supabase-community/realtime-py/commit/6add91fc2bc3d49cb699e90c9ced014c3af37750))

* Merge pull request #4 from lionellloh/pypi

Refactorings for better distribution ([`b0edab0`](https://github.com/supabase-community/realtime-py/commit/b0edab08b8c26a0020ea8c037c13830a66a9d8d7))

* ignore .DS_store ([`9623444`](https://github.com/supabase-community/realtime-py/commit/962344478f78eb9f35a40ebd1b5d4334ddc5fdd6))

* Update Readme and version ([`850c912`](https://github.com/supabase-community/realtime-py/commit/850c912ca9e362dc2a55d7859b3a07bede31b347))

* Merge pull request #3 from lionellloh/pypi

pip pkg related refactor ([`8fef058`](https://github.com/supabase-community/realtime-py/commit/8fef058ae23ab38dfdae136f35d5d38bd8a58976))

* pip pkg related refactor ([`adef018`](https://github.com/supabase-community/realtime-py/commit/adef018da8d7ded6e8e1a549b4bd9f14db27f564))

* Merge pull request #2 from lionellloh/pypi

restructure for PYPI ([`3904e93`](https://github.com/supabase-community/realtime-py/commit/3904e93efd5081aaa14ec4b38cf0d2d451a378ae))

* restructure for PYPI ([`4949494`](https://github.com/supabase-community/realtime-py/commit/49494949e44168b0f55d55af289158bf081b3339))

* fix decorator to return func ([`ccbd91c`](https://github.com/supabase-community/realtime-py/commit/ccbd91c6cf7b2f1456f2b57e8e07c5407be01313))

* fix minor typo ([`9bf2698`](https://github.com/supabase-community/realtime-py/commit/9bf2698d411ac49217b29dcd16d2cd3c7f064b0c))

* Docs ([`4678642`](https://github.com/supabase-community/realtime-py/commit/46786423c5039c2d4694f333f19a9316d8574c42))

* `exceptions` -&gt; `Exceptions` ([`ebac053`](https://github.com/supabase-community/realtime-py/commit/ebac053fb7f35f93f9da68f8f2272d50fae37c2b))

* Decorator to check + Exception if check fails ([`5d8e49b`](https://github.com/supabase-community/realtime-py/commit/5d8e49bb8ab6d528f5d63f80282850d5da23cb1b))

* Added docstrings ([`5d8f9f5`](https://github.com/supabase-community/realtime-py/commit/5d8f9f56898b6dd11d0dd328514677956d78dab6))

* Type hints and named tuples ([`01058df`](https://github.com/supabase-community/realtime-py/commit/01058df29823730ce084b1bb721917140d1ab93d))

* Clean up ([`2c2a6df`](https://github.com/supabase-community/realtime-py/commit/2c2a6dfe995c0a85bf583abb6157f94812e1a13a))

* Removed constants, include type hints ([`b311691`](https://github.com/supabase-community/realtime-py/commit/b311691b092da9df755e5dbb70bd1d5835268817))

* Merge remote-tracking branch &#39;origin/master&#39; ([`4987917`](https://github.com/supabase-community/realtime-py/commit/498791752626d304475f69e1e957c6943ca9f508))

* ignore .idea/* ([`6dde5c5`](https://github.com/supabase-community/realtime-py/commit/6dde5c520e5844837a9af56a2c3ffe4195357da7))

* Use dataclass for Message ([`b206a61`](https://github.com/supabase-community/realtime-py/commit/b206a6188e320f273ddb3435216afa04d014a744))

* Update usage to be clearer that that it is the payload that is passed ([`45658eb`](https://github.com/supabase-community/realtime-py/commit/45658ebcb895444e791653246dc6af7f858e3681))

* Create README.md ([`53216bd`](https://github.com/supabase-community/realtime-py/commit/53216bd732367111f0f8cc48e817b0c4a7269eb8))

* requirements ([`78dc02c`](https://github.com/supabase-community/realtime-py/commit/78dc02c196ad023a507652905b522bdbb65eb3e0))

* Merge pull request #1 from lionellloh/dev

Merge POC work in to master ([`5a1d4db`](https://github.com/supabase-community/realtime-py/commit/5a1d4db119f9251058006dadfd18f8aba361ccd3))

* gitignore ([`828fe8f`](https://github.com/supabase-community/realtime-py/commit/828fe8f0f378147b7ae40bca86ba6c175961c339))

* POC works ([`80d5c42`](https://github.com/supabase-community/realtime-py/commit/80d5c426fe52252df6270b703950f2a7097f9743))

* Initial commit ([`73025b3`](https://github.com/supabase-community/realtime-py/commit/73025b3a469cb167ad548018b4aefd08d19025a3))

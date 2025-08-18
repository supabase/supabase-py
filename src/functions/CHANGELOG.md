# CHANGELOG

## [0.10.1](https://github.com/supabase/functions-py/compare/v0.10.0...v0.10.1) (2025-06-20)


### Bug Fixes

* remove jwt key validation to allow new api keys ([#212](https://github.com/supabase/functions-py/issues/212)) ([5b852e4](https://github.com/supabase/functions-py/commit/5b852e4b92f232c9b6c91e802d2f1cdbb0ab72e2))

## [0.10.0](https://github.com/supabase/functions-py/compare/v0.9.4...v0.10.0) (2025-06-19)


### Features

* allow injection of httpx client ([#205](https://github.com/supabase/functions-py/issues/205)) ([1d3ce59](https://github.com/supabase/functions-py/commit/1d3ce59d7da6b6224cb4e357125c1cbb47f8647b))

## [0.9.4](https://github.com/supabase/functions-py/compare/v0.9.3...v0.9.4) (2025-03-26)


### Bug Fixes

* custom error status code from edge function returned correctly ([#196](https://github.com/supabase/functions-py/issues/196)) ([7077a38](https://github.com/supabase/functions-py/commit/7077a38fb6c303f3c2f6d78f1265a43b04e7ec59))

## [0.9.3](https://github.com/supabase/functions-py/compare/v0.9.2...v0.9.3) (2025-01-29)


### Bug Fixes

* body types other than JSON are improperly handled when invoking a function ([#186](https://github.com/supabase/functions-py/issues/186)) ([d1ba63a](https://github.com/supabase/functions-py/commit/d1ba63a87336e475c6a765c61d1a259a2770930f))

## [0.9.2](https://github.com/supabase/functions-py/compare/v0.9.1...v0.9.2) (2025-01-17)


### Bug Fixes

* ci pipeline issue with renaming the project ([#182](https://github.com/supabase/functions-py/issues/182)) ([658a84d](https://github.com/supabase/functions-py/commit/658a84d95542defd328427e5566910106e2540b9))

## [0.9.1](https://github.com/supabase/functions-py/compare/v0.9.0...v0.9.1) (2025-01-17)


### Bug Fixes

* add full test coverage ([#180](https://github.com/supabase/functions-py/issues/180)) ([2bc3d3c](https://github.com/supabase/functions-py/commit/2bc3d3ccb4d62c98c5d13d25c2073fb86f84feb6))

## [0.9.0](https://github.com/supabase/functions-py/compare/v0.8.0...v0.9.0) (2024-11-28)


### Features

* rewrite region enumerated literals as Enums ([#164](https://github.com/supabase/functions-py/issues/164)) ([3ca78fa](https://github.com/supabase/functions-py/commit/3ca78fa14ceb6b0cb2b70ee6dd7a1229fe974cf4))

## [0.8.0](https://github.com/supabase/functions-py/compare/v0.7.0...v0.8.0) (2024-11-22)


### Features

* Check if token is a JWT ([#159](https://github.com/supabase/functions-py/issues/159)) ([44f7b39](https://github.com/supabase/functions-py/commit/44f7b39ee5f7a4d7a8019bc02599b551fb71272d))

## [0.7.0](https://github.com/supabase/functions-py/compare/v0.6.2...v0.7.0) (2024-10-31)


### Features

* Check if url is an HTTP URL ([#156](https://github.com/supabase/functions-py/issues/156)) ([6123554](https://github.com/supabase/functions-py/commit/6123554c3916d091407c00eab1e4cfb0c57dce56))

## [0.6.2](https://github.com/supabase/functions-py/compare/v0.6.1...v0.6.2) (2024-10-15)


### Bug Fixes

* bump minimal version of Python to 3.9 ([#154](https://github.com/supabase/functions-py/issues/154)) ([f2dab24](https://github.com/supabase/functions-py/commit/f2dab248b81df6c981434cee5d4160e95cb92df9))
* Types to use Option[T] ([#152](https://github.com/supabase/functions-py/issues/152)) ([637bf4e](https://github.com/supabase/functions-py/commit/637bf4e33f1c6a845654dba923e6215ed8cd4a7f))

## [0.6.1](https://github.com/supabase/functions-py/compare/v0.6.0...v0.6.1) (2024-10-02)


### Bug Fixes

* httpx minimum version update ([#150](https://github.com/supabase/functions-py/issues/150)) ([e784961](https://github.com/supabase/functions-py/commit/e7849619532c65f8d02908bc09b4abc60315b213))

## [0.6.0](https://github.com/supabase/functions-py/compare/v0.5.1...v0.6.0) (2024-09-25)


### Features

* Proxy support ([#148](https://github.com/supabase/functions-py/issues/148)) ([7710a3f](https://github.com/supabase/functions-py/commit/7710a3f1068d44ecc21aac48c9f1f9a349fe8968))

## v0.5.1 (2024-07-25)

### Chore

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.5 to 9.8.6 (#125) ([`8db273a`](https://github.com/supabase-community/functions-py/commit/8db273add3dd634667171e575143bc5a2e27faa7))

* chore(deps-dev): bump python-semantic-release from 9.8.5 to 9.8.6 (#124) ([`3b122ca`](https://github.com/supabase-community/functions-py/commit/3b122cab749abe862f5b4174cb70bd1e7f3d7ce8))

* chore(deps-dev): bump pytest from 8.2.2 to 8.3.1 (#123) ([`e4c53f2`](https://github.com/supabase-community/functions-py/commit/e4c53f2421e17d3891b4ab3d57aa991da0039a86))

### Fix

* fix: add x-region support (#126) ([`59135d8`](https://github.com/supabase-community/functions-py/commit/59135d8de63030837a2730dd2631da746386b8fe))

## v0.5.0 (2024-07-21)

### Chore

* chore(release): bump version to v0.5.0 ([`8496b3e`](https://github.com/supabase-community/functions-py/commit/8496b3e0d8eb0cbd7d4d9663b864496abcda5e0e))

* chore(deps-dev): bump pytest-asyncio from 0.23.7 to 0.23.8 (#122) ([`e1d064b`](https://github.com/supabase-community/functions-py/commit/e1d064b75fc828cdd3972ab64e65b9868043246c))

### Feature

* feat: add edge functions timeout (#120) ([`d0abc3c`](https://github.com/supabase-community/functions-py/commit/d0abc3c6a03ce0b2347379b0d7ffdc9f4d37b287))

## v0.4.7 (2024-07-14)

### Chore

* chore(release): bump version to v0.4.7 ([`9d200a9`](https://github.com/supabase-community/functions-py/commit/9d200a97bf89c296e975d4d63aa15b12be6b646a))

* chore(deps-dev): bump python-semantic-release from 9.8.3 to 9.8.5 (#119) ([`d3e1104`](https://github.com/supabase-community/functions-py/commit/d3e1104f221ce7274789856b5a3704f8aa25e60f))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.3 to 9.8.5 (#118) ([`0403bfb`](https://github.com/supabase-community/functions-py/commit/0403bfb84fb9e624974c16880f61a77cc244ff17))

* chore(deps-dev): bump python-semantic-release from 9.8.1 to 9.8.3 (#114) ([`3850c82`](https://github.com/supabase-community/functions-py/commit/3850c82add00a26b5e1a74fda7ce750bae85699a))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.1 to 9.8.3 (#113) ([`c1c0d67`](https://github.com/supabase-community/functions-py/commit/c1c0d67881273f68689959b9858767aa4372c4ef))

### Fix

* fix: version bump (#121) ([`8f9b380`](https://github.com/supabase-community/functions-py/commit/8f9b3802759eec255f3f096ed818d64cd1ff3596))

### Unknown

* Enable HTTP2 (#115) ([`dbe0c73`](https://github.com/supabase-community/functions-py/commit/dbe0c73f025608adb0de1cb7b269de1eae23241d))

## v0.4.6 (2024-06-05)

### Chore

* chore(release): bump version to v0.4.6 ([`f038cad`](https://github.com/supabase-community/functions-py/commit/f038cad35cbeaafbef9a26e4c853237a994ac9c6))

* chore(deps-dev): bump python-semantic-release from 9.8.0 to 9.8.1 (#110) ([`6167b4a`](https://github.com/supabase-community/functions-py/commit/6167b4a894b45062009ad67feefff16a1ba3ff61))

* chore(deps-dev): bump pytest from 8.2.1 to 8.2.2 (#109) ([`9d83fc0`](https://github.com/supabase-community/functions-py/commit/9d83fc0ace5c5a9310a5c3878a2db3586fd97899))

* chore(deps-dev): bump python-semantic-release from 9.7.3 to 9.8.0 (#104) ([`95f4c8e`](https://github.com/supabase-community/functions-py/commit/95f4c8ea317b62548dc196fdc81308b843e09f23))

* chore(deps-dev): bump pytest from 8.2.0 to 8.2.1 (#103) ([`b9523b8`](https://github.com/supabase-community/functions-py/commit/b9523b82b60b9e205077db31d7838af0dba3ea80))

* chore(deps-dev): bump pytest-asyncio from 0.23.6 to 0.23.7 (#102) ([`cee6c49`](https://github.com/supabase-community/functions-py/commit/cee6c49bdd155bbeab32a69977d5049148bcea5b))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.7.2 to 9.7.3 (#101) ([`556f667`](https://github.com/supabase-community/functions-py/commit/556f667e189b787d58895b0e74c71ad60e0b3d2f))

* chore(deps-dev): bump python-semantic-release from 9.7.2 to 9.7.3 (#100) ([`0a7f65f`](https://github.com/supabase-community/functions-py/commit/0a7f65fbb4ad9f0fb6fc2d1b07538775d72fbc7a))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.5.0 to 9.7.2 (#99) ([`730f067`](https://github.com/supabase-community/functions-py/commit/730f067030d047fb8675b366bc428930f06aa4f1))

* chore(deps-dev): bump python-semantic-release from 9.5.0 to 9.7.2 (#98) ([`6b392ac`](https://github.com/supabase-community/functions-py/commit/6b392aca65d47f215a3f51ff840d15e951da2cae))

* chore(deps-dev): bump pytest from 8.1.1 to 8.2.0 (#89) ([`b0f272b`](https://github.com/supabase-community/functions-py/commit/b0f272b7412daee3b23395c9f1363e5290e06e30))

* chore(deps-dev): bump black from 24.3.0 to 24.4.2 (#88) ([`b7944de`](https://github.com/supabase-community/functions-py/commit/b7944decb2584a519941ed53e8786754ac6765d8))

* chore(ci): bump python-semantic-release/python-semantic-release from 9.4.1 to 9.5.0 (#86) ([`fbf01fe`](https://github.com/supabase-community/functions-py/commit/fbf01fe6ff2060152168b96083630d182a4f75b6))

* chore(deps-dev): bump python-semantic-release from 9.4.1 to 9.5.0 (#85) ([`53653e0`](https://github.com/supabase-community/functions-py/commit/53653e027c31e2aecb686c06f188bd3914bb417d))

* chore(deps-dev): bump python-semantic-release from 9.3.1 to 9.4.1 (#81) ([`42b8b95`](https://github.com/supabase-community/functions-py/commit/42b8b9577060dd445a6f7de5fb34e135084e450a))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.3.1 to 9.4.1 (#80) ([`9d7c165`](https://github.com/supabase-community/functions-py/commit/9d7c165c9b0f3b495b35d6e2d7f2942f8f056f16))

* chore(deps-dev): bump respx from 0.21.0 to 0.21.1 (#77) ([`0cf2183`](https://github.com/supabase-community/functions-py/commit/0cf2183efb19ce6898bcdd7d4163534578944996))

* chore(deps-dev): bump python-semantic-release from 9.3.0 to 9.3.1 (#76) ([`98ff552`](https://github.com/supabase-community/functions-py/commit/98ff5526ba1fd5b2abbb5fac3c10dba94864b4a6))

* chore(deps-dev): bump pytest-cov from 4.1.0 to 5.0.0 (#75) ([`519fa30`](https://github.com/supabase-community/functions-py/commit/519fa3060f78ee1e3ba13dbf89fc49a5155a0710))

* chore(deps): bump actions/cache from 3 to 4 (#74) ([`9f61fda`](https://github.com/supabase-community/functions-py/commit/9f61fdadc006ac7a390a1890cbf270e8eecf1c67))

* chore(deps): bump abatilo/actions-poetry from 2 to 3 (#73) ([`e521357`](https://github.com/supabase-community/functions-py/commit/e5213574c32f87c1e47c647c86593e1d59c408c8))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.3.0 to 9.3.1 (#72)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a0a9ad8`](https://github.com/supabase-community/functions-py/commit/a0a9ad8959625772b5e63ebecee96eb783e15d12))

### Ci

* ci(deps): bump python-semantic-release/python-semantic-release from 9.8.0 to 9.8.1 (#108) ([`1e162de`](https://github.com/supabase-community/functions-py/commit/1e162deaedd96e286d74d7cd86cbe66ad0add834))

* ci(deps): bump python-semantic-release/python-semantic-release from 9.7.3 to 9.8.0 (#105) ([`66c3c1a`](https://github.com/supabase-community/functions-py/commit/66c3c1ad682fa0054ad3520cee9499d496923b03))

### Fix

* fix: add &#34;verify&#34; flag to the creation of client ([`f43038c`](https://github.com/supabase-community/functions-py/commit/f43038cf59d772a47420f8ae6cb3ca81b2808193))

### Unknown

* Follow redirects (#107) ([`ccb3f7f`](https://github.com/supabase-community/functions-py/commit/ccb3f7fa81e0e1257e6551a483900083b173135c))

* Update .pre-commit-config.yaml (#93) ([`3201e5d`](https://github.com/supabase-community/functions-py/commit/3201e5d9e68c1e580ea5e61028b08dde4ba3123e))

* Add stale bot (#92) ([`1fb54a8`](https://github.com/supabase-community/functions-py/commit/1fb54a80b211c93a8b7b8118842ab411dc33e22b))

## v0.4.5 (2024-03-23)

### Chore

* chore(release): bump version to v0.4.5 ([`d2b7efb`](https://github.com/supabase-community/functions-py/commit/d2b7efb158baf22a37d0652614c6aaee43fa389a))

### Fix

* fix: configure poetry in github action (#71) ([`886f0fb`](https://github.com/supabase-community/functions-py/commit/886f0fb1590567527159df8944a9ab7d418e5f00))

## v0.4.4 (2024-03-23)

### Chore

* chore(release): bump version to v0.4.4 ([`ebb987f`](https://github.com/supabase-community/functions-py/commit/ebb987fc0df58d41a0307065d28ae14b6697cb3b))

### Fix

* fix: update to perform build via poetry (#70) ([`d518ce5`](https://github.com/supabase-community/functions-py/commit/d518ce5b81fef2ec30907c9261fde29522e37222))

## v0.4.3 (2024-03-23)

### Chore

* chore(release): bump version to v0.4.3 ([`5c707e9`](https://github.com/supabase-community/functions-py/commit/5c707e998df07afdd67c629f034e954564a1c65b))

### Fix

* fix: add supafunc package distribution (#69) ([`d8a6f9a`](https://github.com/supabase-community/functions-py/commit/d8a6f9a89909c5d4bc3d6c11fb369407931c9cc5))

## v0.4.2 (2024-03-23)

### Chore

* chore(release): bump version to v0.4.2 ([`be38b0b`](https://github.com/supabase-community/functions-py/commit/be38b0b38ce878df629b1170b69ccbaf5e54ba03))

### Fix

* fix: ci workflow (#68) ([`a747a72`](https://github.com/supabase-community/functions-py/commit/a747a729b35d31197d2b772d2f5ddc9e5ec9daed))

## v0.4.1 (2024-03-23)

### Chore

* chore(release): bump version to v0.4.1 ([`f9a9a2f`](https://github.com/supabase-community/functions-py/commit/f9a9a2feede1cec36d9a9c9dc35d64594d4f1f84))

* chore(deps-dev): bump python-semantic-release from 9.2.0 to 9.3.0 (#66)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`7d1ce46`](https://github.com/supabase-community/functions-py/commit/7d1ce467159fa08d8cde29056d52553b186319ce))

* chore(deps): bump codecov/codecov-action from 3 to 4 (#50)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ffe43b2`](https://github.com/supabase-community/functions-py/commit/ffe43b2ded9396a893d1c12d9a0077b70aed52df))

* chore(deps): bump actions/checkout from 2 to 4 (#52)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a809e98`](https://github.com/supabase-community/functions-py/commit/a809e98368b1ff8369c787439a5ba2d01a0ebfcf))

* chore(deps): bump abatilo/actions-poetry from 2.2.0 to 3.0.0 (#54)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`4c1365c`](https://github.com/supabase-community/functions-py/commit/4c1365cbb94502cad0bc14032bbf48c74de1971f))

* chore(deps): bump python-semantic-release/python-semantic-release from 8.0.0 to 9.3.0 (#65)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`cddbd1f`](https://github.com/supabase-community/functions-py/commit/cddbd1fe983e600ec4f9cf177a9b5e1f582a7ff0))

* chore(deps-dev): bump pytest from 8.0.2 to 8.1.1 (#57)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`43a2741`](https://github.com/supabase-community/functions-py/commit/43a27418526d2cdd8739ad4f4c69e21a6743d43e))

* chore(deps-dev): bump respx from 0.20.2 to 0.21.0 (#61)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a1481fd`](https://github.com/supabase-community/functions-py/commit/a1481fd126b10719bd92061012a9efba0354530f))

* chore(deps-dev): bump pytest-asyncio from 0.23.5 to 0.23.6 (#62)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a821fe8`](https://github.com/supabase-community/functions-py/commit/a821fe80e5f2f2a68395e86ecb782856f1d18642))

* chore(deps-dev): bump python-semantic-release from 9.1.1 to 9.2.0 (#60)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`719ed64`](https://github.com/supabase-community/functions-py/commit/719ed64f587c40bd2c98255d34c36788e1ccae1b))

* chore(deps): bump actions/setup-python from 2 to 5 (#53)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`867bab3`](https://github.com/supabase-community/functions-py/commit/867bab3a99197da2a7437b903b52afc7a4e5d0a1))

* chore(deps-dev): bump black from 24.2.0 to 24.3.0 (#58)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`0a84c99`](https://github.com/supabase-community/functions-py/commit/0a84c9951bc5ba78d218599bcd1d15a32909fdf9))

* chore(deps-dev): bump pytest from 7.4.4 to 8.0.2 (#48)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ae754cf`](https://github.com/supabase-community/functions-py/commit/ae754cfb4bc7e8832a7aac95f0d29077b2b7ad80))

* chore(deps-dev): bump python-semantic-release from 8.7.0 to 9.1.1 (#47)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`f108ed7`](https://github.com/supabase-community/functions-py/commit/f108ed7691a2bd0801b946e96c7c16cec234972b))

* chore(deps-dev): bump black from 23.12.1 to 24.2.0 (#43)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ed09227`](https://github.com/supabase-community/functions-py/commit/ed092279ad8911f2664a92c0c1e332b3f42e4555))

* chore(deps-dev): bump pytest-asyncio from 0.23.3 to 0.23.5 (#42)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e87489b`](https://github.com/supabase-community/functions-py/commit/e87489b98c7fab52417e9b1f81a2fd4a83caf627))

* chore: rename package to supabase_functions (#37) ([`5b5b5c9`](https://github.com/supabase-community/functions-py/commit/5b5b5c9071d74b7ec3e3da0dd83bbd6bd9303152))

### Fix

* fix: Update library name in pyproject file (#67) ([`5b5fe0d`](https://github.com/supabase-community/functions-py/commit/5b5fe0dcdfd81b1e91da47d49d6aecaad0505a3d))

* fix: bump httpx from 0.25.2 to 0.27.0 (#46)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`03fcb25`](https://github.com/supabase-community/functions-py/commit/03fcb25d5fdca5ee07edac2ba769d797f54e1dc7))

## v0.4.0 (2024-02-29)

### Chore

* chore(release): bump version to v0.4.0 ([`555df53`](https://github.com/supabase-community/functions-py/commit/555df5384d2c8c8de7565f609f231923c118cd8f))

### Feature

* feat: add actions to dependabot.yml (#49) ([`0fa1c6b`](https://github.com/supabase-community/functions-py/commit/0fa1c6b91363714a0f889d73e52a47ca2e5be349))

## v0.3.3 (2024-01-03)

### Chore

* chore(release): bump version to v0.3.3 ([`cd02bb2`](https://github.com/supabase-community/functions-py/commit/cd02bb26e501adb6c66007f637af0ba87b37a6f0))

### Fix

* fix: update job to publish legacy package if current is released (#36) ([`2565c37`](https://github.com/supabase-community/functions-py/commit/2565c372124c08bc2a0bd8fd4b3005cf427062e3))

## v0.3.2 (2024-01-03)

### Chore

* chore(release): bump version to v0.3.2 ([`403418c`](https://github.com/supabase-community/functions-py/commit/403418cc3a801be12e73f84e53daddd517cd5de0))

* chore(deps-dev): bump isort from 5.12.0 to 5.13.0 (#24) ([`e7443ee`](https://github.com/supabase-community/functions-py/commit/e7443eeaad029a19a4276bae8ebfb899d042be3a))

* chore(deps-dev): bump isort from 5.12.0 to 5.13.0

Bumps [isort](https://github.com/pycqa/isort) from 5.12.0 to 5.13.0.
- [Release notes](https://github.com/pycqa/isort/releases)
- [Changelog](https://github.com/PyCQA/isort/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pycqa/isort/compare/5.12.0...5.13.0)

---
updated-dependencies:
- dependency-name: isort
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`89a31c9`](https://github.com/supabase-community/functions-py/commit/89a31c9afb987063f18dd853bc826e4d7e815be3))

* chore(deps-dev): bump pytest-asyncio from 0.21.1 to 0.23.2 (#22) ([`ab767f5`](https://github.com/supabase-community/functions-py/commit/ab767f5cf591679f38404cf609a42d853620c96f))

* chore(deps-dev): bump pytest-asyncio from 0.21.1 to 0.23.2

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.21.1 to 0.23.2.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.21.1...v0.23.2)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`f6fb590`](https://github.com/supabase-community/functions-py/commit/f6fb5906e99e5194413ef8b7f819ba82ae47355e))

* chore: allow manual workflow trigger for releases (#19) ([`07d1ffa`](https://github.com/supabase-community/functions-py/commit/07d1ffa6faa89219f7c73cbd4699436763d9d8bc))

* chore: allow manual workflow trigger for releases ([`2a01399`](https://github.com/supabase-community/functions-py/commit/2a013997215f417fb0efe2badfc9b8a2d3686c48))

### Ci

* ci: update workflow with new pypi project name (#34) ([`7564e2b`](https://github.com/supabase-community/functions-py/commit/7564e2bc1d157a279175a3c8ad6fb2708e1700f4))

### Fix

* fix: update httpx and other dev dependencies (#35) ([`1f8897f`](https://github.com/supabase-community/functions-py/commit/1f8897f88acc4449cd697bd0e122bd4ee3bf0417))

## v0.3.1 (2023-10-30)

### Chore

* chore(release): bump version to v0.3.1 ([`b787f01`](https://github.com/supabase-community/functions-py/commit/b787f0187c1a5312ea368919afd24863ff2f40f0))

### Fix

* fix: exceptions now has message in dictionary (#16) ([`7273927`](https://github.com/supabase-community/functions-py/commit/7273927aa9d0e6eb9d9c9985a7ba5b42f9b6296d))

* fix: exceptions now has message in dictionary

Added tests to check for the messages. ([`07a813a`](https://github.com/supabase-community/functions-py/commit/07a813a02ffcf8999802cece27ee5278c140760d))

## v0.3.0 (2023-10-29)

### Chore

* chore(release): bump version to v0.3.0 ([`4e18712`](https://github.com/supabase-community/functions-py/commit/4e1871215e72efed058d5adf619ae2be0bb27b56))

### Feature

* feat: downgrade httpx dep to 0.24.0 (#15) ([`1f37216`](https://github.com/supabase-community/functions-py/commit/1f37216326c26b65a3c9ccd1c29bea0a184c7624))

### Fix

* fix: update lockfile ([`d4856ec`](https://github.com/supabase-community/functions-py/commit/d4856ec8c6bbbde7efe7ca67c5137ba75e8e7bdb))

### Unknown

* Update pyproject.toml ([`dd43949`](https://github.com/supabase-community/functions-py/commit/dd4394994ae995dd6f953093da73cbd9c1344483))

* Restoring order to the CI/CD pipeline ([`4f28dc6`](https://github.com/supabase-community/functions-py/commit/4f28dc628c9a9aac27a153121c90960bddb5c8bf))

## v0.2.4 (2023-10-25)

### Chore

* chore(release): bump version to v0.2.4 ([`f618547`](https://github.com/supabase-community/functions-py/commit/f61854760d2d90d1352962e427d099da6dac50c1))

* chore: update readme with correct function call ([`88fc1a7`](https://github.com/supabase-community/functions-py/commit/88fc1a797ef7d848bd2e870ddadcf8d51d405989))

* chore(release): bump version to v0.2.4 ([`e958722`](https://github.com/supabase-community/functions-py/commit/e95872200a7470da0e92bd95431eea1e20c66df3))

* chore: bump autoflake version ([`fc3a7bb`](https://github.com/supabase-community/functions-py/commit/fc3a7bb5788feca7acbdf4662feee7cce87f2cda))

### Fix

* fix: correct return type from invoke ([`9a15026`](https://github.com/supabase-community/functions-py/commit/9a15026bbbc63cd4b6d960f8a48db40a06770381))

* fix: add single instance of client instantiation ([`4b8a134`](https://github.com/supabase-community/functions-py/commit/4b8a134ac675bdcc0387cb1d1d55068e1b6be253))

### Unknown

* Temporary CI change to allow publishing of package ([`2d66f21`](https://github.com/supabase-community/functions-py/commit/2d66f21c01efcfd3ba34ab458c11977009580118))

* Merge pull request #11 from supabase-community/silentworks/update-readme

chore: update readme with correct function call ([`1dfe72e`](https://github.com/supabase-community/functions-py/commit/1dfe72eb28c35b0452e8f65d6e9612f9d4e80eb3))

* Merge pull request #9 from supabase-community/silentworks/sync_functions

Add sync functions ([`e2db242`](https://github.com/supabase-community/functions-py/commit/e2db242994c66ce3beec399416512342a2266f85))

* update file formatting with black ([`b1c64f5`](https://github.com/supabase-community/functions-py/commit/b1c64f51a487e9782c45324d0903a5e18c7bd31e))

* Apply suggestions from code review

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`e2a59aa`](https://github.com/supabase-community/functions-py/commit/e2a59aaff604a8c0ff1e3d648a1d2ae3aff44ea7))

* Add github workflow ([`14c8db9`](https://github.com/supabase-community/functions-py/commit/14c8db932527056343e5e7af012db87af6242006))

* Update errors and function signature of invoke ([`575da96`](https://github.com/supabase-community/functions-py/commit/575da968238a494de0996226df0bf54a48bf4e2b))

* Apply suggestions from code review

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`b60615d`](https://github.com/supabase-community/functions-py/commit/b60615d2c70c5a2e32e87f850d5fe1d68e492f59))

* Update supafunc/errors.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`2971673`](https://github.com/supabase-community/functions-py/commit/2971673451c4775c3f5e400983972bebefff4dfe))

* Add sync functions
Add pytests
Throw errors instead of returning them ([`692022f`](https://github.com/supabase-community/functions-py/commit/692022fa4816de5ec3e4cd929352535af719bb87))

## v0.2.3 (2023-08-04)

### Chore

* chore: bump version ([`d5f32ba`](https://github.com/supabase-community/functions-py/commit/d5f32ba75368cc1ba337e1cda0e6d89d426160b1))

* chore: bump httpx to 0.24 ([`6152992`](https://github.com/supabase-community/functions-py/commit/615299278b1d810c1113546938b81eabf075987f))

* chore(deps): bump httpx from 0.23.0 to 0.24.1

Bumps [httpx](https://github.com/encode/httpx) from 0.23.0 to 0.24.1.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.23.0...0.24.1)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`f5c5ca4`](https://github.com/supabase-community/functions-py/commit/f5c5ca44de7d130be5ba2da0671ae8a845ad4d0d))

### Fix

* fix: small typo in authorization

for consistent naming ([`3f0bba8`](https://github.com/supabase-community/functions-py/commit/3f0bba80100f86886f4e8132862fc1e96868e479))

### Unknown

* Merge pull request #4 from anand2312/annad/bump-httpx

chore: bump httpx to 0.24 ([`f9d1c3c`](https://github.com/supabase-community/functions-py/commit/f9d1c3c6f3611f322d336bbd86f080c0d65f6d28))

* Merge pull request #3 from supabase-community/dependabot/pip/main/httpx-0.24.1

chore(deps): bump httpx from 0.23.0 to 0.24.1 ([`67ada27`](https://github.com/supabase-community/functions-py/commit/67ada272a6ea645b9b51041e6dedd829d3410113))

* Create dependabot.yml ([`c7394d7`](https://github.com/supabase-community/functions-py/commit/c7394d7691b6ed35997f6222fe8f37748e132242))

* Merge pull request #2 from 0xflotus/patch-1

fix: small typo in authorization ([`7c60eda`](https://github.com/supabase-community/functions-py/commit/7c60eda605337784a63a99a1405a6cb2c5f407f1))

## v0.2.2 (2022-10-10)

### Chore

* chore: update version ([`a6584a7`](https://github.com/supabase-community/functions-py/commit/a6584a783ed9fea347f89c87f420ba4d56e0383a))

### Feature

* feat: version 0.1.4 ([`7ffeec5`](https://github.com/supabase-community/functions-py/commit/7ffeec5465ce86f7ee077dbf18c21f332f31b1a5))

### Fix

* fix: update dependencies ([`91bc97b`](https://github.com/supabase-community/functions-py/commit/91bc97b66ef609618bb953a6557a2eb904b35d00))

* fix: add default for optional headers ([`02c838c`](https://github.com/supabase-community/functions-py/commit/02c838c73b692ea16912192278dd8550570553a1))

* fix: pass down body ([`d3f9f61`](https://github.com/supabase-community/functions-py/commit/d3f9f6187b7bd7206f89eb3331fa6ea6f13dd58e))

## v0.1.4 (2022-03-31)

### Chore

* chore: update version ([`883661f`](https://github.com/supabase-community/functions-py/commit/883661f3c50d8d5fabcbf9639daaf7e6b8fa2499))

* chore: update version ([`61f78b4`](https://github.com/supabase-community/functions-py/commit/61f78b4986917a234e631a233d72f65b28b414a4))

* chore: cleanup and add LICENSE ([`c9d035e`](https://github.com/supabase-community/functions-py/commit/c9d035eb4005ef9b595206395513abaca8325953))

* chore: rename and update README ([`0e26f92`](https://github.com/supabase-community/functions-py/commit/0e26f92f27079d6ab63da6860f6a26d229be2374))

### Unknown

* initial commit ([`5c93da6`](https://github.com/supabase-community/functions-py/commit/5c93da6948288c3312c0065e22ab968d25b9801b))

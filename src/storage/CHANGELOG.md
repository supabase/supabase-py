# CHANGELOG

## [0.12.2](https://github.com/supabase/storage-py/compare/v0.12.1...v0.12.2) (2025-08-15)


### Bug Fixes

* remove extraneous char in test ([#389](https://github.com/supabase/storage-py/issues/389)) ([088cb7f](https://github.com/supabase/storage-py/commit/088cb7f74eb68deafa007b7b333ed9a9aac4b751))
* use `BaseModel` instead of `dataclass` ([#386](https://github.com/supabase/storage-py/issues/386)) ([c4a81fb](https://github.com/supabase/storage-py/commit/c4a81fb9f7acacf8dccbf579daf4030200d8ab20))

## [0.12.1](https://github.com/supabase/storage-py/compare/v0.12.0...v0.12.1) (2025-08-05)


### Bug Fixes

* add optional type field to bucket metadata ([#380](https://github.com/supabase/storage-py/issues/380)) ([ce48f6c](https://github.com/supabase/storage-py/commit/ce48f6c353453f9971e3c5614b56d02c9af40645))

## [0.12.0](https://github.com/supabase/storage-py/compare/v0.11.3...v0.12.0) (2025-06-19)


### Features

* allow injection of httpx client ([#363](https://github.com/supabase/storage-py/issues/363)) ([b04be02](https://github.com/supabase/storage-py/commit/b04be02edaaa09801b1fd90e755c9ae0eedbb187))

## [0.11.3](https://github.com/supabase/storage-py/compare/v0.11.2...v0.11.3) (2025-01-29)


### Bug Fixes

* older python versions are broken due to NotRequired ([#344](https://github.com/supabase/storage-py/issues/344)) ([ca567e9](https://github.com/supabase/storage-py/commit/ca567e9982a2f29cbc69c3e476ffcd8dad03abf5))

## [0.11.2](https://github.com/supabase/storage-py/compare/v0.11.1...v0.11.2) (2025-01-29)


### Bug Fixes

* add correct naming for returned data keys ([#339](https://github.com/supabase/storage-py/issues/339)) ([4527da6](https://github.com/supabase/storage-py/commit/4527da69a87da08a13f6630bbdd919d721beef4a))

## [0.11.1](https://github.com/supabase/storage-py/compare/v0.11.0...v0.11.1) (2025-01-23)


### Bug Fixes

* exists method raises error when no file found ([#335](https://github.com/supabase/storage-py/issues/335)) ([cc37894](https://github.com/supabase/storage-py/commit/cc378944d97e61718cfa31e5667e7ed52c07e428))

## [0.11.0](https://github.com/supabase/storage-py/compare/v0.10.0...v0.11.0) (2024-12-30)


### Features

* add custom-metadata to upload ([#328](https://github.com/supabase/storage-py/issues/328)) ([d4f9794](https://github.com/supabase/storage-py/commit/d4f979492f94cab6402cf158a41172ef46d68559))
* Implement info and exists file API methods ([#318](https://github.com/supabase/storage-py/issues/318)) ([0100ff1](https://github.com/supabase/storage-py/commit/0100ff10af7fc86cb6286269a7b91195e0393d3a))


### Bug Fixes

* file name in signed URLs is not URI-encoded ([#324](https://github.com/supabase/storage-py/issues/324)) ([c58fbb0](https://github.com/supabase/storage-py/commit/c58fbb0afcff087616d5913c3953e849bb2f6885))
* incorrect upload return type ([#327](https://github.com/supabase/storage-py/issues/327)) ([eb8034f](https://github.com/supabase/storage-py/commit/eb8034f4f2ae4fdb2b12b3dc048d2cf4080fc193))
* upload doesn't close file handle ([#323](https://github.com/supabase/storage-py/issues/323)) ([02ae7fc](https://github.com/supabase/storage-py/commit/02ae7fca681d3f73211c3a500145ed395a159ec3))

## [0.10.0](https://github.com/supabase/storage-py/compare/v0.9.0...v0.10.0) (2024-11-22)


### Features

* add new storage error class ([#313](https://github.com/supabase/storage-py/issues/313)) ([f040f10](https://github.com/supabase/storage-py/commit/f040f10c3a17deec3aa96203c1629174c75b9b00))

## [0.9.0](https://github.com/supabase/storage-py/compare/v0.8.2...v0.9.0) (2024-10-28)


### Features

* remove methods from the bucket object ([#305](https://github.com/supabase/storage-py/issues/305)) ([faa914d](https://github.com/supabase/storage-py/commit/faa914dfc460bdc6a63955e8affbb1275f1e984f))


### Bug Fixes

* add correct return data for upload to signed url ([#309](https://github.com/supabase/storage-py/issues/309)) ([748067f](https://github.com/supabase/storage-py/commit/748067f791a86a4298dd9075227a1be98c0ca4cc))
* add search params to list buckets method ([#308](https://github.com/supabase/storage-py/issues/308)) ([fca2f00](https://github.com/supabase/storage-py/commit/fca2f005f3857e0f96b0505ab83474e3cf5e5e18))
* upload and update method returns correct response body ([#307](https://github.com/supabase/storage-py/issues/307)) ([a9e874a](https://github.com/supabase/storage-py/commit/a9e874a12fd448d2eb3e48df2a80e187b9f41fbb))

## [0.8.2](https://github.com/supabase/storage-py/compare/v0.8.1...v0.8.2) (2024-10-18)


### Bug Fixes

* bump minimal version of Python to 3.9 ([#302](https://github.com/supabase/storage-py/issues/302)) ([b0811b2](https://github.com/supabase/storage-py/commit/b0811b2b38d712d8cd136301663b0a5de20bf890))

## [0.8.1](https://github.com/supabase/storage-py/compare/v0.8.0...v0.8.1) (2024-10-02)


### Bug Fixes

* httpx minimum version update ([#299](https://github.com/supabase/storage-py/issues/299)) ([90d2436](https://github.com/supabase/storage-py/commit/90d2436900558703129788679b356a21221f5c41))

## [0.8.0](https://github.com/supabase/storage-py/compare/v0.7.7...v0.8.0) (2024-09-28)


### Features

* Proxy support ([#297](https://github.com/supabase/storage-py/issues/297)) ([59d733a](https://github.com/supabase/storage-py/commit/59d733a33145389b763c33985079257be0e3a8c3))

## v0.7.7 (2024-07-14)

### Chore

* chore(deps-dev): bump python-semantic-release from 9.8.3 to 9.8.5 (#276)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`0676ed6`](https://github.com/supabase-community/storage-py/commit/0676ed68d83f38649b869613b0e903e042248bec))

* chore: bump dependencies ([`89876df`](https://github.com/supabase-community/storage-py/commit/89876dfcf7721fb87d716a61deac596127107368))

* chore(deps-dev): bump sphinx-toolbox from 3.6.0 to 3.7.0 (#273)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`bdcb828`](https://github.com/supabase-community/storage-py/commit/bdcb828a6fe38c7454cab8e16b2d094f105e38c5))

* chore(deps): bump certifi from 2024.2.2 to 2024.7.4 in the pip group across 1 directory (#275)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`867759d`](https://github.com/supabase-community/storage-py/commit/867759dc83a1a1e3aa20c017886425212ba4b024))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.3 to 9.8.5 (#277)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`fd7a2b0`](https://github.com/supabase-community/storage-py/commit/fd7a2b011c37c52a745a49bdc2d7c8f1a90d6284))

* chore(deps-dev): bump sphinx-toolbox from 3.5.0 to 3.6.0 (#270) ([`a965424`](https://github.com/supabase-community/storage-py/commit/a965424de5200782b021056ce2d8e08b2d0d718a))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.8.1 to 9.8.3 ([`36f45f1`](https://github.com/supabase-community/storage-py/commit/36f45f1b94f275ebebddb7b0df6f40b1b0570796))

* chore(deps-dev): bump python-semantic-release from 9.8.1 to 9.8.3 ([`1fb3885`](https://github.com/supabase-community/storage-py/commit/1fb388562dbafa202f1a9e743e44bea9d68ed726))

* chore(deps-dev): bump urllib3 from 2.2.1 to 2.2.2 in the pip group across 1 directory (#264) ([`af591ee`](https://github.com/supabase-community/storage-py/commit/af591ee9511500a7e6f1a4cb54aec08ad5fa9b65))

* chore(deps): bump typing-extensions from 4.12.1 to 4.12.2 (#263) ([`b22f82b`](https://github.com/supabase-community/storage-py/commit/b22f82bc0b80db2585b009c2dd31f3d27b6989a2))

* chore(deps-dev): bump requests from 2.31.0 to 2.32.2 in the pip group across 1 directory (#262) ([`82e6aed`](https://github.com/supabase-community/storage-py/commit/82e6aed5547cc4d5ee1b369cfc76ad55ba14bf49))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.7.3 to 9.8.1 (#261) ([`fc80cee`](https://github.com/supabase-community/storage-py/commit/fc80ceea43505d7cc3aa6b64eddf3c9eafe81254))

* chore(deps-dev): bump python-semantic-release from 9.7.3 to 9.8.1 (#259) ([`ddad5dd`](https://github.com/supabase-community/storage-py/commit/ddad5dd9089575fdfb0223fdb40c73594fde5f12))

* chore(deps): bump typing-extensions from 4.11.0 to 4.12.1 (#258) ([`a1ec9b1`](https://github.com/supabase-community/storage-py/commit/a1ec9b105c6ffc8989b3ea0fdf6fb4506e4aa842))

### Fix

* fix: version bump (#278) ([`cd12e97`](https://github.com/supabase-community/storage-py/commit/cd12e97f1e61b1d52c10de6b6ccaa3f47c4310a0))

### Unknown

* Enable HTTP2 (#271) ([`f98d565`](https://github.com/supabase-community/storage-py/commit/f98d565e65791103cb9f79da0bbcc4401f127ab2))

## v0.7.6 (2024-06-05)

### Fix

* fix: follow redirects (#257) ([`521fbd9`](https://github.com/supabase-community/storage-py/commit/521fbd924e0633b202fa792d5a52cf241e455060))

## v0.7.5 (2024-06-04)

### Chore

* chore(deps): bump python-semantic-release/python-semantic-release from 9.7.2 to 9.7.3 (#249) ([`ed5ed18`](https://github.com/supabase-community/storage-py/commit/ed5ed1826fdb1ec399e81e6d54b659125321f81e))

* chore(deps-dev): bump python-semantic-release from 9.7.2 to 9.7.3 (#248) ([`da71dd4`](https://github.com/supabase-community/storage-py/commit/da71dd4bf2be866a1642eab17bb78144f0597e85))

* chore(deps-dev): bump python-semantic-release from 9.4.1 to 9.7.2 (#246) ([`eef7b04`](https://github.com/supabase-community/storage-py/commit/eef7b0493e1ec43deb7e183eaadb87fc03ebff49))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.4.1 to 9.7.2 (#247) ([`1527f18`](https://github.com/supabase-community/storage-py/commit/1527f184cd2530a5ec5c294c4eadb811056df0d6))

* chore: update .pre-commit-config.yaml (#240) ([`69ae839`](https://github.com/supabase-community/storage-py/commit/69ae8398328955c4b51a4b7ef4a5e1eb043dace1))

* chore(deps-dev): bump black from 24.3.0 to 24.4.2 (#236) ([`0449382`](https://github.com/supabase-community/storage-py/commit/04493823df2ee691a2cb3c7a4c04206474af4096))

* chore(tests): add supabase cli for tests (#245) ([`b148b09`](https://github.com/supabase-community/storage-py/commit/b148b090831210f06a30a9f08f0cc58728cbe810))

* chore(deps): bump idna from 3.6 to 3.7 (#228) ([`3ff6eed`](https://github.com/supabase-community/storage-py/commit/3ff6eed6e4410b52490cce7b2359dbfd59fb3cf6))

* chore(deps-dev): bump python-semantic-release from 9.3.0 to 9.4.1 (#225) ([`0b6dc6c`](https://github.com/supabase-community/storage-py/commit/0b6dc6cd6f7ef844c4edf485680b9bde57bc4acb))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.4.0 to 9.4.1 (#227) ([`4ce32bc`](https://github.com/supabase-community/storage-py/commit/4ce32bc262c3b2a73df8cb2c08e28ffa2052176e))

* chore(deps): bump typing-extensions from 4.10.0 to 4.11.0 (#226) ([`2650cd8`](https://github.com/supabase-community/storage-py/commit/2650cd8195f17cf5ab11d5315a710bd8ac5ab629))

* chore(deps-dev): bump pytest-cov from 4.1.0 to 5.0.0 (#221) ([`2754a9e`](https://github.com/supabase-community/storage-py/commit/2754a9eaab978275bbfa316bbf3c70da3d61fb74))

* chore(deps): bump actions/cache from 3 to 4 (#219) ([`664519c`](https://github.com/supabase-community/storage-py/commit/664519c714e1a23e07047339d9a307aa630d9552))

* chore(deps): bump abatilo/actions-poetry from 2 to 3 (#218) ([`75e9dba`](https://github.com/supabase-community/storage-py/commit/75e9dba8bcb68010df2dfeb65d48ecb54dc32223))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.3.0 to 9.4.0 (#224) ([`176d0da`](https://github.com/supabase-community/storage-py/commit/176d0da2934e7205982496cedf1c2c03874a0638))

### Fix

* fix: add &#34;verify&#34; flag to the creation of client ([`9ad75b0`](https://github.com/supabase-community/storage-py/commit/9ad75b0a7259dcd21c2a854ca4a498b67afa1611))

### Unknown

* Add stale bot (#237) ([`81935d3`](https://github.com/supabase-community/storage-py/commit/81935d38e1e2eefebe96dc91d8af012e015caf83))

## v0.7.4 (2024-03-23)

### Chore

* chore(deps-dev): bump python-semantic-release from 9.1.1 to 9.3.0 (#213)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e2f594f`](https://github.com/supabase-community/storage-py/commit/e2f594f17b3f3596779b1aa83c60841868657503))

* chore(deps): bump python-dateutil from 2.8.2 to 2.9.0.post0 (#201)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`7471e7a`](https://github.com/supabase-community/storage-py/commit/7471e7a7c36750692b03501805e9059863787f99))

* chore: update ci pipeline to include python 3.12 in tests (#217) ([`dd264f1`](https://github.com/supabase-community/storage-py/commit/dd264f1793f3ca86ad544d5cdc0dcbb786c22904))

* chore(deps): bump httpx from 0.25.0 to 0.27.0 (#192)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`25b2d02`](https://github.com/supabase-community/storage-py/commit/25b2d02c7a7de2cd084a6644d40f7443acacc21c))

* chore(deps-dev): bump jinja2 from 3.1.2 to 3.1.3 (#182)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3b419f5`](https://github.com/supabase-community/storage-py/commit/3b419f50adb893ce34bced49fc9ed4fe8bd27c6c))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.2.2 to 9.3.0 (#215)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`290442a`](https://github.com/supabase-community/storage-py/commit/290442a13f5143af6db14a4a830ef319cab883e7))

* chore(deps-dev): bump pytest from 8.1.0 to 8.1.1 (#206)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`8bcb7a5`](https://github.com/supabase-community/storage-py/commit/8bcb7a5963d0d694ea20fe7f1da31e2474950809))

* chore(deps-dev): bump black from 24.2.0 to 24.3.0 (#208)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e19d5c0`](https://github.com/supabase-community/storage-py/commit/e19d5c0311813cccf74a726fa7bbe9aee86a0765))

* chore(deps): bump python-semantic-release/python-semantic-release from 9.1.1 to 9.2.2 (#210)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c22f449`](https://github.com/supabase-community/storage-py/commit/c22f44936e14aba015da29c2709c8943ed11cef8))

### Fix

* fix: bump sphinx-press-theme from 0.8.0 to 0.9.1 (#216)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`4da4b73`](https://github.com/supabase-community/storage-py/commit/4da4b735e28400967f9303df14c7936a988dcf97))

## v0.7.3 (2024-03-11)

### Chore

* chore: update CODEOWNERS to use python-maintainers (#204) ([`4dc6a5a`](https://github.com/supabase-community/storage-py/commit/4dc6a5a0944f540a394c4bdda6250d33c40a4758))

### Fix

* fix: add json decode error import (#205) ([`7327175`](https://github.com/supabase-community/storage-py/commit/732717510ed2aab7a2b131861b1a6b65fcb6a0dd))

## v0.7.2 (2024-03-10)

### Chore

* chore(deps-dev): bump black from 23.10.0 to 24.2.0 (#193)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`4613502`](https://github.com/supabase-community/storage-py/commit/46135021e8a0fcdc4d41c8465831092b13b9b326))

### Fix

* fix: add upsert option to upload/update (#199) ([`db1b66a`](https://github.com/supabase-community/storage-py/commit/db1b66a0f12795e6ed4be1f3adb5776c296f3ede))

## v0.7.1 (2024-03-10)

### Chore

* chore(deps-dev): bump pytest from 7.4.4 to 8.1.0 (#200)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`bcb0af7`](https://github.com/supabase-community/storage-py/commit/bcb0af74468868eb5610d4b2e83f248b8baf6a7c))

* chore(deps): bump python-semantic-release/python-semantic-release from 8.0.0 to 9.1.1 (#188)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`dd56b26`](https://github.com/supabase-community/storage-py/commit/dd56b26012c6d71a93895ada757f3c1d04e19618))

* chore(deps): bump sphinx-notes/pages from 2 to 3 (#198)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e592b7d`](https://github.com/supabase-community/storage-py/commit/e592b7dd80976cab138a9b27f45897e43cd07b06))

* chore(deps): bump codecov/codecov-action from 1 to 4 (#197)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`5928a4a`](https://github.com/supabase-community/storage-py/commit/5928a4a4aba43a892fb081c93f219fb5278b665b))

* chore(deps-dev): bump pre-commit from 3.4.0 to 3.5.0 (#156)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt;
Co-authored-by: Rodrigo Mansueli &lt;rodrigo@mansueli.com&gt; ([`331779f`](https://github.com/supabase-community/storage-py/commit/331779f2d3299d0561aba6db5421cfc233204899))

* chore(deps): bump github/codeql-action from 2 to 3 (#189)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`5db5fd2`](https://github.com/supabase-community/storage-py/commit/5db5fd29cf07fbc145a8e1a784959921a6eb1ba4))

* chore(deps): bump actions/setup-python from 2 to 5 (#190)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`6160615`](https://github.com/supabase-community/storage-py/commit/6160615201c9da59961e8d8016a4244dbe16f571))

* chore(deps): bump abatilo/actions-poetry from 2.2.0 to 3.0.0 (#186)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`1d02c5a`](https://github.com/supabase-community/storage-py/commit/1d02c5a66dde8cf91ef258e2a5db91c9af5eaca1))

* chore(deps): bump actions/checkout from 2 to 4 (#187)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`dd7e0a5`](https://github.com/supabase-community/storage-py/commit/dd7e0a5c7b4652efa85ab6ed76c24f266e4c0e06))

* chore(deps-dev): bump python-semantic-release from 8.1.1 to 9.1.1 (#191)

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`504c8b2`](https://github.com/supabase-community/storage-py/commit/504c8b2201c7463126722ec9bb68413165908a92))

### Fix

* fix: handle json decode error when there&#39;s no json response (e.g. on 403) (#203)

Co-authored-by: joel &lt;joel@joels-MacBook-Pro.local&gt; ([`cce5ad4`](https://github.com/supabase-community/storage-py/commit/cce5ad420fa01bc032f55822572aa9e9c0061be0))

### Unknown

* Update poetry.lock (#195) ([`641c24e`](https://github.com/supabase-community/storage-py/commit/641c24ee72865e27526a3e10891a437024b6e9ff))

* Merge branch &#39;main&#39; of https://github.com/supabase-community/storage-py ([`84e26e2`](https://github.com/supabase-community/storage-py/commit/84e26e28179aca2eacc180932e1f49e71d04f713))

* Update dependabot.yml (#185) ([`1f2c2f8`](https://github.com/supabase-community/storage-py/commit/1f2c2f8fdf9e1e1501985f27cddaf61595c8ff5b))

* Update poetry.lock ([`1e81c90`](https://github.com/supabase-community/storage-py/commit/1e81c90be16bcbc6f245fa7a9dfc06ded0932206))

* Update MAINTAINERS.md ([`d3f7e8c`](https://github.com/supabase-community/storage-py/commit/d3f7e8c334815c63a77496d6f4ffef36b729f082))

* Update MAINTAINERS.md (#175) ([`6816f0c`](https://github.com/supabase-community/storage-py/commit/6816f0cf36c5995fb6cbf6e5bf9ad0b16e801bf3))

## v0.7.0 (2023-11-22)

### Chore

* chore: update GitHub workflow for releases ([`72ad275`](https://github.com/supabase-community/storage-py/commit/72ad2752849621446fd1df7ebc0b85dc4d9cf4cd))

* chore: add sync version of the update function ([`18c14a4`](https://github.com/supabase-community/storage-py/commit/18c14a4e7888cd14d09b7cbbd2e8b02f9cef02f0))

* chore(deps-dev): bump urllib3 from 2.0.5 to 2.0.7

Bumps [urllib3](https://github.com/urllib3/urllib3) from 2.0.5 to 2.0.7.
- [Release notes](https://github.com/urllib3/urllib3/releases)
- [Changelog](https://github.com/urllib3/urllib3/blob/main/CHANGES.rst)
- [Commits](https://github.com/urllib3/urllib3/compare/v2.0.5...2.0.7)

---
updated-dependencies:
- dependency-name: urllib3
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`79c9ca3`](https://github.com/supabase-community/storage-py/commit/79c9ca3b23e13e7f1d3788edc99d5939f59d0960))

* chore(deps-dev): bump pytest from 7.4.2 to 7.4.3

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`87125bc`](https://github.com/supabase-community/storage-py/commit/87125bccaee9eeffd136af5ee8c442a4161b4761))

* chore(deps-dev): bump black from 23.9.1 to 23.10.0

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`ac6f901`](https://github.com/supabase-community/storage-py/commit/ac6f9017d8cde34b930b0436af5f413fc589b12f))

### Feature

* feat: add update existing file function ([`da4d785`](https://github.com/supabase-community/storage-py/commit/da4d785028e86899f1efc23394883836b94cd0d3))

### Unknown

* Merge pull request #166 from supabase-community/chore/update-gh-workflow

chore: update GitHub workflow for releases ([`f42d176`](https://github.com/supabase-community/storage-py/commit/f42d1766d4a8649a995ae474185eb50d0572bf2c))

* Merge pull request #165 from supabase-community/silentworks/file_update

feat: add update existing file function ([`d8139e0`](https://github.com/supabase-community/storage-py/commit/d8139e0e36f5d083262e61809e74313969de7996))

* Merge pull request #158 from supabase-community/dependabot/pip/urllib3-2.0.7

chore(deps-dev): bump urllib3 from 2.0.5 to 2.0.7 ([`fc8cb5d`](https://github.com/supabase-community/storage-py/commit/fc8cb5d60511d3e795614ff17facebe22b6f93f2))

* Merge pull request #162 from supabase-community/dependabot/pip/main/pytest-7.4.3

chore(deps-dev): bump pytest from 7.4.2 to 7.4.3 ([`9b048cb`](https://github.com/supabase-community/storage-py/commit/9b048cbb913b725f326e1c3e8eaa4b9377b6f1d6))

* Merge pull request #159 from supabase-community/dependabot/pip/main/black-23.10.0

chore(deps-dev): bump black from 23.9.1 to 23.10.0 ([`0f332fa`](https://github.com/supabase-community/storage-py/commit/0f332fa714636f343deb390ec58a288563fc81d2))

## v0.6.1 (2023-10-02)

### Documentation

* docs: fix name of URLOptions type ([`5430e92`](https://github.com/supabase-community/storage-py/commit/5430e920492e6616ce833318daef44176b282401))

### Fix

* fix: make precommit ignore markdown files ([`d2530fe`](https://github.com/supabase-community/storage-py/commit/d2530fe4b661e9b43dc6a0e124ac60ab3ffc64c9))

* fix: pass cache-control as formdata ([`9910fe0`](https://github.com/supabase-community/storage-py/commit/9910fe0d9e88c60798773d42a4449b1df62068ed))

* fix: use correct Any for typehint ([`5ad2ae8`](https://github.com/supabase-community/storage-py/commit/5ad2ae8ed67b6f8fe60ceff8ff6a85d92ac36725))

### Unknown

* Merge pull request #154 from supabase-community/fix/cache-control

fix: send cache-control as form data ([`bab90b6`](https://github.com/supabase-community/storage-py/commit/bab90b67f49631f7a8b2f77998a205b9d9029926))

## v0.6.0 (2023-09-28)

### Chore

* chore: run unasync ([`fc93662`](https://github.com/supabase-community/storage-py/commit/fc936629932271b12bb741b87140744c83d2369b))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`08ea297`](https://github.com/supabase-community/storage-py/commit/08ea297ef0982c70444b0aab8da4072710e7458f))

### Feature

* feat: bump version ([`10ba8be`](https://github.com/supabase-community/storage-py/commit/10ba8be2e1ef45cfc3a596a88e9a674fe5308b0b))

### Fix

* fix: make download key optional ([`dbf8213`](https://github.com/supabase-community/storage-py/commit/dbf82137eb3c18b8892bf1853072f9e82dd0d57b))

### Unknown

* Merge pull request #153 from supabase-community/fix/remove-required-key

fix: make download key optional ([`d0c47c7`](https://github.com/supabase-community/storage-py/commit/d0c47c7dc72864c7e256f27d5d68ccebaff2c18a))

* Merge pull request #152 from supabase-community/j0/test_workflow

feat: bump version ([`9b227ce`](https://github.com/supabase-community/storage-py/commit/9b227ce01b18093ee4967d4eaf249f43c7a22f60))

* Merge pull request #151 from supabase-community/fix/github-workflow-update

Update python-semantic-release version and ci ([`bf49d51`](https://github.com/supabase-community/storage-py/commit/bf49d514390b86670b61ce2b5cd2b7fd8a92d6c3))

* Update python-semantic-release version and ci ([`ad7fc6d`](https://github.com/supabase-community/storage-py/commit/ad7fc6dab3a5be062598e64f4b287370eafcacd5))

* Merge pull request #150 from supabase-community/fix/github-workflow

Fix semantic releaase workflow ([`e13cb9e`](https://github.com/supabase-community/storage-py/commit/e13cb9e5cbc735635d70a8d6f8c3df5b39eb739b))

* Fix semantic releaase workflow ([`3a00104`](https://github.com/supabase-community/storage-py/commit/3a00104fe5206bb48db9e440d8abfe503a6b505f))

* Merge pull request #149 from supabase-community/fix/correct-option-type-for-transforms

Fix image transforms options ([`64a8ab2`](https://github.com/supabase-community/storage-py/commit/64a8ab21713d3b80c647ab54ef78f553744d5ad8))

* Ran pre-commit hooks ([`f8f7482`](https://github.com/supabase-community/storage-py/commit/f8f7482de2088a5539b3c68f53e4c76578c58a70))

* Rename options typehint
Add download option to get_public_url ([`4fc7d8d`](https://github.com/supabase-community/storage-py/commit/4fc7d8d9b6dfcfc8068834cfed1fdd5691ae38fc))

* Fix image transforms options ([`f007596`](https://github.com/supabase-community/storage-py/commit/f007596743ce18647cca782f7765716d4779f3a8))

* Merge pull request #136 from supabase-community/dependabot/pip/main/pytest-7.4.2

chore(deps-dev): bump pytest from 7.4.0 to 7.4.2 ([`7229864`](https://github.com/supabase-community/storage-py/commit/72298641ef1e15e54b897e9ff7ccdffffce511f5))

## v0.5.5 (2023-09-15)

### Chore

* chore: run black ([`14be266`](https://github.com/supabase-community/storage-py/commit/14be2669e381e3bd3fd3a2b73f8a76a3294f33b1))

* chore: create CODEOWNERS ([`8077001`](https://github.com/supabase-community/storage-py/commit/8077001711360c1d7ff2084089ee7eff1b1c99f4))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`e789223`](https://github.com/supabase-community/storage-py/commit/e78922316e4189e19ff3a9d8c3ee38644014c42f))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`0497ef2`](https://github.com/supabase-community/storage-py/commit/0497ef221bb7382170e4f8267f5ea1f768c5619f))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`11b2d5a`](https://github.com/supabase-community/storage-py/commit/11b2d5a382d89b850cf6692fd11563422c307321))

* chore(deps-dev): bump python-semantic-release from 8.0.4 to 8.0.8

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 8.0.4 to 8.0.8.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v8.0.4...v8.0.8)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`0de10b2`](https://github.com/supabase-community/storage-py/commit/0de10b2d39ed455114c8e049df973477f09d135c))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`801681c`](https://github.com/supabase-community/storage-py/commit/801681c7c4458143e3e9ef23140456608fe09d5c))

### Fix

* fix: run unasync and also patch type ([`98aae1c`](https://github.com/supabase-community/storage-py/commit/98aae1c7b8ebb383ab005fbaf4c70f8b388bca9e))

### Unknown

* Merge pull request #143 from supabase-community/j0/patch_remove_type

fix: patch type on remove ([`8dbd29a`](https://github.com/supabase-community/storage-py/commit/8dbd29aef0f9e5b74724f6405d325413c02247cb))

* Merge pull request #142 from supabase-community/j0/add_semver

feat:add semver ([`eaf869a`](https://github.com/supabase-community/storage-py/commit/eaf869a1f03efb9b3f6d0feb1b07b35117581ede))

* Update pyproject.toml ([`b3abdb7`](https://github.com/supabase-community/storage-py/commit/b3abdb79ee28eaeeb9fbff9f5464940f80c3bcdc))

* Update ci.yml

change ref to main ([`1ff3e20`](https://github.com/supabase-community/storage-py/commit/1ff3e20d7fb5c8fa21455e21fd388e66cb96b86c))

* feat:add semver ([`ff91715`](https://github.com/supabase-community/storage-py/commit/ff9171505b99573788879e86aeb897a8461c42ec))

* Merge pull request #141 from supabase-community/J0/add-codeowners

chore: create CODEOWNERS ([`e25c803`](https://github.com/supabase-community/storage-py/commit/e25c8031363cee2c6a62c673ee613329c8fd401f))

* Merge pull request #139 from supabase-community/dependabot/pip/main/black-23.9.1

chore(deps-dev): bump black from 23.7.0 to 23.9.1 ([`d8f6584`](https://github.com/supabase-community/storage-py/commit/d8f6584bcd7ae67606b286bdfd9ed9fdf9a6a63a))

* Merge pull request #140 from supabase-community/dependabot/pip/gitpython-3.1.35

chore(deps-dev): bump gitpython from 3.1.32 to 3.1.35 ([`b39d082`](https://github.com/supabase-community/storage-py/commit/b39d0821c18896aa750f2ae9db0324e0500d5b05))

* Merge pull request #134 from supabase-community/dependabot/pip/main/pre-commit-3.4.0

chore(deps-dev): bump pre-commit from 3.3.3 to 3.4.0 ([`1ae2b4d`](https://github.com/supabase-community/storage-py/commit/1ae2b4de3f2e7ff96c2adb2ccc9687ff3743eea2))

* Merge pull request #132 from supabase-community/dependabot/pip/main/python-semantic-release-8.0.8

chore(deps-dev): bump python-semantic-release from 8.0.4 to 8.0.8 ([`bf90db3`](https://github.com/supabase-community/storage-py/commit/bf90db3fd0eacf0219480e0db3db2fa1501e2c9c))

* Merge pull request #138 from supabase-community/dependabot/pip/main/httpx-0.25.0

chore(deps): bump httpx from 0.24.1 to 0.25.0 ([`f09b35d`](https://github.com/supabase-community/storage-py/commit/f09b35dd46181ec99fdefee3755b4cb0adcfa232))

## v0.5.4 (2023-08-04)

### Chore

* chore(deps-dev): bump python-semantic-release from 7.34.3 to 8.0.4

Bumps [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) from 7.34.3 to 8.0.4.
- [Release notes](https://github.com/python-semantic-release/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v7.34.3...v8.0.4)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`b99cd75`](https://github.com/supabase-community/storage-py/commit/b99cd754e1b7b30a1f1cc11e31b184cd0ad6401e))

* chore(deps-dev): bump sphinx from 7.1.1 to 7.1.2

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 7.1.1 to 7.1.2.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v7.1.1...v7.1.2)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`ec41599`](https://github.com/supabase-community/storage-py/commit/ec415999b10217bda5c1a00f32cd68adcecc6999))

* chore(deps): bump typing-extensions from 4.7.0 to 4.7.1

Bumps [typing-extensions](https://github.com/python/typing_extensions) from 4.7.0 to 4.7.1.
- [Release notes](https://github.com/python/typing_extensions/releases)
- [Changelog](https://github.com/python/typing_extensions/blob/main/CHANGELOG.md)
- [Commits](https://github.com/python/typing_extensions/compare/4.7.0...4.7.1)

---
updated-dependencies:
- dependency-name: typing-extensions
  dependency-type: direct:production
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`5c4a0e4`](https://github.com/supabase-community/storage-py/commit/5c4a0e4ffaece42cea4ab174751581759343e04e))

* chore(deps-dev): bump cryptography from 41.0.2 to 41.0.3

Bumps [cryptography](https://github.com/pyca/cryptography) from 41.0.2 to 41.0.3.
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/41.0.2...41.0.3)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`778deec`](https://github.com/supabase-community/storage-py/commit/778deecfe9da3e2834d22cfabdcdf77f0d84df14))

* chore: bump httpx to ^0.24 ([`cad86d0`](https://github.com/supabase-community/storage-py/commit/cad86d07783794d635261184a1c6ddba95f3341c))

### Feature

* feat: bump version ([`1496da0`](https://github.com/supabase-community/storage-py/commit/1496da08ab4f6ed83fd7b38646459f9d0c771508))

### Unknown

* Merge pull request #124 from supabase-community/dependabot/pip/main/python-semantic-release-8.0.4

chore(deps-dev): bump python-semantic-release from 7.34.3 to 8.0.4 ([`f9f0645`](https://github.com/supabase-community/storage-py/commit/f9f064576832654d7d47551ce953ef3ba7152d0c))

* Merge pull request #128 from supabase-community/dependabot/pip/main/sphinx-7.1.2

chore(deps-dev): bump sphinx from 7.1.1 to 7.1.2 ([`4bb4aa1`](https://github.com/supabase-community/storage-py/commit/4bb4aa173fd8d3afbda5d85e3d26d4f1592b2dfb))

* Merge pull request #114 from supabase-community/dependabot/pip/main/typing-extensions-4.7.1

chore(deps): bump typing-extensions from 4.7.0 to 4.7.1 ([`cc99771`](https://github.com/supabase-community/storage-py/commit/cc9977103c423f3f8acc4184c8398ba18b12a04a))

* Merge pull request #127 from supabase-community/dependabot/pip/cryptography-41.0.3

chore(deps-dev): bump cryptography from 41.0.2 to 41.0.3 ([`950da37`](https://github.com/supabase-community/storage-py/commit/950da37a23f82c220ef28067d9b5640524146216))

* Merge pull request #125 from supabase-community/bump-httpx

chore: bump httpx to ^0.24 ([`56a7594`](https://github.com/supabase-community/storage-py/commit/56a75941c7b1cc0427d67e9dc3c91b51937b4e40))

## v0.5.3 (2023-07-24)

### Chore

* chore: bump pyproject ([`2f2b3a6`](https://github.com/supabase-community/storage-py/commit/2f2b3a6f143826c8eb36c96ee679fa5c2adaec10))

* chore(deps-dev): bump pre-commit from 3.3.2 to 3.3.3

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 3.3.2 to 3.3.3.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v3.3.2...v3.3.3)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`5729d3c`](https://github.com/supabase-community/storage-py/commit/5729d3c1877b26ed044cd7ed6a60a91399700a70))

* chore(deps): bump typing-extensions from 4.6.3 to 4.7.0

Bumps [typing-extensions](https://github.com/python/typing_extensions) from 4.6.3 to 4.7.0.
- [Release notes](https://github.com/python/typing_extensions/releases)
- [Changelog](https://github.com/python/typing_extensions/blob/main/CHANGELOG.md)
- [Commits](https://github.com/python/typing_extensions/compare/4.6.3...4.7.0)

---
updated-dependencies:
- dependency-name: typing-extensions
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`a550c7d`](https://github.com/supabase-community/storage-py/commit/a550c7df410be594a0dc0b05fa0f588b4ae67900))

* chore(deps-dev): bump pytest from 7.3.2 to 7.4.0

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.3.2 to 7.4.0.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.3.2...7.4.0)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`c008911`](https://github.com/supabase-community/storage-py/commit/c0089114d945bd08c15d562aafb7b1dda56512b3))

* chore(deps-dev): bump pytest from 7.3.1 to 7.3.2 (#108)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 7.3.1 to 7.3.2.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/7.3.1...7.3.2)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e5df2ff`](https://github.com/supabase-community/storage-py/commit/e5df2ff8a269337d206b7396ebab04039eb1684e))

* chore: test upload_to_signed_url ([`82ccab4`](https://github.com/supabase-community/storage-py/commit/82ccab43c98ae55078ed5fab76d9c12320261235))

* chore: test create_signed_upload_url ([`c330397`](https://github.com/supabase-community/storage-py/commit/c330397e2657f5e9415c9c4959c07d769ff807a6))

* chore(deps-dev): bump pytest-asyncio from 0.20.3 to 0.21.0

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.20.3 to 0.21.0.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.20.3...v0.21.0)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`8b22943`](https://github.com/supabase-community/storage-py/commit/8b229435d96d9cc86df48a39746ff9e5286990fa))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`1eef352`](https://github.com/supabase-community/storage-py/commit/1eef352118ae685ad0682559a9ee57cfe2cfe5e1))

* chore: update dependencies (#101) ([`03c5b03`](https://github.com/supabase-community/storage-py/commit/03c5b0378d989384e3f2f6a5a7c2b588929dd321))

* chore(deps): bump httpx from 0.23.3 to 0.24.0

Bumps [httpx](https://github.com/encode/httpx) from 0.23.3 to 0.24.0.
- [Release notes](https://github.com/encode/httpx/releases)
- [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
- [Commits](https://github.com/encode/httpx/compare/0.23.3...0.24.0)

---
updated-dependencies:
- dependency-name: httpx
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`84335cd`](https://github.com/supabase-community/storage-py/commit/84335cd6f363496898b6a81f405c30d6e64092bb))

* chore(deps-dev): bump pytest from 7.2.2 to 7.3.1 (#88)

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a95a244`](https://github.com/supabase-community/storage-py/commit/a95a24410be08e9276f3e8214b621f6b82fd81ba))

* chore(deps-dev): bump pre-commit from 3.1.1 to 3.2.0 (#79)

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 3.1.1 to 3.2.0.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v3.1.1...v3.2.0)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`a603a2a`](https://github.com/supabase-community/storage-py/commit/a603a2a684cf6d47eb5b58866c8c8263cc909852))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`e764f25`](https://github.com/supabase-community/storage-py/commit/e764f2503d3ec256c1e4a1917a1fd5a8d7d8c427))

### Documentation

* docs: document all typed dicts ([`1489757`](https://github.com/supabase-community/storage-py/commit/1489757be0492daf9da680267b483cb175df6e68))

### Feature

* feat: add upload_to_signed_url ([`f756460`](https://github.com/supabase-community/storage-py/commit/f75646050e5694930e927d4ffce4b53da9a5b80c))

* feat: make create_signed_upload_url method ([`8343bde`](https://github.com/supabase-community/storage-py/commit/8343bde8f61fab5ed8bf5caf2d2dd876fd61ffd1))

* feat: created functions to get multiple signed URLs. (#105)

* feat: created functions to get multiple signed URLs.

* feat: Fixed optional params. Handling auth token issue #73 in separate PR.

* feat: remove sync code as it will be generated by unasync.

* chore: generate sync client

---------

Co-authored-by: Alexander Leonov &lt;alleonov@icloud.com&gt;
Co-authored-by: anand2312 &lt;40204976+anand2312@users.noreply.github.com&gt; ([`2c5e2fc`](https://github.com/supabase-community/storage-py/commit/2c5e2fc309ab0f862a21e52da9b0e7c2c9d24e19))

* feat: bucket level file controls and an update_bucket method (#103)

* feat: bucket level file controls and an update_bucket method

* fix: import __future__ annotations

python 3.8 doesn&#39;t allow subscripting types like list ([`80454f9`](https://github.com/supabase-community/storage-py/commit/80454f9f6de5d6d5db9840b848b39937fabf5407))

### Unknown

* Merge pull request #123 from supabase-community/j0/bump_storage_0_5_3

feat: bump version to 0.5.3 ([`f1df45f`](https://github.com/supabase-community/storage-py/commit/f1df45f4a9f0c72ab64e2f63a40a51bf56909b33))

* Merge pull request #109 from supabase-community/dependabot/pip/main/pre-commit-3.3.3

chore(deps-dev): bump pre-commit from 3.3.2 to 3.3.3 ([`2eb5ae8`](https://github.com/supabase-community/storage-py/commit/2eb5ae808409c43ea74e490bb682cb5e7e6e5f65))

* Merge pull request #113 from supabase-community/dependabot/pip/main/typing-extensions-4.7.0

chore(deps): bump typing-extensions from 4.6.3 to 4.7.0 ([`3a10bc6`](https://github.com/supabase-community/storage-py/commit/3a10bc618e19a7e710413779a2d0cc4dd1d98b79))

* Merge pull request #112 from supabase-community/dependabot/pip/main/pytest-7.4.0

chore(deps-dev): bump pytest from 7.3.2 to 7.4.0 ([`5cc339d`](https://github.com/supabase-community/storage-py/commit/5cc339d837ac9c0d69d66faab6db42f871b7881b))

* Merge pull request #107 from supabase-community/anand/sign-upload-urls

feat: methods for signed url uploads ([`d4757d2`](https://github.com/supabase-community/storage-py/commit/d4757d20194da4b80d5aaec4ab03a6537b694c57))

* Merge branch &#39;main&#39; into anand/sign-upload-urls ([`2b65b0e`](https://github.com/supabase-community/storage-py/commit/2b65b0ea2ef08bce48895a0263ac9c34551fbf01))

* Merge pull request #78 from supabase-community/dependabot/pip/main/pytest-asyncio-0.21.0

chore(deps-dev): bump pytest-asyncio from 0.20.3 to 0.21.0 ([`7e86450`](https://github.com/supabase-community/storage-py/commit/7e86450d61edf9cbfc849aedd4dbcb2c2229dfe7))

* Merge pull request #106 from supabase-community/J0/update-pre-commit-black

Update .pre-commit-config.yaml ([`27b765c`](https://github.com/supabase-community/storage-py/commit/27b765c2913ca8f0e5d5a1759986f4d0d0566bf9))

* Update .pre-commit-config.yaml ([`a6dca37`](https://github.com/supabase-community/storage-py/commit/a6dca37629f2aef2527a9156fd579f337f45fa13))

* Merge pull request #102 from supabase-community/dependabot/pip/main/httpx-0.24.1

chore(deps): bump httpx from 0.23.3 to 0.24.1 ([`fc18260`](https://github.com/supabase-community/storage-py/commit/fc18260c959323b1a4721d3187febff42020321b))

* Make FileOptions type (#100)

* Update lockfile

* feat: add FileOptions type, make some bucket fields optional

* feat: use FileOptions in upload and document it

* docs: add upload example to README

* fix: don&#39;t mark BaseBucket fields as default

this breaks every other class that inherits from BaseBucket and tries to add
any non-default field. ([`1585e42`](https://github.com/supabase-community/storage-py/commit/1585e4279427934d5e027fc3ea2874085748caa6))

* Merge pull request #87 from supabase-community/dependabot/pip/main/httpx-0.24.0

chore(deps): bump httpx from 0.23.3 to 0.24.0 ([`b69a8ba`](https://github.com/supabase-community/storage-py/commit/b69a8bac00c4a4c05ab224b34fd99a21a712b256))

* Merge branch &#39;main&#39; into dependabot/pip/main/httpx-0.24.0 ([`c1b64e1`](https://github.com/supabase-community/storage-py/commit/c1b64e105e06f146499ef7503a958e4f143cd4ed))

* Fix bad typing on upload functions (#89)

* Fix bad typing on upload functions

* Format using black ([`40fc84b`](https://github.com/supabase-community/storage-py/commit/40fc84b7784b37b9da24c09d2eba2d282603c4fb))

* Merge pull request #76 from supabase-community/dependabot/pip/main/pytest-7.2.2

chore(deps-dev): bump pytest from 7.2.1 to 7.2.2 ([`eef5524`](https://github.com/supabase-community/storage-py/commit/eef55243385d80905d0186b58bcede2092b6c7e4))

## v0.5.2 (2023-03-05)

### Chore

* chore: bump version ([`91c4456`](https://github.com/supabase-community/storage-py/commit/91c4456b55113347d4da2dc26ee3a08dd893ea0e))

* chore(deps): bump typing-extensions from 4.4.0 to 4.5.0

Bumps [typing-extensions](https://github.com/python/typing_extensions) from 4.4.0 to 4.5.0.
- [Release notes](https://github.com/python/typing_extensions/releases)
- [Changelog](https://github.com/python/typing_extensions/blob/main/CHANGELOG.md)
- [Commits](https://github.com/python/typing_extensions/compare/4.4.0...4.5.0)

---
updated-dependencies:
- dependency-name: typing-extensions
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`daaf68d`](https://github.com/supabase-community/storage-py/commit/daaf68d2eb4833bc2b8afb459688dcf4c7be5343))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`698672c`](https://github.com/supabase-community/storage-py/commit/698672c533cc595f1c1e54b1e230e85bed4fb274))

* chore(deps-dev): bump python-dotenv from 0.21.1 to 1.0.0

Bumps [python-dotenv](https://github.com/theskumar/python-dotenv) from 0.21.1 to 1.0.0.
- [Release notes](https://github.com/theskumar/python-dotenv/releases)
- [Changelog](https://github.com/theskumar/python-dotenv/blob/main/CHANGELOG.md)
- [Commits](https://github.com/theskumar/python-dotenv/compare/v0.21.1...v1.0.0)

---
updated-dependencies:
- dependency-name: python-dotenv
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`192120c`](https://github.com/supabase-community/storage-py/commit/192120c6c332b06f426289dee4980cd1bed441cb))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`af38774`](https://github.com/supabase-community/storage-py/commit/af387746d0d18723afbe92595a0f47b285120d92))

* chore(deps-dev): bump pre-commit from 2.21.0 to 3.1.1

Bumps [pre-commit](https://github.com/pre-commit/pre-commit) from 2.21.0 to 3.1.1.
- [Release notes](https://github.com/pre-commit/pre-commit/releases)
- [Changelog](https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md)
- [Commits](https://github.com/pre-commit/pre-commit/compare/v2.21.0...v3.1.1)

---
updated-dependencies:
- dependency-name: pre-commit
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`ec3b46c`](https://github.com/supabase-community/storage-py/commit/ec3b46c43f88cd388ce22fc1dc62e6d75a39bb61))

* chore: bump version, bump CI ([`0679ae9`](https://github.com/supabase-community/storage-py/commit/0679ae9318a54b23e723fe0ccc989cf06020c5d9))

* chore: run black ([`2edbd6b`](https://github.com/supabase-community/storage-py/commit/2edbd6b74e1cd784b5ef4b39ffdce6e47e5e5e64))

* chore(deps-dev): bump sphinx from 5.3.0 to 6.1.3

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 5.3.0 to 6.1.3.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v5.3.0...v6.1.3)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`881fd9d`](https://github.com/supabase-community/storage-py/commit/881fd9d6dc4a576fea5a682e54804912d55781a4))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`1b3a638`](https://github.com/supabase-community/storage-py/commit/1b3a638857728a0e1c7854f615a3ab2c89b16c3d))

* chore(deps-dev): bump isort from 5.11.5 to 5.12.0

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`96ad75f`](https://github.com/supabase-community/storage-py/commit/96ad75f0decbb48af846561b356a9fe4a634971e))

### Fix

* fix: bump timeout ([`15f1547`](https://github.com/supabase-community/storage-py/commit/15f154789c329916b292d5504ad60b37f8b57ff2))

* fix: move timeout to constants file ([`873037a`](https://github.com/supabase-community/storage-py/commit/873037a51144685be76619eb151b917e8b0b8fdc))

* fix: add configurable timeout ([`281fbe7`](https://github.com/supabase-community/storage-py/commit/281fbe7e298aed67cd133c3a51265b356481b120))

### Unknown

* Merge pull request #75 from supabase-community/0.5.6

chore: bump version to 0.5.2 ([`d584b04`](https://github.com/supabase-community/storage-py/commit/d584b044149be643a53b6d10c9347800bb8d8cf8))

* Merge pull request #64 from supabase-community/dependabot/pip/main/typing-extensions-4.5.0

chore(deps): bump typing-extensions from 4.4.0 to 4.5.0 ([`7cb23a2`](https://github.com/supabase-community/storage-py/commit/7cb23a25017ce8b2adbd775750f8a604437168c4))

* Merge pull request #65 from supabase-community/dependabot/pip/main/python-semantic-release-7.33.2

chore(deps-dev): bump python-semantic-release from 7.33.1 to 7.33.2 ([`547e23b`](https://github.com/supabase-community/storage-py/commit/547e23b590fcee173c5e2429a04cee3f5183f0a9))

* Merge pull request #69 from supabase-community/dependabot/pip/main/python-dotenv-1.0.0

chore(deps-dev): bump python-dotenv from 0.21.1 to 1.0.0 ([`49a7044`](https://github.com/supabase-community/storage-py/commit/49a7044764ce56502a0aaa5b3aaa2b6250a1fd84))

* Merge pull request #72 from ChartierLuc/bug-missing-types

fix: added missing types ([`ed0dd37`](https://github.com/supabase-community/storage-py/commit/ed0dd37622ac3d516680d3a4b099c4e113da300b))

* Added missing types allowed_mime_types and file_size_limit ([`64e9e02`](https://github.com/supabase-community/storage-py/commit/64e9e02e8bea3e2b35ca37ed5d14c1197690accc))

* Merge pull request #56 from supabase-community/dependabot/pip/main/black-23.1.0

chore(deps-dev): bump black from 22.12.0 to 23.1.0 ([`7edeff7`](https://github.com/supabase-community/storage-py/commit/7edeff7135e9f3eb35d6016a3eb9ccbbf1351940))

* Merge pull request #74 from supabase-community/dependabot/pip/main/pre-commit-3.1.1

chore(deps-dev): bump pre-commit from 2.21.0 to 3.1.1 ([`0123f8f`](https://github.com/supabase-community/storage-py/commit/0123f8ff1708a8d13e9b436c1af376ab4c71be95))

* Merge pull request #68 from supabase-community/j0/bump_version_0_5_1

chore: bump version to 0_5_1 , bump CI ([`ae9fc30`](https://github.com/supabase-community/storage-py/commit/ae9fc30c4ed65ea27ad824560c3bd1e0cf20118a))

* Merge pull request #66 from supabase-community/j0/add_timeout

fix: add configurable timeout ([`436121f`](https://github.com/supabase-community/storage-py/commit/436121ff23ff128a921f39739dae01b48b328b03))

* Merge pull request #61 from supabase-community/dependabot/pip/main/sphinx-6.1.3

chore(deps-dev): bump sphinx from 5.3.0 to 6.1.3 ([`afb57e7`](https://github.com/supabase-community/storage-py/commit/afb57e70b48fd3161e51ee1c903a4e416583cb60))

* Merge pull request #62 from supabase-community/dependabot/pip/cryptography-39.0.1

chore(deps): bump cryptography from 39.0.0 to 39.0.1 ([`728164b`](https://github.com/supabase-community/storage-py/commit/728164bfa24bef89341f57008f89995e063abea0))

* Merge pull request #60 from supabase-community/dependabot/pip/main/isort-5.12.0

chore(deps-dev): bump isort from 5.11.5 to 5.12.0 ([`eb5be13`](https://github.com/supabase-community/storage-py/commit/eb5be13152e2dcc5d402b2bff1ac5d2e0fb9cde5))

## v0.5.0 (2023-02-05)

### Chore

* chore: bump pre commit ([`25dd2cc`](https://github.com/supabase-community/storage-py/commit/25dd2cc99b5394fae189dd784fd3bc24223b01a0))

* chore: bump version and lockfile ([`f5a20db`](https://github.com/supabase-community/storage-py/commit/f5a20dbae42fb2e6d53816141fc77408d576990d))

* chore(deps-dev): bump python-semantic-release from 7.32.2 to 7.33.1

Bumps [python-semantic-release](https://github.com/relekang/python-semantic-release) from 7.32.2 to 7.33.1.
- [Release notes](https://github.com/relekang/python-semantic-release/releases)
- [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.md)
- [Commits](https://github.com/relekang/python-semantic-release/compare/v7.32.2...v7.33.1)

---
updated-dependencies:
- dependency-name: python-semantic-release
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`5bdb51d`](https://github.com/supabase-community/storage-py/commit/5bdb51dc86f8ec1529e3cb7bb8470e8a56f37e6c))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`ef2e864`](https://github.com/supabase-community/storage-py/commit/ef2e86407027ada25dc361aa7388366baebca38f))

### Fix

* fix: bump python version ([`4d3a781`](https://github.com/supabase-community/storage-py/commit/4d3a7817ae3fb3ee4f93942406d8cfeb81103c88))

* fix: bump poetry version in ci ([`54110c4`](https://github.com/supabase-community/storage-py/commit/54110c4625c95e36461fb56e28287a97db7b02b7))

### Unknown

* Merge pull request #58 from supabase-community/j0/bump_version

chore: bump version and lockfile ([`3f44586`](https://github.com/supabase-community/storage-py/commit/3f4458680d8bac625edca18a249032b66533c06b))

* Merge pull request #57 from supabase-community/dependabot/pip/main/python-semantic-release-7.33.1

chore(deps-dev): bump python-semantic-release from 7.32.2 to 7.33.1 ([`06fb6f5`](https://github.com/supabase-community/storage-py/commit/06fb6f5686e90252828e28ea8d417f4c0c3e9599))

* Merge pull request #42 from supabase-community/dependabot/pip/wheel-0.38.1

chore(deps): bump wheel from 0.37.1 to 0.38.1 ([`f39c4fc`](https://github.com/supabase-community/storage-py/commit/f39c4fc66ab457ece68bc0a818d486e7ac775e10))

## v0.4.0 (2023-01-10)

### Chore

* chore: run black ([`3e985a9`](https://github.com/supabase-community/storage-py/commit/3e985a9e6b4305af0ec93c58c9af304c639b6df0))

* chore: set TransformOptions to None ([`ef32ae7`](https://github.com/supabase-community/storage-py/commit/ef32ae7e5137c54c8ea35ad3b8c2f2b965a8aecd))

* chore: port over infra from storage-js ([`88eb335`](https://github.com/supabase-community/storage-py/commit/88eb33532ff4ba04db740fc868d7ceed9bc0e18f))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`1708708`](https://github.com/supabase-community/storage-py/commit/1708708787c3344ed917ddd270ce7f105d9335f4))

* chore(deps): bump gitpython from 3.1.28 to 3.1.30

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.28 to 3.1.30.
- [Release notes](https://github.com/gitpython-developers/GitPython/releases)
- [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES)
- [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.28...3.1.30)

---
updated-dependencies:
- dependency-name: gitpython
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`84f48ed`](https://github.com/supabase-community/storage-py/commit/84f48ed47677868963be817c29753902975ef8fe))

### Feature

* feat: add transform options to signed_url,download, and public_url ([`122b2a3`](https://github.com/supabase-community/storage-py/commit/122b2a3403dfa1fa33dd384b2a7c42e9f3094f9e))

* feat: add copy and transform option type ([`6be51ee`](https://github.com/supabase-community/storage-py/commit/6be51ee4a5bedabce6a25d05b9a38ae65f40efef))

### Fix

* fix: add stray / ([`27b6bcd`](https://github.com/supabase-community/storage-py/commit/27b6bcd85866a152a1804679cb27f726a50d2bf3))

* fix: remove stray / ([`216cf36`](https://github.com/supabase-community/storage-py/commit/216cf3667479380fb893e16b4bd47d31f5a2b641))

* fix: update render_path for get_public_url ([`0272f1b`](https://github.com/supabase-community/storage-py/commit/0272f1b5dd787b8a51727c1c9de3116c15b124b6))

* fix: run black ([`42a9ed3`](https://github.com/supabase-community/storage-py/commit/42a9ed3f8f4e3d8e66f065f2ec64936a95b422b5))

* fix: handle stray / ([`dd72fd6`](https://github.com/supabase-community/storage-py/commit/dd72fd6758f975e8d1f1ba56765c21ac846cf62c))

* fix: handle stray / ([`604e804`](https://github.com/supabase-community/storage-py/commit/604e804e73583cd396829d41ecb8f3baf789f754))

* fix: remove query params ([`1feb825`](https://github.com/supabase-community/storage-py/commit/1feb82590a9f3ca025da41da82e8089f7835783f))

* fix: add query string param ([`72d299d`](https://github.com/supabase-community/storage-py/commit/72d299d4257265099e44c6b9e821fa3ca86d19ab))

* fix: strip out transformation changes ([`686b7fa`](https://github.com/supabase-community/storage-py/commit/686b7fa03007ee6dddc2bd96492a171bddf7de82))

* fix: remove stray $ ([`f0c8fdc`](https://github.com/supabase-community/storage-py/commit/f0c8fdcf69cd397e31c24091ae10550d65e0cb97))

* fix: switch from | to Union ([`f4005fd`](https://github.com/supabase-community/storage-py/commit/f4005fd672bc86bb694f2ddf50e202be7beb6370))

* fix: import Union, Optional from typing instead of typing-extensions ([`c5e5aba`](https://github.com/supabase-community/storage-py/commit/c5e5abaa8f7830cbfcd1caeafcd5d3c2140f2f0d))

* fix: omit infra changes ([`9b967ce`](https://github.com/supabase-community/storage-py/commit/9b967ce41d3598a68b08cbad45435a26fc0d5f0b))

* fix: add transform options on public url and download ([`7352f61`](https://github.com/supabase-community/storage-py/commit/7352f6128a1bd52e863dea0cf8db6f53519e6c78))

### Refactor

* refactor: remove create_signed_urls ([`b43434f`](https://github.com/supabase-community/storage-py/commit/b43434f6e947ce8a5251c042c19a90f8b6d86a6b))

### Unknown

* Merge pull request #49 from supabase-community/j0/add_transformation_bindings

feat: add transformation bindings ([`a501d41`](https://github.com/supabase-community/storage-py/commit/a501d4109d570297d4f6c18cce8ef96df6228b1b))

* add 3.11 ([`51de064`](https://github.com/supabase-community/storage-py/commit/51de0644cf3f2b72d88deb04951db4a8e7d0b80d))

* Merge pull request #41 from supabase-community/dependabot/pip/main/pre-commit-2.21.0

chore(deps-dev): bump pre-commit from 2.20.0 to 2.21.0 ([`68bcc7d`](https://github.com/supabase-community/storage-py/commit/68bcc7d073d7a27f45719a6fc7eecccbcf833163))

* Merge pull request #47 from supabase-community/dependabot/pip/gitpython-3.1.30

chore(deps): bump gitpython from 3.1.28 to 3.1.30 ([`8e0452a`](https://github.com/supabase-community/storage-py/commit/8e0452a1b39269514cf5e58dff545a29c783e890))

## v0.3.6 (2023-01-05)

### Chore

* chore(deps): bump httpx from 0.23.0 to 0.23.3

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`211dd3c`](https://github.com/supabase-community/storage-py/commit/211dd3cd7f22ec8172b31eb8c2557aaed7054a00))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`996d377`](https://github.com/supabase-community/storage-py/commit/996d37752cfc33b2c9d93666a7f6cc3ebc721c04))

* chore(deps-dev): bump pytest-asyncio from 0.20.1 to 0.20.3

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.20.1 to 0.20.3.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Changelog](https://github.com/pytest-dev/pytest-asyncio/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.20.1...v0.20.3)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-patch
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`3016a2b`](https://github.com/supabase-community/storage-py/commit/3016a2bd4d6a82c2af12a9a800acad0131ea21bf))

* chore(deps-dev): bump isort from 5.10.1 to 5.11.1

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`87f87f5`](https://github.com/supabase-community/storage-py/commit/87f87f5b15228b8fdc3859ec6d5ef809d5512336))

* chore(deps): bump cryptography from 38.0.1 to 38.0.3

Bumps [cryptography](https://github.com/pyca/cryptography) from 38.0.1 to 38.0.3.
- [Release notes](https://github.com/pyca/cryptography/releases)
- [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pyca/cryptography/compare/38.0.1...38.0.3)

---
updated-dependencies:
- dependency-name: cryptography
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`40ba3d6`](https://github.com/supabase-community/storage-py/commit/40ba3d6b622acb5ea8a593f7455acfbbd71efa69))

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`5c64886`](https://github.com/supabase-community/storage-py/commit/5c64886d092a83db2bf76ef7a4fb4b9b449622df))

* chore(deps): bump certifi from 2022.9.24 to 2022.12.7

Bumps [certifi](https://github.com/certifi/python-certifi) from 2022.9.24 to 2022.12.7.
- [Release notes](https://github.com/certifi/python-certifi/releases)
- [Commits](https://github.com/certifi/python-certifi/compare/2022.09.24...2022.12.07)

---
updated-dependencies:
- dependency-name: certifi
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`822d714`](https://github.com/supabase-community/storage-py/commit/822d71431c46f2b36a9704d43d616921a070eb81))

* chore(release): bump version to v0.3.5 ([`323e65e`](https://github.com/supabase-community/storage-py/commit/323e65e98a6101685b689f9f21c87b29a29a1f6c))

* chore(deps-dev): bump python-semantic-release from 7.32.1 to 7.32.2

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`68df5c2`](https://github.com/supabase-community/storage-py/commit/68df5c2f32264a4dd9d71256b0f510a2defa1379))

* chore(deps-dev): bump pytest-asyncio from 0.19.0 to 0.20.1 (#26)

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`999e8c9`](https://github.com/supabase-community/storage-py/commit/999e8c993822177d017ab3f7a69aea0209fefea2))

* chore(deps-dev): bump pytest from 6.2.5 to 7.2.0 (#28)

Bumps [pytest](https://github.com/pytest-dev/pytest) from 6.2.5 to 7.2.0.
- [Release notes](https://github.com/pytest-dev/pytest/releases)
- [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest/compare/6.2.5...7.2.0)

---
updated-dependencies:
- dependency-name: pytest
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`ed35024`](https://github.com/supabase-community/storage-py/commit/ed35024fea5f28fafd6e9b66e73b689e5a9f12f5))

* chore(deps-dev): bump pytest-cov from 3.0.0 to 4.0.0

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

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`d22118b`](https://github.com/supabase-community/storage-py/commit/d22118b7639d9bfef37a8de6bb6e80bcbcb33b85))

* chore(deps-dev): bump sphinx from 5.2.3 to 5.3.0 (#25)

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 5.2.3 to 5.3.0.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v5.2.3...v5.3.0)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9f7bc01`](https://github.com/supabase-community/storage-py/commit/9f7bc01b135fbdcb1f7767f426011c0630408712))

### Fix

* fix: remove trailing &#34;/&#34; in `get_public_url`

When using the `get_public_url` methods, you get the following
responses:

```
https://SUPABASE_ID.supabase.co/storage/v1//object/public/BUCKET/FILE
```

Notice the double slash between
the `v1` and the `object` substrings in the path.

Even though the URL works---as
captured by the tests--it is a non
coherent way of rendering the
URLs.

This commit sets it so that all the
sub-paths inside the public URL
have a single slash.

Authored-By: Diego Rodriguez ([`8bf407c`](https://github.com/supabase-community/storage-py/commit/8bf407c5fc2bca401a673d42d0f9a82b7b9e80bb))

* fix: datetime and upload file type (#12)

* [fix] datetime and upload file type

fix datetime error and add more acceptable file type

* [Fix] Add python-dateutil as dependency

* Fix lock file

* chore: reformat with black

* chore: calm isort down

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`a926a06`](https://github.com/supabase-community/storage-py/commit/a926a068234e68afbf8039fc7f71565397dfea86))

### Unknown

* Merge pull request #46 from supabase-community/dependabot/pip/main/httpx-0.23.3

chore(deps): bump httpx from 0.23.0 to 0.23.3 ([`a9f2def`](https://github.com/supabase-community/storage-py/commit/a9f2def2c25daa6e8f17eaa76c3194943293682b))

* Merge pull request #40 from supabase-community/dependabot/pip/main/isort-5.11.4

chore(deps-dev): bump isort from 5.11.1 to 5.11.4 ([`fd3c480`](https://github.com/supabase-community/storage-py/commit/fd3c4805928f30591058c028bf67a095ea2bcced))

* Merge pull request #32 from supabase-community/dependabot/pip/main/pytest-asyncio-0.20.3

chore(deps-dev): bump pytest-asyncio from 0.20.1 to 0.20.3 ([`57205b1`](https://github.com/supabase-community/storage-py/commit/57205b106a2254cef73e95c04f1b7fd3bcbb4c00))

* Merge pull request #37 from supabase-community/dependabot/pip/main/isort-5.11.1

chore(deps-dev): bump isort from 5.10.1 to 5.11.1 ([`514b2b4`](https://github.com/supabase-community/storage-py/commit/514b2b46b79d0dd018d5ca92956010bb2a3344a1))

* Create codeql.yml ([`993d162`](https://github.com/supabase-community/storage-py/commit/993d162d6770d195dcece59db7cde4a8ae54b359))

* Merge pull request #34 from supabase-community/dependabot/pip/cryptography-38.0.3

chore(deps): bump cryptography from 38.0.1 to 38.0.3 ([`7e4060a`](https://github.com/supabase-community/storage-py/commit/7e4060acf2cf436d020af2e5c46da1e9c428b9e2))

* Merge pull request #35 from supabase-community/dependabot/pip/main/black-22.12.0

chore(deps-dev): bump black from 22.10.0 to 22.12.0 ([`0020dc4`](https://github.com/supabase-community/storage-py/commit/0020dc49c15b1658ef72ea207bcabddfe08214af))

* Merge pull request #33 from supabase-community/dependabot/pip/certifi-2022.12.7

chore(deps): bump certifi from 2022.9.24 to 2022.12.7 ([`4682db1`](https://github.com/supabase-community/storage-py/commit/4682db1f9aacd90c13c07bf3685f30f368522739))

* Merge pull request #13 from asciidiego/diegonyc/fix/public_url_parsing

fix: remove leading &#34;/&#34; in `get_public_url` methods ([`ccd2316`](https://github.com/supabase-community/storage-py/commit/ccd2316f48a17d78d54577dd6add690137ec141a))

* Merge pull request #27 from supabase-community/dependabot/pip/main/python-semantic-release-7.32.2

chore(deps-dev): bump python-semantic-release from 7.32.1 to 7.32.2 ([`1f2a4b5`](https://github.com/supabase-community/storage-py/commit/1f2a4b589746130af1166de66d5281c3e3745a53))

* Merge pull request #23 from supabase-community/dependabot/pip/main/pytest-cov-4.0.0

chore(deps-dev): bump pytest-cov from 3.0.0 to 4.0.0 ([`67ad10c`](https://github.com/supabase-community/storage-py/commit/67ad10c92ef234db5551a2f3699e4be8f36fa15c))

## v0.3.5 (2022-10-11)

### Chore

* chore: bump version ([`15cbda8`](https://github.com/supabase-community/storage-py/commit/15cbda81b32d711b766cfc5e265c07dcb2835e9e))

* chore(deps-dev): bump sphinx from 4.5.0 to 5.2.3

Bumps [sphinx](https://github.com/sphinx-doc/sphinx) from 4.5.0 to 5.2.3.
- [Release notes](https://github.com/sphinx-doc/sphinx/releases)
- [Changelog](https://github.com/sphinx-doc/sphinx/blob/5.x/CHANGES)
- [Commits](https://github.com/sphinx-doc/sphinx/compare/v4.5.0...v5.2.3)

---
updated-dependencies:
- dependency-name: sphinx
  dependency-type: direct:development
  update-type: version-update:semver-major
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`7fe29fe`](https://github.com/supabase-community/storage-py/commit/7fe29fec1ec9467139b247c3040c2c760955ecba))

* chore(deps-dev): bump python-dotenv from 0.20.0 to 0.21.0

Bumps [python-dotenv](https://github.com/theskumar/python-dotenv) from 0.20.0 to 0.21.0.
- [Release notes](https://github.com/theskumar/python-dotenv/releases)
- [Changelog](https://github.com/theskumar/python-dotenv/blob/main/CHANGELOG.md)
- [Commits](https://github.com/theskumar/python-dotenv/compare/v0.20.0...v0.21.0)

---
updated-dependencies:
- dependency-name: python-dotenv
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`6f72dc2`](https://github.com/supabase-community/storage-py/commit/6f72dc267e74c1724ec06014616884cd7745f87b))

* chore(deps): bump typing-extensions from 4.2.0 to 4.4.0

Bumps [typing-extensions](https://github.com/python/typing_extensions) from 4.2.0 to 4.4.0.
- [Release notes](https://github.com/python/typing_extensions/releases)
- [Changelog](https://github.com/python/typing_extensions/blob/main/CHANGELOG.md)
- [Commits](https://github.com/python/typing_extensions/compare/4.2.0...4.4.0)

---
updated-dependencies:
- dependency-name: typing-extensions
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`0b82bb5`](https://github.com/supabase-community/storage-py/commit/0b82bb534e4461e163e9f78b8390d51a889eedf1))

* chore: update lock ([`f34e23e`](https://github.com/supabase-community/storage-py/commit/f34e23e750dd37267541d782daae1483187930e9))

* chore(deps-dev): bump pytest-asyncio from 0.18.3 to 0.19.0

Bumps [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) from 0.18.3 to 0.19.0.
- [Release notes](https://github.com/pytest-dev/pytest-asyncio/releases)
- [Changelog](https://github.com/pytest-dev/pytest-asyncio/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/pytest-dev/pytest-asyncio/compare/v0.18.3...v0.19.0)

---
updated-dependencies:
- dependency-name: pytest-asyncio
  dependency-type: direct:development
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`8de4e10`](https://github.com/supabase-community/storage-py/commit/8de4e10f3438503c9a263122981ccffbf34b9e9a))

### Unknown

* Merge pull request #22 from supabase-community/j0_bump_version

chore: bump storage version ([`8156aae`](https://github.com/supabase-community/storage-py/commit/8156aaec8d75c305c519607bf8f88d65dad3a0af))

* Merge pull request #15 from supabase-community/dependabot/pip/main/sphinx-5.2.3

chore(deps-dev): bump sphinx from 4.5.0 to 5.2.3 ([`727c123`](https://github.com/supabase-community/storage-py/commit/727c12306a24c5410570e8b98b905fb75886e8ae))

* Merge pull request #17 from supabase-community/dependabot/pip/main/python-dotenv-0.21.0

chore(deps-dev): bump python-dotenv from 0.20.0 to 0.21.0 ([`1e2558a`](https://github.com/supabase-community/storage-py/commit/1e2558a85de0b7e307ace3690344833fb71dc399))

* Merge pull request #18 from supabase-community/dependabot/pip/main/typing-extensions-4.4.0

chore(deps): bump typing-extensions from 4.2.0 to 4.4.0 ([`41eb45d`](https://github.com/supabase-community/storage-py/commit/41eb45d44322bd7d079629de8d8d3a04c4f1b43e))

* Merge pull request #21 from supabase-community/J0-bump-httpx

chore: bump httpx to 0.23 ([`517bd66`](https://github.com/supabase-community/storage-py/commit/517bd66cab5eb267e4140d77b36fecd89c4e106a))

* Update pyproject.toml ([`8bee432`](https://github.com/supabase-community/storage-py/commit/8bee43294530d2f5f54b1b9a32d112bc016cf478))

* Merge pull request #16 from supabase-community/dependabot/pip/main/pytest-asyncio-0.19.0

chore(deps-dev): bump pytest-asyncio from 0.18.3 to 0.19.0 ([`31d886c`](https://github.com/supabase-community/storage-py/commit/31d886cf50ba745deab7fc2352050bf6ab81d9e0))

* Update dependabot.yml ([`f6ef85e`](https://github.com/supabase-community/storage-py/commit/f6ef85e217d8f5d141a3fbc6879532e327e69a51))

* Justinbarak patch 1 (#14)

* Removed double &#34;/&#34; in get_public_url

* Removed double &#34;/&#34; in get_public_url ([`20de85e`](https://github.com/supabase-community/storage-py/commit/20de85e677e29cd17bb210a402be947f0ad98509))

## v0.3.4 (2022-06-07)

### Fix

* fix: signed_url

fix: signed_url ([`c8cdf44`](https://github.com/supabase-community/storage-py/commit/c8cdf444090e7d9c6cd68ac4f31afb52921c3ea5))

* fix: try no timeout as fix instead of sleep ([`68026be`](https://github.com/supabase-community/storage-py/commit/68026be058a5e5a0684d7bc174da674dfc6a137c))

* fix: signed_url ([`bd2e09c`](https://github.com/supabase-community/storage-py/commit/bd2e09c28164b364ca919fd888019e837af3890f))

## v0.3.3 (2022-06-06)

### Chore

* chore: build sync ([`1217cba`](https://github.com/supabase-community/storage-py/commit/1217cbac50186fefde73eb83337af9dfbf202d26))

### Fix

* fix: upload method

fix: upload fixes ([`844561f`](https://github.com/supabase-community/storage-py/commit/844561f63d58ad869a4303941e7ef8194ae89154))

* fix: use ** to merge dicts ([`2965ae7`](https://github.com/supabase-community/storage-py/commit/2965ae79857fd3b264384b0fbe8c7172744a9f12))

* fix: poetry lock ([`4d2a73f`](https://github.com/supabase-community/storage-py/commit/4d2a73f7f8170ddeac5ef154fd3c14c7b7bfec71))

### Style

* style: apply pre-commit ([`3b9a3b3`](https://github.com/supabase-community/storage-py/commit/3b9a3b38d553bd505bf077f07dcca18f5cfd72b4))

* style: use lowercase headers ([`66f088e`](https://github.com/supabase-community/storage-py/commit/66f088e8a28122b7085187c3e7c0c45e1ef68b30))

### Test

* test: sleep before download ([`1d3959c`](https://github.com/supabase-community/storage-py/commit/1d3959c554f9547b941e1db4ec7373715f8ce38c))

* test: fix tests to check file content ([`7995837`](https://github.com/supabase-community/storage-py/commit/7995837647a3dded939698405aa79d2dc181b299))

## v0.3.2 (2022-05-16)

### Ci

* ci: add deploy docs action ([`a4cbacf`](https://github.com/supabase-community/storage-py/commit/a4cbacf17260bb434bc8d42cc7e142e9621e3cc7))

### Fix

* fix: don&#39;t create virtualenv in CI (#7) ([`2a85860`](https://github.com/supabase-community/storage-py/commit/2a8586082ff667c7b525bccf01df2c0e890f2b66))

### Unknown

* Docs (#6)

* docs: setup

* docs: write basic documentation

* chore: fix lock file

* chore: calm pre-commit down ([`0974414`](https://github.com/supabase-community/storage-py/commit/0974414707f3e97fc8e44197d1f59a5699a0b582))

## v0.3.1 (2022-05-01)

### Fix

* fix: parity with js ([`19f1816`](https://github.com/supabase-community/storage-py/commit/19f1816d23671d576ddf23feab401d51aaf7b3e4))

## v0.3.0 (2022-04-30)

### Chore

* chore: force release of 0.3.0 ([`5793136`](https://github.com/supabase-community/storage-py/commit/57931368c1800275b84326a7b0b3277c693c114d))

* chore(deps): add typing_extensions ([`f541599`](https://github.com/supabase-community/storage-py/commit/f5415994ca8076a70942a8ed13c600b002e175f7))

* chore: setup ci versioning and publishing ([`a4c1d0b`](https://github.com/supabase-community/storage-py/commit/a4c1d0bced258b3f65e4c9880b196e8d81e8d38d))

* chore: update README ([`8e1f2e3`](https://github.com/supabase-community/storage-py/commit/8e1f2e395b45121e544341e52dc0202c0e78aef4))

* chore: downgrade poetry back to 1.1.11 ([`1daf996`](https://github.com/supabase-community/storage-py/commit/1daf996dd01e39d473d6cc07bebe0d32607da8ac))

* chore(debug end): add tests_only to tests in makefile ([`b9a7dbd`](https://github.com/supabase-community/storage-py/commit/b9a7dbdbd73b51e11f33a3eb9aaae0f69a36420b))

* chore(debug): bump poetry version in ci ([`0d8cf48`](https://github.com/supabase-community/storage-py/commit/0d8cf4877f199bdbe9ef03b4d992659d664264b2))

* chore(debug): remove tests_only from tests ([`c8cbde7`](https://github.com/supabase-community/storage-py/commit/c8cbde711a490c266c91d482435a3e5a038e6f88))

* chore(debug): remove install from tests ([`320739d`](https://github.com/supabase-community/storage-py/commit/320739dbfb17411c90245dc1b37308b3c064b713))

* chore: build sync ([`ae05a5a`](https://github.com/supabase-community/storage-py/commit/ae05a5a8c4fedf63e7668ac3bd0b0cd40e1a185c))

* chore(deps): fix lock ([`2bb8ddc`](https://github.com/supabase-community/storage-py/commit/2bb8ddc96f3106c011958107b0e53f0af31ca67e))

* chore: rm type annotation ([`88457fa`](https://github.com/supabase-community/storage-py/commit/88457fa85246e37c7defe01b6397a14970fbf964))

* chore: add pytest-asyncio dependency ([`6a90169`](https://github.com/supabase-community/storage-py/commit/6a90169fe0f927d2c0b073809dbd6ad4b9b59b67))

### Ci

* ci: add preview to poetry install in semantic-release ([`0fad863`](https://github.com/supabase-community/storage-py/commit/0fad863434e7b6e5a51bb3cd3836acad4504f727))

* ci: uncomment publish to pypi ([`aa6adaf`](https://github.com/supabase-community/storage-py/commit/aa6adaf4858087b041933619ccd93593c9251d28))

* ci(fix): bump poetry version again ([`1b9a455`](https://github.com/supabase-community/storage-py/commit/1b9a455ab6b69a910a74de04280e879afea9e177))

### Feature

* feat: force version bump ([`62556c0`](https://github.com/supabase-community/storage-py/commit/62556c00a064c691df90be6f8c8a46cc1b772ba4))

* feat: ignore unused imports in certain files ([`efebefe`](https://github.com/supabase-community/storage-py/commit/efebefed65a3adfa23ef4142600215bd1e6cff01))

* feat: add context manager ([`ec61c29`](https://github.com/supabase-community/storage-py/commit/ec61c29f72a1dae1148dbd15ab5cdad61eac835c))

* feat: add build_sync to makefile ([`b0a8665`](https://github.com/supabase-community/storage-py/commit/b0a86658678ce98a977cf67c07f07847003dcccf))

* feat: add statusCode to exception ([`6923975`](https://github.com/supabase-community/storage-py/commit/692397503f4a475168b92a8d5d8cda7719d2bf65))

* feat: add key to clients ([`838af7c`](https://github.com/supabase-community/storage-py/commit/838af7c0aded3c2e20df2ddd8e665da33d65106d))

### Fix

* fix(3.7 comp): import TypedDict from typing_extensions ([`dca5d6f`](https://github.com/supabase-community/storage-py/commit/dca5d6f716eb9624c4242a04e41e7b43f4e60ec6))

* fix: add AsyncClient ([`9522298`](https://github.com/supabase-community/storage-py/commit/9522298b9cb63531802984844287e7da3c996a93))

* fix: add storage to url ([`a33f9a3`](https://github.com/supabase-community/storage-py/commit/a33f9a398e43ef49d499b0685ff2557ca386c4fc))

* fix: async fixes ([`061cb15`](https://github.com/supabase-community/storage-py/commit/061cb15c4800117b71c4f3c50e3e1b9bd5989e7c))

* fix: typing.literal compatible w py3.7 ([`fcc21f1`](https://github.com/supabase-community/storage-py/commit/fcc21f16181a2127255edcf628e9f467a09874ca))

### Refactor

* refactor: no need to remerge client headers ([`cef322e`](https://github.com/supabase-community/storage-py/commit/cef322e8fa3e17ec18399dbcae65daf2262acc02))

* refactor: use session to get url and headers ([`b3f049f`](https://github.com/supabase-community/storage-py/commit/b3f049f0332f678e4af4ae95e2e855cefe90c1e8))

### Style

* style: add keyword arguments ([`8fa1279`](https://github.com/supabase-community/storage-py/commit/8fa12796929ee791a7978358ec2ff78dccb9b68d))

* style: sort imports ([`6d709b4`](https://github.com/supabase-community/storage-py/commit/6d709b4c8c8d3a920b60874288ed1b96f9610a2c))

* style: apply ([`688cfc7`](https://github.com/supabase-community/storage-py/commit/688cfc79b870df84ea2c85a1dae50f364799c258))

* style: fix ([`ab7275f`](https://github.com/supabase-community/storage-py/commit/ab7275ffd91564333fed58b5cc6ceb5b78da4d84))

### Test

* test: adapt tests to context manager ([`fd9bc86`](https://github.com/supabase-community/storage-py/commit/fd9bc86fe9f04cbe3d4c76e5b27cd8cbd1b1b750))

* test: add tests ([`488e538`](https://github.com/supabase-community/storage-py/commit/488e538fc637a1f6c433f31b1cf076204540cd51))

### Unknown

* Merge pull request #5 from supabase-community/fix-py3.7

Setup CD versioning and publishing with semantic release ([`9e840bc`](https://github.com/supabase-community/storage-py/commit/9e840bcdaabfc6161c9a15d5ac3bce3ba361012c))

* Merge pull request #4 from supabase-community/fix-py3.7

feat: python 3.7 compatibility and tests ([`5a8a1b4`](https://github.com/supabase-community/storage-py/commit/5a8a1b4be5e8dd6d49b6dc3ad642d8e7fe05fa3d))

* Update storage3/_async/file_api.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`db49eb9`](https://github.com/supabase-community/storage-py/commit/db49eb9bfb5be369a88ab218583c4e5bb67a4130))

* Update storage3/_async/file_api.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`3550527`](https://github.com/supabase-community/storage-py/commit/3550527710cd335c7eb392371eb9972dffcd0733))

* Update storage3/_async/file_api.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`034a218`](https://github.com/supabase-community/storage-py/commit/034a218aac85a419d2c7849dc7e1a5d91fd5eb89))

* Update storage3/_async/file_api.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`637182d`](https://github.com/supabase-community/storage-py/commit/637182d7bf92178777408af72269a82cd1d93983))

* Update storage3/_async/file_api.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`2d34986`](https://github.com/supabase-community/storage-py/commit/2d34986b605a4907ff1c78ed24b4e76b8d95a991))

* Update storage3/_async/file_api.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`07f67dd`](https://github.com/supabase-community/storage-py/commit/07f67ddbb90d9073aa9c6f6e7beff4d0fcf3b855))

* Update storage3/_async/file_api.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`13445f7`](https://github.com/supabase-community/storage-py/commit/13445f78ae3edf317dd4f84e6937e4c332ec4391))

* Update storage3/_async/bucket.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`d1cef58`](https://github.com/supabase-community/storage-py/commit/d1cef58304e6aa9981c2e36e54f85398450fc928))

* Update storage3/_async/bucket.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`26fa8b2`](https://github.com/supabase-community/storage-py/commit/26fa8b2988e2a57ba3183b9772775b8e834d959a))

* Update storage3/_async/bucket.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`20b47bb`](https://github.com/supabase-community/storage-py/commit/20b47bbce4068da381684654f8cecaef2ffe200b))

* Update storage3/_async/bucket.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`91a8ff7`](https://github.com/supabase-community/storage-py/commit/91a8ff7f2882746e90d85c6d292f764ad5c60fcf))

* Update storage3/_async/bucket.py

Co-authored-by: Anand &lt;40204976+anand2312@users.noreply.github.com&gt; ([`734e973`](https://github.com/supabase-community/storage-py/commit/734e9737e1337d5feecffb4789342fb44a0dcfce))

* refactor:export env variables to file ([`a9b8faf`](https://github.com/supabase-community/storage-py/commit/a9b8faf028aad56ea5caf598d983654cb8d713e0))

## v0.2.0 (2022-04-11)

### Chore

* chore: add usage instructions ([`1ab2974`](https://github.com/supabase-community/storage-py/commit/1ab29746e300e4977e50721168d33f3b42d4772a))

* chore: update versions and publish to PyPI ([`7c754cf`](https://github.com/supabase-community/storage-py/commit/7c754cfe4397ff75cd693ab38d4b37fb2e1dc3f5))

* chore: rename storage to storage3 ([`c62151c`](https://github.com/supabase-community/storage-py/commit/c62151c235e1856ea25faeb68515565b7034eb2c))

### Unknown

* Sync support (#1)

* deps: update black, add unasync

* feat: make BaseBucket

* feat: rework bucket, file APIs

* fix: avoid circular import on StorageException

* deps: add dotenv

* feat: pass User-Agent header with requests

* fix: correct type-hint

* fix: formatting

* chore: update example in README ([`75c9c43`](https://github.com/supabase-community/storage-py/commit/75c9c43ea373cb58970255b8e7438c2ec67e7f25))

* Merge branch &#39;main&#39; of github.com:J0/storage-py into main ([`d41b573`](https://github.com/supabase-community/storage-py/commit/d41b57391f04453986f06d564c5c207e4c75b7cc))

## v0.1.0 (2021-12-24)

### Chore

* chore: update maintainers in license and pyproject ([`e77112c`](https://github.com/supabase-community/storage-py/commit/e77112c6ae43df258b85525e514903949a53f735))

* chore: update maintainers in license and pyproject ([`1e41913`](https://github.com/supabase-community/storage-py/commit/1e419130639cd2c03bcdf0af9ffd3aea34e81e85))

* chore: run pre-commit on all files ([`2654aa4`](https://github.com/supabase-community/storage-py/commit/2654aa4d898b724df11eba28350a6b1cdbb8c0da))

* chore: reinstate python version ([`8c9e022`](https://github.com/supabase-community/storage-py/commit/8c9e022780a75c120b7a512d086645b81ad867ad))

### Feature

* feat: initial commit ([`6da4cd9`](https://github.com/supabase-community/storage-py/commit/6da4cd98de5a5344da6683d1082c3237f6870d8d))

### Refactor

* refactor: update test client imports ([`ef1dff9`](https://github.com/supabase-community/storage-py/commit/ef1dff9052aa43165efc3b549026eefbfa75614b))

* refactor: change directory structure ([`57889bc`](https://github.com/supabase-community/storage-py/commit/57889bc13ff67ddcc4033ba2d587e7e9e87abb11))

### Unknown

* bump: version 0.0.1 → 0.1.0 ([`a3f27bb`](https://github.com/supabase-community/storage-py/commit/a3f27bb9865c3f0ed76264fe8e014fd5323e7fa0))

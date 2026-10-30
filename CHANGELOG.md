# Changelog

## [2.34.0](https://github.com/supabase/supabase-py/compare/v2.33.0...v2.34.0) (2026-10-30)


### Features

* **postgrest:** add strip_nulls() ([#1760](https://github.com/supabase/supabase-py/issues/1760)) ([c86ec9f](https://github.com/supabase/supabase-py/commit/c86ec9fc538ffc985d5da6961cdb24e629f974ae))


### Bug Fixes

* **auth:** accept oauth clients without a name ([#1830](https://github.com/supabase/supabase-py/issues/1830)) ([936458e](https://github.com/supabase/supabase-py/commit/936458ed0651309927e96cf801f881b3e72d5206))
* **auth:** avoid cancelling the running refresh callback ([#1716](https://github.com/supabase/supabase-py/issues/1716)) ([606e0ac](https://github.com/supabase/supabase-py/commit/606e0ac34189e9f9bf04bcc441c8aa326931d8e3))
* **auth:** emit PASSWORD_RECOVERY from verify_otp ([#1743](https://github.com/supabase/supabase-py/issues/1743)) ([b571cc2](https://github.com/supabase/supabase-py/commit/b571cc209cab8df7377c5c007d413b9c8973a778))
* **auth:** emit SIGNED_IN when set_session keeps a valid token ([#1749](https://github.com/supabase/supabase-py/issues/1749)) ([9c092db](https://github.com/supabase/supabase-py/commit/9c092dbd46caa54df61b2bdfe6fd027031ab7d2f))
* **auth:** handle empty OAuth client lists ([#1736](https://github.com/supabase/supabase-py/issues/1736)) ([7d68e6b](https://github.com/supabase/supabase-py/commit/7d68e6b2e5948a89c9d0e927166dc218d886f91d))
* **auth:** map httpx transport errors to AuthRetryableError ([#1808](https://github.com/supabase/supabase-py/issues/1808)) ([901f00d](https://github.com/supabase/supabase-py/commit/901f00d8bb908410c9a4707c30cde6f834008329))
* **auth:** normalize trailing slash in base URL ([#1766](https://github.com/supabase/supabase-py/issues/1766)) ([de040ec](https://github.com/supabase/supabase-py/commit/de040ececba0effe0ef6d1cfa7f4dacf78ebf98e))
* **auth:** preserve phone numbers in MFA factor responses ([#1837](https://github.com/supabase/supabase-py/issues/1837)) ([0e1cf4c](https://github.com/supabase/supabase-py/commit/0e1cf4c2013505d6601f07f4b16c0417a7aa6b67))
* **auth:** preserve the server error message on retryable 5xx responses ([#1833](https://github.com/supabase/supabase-py/issues/1833)) ([c1727d5](https://github.com/supabase/supabase-py/commit/c1727d53a3837ec4bcc7f05be6286c96e373c3fc))
* **auth:** require pyjwt&gt;=2.15.1 for security fixes ([#1820](https://github.com/supabase/supabase-py/issues/1820)) ([f41e80e](https://github.com/supabase/supabase-py/commit/f41e80e4c4afa91bbff979685dea0e0c632714b4))
* **auth:** send one refresh request per auto-refresh tick ([#1854](https://github.com/supabase/supabase-py/issues/1854)) ([bc29bc6](https://github.com/supabase/supabase-py/commit/bc29bc6022646bbe2306c2633271064e410d7983))
* **auth:** send PKCE challenges for email and SSO flows ([#1682](https://github.com/supabase/supabase-py/issues/1682)) ([66cd7ee](https://github.com/supabase/supabase-py/commit/66cd7ee857ff284212e009b2ae861a2e4adf1a3e))
* **auth:** stop the admin API from sharing the client's header dict ([#1645](https://github.com/supabase/supabase-py/issues/1645)) ([6b53131](https://github.com/supabase/supabase-py/commit/6b531317f6571de66c0fc23ad93dc9e5a24d1975))
* **functions:** keep the query string when invoking a function ([#1816](https://github.com/supabase/supabase-py/issues/1816)) ([685469c](https://github.com/supabase/supabase-py/commit/685469c4fbde5e09b5cab0c72a3cdf79298c1313))
* make the capability matrix verifiable ([#1867](https://github.com/supabase/supabase-py/issues/1867)) ([804e7e2](https://github.com/supabase/supabase-py/commit/804e7e2d470fe31840ca8d5a01244df3b1fcaa41))
* **postgrest:** apply normalized timeout to internal httpx clients ([#1758](https://github.com/supabase/supabase-py/issues/1758)) ([774e996](https://github.com/supabase/supabase-py/commit/774e996259f42911d40dcc7fde565e192bf1d0e2))
* **postgrest:** clear basic auth when selecting bearer auth ([#1713](https://github.com/supabase/supabase-py/issues/1713)) ([32e748b](https://github.com/supabase/supabase-py/commit/32e748b0e979943357495f5557b50a6dc577382a))
* **postgrest:** make APIError fields optional so partial error bodies keep their message ([#1732](https://github.com/supabase/supabase-py/issues/1732)) ([18bd628](https://github.com/supabase/supabase-py/commit/18bd62818da822ca0bb6112664072ba275dac9df))
* **postgrest:** omit columns for empty bulk inserts and upserts ([#1815](https://github.com/supabase/supabase-py/issues/1815)) ([62a4e4d](https://github.com/supabase/supabase-py/commit/62a4e4d24fbf78da644e9950b6dc318e4693b1c7))
* **postgrest:** preserve chaining after text search ([#1708](https://github.com/supabase/supabase-py/issues/1708)) ([9588283](https://github.com/supabase/supabase-py/commit/958828302d77ed150c446d61f60e30f138e68735))
* **postgrest:** preserve injected HTTPX client authentication ([#1838](https://github.com/supabase/supabase-py/issues/1838)) ([79d14d9](https://github.com/supabase/supabase-py/commit/79d14d9c6c4cc2b5ddd328217cf7a0b10eb87671))
* **postgrest:** quote rpc array elements sent on GET and HEAD ([#1762](https://github.com/supabase/supabase-py/issues/1762)) ([1bb870e](https://github.com/supabase/supabase-py/commit/1bb870e07518d3860eb21860d6dff3e3ed4fb42f))
* **postgrest:** raise on a non-http base_url ([#1881](https://github.com/supabase/supabase-py/issues/1881)) ([610875d](https://github.com/supabase/supabase-py/commit/610875dc747afe487c96ed1f1110d5da401c2fb8))
* **postgrest:** replace conflicting max-affected preferences ([#1827](https://github.com/supabase/supabase-py/issues/1827)) ([5f989e1](https://github.com/supabase/supabase-py/commit/5f989e1e4c6422a83e3f6ef7c25f7136ea0eb2be))
* **postgrest:** send rpc list args as array literals on GET and HEAD ([#1752](https://github.com/supabase/supabase-py/issues/1752)) ([50e7a4c](https://github.com/supabase/supabase-py/commit/50e7a4c2866a668e5248234e9f36034ef7582c09))
* preserve functions timeout when replacing client options ([#1722](https://github.com/supabase/supabase-py/issues/1722)) ([7fac036](https://github.com/supabase/supabase-py/commit/7fac036f734438e4461628cc07f3b189551778cb))
* **realtime:** call late timeout handlers without a payload ([#1831](https://github.com/supabase/supabase-py/issues/1831)) ([b6ddb74](https://github.com/supabase/supabase-py/commit/b6ddb74b369ea9ccdfc9022368aa872088fa2083))
* **realtime:** cap reconnect backoff at 60 seconds ([#1768](https://github.com/supabase/supabase-py/issues/1768)) ([23ddbca](https://github.com/supabase/supabase-py/commit/23ddbcaa21035e2d0bd4c8ef4392e231f63dea81))
* **realtime:** deliver every broadcast to "*" listeners, ignoring case ([#1818](https://github.com/supabase/supabase-py/issues/1818)) ([eae2838](https://github.com/supabase/supabase-py/commit/eae2838eef450669a49dbaf65900fca867951408))
* **realtime:** honor the WebSocket opening timeout ([#1839](https://github.com/supabase/supabase-py/issues/1839)) ([46efa11](https://github.com/supabase/supabase-py/commit/46efa11c2ddca4f835c8045b5b16b7e6a25f41d9))
* **realtime:** keep references to background tasks ([#1888](https://github.com/supabase/supabase-py/issues/1888)) ([f959593](https://github.com/supabase/supabase-py/commit/f959593e906b5a9a5ebc21bae50d5acada434f0a))
* **realtime:** notify subscribers of channel errors and closure ([#1846](https://github.com/supabase/supabase-py/issues/1846)) ([bcecfc3](https://github.com/supabase/supabase-py/commit/bcecfc3fce1ffbdf6449d1eb637e9f93895f8bc7))
* **realtime:** redact api key and access tokens from debug logs ([#1750](https://github.com/supabase/supabase-py/issues/1750)) ([17147f2](https://github.com/supabase/supabase-py/commit/17147f27796751552bad9812799f8bf08171634d))
* **realtime:** restart timeout after resending push ([#1654](https://github.com/supabase/supabase-py/issues/1654)) ([da3a353](https://github.com/supabase/supabase-py/commit/da3a353b8bbdff978f13427413913dfe2dffe808))
* **realtime:** use the client timeout for join and leave pushes ([#1685](https://github.com/supabase/supabase-py/issues/1685)) ([198396d](https://github.com/supabase/supabase-py/commit/198396dd242c94d59d742618a28dfcfd44214b01))
* **storage:** allow null metadata in list_v2 ([#1804](https://github.com/supabase/supabase-py/issues/1804)) ([9d2f19c](https://github.com/supabase/supabase-py/commit/9d2f19cc372da487d50e39c2141cbd33b0b633bf))
* **storage:** close the upload handle we opened, and only that one ([#1607](https://github.com/supabase/supabase-py/issues/1607)) ([2f3bf40](https://github.com/supabase/supabase-py/commit/2f3bf4003542d72c686cce180b21f4a097fb02a5))
* **storage:** install the iceberg file backend ([#1873](https://github.com/supabase/supabase-py/issues/1873)) ([b2cbf04](https://github.com/supabase/supabase-py/commit/b2cbf0444c31da59c3a5c13efacd89a950c97caf))
* **storage:** merge a partial sortBy with the default in list ([#1817](https://github.com/supabase/supabase-py/issues/1817)) ([3fb5620](https://github.com/supabase/supabase-py/commit/3fb562072fe47408dc520f15754504d41e998051))
* **storage:** read object info in exists() so auth and bucket errors raise ([#1825](https://github.com/supabase/supabase-py/issues/1825)) ([980ac9f](https://github.com/supabase/supabase-py/commit/980ac9ff07326606657b829cdd086ba90e21264d))
* **supabase:** keep postgrest and storage timeouts in replace() ([#1809](https://github.com/supabase/supabase-py/issues/1809)) ([795cad4](https://github.com/supabase/supabase-py/commit/795cad428521ac0463fd5283205378edb04b0951))
* **supabase:** keep the session token on every auth event that has one ([#1856](https://github.com/supabase/supabase-py/issues/1856)) ([ca2fb99](https://github.com/supabase/supabase-py/commit/ca2fb998b333213af8e70862309309d72ff0cebf))
* **supabase:** replace() preserves postgrest and storage timeouts ([#1840](https://github.com/supabase/supabase-py/issues/1840)) ([772ee24](https://github.com/supabase/supabase-py/commit/772ee245be48ad7d91dd6341797c336c937d4f11))


### Performance Improvements

* **postgrest:** speed up JSON parsing by 22x using json.loads ([#1571](https://github.com/supabase/supabase-py/issues/1571)) ([c56c5bb](https://github.com/supabase/supabase-py/commit/c56c5bbabdf5c57c57262e69a72af0c3038fc9f5))


### Documentation

* Clarify when get_user() returns None ([#1569](https://github.com/supabase/supabase-py/issues/1569)) ([3d8417f](https://github.com/supabase/supabase-py/commit/3d8417f17730774df84969831799adb484b736d7))
* document SDK compatibility with Supabase services ([#1870](https://github.com/supabase/supabase-py/issues/1870)) ([1ff1e4a](https://github.com/supabase/supabase-py/commit/1ff1e4aa533dfcc1e6ce81f3be2924f76329b1e8))

## [2.33.0](https://github.com/supabase/supabase-py/compare/v2.32.0...v2.33.0) (2026-10-15)


### Features

* **postgrest:** return a select builder from insert, upsert, update and delete ([#1558](https://github.com/supabase/supabase-py/issues/1558)) ([04baf59](https://github.com/supabase/supabase-py/commit/04baf59450e554714c7554c69f18d3c6f11103ba))


### Bug Fixes

* **auth:** allow listeners to unsubscribe during notification ([#1643](https://github.com/supabase/supabase-py/issues/1643)) ([29ff4ff](https://github.com/supabase/supabase-py/commit/29ff4ff878c938689b2e77466a8549b5615470de))
* **auth:** avoid mutating OAuth query params ([#1660](https://github.com/supabase/supabase-py/issues/1660)) ([553cb47](https://github.com/supabase/supabase-py/commit/553cb471f256d20a628fdf02435300b27504f252))
* **auth:** keep the session after refreshing it on initialize ([#1647](https://github.com/supabase/supabase-py/issues/1647)) ([2658d8b](https://github.com/supabase/supabase-py/commit/2658d8b915e37d79ba663779e773d0d61c5f8cf5))
* **auth:** stop putting the raw JWT in UserDoesntExist ([#1602](https://github.com/supabase/supabase-py/issues/1602)) ([aa73211](https://github.com/supabase/supabase-py/commit/aa73211a69d5c75f54228527e03c3b499a9bfda8))
* **functions:** copy headers in invoke() to avoid leaking them across calls ([#1536](https://github.com/supabase/supabase-py/issues/1536)) ([655d4c2](https://github.com/supabase/supabase-py/commit/655d4c2eabfd9358dea785b17e5f346945e2ed31))
* **functions:** do not overwrite content-type when it is passed in ([#1746](https://github.com/supabase/supabase-py/issues/1746)) ([94748bb](https://github.com/supabase/supabase-py/commit/94748bb6b1e3471b479c10a94f7825c47984b356))
* **functions:** do not parse relay error as json, save it as text instead ([#1714](https://github.com/supabase/supabase-py/issues/1714)) ([dfae141](https://github.com/supabase/supabase-py/commit/dfae1419299d58ae23b77431fa56aa5b7acd62fd))
* **functions:** handle case insensitive headers with httpx.Headers ([#1747](https://github.com/supabase/supabase-py/issues/1747)) ([2de8af0](https://github.com/supabase/supabase-py/commit/2de8af0ade465cfcf96a305ea388ea5820e587e6))
* **functions:** pass verify as keyword argument in create_client ([#1705](https://github.com/supabase/supabase-py/issues/1705)) ([#1706](https://github.com/supabase/supabase-py/issues/1706)) ([42549e4](https://github.com/supabase/supabase-py/commit/42549e45f6627db6d6d238dbca288214ee37b4ac))
* **functions:** raise FunctionsRelayError for x-relay-error responses ([#1638](https://github.com/supabase/supabase-py/issues/1638)) ([f294058](https://github.com/supabase/supabase-py/commit/f2940587241cd0022c251c2193ad34a59b6f47c7))
* **postgrest:** escape quoted values in in filters ([#1703](https://github.com/supabase/supabase-py/issues/1703)) ([710042f](https://github.com/supabase/supabase-py/commit/710042fcc890632a97905f178266806a56e13594))
* **postgrest:** serialize neq/gt/gte/lt/lte filter values like eq ([#1723](https://github.com/supabase/supabase-py/issues/1723)) ([d0e1f34](https://github.com/supabase/supabase-py/commit/d0e1f340846b8300dacb1ca287122ed70bcf88f0))
* **realtime:** include connection params in WebSocket URL ([#1652](https://github.com/supabase/supabase-py/issues/1652)) ([954403b](https://github.com/supabase/supabase-py/commit/954403bc0d4214eaecee384980e2d21ac856131a))
* **realtime:** return the existing channel for a topic from channel() ([#1673](https://github.com/supabase/supabase-py/issues/1673)) ([df4ed51](https://github.com/supabase/supabase-py/commit/df4ed5133964b65945ee6c64de27ed2a29204764))
* **realtime:** update channel join payloads in set_auth ([#1656](https://github.com/supabase/supabase-py/issues/1656)) ([a2a142e](https://github.com/supabase/supabase-py/commit/a2a142e2ee02e77c9da0d524431a38022a6917a6))
* **storage:** make vector object metadata JSON ([#1717](https://github.com/supabase/supabase-py/issues/1717)) ([05c03dc](https://github.com/supabase/supabase-py/commit/05c03dc7cd025f3bf6b626b50ce5e7f13809c048))
* **storage:** preserve vector index creation time ([#1701](https://github.com/supabase/supabase-py/issues/1701)) ([c5e345d](https://github.com/supabase/supabase-py/commit/c5e345dee8afe07f658b73641fe78dfa28441712))

## [2.32.0](https://github.com/supabase/supabase-py/compare/v2.31.0...v2.32.0) (2026-10-02)


### Features

* **functions:** fix invoke option leakage, add method and bytes body support ([#1600](https://github.com/supabase/supabase-py/issues/1600)) ([9dcbc5f](https://github.com/supabase/supabase-py/commit/9dcbc5fdef03477b4c65c1526b861dec55b7b6c2))
* support new realtime features ([#1524](https://github.com/supabase/supabase-py/issues/1524)) ([80688d1](https://github.com/supabase/supabase-py/commit/80688d1278634b7190fc9e7f57b3e885ff3f027c))


### Bug Fixes

* **auth:** raise AuthInvalidJwtError when get_claims JWT has no exp ([#1603](https://github.com/supabase/supabase-py/issues/1603)) ([899302e](https://github.com/supabase/supabase-py/commit/899302ec39fca876c9b70e01f1344b801ce8b842))
* **auth:** raise AuthWeakPasswordError for responses without an error code ([#1629](https://github.com/supabase/supabase-py/issues/1629)) ([1f74409](https://github.com/supabase/supabase-py/commit/1f74409d2f08898988efd534e654c5612d0e214a))
* **ci:** point SDK compliance workflow at the python reusable workflow ([#1540](https://github.com/supabase/supabase-py/issues/1540)) ([b16b16a](https://github.com/supabase/supabase-py/commit/b16b16a175be0bfc57cf7af6acac01ef4078590a))
* **ci:** unbreak storage tests (service_role for bucket empty) and stop fail-fast cancelling sibling jobs ([#1601](https://github.com/supabase/supabase-py/issues/1601)) ([2f9ca44](https://github.com/supabase/supabase-py/commit/2f9ca4446eb691f6a2ef48c68bb24f4d88448774))
* **client_options:** honor False for boolean options in replace() ([#1516](https://github.com/supabase/supabase-py/issues/1516)) ([10fb8f9](https://github.com/supabase/supabase-py/commit/10fb8f9029d4659f1ea874e7154b3ae19a4a1fa1))
* correct invalid feature IDs in sdk-compliance.yaml ([#1578](https://github.com/supabase/supabase-py/issues/1578)) ([2a795a7](https://github.com/supabase/supabase-py/commit/2a795a79c20936771c67d65302495bb8dfa9b2f3))
* handle non-standard and non-JSON error responses without AttributeError ([#1577](https://github.com/supabase/supabase-py/issues/1577)) ([5b8080a](https://github.com/supabase/supabase-py/commit/5b8080af4d4a3d6b3a9491d331a67e8bc115cd9c))
* **postgrest:** align rpc maybe_single with select ([#1555](https://github.com/supabase/supabase-py/issues/1555)) ([0490201](https://github.com/supabase/supabase-py/commit/0490201fb7f201808d0dfdf521ec17015f67b308))
* **postgrest:** coerce non-string values in array filters ([#1530](https://github.com/supabase/supabase-py/issues/1530)) ([3433b0d](https://github.com/supabase/supabase-py/commit/3433b0db4993445a459c6ed7e497e3bdcc194258))
* **postgrest:** escape array-literal elements in cs/cd/contains/contained_by/overlaps ([#1593](https://github.com/supabase/supabase-py/issues/1593)) ([f140cd6](https://github.com/supabase/supabase-py/commit/f140cd6aa900bcf1bb633bcd748598bc82c035a5))
* **postgrest:** normalize boolean values in is_() to lowercase literals ([#1535](https://github.com/supabase/supabase-py/issues/1535)) ([21ccd63](https://github.com/supabase/supabase-py/commit/21ccd6325f9e09e068696c62721f29c76a348a92))
* **postgrest:** preserve negation for or filters ([#1619](https://github.com/supabase/supabase-py/issues/1619)) ([c1dc291](https://github.com/supabase/supabase-py/commit/c1dc29158569cbcbacbf10f850e198a514d81d6f))
* **postgrest:** preserve text search negation ([#1624](https://github.com/supabase/supabase-py/issues/1624)) ([62a0902](https://github.com/supabase/supabase-py/commit/62a090215b7f389a574767c38d4ab92fb1a82990))
* **postgrest:** retry transient failures for HEAD requests ([#1610](https://github.com/supabase/supabase-py/issues/1610)) ([bb7ecc5](https://github.com/supabase/supabase-py/commit/bb7ecc5fb86f5f8729c40a3885c6154d9b9f6262))
* **postgrest:** serialize filter values in eq() ([#1591](https://github.com/supabase/supabase-py/issues/1591)) ([8d90cfa](https://github.com/supabase/supabase-py/commit/8d90cfaf118933a4823f90f4cc3b36e39b73d0bd))
* **realtime:** include join_ref on every client-sent channel event ([#1626](https://github.com/supabase/supabase-py/issues/1626)) ([8c1a914](https://github.com/supabase/supabase-py/commit/8c1a91408b0ca04e9c780fc21b61cb596083ab72))
* **realtime:** process every key in a presence diff's leaves ([#1631](https://github.com/supabase/supabase-py/issues/1631)) ([8913406](https://github.com/supabase/supabase-py/commit/8913406b5b8dac9b7e6f8a359f36fe078eeb299a))
* **storage:** cache control header and retry safety ([#1556](https://github.com/supabase/supabase-py/issues/1556)) ([e9f1141](https://github.com/supabase/supabase-py/commit/e9f11419fca9f97cfcd175cf4bb5bdbfc7e17b5a))
* **storage:** make list_v2 method's `key` optional ([#1695](https://github.com/supabase/supabase-py/issues/1695)) ([e6fba08](https://github.com/supabase/supabase-py/commit/e6fba08f6c20fca4048c0f477af1533d196e1038))
* **storage:** send camelCase sort params in analytics list ([#1636](https://github.com/supabase/supabase-py/issues/1636)) ([11f6cdf](https://github.com/supabase/supabase-py/commit/11f6cdf324d53d76fab5607698e05abcd9514711))


### Documentation

* fix code of conduct link in CONTRIBUTING ([#1538](https://github.com/supabase/supabase-py/issues/1538)) ([3c98900](https://github.com/supabase/supabase-py/commit/3c9890089c7dab5891feb9fdc7872dca9c5a749b))

## [2.31.0](https://github.com/supabase/supabase-py/compare/v2.30.1...v2.31.0) (2026-06-04)


### Features

* update X-Client-Info to use structured semicolon-delimited metadata ([#1479](https://github.com/supabase/supabase-py/issues/1479)) ([cb3857c](https://github.com/supabase/supabase-py/commit/cb3857cf54ff34de9842c447c349dfef7cd8c3c8))


### Bug Fixes

* **storage:** make pyiceberg an optional dependency ([#1513](https://github.com/supabase/supabase-py/issues/1513)) ([d16cfc0](https://github.com/supabase/supabase-py/commit/d16cfc090e6ca55f77b66a123250febc688cd75f))

## [2.30.1](https://github.com/supabase/supabase-py/compare/v2.30.0...v2.30.1) (2026-05-27)


### Documentation

* fix GitHub Issues link in CONTRIBUTING ([#1493](https://github.com/supabase/supabase-py/issues/1493)) ([01377f7](https://github.com/supabase/supabase-py/commit/01377f7f2fe13d7b990ab934cdc5c07bdab651a4))

## [2.30.0](https://github.com/supabase/supabase-py/compare/v2.29.0...v2.30.0) (2026-05-06)


### Features

* **auth:** add current_password to UserAttributes ([#1475](https://github.com/supabase/supabase-py/issues/1475)) ([13df40b](https://github.com/supabase/supabase-py/commit/13df40b9cafd332e56ca816a0406ac31e4a3fc4b))
* **postgrest:** allow select() chaining on write builders ([#1383](https://github.com/supabase/supabase-py/issues/1383)) ([3ed928c](https://github.com/supabase/supabase-py/commit/3ed928c84656872208b42b3462b03efbd491f0e5))
* **postgrest:** use model_construct to avoid validating twice ([#1484](https://github.com/supabase/supabase-py/issues/1484)) ([107bf4e](https://github.com/supabase/supabase-py/commit/107bf4e824bd731f13a252f37a7ae9518b56c8ff))

## [2.29.0](https://github.com/supabase/supabase-py/compare/v2.28.3...v2.29.0) (2026-04-22)


### Features

* **postgrest:** add retry logic on cloudflare errors ([#1449](https://github.com/supabase/supabase-py/issues/1449)) ([a282549](https://github.com/supabase/supabase-py/commit/a2825494a7ed20f35918ef0a02d5024d1a389fa2))


### Bug Fixes

* **storage:** make signedURL an optional string ([#1461](https://github.com/supabase/supabase-py/issues/1461)) ([611cdbb](https://github.com/supabase/supabase-py/commit/611cdbb6046601c973a106303146e4faa50b7756))

## [2.28.3](https://github.com/supabase/supabase-py/compare/v2.28.2...v2.28.3) (2026-03-20)


### Bug Fixes

* **postgrest:** fix maybe_single ([#1424](https://github.com/supabase/supabase-py/issues/1424)) ([c7f8f13](https://github.com/supabase/supabase-py/commit/c7f8f13b40c9f46a46276241f25c17f45b17e069))

## [2.28.2](https://github.com/supabase/supabase-py/compare/v2.28.1...v2.28.2) (2026-03-13)


### Bug Fixes

* **auth:** fix admin list factors payload format. ([#1415](https://github.com/supabase/supabase-py/issues/1415)) ([32843cf](https://github.com/supabase/supabase-py/commit/32843cf8346529e2b7fbcec9d0e787424b70e55c))

## [2.28.1](https://github.com/supabase/supabase-py/compare/v2.28.0...v2.28.1) (2026-03-12)


### Bug Fixes

* **auth:** prevent OverflowError in auto-refresh token retry ([#1397](https://github.com/supabase/supabase-py/issues/1397)) ([#1400](https://github.com/supabase/supabase-py/issues/1400)) ([08bdf38](https://github.com/supabase/supabase-py/commit/08bdf38198680ec25f85ded68dc358c75ddf6fd3))
* **postgrest:** comment out ssl error test ([#1410](https://github.com/supabase/supabase-py/issues/1410)) ([51b86be](https://github.com/supabase/supabase-py/commit/51b86becfe1a51addd59cc3f8e24e891bfd5eb4a))
* **postgrest:** remove check against message field in data payload ([#1413](https://github.com/supabase/supabase-py/issues/1413)) ([81041a4](https://github.com/supabase/supabase-py/commit/81041a4289b449e534ab46cc9cb54a08b6b7fa4f))

## [2.28.0](https://github.com/supabase/supabase-py/compare/v2.27.3...v2.28.0) (2026-02-10)


### Features

* **storage:** add list_v2 method to file_api client ([#1377](https://github.com/supabase/supabase-py/issues/1377)) ([259f4ad](https://github.com/supabase/supabase-py/commit/259f4ad42d4022eed2c44e0e9a316271cfccbde4))


### Bug Fixes

* **auth:** add missing is_sso_user, deleted_at, banned_until to User model ([#1375](https://github.com/supabase/supabase-py/issues/1375)) ([7f84a62](https://github.com/supabase/supabase-py/commit/7f84a629968b9269f233e75e28f973c1cae530d6))
* **realtime:** ensure remove_channel removes channel from channels dict ([#1373](https://github.com/supabase/supabase-py/issues/1373)) ([0923314](https://github.com/supabase/supabase-py/commit/09233140397e7921ab054dbf4d88d1899d30c244))
* **realtime:** use pop with default in _handle_message to prevent KeyError ([#1388](https://github.com/supabase/supabase-py/issues/1388)) ([baea26f](https://github.com/supabase/supabase-py/commit/baea26f7ce7f0572b4e96caaf27add29127349fe))
* **storage3:** replace print() with warnings.warn() for trailing slash notice ([#1380](https://github.com/supabase/supabase-py/issues/1380)) ([50b099f](https://github.com/supabase/supabase-py/commit/50b099fa06efa643d1d43830e4497e21972e46bc))

## [2.27.3](https://github.com/supabase/supabase-py/compare/v2.27.2...v2.27.3) (2026-02-03)


### Bug Fixes

* deprecate python 3.9 in all packages ([#1365](https://github.com/supabase/supabase-py/issues/1365)) ([cc72ed7](https://github.com/supabase/supabase-py/commit/cc72ed75d4c2d05514476d4e8f2786f5e09a174b))
* ensure storage_url has trailing slash to prevent warning ([#1367](https://github.com/supabase/supabase-py/issues/1367)) ([4267ff1](https://github.com/supabase/supabase-py/commit/4267ff134542a742c8cabb1daf01597c3198494d))

## [2.27.2](https://github.com/supabase/supabase-py/compare/v2.27.1...v2.27.2) (2026-01-14)


### Bug Fixes

* **ci:** generate new token for release-please ([#1348](https://github.com/supabase/supabase-py/issues/1348)) ([c2ad37f](https://github.com/supabase/supabase-py/commit/c2ad37f9dc2c5a73d9a1ea06f723e0810ab6aecd))
* **ci:** run CI when .github files change ([#1349](https://github.com/supabase/supabase-py/issues/1349)) ([a221aac](https://github.com/supabase/supabase-py/commit/a221aac029a36693e325125ad036c34936617247))
* **realtime:** ammend reconnect logic to not unsubscribe ([#1346](https://github.com/supabase/supabase-py/issues/1346)) ([cfbe594](https://github.com/supabase/supabase-py/commit/cfbe5943cbc45679bd85dcfd6860c98435912011))

## [2.27.1](https://github.com/supabase/supabase-py/compare/v2.27.0...v2.27.1) (2026-01-06)


### Bug Fixes

* **realtime:** use 'event' instead of 'events' in postgres_changes protocol ([#1339](https://github.com/supabase/supabase-py/issues/1339)) ([c1e7986](https://github.com/supabase/supabase-py/commit/c1e7986c5ef6406b1e966cc7aa69971876ef5934))
* **storage:** catch bad responses from server ([#1344](https://github.com/supabase/supabase-py/issues/1344)) ([ddb5054](https://github.com/supabase/supabase-py/commit/ddb50547db2742411a7ca78fef243f3c5616d57d))

## [2.27.0](https://github.com/supabase/supabase-py/compare/v2.26.0...v2.27.0) (2025-12-16)


### Features

* **auth:** add X (OAuth 2.0) provider ([#1335](https://github.com/supabase/supabase-py/issues/1335)) ([f600f96](https://github.com/supabase/supabase-py/commit/f600f96b521d306f07a21601c58c61dc7fc29c68))


### Bug Fixes

* **storage:** replace deprecated pydantic Extra with literal values ([#1334](https://github.com/supabase/supabase-py/issues/1334)) ([6df3545](https://github.com/supabase/supabase-py/commit/6df354578560fdd2a1a50380420c10b436e7bca1))

## [2.26.0](https://github.com/supabase/supabase-py/compare/v2.25.1...v2.26.0) (2025-12-15)


### Features

* **storage:** add pyiceberg wrapper ([#1326](https://github.com/supabase/supabase-py/issues/1326)) ([08e3b4c](https://github.com/supabase/supabase-py/commit/08e3b4caa47badae3df9116c277b3df326e84a53))
* **supabase:** use yarl URL builder in supabase as well ([#1331](https://github.com/supabase/supabase-py/issues/1331)) ([78ebf2c](https://github.com/supabase/supabase-py/commit/78ebf2c62107bd2cfc7e2ee4bcdd3388f091a6e3))


### Bug Fixes

* **storage:** remove v1 from path concatenation ([#1330](https://github.com/supabase/supabase-py/issues/1330)) ([e3ddf40](https://github.com/supabase/supabase-py/commit/e3ddf408293caa318f25fc2c3048373442ac6edc))

## [2.25.1](https://github.com/supabase/supabase-py/compare/v2.25.0...v2.25.1) (2025-12-09)


### Bug Fixes

* **storage:** add query parameters option to download ([#1327](https://github.com/supabase/supabase-py/issues/1327)) ([63f7226](https://github.com/supabase/supabase-py/commit/63f72260b8d68cac4185b66517f58cbb2b40365f))

## [2.25.0](https://github.com/supabase/supabase-py/compare/v2.24.0...v2.25.0) (2025-12-03)


### Features

* **storage:** add vector and analytics buckets support ([#1318](https://github.com/supabase/supabase-py/issues/1318)) ([fd0c122](https://github.com/supabase/supabase-py/commit/fd0c1220e4fbf13f0953953df0b58ddeadce0bd9))

## [2.24.0](https://github.com/supabase/supabase-py/compare/v2.23.3...v2.24.0) (2025-11-07)


### Features

* add more workspace linting rules ([#1304](https://github.com/supabase/supabase-py/issues/1304)) ([31704ac](https://github.com/supabase/supabase-py/commit/31704aceae8757c08fe314925337202337f6adb1))

### Breaking changes

* Removed `SyncClient` classes from both `supabase_auth` and `supabase_functions`, in favor of plain `httpx.Client`s instead.

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

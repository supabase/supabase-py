# Changelog

## [3.0.0-a2](https://github.com/supabase/supabase-py/compare/v3.0.0-a1...v3.0.0-a2) (2026-11-18)


### ⚠ BREAKING CHANGES

* log requests through a supabase logger hierarchy without secrets ([#2109](https://github.com/supabase/supabase-py/issues/2109))
* **realtime:** add http_send and raise from send_broadcast on an unjoined channel ([#2110](https://github.com/supabase/supabase-py/issues/2110))
* **storage:** stream uploads and downloads ([#2105](https://github.com/supabase/supabase-py/issues/2105))
* **storage:** add copy and move options and return the object id from upload ([#2104](https://github.com/supabase/supabase-py/issues/2104))
* **auth:** return pagination info and lazy iterators from admin list_users ([#2102](https://github.com/supabase/supabase-py/issues/2102))
* **supabase:** reject a supabase_url that does not use https ([#2098](https://github.com/supabase/supabase-py/issues/2098))
* **realtime:** reject ws urls on hosts that are not loopback ([#2092](https://github.com/supabase/supabase-py/issues/2092))
* **realtime:** align presence with the presence specs ([#2088](https://github.com/supabase/supabase-py/issues/2088))
* **realtime:** rejoin channels after a reconnect and time out pushes ([#2082](https://github.com/supabase/supabase-py/issues/2082))
* **storage:** drop the legacy list endpoint and make list-v2 the only list ([#2067](https://github.com/supabase/supabase-py/issues/2067))
* **realtime:** flatten the postgres_changes payload ([#2055](https://github.com/supabase/supabase-py/issues/2055))
* **postgrest:** return csv() results as a TextAPIResponse ([#2051](https://github.com/supabase/supabase-py/issues/2051))
* **postgrest:** parse responses with json.loads and return scalar RPC results ([#2049](https://github.com/supabase/supabase-py/issues/2049))
* **postgrest:** send datetime filter values as iso 8601 with an offset ([#2047](https://github.com/supabase/supabase-py/issues/2047))
* **supabase:** share one lazily connecting realtime client per AsyncClient ([#2034](https://github.com/supabase/supabase-py/issues/2034))
* **realtime:** rename RealtimeClient.close() to aclose() ([#2036](https://github.com/supabase/supabase-py/issues/2036))
* **realtime:** move to protocol 2.0.0 with binary broadcast ([#2033](https://github.com/supabase/supabase-py/issues/2033))
* add a shared retry policy with Retry-After, jitter and per-client configuration ([#2030](https://github.com/supabase/supabase-py/issues/2030))
* **postgrest:** type text_search options and the response shape ([#2028](https://github.com/supabase/supabase-py/issues/2028))
* **postgrest:** require a filter or all() on update() and delete() ([#2025](https://github.com/supabase/supabase-py/issues/2025))
* **postgrest:** make the request builders immutable ([#2023](https://github.com/supabase/supabase-py/issues/2023))
* **auth:** typed auth state changes and a single-flight session refresh core ([#2021](https://github.com/supabase/supabase-py/issues/2021))
* add a root SupabaseError and wrap transport errors in every package ([#2018](https://github.com/supabase/supabase-py/issues/2018))
* **functions:** remove FunctionsError.to_dict and FunctionsApiErrorDict ([#2015](https://github.com/supabase/supabase-py/issues/2015))
* **supabase:** replace ClientOptions with keyword arguments and per-service options ([#2011](https://github.com/supabase/supabase-py/issues/2011))
* add configurable request timeouts for every service ([#2010](https://github.com/supabase/supabase-py/issues/2010))
* **realtime:** raise send failures instead of writing to a failed connection ([#2007](https://github.com/supabase/supabase-py/issues/2007))
* **realtime:** honor heartbeat intervals below 15 seconds and accept float durations ([#2006](https://github.com/supabase/supabase-py/issues/2006))
* raise the minimum python version to 3.12 ([#2002](https://github.com/supabase/supabase-py/issues/2002))
* **supabase:** freeze the option and parameter dataclasses ([#2000](https://github.com/supabase/supabase-py/issues/2000))
* **supabase:** share one client implementation between AsyncClient and Client ([#1998](https://github.com/supabase/supabase-py/issues/1998))
* **storage:** take upsert as a bool in upload and create_signed_upload_url ([#1997](https://github.com/supabase/supabase-py/issues/1997))
* **storage:** treat object keys as literal strings ([#1987](https://github.com/supabase/supabase-py/issues/1987))
* spell out abbreviations in public names ([#1981](https://github.com/supabase/supabase-py/issues/1981))
* **functions,postgrest:** stop importing httpx outside the httpx adapter ([#1977](https://github.com/supabase/supabase-py/issues/1977))

### Features

* add a root SupabaseError and wrap transport errors in every package ([#2018](https://github.com/supabase/supabase-py/issues/2018)) ([ac8950f](https://github.com/supabase/supabase-py/commit/ac8950f614ba714211bfb62c15656332c90a7e57))
* add a shared retry policy with Retry-After, jitter and per-client configuration ([#2030](https://github.com/supabase/supabase-py/issues/2030)) ([885bfc5](https://github.com/supabase/supabase-py/commit/885bfc5da6a8e809873ba1e68443178adb652547))
* add configurable request timeouts for every service ([#2010](https://github.com/supabase/supabase-py/issues/2010)) ([50354b6](https://github.com/supabase/supabase-py/commit/50354b63c65d8e395f7de3c18e61eb90779dad8d))
* **auth:** add admin mfa update_factor ([#2129](https://github.com/supabase/supabase-py/issues/2129)) ([75b9e1d](https://github.com/supabase/supabase-py/commit/75b9e1df5c099aa5db969c5a7617b26dff0fe92e))
* **auth:** add admin sign_out ([#2108](https://github.com/supabase/supabase-py/issues/2108)) ([0df6509](https://github.com/supabase/supabase-py/commit/0df65095ba303330adc11ff3e8c2a1df7ae554c1))
* **auth:** detect pkce codes and error redirects in initialize_from_url ([#2124](https://github.com/supabase/supabase-py/issues/2124)) ([8032d97](https://github.com/supabase/supabase-py/commit/8032d9754fabecd21417c8d0d4e4836dee1beed1))
* **auth:** return pagination info and lazy iterators from admin list_users ([#2102](https://github.com/supabase/supabase-py/issues/2102)) ([7388531](https://github.com/supabase/supabase-py/commit/73885310f17645273d303b790021c2504ff31c10))
* **auth:** typed auth state changes and a single-flight session refresh core ([#2021](https://github.com/supabase/supabase-py/issues/2021)) ([1f56185](https://github.com/supabase/supabase-py/commit/1f56185a062d75ec2c31694eeb8633705a76f0bc))
* **functions:** stream invocation responses and parse server-sent events ([#2111](https://github.com/supabase/supabase-py/issues/2111)) ([0af8711](https://github.com/supabase/supabase-py/commit/0af87115738a2366e9a12547ce42dfdff337ae71))
* log requests through a supabase logger hierarchy without secrets ([#2109](https://github.com/supabase/supabase-py/issues/2109)) ([76d87d4](https://github.com/supabase/supabase-py/commit/76d87d4eb4c76d544ffc19a0bbe7a7ae04d7836d))
* **postgrest:** add casts, JSON paths and aggregates as column expressions ([#2114](https://github.com/supabase/supabase-py/issues/2114)) ([b3d4810](https://github.com/supabase/supabase-py/commit/b3d4810ddf3e0fb0d72583bf5d171e8f232307ec))
* **postgrest:** add column expressions and the filter tree ([#2041](https://github.com/supabase/supabase-py/issues/2041)) ([82e2bb3](https://github.com/supabase/supabase-py/commit/82e2bb336029667875e3439d08f774624f347aa3))
* **postgrest:** add embedded relations and scopes ([#2117](https://github.com/supabase/supabase-py/issues/2117)) ([9dfc8ac](https://github.com/supabase/supabase-py/commit/9dfc8ac9efbd2ffc541598471c5845b3bc7c9975))
* **postgrest:** add is_distinct, dry_run and geojson to the string builder ([#2113](https://github.com/supabase/supabase-py/issues/2113)) ([b922058](https://github.com/supabase/supabase-py/commit/b922058c3402cdee9124a5730e371f9666774ec5))
* **postgrest:** add projection models with select_as ([#2122](https://github.com/supabase/supabase-py/issues/2122)) ([9779632](https://github.com/supabase/supabase-py/commit/97796321e6ad2c59369ecff24c74cf78b66d1344))
* **postgrest:** add the remaining filter operators and orderings ([#2042](https://github.com/supabase/supabase-py/issues/2042)) ([d1e755d](https://github.com/supabase/supabase-py/commit/d1e755de69fda17a4095ffa9063179113c4bd10f))
* **postgrest:** add the table definition, the request value and the executor ([#2043](https://github.com/supabase/supabase-py/issues/2043)) ([1217f42](https://github.com/supabase/supabase-py/commit/1217f4225daf359216ceaf6662719a7cd258a227))
* **postgrest:** add the typed query builder ([#2044](https://github.com/supabase/supabase-py/issues/2044)) ([e0ee463](https://github.com/supabase/supabase-py/commit/e0ee463cda269ca63fdae3d284fda4019bc9bd4e))
* **postgrest:** add typed rpc ([#2120](https://github.com/supabase/supabase-py/issues/2120)) ([a709bbc](https://github.com/supabase/supabase-py/commit/a709bbcf386fa031a3e8176d9f3e9b453c441f54))
* **postgrest:** require a filter or all() on update() and delete() ([#2025](https://github.com/supabase/supabase-py/issues/2025)) ([29843bd](https://github.com/supabase/supabase-py/commit/29843bdca5e2e97ce50be2648d716975c2cb927e))
* **postgrest:** type text_search options and the response shape ([#2028](https://github.com/supabase/supabase-py/issues/2028)) ([d3dd14b](https://github.com/supabase/supabase-py/commit/d3dd14bdae69550b5c81f25d216ae7acc4b9f199))
* **realtime:** accept typed tables, filters and columns in postgres_changes ([#2126](https://github.com/supabase/supabase-py/issues/2126)) ([854038e](https://github.com/supabase/supabase-py/commit/854038efc31773dda0dd8cf89ad70ddb46a828e7))
* **realtime:** add a custom websocket transport and deferred disconnect ([#2115](https://github.com/supabase/supabase-py/issues/2115)) ([7554c3e](https://github.com/supabase/supabase-py/commit/7554c3e178e09f464764e8e7fa996a37b5f8eacf))
* **realtime:** add http_send and raise from send_broadcast on an unjoined channel ([#2110](https://github.com/supabase/supabase-py/issues/2110)) ([575f4c6](https://github.com/supabase/supabase-py/commit/575f4c60ca9456eed6839ddcaf4d7785a08b3d8a))
* **realtime:** add the persist option to send_broadcast and http_send ([#2118](https://github.com/supabase/supabase-py/issues/2118)) ([1fb7ad7](https://github.com/supabase/supabase-py/commit/1fb7ad7b395fadb42b8f4cbf071d4d2e8821b4d2))
* **realtime:** expose connection state and heartbeat statuses ([#2087](https://github.com/supabase/supabase-py/issues/2087)) ([7751295](https://github.com/supabase/supabase-py/commit/7751295f6ed93918022488c1b393a23a8902edb9))
* **realtime:** flatten the postgres_changes payload ([#2055](https://github.com/supabase/supabase-py/issues/2055)) ([569e6fa](https://github.com/supabase/supabase-py/commit/569e6fa4363a5cd525ac5d143beefe400b2711d5))
* **realtime:** move to protocol 2.0.0 with binary broadcast ([#2033](https://github.com/supabase/supabase-py/issues/2033)) ([92d524c](https://github.com/supabase/supabase-py/commit/92d524c1d8778d0dc0070663c28413b308722561))
* **realtime:** rename RealtimeClient.close() to aclose() ([#2036](https://github.com/supabase/supabase-py/issues/2036)) ([6eca35f](https://github.com/supabase/supabase-py/commit/6eca35f9efd3afb6049919edcaa657de135b82ec))
* **storage:** add bucket lifecycle policies ([#2130](https://github.com/supabase/supabase-py/issues/2130)) ([ff8a232](https://github.com/supabase/supabase-py/commit/ff8a2321b95bf7a6d45d0c8e354b283692f36eaf))
* **storage:** add cache_nonce to signed, public and download URLs ([#2123](https://github.com/supabase/supabase-py/issues/2123)) ([cfa5f89](https://github.com/supabase/supabase-py/commit/cfa5f895c7714aae00c7a804007754af459e38a5))
* **storage:** add copy and move options and return the object id from upload ([#2104](https://github.com/supabase/supabase-py/issues/2104)) ([a0797de](https://github.com/supabase/supabase-py/commit/a0797de1dbf81f73cd57b29e388690fde63be88b))
* **storage:** add resumable uploads with pause, resume and cancel ([#2125](https://github.com/supabase/supabase-py/issues/2125)) ([3ad73d9](https://github.com/supabase/supabase-py/commit/3ad73d913770316b6973238e576531a4c37c3643))
* **storage:** download byte ranges and resume partial downloads ([#2119](https://github.com/supabase/supabase-py/issues/2119)) ([9de9bd9](https://github.com/supabase/supabase-py/commit/9de9bd9aaf7db36d51a5dc1ba913ec5d50f41adf))
* **storage:** paginate list lazily and add list_buckets options ([#2103](https://github.com/supabase/supabase-py/issues/2103)) ([1535ff7](https://github.com/supabase/supabase-py/commit/1535ff755592034654c49707127e1033ba21de69))
* **storage:** report upload and download progress ([#2116](https://github.com/supabase/supabase-py/issues/2116)) ([ee7b1d4](https://github.com/supabase/supabase-py/commit/ee7b1d407fa24b7c0e69761194d15db0b4edf094))
* **storage:** stream uploads and downloads ([#2105](https://github.com/supabase/supabase-py/issues/2105)) ([9c39732](https://github.com/supabase/supabase-py/commit/9c39732c1670b8d11ea24c52dfe59c14b2b86ddf))
* **supabase:** add close() and aclose() to the top-level client ([#2035](https://github.com/supabase/supabase-py/issues/2035)) ([1ab137d](https://github.com/supabase/supabase-py/commit/1ab137d884f2ab2bc55b2065877be1a763ea97e0))
* **supabase:** add with_token() for per-request clients ([#2032](https://github.com/supabase/supabase-py/issues/2032)) ([236b2a1](https://github.com/supabase/supabase-py/commit/236b2a16e4f8bb25a4a80c18311b6200d1bafdf2))
* **supabase:** expose the typed API on the client ([#2121](https://github.com/supabase/supabase-py/issues/2121)) ([04663b9](https://github.com/supabase/supabase-py/commit/04663b9552606aa767da2ad66d9c4a43655462ec))
* **supabase:** pull the realtime access token from the auth session ([#2038](https://github.com/supabase/supabase-py/issues/2038)) ([73a65b4](https://github.com/supabase/supabase-py/commit/73a65b48b96b779461954ccfaae09dbd489304d8)), closes [#1210](https://github.com/supabase/supabase-py/issues/1210)
* **supabase:** replace ClientOptions with keyword arguments and per-service options ([#2011](https://github.com/supabase/supabase-py/issues/2011)) ([797f938](https://github.com/supabase/supabase-py/commit/797f938f87a9fbbe8f9ef009f046293026ede641))


### Bug Fixes

* **auth:** align get_claims with the spec ([#2081](https://github.com/supabase/supabase-py/issues/2081)) ([7320cd2](https://github.com/supabase/supabase-py/commit/7320cd232d70386fe6a921068e2c60aef9d0fc09))
* **auth:** align sign_out with the sign-out spec ([#2080](https://github.com/supabase/supabase-py/issues/2080)) ([101277a](https://github.com/supabase/supabase-py/commit/101277a4ee724468b2b04c6821b32edb162fdc75))
* **auth:** make the sync test generator reproduce the committed sync tests ([#1971](https://github.com/supabase/supabase-py/issues/1971)) ([5523e0b](https://github.com/supabase/supabase-py/commit/5523e0b141bf7f3a207211c7c6e68312aa2ace8b))
* **auth:** notify password recovery from verify_otp and pkce exchanges ([#2057](https://github.com/supabase/supabase-py/issues/2057)) ([e05176b](https://github.com/supabase/supabase-py/commit/e05176b152ea9ddc1ce5f5a78dae7afa165729d8))
* **auth:** port the v2 response parsing fixes ([#2058](https://github.com/supabase/supabase-py/issues/2058)) ([16825e8](https://github.com/supabase/supabase-py/commit/16825e8d46654084f2ad3a83fa0f4e02c8850f2e))
* **auth:** raise AuthInvalidJwtError for malformed JWTs in decode_jwt ([#2056](https://github.com/supabase/supabase-py/issues/2056)) ([868f681](https://github.com/supabase/supabase-py/commit/868f681bb9d78f6cc40f3e3fc495ca8d846c94ce))
* **auth:** raise AuthInvalidJwtError for non-JWT access tokens in set_session ([#2059](https://github.com/supabase/supabase-py/issues/2059)) ([27dcc04](https://github.com/supabase/supabase-py/commit/27dcc0454e7de5b54bfe3e37ef655114c187ec2c))
* **auth:** raise the API error when fetching the JWKS fails ([#2079](https://github.com/supabase/supabase-py/issues/2079)) ([a5e9e1a](https://github.com/supabase/supabase-py/commit/a5e9e1a97468ba33da26d194d8e5a7aaf60f2543))
* **auth:** read implicit grant params from the url fragment ([#2060](https://github.com/supabase/supabase-py/issues/2060)) ([9fac82d](https://github.com/supabase/supabase-py/commit/9fac82daa9af73a48baa08a65474f22210240e3f))
* **auth:** start refresh token retry backoff at 200 milliseconds ([#1978](https://github.com/supabase/supabase-py/issues/1978)) ([394a690](https://github.com/supabase/supabase-py/commit/394a69020f8135746f78931178ba06a258cd715e))
* **deps:** raise the pyjwt floor to 2.15.1 and install pyiceberg with pyarrow ([#1993](https://github.com/supabase/supabase-py/issues/1993)) ([14e4d9a](https://github.com/supabase/supabase-py/commit/14e4d9a1501e96a95501c207b36bdb0573cd3e63))
* **functions,postgrest:** stop importing httpx outside the httpx adapter ([#1977](https://github.com/supabase/supabase-py/issues/1977)) ([5331957](https://github.com/supabase/supabase-py/commit/533195702a4e61bca4f19aae9680d7b13d85437d))
* **functions:** accept regions that are not in FunctionRegion ([#2091](https://github.com/supabase/supabase-py/issues/2091)) ([4a311ef](https://github.com/supabase/supabase-py/commit/4a311ef6095796dc99010bc6355f6aa1130480f8))
* **functions:** keep the query string when invoking a function ([#2064](https://github.com/supabase/supabase-py/issues/2064)) ([d49f13b](https://github.com/supabase/supabase-py/commit/d49f13b057ef18e1899d95088ed99a7c10272ffe))
* **postgrest:** accept generated TypedDict types in insert, upsert and update ([#2062](https://github.com/supabase/supabase-py/issues/2062)) ([439735e](https://github.com/supabase/supabase-py/commit/439735e045eba8a6332d2c031c280425f7d0170a))
* **postgrest:** describe bodiless and non-JSON error responses with the status phrase, Proxy-Status code and decoded body ([#2061](https://github.com/supabase/supabase-py/issues/2061)) ([90d19c9](https://github.com/supabase/supabase-py/commit/90d19c98b074d213672edcea1ecd783b79eb22e4))
* **postgrest:** describe non-PostgREST JSON error bodies by their status ([#2063](https://github.com/supabase/supabase-py/issues/2063)) ([7d0ff4a](https://github.com/supabase/supabase-py/commit/7d0ff4aab914af3d9eda610af91ec629222e2967))
* **postgrest:** escape bulk column names and reject None in in_() ([#2046](https://github.com/supabase/supabase-py/issues/2046)) ([cde16dc](https://github.com/supabase/supabase-py/commit/cde16dcfbbe6341bf35e4064b1e657e96cb92857))
* **postgrest:** keep bulk insert columns in first-seen order ([#2045](https://github.com/supabase/supabase-py/issues/2045)) ([efe7cf8](https://github.com/supabase/supabase-py/commit/efe7cf86fb07c968514e08d7eeef17386e8c0138))
* **postgrest:** make the request builders immutable ([#2023](https://github.com/supabase/supabase-py/issues/2023)) ([eb983ef](https://github.com/supabase/supabase-py/commit/eb983ef5ec72e4027c1c19eccac3a0f02c79986d)), closes [#1208](https://github.com/supabase/supabase-py/issues/1208)
* **postgrest:** omit the columns parameter when a bulk insert has no keys ([#2048](https://github.com/supabase/supabase-py/issues/2048)) ([f80e732](https://github.com/supabase/supabase-py/commit/f80e7325db9e4da1a3d5cfc9dee1a2a4971f02a1))
* **postgrest:** parse responses with json.loads and return scalar RPC results ([#2049](https://github.com/supabase/supabase-py/issues/2049)) ([d5ead1f](https://github.com/supabase/supabase-py/commit/d5ead1f5618a7dcc2ab945ad14f300d6501c7e1e))
* **postgrest:** port small v2 request fixes ([#2050](https://github.com/supabase/supabase-py/issues/2050)) ([f13f7a3](https://github.com/supabase/supabase-py/commit/f13f7a3fdc4b65924408fd356eb85e5f40d698d4))
* **postgrest:** quote json path keys separately from the column name ([#2054](https://github.com/supabase/supabase-py/issues/2054)) ([f8f4dbf](https://github.com/supabase/supabase-py/commit/f8f4dbf313df7499e64cfb803902fce789b7bf02))
* **postgrest:** reject filters and transforms after insert() and upsert() ([#2022](https://github.com/supabase/supabase-py/issues/2022)) ([1166a75](https://github.com/supabase/supabase-py/commit/1166a759a40834284601644d6f339da8d507800d))
* **postgrest:** replace profile headers when switching schema ([#2075](https://github.com/supabase/supabase-py/issues/2075)) ([7572f13](https://github.com/supabase/supabase-py/commit/7572f1300ae738467cae75fba7d2b9be2d6a3f57))
* **postgrest:** return csv() results as a TextAPIResponse ([#2051](https://github.com/supabase/supabase-py/issues/2051)) ([fd9ff93](https://github.com/supabase/supabase-py/commit/fd9ff93616616ee5b87aee2893c58c15fc773076))
* **postgrest:** send datetime filter values as iso 8601 with an offset ([#2047](https://github.com/supabase/supabase-py/issues/2047)) ([8b1ab30](https://github.com/supabase/supabase-py/commit/8b1ab30a1d3720862fdb7fe75403f74ba0d42928))
* **postgrest:** type rpc() with count but no head as the filter builder ([#2053](https://github.com/supabase/supabase-py/issues/2053)) ([8323a9f](https://github.com/supabase/supabase-py/commit/8323a9f380ced9f8641ec62d05da154419950f22))
* **postgrest:** validate typed writes against the insert and update types and send aliased columns by name ([#2069](https://github.com/supabase/supabase-py/issues/2069)) ([9f44e88](https://github.com/supabase/supabase-py/commit/9f44e88c25347d624cea21fcf623a0346380f362))
* **realtime:** align presence with the presence specs ([#2088](https://github.com/supabase/supabase-py/issues/2088)) ([c6c65ab](https://github.com/supabase/supabase-py/commit/c6c65ab496bc91197b4098f1092c796285c2117d))
* **realtime:** fail presence updates at once when the channel closes ([#2089](https://github.com/supabase/supabase-py/issues/2089)) ([5261272](https://github.com/supabase/supabase-py/commit/52612721c7ff029f4913dcbc7ee8e3c893611f80))
* **realtime:** honor heartbeat intervals below 15 seconds and accept float durations ([#2006](https://github.com/supabase/supabase-py/issues/2006)) ([c66e48e](https://github.com/supabase/supabase-py/commit/c66e48edb6c1d0ff02237472fd5468933755a760))
* **realtime:** move channels out of joined on phx_error, phx_close and dropped connections ([#2068](https://github.com/supabase/supabase-py/issues/2068)) ([2caaadf](https://github.com/supabase/supabase-py/commit/2caaadfcace92f9682f029e04ff11189a76c8f3a))
* **realtime:** port the v2 postgres_changes fixes ([#2052](https://github.com/supabase/supabase-py/issues/2052)) ([b672e62](https://github.com/supabase/supabase-py/commit/b672e62c169b858304778575e57f513ee755e9c1))
* **realtime:** raise send failures instead of writing to a failed connection ([#2007](https://github.com/supabase/supabase-py/issues/2007)) ([7f6add1](https://github.com/supabase/supabase-py/commit/7f6add13ebf4790fe225068986a85a4cf1fc4592))
* **realtime:** redact API keys and access tokens from debug logs ([#1992](https://github.com/supabase/supabase-py/issues/1992)) ([2b20207](https://github.com/supabase/supabase-py/commit/2b202075f15129283ae69bcfa64b42a2df0d72b7))
* **realtime:** reject ws urls on hosts that are not loopback ([#2092](https://github.com/supabase/supabase-py/issues/2092)) ([b16efdb](https://github.com/supabase/supabase-py/commit/b16efdbd273f0019e8d05d7b29e0168302597ecb))
* **realtime:** rejoin channels after a reconnect and time out pushes ([#2082](https://github.com/supabase/supabase-py/issues/2082)) ([56af8b0](https://github.com/supabase/supabase-py/commit/56af8b069020961fd222b26c950acaeb9e0d7bb3))
* **realtime:** send the access token on every join and push it on every session change ([#2037](https://github.com/supabase/supabase-py/issues/2037)) ([20d29b6](https://github.com/supabase/supabase-py/commit/20d29b64547f4fbf503f19a9a557ff575cc9f3b3))
* **storage:** drop the legacy list endpoint and make list-v2 the only list ([#2067](https://github.com/supabase/supabase-py/issues/2067)) ([cc2cc3b](https://github.com/supabase/supabase-py/commit/cc2cc3b33c04cc645670dcc1d3d4aab265c1fec7))
* **storage:** normalize object keys in every method and base exists() on object info ([#2097](https://github.com/supabase/supabase-py/issues/2097)) ([6e182b0](https://github.com/supabase/supabase-py/commit/6e182b0d8830ef4e34aed5c3c485320ee6e6bbfe))
* **storage:** port the v2 vector and analytics bucket fixes ([#2066](https://github.com/supabase/supabase-py/issues/2066)) ([4efbdbc](https://github.com/supabase/supabase-py/commit/4efbdbcdab8d5314f8cad9efcec1025cd8dbab6a))
* **storage:** raise valueerror when the analytics catalog has no api key ([#2093](https://github.com/supabase/supabase-py/issues/2093)) ([7321cab](https://github.com/supabase/supabase-py/commit/7321cabef548389aa89ed1375a57c833de48556f))
* **storage:** reject object keys with empty segments ([#2095](https://github.com/supabase/supabase-py/issues/2095)) ([2a49071](https://github.com/supabase/supabase-py/commit/2a49071dd6627a6c5c23bf026eb6065cc34219bc))
* **storage:** take upsert as a bool in upload and create_signed_upload_url ([#1997](https://github.com/supabase/supabase-py/issues/1997)) ([0331c57](https://github.com/supabase/supabase-py/commit/0331c57eff1569cd0ea69250a3bafc752b6d50e6)), closes [#1996](https://github.com/supabase/supabase-py/issues/1996)
* **storage:** treat object keys as literal strings ([#1987](https://github.com/supabase/supabase-py/issues/1987)) ([b54cba4](https://github.com/supabase/supabase-py/commit/b54cba4ff061cdcdd0b0d7cb1e38395aac1bf5ce))
* **supabase:** default to a 60 second request timeout with httpx and aiohttp ([#2096](https://github.com/supabase/supabase-py/issues/2096)) ([6a57d1f](https://github.com/supabase/supabase-py/commit/6a57d1f8d170f9b709c00b7111c434a569459b93))
* **supabase:** export create_client from supabase with httpx as the default backend ([#2083](https://github.com/supabase/supabase-py/issues/2083)) ([4200cb9](https://github.com/supabase/supabase-py/commit/4200cb941b5a2dc9c1a0d6e31389ce70a4349828))
* **supabase:** freeze the option and parameter dataclasses ([#2000](https://github.com/supabase/supabase-py/issues/2000)) ([7bcf067](https://github.com/supabase/supabase-py/commit/7bcf067c8a8d7f5bd65ba141392eb3d140b7314b))
* **supabase:** keep a secret key for data calls after a sign-in ([#2078](https://github.com/supabase/supabase-py/issues/2078)) ([336f27b](https://github.com/supabase/supabase-py/commit/336f27b4236a9ec414297a4b6a07b73b11fd8b94))
* **supabase:** keep the session token on every auth event that has one ([#1989](https://github.com/supabase/supabase-py/issues/1989)) ([0c07c58](https://github.com/supabase/supabase-py/commit/0c07c5860180dff7549154a38b899e5c0fc0e337))
* **supabase:** raise unexpected errors from the stored session lookup in create ([#2094](https://github.com/supabase/supabase-py/issues/2094)) ([7c658a7](https://github.com/supabase/supabase-py/commit/7c658a749c8c1223a2008e9f2fbdeded2ec3d9b1))
* **supabase:** reject a supabase_url that does not use https ([#2098](https://github.com/supabase/supabase-py/issues/2098)) ([91aa96e](https://github.com/supabase/supabase-py/commit/91aa96eb6b8e90548d4ebc534977fdfe4213cab4))
* **supabase:** reject non-string url and key in create_client ([#2065](https://github.com/supabase/supabase-py/issues/2065)) ([c49d791](https://github.com/supabase/supabase-py/commit/c49d791f193e2d3eeb97c8ab804eba82c9bd0d04))
* **supabase:** share one client implementation between AsyncClient and Client ([#1998](https://github.com/supabase/supabase-py/issues/1998)) ([76f31e2](https://github.com/supabase/supabase-py/commit/76f31e2431771024c09ff1b193a1fcedf4590ce9))
* **supabase:** share one lazily connecting realtime client per AsyncClient ([#2034](https://github.com/supabase/supabase-py/issues/2034)) ([60ce545](https://github.com/supabase/supabase-py/commit/60ce54577c80591fe007f83f6318e42f791f47a9))
* **supabase:** stop sending new-format api keys as bearer to edge functions ([#2005](https://github.com/supabase/supabase-py/issues/2005)) ([213ae34](https://github.com/supabase/supabase-py/commit/213ae34a1433ab4aa7f7fa7512ebf232c3bdbf90))
* **utils:** drop credential headers on cross origin redirects ([#1994](https://github.com/supabase/supabase-py/issues/1994)) ([72bf760](https://github.com/supabase/supabase-py/commit/72bf76061090ce3ec539a6ec2f812f13ed7e9643))
* **utils:** keep name, docstring and signature of handle_http_io methods ([#1976](https://github.com/supabase/supabase-py/issues/1976)) ([68cb2b8](https://github.com/supabase/supabase-py/commit/68cb2b8d423eeea2fe8b731f24de9ce1e2345364))
* **utils:** keep the request's Authorization header over injected httpx client auth ([#1990](https://github.com/supabase/supabase-py/issues/1990)) ([8b6b049](https://github.com/supabase/supabase-py/commit/8b6b0490b173c687728d89f5388ab76e294f6e25))
* **utils:** type async request methods as coroutines and test cancelling them ([#2112](https://github.com/supabase/supabase-py/issues/2112)) ([e849e5e](https://github.com/supabase/supabase-py/commit/e849e5e78c542ad4122749625477709862810de3))


### Documentation

* clarify contribution policy for v3 and v2 ([#1958](https://github.com/supabase/supabase-py/issues/1958)) ([84b919e](https://github.com/supabase/supabase-py/commit/84b919e4c4e767bad1b3e682aca0b887b9dd2fa8))
* point agents to the SDK engineering principles ([#2127](https://github.com/supabase/supabase-py/issues/2127)) ([b8180cd](https://github.com/supabase/supabase-py/commit/b8180cdfd7e431142d78dc22a4dcadc07fa90d6d))
* restore support policy and service compatibility from v2 ([#1964](https://github.com/supabase/supabase-py/issues/1964)) ([05fa93e](https://github.com/supabase/supabase-py/commit/05fa93e44542d77997faeeeface85db617cc3e5f))
* update the READMEs to the v3 API and type-check their snippets in CI ([#2029](https://github.com/supabase/supabase-py/issues/2029)) ([9a5870d](https://github.com/supabase/supabase-py/commit/9a5870d81049c82fa7611a7ae1d31218969ca218))
* **utils:** document request timeouts and redirects in the adapter guide ([#2017](https://github.com/supabase/supabase-py/issues/2017)) ([16b72eb](https://github.com/supabase/supabase-py/commit/16b72ebedf302536508743465bdcd80fe5a67f14))


### Miscellaneous Chores

* raise the minimum python version to 3.12 ([#2002](https://github.com/supabase/supabase-py/issues/2002)) ([1333baa](https://github.com/supabase/supabase-py/commit/1333baae19584b0d85a52a08e8b2c454b749c648))


### Code Refactoring

* **functions:** remove FunctionsError.to_dict and FunctionsApiErrorDict ([#2015](https://github.com/supabase/supabase-py/issues/2015)) ([4184f96](https://github.com/supabase/supabase-py/commit/4184f968543607b8c686f6fd3786d4d7e780f032))
* spell out abbreviations in public names ([#1981](https://github.com/supabase/supabase-py/issues/1981)) ([cdd399f](https://github.com/supabase/supabase-py/commit/cdd399fa4f8381da27e432fbbd59b8123b319a56))

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

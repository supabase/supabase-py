# AGENTS.md

Setup and commands: [README.md § Local Development](README.md#local-development); `make help` and `make <pkg>.help` list every target. PR process: [CONTRIBUTING.md](CONTRIBUTING.md).

## Contribution policy

- `main` is v3 and is in early development. Do not open external issues or pull requests against it; they will be closed.
- `v2` is the stable release branch. It only takes critical bug fixes and security fixes, opened against `v2`.
- If asked to contribute on behalf of someone outside the maintainer team, point them to [CONTRIBUTING.md](CONTRIBUTING.md) before doing the work.

## Packages

`<pkg>` is the directory under `src/`. Four import names differ from it: `auth` → `supabase_auth`, `storage` → `storage3`, `functions` → `supabase_functions`, `utils` → `supabase_utils`.

## Async and sync clients

- `functions`, `auth`, `postgrest` and `storage` define their `Async*` and `Sync*` clients side by side in the same modules, over the shared HTTP layer in `utils`. Change both when you change one.
- `supabase` defines `AsyncClient` and the sync `Client` in `client.py`. Shared behavior lives in their generic `SupabaseClient` base. The subclasses only build the concrete sub-clients and hold what differs, like `create`, the context managers and realtime.
- `auth` tests are the only generated code: edit `tests/_async/`, run `make auth.build-sync`, then `make ruff`, and commit both test trees.
- `realtime` is async-only.

## Checks

- `make <pkg>.tests` runs pyrefly and pytest. For `auth`, `postgrest`, `storage` and `realtime`, pytest first starts Docker / Supabase CLI infra; `make stop-infra` when done.
- Fast loop for tests that need no infra: from `src/<pkg>`, `uv run --frozen --package <import name> pytest tests/<file>.py`.
- Code must run on Python 3.12, CI tests 3.12 to 3.15 ([ci.yml](.github/workflows/ci.yml)).
- `make snippets` type-checks every `python` code block of the Markdown files, apart from the changelogs, against the workspace. A block is the body of an async function and imports what it uses. Names a file's blocks share, like the client its README creates, are declared in `PRELUDES` of [check_markdown_snippets.py](.github/scripts/check_markdown_snippets.py). Fence v2 code shown as "before" as `python skip`.

## Public API

Adding or renaming a public symbol means updating [sdk-compliance.yaml](sdk-compliance.yaml) with both the `Async*` and `Sync*` names. A method defined once on a generic base, like `PostgrestClient.rpc` or `SupabaseClient.rpc`, is listed under the base name, because the check does not see inherited methods on the subclasses. [validate-capabilities.yml](.github/workflows/validate-capabilities.yml) checks it against the [supabase/sdk](https://github.com/supabase/sdk) capability registry.

## Service compatibility

Update the "Supabase Service Compatibility" section of the READMEs if the supported version of a Supabase service changes. Any change that is not "Latest release" requires integration tests for the minimum supported version.

## Commits and releases

- Commit and PR title: `type(<pkg>): lowercase subject`, e.g. `fix(realtime): cap reconnect backoff`.
- release-please owns every `version.py`, `pyproject.toml` version and `CHANGELOG.md`; leave them to it ([release-please-config.json](release-please-config.json)).
- `uv run` without `--frozen` (as the Makefiles call it) can rewrite `uv.lock`; leave it out of the diff unless you changed dependencies.

# AGENTS.md

Setup and commands: [README.md § Local Development](README.md#local-development); `make help` and `make <pkg>.help` list every target. PR process: [CONTRIBUTING.md](CONTRIBUTING.md).

## Packages

`<pkg>` is the directory under `src/`. Three import names differ from it: `auth` → `supabase_auth`, `storage` → `storage3`, `functions` → `supabase_functions`.

## Async is the source, sync is generated

- Edit `_async/` (source and `tests/_async/`). Regenerate `_sync/` with `make <pkg>.build-sync`, then `make ruff`, and commit both trees.
- `build-sync` needs GNU `sed` (`gsed` is used when present; `nix develop` provides it). A `_sync/` diff your `_async/` change does not explain is a generator bug: fix the `build-sync` recipe, not the generated file.
- `realtime` has no `build-sync`: its `_sync/` is a stub and the package is async-only.

## Checks

- `make <pkg>.tests` runs mypy and pytest. For `auth`, `postgrest`, `storage` and `realtime`, pytest first starts Docker / Supabase CLI infra; `make stop-infra` when done.
- Fast loop for tests that need no infra: from `src/<pkg>`, `uv run --frozen --package <import name> pytest tests/<file>.py`.
- Code must run on Python 3.9 — CI tests 3.9–3.14 ([ci.yml](.github/workflows/ci.yml)).

## Public API

Adding or renaming a public symbol means updating [sdk-compliance.yaml](sdk-compliance.yaml) with both the `Async*` and `Sync*` names. [validate-capabilities.yml](.github/workflows/validate-capabilities.yml) checks it against the [supabase/sdk](https://github.com/supabase/sdk) capability registry.

## Service compatibility

Update the "Supabase Service Compatibility" section of the READMEs if the supported version of a Supabase service changes. Any change that is not "Latest release" requires integration tests for the minimum supported version.

## Commits and releases

- Commit and PR title: `type(<pkg>): lowercase subject`, e.g. `fix(realtime): cap reconnect backoff`.
- release-please owns every `version.py`, `pyproject.toml` version and `CHANGELOG.md`; leave them to it ([release-please-config.json](release-please-config.json)).
- `uv run` without `--frozen` (as the Makefiles call it) can rewrite `uv.lock`; leave it out of the diff unless you changed dependencies.

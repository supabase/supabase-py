# AGENTS.md

Setup and commands: [README.md § Local Development](README.md#local-development); `make help` and `make <pkg>.help` list every target. PR process: [CONTRIBUTING.md](CONTRIBUTING.md).

## Packages

`<pkg>` is the directory under `src/`. Four import names differ from it: `auth` → `supabase_auth`, `storage` → `storage3`, `functions` → `supabase_functions`, `utils` → `supabase_utils`.

## Async and sync clients

- `functions`, `auth`, `postgrest` and `storage` define their `Async*` and `Sync*` clients side by side in the same modules, over the shared HTTP layer in `utils`. Change both when you change one.
- `supabase` keeps hand-written `_async/` and `_sync/` clients. Edit both.
- `auth` tests are the only generated code: edit `tests/_async/`, run `make auth.build-sync`, then `make ruff`, and commit both test trees.
- `realtime` is async-only.

## Checks

- `make <pkg>.tests` runs mypy and pytest. For `auth`, `postgrest`, `storage` and `realtime`, pytest first starts Docker / Supabase CLI infra; `make stop-infra` when done.
- Fast loop for tests that need no infra: from `src/<pkg>`, `uv run --frozen --package <import name> pytest tests/<file>.py`.
- Code must run on Python 3.10 — CI tests 3.10–3.14 ([ci.yml](.github/workflows/ci.yml)).

## Public API

Adding or renaming a public symbol means updating [sdk-compliance.yaml](sdk-compliance.yaml) with both the `Async*` and `Sync*` names. [validate-capabilities.yml](.github/workflows/validate-capabilities.yml) checks it against the [supabase/sdk](https://github.com/supabase/sdk) capability registry.

## Commits and releases

- Commit and PR title: `type(<pkg>): lowercase subject`, e.g. `fix(realtime): cap reconnect backoff`.
- release-please owns every `version.py`, `pyproject.toml` version and `CHANGELOG.md`; leave them to it ([release-please-config.json](release-please-config.json)).
- `uv run` without `--frozen` (as the Makefiles call it) can rewrite `uv.lock`; leave it out of the diff unless you changed dependencies.

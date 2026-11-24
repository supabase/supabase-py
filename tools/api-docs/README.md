# API docs

Generates the API docs definitions that supabase.com/docs reads: one Markdown file for each
function and method that can be imported by public names, with a docstring or without one, written
to `docs/api-docs/definitions`. Git ignores that folder.

The file name is the `id` of the definition, and it is made from the code alone: the import path
of the function, in lowercase words. `storage3.StorageFileApiClient.upload` is
`storage3-storage-file-api-client-upload`. Renaming a function or its class, or changing where its
package exports it, changes the id, and with it the address of the page on the docs site.

This folder holds no logic. The generator and the check are the `@supabase/doc-generator` and
`@supabase/doc-check` packages of [supabase/sdk](https://github.com/supabase/sdk), shared by every
SDK. What is specific to supabase-py is in [`doc-generator.config.mjs`](doc-generator.config.mjs).

> **Prototype.** The two packages are not on npm yet. `package.json` links them from a checkout of
> supabase/sdk next to this repository, on its `feature/doc-generator` branch.

## Setup

Needs git, bun and npm. Run the commands from the root of this repository.

```bash
# 1. Check out supabase/sdk next to this repository, as ../sdk, on the branch with the packages:
git clone --branch feature/doc-generator https://github.com/supabase/sdk.git ../sdk

# 2. Build the two packages there, once and after every change there:
(cd ../sdk/packages/doc-check && bun install && bun run build)
(cd ../sdk/packages/doc-generator && bun install && bun run build)

# 3. Link them into this folder, once:
npm install --prefix tools/api-docs
```

`npm install` fails until steps 1 and 2 are done. To get the newest commit of the branch, run
`git -C ../sdk pull` and step 2 again.

With a checkout of supabase/sdk that you already have, skip the clone:

- **At `../sdk`:** switch it to the branch with `git -C ../sdk switch feature/doc-generator`.
- **Somewhere else:** link it with `ln -s <absolute path of your checkout> ../sdk`.

The checkout is an ordinary one. To work on the two packages, change them there and build them
again.

## Commands

```bash
make api-docs        # dump the API with griffe, generate, then check
make api-docs-check  # only check the definitions that are there
```

Generating needs uv and Node. Checking needs only Node.

griffe is a dependency of this repository like ruff and pytest: the `api-docs` group in the root
[`pyproject.toml`](../../pyproject.toml) names it, [`uv.lock`](../../uv.lock) holds its version,
and `uv run` runs it on the Python of the project's environment. It reads the source without
importing it, so the packages do not have to be installed. The group is not installed by default.

### Options

make keeps the options on its command line for itself, so the options of the two tools go through
one variable each, the same two in every SDK. make hands them on as written:

| Variable        | Goes to         | Taken by                                 |
| --------------- | --------------- | ---------------------------------------- |
| `GENERATE_ARGS` | `doc-generator` | `make api-docs`, `make api-docs-preview` |
| `CHECK_ARGS`    | `doc-check`     | All three targets                        |

```bash
make api-docs GENERATE_ARGS="--verbose"
make api-docs GENERATE_ARGS="--verbose" CHECK_ARGS="--schema-url https://example.com/definition.schema.json"
```

A tool rejects an option it does not know: it prints its usage and exits with code 2, which stops
the run. The options of each tool are in its README in supabase/sdk:

- `doc-generator`: [Options](https://github.com/supabase/sdk/blob/main/packages/doc-generator/README.md#options) in `packages/doc-generator/README.md`
- `doc-check`: [Which schema](https://github.com/supabase/sdk/blob/main/packages/doc-check/README.md#which-schema) in `packages/doc-check/README.md`

The check uses the schema bundled with `@supabase/doc-check`. To check against the schema the docs
team has now, give it a URL, or a file in Git at a branch or a full commit SHA:

```bash
make api-docs-check CHECK_ARGS="--schema-git https://github.com/supabase/supabase.git \
  --schema-ref jeremias/reference-beta \
  --schema-path apps/docs/content/reference-beta/definition.schema.json"

make api-docs-check CHECK_ARGS="--schema-url https://example.com/definition.schema.json"
```

## Preview on the docs site

To see the definitions as supabase.com will show them, the preview copies them into a local
checkout of [supabase/supabase](https://github.com/supabase/supabase), starts the docs site there
(`pnpm dev:docs`) and opens the page in your browser. The checkout has to be on a branch that has
the new reference pages. Today that is the docs team's `jeremias/reference-beta`.

```bash
make api-docs-preview DOCS=../supabase   # generate, check, copy, then serve
# Starts the docs site, then opens http://localhost:3001/docs/reference-beta/python. Ctrl-C stops it.
```

When the docs site already runs, the preview only opens the page. The first start of the docs
site takes a while, and needs `pnpm install` in the checkout first.

The preview replaces the definitions of the preview before. It writes a placeholder introduction
page the first time and never overwrites one, so that page can be edited in the docs checkout.
The docs checkout ignores the copied definitions in Git.

## Editing

The definitions are generated files: change the docstring, then run `make api-docs` again. Never
edit them by hand.

A function without a docstring gets a definition too, with its signature and types and an empty
summary. `make api-docs` says how many there are, and this lists them:

```bash
make api-docs GENERATE_ARGS="--verbose"
```

Strict mode turns each of them into an error: the run then fails until every public function has
a docstring or is left out with `exclude`. `strict: true` in the config turns it on for every
run, `make api-docs GENERATE_ARGS="--strict"` for one. It is off here, because 228 public
functions have no docstring yet.

What is public follows Python's own rules: the names in `__all__` when a module has one, and
otherwise every name that does not start with an underscore. To leave a function out,
add `exclude` to [`doc-generator.config.mjs`](doc-generator.config.mjs): regular expressions
matched against import paths such as `supabase_auth.AsyncSupabaseAuthClient.sign_up`.
`"^supabase_auth\\.AsyncSupabaseAuthClient\\."` leaves out the methods of the async auth client.

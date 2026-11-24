.PHONY: ci, default, clean, start-infra, stop-infra, api-docs, api-docs-check, api-docs-preview

PACKAGES := utils functions realtime storage auth postgrest supabase
FORALL_PKGS = $(foreach pkg, $(PACKAGES), $(pkg).$(1))

help::
	@echo "Available commands"
	@echo "  help           -- (default) print this message"

ci: ruff snippets $(call FORALL_PKGS,tests)
help::
	@echo "  ci             -- Run tests for all packages, the same way as CI does"

clean: $(call FORALL_PKGS,clean)
	rm -rf dist .ruff_cache .pytest_cache
help::
	@echo "  clean          -- Delete cache files and coverage reports from tests"

publish: $(call FORALL_PKGS,build)
	uv publish

# not all packages have infra, so just manually instantiate the ones that do for now
start-infra: realtime.start-infra storage.start-infra auth.start-infra postgrest.start-infra
help::
	@echo "  start-infra    -- Start all containers necessary for tests."
	@echo "                    NOTE: it is not necessary to this command before running CI tests"

stop-infra: realtime.stop-infra storage.stop-infra auth.stop-infra postgrest.stop-infra
help::
	@echo "  stop-infra     -- Stop all infra used by tests."
	@echo "                    NOTE: run this command to ensure all containers are stopped after tests"

snippets:
	uv run --all-packages --all-extras python .github/scripts/check_markdown_snippets.py
help::
	@echo "  snippets       -- Type-check the Python snippets of the Markdown files"

pyrefly: $(call FORALL_PKGS,pyrefly)
help::
	@echo "  pyrefly        -- Run pyrefly on all packages"

API_DOCS := tools/api-docs
# griffe is the `api-docs` dependency group of pyproject.toml: uv.lock holds its version, and it runs
# on the Python of the project's environment. It reads the source without importing it, so it needs
# only that group, not the packages.
GRIFFE := uv run --only-group api-docs griffe
IMPORT_NAMES := supabase_utils supabase_functions realtime storage3 supabase_auth postgrest supabase

# make keeps the options on its command line for itself, so each tool gets its own through one
# variable, passed on as written: the same two variables in every SDK. Every target that runs the
# tool takes it, and a new option of a tool needs no change here.
#   GENERATE_ARGS  options of doc-generator:  make api-docs GENERATE_ARGS="--verbose"
#   CHECK_ARGS     options of doc-check:      make api-docs CHECK_ARGS="--schema-url <url>"
# Each target prints the options it passes on before it runs, so the output records them.
show-args = $(info $(1) ($(2)): $(or $(strip $($(1))),none))

api-docs:
	$(call show-args,GENERATE_ARGS,doc-generator)
	$(call show-args,CHECK_ARGS,doc-check)
	@mkdir -p $(API_DOCS)/build
	$(GRIFFE) dump --full --docstyle google --resolve-aliases \
		$(foreach pkg,$(PACKAGES),--search src/$(pkg)/src) \
		--output $(API_DOCS)/build/griffe.json $(IMPORT_NAMES)
	@npm --prefix $(API_DOCS) run --silent generate -- $(GENERATE_ARGS)
	@npm --prefix $(API_DOCS) run --silent check -- $(CHECK_ARGS)
help::
	@echo "  api-docs -- Generate the API docs definitions for supabase.com/docs and check them"
	@echo "              (GENERATE_ARGS=\"...\" and CHECK_ARGS=\"...\" pass options to the generator and the check)"

# The default schema is the one bundled with doc-check. Its options pick another:
#   make api-docs-check CHECK_ARGS="--schema-url <url>"
#   make api-docs-check CHECK_ARGS="--schema-git <repository> --schema-ref <ref> --schema-path <path>"
api-docs-check:
	$(call show-args,CHECK_ARGS,doc-check)
	@npm --prefix $(API_DOCS) run --silent check -- $(CHECK_ARGS)
help::
	@echo "  api-docs-check -- Check the API docs definitions against the docs schema (CHECK_ARGS=\"...\")"

# DOCS is a local checkout of supabase/supabase, on a branch that has the new reference pages:
#   make api-docs-preview DOCS=../supabase
# It then starts the docs site there (pnpm dev:docs), unless it already runs, and opens the page.
api-docs-preview:
	@test -d "$(DOCS)" || { echo "usage: make api-docs-preview DOCS=<checkout of supabase/supabase>" >&2; exit 2; }
	@$(MAKE) --no-print-directory api-docs
	@npm --prefix $(API_DOCS) run --silent preview -- "$(abspath $(DOCS))"
help::
	@echo "  api-docs-preview -- Generate the API docs definitions and copy them into a local docs checkout (DOCS=<path>)"

ruff:
	@uv run ruff check --fix
	@uv run ruff format
	@uv run python .github/scripts/check_docstrings.py
	@uv run pydoclint --quiet src/*/src
help::
	@echo "  ruff           -- Run ruff checks on all files, and check that docstrings are in Google style and match their signatures."

define COMMITIZEN_HOOK_CONTENTS
#!/bin/sh
MSG_FILE=$$1
uv tool run --from commitizen cz check --allow-abort --commit-msg-file $$MSG_FILE
endef
export COMMITIZEN_HOOK_CONTENTS
install-hooks:
	@echo "make ruff" > .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "$$COMMITIZEN_HOOK_CONTENTS" > .git/hooks/commit-msg
	@chmod +x .git/hooks/commit-msg
help::
	@echo "  install-hooks  -- Install custom pre-commit hooks locally."
	@echo "                 -- NOTE: Do this at least once after cloning the repo."

realtime.%:
	@$(MAKE) -C src/realtime $*

utils.%:
	@$(MAKE) -C src/utils $*

functions.%:
	@$(MAKE) -C src/functions $*

storage.%:
	@$(MAKE) -C src/storage $*

auth.%:
	@$(MAKE) -C src/auth $*

postgrest.%:
	@$(MAKE) -C src/postgrest $*

supabase.%:
	@$(MAKE) -C src/supabase $*

help::
	@echo
	@echo "Package specific commands can be ran by prefixing the command with the package name. Examples:"
	@echo "  realtime.pyrefly -- runs realtime's pyrefly target"
	@echo "  supabase.build -- runs supabase's build target"

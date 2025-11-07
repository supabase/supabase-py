.PHONY: ci, default, clean, start-infra, stop-infra

PACKAGES := functions realtime storage auth postgrest supabase
FORALL_PKGS = $(foreach pkg, $(PACKAGES), $(pkg).$(1))

help::
	@echo "Available commands"
	@echo "  help           -- (default) print this message"

ci: ruff $(call FORALL_PKGS,tests)
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

mypy: $(call FORALL_PKGS,mypy)
help::
	@echo "  mypy          -- Run mypy on all files"

ruff:
	@uv run ruff check --fix
	@uv run ruff format
help::
	@echo "  ruff           -- Run ruff checks on all files."

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
	@echo "  realtime.mypy  -- runs relatime's mypy target"
	@echo "  supabase.build -- runs supabase's build target"

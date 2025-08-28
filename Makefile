.PHONY: ci, default, pre-commit, clean, start-infra, stop-infra

PACKAGES := functions realtime storage auth postgrest supabase
FORALL_PKGS = $(foreach pkg, $(PACKAGES), $(pkg).$(1))

help::
	@echo "Available commands"
	@echo "  help           -- (default) print this message"

ci: pre-commit $(call FORALL_PKGS,tests)
help::
	@echo "  ci             -- Run tests for all packages, the same way as CI does"

pre-commit:
	uv run pre-commit run --all-files
help::
	@echo "  pre-commit     -- Run pre-commit on all files"

clean: $(call FORALL_PKGS,clean)
	rm -rf dist .ruff_cache .pytest_cache
help::
	@echo "  clean          -- Delete cache files and coverage reports from tests"

publish: $(call FORALL_PKGS,build)
	uv publish

# not all packages have infra, so just manually instantiate the ones that do for now
start-infra: realtime.start-infra storage.start-infra auth.start-infra postgrest.start-infra
help::
	@echo "  start-infra    -- Start all containers necessary for tests. NOTE: it is not necessary to this before running CI tests, they start the infra by themselves"
stop-infra: realtime.stop-infra storage.stop-infra auth.stop-infra postgrest.stop-infra
help::
	@echo "  stop-infra     -- Stop all infra used by tests. NOTE: tests do leave their infra running, so run this to ensure all containers are stopped"


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

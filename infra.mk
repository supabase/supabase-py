# Start test infrastructure, retrying after cleaning up a partial start.
# A failed start can leave containers holding host ports, which makes every
# following attempt fail with "address already in use".
#
# $(call retry_start_infra,<cleanup command>,<start command>)
INFRA_START_ATTEMPTS := 3

define retry_start_infra
attempt=1; \
while true; do \
	$(1); \
	if $(2); then sleep 2; exit 0; fi; \
	if [ $$attempt -ge $(INFRA_START_ATTEMPTS) ]; then \
		$(1); \
		echo "Starting infrastructure failed after $(INFRA_START_ATTEMPTS) attempts" >&2; \
		exit 1; \
	fi; \
	delay=$$((attempt * 20)); \
	echo "Starting infrastructure failed (attempt $$attempt/$(INFRA_START_ATTEMPTS)), retrying in $${delay}s"; \
	sleep $$delay; \
	attempt=$$((attempt + 1)); \
done
endef

# $(call supabase_cleanup,<project id>)
supabase_cleanup = supabase --workdir infra stop --no-backup >/dev/null 2>&1 || true; \
	docker ps -aq --filter "label=com.supabase.cli.project=$(1)" | xargs docker rm -f >/dev/null 2>&1 || true

compose_cleanup = (cd infra && docker compose down --remove-orphans >/dev/null 2>&1) || true

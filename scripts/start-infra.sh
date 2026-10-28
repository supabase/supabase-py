#!/usr/bin/env bash
# Start test infrastructure, surviving throttled registries and half-started containers.
#
# Usage, from a package directory:
#   start-infra.sh supabase <project id> <excluded services>
#   start-infra.sh compose
set -uo pipefail

mode="$1"
attempts=4
registries=("" "ghcr.io" "docker.io" "")

cleanup() {
  case "$mode" in
    supabase)
      supabase --workdir infra stop --no-backup >/dev/null 2>&1 || true
      leftovers="$(docker ps -aq --filter "label=com.supabase.cli.project=$2")"
      if [ -n "$leftovers" ]; then
        # shellcheck disable=SC2086
        docker rm -f $leftovers >/dev/null 2>&1 || true
      fi
      ;;
    compose)
      (cd infra && docker compose down --remove-orphans >/dev/null 2>&1) || true
      ;;
  esac
}

start() {
  case "$mode" in
    supabase) supabase --workdir infra start -x "$3" ;;
    compose) (cd infra && docker compose up -d) ;;
  esac
}

for attempt in $(seq 1 "$attempts"); do
  cleanup "$@"
  registry="${registries[$((attempt - 1))]}"
  if [ -n "$registry" ]; then
    echo "Attempt $attempt/$attempts using image registry $registry"
    export SUPABASE_INTERNAL_IMAGE_REGISTRY="$registry"
  else
    echo "Attempt $attempt/$attempts using the default image registry"
    unset SUPABASE_INTERNAL_IMAGE_REGISTRY
  fi
  if start "$@"; then
    sleep 2
    exit 0
  fi
  if [ "$attempt" -lt "$attempts" ]; then
    delay=$((attempt * 20))
    echo "Starting infrastructure failed, retrying in ${delay}s"
    sleep "$delay"
  fi
done

cleanup "$@"
echo "Starting infrastructure failed after $attempts attempts" >&2
exit 1

#!/usr/bin/env bash
# Start test infrastructure, retrying after cleaning up a partial start.
#
# A failed start can leave containers holding host ports, which makes every
# following attempt fail with "address already in use".
#
# Usage, from a package directory:
#   start-infra.sh supabase <project id> <excluded services>
#   start-infra.sh compose
set -uo pipefail

mode="$1"
attempts=3

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
  if start "$@"; then
    sleep 2
    exit 0
  fi
  if [ "$attempt" -lt "$attempts" ]; then
    delay=$((attempt * 20))
    echo "Starting infrastructure failed (attempt $attempt/$attempts), retrying in ${delay}s"
    sleep "$delay"
  fi
done

cleanup "$@"
echo "Starting infrastructure failed after $attempts attempts" >&2
exit 1

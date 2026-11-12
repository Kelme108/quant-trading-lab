#!/bin/sh
# Keeps every ACTIVE dry-run bot running. Every WATCHDOG_INTERVAL seconds (default 300) it checks each bot that has a freeze
# record in research/forward/H-*-freeze.json and, when fewer containers run than its compose file defines, starts them with
# `docker compose -f <file> up -d`. It only STARTS containers from the existing compose files: it edits nothing, so the freeze
# hashes stay valid. Retired bots (their freeze moved to research/forward/retired/) are never restarted.
# After a start it sets the Docker restart policy to `unless-stopped` with `docker update`, which changes the container only,
# not the compose file (changing the file would break the freeze). So Docker itself brings the bots back after a reboot.
# Kill switch: while ops/state/STOP.forward exists (written by ops/freqtrade_guard.py or by hand) nothing is started.
# No exchange keys, no real money: the forward bots are dry-run only.
APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
INTERVAL="${WATCHDOG_INTERVAL:-300}"
LOG="$APP_DIR/ops/state/watchdog.log"
mkdir -p "$APP_DIR/ops/state"
cd "$APP_DIR" || exit 1
log() { echo "$(date -u '+%F %T') UTC $*" >> "$LOG"; }

while true; do
  if ! docker info >/dev/null 2>&1; then
    log "docker is not answering (is the docker service up?)"
  elif [ -f ops/state/STOP.forward ]; then
    log "ops/state/STOP.forward exists: nothing started"
  else
    for freeze in research/forward/H-*-freeze.json; do
      [ -f "$freeze" ] || continue
      tag=$(basename "$freeze" -freeze.json | sed 's/^H-/h/')
      compose="docker-compose.forward.$tag.yml"
      [ -f "$compose" ] || { log "$freeze has no $compose"; continue; }
      want=$(docker compose -f "$compose" config --services 2>/dev/null | wc -l)
      have=$(docker compose -f "$compose" ps -q --status running 2>/dev/null | wc -l)
      if [ "$have" -lt "$want" ]; then
        log "$compose: $have/$want running -> up -d"
        docker compose -f "$compose" up -d >> "$LOG" 2>&1
      fi
      ids=$(docker compose -f "$compose" ps -q 2>/dev/null)
      [ -n "$ids" ] && docker update --restart unless-stopped $ids >/dev/null 2>&1
    done
  fi
  sleep "$INTERVAL"
done

#!/bin/sh
# The continuous research loop: cycle after cycle of `python -m lab.pipeline weekly`, then the dry-run verdicts (which also
# retire bots that did not trade for 2 days), and the sources refresh every 4th cycle. This is what spends agent money
# (lab/config/budget.json: 4 USD per agent call, 60 USD per cycle), so start it only on purpose.
#
# Stop it cleanly:   touch ops/state/STOP_CYCLES     (checked BETWEEN cycles; a running cycle is never cut)
# A cycle that ends STOPPED (guard violation, budget) pauses 10 minutes; three STOPPED in a row end the loop.
# IMPORTANT: while this runs, do not edit files in the repository by hand. The guard (lab/guard.py) aborts a cycle when
# something outside an agent's allowed paths changes during its step. Stop the loop first, edit, start it again.
APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$APP_DIR" || exit 1
mkdir -p ops/state
# the project's venv first: the agents run `python -m unittest`, so `python` must exist and be the venv's
[ -x "$APP_DIR/.venv/bin/python" ] && PATH="$APP_DIR/.venv/bin:$PATH"
export PATH PYTHONIOENCODING=utf-8
PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
command -v claude >/dev/null 2>&1 || { echo "the claude CLI is not on PATH (see docs/migracao-linux.md, section 8)"; exit 1; }

STOP="ops/state/STOP_CYCLES"
LOG="ops/state/loop-$(date -u +%Y%m%dT%H%M%S).log"
SCOUT_COUNT="${SCOUT_COUNT:-10}"
MAX_NEW="${MAX_NEW:-10}"
rm -f "$STOP"
i=0; stops=0
while [ ! -f "$STOP" ]; do
  i=$((i+1))
  echo "=== cycle $i $(date -u)" >> "$LOG"
  "$PY" -m lab.pipeline weekly --scout-count "$SCOUT_COUNT" --max-new "$MAX_NEW" >> "$LOG" 2>&1
  "$PY" -m lab.pipeline dryrun >> "$LOG" 2>&1
  [ $((i % 4)) -eq 1 ] && "$PY" -m lab.pipeline sources >> "$LOG" 2>&1
  report=$(ls -t research/pipeline/cycle-*.md | head -1)
  grep -E "Outcome|spend|^\| (I-|-)" "$report" | cut -c1-400 >> "$LOG"
  if grep -q "Outcome: STOPPED" "$report"; then
    stops=$((stops+1))
    [ "$stops" -ge 3 ] && { echo "three STOPPED cycles in a row: ending" >> "$LOG"; break; }
    sleep 600
  else
    stops=0
  fi
done
echo "loop ended after $i cycle(s); log $LOG"

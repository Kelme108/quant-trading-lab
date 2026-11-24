#!/usr/bin/env bash
# Gravador de ticks de WIN e WDO, só leitura (equivale a ops/windows/tick-recorder.cmd). Salva os ticks em
# user_data/data/b3/clear/ticks/ e depois refaz as barras de fluxo de 1 minuto (b3/tick_search.py) no Python nativo.
# Precisa do terminal da Clear aberto e logado na DEMO. Não envia ordem. Agendado por trade-tick-recorder.timer.
set -uo pipefail
. "$(dirname "$0")/env.sh"
cd "$ROOT"
mkdir -p live/logs
LOG=live/logs/tick-recorder.log
echo "==== $(date '+%F %T') start" >> "$LOG"
wpy -m b3.data.tick_recorder >> "$LOG" 2>&1
"$PY" -m b3.tick_search bars --market WIN >> "$LOG" 2>&1
"$PY" -m b3.tick_search bars --market WDO >> "$LOG" 2>&1
echo "==== $(date '+%F %T') exit $?" >> "$LOG"

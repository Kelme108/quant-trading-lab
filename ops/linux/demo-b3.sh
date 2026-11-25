#!/usr/bin/env bash
# Robôs de DEMONSTRAÇÃO na conta demo da Clear (equivale a ops/windows/demo-b3.cmd). NÃO é evidência.
#
#   ops/linux/demo-b3.sh demo-b3-p032-win            # liga um robô (live/config/<nome>.json) em segundo plano
#   ops/linux/demo-b3.sh demo-b3-p032-win --foreground   # sem soltar (é assim que o systemd chama: trade-demo@.service)
#   ops/linux/demo-b3.sh --all                       # liga todos os live/config/demo-b3-*.json que ainda não rodam
#   ops/linux/demo-b3.sh --list                      # lista os robôs e se cada um está rodando
#
# Precisa do terminal da Clear aberto e logado na DEMO (ops/linux/mt5-terminal.sh clear). O robô roda no Python para
# Windows do Wine (só ele importa MetaTrader5), anexado ao terminal por b3/config/broker_mt5.json, sem senha.
# Parar: crie live/STOP (zera posições e não manda nada novo) ou mate o processo. Diário: live/journal.<nome>.sqlite.
# Robôs da conta REAL (live/config/live-*.json) não são ligados por este script.
set -euo pipefail
. "$(dirname "$0")/env.sh"
cd "$ROOT"

running() { pgrep -f -- "live.run --config live/config/$1.json" >/dev/null 2>&1; }

start_one() {   # start_one <nome> [--foreground]
  local name="$1" mode="${2:-}"
  case "$name" in demo-*) ;; *) echo "recusado: $name não é um robô de demo (só live/config/demo-*.json)"; return 1 ;; esac
  [ -f "live/config/$name.json" ] || { echo "não existe live/config/$name.json"; return 1; }
  if [ -f live/retirados.json ] && grep -q "\"$name\"" live/retirados.json; then echo "  retirado    $name (live/retirados.json)"; return 0; fi
  if running "$name"; then echo "  já rodando  $name"; return 0; fi
  mkdir -p live/logs
  local log="live/logs/$name-task.log"
  echo "==== $(date '+%F %T') start" >> "$log"
  if [ "$mode" = "--foreground" ]; then
    wpy -m live.run --config "live/config/$name.json" >> "$log" 2>&1 || true
    echo "==== $(date '+%F %T') exit" >> "$log"
    return 0
  fi
  nohup bash -c '. "$1"; wpy -m live.run --config "live/config/$2.json"; echo "==== $(date "+%F %T") exit $?"' \
      _ "$ROOT/ops/linux/env.sh" "$name" >> "$log" 2>&1 &
  echo "  ligado      $name (pid $!, log $log)"
}

case "${1:-}" in
  ""|-h|--help) sed -n '2,13p' "$0" ;;
  --list)
    for f in live/config/demo-*.json; do n="$(basename "$f" .json)"; running "$n" && s="rodando" || s="parado"; grep -qs "\"$n\"" live/retirados.json && s="retirado"; printf '  %-8s %s\n' "$s" "$n"; done ;;
  --all)
    [ -f live/STOP ] && echo "AVISO: live/STOP existe; os robôs vão zerar e não operar até você apagá-lo."
    for f in live/config/demo-b3-*.json; do start_one "$(basename "$f" .json)"; sleep 2; done ;;
  *) start_one "$1" "${2:-}" ;;
esac

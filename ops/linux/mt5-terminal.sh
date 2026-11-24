#!/usr/bin/env bash
# Abre um terminal MetaTrader 5 no Wine (equivale a abrir o atalho no Windows).
#
#   ops/linux/mt5-terminal.sh clear              # MT5 da Clear: é o que os robôs de demo, o histórico e o gravador de ticks usam
#   ops/linux/mt5-terminal.sh normal             # MT5 normal da MetaQuotes
#   ops/linux/mt5-terminal.sh clear --foreground # não solta o terminal (para systemd: trade-mt5-clear.service)
#
# Primeira vez: com tela, abra o da Clear, Arquivo > Abrir uma conta > servidor ClearInvestimentos-DEMO e entre com
# o login da DEMO, marcando "salvar senha". O terminal guarda o login; os robôs só se anexam a ele (nenhuma senha no
# repositório). Nunca use servidor com PRD/REAL no nome (docs/cerebro/Regras-inviolaveis.md).
# Sem tela (servidor), o terminal roda num X virtual (Xvfb) e reaproveita o login salvo antes.
set -euo pipefail
. "$(dirname "$0")/env.sh"

WHICH="${1:-clear}"; MODE="${2:-}"
case "$WHICH" in
  clear)  EXE="$CLEAR_TERMINAL" ;;
  normal) EXE="$MQ_TERMINAL" ;;
  *) echo "uso: $0 clear|normal [--foreground]"; exit 2 ;;
esac
[ -f "$EXE" ] || { echo "Terminal não instalado em $EXE. Rode: ops/linux/install.sh mt5"; exit 1; }

if pgrep -f "$(basename "$(dirname "$EXE")")/terminal64.exe" >/dev/null 2>&1; then
  echo "O terminal $WHICH já está aberto."
  [ "$MODE" = "--foreground" ] || exit 0
fi

mkdir -p "$ROOT/live/logs"
LOG="$ROOT/live/logs/mt5-$WHICH.log"
if [ "$MODE" = "--foreground" ]; then
  exec bash -c '. "$1"; wine_run "$2"' _ "$ROOT/ops/linux/env.sh" "$EXE" >>"$LOG" 2>&1
fi
nohup bash -c '. "$1"; wine_run "$2"' _ "$ROOT/ops/linux/env.sh" "$EXE" >>"$LOG" 2>&1 &
echo "Terminal $WHICH aberto (pid $!). Log: live/logs/mt5-$WHICH.log"

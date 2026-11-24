#!/usr/bin/env bash
# Um ciclo da esteira de famílias (equivale a ops/windows/esteira-cycle.cmd): o agente esteira-research escreve um lote,
# as checagens rodam, o lote é commitado antes de qualquer leitura e é triado na exploração. GASTA DINHEIRO DE AGENTE
# (teto diário em b3/config/esteira_b3.json). Agendado por trade-esteira.timer (de hora em hora), que só o dono liga.
# O ciclo recusa uma segunda cópia e se pausa após dois erros seguidos. Pausa manual: touch ops/state/STOP_ESTEIRA
set -uo pipefail
. "$(dirname "$0")/env.sh"
cd "$ROOT"
export PATH="$ROOT/.venv/bin:$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"   # python = o do .venv; claude do instalador nativo ou do npm
command -v claude >/dev/null 2>&1 || { echo "CLI claude não encontrado (ops/linux/install.sh claude)"; exit 1; }
mkdir -p ops/state
echo "==== $(date '+%F %T')" >> ops/state/esteira-cycle.log
"$PY" -m b3.esteira_cycle cycle --max 200 --minutes 50 >> ops/state/esteira-cycle.log 2>&1

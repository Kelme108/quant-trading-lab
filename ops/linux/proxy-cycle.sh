#!/usr/bin/env bash
# Um ciclo do pipeline de agentes na linha ativa (equivale a ops/windows/proxy-cycle.cmd). GASTA DINHEIRO DE AGENTE.
# O pipeline aplica os próprios limites e recusa uma segunda cópia. Pausa manual: touch ops/state/STOP_PROXY_CYCLES
set -uo pipefail
. "$(dirname "$0")/env.sh"
cd "$ROOT"
export PATH="$ROOT/.venv/bin:$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"
command -v claude >/dev/null 2>&1 || { echo "CLI claude não encontrado (ops/linux/install.sh claude)"; exit 1; }
mkdir -p ops/state
echo "==== $(date '+%F %T')" >> ops/state/proxy-cycle.log
"$PY" -m b3.proxy_pipeline cycle --max 1 >> ops/state/proxy-cycle.log 2>&1

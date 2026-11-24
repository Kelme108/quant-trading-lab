#!/usr/bin/env bash
# Portal somente leitura em http://127.0.0.1:8765 (Python nativo). De outra máquina: ssh -L 8765:127.0.0.1:8765 usuario@servidor
#   ops/linux/portal.sh          # abre o navegador se houver tela
#   ops/linux/portal.sh --no-open
set -euo pipefail
. "$(dirname "$0")/env.sh"
cd "$ROOT"
if [ "${1:-}" = "--no-open" ] || { [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; }; then
  exec "$PY" -m lab.dashboard serve
fi
exec "$PY" -m lab.dashboard serve --open

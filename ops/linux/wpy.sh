#!/usr/bin/env bash
# Roda qualquer comando do repositório no Python para Windows do Wine (o único que importa MetaTrader5), a partir da
# raiz do repositório. Exemplos:
#
#   ops/linux/wpy.sh -m b3.data.mt5_history symbols --attach b3/config/broker_mt5.json
#   ops/linux/wpy.sh -m b3.data.mt5_history download --attach b3/config/broker_mt5.json --symbols WIN\$N WDO\$N --timeframes M1 M5 M15
#   ops/linux/wpy.sh -m live.run --config live/config/demo-b3-p032-win.json --check
#   ops/linux/wpy.sh -m pip list
set -euo pipefail
. "$(dirname "$0")/env.sh"
wpy "$@"

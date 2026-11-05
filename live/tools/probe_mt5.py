"""Read-only probe of the local MetaTrader 5 terminal. Sends no orders.

Usage (terminal open and logged in):
    live/.venv/Scripts/python.exe live/tools/probe_mt5.py

Prints terminal build, account type (demo/real, netting/hedging, server) and,
for WIN/WDO symbols, the contract spec read from the server. Login/password
are never printed.
"""

from __future__ import annotations

import sys

import MetaTrader5 as mt5

MODES = {0: "DEMO", 1: "CONTEST", 2: "REAL"}
MARGIN = {0: "NETTING", 1: "EXCHANGE", 2: "HEDGING"}


def main() -> int:
    if not mt5.initialize():
        print("initialize() falhou:", mt5.last_error())
        print("Abra o terminal MT5, faça login e rode de novo.")
        return 1
    try:
        term, acc = mt5.terminal_info(), mt5.account_info()
        print(f"terminal: {term.name} build {term.build} | conectado={term.connected}")
        if acc is None:
            print("sem conta logada")
            return 1
        print(f"servidor: {acc.server} | empresa: {acc.company}")
        print(f"tipo: {MODES.get(acc.trade_mode, acc.trade_mode)} | "
              f"margem: {MARGIN.get(acc.margin_mode, acc.margin_mode)} | moeda: {acc.currency}")
        if acc.trade_mode == 2:
            print("ATENÇÃO: conta REAL. Este projeto só opera demo nesta fase.")
        for prefix in ("WIN", "WDO"):
            syms = mt5.symbols_get(f"{prefix}*") or ()
            names = sorted(s.name for s in syms)
            print(f"\n{prefix}: {len(names)} símbolos -> {names[:12]}")
            for s in syms[:3]:
                print(f"  {s.name}: tick={s.trade_tick_size} valor_tick={s.trade_tick_value} "
                      f"vol_min={s.volume_min} vol_step={s.volume_step} "
                      f"filling={s.filling_mode} modo={s.trade_mode}")
        if not (mt5.symbols_get("WIN*") or mt5.symbols_get("WDO*")):
            print("\nNenhum WIN/WDO: esta conta não serve para B3. Peça demo B3 à corretora.")
            return 2
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())

"""Limit (maker) orders on crypto perpetuals with 1-minute bars: fill rate and adverse selection.

Every `step` minutes a resting limit BUY is placed at close*(1-d) and a SELL at close*(1+d), valid for `wait`
minutes. Conservative fill rule (queue position unknown): a buy fills only when a later bar's LOW trades
strictly BELOW the limit by at least one price tick of 1e-5 relative (a trade-through), a sell when the HIGH
trades above it. Markout of a fill = the move from the limit price to the close `h` minutes after the fill bar,
in the order's favour (positive = good for the maker). The unconditional move over the same horizon is the
benchmark. Exploration data only (futures splits end 2024-07-04).

    python research/tools/maker_fill_sim.py [--pairs BTC,ETH,SOL]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "user_data" / "data" / "binance" / "futures"
EXPLORATION_END = pd.Timestamp("2024-07-04T19:00:00Z")
OFFSETS_BP = (0, 1, 3, 5, 10)
WAIT_MIN = (1, 5, 15)
HORIZONS = (1, 5, 15, 30)
MAKER_FEE, TAKER_FEE = 0.0002, 0.00045       # Binance USD-M, non-VIP; BNB discount applies to taker only


def load(pair: str) -> pd.DataFrame:
    df = pd.read_feather(DATA / f"{pair}_USDT_USDT-1m-futures.feather")
    df = df[df["date"] < EXPLORATION_END].reset_index(drop=True)
    return df


def simulate(df: pd.DataFrame, d_bp: float, wait: int, step: int = 5) -> dict:
    close, high, low = df["close"].to_numpy(), df["high"].to_numpy(), df["low"].to_numpy()
    n = len(df)
    idx = np.arange(0, n - wait - max(HORIZONS) - 1, step)
    d = d_bp / 1e4
    out = {}
    for side in ("buy", "sell"):
        price = close[idx] * ((1 - d) if side == "buy" else (1 + d))
        fill_bar = np.full(len(idx), -1)
        for k in range(1, wait + 1):
            j = idx + k
            hit = (low[j] < price * (1 - 1e-5)) if side == "buy" else (high[j] > price * (1 + 1e-5))
            fill_bar = np.where((fill_bar < 0) & hit, j, fill_bar)
        filled = fill_bar >= 0
        res = {"orders": int(len(idx)), "fill_rate": round(float(filled.mean()), 4)}
        sgn = 1.0 if side == "buy" else -1.0
        for h in HORIZONS:
            fb = fill_bar[filled]
            mark = sgn * (close[fb + h] / price[filled] - 1)
            base = sgn * (close[idx + h] / close[idx] - 1)
            res[f"markout_{h}m_bp"] = round(1e4 * float(mark.mean()), 3)
            res[f"unconditional_{h}m_bp"] = round(1e4 * float(base.mean()), 3)
        out[side] = res
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="BTC,ETH,SOL")
    ap.add_argument("--out", default=str(ROOT / "research/proxies/maker_fill_sim.json"))
    a = ap.parse_args()
    rows = []
    for pair in a.pairs.split(","):
        df = load(pair)
        print(f"{pair}: {len(df)} 1m bars {df['date'].iloc[0]} .. {df['date'].iloc[-1]}", flush=True)
        for d in OFFSETS_BP:
            for w in WAIT_MIN:
                r = simulate(df, d, w)
                rows.append({"pair": pair, "offset_bp": d, "wait_min": w, **r})
                b, s = r["buy"], r["sell"]
                print(f"  offset {d:>2}bp wait {w:>2}m: fill buy {b['fill_rate']:.2f} sell {s['fill_rate']:.2f} | "
                      f"markout after fill (bp) 1m {b['markout_1m_bp']:+.1f}/{s['markout_1m_bp']:+.1f} "
                      f"5m {b['markout_5m_bp']:+.1f}/{s['markout_5m_bp']:+.1f} "
                      f"30m {b['markout_30m_bp']:+.1f}/{s['markout_30m_bp']:+.1f}", flush=True)
    Path(a.out).write_text(json.dumps({"maker_fee": MAKER_FEE, "taker_fee": TAKER_FEE, "rows": rows}, indent=1),
                           encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

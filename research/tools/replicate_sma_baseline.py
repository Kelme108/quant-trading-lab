"""Independent re-simulation of SmaTrendBaseline (H-001) without Freqtrade.

Purpose: check the backtest engine and the harness, not the strategy. The same
rule is re-implemented in plain pandas and its trade list is compared with the
one Freqtrade exported. A systematic difference in entry/exit times or in the
per-trade profit would mean the harness or the engine does not do what the
documentation says.

Assumptions mirrored from Freqtrade: signals use closed candles and fill at the
next candle's open; the 10% stop is checked on every candle from the entry
candle on and fills at the stop price, or at the open when the candle gaps
below it; fee is charged on both sides; one position; whole balance.

Usage: python research/tools/replicate_sma_baseline.py <pair-file.feather> <export.zip> <fee> <start_unix> <end_unix>
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

STOP = 0.10


def fill_missing_candles(df: pd.DataFrame) -> pd.DataFrame:
    """Freqtrade's backtest fills a missing hourly candle with the previous close
    (open = high = low = close) and volume 0. Indicator windows then count the
    filled bars, and volume > 0 blocks any signal on them."""
    full = df.set_index("date").reindex(pd.date_range(df["date"].min(), df["date"].max(), freq="1h", tz="UTC"))
    full["close"] = full["close"].ffill()
    for col in ("open", "high", "low"):
        full[col] = full[col].fillna(full["close"])
    full["volume"] = full["volume"].fillna(0.0)
    full.index.name = "date"
    return full.reset_index()


def _close(pos: dict, row: pd.Series, exit_rate: float, reason: str, fee: float) -> dict:
    ratio = (exit_rate * (1 - fee)) / (pos["open_rate"] * (1 + fee)) - 1
    return {"open_date": pos["open_date"], "open_rate": pos["open_rate"], "close_date": row["date"],
            "close_rate": exit_rate, "profit_ratio": ratio, "exit_reason": reason}


def simulate(df: pd.DataFrame, fee: float, start: pd.Timestamp, end: pd.Timestamp, warmup: int = 200) -> pd.DataFrame:
    df = fill_missing_candles(df)
    fast, slow, regime = (df["close"].rolling(n).mean() for n in (20, 50, 200))
    entry = (fast > slow) & (fast.shift(1) <= slow.shift(1)) & (df["close"] > regime) & (df["volume"] > 0)
    exit_ = (fast < slow) & (fast.shift(1) >= slow.shift(1)) & (df["volume"] > 0)
    first = int(df.index[df["date"] >= start][0])
    # Freqtrade moves the start by startup_candle_count; nothing can trade before that.
    first = max(first, warmup)
    trades = []
    pos = None
    for i in range(first, len(df)):
        row = df.iloc[i]
        if row["date"] > end:
            break
        # 1) An open position is closed first. A pending exit signal fills at this candle's
        #    open, which comes before any intrabar stop; otherwise the stop is checked.
        if pos is not None and i > pos["i"]:
            stop_price = pos["open_rate"] * (1 - STOP)
            if exit_.iloc[i - 1]:
                exit_rate, reason = row["open"], "exit_signal"
            elif row["low"] <= stop_price:
                exit_rate, reason = min(stop_price, row["open"]), "stop_loss"
            else:
                exit_rate = None
            if exit_rate is not None:
                trades.append(_close(pos, row, exit_rate, reason, fee))
                pos = None
        # 2) A free slot may be filled at this open, even on the candle that just closed a trade.
        if pos is None and entry.iloc[i - 1]:
            pos = {"open_date": row["date"], "open_rate": row["open"], "i": i}
        # 3) The stop also applies on the entry candle itself.
        if pos is not None and i == pos["i"]:
            stop_price = pos["open_rate"] * (1 - STOP)
            if row["low"] <= stop_price:
                trades.append(_close(pos, row, min(stop_price, row["open"]), "stop_loss", fee))
                pos = None
    return pd.DataFrame(trades)


def load_export(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as archive:
        name = [n for n in archive.namelist() if n.endswith(".json") and not n.endswith("_config.json")][0]
        stats = list(json.load(archive.open(name))["strategy"].values())[0]
    out = pd.DataFrame(stats["trades"])
    out["open_date"] = pd.to_datetime(out["open_date"], utc=True)
    out["close_date"] = pd.to_datetime(out["close_date"], utc=True)
    return out


def main(argv: list[str]) -> int:
    feather, zip_path, fee, t0, t1 = argv[0], Path(argv[1]), float(argv[2]), int(argv[3]), int(argv[4])
    df = pd.read_feather(feather)
    mine = simulate(df, fee, pd.Timestamp(t0, unit="s", tz="UTC"), pd.Timestamp(t1, unit="s", tz="UTC"))
    theirs = load_export(zip_path)
    print(f"trades: replica={len(mine)} freqtrade={len(theirs)}")
    same_open = set(mine["open_date"]) & set(theirs["open_date"])
    print(f"same open_date: {len(same_open)} of {len(theirs)}")
    merged = mine.merge(theirs, on="open_date", suffixes=("_mine", "_ft"))
    same_close = (merged["close_date_mine"] == merged["close_date_ft"]).sum()
    diff = (merged["profit_ratio_mine"] - merged["profit_ratio_ft"]).abs()
    print(f"same close_date: {same_close} of {len(merged)}; profit_ratio abs diff max={diff.max():.2e} median={diff.median():.2e}")
    only_mine = sorted(set(mine["open_date"]) - set(theirs["open_date"]))
    only_ft = sorted(set(theirs["open_date"]) - set(mine["open_date"]))
    print("only in replica:", only_mine[:5], "\nonly in freqtrade:", only_ft[:5])
    bad = merged[merged["close_date_mine"] != merged["close_date_ft"]]
    if len(bad):
        print(bad[["open_date", "close_date_mine", "close_date_ft", "exit_reason_mine", "exit_reason_ft"]].head(8).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

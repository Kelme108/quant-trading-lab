"""Fidelity of b3/freqtrade_adapter.py: replay a strategy on BTC/USDT with the adapter (24-hour mode, the strategy's
own timeframe as the clock) and compare its trades with the lab's Freqtrade backtest export of the SAME strategy
file (the copy stored inside the export zip), the same timerange and the same fee.

    python research/tools/adapter_fidelity.py SessionHighBreakRetest_H124_v1 HourlyWilliamsVolBreakout_H043_v1 ...
    -> research/b3/adapter_fidelity.json

Match rules: an adapter trade matches a Freqtrade trade when both open on the same candle; the exit matches when it
is within one strategy candle. The plan's acceptance (docs/plano-b3-reuso.md F2): the trades coincide.
"""

from __future__ import annotations

import glob
import json
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from b3 import freqtrade_adapter as fa  # noqa: E402
from b3.backtest import BacktestConfig, run  # noqa: E402

OUT = ROOT / "research" / "b3" / "adapter_fidelity.json"
DATA = ROOT / "user_data" / "data" / "binance"


def latest_export(strategy: str, pair_slug: str = "btc-usdt") -> tuple[Path, dict, Path] | None:
    """Most recent exploration export of `strategy` on BTC with the lowest fee; (zip, strategy result, source copy)."""
    best = None
    for z in sorted(glob.glob(str(ROOT / "research" / "experiments" / f"*-exploration-{pair_slug}" / "raw" / "*.zip"))):
        with zipfile.ZipFile(z) as f:
            names = f.namelist()
            if not any(n.endswith(f"_{strategy}.py") for n in names):
                continue
            main = next(n for n in names if n.endswith(".json") and not n.endswith("_config.json"))
            res = json.loads(f.read(main))["strategy"].get(strategy)
            if not res or not res.get("trades"):
                continue
            fee = res["trades"][0].get("fee_open", 1.0)
            key = (Path(z).parent.parent.name[:16], -fee)
            if best is None or key > best[0]:
                best = (key, Path(z), res)
    if best is None:
        return None
    _, z, res = best
    tmp = Path(tempfile.mkdtemp(prefix="ftsrc_")) / f"{strategy}.py"
    with zipfile.ZipFile(z) as f:
        src = next(n for n in f.namelist() if n.endswith(f"_{strategy}.py"))
        tmp.write_bytes(f.read(src))
    return z, res, tmp


def load_candles(timeframe: str) -> pd.DataFrame:
    """Exchange candles with missing ones filled like Freqtrade's ohlcv_fill_up_missing_data (OHLC = previous
    close, volume 0), which every Freqtrade backtest applies."""
    df = pd.read_feather(DATA / f"BTC_USDT-{timeframe}.feather")
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.set_index("date")[["open", "high", "low", "close", "volume"]]
    full = pd.date_range(df.index.min(), df.index.max(), freq=f"{fa.tf_minutes(timeframe)}min", tz="UTC")
    df = df.reindex(full)
    close = df["close"].ffill()
    for c in ("open", "high", "low"):
        df[c] = df[c].fillna(close)
    df["close"], df["volume"] = close, df["volume"].fillna(0.0)
    return df.rename_axis("time").reset_index()


def compare(strategy: str) -> dict:
    found = latest_export(strategy)
    if found is None:
        return {"strategy": strategy, "error": "no BTC export with trades"}
    z, res, src = found
    fee = float(res["trades"][0]["fee_open"])
    rule = fa.make_crypto_rule(strategy, fee=fee, path=src)
    tf = fa.tf_minutes(rule.ft_class.timeframe)
    start = pd.Timestamp(res["backtest_start"], tz="UTC")
    end = pd.Timestamp(res["backtest_end"], tz="UTC")
    bars = load_candles(rule.ft_class.timeframe)
    first = bars.index[bars["time"] >= start][0]
    bars = bars.iloc[max(0, first - rule.warmup):]
    bars = bars[bars["time"] <= end].reset_index(drop=True)
    out = run(bars, rule, rule.market.cost(), BacktestConfig(allow_short=False))
    mine = out.trades_frame()
    mine = mine[pd.to_datetime(mine["entry_time"], utc=True) >= start]
    ft = pd.DataFrame(res["trades"])
    ft_open = pd.to_datetime(ft["open_date"], utc=True)
    ft_close = pd.to_datetime(ft["close_date"], utc=True)
    by_open = {t: i for i, t in enumerate(ft_open)}
    matched = exit_ok = 0
    price_err, mism = [], []
    for r in mine.itertuples(index=False):
        i = by_open.get(pd.Timestamp(r.entry_time))
        if i is None:
            if len(mism) < 8:
                mism.append({"adapter_only": str(r.entry_time), "exit": str(r.exit_time), "reason": r.exit_reason})
            continue
        matched += 1
        price_err.append(abs(r.entry_price / ft["open_rate"].iloc[i] - 1))
        # Freqtrade stamps a stop exit at the candle's open; the engine at the candle's close
        delta = abs((pd.Timestamp(r.exit_time) - ft_close.iloc[i]).total_seconds()) / 60
        if delta <= tf:
            exit_ok += 1
        elif len(mism) < 8:
            mism.append({"entry": str(r.entry_time), "adapter_exit": str(r.exit_time), "adapter_reason": r.exit_reason,
                         "freqtrade_exit": str(ft_close.iloc[i]), "freqtrade_reason": ft["exit_reason"].iloc[i]})
    n_ft, n_me = len(ft), len(mine)
    ft_ret = float(ft["profit_ratio"].sum())
    me_ret = float((mine["net_brl"] / mine["entry_price"]).sum()) if n_me else 0.0
    return {"strategy": strategy, "export": str(z.relative_to(ROOT)).replace("\\", "/"), "timeframe": rule.ft_class.timeframe,
            "fee_per_side": fee, "timerange": [str(start), str(end)], "freqtrade_trades": n_ft, "adapter_trades": n_me,
            "entries_matched": matched, "entries_matched_share_of_freqtrade": round(matched / n_ft, 4) if n_ft else None,
            "exits_within_one_candle_share": round(exit_ok / matched, 4) if matched else None,
            "median_entry_price_error_pct": round(100 * float(pd.Series(price_err).median()), 5) if price_err else None,
            "sum_return_freqtrade_pct": round(100 * ft_ret, 3), "sum_return_adapter_pct": round(100 * me_ret, 3),
            "freqtrade_exit_reasons": ft["exit_reason"].value_counts().to_dict(),
            "adapter_exit_reasons": mine["exit_reason"].value_counts().to_dict() if n_me else {},
            "stop_moves": out.stop_moves, "vetoes": dict(out.vetoes), "examples_of_differences": mism}


def main(argv=None) -> int:
    names = (argv if argv is not None else sys.argv[1:])
    rows = []
    for n in names:
        try:
            r = compare(n)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            r = {"strategy": n, "error": repr(exc)}
        rows.append(r)
        print(json.dumps({k: r.get(k) for k in ("strategy", "freqtrade_trades", "adapter_trades",
                                                "entries_matched_share_of_freqtrade", "exits_within_one_candle_share",
                                                "sum_return_freqtrade_pct", "sum_return_adapter_pct", "error")}), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"strategies": {}}
    prev["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    prev["strategies"].update({r["strategy"]: r for r in rows})
    OUT.write_text(json.dumps(prev, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

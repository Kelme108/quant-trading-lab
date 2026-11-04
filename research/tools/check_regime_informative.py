"""Run INSIDE the Freqtrade container: the regime computed on daily candles and merged into the execution timeframe
(real merge_informative_pair, real generated strategies, real BTC data) uses only closed days.

  docker run --rm --entrypoint python -v <repo>/user_data:/freqtrade/user_data -v <repo>/research/tools:/chk:ro \
      -e PYTHONPATH=/chk:/freqtrade/user_data/strategies freqtradeorg/freqtrade:2026.9 /chk/check_regime_informative.py

For each of the four ablation strategies:
 1. prefix invariance: cutting hourly/4h and daily data at a day boundary leaves every signal before the cut unchanged;
 2. future corruption: overwriting every candle (both timeframes) from the cut onward leaves all rows before it unchanged;
 3. the regime visible on a row of date t is the regime of day floor(t + tf) - 1 day (a day is visible only after it closed).
Exit code 1 on any failure.
"""
import sys
import types

import numpy as np
import pandas as pd

import regime_strategies

BASE = "/freqtrade/user_data/data/binance/BTC_USDT-"
daily_all = pd.read_feather(BASE + "1d.feather")
daily_all["date"] = pd.to_datetime(daily_all["date"], utc=True)
daily_all = daily_all[daily_all["date"] >= "2018-01-01"].reset_index(drop=True)
COLUMNS = ["regime_1d", "enter_long", "exit_long"]


class FakeDP:
    def __init__(self, daily):
        self.daily = daily

    def get_pair_dataframe(self, pair, timeframe):
        return self.daily.copy()

    def current_whitelist(self):
        return ["BTC/USDT"]


def load_class(family, use_vol):
    name = f"Chk_{family}_{int(use_vol)}"
    module = types.ModuleType(name)
    exec(compile(regime_strategies.source(family, use_vol, name), name, "exec"), module.__dict__)
    return getattr(module, name)


def signals(cls, frame, daily):
    strategy = cls.__new__(cls)
    strategy.dp = FakeDP(daily)
    meta = {"pair": "BTC/USDT"}
    out = strategy.populate_indicators(frame.copy(), meta)
    out["enter_long"] = 0
    out["exit_long"] = 0
    out = strategy.populate_entry_trend(out, meta)
    out = strategy.populate_exit_trend(out, meta)
    return out.set_index("date")[COLUMNS].fillna(-1).astype(float)


def corrupt(frame, cut):
    out = frame.copy()
    mask = out["date"] >= cut
    for column in ("open", "high", "low", "close", "volume"):
        out.loc[mask, column] = np.where(np.arange(int(mask.sum())) % 2, 5.0e5, 1.0)
    return out


failures = 0
for family, tf in (("sma200", "1h"), ("donchian", "4h")):
    frame = pd.read_feather(BASE + f"{tf}.feather")
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    frame = frame[frame["date"] >= "2018-01-01"].reset_index(drop=True)
    for use_vol in (False, True):
        cls = load_class(family, use_vol)
        full = signals(cls, frame, daily_all)
        problems = []
        if use_vol and full["regime_1d"].eq(1).sum() == 0:
            problems.append("regime never on")
        for cut in pd.to_datetime(["2020-06-01", "2022-03-01", "2023-09-15"], utc=True):
            part = signals(cls, frame[frame["date"] < cut], daily_all[daily_all["date"] < cut])
            if not part.equals(full.loc[part.index]):
                problems.append(f"prefix cut {cut.date()}: differs")
            bad = signals(cls, corrupt(frame, cut), corrupt(daily_all, cut))
            before = full.index < cut
            if not bad[bad.index < cut].equals(full[before]):
                problems.append(f"future corruption {cut.date()}: changed rows before the cut")
        # 3. visible day check on the regime column
        daily = daily_all.copy()
        sample = full["regime_1d"]
        lookup = None
        from regime_filter import regime_on
        flag = regime_on(daily["close"], use_vol=use_vol, use_trend=(family == "sma200")).astype(float)
        lookup = pd.Series(flag.to_numpy(), index=daily["date"])
        delta = pd.Timedelta(tf)
        expected_day = (sample.index + delta).floor("D") - pd.Timedelta(days=1)
        expected = pd.Series(expected_day.map(lookup).to_numpy(), index=sample.index).fillna(-1)
        valid = sample.index >= pd.Timestamp("2018-03-01", tz="UTC")
        mismatches = int((sample[valid] != expected[valid]).sum())
        if mismatches:
            problems.append(f"visible-day check: {mismatches} rows differ")
        status = "OK" if not problems else "FAIL " + "; ".join(problems)
        print(f"{family:9s} use_vol={use_vol!s:5s} rows={len(full):6d} regime_on_rows={int((full['regime_1d'] == 1).sum()):6d} {status}")
        failures += bool(problems)
sys.exit(1 if failures else 0)

"""H-061: daily floor-pivot S1 reclaim on 15m, target the pivot, flat by UTC day end.

Rule (research/proposals/H-061.json), all times UTC, closed 15m bars, signal at close fills at next open:
- Daily levels from the previous completed UTC day (its 96 15m bars): P=(H+L+C)/3, S1=2P-H, S2=P-(H-L).
  Built here from the 15m frame itself: per-date H/L/C, kept only when the day has all 96 bars, then
  moved forward one calendar day, so day D only ever sees day D-1.
- Armed day: (P-S1)/S1 >= 0.008.
- Entry at close of bar t (open time 00:00..19:45) when: min(low[t-3..t]) < S1; close(t) > S1 and
  (close(t-1) <= S1 or low(t) < S1); no bar of the day so far (00:00..t) has low <= S2; no open position
  and no entry earlier in the same UTC day.
- At entry record SweepLow = min(low[t-3..t]) and P. Exit at first close with close >= P (target),
  close < SweepLow (structure stop), or the close of the 23:45 bar of the entry day (time exit).
- Native fixed stop 3% below entry. No cooldown, trailing or pyramiding.

The position/one-trade-per-day state is path dependent, so it is replayed with a forward-only loop over
past rows. If the 23:45 bar of the entry day is missing or has zero volume, the time exit fires on the
next tradable bar (the first one after the entry day) so the state cannot linger.
"""

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BARS_PER_DAY = 96
MIN_PIVOT_DISTANCE = 0.008
SWEEP_WINDOW = 4
ENTRY_LAST_MINUTE = 19 * 60 + 45
TIME_EXIT_MINUTE = 23 * 60 + 45


def prior_day_levels(dataframe: DataFrame) -> DataFrame:
    """P, S1, S2 of the previous completed UTC day for each 15m row (NaN when unavailable)."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    day = dates.dt.floor("D")
    daily = (
        pd.DataFrame({"day": day, "high": dataframe["high"], "low": dataframe["low"], "close": dataframe["close"]})
        .groupby("day")
        .agg(high=("high", "max"), low=("low", "min"), close=("close", "last"), bars=("close", "size"))
    )
    daily = daily[daily["bars"] == BARS_PER_DAY]
    pivot = (daily["high"] + daily["low"] + daily["close"]) / 3.0
    levels = pd.DataFrame(
        {
            "pivot_p": pivot,
            "pivot_s1": 2.0 * pivot - daily["high"],
            "pivot_s2": pivot - (daily["high"] - daily["low"]),
        }
    )
    # Day D uses the levels of calendar day D-1 only.
    levels.index = levels.index + pd.Timedelta(days=1)
    out = levels.reindex(pd.DatetimeIndex(day))
    out.index = dataframe.index
    return out


class DailyPivotS1Reclaim_H061_v1(IStrategy):
    """Prior-day floor pivot S1 sweep-and-reclaim, target P, flat by UTC day end."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dates = pd.to_datetime(dataframe["date"], utc=True)
        day = dates.dt.floor("D")
        minute = dates.dt.hour * 60 + dates.dt.minute

        levels = prior_day_levels(dataframe)
        dataframe["pivot_p"] = levels["pivot_p"]
        dataframe["pivot_s1"] = levels["pivot_s1"]
        dataframe["pivot_s2"] = levels["pivot_s2"]

        s1 = dataframe["pivot_s1"]
        dataframe["sweep_low"] = dataframe["low"].rolling(SWEEP_WINDOW).min()
        armed = (dataframe["pivot_p"] - s1) / s1 >= MIN_PIVOT_DISTANCE
        swept = dataframe["sweep_low"] < s1
        reclaim = (dataframe["close"] > s1) & (
            (dataframe["close"].shift(1) <= s1) | (dataframe["low"] < s1)
        )
        s2_hit = (dataframe["low"] <= dataframe["pivot_s2"]).astype(int)
        s2_breached = s2_hit.groupby(day).cummax() > 0
        in_window = minute <= ENTRY_LAST_MINUTE
        defined = (
            dataframe[["pivot_p", "pivot_s1", "pivot_s2", "sweep_low"]].notna().all(axis=1)
            & dataframe["close"].shift(1).notna()
        )
        setup = (
            defined & armed & swept & reclaim & ~s2_breached & in_window & (dataframe["volume"] > 0)
        ).fillna(False)

        # Forward-only replay of position state: one position, one entry per UTC day.
        n = len(dataframe)
        setup_v = setup.to_numpy(dtype=bool)
        close_v = dataframe["close"].to_numpy(dtype=float)
        vol_v = dataframe["volume"].to_numpy(dtype=float)
        sweep_v = dataframe["sweep_low"].to_numpy(dtype=float)
        p_v = dataframe["pivot_p"].to_numpy(dtype=float)
        day_v = day.to_numpy()
        minute_v = minute.to_numpy()
        entry_sig = np.zeros(n, dtype=int)
        exit_sig = np.zeros(n, dtype=int)

        in_trade = False
        trade_day = None
        trade_sweep = np.nan
        trade_p = np.nan
        last_entry_day = None
        for i in range(n):
            if in_trade:
                if vol_v[i] > 0 and not np.isnan(close_v[i]):
                    if (
                        close_v[i] >= trade_p
                        or close_v[i] < trade_sweep
                        or (day_v[i] == trade_day and minute_v[i] == TIME_EXIT_MINUTE)
                        or day_v[i] != trade_day
                    ):
                        exit_sig[i] = 1
                        in_trade = False
                continue
            if setup_v[i] and day_v[i] != last_entry_day:
                entry_sig[i] = 1
                in_trade = True
                trade_day = day_v[i]
                last_entry_day = day_v[i]
                trade_sweep = sweep_v[i]
                trade_p = p_v[i]

        dataframe["pivot_entry"] = entry_sig
        dataframe["pivot_exit"] = exit_sig
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["pivot_entry"] == 1) & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "s1_reclaim")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["pivot_exit"] == 1) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "pivot_target_or_structure_or_time")
        return dataframe

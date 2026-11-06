"""H-049: 4h Kaufman adaptive MA trend, executed on 1h candles.

4h candles are built from closed 1h bars in UTC blocks starting 00,04,08,12,16,20 (open=first open, high=max high,
low=min low, close=last close; only blocks with all four 1h bars) and attached with merge_informative_pair(ffill=True),
so a 4h bar becomes visible on the 1h candle that completes its block (opening 03,07,11,15,19,23 UTC).

On the 4h series (index k):
  ER(k)   = |close(k) - close(k-10)| / sum_{j=k-9..k} |close(j) - close(j-1)|   (0 if the denominator is 0)
  SC(k)   = (ER(k) * (2/3 - 2/31) + 2/31) ** 2
  KAMA(9) = SMA of the first 10 4h closes; KAMA(k) = KAMA(k-1) + SC(k) * (close(k) - KAMA(k-1))
  RISING  = KAMA(k) > KAMA(k-6)
Signals only on the 1h candle that completes a 4h block:
  entry: close4h(k) > 1.015 * KAMA(k) and RISING(k)
  exit:  close4h(k) < KAMA(k)
Stop: native stoploss -8% (intrabar). No ROI, no trailing, no time stop, no cooldown.
"""

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair

ER_PERIOD = 10
FAST_PERIOD = 2
SLOW_PERIOD = 30
SEED_BARS = 10
ENTRY_BAND = 1.015
SLOPE_LAG = 6


def kama_series(close: np.ndarray) -> np.ndarray:
    """KAMA(10, 2, 30) seeded at index 9 with the SMA of the first 10 closes. Causal; NaN before the seed."""
    m = len(close)
    out = np.full(m, np.nan)
    if m < SEED_BARS:
        return out
    fast = 2.0 / (FAST_PERIOD + 1)
    slow = 2.0 / (SLOW_PERIOD + 1)
    absdiff = np.abs(np.diff(close, prepend=np.nan))
    out[SEED_BARS - 1] = float(np.mean(close[:SEED_BARS]))
    for k in range(SEED_BARS, m):
        change = abs(close[k] - close[k - ER_PERIOD])
        volatility = float(np.sum(absdiff[k - ER_PERIOD + 1 : k + 1]))
        er = change / volatility if volatility != 0 else 0.0
        sc = (er * (fast - slow) + slow) ** 2
        out[k] = out[k - 1] + sc * (close[k] - out[k - 1])
    return out


class FourHourKAMATrend_H049_v1(IStrategy):
    """Close 1.5% above a rising 4h KAMA(10,2,30) enters; close below KAMA exits."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.08
    trailing_stop = False
    startup_candle_count = 4000

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dates = pd.to_datetime(dataframe["date"], utc=True)
        block = dates.dt.floor("4h")
        grouped = dataframe.assign(block=block).groupby("block", sort=True)
        bars = pd.DataFrame(
            {
                "open": grouped["open"].first(),
                "high": grouped["high"].max(),
                "low": grouped["low"].min(),
                "close": grouped["close"].last(),
                "count": grouped["close"].count(),
            }
        )
        bars = bars[bars["count"] == 4].copy()
        bars.index.name = "date"
        bars = bars.reset_index()

        kama = kama_series(bars["close"].to_numpy(dtype=float))
        bars["kama"] = kama
        bars["kama_lag"] = pd.Series(kama).shift(SLOPE_LAG).to_numpy()

        dataframe = merge_informative_pair(
            dataframe, bars[["date", "close", "kama", "kama_lag"]], self.timeframe, "4h", ffill=True
        )
        merged_dates = pd.to_datetime(dataframe["date"], utc=True)
        block_dates = pd.to_datetime(dataframe["date_4h"], utc=True)
        dataframe["block_complete"] = (merged_dates - block_dates) == pd.Timedelta(hours=3)
        return dataframe

    def _valid(self, dataframe: DataFrame) -> pd.Series:
        return (
            dataframe["block_complete"]
            & dataframe["close_4h"].notna()
            & dataframe["kama_4h"].notna()
            & (dataframe["volume"] > 0)
        )

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            self._valid(dataframe)
            & dataframe["kama_lag_4h"].notna()
            & (dataframe["close_4h"] > ENTRY_BAND * dataframe["kama_4h"])
            & (dataframe["kama_4h"] > dataframe["kama_lag_4h"])
        )
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "kama4h_band_rising")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = self._valid(dataframe) & (dataframe["close_4h"] < dataframe["kama_4h"])
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "kama4h_close_below")
        return dataframe

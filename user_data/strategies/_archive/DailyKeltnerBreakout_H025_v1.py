"""H-025: Daily Keltner upper-band close breakout in uptrend, exit at daily EMA20.

Signals use closed daily (UTC) candles from the 1d informative frame, merged by
Freqtrade so a daily value is visible only after that day has closed. Orders
execute on the 1h chart at the next open. Spot long only.

Daily definitions (d = just-closed day):
- EMA20 = EMA of close, alpha 2/21, seeded with the first daily close.
- TR(d) = max(high-low, |high-close(d-1)|, |low-close(d-1)|).
- ATR20 = Wilder smoothing (alpha 1/20) seeded with the mean of the first 20 TRs.
- UpperBand = EMA20 + 1.5 * ATR20; SMA100 = mean of last 100 closes.
- Entry: close(d) > UpperBand(d) AND close(d-1) <= UpperBand(d-1)
  AND close(d) > SMA100(d).
- Exit: close(d) < EMA20(d), or the 8% native stop.
"""

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy, informative


class DailyKeltnerBreakout_H025_v1(IStrategy):
    """Fresh daily close above EMA20 + 1.5 ATR20 inside a SMA100 uptrend."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.08
    startup_candle_count = 3700

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        prev_close = close.shift(1)
        true_range = (
            (dataframe["high"] - dataframe["low"]).to_frame("a")
            .assign(
                b=(dataframe["high"] - prev_close).abs(),
                c=(dataframe["low"] - prev_close).abs(),
            )
            .max(axis=1, skipna=True)
        )
        tr_values = true_range.to_numpy(dtype=float)
        atr_values = np.full(len(tr_values), np.nan)
        if len(tr_values) >= 20:
            atr_values[19] = tr_values[:20].mean()
            for i in range(20, len(tr_values)):
                atr_values[i] = atr_values[i - 1] + (tr_values[i] - atr_values[i - 1]) / 20.0
        dataframe["atr20"] = atr_values
        dataframe["ema20"] = close.ewm(alpha=2.0 / 21.0, adjust=False).mean()
        dataframe["sma100"] = close.rolling(100).mean()
        upper = dataframe["ema20"] + 1.5 * dataframe["atr20"]
        dataframe["upper_band"] = upper
        fresh = (close > upper) & (close.shift(1) <= upper.shift(1))
        valid = upper.notna() & upper.shift(1).notna() & prev_close.notna()
        dataframe["fresh_cross"] = fresh.astype(float).where(valid)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["upper_band_1d"].notna()
                & dataframe["sma100_1d"].notna()
                & dataframe["fresh_cross_1d"].notna()
                & (dataframe["fresh_cross_1d"] == 1.0)
                & (dataframe["close_1d"] > dataframe["upper_band_1d"])
                & (dataframe["close_1d"] > dataframe["sma100_1d"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "keltner_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["ema20_1d"].notna()
                & (dataframe["close_1d"] < dataframe["ema20_1d"])
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "close_below_ema20")
        return dataframe

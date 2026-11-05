"""H-027: Daily Supertrend (ATR 10, x3) long-only flip trend follower.

Signals use closed daily (UTC) candles from the 1d informative frame, merged by
Freqtrade so a daily value is visible only after that day has closed. Orders
execute on the 1h chart at the next open. Spot long only.

Daily definitions (d = just-closed day):
- TR(d) = max(high-low, |high-close(d-1)|, |low-close(d-1)|).
- ATR = Wilder smoothing (alpha 1/10) seeded with the mean of the first 10 TRs.
- BasicUpper/Lower = hl2 +/- 3.0 * ATR, ratcheting FinalUpper/FinalLower.
- State starts DOWN on the first day with a defined ATR; DOWN->UP when
  close > FinalUpper, UP->DOWN when close < FinalLower.
- Entry: flip DOWN->UP. Exit: flip UP->DOWN. No binding stop (-0.99 placeholder).
"""

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy, informative

ATR_LENGTH = 10
MULTIPLIER = 3.0


class DailySupertrendFlip_H027_v1(IStrategy):
    """Long on daily Supertrend flip to UP, exit on flip to DOWN."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.99
    startup_candle_count = 3700

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        close = dataframe["close"].to_numpy(dtype=float)
        n = len(close)

        tr = np.full(n, np.nan)
        for i in range(n):
            value = high[i] - low[i]
            if i > 0:
                value = max(value, abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
            tr[i] = value

        atr = np.full(n, np.nan)
        final_upper = np.full(n, np.nan)
        final_lower = np.full(n, np.nan)
        state = np.full(n, np.nan)  # 1.0 = UP, 0.0 = DOWN
        flip_up = np.full(n, np.nan)
        flip_down = np.full(n, np.nan)

        first = ATR_LENGTH - 1
        if n > first and not np.isnan(tr[: first + 1]).any():
            atr[first] = tr[: first + 1].mean()
            for i in range(first + 1, n):
                atr[i] = atr[i - 1] + (tr[i] - atr[i - 1]) / ATR_LENGTH

            for i in range(first, n):
                hl2 = (high[i] + low[i]) / 2.0
                basic_upper = hl2 + MULTIPLIER * atr[i]
                basic_lower = hl2 - MULTIPLIER * atr[i]
                if i == first:
                    final_upper[i] = basic_upper
                    final_lower[i] = basic_lower
                    state[i] = 0.0
                    continue
                if basic_upper < final_upper[i - 1] or close[i - 1] > final_upper[i - 1]:
                    final_upper[i] = basic_upper
                else:
                    final_upper[i] = final_upper[i - 1]
                if basic_lower > final_lower[i - 1] or close[i - 1] < final_lower[i - 1]:
                    final_lower[i] = basic_lower
                else:
                    final_lower[i] = final_lower[i - 1]
                prev_state = state[i - 1]
                if prev_state == 0.0 and close[i] > final_upper[i]:
                    state[i] = 1.0
                elif prev_state == 1.0 and close[i] < final_lower[i]:
                    state[i] = 0.0
                else:
                    state[i] = prev_state
                flip_up[i] = 1.0 if (prev_state == 0.0 and state[i] == 1.0) else 0.0
                flip_down[i] = 1.0 if (prev_state == 1.0 and state[i] == 0.0) else 0.0

        dataframe["st_atr"] = atr
        dataframe["st_final_upper"] = final_upper
        dataframe["st_final_lower"] = final_lower
        dataframe["st_state"] = state
        dataframe["st_flip_up"] = flip_up
        dataframe["st_flip_down"] = flip_down
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["st_state_1d"].notna()
                & dataframe["st_flip_up_1d"].notna()
                & (dataframe["st_flip_up_1d"] == 1.0)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "supertrend_flip_up")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["st_state_1d"].notna()
                & dataframe["st_flip_down_1d"].notna()
                & (dataframe["st_flip_down_1d"] == 1.0)
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "supertrend_flip_down")
        return dataframe

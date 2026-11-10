"""H-097: 15m RSI bullish divergence at confirmed pivot lows, hourly RSI < 40.

Closed candles only. A pivot low at bar i (3 bars each side) is known only at
the close of i+3. Divergence between two consecutive confirmed pivots, then the
first close above the post-pivot structure inside i2+3..i2+8 with 1h RSI < 40
is the entry (one signal per divergence). The fixed percentage stop D is
carried in the entry tag and applied by custom_stoploss from the open rate.
Exits: stop, 2D take-profit (custom_exit), 15m RSI >= 70 (exit signal),
12h time exit (custom_exit). Hard native stoploss -0.03.
"""

from datetime import timedelta

import numpy as np
import talib.abstract as ta
from pandas import DataFrame
from freqtrade.strategy import IStrategy, merge_informative_pair

PIVOT_BARS = 3
MIN_GAP = 6
MAX_GAP = 25
RSI_FIRST_MAX = 40.0
H1_RSI_MAX = 40.0
WINDOW_START = 3
WINDOW_END = 8
STOP_BUFFER = 0.002
MIN_STOP = 0.01
MAX_STOP = 0.03


def find_signals(low, high, close, volume, rsi, h1_rsi):
    """Return (signal, stop_distance) arrays. Looks backwards only."""
    n = len(close)
    signal = np.zeros(n, dtype=bool)
    stop = np.full(n, np.nan)
    last_piv = None  # (index, low, rsi)
    active = None  # index i2 of a live divergence
    k = PIVOT_BARS
    for t in range(n):
        i = t - k
        if i >= k:
            seg = low[i - k : i + k + 1]
            if np.isfinite(seg).all() and np.isfinite(rsi[i]):
                left_ok = all(low[i] < low[j] for j in range(i - k, i))
                right_ok = all(low[i] <= low[j] for j in range(i + 1, i + k + 1))
                if left_ok and right_ok:
                    if last_piv is not None:
                        i1, low1, rsi1 = last_piv
                        if (
                            MIN_GAP <= i - i1 <= MAX_GAP
                            and low[i] < low1
                            and rsi[i] > rsi1
                            and rsi1 < RSI_FIRST_MAX
                        ):
                            active = i
                    last_piv = (i, low[i], rsi[i])
        if active is not None:
            if t > active + WINDOW_END:
                active = None
            elif t >= active + WINDOW_START:
                prior_high = high[active:t]
                if (
                    volume[t] > 0
                    and np.isfinite(close[t])
                    and np.isfinite(prior_high).all()
                    and np.isfinite(h1_rsi[t])
                    and close[t] > prior_high.max()
                    and h1_rsi[t] < H1_RSI_MAX
                ):
                    r = 1.0 - low[active] * (1.0 - STOP_BUFFER) / close[t]
                    if r <= MAX_STOP:
                        signal[t] = True
                        stop[t] = max(MIN_STOP, r)
                    active = None
    return signal, stop


class RSIBullDivergence_H097_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_custom_stoploss = True
    startup_candle_count = 1200

    rsi_period = 14
    h1_rsi_period = 14
    rsi_exit_level = 70
    take_profit_r = 2
    max_hold_hours = 12

    def informative_pairs(self):
        if not self.dp:
            return []
        return [(pair, "1h") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        informative = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="1h")
        informative["rsi"] = ta.RSI(informative, timeperiod=14)
        dataframe = merge_informative_pair(
            dataframe, informative, self.timeframe, "1h", ffill=True
        )
        signal, stop = find_signals(
            dataframe["low"].to_numpy(dtype=float),
            dataframe["high"].to_numpy(dtype=float),
            dataframe["close"].to_numpy(dtype=float),
            dataframe["volume"].to_numpy(dtype=float),
            dataframe["rsi"].to_numpy(dtype=float),
            dataframe["rsi_1h"].to_numpy(dtype=float),
        )
        dataframe["div_signal"] = signal.astype(int)
        dataframe["stop_dist"] = stop
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        mask = (
            (dataframe["div_signal"] == 1)
            & dataframe["stop_dist"].notna()
            & dataframe["rsi"].notna()
            & dataframe["rsi_1h"].notna()
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[mask, "enter_long"] = 1
        dataframe.loc[mask, "enter_tag"] = dataframe.loc[mask, "stop_dist"].map(
            lambda d: "div_%.5f" % d
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        mask = dataframe["rsi"].notna() & (dataframe["rsi"] >= self.rsi_exit_level) & (
            dataframe["volume"] > 0
        )
        dataframe.loc[mask, "exit_long"] = 1
        dataframe.loc[mask, "exit_tag"] = "rsi70"
        return dataframe

    @staticmethod
    def _stop_distance(trade):
        tag = trade.enter_tag or ""
        if tag.startswith("div_"):
            try:
                return float(tag[4:])
            except ValueError:
                return None
        return None

    def custom_stoploss(
        self, pair, trade, current_time, current_rate, current_profit, **kwargs
    ):
        d = self._stop_distance(trade)
        if d is None or current_rate <= 0:
            return None
        stop_price = trade.open_rate * (1.0 - d)
        rel = stop_price / current_rate - 1.0
        return min(rel, -0.0001)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        d = self._stop_distance(trade)
        if d is not None and current_profit >= self.take_profit_r * d:
            return "take_profit_2R"
        if current_time - trade.open_date_utc >= timedelta(hours=self.max_hold_hours):
            return "time_12h"
        return None

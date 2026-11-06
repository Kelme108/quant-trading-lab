"""H-050: 15m high-volume 6-hour selloff reversal in a daily uptrend, with a 12-hour time exit.

Closed candles only; a signal at the close of bar t is filled at the open of bar t+1. Spot, long only,
one position per pair, no sizing hooks.

Definitions (completed 15m bars):
- r24(t)  = close(t) / close(t-24) - 1                         (6-hour return)
- V6(t)   = sum of volume over bars t-23..t                     (24 bars)
- Vref(t) = mean of V6(t - 24*k), k = 1..56                     (bars t-1367..t-24; current window excluded)
- Daily regime: last COMPLETED daily close > SMA(100) of daily closes ending that same day. Daily values reach
  the 15m frame through merge_informative_pair (ffill), so only fully closed UTC days are visible.

Entry at the close of bar t when all hold: r24 <= -0.03; V6 >= 1.5 * Vref; close > open; daily regime;
all inputs defined; volume > 0. One position and the cooldown are enforced by the engine.

Exit (custom_exit, evaluated on closed bars, filled at the next open), first of:
- (a) close(u) >= P for some bar u >= t+1, where P = close(t-24) of the signal bar (fixed for the trade);
- (b) time exit at the close of bar t+48 (filled at the open of bar t+49).
Stop: fixed 3% below entry (native intrabar stoploss). Cooldown: 24 candles after any exit.
"""

from datetime import timedelta

import numpy as np
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair

RETURN_BARS = 24
DROP_THRESHOLD = -0.03
VOLUME_WINDOW = 24
VOLUME_REF_SAMPLES = 56
VOLUME_MULTIPLE = 1.5
REGIME_SMA_DAYS = 100
TIME_EXIT_BARS = 48
COOLDOWN_BARS = 24
BAR_MINUTES = 15


def volume_reference(volume, window: int = VOLUME_WINDOW, samples: int = VOLUME_REF_SAMPLES):
    """(V6, Vref): rolling window sum and the mean of the `samples` previous non-overlapping window sums."""
    v6 = volume.rolling(window).sum()
    total = v6.shift(window)
    for k in range(2, samples + 1):
        total = total + v6.shift(window * k)
    return v6, total / samples


class VolumeConditionedReversal_H050_v1(IStrategy):
    """Buy the first green 15m bar after a high-volume 6h selloff inside a daily uptrend."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_exit_signal = True
    startup_candle_count = 1400

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def informative_pairs(self):
        return [(pair, "1d") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["r24"] = dataframe["close"] / dataframe["close"].shift(RETURN_BARS) - 1.0
        dataframe["pre_drop_close"] = dataframe["close"].shift(RETURN_BARS)
        v6, vref = volume_reference(dataframe["volume"])
        dataframe["v6"] = v6
        dataframe["vref"] = vref

        daily = self.dp.get_pair_dataframe(metadata["pair"], "1d").copy()
        daily["dsma"] = daily["close"].rolling(REGIME_SMA_DAYS).mean()
        dataframe = merge_informative_pair(
            dataframe, daily[["date", "close", "dsma"]], self.timeframe, "1d", ffill=True
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["r24"].notna()
            & dataframe["v6"].notna()
            & dataframe["vref"].notna()
            & dataframe["close_1d"].notna()
            & dataframe["dsma_1d"].notna()
            & dataframe["open"].notna()
            & dataframe["close"].notna()
        )
        dataframe.loc[
            (
                defined
                & (dataframe["r24"] <= DROP_THRESHOLD)
                & (dataframe["v6"] >= VOLUME_MULTIPLE * dataframe["vref"])
                & (dataframe["close"] > dataframe["open"])
                & (dataframe["close_1d"] > dataframe["dsma_1d"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "volume_selloff_reversal")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Both exits depend on the open trade (fixed P, bars since the signal): see custom_exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        bar = timedelta(minutes=BAR_MINUTES)
        open_date = trade.open_date_utc

        # Signal bar t: the last bar that opened before the entry fill (entry fills at the open of t+1).
        before = dataframe.loc[dataframe["date"] < open_date]
        if before.empty:
            return None
        signal = before.iloc[-1]

        # Closed bars u >= t+1: opened at or after the entry and fully closed by current_time.
        after = dataframe.loc[(dataframe["date"] >= open_date) & (dataframe["date"] + bar <= current_time)]
        # Never exit on a candle with zero volume.
        if after.empty or not after["volume"].iloc[-1] > 0:
            return None
        after = after.loc[after["volume"] > 0]

        target = signal["pre_drop_close"]
        if target == target and bool(np.any(after["close"].to_numpy() >= float(target))):
            return "retrace_to_pre_drop_close"

        # Bar t+48 is the bar that opens at open_date + 47 bars; its close is open_date + 48 bars.
        if open_date + TIME_EXIT_BARS * bar <= current_time:
            return "time_exit_48_bars"
        return None

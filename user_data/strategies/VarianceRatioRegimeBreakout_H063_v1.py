"""H-063: 15m 24-hour-high breakout gated by a 4-bar variance ratio and a 4h trend filter.

All times UTC, closed 15m bars only; a signal at the close of bar t fills at the open of bar t+1.
Long only, spot, one position per pair (engine), no pyramiding, no take-profit, no sizing hooks.

Definitions:
- r(i) = ln(close(i) / close(i-1)).
- q(i) = r(i-3) + r(i-2) + r(i-1) + r(i) (overlapping 4-bar sums).
- VR(t) = var(q, last 381 values, ddof=1) / (4 * var(r, last 384 values, ddof=1)).
- HTF filter: 4h candles built from the 15m data in UTC blocks 00/04/08/12/16/20, attached with
  merge_informative_pair (ffill), so only completed 4h candles are visible. True when the last completed
  4h close > simple mean of the last 50 completed 4h closes (that close included).
Entry at the close of bar t when all hold: close(t) > highest high of bars t-96..t-1; VR(t) >= 1.10;
HTF filter true; no position open (engine). No cooldown.
Exits (custom_exit), first of:
- (a) at the close of a bar after the entry bar (the fill bar), close < lowest low of the prior 16 bars
  (current bar excluded) -> sell at the next open;
- (b) time exit: after the 96th 15m bar counted from the entry bar closes -> sell at the next open.
- (c) native 5% stoploss (protective backstop).
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair

BAR = timedelta(minutes=15)
VR_WINDOW = 384
VR_HORIZON = 4
VR_THRESHOLD = 1.10
BREAKOUT_LOOKBACK = 96
HTF_SMA_LENGTH = 50
EXIT_LOW_LOOKBACK = 16
TIME_EXIT_BARS = 96


def regime_indicators(dataframe: DataFrame) -> DataFrame:
    """Add log_ret, vr, breakout_high and exit_low. Backward-looking only."""
    close = dataframe["close"]
    log_ret = np.log(close / close.shift(1))
    q = log_ret.rolling(VR_HORIZON).sum()
    q_var = q.rolling(VR_WINDOW - VR_HORIZON + 1).var()
    r_var = log_ret.rolling(VR_WINDOW).var()
    vr = q_var / (VR_HORIZON * r_var.where(r_var > 0))
    dataframe["log_ret"] = log_ret
    dataframe["vr"] = vr.replace([np.inf, -np.inf], np.nan)
    # Levels compared with the current candle exclude it (shift by one candle).
    dataframe["breakout_high"] = dataframe["high"].rolling(BREAKOUT_LOOKBACK).max().shift(1)
    dataframe["exit_low"] = dataframe["low"].rolling(EXIT_LOW_LOOKBACK).min().shift(1)
    return dataframe


def four_hour_from_intraday(dataframe: DataFrame) -> DataFrame:
    """4h UTC-block closes from the 15m bars, on a gap-free calendar, with the 50-block simple mean."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    block = dates.dt.floor("4h")
    block_close = dataframe["close"].groupby(block.to_numpy()).last()
    block_close.index = pd.DatetimeIndex(block_close.index)
    if block_close.index.tz is None:
        block_close.index = block_close.index.tz_localize("UTC")
    calendar = pd.date_range(block_close.index.min(), block_close.index.max(), freq="4h")
    block_close = block_close.reindex(calendar)
    return DataFrame(
        {
            "date": calendar,
            "close": block_close.to_numpy(dtype=float),
            "hsma": block_close.rolling(HTF_SMA_LENGTH).mean().to_numpy(dtype=float),
        }
    )


class VarianceRatioRegimeBreakout_H063_v1(IStrategy):
    """Buy a 24h-high breakout when 15m returns trend (VR >= 1.1) in a 4h uptrend; out within 24h."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    use_exit_signal = True
    startup_candle_count = 900

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = regime_indicators(dataframe)
        four_hour = four_hour_from_intraday(dataframe)
        dataframe = merge_informative_pair(dataframe, four_hour, self.timeframe, "4h", ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        cond = (
            close.notna()
            & dataframe["breakout_high"].notna()
            & dataframe["vr"].notna()
            & dataframe["close_4h"].notna()
            & dataframe["hsma_4h"].notna()
            & (close > dataframe["breakout_high"])
            & (dataframe["vr"] >= VR_THRESHOLD)
            & (dataframe["close_4h"] > dataframe["hsma_4h"])
            & (dataframe["volume"] > 0)
        ).fillna(False)
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "vr_breakout96")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Both exits depend on the open trade (entry bar, bar count): see custom_exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        open_date = trade.open_date_utc
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is not None and len(dataframe) > 0:
            closed = dataframe.loc[dataframe["date"] + BAR <= current_time]
            if not closed.empty:
                last = closed.iloc[-1]
                # Only bars after the entry bar (the bar whose open was the fill).
                if (
                    last["date"] >= open_date + BAR
                    and last["volume"] > 0
                    and pd.notna(last["exit_low"])
                    and pd.notna(last["close"])
                    and last["close"] < last["exit_low"]
                ):
                    return "close_below_low16"
        # The 96th bar counted from the entry bar closes at open_date + 96 bars.
        if current_time >= open_date + TIME_EXIT_BARS * BAR:
            return "time_exit_96_bars"
        return None

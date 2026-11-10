"""H-100 (v2 of H-085): Overbought-is-strength with a relative-volume confirmation: 1h RSI(14) cross above 70 on at least twice the usual volume.

One change from H-085, fixed ex ante: the signal bar's volume must be at least 2.0 times the mean volume of the previous 120 bars.
Everything else (entries, exits, stop, warm-up) is the parent's code.

--- parent description ---
H-085: overbought-is-strength. Buy the fresh 1h RSI(14) cross above 70.

Rule (research/proposals/H-085.json), 1h, closed bars only, long only, spot:
- RSI14 = Wilder RSI(14) on 1h closes (talib RSI).
- ENTRY at the close of bar t when RSI14(t-1) <= 70 and RSI14(t) > 70; the order fills at the next 1h open.
- EXITS, whichever comes first:
  (a) take-profit +3% (current_profit >= 0.03), in custom_exit because the contract fixes
      minimal_roi = {"0": 100.0};
  (b) a closed 1h bar with RSI14 < 55 (exit signal, sells at the next open);
  (c) time exit: trade age >= 24 hours (custom_exit).
- No stop in the published rule: stoploss = -0.99 is a non-binding engine placeholder.
- No cooldown, no trend or volume filter. Warm-up 300 bars so the recursive Wilder smoothing has converged.
"""

from datetime import timedelta

import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
from freqtrade.strategy import IStrategy

RSI_LENGTH = 14
RSI_ENTRY_LEVEL = 70.0
RSI_EXIT_LEVEL = 55.0
TAKE_PROFIT = 0.03
TIME_EXIT_HOURS = 24


RVOL_WINDOW = 120  # bars; 1h chart = 5 days
RVOL_MIN = 2.0  # signal-bar volume must be at least twice the mean volume of the previous RVOL_WINDOW bars


def relative_volume(volume):
    """Volume of each bar divided by the mean volume of the PREVIOUS 120 bars (the current bar is excluded)."""
    return volume / volume.shift(1).rolling(RVOL_WINDOW).mean()


class RSIOverboughtMomentumRVol_H100_v1(IStrategy):
    """Fresh RSI(14) cross above 70 on 1h; exit +3%, RSI < 55, or after 24 hours."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.99
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = pd.Series(ta.RSI(dataframe, timeperiod=RSI_LENGTH), index=dataframe.index).astype(float)
        dataframe["rsi_prev"] = dataframe["rsi"].shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = dataframe["rsi"]
        rsi_prev = dataframe["rsi_prev"]
        rvol_ok = (relative_volume(dataframe["volume"]) >= RVOL_MIN).fillna(False)
        cross_up = (
            rsi.notna()
            & rsi_prev.notna()
            & (rsi_prev <= RSI_ENTRY_LEVEL)
            & (rsi > RSI_ENTRY_LEVEL)
        )
        dataframe.loc[cross_up & rvol_ok & (dataframe["volume"] > 0), ["enter_long", "enter_tag"]] = (1, "rsi_cross_above_70")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = dataframe["rsi"]
        weak = rsi.notna() & (rsi < RSI_EXIT_LEVEL)
        dataframe.loc[weak & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (1, "rsi_below_55")
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        if current_profit >= TAKE_PROFIT:
            return "take_profit_3pct"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_24h"
        return None

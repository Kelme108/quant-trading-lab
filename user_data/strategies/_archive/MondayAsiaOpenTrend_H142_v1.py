"""H-142: Monday Asia-open trend window, 15m, prior 8-hour-high breakouts on Monday UTC only.

Rule (research/proposals/H-142.json), 15m, UTC, closed bars only, spot, long only:
- HH32(t) = highest high of bars t-32..t-1 (bar t excluded). Any missing bar -> no signal.
- NATR(t) = Wilder ATR(14)(t) / close(t) (talib ATR).
- WINDOW: bar open time Monday 00:00 .. Monday 23:30 UTC. No entries on other days.
- ENTRY: close(t) > HH32(t) and NATR(t) >= 0.004; buy at the open of bar t+1.
  Fewer than 3 entries already made on the pair that Monday (UTC date), and the signal bar must be
  after the bar on which the previous trade of the pair exited: both in confirm_trade_entry.
  One open position per pair is the engine default.
- EXITS: stop -1.0% (native stoploss), take-profit +1.8% and 12h (48 bars) time exit in custom_exit,
  and an exit signal on the close of the Monday 23:45 bar (fill Tuesday 00:00).
- Warm-up 400 bars.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

BAR = timedelta(minutes=15)
BREAKOUT_BARS = 32
ATR_PERIOD = 14
NATR_MIN = 0.004
MAX_ENTRIES_PER_MONDAY = 3
TAKE_PROFIT_PCT = 0.018
TIME_EXIT_HOURS = 12  # 48 bars of 15m
WINDOW_LAST_SIGNAL_MINUTE = 23 * 60 + 30  # Monday 23:30 open
FORCED_EXIT_MINUTE = 23 * 60 + 45  # Monday 23:45 open: exit signal, fill Tuesday 00:00
MONDAY = 0


class MondayAsiaOpenTrend_H142_v1(IStrategy):
    """Prior 8h-high breakout with a volatility gate, Monday UTC only, flat by Monday end."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.01
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"])

        # highest high of the 32 previous bars (current bar excluded)
        dataframe["hh32"] = dataframe["high"].shift(1).rolling(BREAKOUT_BARS).max()
        # all 32 previous bars must exist on the 15m grid (no missing candles)
        # (rows t-32..t span exactly 32 bar intervals, so none of the 32 prior bars is missing)
        span = date - date.shift(BREAKOUT_BARS)
        contiguous = span == BREAKOUT_BARS * BAR
        dataframe["hh32"] = dataframe["hh32"].where(contiguous)

        atr = pd.Series(ta.ATR(dataframe, timeperiod=ATR_PERIOD), index=dataframe.index).astype(float)
        dataframe["atr14"] = atr
        dataframe["natr"] = atr / dataframe["close"]

        minute_of_day = date.dt.hour * 60 + date.dt.minute
        monday = date.dt.day_of_week == MONDAY
        dataframe["in_window"] = monday & (minute_of_day <= WINDOW_LAST_SIGNAL_MINUTE)
        dataframe["forced_exit_bar"] = monday & (minute_of_day == FORCED_EXIT_MINUTE)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            dataframe["in_window"].fillna(False).astype(bool)
            & dataframe["hh32"].notna()
            & dataframe["natr"].notna()
            & (dataframe["volume"] > 0)
            & (dataframe["close"] > dataframe["hh32"])
            & (dataframe["natr"] >= NATR_MIN)
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = dataframe["forced_exit_bar"].fillna(False).astype(bool) & (dataframe["volume"] > 0)
        if ok.any():
            dataframe.loc[ok, "exit_long"] = 1
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Max 3 entries per pair per Monday; signal bar must be after the previous exit bar."""
        now = pd.Timestamp(current_time)
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        signal_bar_open = now.floor("15min") - pd.Timedelta(minutes=15)
        today = now.date()
        entries_today = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            opened = trade.open_date_utc
            if opened is not None and pd.Timestamp(opened).date() == today:
                entries_today += 1
            closed = trade.close_date_utc
            if closed is not None and pd.Timestamp(closed) >= signal_bar_open:
                return False
        return entries_today < MAX_ENTRIES_PER_MONDAY

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        if current_profit >= TAKE_PROFIT_PCT:
            return "take_profit_1p8pct"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        # never held past Tuesday 00:00 UTC (backup for the Monday 23:45 exit signal)
        if current_time.date() > trade.open_date_utc.date():
            return "monday_end"
        return None

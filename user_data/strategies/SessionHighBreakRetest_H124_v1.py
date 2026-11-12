"""H-124: prior 8h-session high, volume-backed break, buy the first bullish wick-retest (15m).

Rule (research/proposals/H-124.json), 15m, UTC, closed bars only, spot, long only:
- SESSIONS: 00:00-07:45, 08:00-15:45, 16:00-23:45 (32 bars each).
- LEVEL: for a bar in session S, PSH = highest high of the 32 bars of session S-1.
  If any of those 32 bars is missing, session S gives no setup.
- BREAK: the FIRST bar b of S with close >= 1.002 x PSH and volume >= 1.5 x mean volume of bars
  b-20..b-1. At most one setup per session; a new setup replaces an older active one (the
  replacement happens at the close of bar b, before bar b would be checked for the old setup).
- RETEST WINDOW: bars b+1..b+16 (time based: at most 16 x 15m after b). Per bar, in order:
  close < 0.995 x PSH -> setup cancelled; otherwise low <= 1.002 x PSH and close >= PSH and
  close > open -> entry signal (setup used up at this bar whether or not an order fills).
  The signal fills at the next open; low(t) travels in enter_tag ("shbr:<low>").
- STOP: d = max(1 - 0.998 x low(t) / E, 0.01), E = fill price, frozen; stop price E x (1 - d).
  Implemented in custom_stoploss as a fixed absolute price (converted to a ratio of the
  current rate, which is what Freqtrade expects); native stoploss -0.10 is only a backstop.
- TAKE-PROFIT +2% and TIME EXIT 12 h (48 bars) in custom_exit. No other exits, no cooldown.
- Warm-up 100 bars.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

SESSION_HOURS = 8
SESSION_BARS = 32
BAR_MINUTES = 15
BREAK_CLOSE_MULT = 1.002
VOLUME_MEAN_BARS = 20
VOLUME_MULT = 1.5
RETEST_WINDOW_BARS = 16
RETEST_LOW_MULT = 1.002
INVALIDATION_CLOSE_MULT = 0.995
STOP_LOW_MULT = 0.998
MIN_STOP_PCT = 0.01
TAKE_PROFIT_PCT = 0.02
TIME_EXIT_HOURS = 12  # 48 bars of 15m
TAG_PREFIX = "shbr:"


class SessionHighBreakRetest_H124_v1(IStrategy):
    """Break of the prior 8h-session high on volume, then buy the first defended retest, 15m."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 100

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        date = pd.to_datetime(dataframe["date"])
        session = date.dt.floor(f"{SESSION_HOURS}h")

        # previous completed session high (NaN unless all 32 bars of S-1 are present)
        grouped_high = dataframe["high"].groupby(session)
        session_high = grouped_high.max()
        session_count = grouped_high.count()
        session_high = session_high.where(session_count == SESSION_BARS)
        previous_session = pd.Index(session - pd.Timedelta(hours=SESSION_HOURS))
        dataframe["psh"] = session_high.reindex(previous_session).to_numpy(dtype=float)

        # mean volume of the previous 20 bars; the current bar is excluded
        dataframe["vmean"] = dataframe["volume"].shift(1).rolling(VOLUME_MEAN_BARS).mean()

        break_cond = (
            dataframe["psh"].notna()
            & dataframe["vmean"].notna()
            & (dataframe["volume"] > 0)
            & (dataframe["close"] >= BREAK_CLOSE_MULT * dataframe["psh"])
            & (dataframe["volume"] >= VOLUME_MULT * dataframe["vmean"])
        )
        # first qualifying bar of each session only
        running = break_cond.astype(int).groupby(session).cumsum()
        dataframe["sbr_break"] = break_cond & (running == 1)

        # setup state machine, strictly backwards in time
        bar_no = ((date - date.iloc[0]) / pd.Timedelta(minutes=BAR_MINUTES)).round().to_numpy() if n else np.array([])
        psh = dataframe["psh"].to_numpy(dtype=float)
        open_ = dataframe["open"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        close = dataframe["close"].to_numpy(dtype=float)
        is_break = dataframe["sbr_break"].to_numpy(dtype=bool)

        signal = np.zeros(n, dtype=bool)
        signal_low = np.full(n, np.nan)
        active = False
        level = np.nan
        break_bar_no = 0.0
        for i in range(n):
            if is_break[i]:
                active = True
                level = psh[i]
                break_bar_no = bar_no[i]
                continue
            if not active:
                continue
            if bar_no[i] - break_bar_no > RETEST_WINDOW_BARS:
                active = False
                continue
            if not (np.isfinite(open_[i]) and np.isfinite(low[i]) and np.isfinite(close[i])):
                continue
            if close[i] < INVALIDATION_CLOSE_MULT * level:
                active = False
                continue
            if low[i] <= RETEST_LOW_MULT * level and close[i] >= level and close[i] > open_[i]:
                signal[i] = True
                signal_low[i] = low[i]
                active = False

        dataframe["sbr_signal"] = signal
        dataframe["sbr_low"] = signal_low
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            dataframe["sbr_signal"].fillna(False).astype(bool)
            & dataframe["sbr_low"].notna()
            & dataframe["psh"].notna()
            & dataframe["vmean"].notna()
            & (dataframe["volume"] > 0)
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
            dataframe.loc[ok, "enter_tag"] = dataframe.loc[ok, "sbr_low"].map(
                lambda value: TAG_PREFIX + repr(float(value))
            )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No exit signals: exits are the stop, the take-profit and the time exit.
        return dataframe

    @staticmethod
    def _signal_low(trade):
        tag = trade.enter_tag
        if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
            return None
        try:
            value = float(tag[len(TAG_PREFIX):])
        except ValueError:
            return None
        return value if np.isfinite(value) and value > 0 else None

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float,
        current_profit: float, after_fill: bool = False, **kwargs
    ):
        low = self._signal_low(trade)
        entry = trade.open_rate
        if low is None or not entry or not current_rate:
            return None  # fall back to the native backstop
        distance = max(1.0 - STOP_LOW_MULT * low / entry, MIN_STOP_PCT)
        stop_price = entry * (1.0 - distance)
        ratio = stop_price / current_rate - 1.0
        if ratio >= 0:
            # price already at or below the frozen stop: stop out as soon as possible
            return -1e-6
        return ratio

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        if current_profit >= TAKE_PROFIT_PCT:
            return "take_profit_2pct"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None

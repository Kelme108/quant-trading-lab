"""H-099: 60-hour momentum sign with a rising-bar trigger, intraday long only.

1h chart, closed candles only. Signal at the close of bar t, fill at the open
of bar t+1.
Entry: close(t) > close(t-60) and close(t) > close(t-1), fill bar opening at
00:00-16:00 UTC (signal bar opening at 23:00 or 00:00-15:00 UTC), at most two
entries per pair per UTC day (confirm_trade_entry), cooldown of 2 candles.
Exit (first to occur): close(t) <= close(t-60); native stop -2%; evening exit
at the 23:00 UTC open (signal on the 22:00 bar); time exit 12 bars after the
fill (custom_exit).
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy

MOMENTUM_LOOKBACK = 60
TRIGGER_LAG = 1
MAX_ENTRIES_PER_DAY = 2
MAX_HOLD_BARS = 12
EVENING_EXIT_BAR_HOUR = 23
LAST_FILL_HOUR = 16


class TimeSeriesMomentum_H099_v1(IStrategy):
    """Sixty-hour time-series momentum, intraday, flat by 23:00 UTC."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    startup_candle_count = 100

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 2}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["close_lag_mom"] = dataframe["close"].shift(MOMENTUM_LOOKBACK)
        dataframe["close_lag_1"] = dataframe["close"].shift(TRIGGER_LAG)
        dataframe["bar_hour"] = pd.to_datetime(dataframe["date"], utc=True).dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = dataframe["bar_hour"]
        # Fill bar is t+1: hours 00..16 -> signal bar hour is 23 or 0..15.
        in_window = (hour == EVENING_EXIT_BAR_HOUR) | (hour <= LAST_FILL_HOUR - 1)
        valid = (
            dataframe["close_lag_mom"].notna()
            & dataframe["close_lag_1"].notna()
            & (dataframe["volume"] > 0)
        )
        signal = (
            valid
            & (dataframe["close"] > dataframe["close_lag_mom"])
            & (dataframe["close"] > dataframe["close_lag_1"])
            & in_window
        )
        dataframe.loc[signal, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        valid = dataframe["close_lag_mom"].notna() & (dataframe["volume"] > 0)
        momentum_exit = valid & (dataframe["close"] <= dataframe["close_lag_mom"])
        # Signal on the 22:00 bar -> sold at the open of the 23:00 bar.
        evening_exit = valid & (dataframe["bar_hour"] == EVENING_EXIT_BAR_HOUR - 1)
        dataframe.loc[momentum_exit | evening_exit, "exit_long"] = 1
        return dataframe

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time,
        entry_tag,
        side: str,
        **kwargs,
    ) -> bool:
        from freqtrade.persistence import Trade

        now = pd.Timestamp(current_time)
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        today = now.tz_convert("UTC").date()
        count = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            opened = pd.Timestamp(trade.open_date_utc)
            if opened.tzinfo is None:
                opened = opened.tz_localize("UTC")
            if opened.tz_convert("UTC").date() == today:
                count += 1
        return count < MAX_ENTRIES_PER_DAY

    def custom_exit(
        self, pair, trade, current_time, current_rate, current_profit, **kwargs
    ):
        if current_time - trade.open_date_utc >= timedelta(hours=MAX_HOLD_BARS):
            return "time_exit_12h"
        now = pd.Timestamp(current_time)
        opened = pd.Timestamp(trade.open_date_utc)
        if now.date() > opened.date() or now.hour >= EVENING_EXIT_BAR_HOUR:
            return "evening_exit_2300"
        return None

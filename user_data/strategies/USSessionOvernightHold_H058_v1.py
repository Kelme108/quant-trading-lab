"""H-058: US cash-session weakness, overnight hold.

Closed 1h candles, UTC clock. Freqtrade dates a candle by its open time, so the "19:00 bar" is the row dated
19:00 (covering 19:00-20:00); a signal on it fills at the 20:00 open.

US SESSION of UTC day d = the 1h bars opening 13:00..19:00 UTC of day d.
  S(d) = close(19:00 bar of d) / open(13:00 bar of d) - 1
ENTRY at the close of the 19:00 bar of day d when its weekday is Mon-Fri (dayofweek 0-4) and S(d) < +0.003.
  No signal that day if the 13:00 or the 19:00 bar is missing. One position per pair (engine).
EXIT at the close of the 12:00 UTC bar (sell at the 13:00 open of day d+1), regardless of price.
  Backstop (custom_exit): any trade open for 17 hours or more exits at the next bar open.
STOP: fixed 3% below entry, the engine's native intrabar stoploss. No take-profit, no cooldown, no other filters.
"""

from datetime import timedelta

import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

SESSION_FIRST_BAR_HOUR = 13
SESSION_LAST_BAR_HOUR = 19
SESSION_THRESHOLD = 0.003
EXIT_SIGNAL_BAR_HOUR = 12
MAX_HOLD = timedelta(hours=17)
SIGNAL_WEEKDAYS = (0, 1, 2, 3, 4)


class USSessionOvernightHold_H058_v1(IStrategy):
    """Buy at 20:00 UTC after a US session that did not rally 0.3%; sell at the 13:00 UTC open next day."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 24

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        hour = date.dt.hour
        day = date.dt.floor("D")

        # Open of the 13:00 bar of the same UTC day, carried forward within the day only (backward-looking).
        open_13 = dataframe["open"].where(hour == SESSION_FIRST_BAR_HOUR)
        session_open = open_13.groupby(day.to_numpy()).ffill()

        session_close = hour == SESSION_LAST_BAR_HOUR
        dataframe["hour"] = hour.to_numpy()
        dataframe["weekday"] = date.dt.day_of_week.to_numpy()
        dataframe["session_open"] = session_open.where(session_close).to_numpy(dtype=float)
        dataframe["session_ret"] = (dataframe["close"] / dataframe["session_open"] - 1.0).where(session_close)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            (dataframe["hour"] == SESSION_LAST_BAR_HOUR)
            & dataframe["weekday"].isin(SIGNAL_WEEKDAYS)
            & dataframe["session_ret"].notna()
            & (dataframe["session_ret"] < SESSION_THRESHOLD)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        dataframe.loc[ok, ["enter_long", "enter_tag"]] = (1, "us_session_weak")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_bar = (dataframe["hour"] == EXIT_SIGNAL_BAR_HOUR) & (dataframe["volume"] > 0)
        dataframe.loc[exit_bar, ["exit_long", "exit_tag"]] = (1, "time_exit_13utc")
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """Backstop: a trade open for 17 hours or more exits at this bar open (covers missing bars)."""
        if current_time >= trade.open_date_utc + MAX_HOLD:
            return "time_backstop_17h"
        return None

"""H-082: hourly 10-day closing extreme, 24h hold.

Rule (1h, closed candles only, long only, spot):
- MAX240(t) = highest close of bars t-240..t-1, MIN240(t) = lowest close of bars t-240..t-1
  (current bar excluded: rolling(240) then shift(1)).
- Entry at the close of bar t when close(t) > MAX240(t) OR close(t) < MIN240(t); fill at the next open.
- Exit: time only, once the trade has been open for >= 24 hours (custom_exit; in backtesting this fires on
  the candle that opens 24h after the entry fill, i.e. the open of bar t+25).
- No take-profit, no indicator exit, no trailing stop. The mandatory native stop is -0.99. No cooldown.
"""

from datetime import timedelta

from pandas import DataFrame

from freqtrade.strategy import IStrategy

LOOKBACK = 240
HOLD = timedelta(hours=24)


class HourlyTenDayExtreme_H082_v1(IStrategy):
    """Buy a 1h close beyond its prior 240-bar closing high or low; hold 24h."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.99
    trailing_stop = False
    use_exit_signal = True
    startup_candle_count = 300

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["max240"] = dataframe["close"].rolling(LOOKBACK).max().shift(1)
        dataframe["min240"] = dataframe["close"].rolling(LOOKBACK).min().shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        at_max = dataframe["close"] > dataframe["max240"]
        at_min = dataframe["close"] < dataframe["min240"]
        defined = dataframe["max240"].notna() & dataframe["min240"].notna() & dataframe["close"].notna()
        live = dataframe["volume"] > 0
        dataframe.loc[at_max & defined & live, ["enter_long", "enter_tag"]] = (1, "at_max240")
        dataframe.loc[at_min & defined & live, ["enter_long", "enter_tag"]] = (1, "at_min240")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Time exit only (see custom_exit); no indicator exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_time - trade.open_date_utc >= HOLD:
            return "time_24h"
        return None

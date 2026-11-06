"""H-024: Daily lottery-jump (MAX) persistence gate with 20-day mean exit.

Signals use closed daily (UTC) candles from the 1d informative frame, merged by
Freqtrade so a daily value is visible only after that day has closed. Orders
execute on the 1h chart at the next open. Spot long only.

Daily definitions (d = just-closed day):
- r(d) = C(d)/C(d-1) - 1; MAX(d) = max of r(d-29..d).
- Jump regime ON when MAX(d) >= median of MAX(d-150..d-1) (today excluded).
- Entry: regime ON AND C(d) > SMA50(d) AND C(d) > highest close of d-10..d-1.
- Exit: C(d) < SMA20(d), or the 12% native stop.
- Cooldown: 72 hourly candles after any exit.
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy, informative


class DailyMaxJumpMomentum_H024_v1(IStrategy):
    """MAX-jump regime plus trend and breakout confirmation on daily closes."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.12
    startup_candle_count = 4400

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 72}]

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        daily_return = dataframe["close"] / dataframe["close"].shift(1) - 1.0
        max30 = daily_return.rolling(30).max()
        dataframe["max30"] = max30
        # Median of the 150 previous MAX values, excluding today.
        dataframe["max_median150"] = max30.shift(1).rolling(150).median()
        dataframe["sma50"] = dataframe["close"].rolling(50).mean()
        dataframe["sma20"] = dataframe["close"].rolling(20).mean()
        # Highest close of the 10 days before today.
        dataframe["high10_prev"] = dataframe["close"].shift(1).rolling(10).max()
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["max30_1d"].notna()
                & dataframe["max_median150_1d"].notna()
                & dataframe["sma50_1d"].notna()
                & dataframe["high10_prev_1d"].notna()
                & (dataframe["max30_1d"] >= dataframe["max_median150_1d"])
                & (dataframe["close_1d"] > dataframe["sma50_1d"])
                & (dataframe["close_1d"] > dataframe["high10_prev_1d"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "max_jump_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["sma20_1d"].notna()
                & (dataframe["close_1d"] < dataframe["sma20_1d"])
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "close_below_sma20")
        return dataframe

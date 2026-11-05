"""H-026: Daily nearness-to-26-week-high anchoring gate with hysteresis exit.

Signals use closed daily (UTC) candles from the 1d informative frame, merged by
Freqtrade so a daily value is visible only after that day has closed. Orders
execute on the 1h chart at the next open. Spot long only.

Daily definitions (d = just-closed day):
- H(d) = highest daily HIGH of the 182 daily candles ending at d (d included).
- N(d) = close(d) / H(d).
- Entry: N(d) >= 0.95 (Freqtrade holds one position per pair).
- Exit: N(d) < 0.85. Between 0.85 and 0.95 the state is held.
- No binding stop (stoploss -0.99 only satisfies the engine contract).
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy, informative


class NearHighAnchorGate_H026_v1(IStrategy):
    """Enter near the 182-day high, exit on a 15% drawdown from it."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.99
    startup_candle_count = 4400

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["high182"] = dataframe["high"].rolling(182).max()
        dataframe["nearness"] = dataframe["close"] / dataframe["high182"]
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["nearness_1d"].notna()
                & (dataframe["nearness_1d"] >= 0.95)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "near_182d_high")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["nearness_1d"].notna()
                & (dataframe["nearness_1d"] < 0.85)
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "below_85pct_of_high")
        return dataframe

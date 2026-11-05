"""H-022: Connors 3-day lower highs and lows pullback inside a 200-day uptrend.

Signals use closed daily (UTC) candles from the 1d informative frame, merged by
Freqtrade so a daily value is visible only after that day has closed. Orders
execute on the 1h chart at the next open. Spot long only.

Rules (daily data, indicators include the just-closed day d):
- Falling range: H(d)<H(d-1), L(d)<L(d-1), H(d-1)<H(d-2), L(d-1)<L(d-2),
  H(d-2)<H(d-3), L(d-2)<L(d-3) (strict).
- Entry: close > SMA(200) AND close < SMA(5) AND falling range.
- Exit: daily close above SMA(5) OR daily close below SMA(200); hard stop 12%.
- No cooldown. Exposure is set by the lab, not here.
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy, informative


class ThreeDayLowerRangeDip_H022_v1(IStrategy):
    """Connors 3-day lower range dip on daily closes, executed on 1h."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.12
    startup_candle_count = 400

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma200"] = dataframe["close"].rolling(200).mean()
        dataframe["sma5"] = dataframe["close"].rolling(5).mean()
        high = dataframe["high"]
        low = dataframe["low"]
        falling = (
            (high < high.shift(1))
            & (low < low.shift(1))
            & (high.shift(1) < high.shift(2))
            & (low.shift(1) < low.shift(2))
            & (high.shift(2) < high.shift(3))
            & (low.shift(2) < low.shift(3))
        )
        defined = high.shift(3).notna() & low.shift(3).notna()
        dataframe["falling3"] = (falling & defined).astype(int)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["sma200_1d"].notna()
                & dataframe["sma5_1d"].notna()
                & dataframe["falling3_1d"].notna()
                & (dataframe["close_1d"] > dataframe["sma200_1d"])
                & (dataframe["close_1d"] < dataframe["sma5_1d"])
                & (dataframe["falling3_1d"] == 1)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "daily_3d_lower_range_dip")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["sma200_1d"].notna()
                & dataframe["sma5_1d"].notna()
                & (
                    (dataframe["close_1d"] > dataframe["sma5_1d"])
                    | (dataframe["close_1d"] < dataframe["sma200_1d"])
                )
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "daily_close_sma5_or_below_sma200")
        return dataframe

"""H-047: relative-strength ratio breakout vs the other two pairs, 1h, long only.

Closed candles only; orders execute on the following candle. Spot long only.

For traded pair X, Y = sqrt(close_A * close_B) of the other two pairs among
BTC/USDT, ETH/USDT, BNB/USDT (informative 1h pairs aligned on candle date).
R = close_X / Y.

- Entry: R > SMA(480) of R, R >= max R over the last 120 bars (incl. t),
  close_X > SMA(480) of close_X.
- Exit: R < SMA(48) of R OR close_X < SMA(480) of close_X.
- 6% hard stop via stoploss; 12-candle cooldown after any exit.
"""

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy

PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]


class RelativeStrengthRatioRotation_H047_v1(IStrategy):
    """Ratio-to-basket breakout with a ratio-weakness exit."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.06
    startup_candle_count = 500

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 12}]

    def informative_pairs(self):
        return [(pair, "1h") for pair in PAIRS]

    def _others(self, pair: str) -> list:
        return [p for p in PAIRS if p != pair]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        others = self._others(metadata.get("pair", ""))
        closes = []
        for other in others:
            other_df = self.dp.get_pair_dataframe(pair=other, timeframe="1h")
            series = other_df.drop_duplicates("date").set_index("date")["close"]
            closes.append(dataframe["date"].map(series).astype(float))

        if len(closes) == 2:
            basket = np.sqrt(closes[0] * closes[1])
            ratio = dataframe["close"] / basket
        else:
            ratio = dataframe["close"] * np.nan
        ratio = ratio.replace([np.inf, -np.inf], np.nan)

        dataframe["ratio"] = ratio
        dataframe["ratio_sma_entry"] = ratio.rolling(480).mean()
        dataframe["ratio_high"] = ratio.rolling(120).max()
        dataframe["ratio_sma_exit"] = ratio.rolling(48).mean()
        dataframe["close_sma_regime"] = dataframe["close"].rolling(480).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["ratio"].notna()
                & dataframe["ratio_sma_entry"].notna()
                & dataframe["ratio_high"].notna()
                & dataframe["close_sma_regime"].notna()
                & (dataframe["ratio"] > dataframe["ratio_sma_entry"])
                & (dataframe["ratio"] >= dataframe["ratio_high"])
                & (dataframe["close"] > dataframe["close_sma_regime"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "ratio_breakout120")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["ratio"].notna()
                & dataframe["ratio_sma_exit"].notna()
                & dataframe["close_sma_regime"].notna()
                & (
                    (dataframe["ratio"] < dataframe["ratio_sma_exit"])
                    | (dataframe["close"] < dataframe["close_sma_regime"])
                )
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "ratio_weak_or_regime_lost")
        return dataframe

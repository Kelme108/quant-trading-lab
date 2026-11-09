"""H-090: 1h relative-strength ratio breakout vs BTC/ETH/BNB basket, flat within the UTC day.

Closed candles only; orders execute on the following candle. Spot long only.

Y = geometric mean of BTC/ETH/BNB closes excluding the traded pair. R = close_X / Y.
- Entry: R > SMA(40) R, R >= max R of last 10 bars (incl. t), close > SMA(40) close,
  bar opens 00:00-15:00 UTC, fewer than 2 entries already filled on the UTC day.
- Exit: R < SMA(4) R or close < SMA(40) close; forced exit signal at the bar opening
  22:00 UTC (fill at 23:00 open); max hold 12h via custom_exit.
- 2% stop via stoploss; 1-candle cooldown via protections.
"""

from datetime import timedelta

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy

PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]


class RelativeStrengthRatioRotation_H090_v1(IStrategy):
    """Ratio-to-basket breakout, intraday, with time exits."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    startup_candle_count = 50

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 1}]

    def informative_pairs(self):
        return [(pair, "1h") for pair in PAIRS]

    def _basket_members(self, pair: str) -> list:
        return [p for p in PAIRS if p != pair]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        members = self._basket_members(metadata.get("pair", ""))
        closes = []
        for member in members:
            member_df = self.dp.get_pair_dataframe(pair=member, timeframe="1h")
            series = member_df.drop_duplicates("date").set_index("date")["close"]
            closes.append(dataframe["date"].map(series).astype(float))

        product = None
        for c in closes:
            product = c if product is None else product * c
        if product is None:
            basket = dataframe["close"] * np.nan
        else:
            basket = product ** (1.0 / len(closes))
        ratio = (dataframe["close"] / basket).replace([np.inf, -np.inf], np.nan)

        dataframe["ratio"] = ratio
        dataframe["ratio_sma_entry"] = ratio.rolling(40).mean()
        dataframe["ratio_high"] = ratio.rolling(10).max()
        dataframe["ratio_sma_exit"] = ratio.rolling(4).mean()
        dataframe["close_sma_regime"] = dataframe["close"].rolling(40).mean()
        dataframe["bar_hour"] = dataframe["date"].dt.hour
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
                & (dataframe["bar_hour"] >= 0)
                & (dataframe["bar_hour"] <= 15)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "ratio_breakout10")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        weak = (
            dataframe["ratio"].notna()
            & dataframe["ratio_sma_exit"].notna()
            & dataframe["close_sma_regime"].notna()
            & (
                (dataframe["ratio"] < dataframe["ratio_sma_exit"])
                | (dataframe["close"] < dataframe["close_sma_regime"])
            )
        )
        dataframe.loc[
            weak & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "ratio_weak_or_regime_lost")
        dataframe.loc[
            (dataframe["bar_hour"] == 22) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "time_exit_2300")
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_time - trade.open_date_utc >= timedelta(hours=12):
            return "time_exit_12h"
        return None

    def confirm_trade_entry(
        self, pair, order_type, amount, rate, time_in_force, current_time, entry_tag, side, **kwargs
    ) -> bool:
        from freqtrade.persistence import Trade

        day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        count = 0
        for t in Trade.get_trades_proxy(pair=pair):
            opened = t.open_date_utc
            if opened >= day_start and opened < day_start + timedelta(days=1):
                count += 1
        return count < 2

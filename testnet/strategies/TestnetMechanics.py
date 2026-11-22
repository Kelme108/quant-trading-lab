"""Order-mechanics exerciser for the Binance SPOT TESTNET. NOT a research strategy.

It exists only to make real orders reach the testnet server often enough to test
the plumbing (API keys, limit fills, stoploss_on_exchange, restarts, rejections).
It lives outside user_data/strategies on purpose: the lab never scans, backtests
or ranks it, and its testnet results carry no information about any market.

Rules, on closed 5m candles:
- Entry: the candle that opened at minute 00 of each hour (one entry per hour).
- Exit: the candle that opened at minute 15, or the exchange-side stop at -3%.
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy


class TestnetMechanics(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    can_short = False
    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 0
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["minute"] = dataframe["date"].dt.minute
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["minute"] == 0, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["minute"] == 15, "exit_long"] = 1
        return dataframe

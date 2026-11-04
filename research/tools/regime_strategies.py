"""Strategy sources for the step 1.4 ablation (regime filter on/off). Not hypotheses: written to the strategy path
only for the duration of a run (see ablation_regime.py), never registered in the ledger.

Rule fixed before any run:
- regime(t) = regime_on(daily close, use_vol=USE_VOL, use_trend=<family>) on CLOSED daily candles (merge_informative_pair).
- Entry only while regime is on; the position is also closed when the regime turns off.
- sma200 family: trend_regime (the SMA(200) itself) always on, vol_regime on/off. Execution timeframe 1h.
- donchian family: Donchian(20 entry / 10 exit, prior candles) on 4h candles, stop -10%; no trend_regime; vol_regime on/off.
"""

COMMON = '''
from pandas import DataFrame
from freqtrade.strategy import IStrategy, merge_informative_pair
from regime_filter import regime_on

USE_VOL = {use_vol}
USE_TREND = {use_trend}
'''

BODY = '''

class {name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{tf}"
    can_short = False
    minimal_roi = {{"0": 100.0}}
    stoploss = {stoploss}
    startup_candle_count = 400

    def informative_pairs(self):
        return [(pair, "1d") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        daily = self.dp.get_pair_dataframe(metadata["pair"], "1d")
        daily["regime"] = regime_on(daily["close"], use_vol=USE_VOL, use_trend=USE_TREND).astype(int)
        dataframe = merge_informative_pair(dataframe, daily[["date", "regime"]], self.timeframe, "1d", ffill=True)
{indicators}
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["regime_1d"] == 1){entry_extra} & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "regime_entry")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            ((dataframe["regime_1d"] == 0){exit_extra}) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "regime_off_or_exit")
        return dataframe
'''

SMA_IND = ""
DON_IND = '''        dataframe["don_high"] = dataframe["high"].rolling(20).max().shift(1)
        dataframe["don_low"] = dataframe["low"].rolling(10).min().shift(1)'''


def source(family: str, use_vol: bool, name: str) -> str:
    if family == "sma200":
        head = COMMON.format(use_vol=use_vol, use_trend=True)
        body = BODY.format(name=name, tf="1h", stoploss=-0.99, indicators=SMA_IND, entry_extra="", exit_extra="")
    elif family == "donchian":
        head = COMMON.format(use_vol=use_vol, use_trend=False)
        body = BODY.format(
            name=name, tf="4h", stoploss=-0.10, indicators=DON_IND,
            entry_extra=' & (dataframe["close"] > dataframe["don_high"])',
            exit_extra=' | (dataframe["close"] < dataframe["don_low"])',
        )
    else:
        raise ValueError(family)
    return head + body

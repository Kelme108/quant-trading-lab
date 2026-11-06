"""H-031: buy the laggard after the other two pairs jump (1h, BTC/ETH/BNB USDT).

r(t) = close(t)/close(t-2) - 1 for the traded pair; L(t) = mean of the same
2-bar return of the other two pairs (informative 1h candles, aligned on the same
candle timestamp, closed bars only).
Entry (signal at close of t, fill at open of t+1): L >= 0.015 and r <= L - 0.010.
Exit: time exit. Entry fills at open of bar e, exit signal at close of e+3, fill at
open of e+4. The exit signal is derived by replaying the entry signals with the
one-position rule and the 4-candle cooldown (the stop is not replayed).
Stop: fixed 1.5% (stoploss attribute). Cooldown: 4 candles via protections.
"""

import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
RETURN_BARS = 2
LEADER_THRESHOLD = 0.015
GAP_THRESHOLD = 0.010
HOLD_BARS = 4
COOLDOWN_BARS = 4


class CrossPairCatchUp_H031_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.015
    startup_candle_count = 50

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def informative_pairs(self):
        return [(pair, self.timeframe) for pair in PAIRS]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get("pair")
        dataframe["ret2"] = dataframe["close"] / dataframe["close"].shift(RETURN_BARS) - 1
        dates = pd.to_datetime(dataframe["date"], utc=True)
        leaders = []
        for other in PAIRS:
            if other == pair:
                continue
            inf = self.dp.get_pair_dataframe(pair=other, timeframe=self.timeframe)
            inf_close = pd.Series(
                inf["close"].to_numpy(),
                index=pd.DatetimeIndex(pd.to_datetime(inf["date"], utc=True)),
            )
            inf_close = inf_close[~inf_close.index.duplicated(keep="last")]
            inf_ret = inf_close / inf_close.shift(RETURN_BARS) - 1
            leaders.append(pd.Series(inf_ret.reindex(dates).to_numpy(), index=dataframe.index))
        dataframe["leader_ret2"] = pd.concat(leaders, axis=1).mean(axis=1, skipna=False)

        raw = (
            dataframe["ret2"].notna()
            & dataframe["leader_ret2"].notna()
            & (dataframe["leader_ret2"] >= LEADER_THRESHOLD)
            & (dataframe["ret2"] <= dataframe["leader_ret2"] - GAP_THRESHOLD)
            & (dataframe["volume"] > 0)
        )
        dataframe["raw_entry"] = raw.astype(int)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["raw_entry"] == 1, ["enter_long", "enter_tag"]] = (
            1,
            "laggard_catchup",
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        raw = dataframe["raw_entry"].to_numpy()
        volume = dataframe["volume"].to_numpy()
        exit_idx = []
        next_allowed = 0
        n = len(dataframe)
        for t in range(n):
            if raw[t] == 1 and t >= next_allowed:
                exit_signal = t + 1 + HOLD_BARS - 1  # close of bar e+3, e = t+1
                if exit_signal < n:
                    exit_idx.append(exit_signal)
                # exit fills at t+5; no new signal until cooldown has passed
                next_allowed = exit_signal + 1 + COOLDOWN_BARS - 1
        mask = pd.Series(False, index=dataframe.index)
        if exit_idx:
            mask.iloc[exit_idx] = True
        mask = mask & (dataframe["volume"] > 0)
        dataframe.loc[mask, ["exit_long", "exit_tag"]] = (1, "time_4bars")
        return dataframe

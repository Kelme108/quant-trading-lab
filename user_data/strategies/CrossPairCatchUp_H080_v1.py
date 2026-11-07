"""H-080: BTC-led 15m catch-up, long only, 4-hour time cap.

Closed candles only; signal at the close of bar t, fill at the open of bar t+1.
Leader L = BTC/USDT for every pair except BTC/USDT, whose leader is ETH/USDT
(informative 15m pair aligned on the same candle date).

- b(t)  = close_L(t) / close_L(t-1) - 1
- sL(t) = std (ddof=1) of b over bars t-672..t-1 (current bar excluded)
- VL(t) = volume_L(t) / median(volume_L over t-96..t-1) (current bar excluded)
- x(t)  = close_X(t) / close_X(t-1) - 1
- SMA96_L(t) = mean of close_L over t-95..t

Entry: b >= max(0.006, 2.5*sL), VL >= 2.0, x <= 0.4*b, close_L > SMA96_L.
At entry (signal bar t): T = close_X(t) * (1 + b - x); S = E * (1 - 1.5*b), E = fill.
Exit (custom_exit, on closed candles from the entry bar on), first of:
  close_X >= T; close_X <= S; close of the 16th bar counted from the entry bar.
Native 3% stop (intrabar). No cooldown.
"""

from datetime import timedelta

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy

DEFAULT_LEADER = "BTC/USDT"
LEADER_FOR_BTC = "ETH/USDT"
LEADER_MIN_RETURN = 0.006
LEADER_SIGMA_MULT = 2.5
SIGMA_LOOKBACK = 672
VOLUME_MEDIAN_LOOKBACK = 96
VOLUME_RATIO_MIN = 2.0
LAG_FRACTION_MAX = 0.4
LEADER_SMA_BARS = 96
EXIT_LEVEL_MULT = 1.5
TIME_EXIT_BARS = 16
BAR = timedelta(minutes=15)


def leader_for(pair: str) -> str:
    return LEADER_FOR_BTC if pair.split(":")[0] == DEFAULT_LEADER else DEFAULT_LEADER


class CrossPairCatchUp_H080_v1(IStrategy):
    """Buy a pair that lagged a volume-backed leader surge bar."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 700

    use_exit_signal = True

    def informative_pairs(self):
        return [(DEFAULT_LEADER, "15m"), (LEADER_FOR_BTC, "15m")]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        leader = leader_for(metadata.get("pair", ""))
        leader_df = self.dp.get_pair_dataframe(pair=leader, timeframe=self.timeframe)
        leader_df = leader_df.drop_duplicates("date").set_index("date")
        close_l = dataframe["date"].map(leader_df["close"]).astype(float)
        volume_l = dataframe["date"].map(leader_df["volume"]).astype(float)

        b = close_l / close_l.shift(1) - 1.0
        sigma_l = b.rolling(SIGMA_LOOKBACK).std(ddof=1).shift(1)
        vol_median = volume_l.rolling(VOLUME_MEDIAN_LOOKBACK).median().shift(1)
        vol_ratio = (volume_l / vol_median).replace([np.inf, -np.inf], np.nan)
        x = dataframe["close"] / dataframe["close"].shift(1) - 1.0

        dataframe["lead_close"] = close_l
        dataframe["lead_ret"] = b
        dataframe["lead_sigma"] = sigma_l
        dataframe["lead_vol_ratio"] = vol_ratio
        dataframe["lead_sma"] = close_l.rolling(LEADER_SMA_BARS).mean()
        dataframe["pair_ret"] = x
        dataframe["catchup_target"] = dataframe["close"] * (1.0 + b - x)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        b = dataframe["lead_ret"]
        threshold = np.maximum(LEADER_MIN_RETURN, LEADER_SIGMA_MULT * dataframe["lead_sigma"])
        dataframe.loc[
            (
                b.notna()
                & dataframe["lead_sigma"].notna()
                & dataframe["lead_vol_ratio"].notna()
                & dataframe["lead_sma"].notna()
                & dataframe["pair_ret"].notna()
                & dataframe["catchup_target"].notna()
                & (b >= threshold)
                & (dataframe["lead_vol_ratio"] >= VOLUME_RATIO_MIN)
                & (dataframe["pair_ret"] <= LAG_FRACTION_MAX * b)
                & (dataframe["lead_close"] > dataframe["lead_sma"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "leader_surge_catchup")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # All exits depend on per-trade values and are handled in custom_exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        open_date = trade.open_date_utc
        # Last closed candle: its close time (date + 1 bar) is not after current_time.
        closed = dataframe[dataframe["date"] + BAR <= current_time]
        if len(closed) == 0:
            return None
        candle = closed.iloc[-1]
        # Only candles from the entry bar (fill bar) onwards count.
        if candle["date"] < open_date:
            return None
        if not (candle["volume"] > 0) or np.isnan(candle["close"]):
            return None

        signal = dataframe[dataframe["date"] == open_date - BAR]
        if len(signal) > 0:
            target = signal["catchup_target"].iloc[-1]
            lead_ret = signal["lead_ret"].iloc[-1]
            if not np.isnan(target) and candle["close"] >= target:
                return "catchup_target"
            if not np.isnan(lead_ret):
                exit_level = trade.open_rate * (1.0 - EXIT_LEVEL_MULT * lead_ret)
                if candle["close"] <= exit_level:
                    return "catchup_fail_level"

        # Close of the 16th bar counted from the entry bar (inclusive).
        if candle["date"] >= open_date + (TIME_EXIT_BARS - 1) * BAR:
            return "time_exit_16"
        return None

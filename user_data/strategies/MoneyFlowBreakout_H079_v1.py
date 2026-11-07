"""H-079: Chaikin Money Flow confirmed 1h breakout of the 24-hour high.

Rule (closed 1h bars; signal at the close of bar t, fill at the open of bar t+1; long only, spot):
- MFM(i) = ((close-low) - (high-close)) / (high-low), 0 when high == low. MFV = MFM * volume.
- CMF20(t) = sum(MFV, t-19..t) / sum(volume, t-19..t), 0 when the volume sum is 0.
- H24 / L24 = highest high / lowest low of bars t-24..t-1 (current bar excluded).
- L6 = lowest low of bars t-6..t-1 (current bar excluded).
- Entry when: close > H24, CMF20 >= 0.05, CMF20 > CMF20(t-6), (H24 - L24) / close >= 0.02.
  One open position and the 6-candle cooldown after any exit are handled by the engine
  (max_open_trades and the CooldownPeriod protection).
- Exit when: CMF20 <= -0.05, or close < L6, or the trade has been open 24 bars (custom_exit:
  at the close of the 24th bar after the entry fill, filled at the next open).
- Stop-loss: fixed 2.5% below entry, engine-native (intrabar). No ROI, no trailing stop.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

CMF_PERIOD = 20
CMF_ENTRY_MIN = 0.05
CMF_RISE_LAG_BARS = 6
CMF_EXIT_MAX = -0.05
BREAKOUT_LOOKBACK_BARS = 24
MIN_RANGE_PCT = 0.02
EXIT_LOW_LOOKBACK_BARS = 6
TIME_EXIT_BARS = 24
COOLDOWN_BARS = 6
BAR_HOURS = 1


def chaikin_money_flow(dataframe: DataFrame, period: int) -> pd.Series:
    """CMF over the last `period` bars including the current closed bar. Backward-looking only."""
    high = dataframe["high"]
    low = dataframe["low"]
    close = dataframe["close"]
    bar_range = high - low
    mfm = ((close - low) - (high - close)) / bar_range.replace(0, np.nan)
    mfm = mfm.mask(bar_range == 0, 0.0)
    mfv = mfm * dataframe["volume"]
    mfv_sum = mfv.rolling(period).sum()
    vol_sum = dataframe["volume"].rolling(period).sum()
    cmf = mfv_sum / vol_sum.replace(0, np.nan)
    cmf = cmf.mask(vol_sum == 0, 0.0)
    return cmf


class MoneyFlowBreakout_H079_v1(IStrategy):
    """CMF-confirmed 24-hour-high breakout with distribution, 6-bar-low and 24-bar time exits."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.025
    trailing_stop = False
    use_exit_signal = True
    startup_candle_count = 30

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["cmf20"] = chaikin_money_flow(dataframe, CMF_PERIOD)
        dataframe["cmf20_lag"] = dataframe["cmf20"].shift(CMF_RISE_LAG_BARS)
        dataframe["h24"] = dataframe["high"].rolling(BREAKOUT_LOOKBACK_BARS).max().shift(1)
        dataframe["l24"] = dataframe["low"].rolling(BREAKOUT_LOOKBACK_BARS).min().shift(1)
        dataframe["l6"] = dataframe["low"].rolling(EXIT_LOW_LOOKBACK_BARS).min().shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["cmf20"].notna()
            & dataframe["cmf20_lag"].notna()
            & dataframe["h24"].notna()
            & dataframe["l24"].notna()
        )
        entry = (
            defined
            & (dataframe["close"] > dataframe["h24"])
            & (dataframe["cmf20"] >= CMF_ENTRY_MIN)
            & (dataframe["cmf20"] > dataframe["cmf20_lag"])
            & ((dataframe["h24"] - dataframe["l24"]) / dataframe["close"] >= MIN_RANGE_PCT)
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[entry, ["enter_long", "enter_tag"]] = (1, "cmf_h24_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        volume_ok = dataframe["volume"] > 0
        distribution = dataframe["cmf20"].notna() & (dataframe["cmf20"] <= CMF_EXIT_MAX)
        breakdown = dataframe["l6"].notna() & (dataframe["close"] < dataframe["l6"])
        dataframe.loc[distribution & volume_ok, ["exit_long", "exit_tag"]] = (1, "cmf_distribution")
        dataframe.loc[breakdown & ~distribution & volume_ok, ["exit_long", "exit_tag"]] = (1, "close_below_l6")
        return dataframe

    def custom_exit(self, pair: str, trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs):
        """Time exit: after 24 bars open (close of the 24th bar after the entry fill), exit at the next open."""
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_BARS * BAR_HOURS):
            return "time_exit_24h"
        return None

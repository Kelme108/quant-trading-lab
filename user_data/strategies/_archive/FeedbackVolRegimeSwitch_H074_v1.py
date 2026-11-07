"""H-074: feedback-trading volatility switch on 1h, long only.

Closed candles only; the signal at the close of bar t fills at the open of bar t+1. Spot, long only.

Definitions:
  r(i)  = ln(close(i) / close(i-1))
  sig(t) = sample std (ddof=1) of r over bars t-23..t (current bar included)
  M(t)  = median of sig over bars t-720..t-1 (current bar excluded)
  R6(t) = close(t) / close(t-6) - 1
Regimes: CALM sig < M; VOLATILE sig >= 1.5*M; no entry in between.
ENTRY A (CALM):     R6 >= 2.0*sig*sqrt(6) AND R6 >= 0.012
ENTRY B (VOLATILE): R6 <= -2.0*sig*sqrt(6) AND R6 <= -0.025
EXIT: native 3% stoploss (intrabar), or time exit at the close of the 12th bar after the entry bar
(the candle dated fill + 12h), filled at the next open. Cooldown 6 candles after any exit.
Warm-up 800 bars (745 needed).
"""

import math
from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy

VOL_WINDOW = 24
VOL_DDOF = 1
MEDIAN_WINDOW = 720
RETURN_HORIZON = 6
CALM_MULT = 1.0
VOLATILE_MULT = 1.5
SIGMA_MOVE_MULT = 2.0
MIN_SURGE = 0.012
MIN_DROP = -0.025
TIME_EXIT_BARS = 12
COOLDOWN_BARS = 6
BAR = timedelta(hours=1)


class FeedbackVolRegimeSwitch_H074_v1(IStrategy):
    """Follow 6h surges in calm regimes, fade 6h drops in volatile regimes; 12-bar time exit."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    trailing_stop = False
    use_exit_signal = True
    startup_candle_count = 800

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"].astype(float)
        log_ret = np.log(close / close.shift(1))
        sig = log_ret.rolling(VOL_WINDOW).std(ddof=VOL_DDOF)
        dataframe["log_ret"] = log_ret
        dataframe["sig"] = sig
        dataframe["sig_median"] = sig.shift(1).rolling(MEDIAN_WINDOW).median()
        dataframe["r6"] = close / close.shift(RETURN_HORIZON) - 1.0
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        sig = dataframe["sig"]
        med = dataframe["sig_median"]
        r6 = dataframe["r6"]
        defined = sig.notna() & med.notna() & r6.notna()
        move = SIGMA_MOVE_MULT * sig * math.sqrt(RETURN_HORIZON)

        calm = sig < CALM_MULT * med
        volatile = sig >= VOLATILE_MULT * med
        entry_a = calm & (r6 >= move) & (r6 >= MIN_SURGE)
        entry_b = volatile & (r6 <= -move) & (r6 <= MIN_DROP)
        base = defined & (dataframe["volume"] > 0)

        dataframe.loc[base & entry_a, ["enter_long", "enter_tag"]] = (1, "calm_continuation")
        dataframe.loc[base & entry_b & ~entry_a, ["enter_long", "enter_tag"]] = (1, "volatile_reversal")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # The only signal exit is the 12-bar time exit, which depends on the fill time: see custom_exit.
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        last = dataframe.iloc[-1]
        open_date = pd.Timestamp(trade.open_date_utc)
        candle_date = pd.Timestamp(last["date"])
        if candle_date.tzinfo is None and open_date.tzinfo is not None:
            candle_date = candle_date.tz_localize(open_date.tzinfo)
        elif candle_date.tzinfo is not None and open_date.tzinfo is None:
            open_date = open_date.tz_localize(candle_date.tzinfo)
        if not (last["volume"] > 0) or pd.isna(last["close"]):
            return None
        # Entry bar is dated open_date; the 12th bar after it is dated open_date + 12h.
        if candle_date >= open_date + TIME_EXIT_BARS * BAR:
            return "time_12_bars"
        return None

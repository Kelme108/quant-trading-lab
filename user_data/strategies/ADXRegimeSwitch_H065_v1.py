"""H-065: ADX/volatility regime switch on 1h closed candles.

TREND regime: ADX14 >= 25 and +DI14 > -DI14 and ATRp >= MED, where ATRp = ATR14 / close and MED is the median of
ATRp over the 720 previous bars (t-720..t-1, current bar excluded).
RANGE regime: ADX14 < 20.

Entry 'trend': TREND regime and EMA10 crosses above 1.002 * EMA30 on this bar
(EMA10(t) > 1.002*EMA30(t) and EMA10(t-1) <= 1.002*EMA30(t-1)).
Entry 'range': RANGE regime and RSI14 < 30. Trend takes precedence if both fire.

Exits depend on the entry tag (custom_exit, read on the last closed candle, filled at the next open):
'trend' exits on EMA10 < EMA30; 'range' exits on RSI14 >= 50. Both exit at the latest 24 hours after entry
(open of bar 25 counting the fill bar as bar 1). Stop 3% (native, intrabar). Cooldown 4 candles after any exit.

ADX/DI/ATR/RSI use Wilder smoothing seeded with the simple mean of the first `period` values (as TA-Lib does);
EMA is seeded with the SMA of the first `period` closes. All are causal: a value depends only on earlier rows.
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

ADX_PERIOD = 14
ATR_PERIOD = 14
ATRP_MEDIAN_LOOKBACK = 720
ADX_TREND_MIN = 25.0
ADX_RANGE_MAX = 20.0
EMA_FAST = 10
EMA_SLOW = 30
EMA_CROSS_BUFFER = 1.002
RSI_PERIOD = 14
RSI_ENTRY_BELOW = 30.0
RSI_EXIT_AT_OR_ABOVE = 50.0
TIME_EXIT_BARS = 24
COOLDOWN_BARS = 4


def _recursive_smooth(values: np.ndarray, period: int, alpha: float) -> np.ndarray:
    """Seed with the mean of the first `period` defined values, then s = s + alpha * (x - s). Backward-only."""
    out = np.full(len(values), np.nan)
    defined = np.flatnonzero(~np.isnan(values))
    if len(defined) == 0:
        return out
    start = defined[0]
    seed_end = start + period - 1
    if seed_end >= len(values):
        return out
    state = float(np.mean(values[start : seed_end + 1]))
    out[seed_end] = state
    for i in range(seed_end + 1, len(values)):
        state = state + alpha * (values[i] - state)
        out[i] = state
    return out


def wilder(values: pd.Series, period: int) -> pd.Series:
    return pd.Series(
        _recursive_smooth(values.to_numpy(dtype=float), period, 1.0 / period), index=values.index
    )


def ema_sma_seeded(values: pd.Series, period: int) -> pd.Series:
    return pd.Series(
        _recursive_smooth(values.to_numpy(dtype=float), period, 2.0 / (period + 1)), index=values.index
    )


def true_range(dataframe: DataFrame) -> pd.Series:
    prev_close = dataframe["close"].shift(1)
    ranges = pd.concat(
        [
            dataframe["high"] - dataframe["low"],
            (dataframe["high"] - prev_close).abs(),
            (dataframe["low"] - prev_close).abs(),
        ],
        axis=1,
    )
    tr = ranges.max(axis=1)
    tr[prev_close.isna()] = np.nan
    return tr


def adx_di(dataframe: DataFrame, period: int):
    up = dataframe["high"] - dataframe["high"].shift(1)
    down = dataframe["low"].shift(1) - dataframe["low"]
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=dataframe.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=dataframe.index)
    plus_dm[up.isna()] = np.nan
    minus_dm[up.isna()] = np.nan
    tr_s = wilder(true_range(dataframe), period)
    plus_di = 100.0 * wilder(plus_dm, period) / tr_s
    minus_di = 100.0 * wilder(minus_dm, period) / tr_s
    di_sum = plus_di + minus_di
    dx = 100.0 * (plus_di - minus_di).abs() / di_sum
    dx = dx.where(~((di_sum == 0) & plus_di.notna()), 0.0)
    adx = wilder(dx, period)
    return adx, plus_di, minus_di


def rsi_wilder(close: pd.Series, period: int) -> pd.Series:
    diff = close.diff()
    gain = diff.clip(lower=0.0)
    loss = (-diff).clip(lower=0.0)
    avg_gain = wilder(gain, period)
    avg_loss = wilder(loss, period)
    total = avg_gain + avg_loss
    rsi = 100.0 * avg_gain / total
    return rsi.where(total > 0)


class ADXRegimeSwitch_H065_v1(IStrategy):
    """ADX/DI + ATR-percentile regime switch: EMA-cross momentum in trends, RSI dips in ranges."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    trailing_stop = False
    use_custom_stoploss = False
    use_exit_signal = True
    process_only_new_candles = True
    startup_candle_count = 1000

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        adx, plus_di, minus_di = adx_di(dataframe, ADX_PERIOD)
        dataframe["adx"] = adx
        dataframe["plus_di"] = plus_di
        dataframe["minus_di"] = minus_di
        dataframe["atr"] = wilder(true_range(dataframe), ATR_PERIOD)
        dataframe["atrp"] = dataframe["atr"] / dataframe["close"]
        dataframe["atrp_med"] = dataframe["atrp"].shift(1).rolling(ATRP_MEDIAN_LOOKBACK).median()
        dataframe["ema_fast"] = ema_sma_seeded(dataframe["close"], EMA_FAST)
        dataframe["ema_slow"] = ema_sma_seeded(dataframe["close"], EMA_SLOW)
        dataframe["rsi"] = rsi_wilder(dataframe["close"], RSI_PERIOD)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        live = dataframe["volume"] > 0
        trend_ready = (
            dataframe[["adx", "plus_di", "minus_di", "atrp", "atrp_med", "ema_fast", "ema_slow"]].notna().all(axis=1)
            & dataframe["ema_fast"].shift(1).notna()
            & dataframe["ema_slow"].shift(1).notna()
        )
        trend_regime = (
            (dataframe["adx"] >= ADX_TREND_MIN)
            & (dataframe["plus_di"] > dataframe["minus_di"])
            & (dataframe["atrp"] >= dataframe["atrp_med"])
        )
        level = EMA_CROSS_BUFFER * dataframe["ema_slow"]
        cross_up = (dataframe["ema_fast"] > level) & (dataframe["ema_fast"].shift(1) <= level.shift(1))
        trend_entry = live & trend_ready & trend_regime & cross_up

        range_ready = dataframe["adx"].notna() & dataframe["rsi"].notna()
        range_entry = live & range_ready & (dataframe["adx"] < ADX_RANGE_MAX) & (dataframe["rsi"] < RSI_ENTRY_BELOW)

        dataframe.loc[range_entry, ["enter_long", "enter_tag"]] = (1, "range")
        # Trend entry takes precedence when both are true on the same bar.
        dataframe.loc[trend_entry, ["enter_long", "enter_tag"]] = (1, "trend")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits depend on the entry tag, so they are not a generic exit_long signal. The per-tag conditions are
        # stored here and read by custom_exit on the last closed candle.
        live = dataframe["volume"] > 0
        ema_ready = dataframe["ema_fast"].notna() & dataframe["ema_slow"].notna()
        dataframe["exit_trend_cond"] = (live & ema_ready & (dataframe["ema_fast"] < dataframe["ema_slow"])).astype(int)
        dataframe["exit_range_cond"] = (
            live & dataframe["rsi"].notna() & (dataframe["rsi"] >= RSI_EXIT_AT_OR_ABOVE)
        ).astype(int)
        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> Optional[str]:
        if current_time >= trade.open_date_utc + timedelta(hours=TIME_EXIT_BARS):
            return "time_exit"
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        last = dataframe.iloc[-1]
        tag = trade.enter_tag
        if tag == "trend" and last.get("exit_trend_cond", 0) == 1:
            return "trend_ema_exit"
        if tag == "range" and last.get("exit_range_cond", 0) == 1:
            return "range_rsi_exit"
        return None

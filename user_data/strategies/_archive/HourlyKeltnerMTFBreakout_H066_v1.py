"""H-066: 1h Keltner 2.5-ATR breakout gated by a rising 4h EMA50; ATR stop and target, 16-bar time exit.

Closed 1h candles only; a signal at the close of bar t fills at the open of bar t+1. Spot, long only,
one position per pair (engine), no pyramiding, no trailing, no sizing hooks, no cooldown.

1h indicators:
- EMA50 = EMA(50) of close (SMA-seeded); ATR50, ATR30, ATR20 = Wilder ATR over 50, 30, 20 bars.
- U = EMA50 + 2.5 * ATR50.
- RSI40 = Wilder RSI(40) of the typical price (high + low + close) / 3.
4h filter: 4h candles built from the 1h bars in UTC blocks 00/04/08/12/16/20, attached with
merge_informative_pair, so a 4h candle is visible only once its last 1h bar has closed.
EMA4h = EMA(50) of the 4h close. Holds when close_4h > EMA4h and EMA4h > EMA4h of the completed
4h bar 6 bars earlier.
Entry at the close of bar t when all hold: close(t) > U(t); close(t-1) <= U(t-1); RSI40(t) > 50;
4h filter holds; volume > 0.
Per-trade levels, frozen from the signal bar and written into the entry tag:
- Stop: P - 1.6 * ATR20(t), set once and never moved (custom_stoploss, intrabar). The native
  stoploss is only a far backstop so the ATR stop is never capped by it.
- Target: P + 4.5 * ATR30(t), intrabar (custom_roi at that price; custom_exit if the open is
  already at or above it). The engine checks the stop before ROI, so a bar touching both is a stop.
- Time exit: after bar t+16 closes (16 bars after the fill) -> sell at the open of bar t+17.
Warm-up: 1000 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair

EMA_1H_PERIOD = 50
ATR_BAND_PERIOD = 50
BAND_ATR_MULT = 2.5
RSI_PERIOD = 40
RSI_THRESHOLD = 50.0
EMA_4H_PERIOD = 50
EMA_4H_SLOPE_BARS = 6
ATR_STOP_PERIOD = 20
STOP_ATR_MULT = 1.6
ATR_TARGET_PERIOD = 30
TARGET_ATR_MULT = 4.5
TIME_EXIT_BARS = 16
BAR = timedelta(hours=1)
TAG_PREFIX = "kc"


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


def rsi_wilder(source: pd.Series, period: int) -> pd.Series:
    diff = source.diff()
    gain = diff.clip(lower=0.0)
    loss = (-diff).clip(lower=0.0)
    avg_gain = wilder(gain, period)
    avg_loss = wilder(loss, period)
    total = avg_gain + avg_loss
    rsi = 100.0 * avg_gain / total
    return rsi.where(total > 0)


def hourly_indicators(dataframe: DataFrame) -> DataFrame:
    """EMA50, ATR50/30/20, upper band, previous-bar band and RSI40 of typical price. Backward only."""
    tr = true_range(dataframe)
    dataframe["ema50"] = ema_sma_seeded(dataframe["close"].astype(float), EMA_1H_PERIOD)
    dataframe["atr50"] = wilder(tr, ATR_BAND_PERIOD)
    dataframe["atr30"] = wilder(tr, ATR_TARGET_PERIOD)
    dataframe["atr20"] = wilder(tr, ATR_STOP_PERIOD)
    dataframe["kc_upper"] = dataframe["ema50"] + BAND_ATR_MULT * dataframe["atr50"]
    # The band of the previous candle and its close, for the "fresh close above the band" test.
    dataframe["kc_upper_prev"] = dataframe["kc_upper"].shift(1)
    dataframe["close_prev"] = dataframe["close"].shift(1)
    typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
    dataframe["rsi40_tp"] = rsi_wilder(typical.astype(float), RSI_PERIOD)
    return dataframe


def four_hour_from_hourly(dataframe: DataFrame) -> DataFrame:
    """4h UTC-block closes from the 1h bars, with EMA(50) and the EMA of the 4h bar 6 bars earlier."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    block = dates.dt.floor("4h")
    block_close = dataframe["close"].astype(float).groupby(block.to_numpy()).last()
    index = pd.DatetimeIndex(block_close.index)
    if index.tz is None:
        index = index.tz_localize("UTC")
    close = pd.Series(block_close.to_numpy(dtype=float), index=range(len(block_close)))
    ema = ema_sma_seeded(close, EMA_4H_PERIOD)
    return DataFrame(
        {
            "date": index,
            "close": close.to_numpy(dtype=float),
            "ema": ema.to_numpy(dtype=float),
            "ema_lag": ema.shift(EMA_4H_SLOPE_BARS).to_numpy(dtype=float),
        }
    )


def make_tag(atr20: float, atr30: float) -> str:
    return f"{TAG_PREFIX}|{atr20!r}|{atr30!r}"


def parse_tag(tag) -> tuple[float, float] | None:
    """(ATR20, ATR30) of the signal bar recorded in an entry tag, or None for a foreign tag."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 3 or parts[0] != TAG_PREFIX:
        return None
    try:
        atr20, atr30 = float(parts[1]), float(parts[2])
    except ValueError:
        return None
    if not (atr20 > 0 and atr30 > 0):
        return None
    return atr20, atr30


class HourlyKeltnerMTFBreakout_H066_v1(IStrategy):
    """Fresh 1h close above EMA50 + 2.5 ATR50 in a rising 4h EMA50 trend; ATR stop/target, 16h cap."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    # Far backstop only: the frozen ATR stop is set by custom_stoploss and must not be capped.
    stoploss = -0.99
    use_custom_stoploss = True
    use_custom_roi = True
    use_exit_signal = True
    trailing_stop = False
    startup_candle_count = 1000

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = hourly_indicators(dataframe)
        four_hour = four_hour_from_hourly(dataframe)
        dataframe = merge_informative_pair(dataframe, four_hour, self.timeframe, "4h", ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        cond = (
            close.notna()
            & dataframe["kc_upper"].notna()
            & dataframe["kc_upper_prev"].notna()
            & dataframe["close_prev"].notna()
            & dataframe["rsi40_tp"].notna()
            & dataframe["atr20"].notna()
            & dataframe["atr30"].notna()
            & dataframe["close_4h"].notna()
            & dataframe["ema_4h"].notna()
            & dataframe["ema_lag_4h"].notna()
            & (close > dataframe["kc_upper"])
            & (dataframe["close_prev"] <= dataframe["kc_upper_prev"])
            & (dataframe["rsi40_tp"] > RSI_THRESHOLD)
            & (dataframe["close_4h"] > dataframe["ema_4h"])
            & (dataframe["ema_4h"] > dataframe["ema_lag_4h"])
            & (dataframe["atr20"] > 0)
            & (dataframe["atr30"] > 0)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            tags = [
                make_tag(float(a20), float(a30))
                for a20, a30 in zip(dataframe.loc[cond, "atr20"], dataframe.loc[cond, "atr30"])
            ]
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = tags
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Stop, target and time exit all depend on the open trade: see the custom_* callbacks.
        return dataframe

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        """Stop price P - 1.6 * ATR20(t), fixed at entry, expressed relative to the current rate."""
        recorded = parse_tag(trade.enter_tag)
        if recorded is None or not current_rate or not trade.open_rate:
            return None
        atr20, _ = recorded
        stop_price = trade.open_rate - STOP_ATR_MULT * atr20
        if stop_price <= 0:
            return None
        return max(1.0 - stop_price / current_rate, 0.0)

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side, **kwargs):
        """ROI whose exit price is exactly P + 4.5 * ATR30(t) after the engine's fee adjustment."""
        recorded = parse_tag(trade.enter_tag)
        if recorded is None or not trade.open_rate:
            return None
        _, atr30 = recorded
        target = trade.open_rate + TARGET_ATR_MULT * atr30
        fee_open = trade.fee_open or 0.0
        fee_close = trade.fee_close or 0.0
        return (target * (1.0 - fee_close) - trade.open_rate * (1.0 + fee_open)) / trade.open_rate

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        recorded = parse_tag(trade.enter_tag)
        if recorded is not None and trade.open_rate:
            _, atr30 = recorded
            if current_rate >= trade.open_rate + TARGET_ATR_MULT * atr30:
                return "target_4p5_atr30"
        # Filled at the open of t+1; bar t+16 closes 16 bars later -> sell at the open of t+17.
        if current_time >= trade.open_date_utc + TIME_EXIT_BARS * BAR:
            return "time_exit_16_bars"
        return None

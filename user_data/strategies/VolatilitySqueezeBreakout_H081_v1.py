"""H-081: 15m TTM squeeze fire with rising positive momentum and a closed-4h EMA50 uptrend filter.

Closed 15m bars only; a signal at the close of bar t fills at the open of bar t+1. Long only, spot,
one position per pair (engine), no pyramiding, no take-profit, no cooldown.

Indicators (15m):
- SMA20 = 20-bar mean of close; std20 = 20-bar population std of close (ddof=0).
- BBU/BBL = SMA20 +/- 2.0 * std20.
- ATR20 = Wilder ATR (true range smoothed with alpha 1/20).
- KCU/KCL = SMA20 +/- 1.5 * ATR20.
- SQUEEZE_ON(t) = BBU(t) < KCU(t) and BBL(t) > KCL(t).
- Mid(t) = ((highest high t-19..t + lowest low t-19..t) / 2 + SMA20(t)) / 2.
- MOM(t) = linreg(close - Mid, 20, 0): OLS line over bars t-19..t (x = 0..19), fitted at x = 19.
4h filter: 4h candles built from the 15m data in UTC blocks 00/04/08/12/16/20, attached with
merge_informative_pair (ffill), so a 4h bar is visible only once it has closed.
EMA50_4h = 50-period EMA of the 4h close (adjust=False).

Entry at the close of bar t when all hold:
(1) SQUEEZE_ON on each of bars t-6..t-1 and SQUEEZE_ON(t) false (the fire);
(2) MOM(t) > 0 and MOM(t) > MOM(t-1);
(3) close(t) > KCU(t);
(4) last closed 4h close > its EMA50_4h and that EMA50_4h > EMA50_4h of the previous 4h bar.
Exit, first of:
(a) MOM(t) < MOM(t-1) and MOM(t-1) < MOM(t-2) (exit signal);
(b) close(t) < SMA20(t) (exit signal);
(c) 32 bars (8 hours) after entry (custom_exit, sells at that open);
native 1.5% stoploss (intrabar).
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair

BAR = timedelta(minutes=15)
LENGTH = 20
BB_STD = 2.0
KC_ATR_MULT = 1.5
MIN_SQUEEZE_BARS = 6
EMA_4H_LENGTH = 50
TIME_EXIT_BARS = 32


def linreg_last(values: pd.Series, length: int) -> pd.Series:
    """Fitted value at the last point of an OLS line over the trailing `length` values (x = 0..length-1)."""
    x = np.arange(length, dtype=float)
    x_mean = x.mean()
    sxx = float(((x - x_mean) ** 2).sum())
    # fitted(last) = mean(y) + slope * (x_last - x_mean), slope = sum((x - x_mean) * y) / sxx
    weights = 1.0 / length + (x - x_mean) * (x[-1] - x_mean) / sxx
    arr = values.to_numpy(dtype=float)
    out = np.full(len(arr), np.nan)
    if len(arr) >= length:
        windows = np.lib.stride_tricks.sliding_window_view(arr, length)
        out[length - 1:] = windows @ weights
    return pd.Series(out, index=values.index)


def squeeze_indicators(dataframe: DataFrame) -> DataFrame:
    """15m Bollinger/Keltner squeeze and momentum. Backward-looking only."""
    close = dataframe["close"]
    high = dataframe["high"]
    low = dataframe["low"]

    sma20 = close.rolling(LENGTH).mean()
    std20 = close.rolling(LENGTH).std(ddof=0)
    prev_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr20 = true_range.ewm(alpha=1.0 / LENGTH, adjust=False).mean()

    dataframe["sma20"] = sma20
    dataframe["bbu"] = sma20 + BB_STD * std20
    dataframe["bbl"] = sma20 - BB_STD * std20
    dataframe["atr20"] = atr20
    dataframe["kcu"] = sma20 + KC_ATR_MULT * atr20
    dataframe["kcl"] = sma20 - KC_ATR_MULT * atr20

    defined = dataframe[["bbu", "bbl", "kcu", "kcl"]].notna().all(axis=1)
    squeeze_on = defined & (dataframe["bbu"] < dataframe["kcu"]) & (dataframe["bbl"] > dataframe["kcl"])
    dataframe["squeeze_defined"] = defined.astype(float)
    dataframe["squeeze_on"] = squeeze_on.astype(float).where(defined)
    # Bars t-6..t-1 all in squeeze (NaN while any of them is undefined).
    dataframe["squeeze_prior"] = dataframe["squeeze_on"].shift(1).rolling(MIN_SQUEEZE_BARS).sum()

    mid = ((high.rolling(LENGTH).max() + low.rolling(LENGTH).min()) / 2.0 + sma20) / 2.0
    dataframe["mid"] = mid
    mom = linreg_last(close - mid, LENGTH)
    dataframe["mom"] = mom
    dataframe["mom_1"] = mom.shift(1)
    dataframe["mom_2"] = mom.shift(2)
    return dataframe


def four_hour_from_intraday(dataframe: DataFrame) -> DataFrame:
    """4h UTC-block closes from the 15m bars on a gap-free calendar, with EMA50 and its previous value."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    block = dates.dt.floor("4h")
    block_close = dataframe["close"].groupby(block.to_numpy()).last()
    block_close.index = pd.DatetimeIndex(block_close.index)
    if block_close.index.tz is None:
        block_close.index = block_close.index.tz_localize("UTC")
    calendar = pd.date_range(block_close.index.min(), block_close.index.max(), freq="4h")
    block_close = block_close.reindex(calendar)
    ema = block_close.ewm(span=EMA_4H_LENGTH, adjust=False).mean()
    return DataFrame(
        {
            "date": calendar,
            "close": block_close.to_numpy(dtype=float),
            "ema50": ema.to_numpy(dtype=float),
            "ema50_prev": ema.shift(1).to_numpy(dtype=float),
        }
    )


class VolatilitySqueezeBreakout_H081_v1(IStrategy):
    """Buy a 15m TTM squeeze fire up through the Keltner band in a rising closed-4h EMA50 uptrend."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.015
    use_exit_signal = True
    startup_candle_count = 2400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = squeeze_indicators(dataframe)
        four_hour = four_hour_from_intraday(dataframe)
        dataframe = merge_informative_pair(dataframe, four_hour, self.timeframe, "4h", ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        cond = (
            close.notna()
            & dataframe["squeeze_prior"].notna()
            & (dataframe["squeeze_defined"] == 1)
            & dataframe["mom"].notna()
            & dataframe["mom_1"].notna()
            & dataframe["kcu"].notna()
            & dataframe["close_4h"].notna()
            & dataframe["ema50_4h"].notna()
            & dataframe["ema50_prev_4h"].notna()
            # (1) squeeze on for each of the 6 prior bars, off on this bar
            & (dataframe["squeeze_prior"] == MIN_SQUEEZE_BARS)
            & (dataframe["squeeze_on"] == 0)
            # (2) positive, rising momentum
            & (dataframe["mom"] > 0)
            & (dataframe["mom"] > dataframe["mom_1"])
            # (3) close above the upper Keltner band
            & (close > dataframe["kcu"])
            # (4) closed-4h uptrend with rising EMA50
            & (dataframe["close_4h"] > dataframe["ema50_4h"])
            & (dataframe["ema50_4h"] > dataframe["ema50_prev_4h"])
            & (dataframe["volume"] > 0)
        ).fillna(False)
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "ttm_squeeze_fire")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        mom_fall = (
            dataframe["mom"].notna()
            & dataframe["mom_1"].notna()
            & dataframe["mom_2"].notna()
            & (dataframe["mom"] < dataframe["mom_1"])
            & (dataframe["mom_1"] < dataframe["mom_2"])
        )
        below_sma = (
            dataframe["close"].notna()
            & dataframe["sma20"].notna()
            & (dataframe["close"] < dataframe["sma20"])
        )
        cond = ((mom_fall | below_sma) & (dataframe["volume"] > 0)).fillna(False)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "mom_fade_or_below_sma20")
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        # Time exit: 32 bars after the fill, sold at that open.
        if current_time >= trade.open_date_utc + TIME_EXIT_BARS * BAR:
            return "time_exit_32_bars"
        return None

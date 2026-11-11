"""H-112: 15m OBV leads price. Buy a fresh 48-hour OBV high while price is within 1.5% below its 48-hour high.

Rule (research/proposals/H-112.json), 15m, closed bars only, long only, spot. A signal at the close of bar t
fills at the open of bar t+1.

Definitions:
- OBV(i) = OBV(i-1) +/- volume(i) by the sign of close(i) - close(i-1) (raw cumulative, no smoothing).
- OBVMAX(t), OBVMIN(t) = max / min OBV over bars t-192..t-1 (current bar excluded).
- HH(t) = highest high of bars t-192..t-1 (current bar excluded).
- L10(t) = lowest low of bars t-9..t (10 bars including the signal bar).
- Filter: last completed 1h close > EMA(50) of 1h closes (1h bars built from the 15m bars, attached with
  merge_informative_pair so only a completed 1h bar is visible).
Entry at the close of bar t when all hold:
  OBV(t) > OBVMAX(t); close < HH; close >= 0.985 * HH; close > open; 1h filter;
  0.008 <= (close - L10) / close <= 0.03;
  cooldown of 16 bars after the last exit (protections); fewer than 3 trades opened on this pair
  during the UTC day (confirm_trade_entry); one position per pair (engine).
The entry tag stores STOP = L10(t) and TARGET = close(t) + 1.5 * (close(t) - L10(t)) as fixed prices.
Exits, first one wins:
- STOP: custom_stoploss keeps the stop at the fixed STOP price (native stoploss -0.04 is a backstop only).
- TAKE-PROFIT: custom_exit when the profit reaches (TARGET - entry_fill) / entry_fill (trade exits at once if <= 0).
- EARLY EXIT: OBV(t) < OBVMIN(t) at the close of a bar -> exit signal, sell at the next open.
- TIME EXIT: custom_exit 48 bars (12 h) after the entry bar.
Warm-up 2000 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, merge_informative_pair

OBV_WINDOW = 192
HIGH_WINDOW = 192
NEAR_HIGH_FRACTION = 0.985
STOP_LOW_WINDOW = 10
MIN_RISK_FRACTION = 0.008
MAX_RISK_FRACTION = 0.03
TARGET_R_MULTIPLE = 1.5
FILTER_EMA_PERIOD = 50
COOLDOWN_BARS = 16
MAX_ENTRIES_PER_UTC_DAY = 3
TIME_EXIT_BARS = 48
BAR = timedelta(minutes=15)
TAG_PREFIX = "obvlead"


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def parse_tag(tag):
    """(stop, target) prices stored in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 3 or parts[0] != TAG_PREFIX:
        return None
    try:
        stop = float(parts[1])
        target = float(parts[2])
    except ValueError:
        return None
    if not (np.isfinite(stop) and np.isfinite(target)) or stop <= 0 or target <= 0:
        return None
    return stop, target


def ema_seeded(values: np.ndarray, period: int) -> np.ndarray:
    """EMA seeded with the simple mean of the first `period` values (TA-Lib convention). Backward-looking."""
    out = np.full(len(values), np.nan)
    if len(values) < period:
        return out
    k = 2.0 / (period + 1.0)
    out[period - 1] = values[:period].mean()
    for i in range(period, len(values)):
        out[i] = k * values[i] + (1.0 - k) * out[i - 1]
    return out


def obv_series(dataframe: DataFrame) -> pd.Series:
    """Raw cumulative on-balance volume."""
    direction = np.sign(dataframe["close"].diff()).fillna(0.0)
    return (direction * dataframe["volume"]).cumsum()


def hourly_filter_frame(dataframe: DataFrame) -> DataFrame:
    """1h closes built from the 15m bars with their EMA(50)."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    hour = dates.dt.floor("h")
    hourly_close = dataframe["close"].groupby(hour.to_numpy()).last()
    hours = pd.DatetimeIndex(hourly_close.index)
    if hours.tz is None:
        hours = hours.tz_localize("UTC")
    ema = ema_seeded(hourly_close.to_numpy(dtype=float), FILTER_EMA_PERIOD)
    return DataFrame({"date": hours, "close": hourly_close.to_numpy(dtype=float), "ema": ema})


class OBVLeadBreakout_H112_v1(IStrategy):
    """Fresh 48h OBV high while close sits within 1.5% under the 48h high; fixed stop, 1.5R target, 12h time exit."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 2000

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        obv = obv_series(dataframe)
        dataframe["obv"] = obv
        # Windows end at t-1: the current bar is excluded.
        dataframe["obv_max"] = obv.shift(1).rolling(OBV_WINDOW).max()
        dataframe["obv_min"] = obv.shift(1).rolling(OBV_WINDOW).min()
        dataframe["hh"] = dataframe["high"].shift(1).rolling(HIGH_WINDOW).max()
        # 10 bars including the signal bar.
        dataframe["l10"] = dataframe["low"].rolling(STOP_LOW_WINDOW).min()
        hourly = hourly_filter_frame(dataframe)
        dataframe = merge_informative_pair(dataframe, hourly, self.timeframe, "1h", ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        risk = close - dataframe["l10"]
        risk_fraction = risk / close
        cond = (
            dataframe["obv"].notna()
            & dataframe["obv_max"].notna()
            & dataframe["hh"].notna()
            & dataframe["l10"].notna()
            & dataframe["close_1h"].notna()
            & dataframe["ema_1h"].notna()
            & (dataframe["volume"] > 0)
            & (dataframe["obv"] > dataframe["obv_max"])
            & (close < dataframe["hh"])
            & (close >= NEAR_HIGH_FRACTION * dataframe["hh"])
            & (close > dataframe["open"])
            & (dataframe["close_1h"] > dataframe["ema_1h"])
            & (risk_fraction >= MIN_RISK_FRACTION)
            & (risk_fraction <= MAX_RISK_FRACTION)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            stops = dataframe.loc[cond, "l10"].astype(float)
            targets = close.loc[cond].astype(float) + TARGET_R_MULTIPLE * risk.loc[cond].astype(float)
            dataframe.loc[cond, "enter_tag"] = [
                f"{TAG_PREFIX}|{float(s)!r}|{float(t)!r}" for s, t in zip(stops, targets)
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            dataframe["obv"].notna()
            & dataframe["obv_min"].notna()
            & (dataframe["volume"] > 0)
            & (dataframe["obv"] < dataframe["obv_min"])
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "exit_long"] = 1
            dataframe.loc[cond, "exit_tag"] = "obv_below_48h_low"
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Fewer than 3 trades opened on this pair during the UTC day of the entry (closed trades count)."""
        if parse_tag(entry_tag) is None:
            return False
        today = utc_day(current_time)
        opened_today = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                opened_today += 1
        return opened_today < MAX_ENTRIES_PER_UTC_DAY

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        """Keep the stop at the fixed STOP price stored at entry (never moved)."""
        parsed = parse_tag(trade.enter_tag)
        if parsed is None or not current_rate or current_rate <= 0:
            return self.stoploss
        stop, _ = parsed
        distance = 1.0 - stop / current_rate
        if distance <= 0:
            # Price is already at or below the stop: stop as tight as possible.
            return -0.0001
        return -min(distance, abs(self.stoploss))

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is not None:
            _, target = parsed
            target_ratio = target / trade.open_rate - 1.0
            if target_ratio <= 0 or current_profit >= target_ratio or current_rate >= target:
                return "take_profit_1_5r"
        if current_time - trade.open_date_utc >= TIME_EXIT_BARS * BAR:
            return "time_exit_12h"
        return None

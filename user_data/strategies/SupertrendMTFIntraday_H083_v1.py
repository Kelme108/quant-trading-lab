"""H-083: 15m Supertrend(10,3) up-flip above the closed-1h EMA200; Supertrend-line stop, 2R target, 24h time exit.

Closed 15m bars only; a signal at the close of bar t fills at the open of bar t+1. Long only, spot, one position
per pair (engine), no pyramiding, no sizing hooks, no cooldown.

15m indicators:
- ATR10 = Wilder ATR(10) (true range smoothed with alpha = 1/10). hl2 = (high + low) / 2.
- BU = hl2 + 3*ATR10, BL = hl2 - 3*ATR10.
- FU(t) = BU(t) if BU(t) < FU(t-1) or close(t-1) > FU(t-1), else FU(t-1).
- FL(t) = BL(t) if BL(t) > FL(t-1) or close(t-1) < FL(t-1), else FL(t-1).
- direction(t) = UP if close(t) > FU(t-1); DOWN if close(t) < FL(t-1); else direction(t-1).
  (Undefined until the first band break.) ST(t) = FL(t) when direction(t) = UP.
1h filter: EMA200 (alpha 2/201) of 1h closes. The 1h candles are built from the 15m bars (1h close = close of
the hour's last 15m bar; a partial leading hour is dropped) and attached with merge_informative_pair, so a 15m bar
only sees the last completed 1h bar.

ENTRY at the close of bar t: direction(t-1) = DOWN and direction(t) = UP and close(t) > EMA200_1h.
S = ST(t) is written into the entry tag and is the fixed stop for the whole trade.
At fill price P: R = P - S; confirm_trade_entry rejects the entry if R / P < 0.004.
EXITS (first hit wins):
1. Stop at S, intrabar (custom_stoploss). Native stoploss -10% is a backstop; Freqtrade never loosens the stop
   below it, so the effective stop is max(S, 0.90 * P).
2. Target P + 2R, intrabar (custom_roi at that price; custom_exit if the rate is already >= target).
3. Trend flip: exit signal at the close of a bar whose direction is DOWN -> sell at the next open. A trade is
   only opened while direction is UP, so the first DOWN bar during a trade is the bar where direction turns DOWN.
   No exit signal is raised on a zero-volume candle (it is raised on the next DOWN candle with volume).
4. Time exit: custom_exit once 24h have passed since the fill (close of the 96th 15m bar after entry).
Warm-up: 3200 15m bars (800 completed 1h bars).
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair

ATR_PERIOD = 10
ST_FACTOR = 3.0
EMA_PERIOD_1H = 200
MIN_RISK_FRACTION = 0.004
REWARD_RISK = 2.0
TIME_EXIT_BARS = 96
BAR = timedelta(minutes=15)
BARS_PER_HOUR = 4
TAG_PREFIX = "st83"


def wilder_atr(dataframe: DataFrame, period: int) -> pd.Series:
    """Wilder ATR: true range smoothed with alpha = 1/period. Causal; NaN until `period` true ranges exist."""
    prev_close = dataframe["close"].shift(1)
    true_range = pd.concat(
        [
            dataframe["high"] - dataframe["low"],
            (dataframe["high"] - prev_close).abs(),
            (dataframe["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1, skipna=False)
    return true_range.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def supertrend(high: np.ndarray, low: np.ndarray, close: np.ndarray, atr: np.ndarray, factor: float):
    """Final bands, direction (1 = UP, -1 = DOWN, NaN = undefined) and ST line. Backward-only recursion."""
    n = len(close)
    hl2 = (high + low) / 2.0
    bu = hl2 + factor * atr
    bl = hl2 - factor * atr
    fu = np.full(n, np.nan)
    fl = np.full(n, np.nan)
    direction = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(bu[i]) or np.isnan(bl[i]):
            continue
        if i == 0 or np.isnan(fu[i - 1]) or np.isnan(fl[i - 1]):
            fu[i] = bu[i]
            fl[i] = bl[i]
            continue
        prev_close = close[i - 1]
        fu[i] = bu[i] if (bu[i] < fu[i - 1] or prev_close > fu[i - 1]) else fu[i - 1]
        fl[i] = bl[i] if (bl[i] > fl[i - 1] or prev_close < fl[i - 1]) else fl[i - 1]
        if close[i] > fu[i - 1]:
            direction[i] = 1.0
        elif close[i] < fl[i - 1]:
            direction[i] = -1.0
        else:
            direction[i] = direction[i - 1]
    st_line = np.where(direction == 1.0, fl, np.nan)
    return fu, fl, direction, st_line


def hourly_ema_from_intraday(dataframe: DataFrame) -> DataFrame:
    """1h candles (close = last 15m close of the hour) and EMA200 of their closes. Partial leading hour dropped."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    hour = dates.dt.floor("h")
    grouped = dataframe["close"].astype(float).groupby(hour)
    hourly = DataFrame({"close": grouped.last(), "bars": grouped.size()})
    if len(hourly) > 0 and hourly["bars"].iloc[0] < BARS_PER_HOUR:
        hourly = hourly.iloc[1:]
    index = pd.DatetimeIndex(hourly.index)
    if index.tz is None:
        index = index.tz_localize("UTC")
    ema = hourly["close"].ewm(span=EMA_PERIOD_1H, adjust=False, min_periods=EMA_PERIOD_1H).mean()
    return DataFrame({"date": index, "ema200": ema.to_numpy(dtype=float)})


def make_tag(stop: float) -> str:
    return f"{TAG_PREFIX}|{float(stop)!r}"


def parse_tag(tag) -> float | None:
    """Stop price S recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 2 or parts[0] != TAG_PREFIX:
        return None
    try:
        value = float(parts[1])
    except ValueError:
        return None
    if not np.isfinite(value) or value <= 0:
        return None
    return value


class SupertrendMTFIntraday_H083_v1(IStrategy):
    """15m Supertrend(10,3) up-flip above closed-1h EMA200; stop at ST line, 2R target, 24h time exit."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    use_custom_stoploss = True
    use_custom_roi = True
    use_exit_signal = True
    trailing_stop = False
    startup_candle_count = 3200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["atr10"] = wilder_atr(dataframe, ATR_PERIOD)
        fu, fl, direction, st_line = supertrend(
            dataframe["high"].to_numpy(dtype=float),
            dataframe["low"].to_numpy(dtype=float),
            dataframe["close"].to_numpy(dtype=float),
            dataframe["atr10"].to_numpy(dtype=float),
            ST_FACTOR,
        )
        dataframe["st_upper"] = fu
        dataframe["st_lower"] = fl
        dataframe["st_dir"] = direction
        dataframe["st_line"] = st_line
        hourly = hourly_ema_from_intraday(dataframe)
        dataframe = merge_informative_pair(dataframe, hourly, self.timeframe, "1h", ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        direction = dataframe["st_dir"]
        prev_direction = direction.shift(1)
        ema = dataframe["ema200_1h"]
        stop = dataframe["st_line"]
        cond = (
            (prev_direction == -1.0)
            & (direction == 1.0)
            & ema.notna()
            & stop.notna()
            & (stop > 0)
            & dataframe["close"].notna()
            & (dataframe["close"] > ema)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [make_tag(value) for value in dataframe.loc[cond, "st_line"]]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["st_dir"] == -1.0)
            & dataframe["close"].notna()
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "exit_long"] = 1
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Reject the entry when the risk to the stop is below 0.4% of the fill price."""
        stop = parse_tag(entry_tag)
        if stop is None or not rate or rate <= 0:
            return False
        return (rate - stop) / rate >= MIN_RISK_FRACTION

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        """Stop price S, fixed for the trade, expressed relative to the current rate."""
        stop = parse_tag(trade.enter_tag)
        if stop is None or not current_rate:
            return None
        return max(1.0 - stop / current_rate, 0.0)

    def _target(self, trade) -> float | None:
        stop = parse_tag(trade.enter_tag)
        if stop is None or not trade.open_rate:
            return None
        risk = trade.open_rate - stop
        if risk <= 0:
            return None
        return trade.open_rate + REWARD_RISK * risk

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side, **kwargs):
        """ROI whose exit price is exactly P + 2R after the engine's fee adjustment."""
        target = self._target(trade)
        if target is None:
            return None
        fee_open = trade.fee_open or 0.0
        fee_close = trade.fee_close or 0.0
        return (target * (1.0 - fee_close) - trade.open_rate * (1.0 + fee_open)) / trade.open_rate

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        target = self._target(trade)
        if target is not None and current_rate >= target:
            return "target_2r"
        if pd.Timestamp(current_time) >= pd.Timestamp(trade.open_date_utc) + TIME_EXIT_BARS * BAR:
            return "time_exit_24h"
        return None

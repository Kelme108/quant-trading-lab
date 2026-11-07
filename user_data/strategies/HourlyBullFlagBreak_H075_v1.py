"""H-075: hourly bull flag. Steep 6-bar pole, tight low-volume 2-8 bar flag, buy the close above the pole high.

Closed 1h bars only; a signal at the close of bar t fills at the open of bar e = t+1. Long only, spot,
one position (engine), whole balance, no pyramiding, no trailing stop, no cooldown.

Pole candidates: every p with t-9 <= p <= t-3 (flag of 2..8 bars), i.e. k = t - p in 3..9:
- pole: high(p) = highest high of bars p..t-1;
  PL(p) = lowest low of bars p-5..p (6 bars); H = high(p) - PL(p); high(p) / PL(p) - 1 >= 0.025.
- flag = bars p+1..t-1; FL = lowest low, FH = highest high of the flag.
  (1) depth:     FL >= high(p) - 0.5 * H
  (2) tightness: FH - FL <= 0.5 * H
  (3) volume:    mean volume of the flag <= 0.7 * mean volume of bars p-5..p
If several p pass (pole, 1-3), the most recent p (smallest k) is used.
Entry at the close of t: close(t) > high(p) of that p, close(t) > SMA168(close) at t, volume > 0, and the pole
(timestamp of bar p) has not been traded before (confirm_trade_entry; pole timestamp, FL and TARGET = FL + H
are written into the entry tag, fixed at entry).
Exits, first of:
(a) target FL + H, intrabar (custom_roi at that price; custom_exit if a bar opens at or above it);
(b) structural stop: a closed bar u after the fill with close(u) < FL -> exit at the open of u+1;
(c) native stop 4% below the fill, intrabar (stoploss = -0.04);
(d) time exit at the open of bar e+24 (24 hours after the fill).
Warm-up: 200 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

BAR = timedelta(hours=1)
POLE_BARS = 6
FLAG_MIN_BARS = 2
FLAG_MAX_BARS = 8
MIN_POLE_RISE = 0.025
MAX_RETRACE_OF_POLE = 0.5
MAX_FLAG_RANGE_OF_POLE = 0.5
FLAG_VOLUME_RATIO_MAX = 0.7
TREND_SMA_BARS = 168
TARGET_MULTIPLE_OF_POLE = 1.0
TIME_EXIT_BARS = 24
TAG_PREFIX = "hbf"


def make_tag(pole_ts: int, flag_low: float, target: float) -> str:
    return f"{TAG_PREFIX}|{int(pole_ts)}|{float(flag_low)!r}|{float(target)!r}"


def parse_tag(tag) -> tuple[int, float, float] | None:
    """(pole timestamp in seconds, FL, TARGET) from an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 4 or parts[0] != TAG_PREFIX:
        return None
    try:
        pole_ts = int(parts[1])
        flag_low = float(parts[2])
        target = float(parts[3])
    except ValueError:
        return None
    if not (np.isfinite(flag_low) and np.isfinite(target)) or flag_low <= 0 or target <= flag_low:
        return None
    return pole_ts, flag_low, target


def bull_flag_indicators(dataframe: DataFrame) -> DataFrame:
    """Add sma168 and, for the most recent valid pole, pole_high, pole_height, flag_low, pole_ts. Backward-only."""
    high = dataframe["high"].astype(float)
    low = dataframe["low"].astype(float)
    close = dataframe["close"].astype(float)
    volume = dataframe["volume"].astype(float)
    dates = pd.to_datetime(dataframe["date"], utc=True)
    epoch = pd.Series(dates.astype("int64").to_numpy() // 10**9, index=dataframe.index, dtype=float)

    dataframe["sma168"] = close.rolling(TREND_SMA_BARS).mean()

    pole_low_6 = low.rolling(POLE_BARS).min()  # lowest low of bars p-5..p, indexed at p
    pole_vol_6 = volume.rolling(POLE_BARS).mean()  # mean volume of bars p-5..p, indexed at p

    n = len(dataframe)
    sel_high = np.full(n, np.nan)
    sel_height = np.full(n, np.nan)
    sel_flag_low = np.full(n, np.nan)
    sel_ts = np.full(n, np.nan)
    chosen = np.zeros(n, dtype=bool)

    # k = t - p; smallest k is the most recent pole and takes priority.
    for k in range(FLAG_MIN_BARS + 1, FLAG_MAX_BARS + 2):
        flag_len = k - 1
        hp = high.shift(k)
        pl = pole_low_6.shift(k)
        height = hp - pl
        max_p_to_prev = high.shift(1).rolling(k).max()  # bars t-k .. t-1 = p .. t-1
        flag_low = low.shift(1).rolling(flag_len).min()  # bars p+1 .. t-1
        flag_high = high.shift(1).rolling(flag_len).max()
        flag_vol = volume.shift(1).rolling(flag_len).mean()
        pole_vol = pole_vol_6.shift(k)
        ts = epoch.shift(k)
        valid = (
            hp.notna()
            & pl.notna()
            & (pl > 0)
            & max_p_to_prev.notna()
            & flag_low.notna()
            & flag_high.notna()
            & flag_vol.notna()
            & pole_vol.notna()
            & ts.notna()
            & (hp >= max_p_to_prev)
            & (hp / pl - 1.0 >= MIN_POLE_RISE)
            & (flag_low >= hp - MAX_RETRACE_OF_POLE * height)
            & (flag_high - flag_low <= MAX_FLAG_RANGE_OF_POLE * height)
            & (flag_vol <= FLAG_VOLUME_RATIO_MAX * pole_vol)
        ).fillna(False).to_numpy(dtype=bool)
        take = valid & ~chosen
        sel_high[take] = hp.to_numpy(dtype=float)[take]
        sel_height[take] = height.to_numpy(dtype=float)[take]
        sel_flag_low[take] = flag_low.to_numpy(dtype=float)[take]
        sel_ts[take] = ts.to_numpy(dtype=float)[take]
        chosen |= take

    dataframe["pole_high"] = sel_high
    dataframe["pole_height"] = sel_height
    dataframe["flag_low"] = sel_flag_low
    dataframe["pole_ts"] = sel_ts
    dataframe["flag_target"] = dataframe["flag_low"] + TARGET_MULTIPLE_OF_POLE * dataframe["pole_height"]
    return dataframe


class HourlyBullFlagBreak_H075_v1(IStrategy):
    """Close above the pole high after a tight, shallow, low-volume flag, above SMA168; target FL + H."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    use_custom_roi = True
    use_exit_signal = True
    trailing_stop = False
    startup_candle_count = 200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return bull_flag_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        cond = (
            close.notna()
            & dataframe["sma168"].notna()
            & dataframe["pole_high"].notna()
            & dataframe["pole_height"].notna()
            & dataframe["flag_low"].notna()
            & dataframe["pole_ts"].notna()
            & (close > dataframe["pole_high"])
            & (close > dataframe["sma168"])
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                make_tag(ts, fl, target)
                for ts, fl, target in zip(
                    dataframe.loc[cond, "pole_ts"],
                    dataframe.loc[cond, "flag_low"],
                    dataframe.loc[cond, "flag_target"],
                )
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # All exits depend on the trade (FL, target, fill time); handled in custom_roi / custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Reject an entry whose pole (timestamp of bar p) was already traded on this pair."""
        parsed = parse_tag(entry_tag)
        if parsed is None:
            return False
        pole_ts = parsed[0]
        for trade in Trade.get_trades_proxy(pair=pair):
            previous = parse_tag(trade.enter_tag)
            if previous is not None and previous[0] == pole_ts:
                return False
        return True

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side, **kwargs):
        """ROI whose exit price is exactly TARGET = FL + H after the engine's fee adjustment."""
        parsed = parse_tag(trade.enter_tag)
        if parsed is None or not trade.open_rate:
            return None
        target = parsed[2]
        fee_open = trade.fee_open or 0.0
        fee_close = trade.fee_close or 0.0
        return (target * (1.0 - fee_close) - trade.open_rate * (1.0 + fee_open)) / trade.open_rate

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is not None:
            _, flag_low, target = parsed
            if current_rate is not None and current_rate >= target:
                return "target_flag_low_plus_pole"
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is not None and len(dataframe) > 0:
                closed = dataframe[dataframe["date"] + BAR <= current_time]
                if len(closed) > 0:
                    last = closed.iloc[-1]
                    if (
                        last["date"] >= trade.open_date_utc
                        and last["volume"] > 0
                        and last["close"] == last["close"]
                        and last["close"] < flag_low
                    ):
                        return "close_below_flag_low"
        if current_time >= trade.open_date_utc + BAR * TIME_EXIT_BARS:
            return "time_exit_24_bars"
        return None

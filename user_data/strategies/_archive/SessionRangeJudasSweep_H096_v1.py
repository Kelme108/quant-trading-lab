"""H-096: Judas sweep of a pre-open session range low, buy the quick reclaim, target the range high.

15m closed candles, UTC, spot long only. Two setups per UTC day:
  A (Asia->London): range 00:00-06:45, window 07:00-10:45, exit bar 14:45.
  L (London->US):   range 07:00-13:15, window 13:30-16:45, exit bar 20:45.
The signal is computed at the close of the reclaim bar and carries the setup,
the range high RH and the sweep low SL in the entry tag ("A|RH|SL").
Fill checks (confirm_trade_entry), the frozen stop (custom_stoploss), the
range-high take-profit and the time exit (custom_exit) are derived from the tag
and the trade's fill price, so no mutable state is kept.
"""

from datetime import timedelta

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy

BAR = timedelta(minutes=15)

# name: (range start, range end bar, window start, window end bar, exit fill time) in minutes of day
SETUPS = {
    "A": (0, 6 * 60 + 45, 7 * 60, 10 * 60 + 45, 15 * 60),
    "L": (7 * 60, 13 * 60 + 15, 13 * 60 + 30, 16 * 60 + 45, 21 * 60),
}

MIN_RANGE_WIDTH = 0.012
SWEEP_DEPTH = 0.999
DEAD_CLOSE = 0.995
MAX_BARS_AFTER_LOW = 4
MIN_CLOSE_LOCATION = 0.5
STOP_BUFFER = 0.998
MAX_STOP_DISTANCE = 0.03
MIN_TARGET_DISTANCE = 0.01
STOP_FROM_FILL = 0.99
WARMUP = 96


def parse_tag(tag):
    """Return (setup, RH, SL) from an entry tag, or None."""
    try:
        setup, rh, sl = str(tag).split("|")
        if setup not in SETUPS:
            return None
        return setup, float(rh), float(sl)
    except (ValueError, TypeError):
        return None


def stop_price(sl, fill):
    return min(STOP_BUFFER * sl, STOP_FROM_FILL * fill)


def find_signals(times, opens, highs, lows, closes, volumes):
    """Return {row_index: tag} for reclaim signals. Uses only bars up to each signal row."""
    n = len(times)
    out = {}
    index_of = {t: i for i, t in enumerate(times)}
    days = sorted({t.normalize() for t in times})
    for day in days:
        for name, (r0, r1, w0, w1, _exit) in SETUPS.items():
            range_idx = []
            t = day + timedelta(minutes=r0)
            end = day + timedelta(minutes=r1)
            missing = False
            while t <= end:
                i = index_of.get(t)
                if i is None:
                    missing = True
                    break
                range_idx.append(i)
                t += BAR
            if missing or not range_idx:
                continue
            if not all(np.isfinite(highs[i]) and np.isfinite(lows[i]) for i in range_idx):
                continue
            rh = max(highs[i] for i in range_idx)
            rl = min(lows[i] for i in range_idx)
            if not (np.isfinite(rh) and np.isfinite(rl)) or rl <= 0:
                continue
            if (rh - rl) / rl < MIN_RANGE_WIDTH:
                continue
            window_idx = []
            t = day + timedelta(minutes=w0)
            end = day + timedelta(minutes=w1)
            while t <= end:
                i = index_of.get(t)
                if i is not None:
                    window_idx.append((int((t - (day + timedelta(minutes=w0))) / BAR), i))
                t += BAR
            swept = False
            sl = np.inf
            k_slot = None
            for slot, i in window_idx:
                low, high, close = lows[i], highs[i], closes[i]
                if not (np.isfinite(low) and np.isfinite(high) and np.isfinite(close)):
                    break
                prev_sl = sl
                if low <= sl:
                    sl = low
                    k_slot = slot
                if not swept:
                    if low < SWEEP_DEPTH * rl:
                        swept = True
                    else:
                        continue
                else:
                    if close < DEAD_CLOSE * prev_sl:
                        break
                if (
                    slot - k_slot <= MAX_BARS_AFTER_LOW
                    and close > rl
                    and high > low
                    and (close - low) / (high - low) >= MIN_CLOSE_LOCATION
                ):
                    out[i] = "%s|%.10f|%.10f" % (name, rh, sl)
                    break
    return out


class SessionRangeJudasSweep_H096_v1(IStrategy):
    """Buy a fast reclaim of a swept session-range low, target the range high."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_custom_stoploss = True
    startup_candle_count = 96

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["judas_tag"] = None
        if len(dataframe) == 0:
            return dataframe
        times = list(dataframe["date"])
        signals = find_signals(
            times,
            dataframe["open"].to_numpy(dtype=float),
            dataframe["high"].to_numpy(dtype=float),
            dataframe["low"].to_numpy(dtype=float),
            dataframe["close"].to_numpy(dtype=float),
            dataframe["volume"].to_numpy(dtype=float),
        )
        col = dataframe.columns.get_loc("judas_tag")
        for i, tag in signals.items():
            dataframe.iloc[i, col] = tag
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        position = np.arange(len(dataframe))
        mask = (
            dataframe["judas_tag"].notna()
            & (dataframe["volume"] > 0)
            & (position >= self.startup_candle_count)
        )
        dataframe.loc[mask, "enter_long"] = 1
        dataframe.loc[mask, "enter_tag"] = dataframe.loc[mask, "judas_tag"]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # The take-profit and time exit depend on the trade; see custom_exit.
        return dataframe

    def confirm_trade_entry(
        self, pair, order_type, amount, rate, time_in_force, current_time, entry_tag, side, **kwargs
    ):
        parsed = parse_tag(entry_tag)
        if parsed is None:
            return False
        _setup, rh, sl = parsed
        if STOP_BUFFER * sl < (1 - MAX_STOP_DISTANCE) * rate:
            return False
        if rh < (1 + MIN_TARGET_DISTANCE) * rate:
            return False
        return True

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is None:
            return None
        _setup, _rh, sl = parsed
        sp = stop_price(sl, trade.open_rate)
        if current_rate <= 0:
            return None
        # Fixed absolute stop at SP, expressed relative to the current rate.
        return max(1.0 - sp / current_rate, 0.0001)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is None:
            return None
        setup, rh, _sl = parsed
        if current_rate >= rh:
            return "take_profit_rh"
        open_time = trade.open_date_utc
        exit_minutes = SETUPS[setup][4]
        deadline = open_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            minutes=exit_minutes
        )
        if current_time >= deadline:
            return "time_exit"
        return None

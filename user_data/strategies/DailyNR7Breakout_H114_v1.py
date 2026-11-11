"""H-114: session-aware hourly NR4 breakout on 15m (research/proposals/H-114.json).

Chart 15m, UTC, closed bars only, spot, long only.
- Hourly bar H = four completed 15m bars h:00..h:45 (complete at the h:45 close).
- NR4 setup: range(H) is strictly smaller than the range of the same clock hour on each of
  days d-1, d-2, d-3 (all three must exist and be complete) and range(H)/close(H) >= 0.0025.
- Filter: close of the last completed 4h block (16 bars, blocks start 00/04/08/12/16/20 UTC)
  is above the SMA(50) of the last 50 completed 4h closes, including that block.
- Entry window: the 8 bars after H (age 15..120 minutes after the h:45 bar). The most recently
  completed NR4 bar is the one used. Entry at the first window bar with close > high(H), filter
  true, low(H) >= 0.98 x close; filled at the next open. One entry per NR4 bar and at most two
  entries per pair per UTC date of the signal bar (both enforced in confirm_trade_entry).
- Stop: stop_pct = min(0.02, max(0.01, (entry - low(H)) / entry)); constant price
  entry x (1 - stop_pct) through custom_stoploss; native hard stop -0.02. low(H) travels in the
  enter_tag as "nr4|<low>|<NR4 bar time>|<signal date>".
- Target: close of a closed 15m candle >= entry x (1 + 2 x stop_pct), exit at the next open
  (custom_exit). Time exit: 8 hours after the entry bar opens (32 bars) in custom_exit.
- No other exits. Warm-up 900 bars.
"""

from datetime import timedelta
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BARS_PER_HOUR = 4
PRIOR_DAYS = 3
MIN_RANGE_TO_CLOSE = 0.0025
BARS_PER_BLOCK = 16  # 4h of 15m bars
HTF_SMA_LENGTH = 50
WINDOW_MIN_AGE_MINUTES = 15
WINDOW_MAX_AGE_MINUTES = 120  # 8 bars after the NR4 bar
LOW_TO_CLOSE_MIN = 0.98
MAX_ENTRIES_PER_DAY = 2
STOP_FLOOR_PCT = 0.01
STOP_CAP_PCT = 0.02
TARGET_R = 2.0
TIME_EXIT_HOURS = 8  # 32 bars of 15m
BAR_MINUTES = 15


def parse_tag(tag) -> Optional[tuple]:
    """Return (low_H, nr4_bar_time, signal_date) from an entry tag, or None."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 4 or parts[0] != "nr4":
        return None
    try:
        low = float(parts[1])
    except ValueError:
        return None
    if not np.isfinite(low):
        return None
    return low, parts[2], parts[3]


def stop_pct_for(entry: float, low_h: float) -> float:
    return min(STOP_CAP_PCT, max(STOP_FLOOR_PCT, (entry - low_h) / entry))


class DailyNR7Breakout_H114_v1(IStrategy):
    """Hourly same-clock-hour NR4 breakout, 4h SMA50 filter, 1% floor stop, 2R target, 8h exit."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    use_custom_stoploss = True
    use_exit_signal = False
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    process_only_new_candles = True
    startup_candle_count = 900
    dp = None  # replaced by the engine's data provider

    def bot_start(self, **kwargs) -> None:
        self._nr4_used = set()
        self._day_counts = {}

    def _state(self):
        try:
            return self._nr4_used, self._day_counts
        except AttributeError:
            self._nr4_used = set()
            self._day_counts = {}
            return self._nr4_used, self._day_counts

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dates = pd.to_datetime(dataframe["date"], utc=True)
        close = dataframe["close"].astype(float)

        # ---- hourly bars from four 15m bars (causal: running max/min inside the hour) ----
        hour_key = dates.dt.floor("h")
        running_high = dataframe["high"].astype(float).groupby(hour_key).cummax()
        running_low = dataframe["low"].astype(float).groupby(hour_key).cummin()
        in_hour = close.groupby(hour_key).cumcount() + 1
        hour_done = (dates.dt.minute == 45) & (in_hour == BARS_PER_HOUR)
        hour_range = (running_high - running_low).where(hour_done)

        hour_starts = pd.DatetimeIndex(hour_key[hour_done])
        by_hour = pd.Series(hour_range[hour_done].to_numpy(), index=hour_starts)
        by_hour = by_hour[~by_hour.index.duplicated()]
        narrower = hour_done.copy()
        for days_back in range(1, PRIOR_DAYS + 1):
            prior = pd.Series(np.nan, index=dataframe.index, dtype=float)
            prior.loc[hour_done] = by_hour.reindex(
                hour_starts - pd.Timedelta(days=days_back)
            ).to_numpy()
            dataframe[f"prior_range_{days_back}"] = prior
            narrower = narrower & (hour_range < prior)
        wide_enough = (hour_range / close) >= MIN_RANGE_TO_CLOSE
        nr4 = narrower & wide_enough & hour_range.notna()

        dataframe["nr_high"] = running_high.where(nr4).ffill()
        dataframe["nr_low"] = running_low.where(nr4).ffill()
        nr_date = dates.where(nr4).ffill()
        dataframe["nr_date"] = nr_date
        dataframe["nr_age_min"] = (dates - nr_date).dt.total_seconds() / 60.0

        # ---- 4h blocks of 16 completed 15m bars, SMA(50) of completed 4h closes ----
        block_key = dates.dt.floor("4h")
        in_block = close.groupby(block_key).cumcount() + 1
        block_done = (
            (dates.dt.hour % 4 == 3) & (dates.dt.minute == 45) & (in_block == BARS_PER_BLOCK)
        )
        block_close = close[block_done]
        block_sma = block_close.rolling(HTF_SMA_LENGTH).mean()
        dataframe["h4_close"] = block_close.reindex(dataframe.index).ffill()
        dataframe["h4_sma"] = block_sma.reindex(dataframe.index).ffill()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        needed = ["close", "nr_high", "nr_low", "nr_age_min", "h4_close", "h4_sma"]
        defined = dataframe[needed].notna().all(axis=1) & (dataframe["volume"] > 0)
        age = dataframe["nr_age_min"]
        in_window = (age >= WINDOW_MIN_AGE_MINUTES) & (age <= WINDOW_MAX_AGE_MINUTES)
        breakout = dataframe["close"] > dataframe["nr_high"]
        trend_up = dataframe["h4_close"] > dataframe["h4_sma"]
        low_ok = dataframe["nr_low"] >= LOW_TO_CLOSE_MIN * dataframe["close"]
        signal = defined & in_window & breakout & trend_up & low_ok
        if bool(signal.any()):
            dates = pd.to_datetime(dataframe["date"], utc=True)
            tags = [
                f"nr4|{float(low)!r}|{pd.Timestamp(nr_time).isoformat()}|{signal_time:%Y-%m-%d}"
                for low, nr_time, signal_time in zip(
                    dataframe.loc[signal, "nr_low"],
                    dataframe.loc[signal, "nr_date"],
                    dates[signal],
                )
            ]
            dataframe.loc[signal, "enter_long"] = 1
            dataframe.loc[signal, "enter_tag"] = tags
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time,
        entry_tag,
        side: str,
        **kwargs,
    ) -> bool:
        parsed = parse_tag(entry_tag)
        if parsed is None:
            return True
        _, nr_time, signal_day = parsed
        used, counts = self._state()
        if (pair, nr_time) in used:
            return False
        if counts.get((pair, signal_day), 0) >= MAX_ENTRIES_PER_DAY:
            return False
        used.add((pair, nr_time))
        counts[(pair, signal_day)] = counts.get((pair, signal_day), 0) + 1
        return True

    def custom_stoploss(
        self,
        pair: str,
        trade,
        current_time,
        current_rate: float,
        current_profit: float,
        after_fill: bool = False,
        **kwargs,
    ) -> Optional[float]:
        parsed = parse_tag(trade.enter_tag)
        if parsed is None or not current_rate or current_rate <= 0:
            return None
        pct = stop_pct_for(trade.open_rate, parsed[0])
        stop_price = trade.open_rate * (1.0 - pct)
        relative = stop_price / current_rate - 1.0
        if relative >= 0:
            return None
        return relative

    def _closed_candle_at_target(self, pair: str, trade, target: float) -> Optional[bool]:
        """True/False from the last closed candle at or after the entry bar; None if unavailable."""
        provider = self.dp
        if provider is None:
            return None
        frame, _ = provider.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or len(frame) == 0:
            return None
        last = frame.iloc[-1]
        entry_bar = pd.Timestamp(trade.open_date_utc).floor(f"{BAR_MINUTES}min")
        if pd.Timestamp(last["date"]) < entry_bar:
            return False
        return bool(float(last["close"]) >= target)

    def custom_exit(
        self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs
    ):
        parsed = parse_tag(trade.enter_tag)
        if parsed is not None:
            pct = stop_pct_for(trade.open_rate, parsed[0])
            target = trade.open_rate * (1.0 + TARGET_R * pct)
            hit = self._closed_candle_at_target(pair, trade, target)
            if hit is None:
                hit = current_profit >= TARGET_R * pct
            if hit:
                return "take_profit_2R"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_8h"
        return None

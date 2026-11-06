"""H-055: 15m stop-sweep of the 24-hour low reclaimed within an hour.

Closed 15m candles only; signals at the close of bar t, fills at the open of bar t+1. Spot long only.

Definitions:
  PL(t)     = lowest low of bars t-100..t-5 inclusive (96 bars; excludes bars t-4..t).
  SL4(t)    = min(low of bars t-3..t).
  SMA384(t) = mean of the 384 closes ending at t (inclusive).
Entry at the close of bar t when all hold:
  (1) SWEEP:     SL4(t) < 0.998 * PL(t)
  (2) DEPTH CAP: SL4(t) >= 0.98 * PL(t)
  (3) RECLAIM:   close(t) > PL(t) and close(t-1) <= PL(t)
  (4) TREND:     close(t) > SMA384(t)
  (5) no position open (one position per pair, handled by the engine)
  (6) SPACING:   no entry filled at bars t-15..t (confirm_trade_entry)
  (7) all inputs defined, volume > 0.
SWEEP_LOW = SL4(t) is stored in the entry tag, fixed for the trade.
Exits, first of:
  (a) take-profit at entry_fill * 1.012 (gross price), intrabar via custom_roi; custom_exit
      also exits at the open when the bar opens at or above that level.
  (b) a closed bar u after the entry fill with close < SWEEP_LOW * 0.998 -> exit at open of u+1.
  (c) native intrabar stop 2% below the entry fill (stoploss = -0.02).
  (d) time exit at the open of bar e+48 (entry filled at the open of bar e).
No trailing stop, no other filters. Warm-up 400 bars.
"""

from __future__ import annotations

from datetime import timedelta

from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

BAR = timedelta(minutes=15)
PL_WINDOW_BARS = 96
PL_END_OFFSET = 5
SWEEP_WINDOW_BARS = 4
SWEEP_MIN_BREAK = 0.998
DEPTH_CAP = 0.98
TREND_SMA_BARS = 384
ENTRY_SPACING_BARS = 16
TAKE_PROFIT = 0.012
SWEEP_LOW_EXIT_FACTOR = 0.998
TIME_EXIT_BARS = 48
TAG_PREFIX = "fbr15"


def make_tag(sweep_low: float) -> str:
    return f"{TAG_PREFIX}|{sweep_low!r}"


def parse_tag(tag) -> float | None:
    """SWEEP_LOW recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 2 or parts[0] != TAG_PREFIX:
        return None
    try:
        return float(parts[1])
    except ValueError:
        return None


class HourlyFailedBreakdownReclaim_H055_v1(IStrategy):
    """Buy a quick sweep of the 24h low that closes back above it, above the 4-day mean."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    trailing_stop = False
    use_custom_roi = True
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        low = dataframe["low"].astype(float)
        close = dataframe["close"].astype(float)
        # Lowest low of bars t-100..t-5: a 96-bar window ending at t-5.
        dataframe["pl"] = low.rolling(PL_WINDOW_BARS).min().shift(PL_END_OFFSET)
        dataframe["sl4"] = low.rolling(SWEEP_WINDOW_BARS).min()
        dataframe["sma_trend"] = close.rolling(TREND_SMA_BARS).mean()
        dataframe["prev_close"] = close.shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        pl = dataframe["pl"]
        sl4 = dataframe["sl4"]
        cond = (
            pl.notna()
            & sl4.notna()
            & dataframe["sma_trend"].notna()
            & dataframe["prev_close"].notna()
            & close.notna()
            & (sl4 < SWEEP_MIN_BREAK * pl)
            & (sl4 >= DEPTH_CAP * pl)
            & (close > pl)
            & (dataframe["prev_close"] <= pl)
            & (close > dataframe["sma_trend"])
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [make_tag(float(v)) for v in sl4[cond]]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # All exits depend on per-trade state (entry fill, SWEEP_LOW); handled per trade.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Condition (6): no entry filled at bars t-15..t, where t is the signal bar."""
        if parse_tag(entry_tag) is None:
            return False
        signal_bar = current_time - BAR
        earliest_blocked = signal_bar - BAR * (ENTRY_SPACING_BARS - 1)
        for trade in Trade.get_trades_proxy(pair=pair):
            if trade.open_date_utc >= earliest_blocked:
                return False
        return True

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side, **kwargs):
        """ROI whose exit price is exactly entry_fill * 1.012 after the engine's fee adjustment."""
        if not trade.open_rate:
            return None
        target = trade.open_rate * (1.0 + TAKE_PROFIT)
        fee_open = trade.fee_open or 0.0
        fee_close = trade.fee_close or 0.0
        return (target * (1.0 - fee_close) - trade.open_rate * (1.0 + fee_open)) / trade.open_rate

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if trade.open_rate and current_rate >= trade.open_rate * (1.0 + TAKE_PROFIT):
            return "take_profit_1_2pct"
        sweep_low = parse_tag(trade.enter_tag)
        if sweep_low is not None:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is not None and len(dataframe) > 0:
                closed = dataframe[dataframe["date"] + BAR <= current_time]
                if len(closed) > 0:
                    last = closed.iloc[-1]
                    if (
                        last["date"] >= trade.open_date_utc
                        and last["volume"] > 0
                        and last["close"] == last["close"]
                        and last["close"] < sweep_low * SWEEP_LOW_EXIT_FACTOR
                    ):
                        return "sweep_low_exit"
        if current_time >= trade.open_date_utc + BAR * TIME_EXIT_BARS:
            return "time_exit_48_bars"
        return None

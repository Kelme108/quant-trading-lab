"""H-131: hourly trend entered on 15m three-bar counter-move streaks, 1h ATR expansion gate (15m).

Rule (research/proposals/H-131.json), 15m, closed bars only, long only, spot:
- 1h bars are built from closed 15m candles (a 1h bar needs all four 15m candles). A 15m bar at time t
  uses only the last COMPLETED 1h bar (the hour before floor(t, 1h)), the same visibility as
  merge_informative_pair(..., "1h").
- MID48(h) = (max 1h high over h-47..h + min 1h low over h-47..h) / 2.
  BASE_TREND(h) = close_1h(h) > MID48(h) AND close_1h(h) > close_1h(h-24).
- ATR14_1h = Wilder ATR(14) on the 1h bars (seeded with the mean of the first 14 true ranges).
  ACTIVITY(h) = ATR14_1h(h) >= 1.5 x median of ATR14_1h over the 480 hours h-480..h-1.
- ENTRY at the close of 15m bar t: BASE_TREND and ACTIVITY (last completed hour), three consecutive
  lower 15m closes (close(t) < close(t-1) < close(t-2) < close(t-3)) and close(t) <= 0.994 x close(t-3).
  The order fills at the next 15m open. One position per pair is a Freqtrade default; the 4-candle
  cooldown after an exit is the CooldownPeriod protection.
- EXITS, first wins: (1) native stop -1.2%; (2) take-profit +1.5% in custom_exit;
  (3) trend exit: exit signal on any 15m bar where BASE_TREND of the last completed hour is false;
  (4) time exit 720 minutes after the fill in custom_exit.
- ACTIVITY is an entry condition only. Warm-up 2400 bars (15m).
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

TREND_RANGE_HOURS = 48
TREND_LAG_HOURS = 24
ATR_PERIOD = 14
ATR_MEDIAN_HOURS = 480
ATR_EXPANSION_MULT = 1.5
STREAK_BARS = 3
COUNTER_MOVE_MULT = 0.994  # close(t) <= 0.994 x close(t-3): at least 0.6% down
STOPLOSS = -0.012
TAKE_PROFIT_PCT = 0.015
TIME_EXIT_MINUTES = 720
COOLDOWN_BARS = 4
BARS_PER_HOUR = 4


def _wilder_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    """Causal Wilder ATR; resets (NaN) whenever a true range is undefined."""
    n = len(close)
    out = np.full(n, np.nan)
    prev_close = np.concatenate([[np.nan], close[:-1]]) if n else close
    tr = np.maximum.reduce(
        [high - low, np.abs(high - prev_close), np.abs(low - prev_close)]
    ) if n else high
    valid = 0
    total = 0.0
    atr = np.nan
    for i in range(n):
        value = tr[i]
        if not np.isfinite(value) or not np.isfinite(high[i] - low[i]):
            valid = 0
            total = 0.0
            atr = np.nan
            continue
        valid += 1
        if valid < period:
            total += value
        elif valid == period:
            total += value
            atr = total / period
            out[i] = atr
        else:
            atr = (atr * (period - 1) + value) / period
            out[i] = atr
    return out


class TrendCounterMoveOverlay_H131_v1(IStrategy):
    """Hourly uptrend + ATR expansion, entered on a 0.6% three-bar 15m counter-move."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = STOPLOSS
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 2400

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        date = pd.to_datetime(dataframe["date"])
        hour = date.dt.floor("1h")

        trend_value = np.full(n, np.nan)
        activity_value = np.full(n, np.nan)
        if n:
            grouped = pd.DataFrame(
                {
                    "high": dataframe["high"].to_numpy(dtype=float),
                    "low": dataframe["low"].to_numpy(dtype=float),
                    "close": dataframe["close"].to_numpy(dtype=float),
                    "hour": hour.to_numpy(),
                }
            ).groupby("hour")
            hourly = pd.DataFrame(
                {
                    "high": grouped["high"].max(),
                    "low": grouped["low"].min(),
                    "close": grouped["close"].last(),
                    "n": grouped["close"].count(),
                }
            )
            hourly = hourly.reindex(pd.date_range(hourly.index.min(), hourly.index.max(), freq="1h"))
            complete = hourly["n"] == BARS_PER_HOUR
            for column in ("high", "low", "close"):
                hourly[column] = hourly[column].where(complete)

            mid = (
                hourly["high"].rolling(TREND_RANGE_HOURS).max()
                + hourly["low"].rolling(TREND_RANGE_HOURS).min()
            ) / 2.0
            lagged = hourly["close"].shift(TREND_LAG_HOURS)
            defined_trend = mid.notna() & lagged.notna() & hourly["close"].notna()
            base_trend = (
                ((hourly["close"] > mid) & (hourly["close"] > lagged)).astype(float).where(defined_trend)
            )

            atr = pd.Series(
                _wilder_atr(
                    hourly["high"].to_numpy(dtype=float),
                    hourly["low"].to_numpy(dtype=float),
                    hourly["close"].to_numpy(dtype=float),
                    ATR_PERIOD,
                ),
                index=hourly.index,
            )
            median = atr.shift(1).rolling(ATR_MEDIAN_HOURS).median()
            defined_activity = atr.notna() & median.notna()
            activity = (atr >= ATR_EXPANSION_MULT * median).astype(float).where(defined_activity)

            # The 15m bar in hour H sees hour H-1, the last completed 1h bar.
            last_completed = hour - pd.Timedelta(hours=1)
            trend_value = base_trend.reindex(last_completed).to_numpy(dtype=float)
            activity_value = activity.reindex(last_completed).to_numpy(dtype=float)

        dataframe["h_trend"] = trend_value
        dataframe["h_activity"] = activity_value
        close = dataframe["close"]
        dataframe["streak_down"] = (
            (close < close.shift(1)) & (close.shift(1) < close.shift(2)) & (close.shift(2) < close.shift(3))
        )
        dataframe["counter_move"] = close <= COUNTER_MOVE_MULT * close.shift(STREAK_BARS)
        dataframe["close_lag3"] = close.shift(STREAK_BARS)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["h_trend"].notna()
            & dataframe["h_activity"].notna()
            & dataframe["close_lag3"].notna()
            & (dataframe["volume"] > 0)
        )
        signal = (
            defined
            & (dataframe["h_trend"] == 1.0)
            & (dataframe["h_activity"] == 1.0)
            & dataframe["streak_down"].fillna(False).astype(bool)
            & dataframe["counter_move"].fillna(False).astype(bool)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "trend_counter_move")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        signal = dataframe["h_trend"].notna() & (dataframe["h_trend"] == 0.0) & (dataframe["volume"] > 0)
        dataframe.loc[signal, ["exit_long", "exit_tag"]] = (1, "trend_lost")
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        if current_profit >= TAKE_PROFIT_PCT:
            return "take_profit_1_5pct"
        if current_time - trade.open_date_utc >= timedelta(minutes=TIME_EXIT_MINUTES):
            return "time_exit_12h"
        return None

"""H-094: Raschke Holy Grail on 15m (ADX > 30 and rising, first pullback to EMA20).

Exploratory candidate, not a performance claim. Closed candles only; a signal
at the close of bar t is filled at the open of bar t+1.

- Touch bar s: ADX(s-1) > 30, ADX(s-1) > ADX(s-5), +DI(s-1) > -DI(s-1),
  EMA20(s) > EMA20(s-4), close(s-1) > EMA20(s-1), low(s) <= EMA20(s).
- Trigger at t (s in t-3..t-1, earliest unconsumed): close(t) > high(t-1) and
  close(t) > EMA20(t). LL = lowest low of s..t. Skip if LL < 0.975 * close(t).
- At most 3 entry signals per UTC day; a used setup is consumed.
- Stop: min(LL, 0.99 * fill) fixed at the fill (custom_stoploss), native -3% backstop.
- Take-profit at 1.5R and time exit after 32 bars in custom_exit.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class HolyGrailADXPullback_H094_v1(IStrategy):
    """Holy Grail ADX pullback, single fixed cell."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_custom_stoploss = True
    startup_candle_count = 500

    ADX_PERIOD = 14
    ADX_MIN = 30
    EMA_PERIOD = 20
    WINDOW = 3
    MAX_STOP_FROM_CLOSE = 0.975
    MIN_STOP_FACTOR = 0.99
    TAKE_PROFIT_R = 1.5
    TIME_EXIT_BARS = 32
    MAX_ENTRIES_PER_DAY = 3
    BARS_PER_DAY = 96

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Wilder ADX/DI, EMA20 and the touch-bar flag (backward looking only)."""
        alpha = 1.0 / self.ADX_PERIOD
        high, low, close = dataframe["high"], dataframe["low"], dataframe["close"]
        prev_close = close.shift(1)
        up = high - high.shift(1)
        down = low.shift(1) - low
        plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=dataframe.index)
        minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=dataframe.index)
        valid = prev_close.notna()
        plus_dm = plus_dm.where(valid)
        minus_dm = minus_dm.where(valid)
        true_range = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
        ).max(axis=1, skipna=False)

        tr_s = true_range.ewm(alpha=alpha, adjust=False).mean()
        plus_s = plus_dm.ewm(alpha=alpha, adjust=False).mean()
        minus_s = minus_dm.ewm(alpha=alpha, adjust=False).mean()
        plus_di = (100.0 * plus_s / tr_s).replace([np.inf, -np.inf], np.nan)
        minus_di = (100.0 * minus_s / tr_s).replace([np.inf, -np.inf], np.nan)
        dx = (100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di)).replace(
            [np.inf, -np.inf], np.nan
        )
        dataframe["adx"] = dx.ewm(alpha=alpha, adjust=False).mean()
        dataframe["plus_di"] = plus_di
        dataframe["minus_di"] = minus_di
        dataframe["ema20"] = close.ewm(span=20, adjust=False).mean()

        dataframe["hg_touch"] = (
            (dataframe["adx"].shift(1) > self.ADX_MIN)
            & (dataframe["adx"].shift(1) > dataframe["adx"].shift(5))
            & (dataframe["plus_di"].shift(1) > dataframe["minus_di"].shift(1))
            & (dataframe["ema20"] > dataframe["ema20"].shift(4))
            & (close.shift(1) > dataframe["ema20"].shift(1))
            & (low <= dataframe["ema20"])
        ).astype(int)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Sequential setup tracking: consumption, skip rule and daily cap."""
        n = len(dataframe)
        touch = dataframe["hg_touch"].to_numpy() == 1
        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        close = dataframe["close"].to_numpy(dtype=float)
        ema = dataframe["ema20"].to_numpy(dtype=float)
        volume = dataframe["volume"].to_numpy(dtype=float)
        if "date" in dataframe.columns:
            days = pd.to_datetime(dataframe["date"]).dt.strftime("%Y-%m-%d").to_numpy()
        else:
            days = (np.arange(n) // self.BARS_PER_DAY).astype(str)

        enter = np.zeros(n, dtype=bool)
        setup_ll = np.full(n, np.nan)
        consumed_upto = -1
        counts = {}
        for t in range(1, n):
            first = max(t - self.WINDOW, consumed_upto + 1, 0)
            s = -1
            for k in range(first, t):
                if touch[k]:
                    s = k
                    break
            if s < 0:
                continue
            if not (
                np.isfinite(close[t]) and np.isfinite(high[t - 1]) and np.isfinite(ema[t])
            ):
                continue
            if not (close[t] > high[t - 1] and close[t] > ema[t]):
                continue
            ll = np.min(low[s : t + 1])
            if not np.isfinite(ll):
                continue
            if ll < self.MAX_STOP_FROM_CLOSE * close[t]:
                consumed_upto = t
                continue
            if volume[t] > 0 and counts.get(days[t], 0) < self.MAX_ENTRIES_PER_DAY:
                enter[t] = True
                setup_ll[t] = ll
                counts[days[t]] = counts.get(days[t], 0) + 1
                consumed_upto = t

        dataframe["setup_ll"] = setup_ll
        dataframe.loc[enter, ["enter_long", "enter_tag"]] = (1, "holy_grail_adx")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """No indicator exit; exits are in custom_exit and the stop."""
        return dataframe

    # ---- trade management -------------------------------------------------

    def _stop_distance(self, pair, trade):
        """Return (stop price, stop fraction d) frozen from the signal candle."""
        try:
            frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            signal_date = trade.open_date_utc - timedelta(minutes=15)
            rows = frame.loc[frame["date"] == signal_date, "setup_ll"]
            ll = float(rows.iloc[-1])
        except Exception:
            return None
        if not np.isfinite(ll):
            return None
        fill = float(trade.open_rate)
        stop_price = min(ll, self.MIN_STOP_FACTOR * fill)
        return stop_price, (fill - stop_price) / fill

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """Fixed stop price below the entry, frozen at the fill."""
        info = self._stop_distance(pair, trade)
        if info is None or current_rate <= 0:
            return self.stoploss
        stop_price, _ = info
        return stop_price / current_rate - 1.0

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """1.5R take-profit and 32-bar time exit."""
        info = self._stop_distance(pair, trade)
        if info is not None:
            _, d = info
            if current_profit >= self.TAKE_PROFIT_R * d:
                return "take_profit_1_5R"
        held = current_time - trade.open_date_utc
        if held >= timedelta(minutes=15 * self.TIME_EXIT_BARS):
            return "time_exit_8h"
        return None

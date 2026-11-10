"""H-093: DeMark TD buy setup 9 with perfection on 15m (long only).

Rule (closed bars only, signal at bar close, fill at the next open):
1) Bearish price flip at bar f: close[f] < close[f-4] and close[f-1] > close[f-5].
2) Buy setup: bars f+1..f+8 each close below the close 4 bars earlier (count 9 at f+8).
3) Decline filter at n9: close[f-1] / close[n9] - 1 >= 0.015.
4) Perfection: P = min(low[n6], low[n7]); perfected at n9 if min(low[n8], low[n9]) <= P
   (p = n9), else first bar of n9+1..n9+4 with low <= P.
5) Trigger: first bar t in p..p+3 with close[t] > high[t-1].
6) At the fill: LL = lowest low f..t, STOP = min(LL*0.998, entry*0.99), skip if
   STOP < entry*0.97; TP = highest high f..n9, skip if TP < entry*1.01.
7) Exits: fixed STOP level (custom_stoploss), TP and 8-hour time exit (custom_exit).
"""

from __future__ import annotations

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class TDSetupExhaustion_H093_v1(IStrategy):
    """TD buy setup 9 exhaustion with perfection and reversal-bar trigger."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_custom_stoploss = True
    startup_candle_count = 100

    FLIP_LAG = 4
    SETUP_COUNT = 9
    DECLINE_MIN = 0.015
    PERFECTION_LATE_BARS = 4
    ENTRY_WINDOW_BARS = 4
    STOP_BUFFER = 0.998
    STOP_MIN_FRAC = 0.99
    STOP_MAX_FRAC = 0.97
    TP_MIN_FRAC = 1.01
    TIME_EXIT_BARS = 32
    WARMUP_BARS = 100

    dp = None
    _levels = {}

    # ------------------------------------------------------------------ signals
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        close = dataframe["close"].to_numpy(dtype=float)
        n = len(close)
        signal = np.zeros(n, dtype=int)
        ll_out = np.full(n, np.nan)
        tp_out = np.full(n, np.nan)

        counting = False
        f = -1
        count = 0
        pending = None  # dict: f, n9, P, p

        for i in range(5, n):
            if not (
                np.isfinite(close[i]) and np.isfinite(high[i]) and np.isfinite(low[i])
                and np.isfinite(close[i - 1]) and np.isfinite(close[i - 4])
                and np.isfinite(close[i - 5]) and np.isfinite(high[i - 1])
            ):
                counting = False
                pending = None
                continue

            # Pending perfection / trigger tracking (started at an earlier n9).
            if pending is not None and i > pending["n9"]:
                if pending["p"] is None:
                    if i <= pending["n9"] + self.PERFECTION_LATE_BARS:
                        if low[i] <= pending["P"]:
                            pending["p"] = i
                    else:
                        pending = None
                if pending is not None and pending["p"] is not None:
                    if close[i] > high[i - 1]:
                        signal[i] = 1
                        ll_out[i] = np.min(low[pending["f"]:i + 1])
                        tp_out[i] = np.max(high[pending["f"]:pending["n9"] + 1])
                        pending = None
                    elif i >= pending["p"] + self.ENTRY_WINDOW_BARS - 1:
                        pending = None

            # Setup counting.
            if counting:
                if close[i] < close[i - self.FLIP_LAG]:
                    count += 1
                    if count == self.SETUP_COUNT:
                        counting = False
                        n9 = i
                        if close[f - 1] / close[n9] - 1.0 >= self.DECLINE_MIN:
                            peak = min(low[f + 5], low[f + 6])
                            new = {"f": f, "n9": n9, "P": peak, "p": None}
                            if min(low[n9 - 1], low[n9]) <= peak:
                                new["p"] = n9
                                if close[i] > high[i - 1]:
                                    signal[i] = 1
                                    ll_out[i] = np.min(low[f:i + 1])
                                    tp_out[i] = np.max(high[f:n9 + 1])
                                    new = None
                            pending = new
                else:
                    counting = False
            elif (
                close[i] < close[i - self.FLIP_LAG]
                and close[i - 1] > close[i - 5]
            ):
                counting = True
                f = i
                count = 1

        signal[: self.WARMUP_BARS] = 0
        dataframe["td_signal"] = signal
        dataframe["td_ll"] = ll_out
        dataframe["td_tp"] = tp_out
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        valid = (
            (dataframe["td_signal"] == 1)
            & (dataframe["volume"] > 0)
            & dataframe["td_ll"].notna()
            & dataframe["td_tp"].notna()
        )
        dataframe.loc[valid, ["enter_long", "enter_tag"]] = (1, "td_setup9_perfected")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits are handled by custom_stoploss and custom_exit.
        return dataframe

    # ------------------------------------------------------------------ trade checks
    def _signal_levels(self, pair, current_time):
        dp = self.dp
        if dp is None:
            return None
        frame, _ = dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or len(frame) == 0:
            return None
        row = frame.iloc[-1]
        ll, tp = row.get("td_ll"), row.get("td_tp")
        if ll is None or tp is None or not (np.isfinite(ll) and np.isfinite(tp)):
            return None
        return float(ll), float(tp)

    def confirm_trade_entry(
        self, pair, order_type, amount, rate, time_in_force, current_time,
        entry_tag, side, **kwargs
    ) -> bool:
        levels = self._signal_levels(pair, current_time)
        if levels is None:
            return False
        ll, tp = levels
        stop = min(ll * self.STOP_BUFFER, rate * self.STOP_MIN_FRAC)
        if stop < rate * self.STOP_MAX_FRAC:
            return False
        if tp < rate * self.TP_MIN_FRAC:
            return False
        self._levels[pair] = (stop, tp)
        return True

    def custom_stoploss(
        self, pair, trade, current_time, current_rate, current_profit, **kwargs
    ):
        level = self._levels.get(pair)
        if level is None or not current_rate:
            return None
        distance = 1.0 - level[0] / current_rate  # as stoploss_from_absolute
        return -max(distance, 0.0001)

    def custom_exit(
        self, pair, trade, current_time, current_rate, current_profit, **kwargs
    ):
        level = self._levels.get(pair)
        if level is not None and current_rate >= level[1]:
            return "td_take_profit"
        held = current_time - trade.open_date_utc
        minutes = held.total_seconds() / 60.0
        if minutes >= self.TIME_EXIT_BARS * 15:
            return "td_time_exit"
        return None

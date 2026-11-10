"""H-098: CRT on 4h UTC blocks, low-only sweep that closes back inside below mid.

15m chart, closed candles only. At the close of the 16th bar of 4h block C2,
compare with the previous block C1: C2 sweeps below L1, does not exceed H1,
closes above L1 and below the C1 midpoint, and the swept low is within 3% of
the close. Buy next bar open. Stop at SP = min(low(C2), 0.992*close(C2)),
frozen as a price; take-profit at H1 and a 12 hour time exit in custom_exit.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy

BARS_PER_BLOCK = 16
BAR_MINUTES = 15
TIME_EXIT_BARS = 48


class HourlyFailedBreakdownReclaim_H098_v1(IStrategy):
    """Candle Range Theory low sweep on 4h UTC blocks."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    use_custom_stoploss = True
    startup_candle_count = 64

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        block = date.dt.floor("4h")
        grouped_high = dataframe["high"].groupby(block).cummax()
        grouped_low = dataframe["low"].groupby(block).cummin()
        count = dataframe["high"].groupby(block).cumcount() + 1
        is_last_slot = (date.dt.hour % 4 == 3) & (date.dt.minute == 45)
        complete = (count == BARS_PER_BLOCK) & is_last_slot

        block_high = grouped_high.where(complete)
        block_low = grouped_low.where(complete)
        block_close = dataframe["close"].where(complete)

        # C1 = block ending exactly 16 bars earlier, must be complete and contiguous.
        gap = date - date.shift(BARS_PER_BLOCK)
        c1_ok = complete.shift(BARS_PER_BLOCK, fill_value=False).astype(bool) & (
            gap == pd.Timedelta(hours=4)
        )
        h1 = block_high.shift(BARS_PER_BLOCK).where(c1_ok)
        l1 = block_low.shift(BARS_PER_BLOCK).where(c1_ok)
        r1 = h1 - l1
        dataframe["crt_h1"] = h1
        dataframe["crt_l1"] = l1
        dataframe["crt_mid1"] = l1 + r1 / 2.0
        dataframe["crt_range_frac"] = r1 / l1
        dataframe["crt_low2"] = block_low
        dataframe["crt_high2"] = block_high
        dataframe["crt_close2"] = block_close
        dataframe["crt_sp"] = np.minimum(block_low, 0.992 * block_close)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        setup = (
            (dataframe["crt_range_frac"] >= 0.015)
            & (dataframe["crt_low2"] < dataframe["crt_l1"])
            & (dataframe["crt_high2"] <= dataframe["crt_h1"])
            & (dataframe["crt_close2"] > dataframe["crt_l1"])
            & (dataframe["crt_close2"] < dataframe["crt_mid1"])
            & (dataframe["crt_low2"] >= 0.97 * dataframe["crt_close2"])
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[setup.fillna(False), ["enter_long", "enter_tag"]] = (
            1,
            "crt_4h_low_sweep",
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits are handled by custom_exit (take-profit, time) and the stops.
        return dataframe

    # ----- helpers -------------------------------------------------------
    def _signal_levels(self, pair: str, bar_open_time):
        """Return (H1, SP) of the signal candle preceding the bar at bar_open_time."""
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or len(frame) == 0:
            return None
        bar = pd.Timestamp(bar_open_time)
        if bar.tzinfo is None:
            bar = bar.tz_localize("UTC")
        signal_time = bar.floor(f"{BAR_MINUTES}min") - timedelta(minutes=BAR_MINUTES)
        dates = pd.to_datetime(frame["date"], utc=True)
        rows = frame[dates == signal_time]
        if len(rows) == 0:
            return None
        row = rows.iloc[-1]
        h1, sp = row["crt_h1"], row["crt_sp"]
        if pd.isna(h1) or pd.isna(sp):
            return None
        return float(h1), float(sp)

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
        levels = self._signal_levels(pair, current_time)
        if levels is None:
            return False
        h1, sp = levels
        return bool(rate < h1 and rate > sp)

    def custom_stoploss(
        self, pair, trade, current_time, current_rate, current_profit, **kwargs
    ) -> float:
        levels = self._signal_levels(pair, trade.open_date_utc)
        if levels is None:
            return self.stoploss
        _, sp = levels
        d = (trade.open_rate - sp) / trade.open_rate
        if not d > 0:
            return self.stoploss
        stop_price = trade.open_rate * (1.0 - d)
        value = stop_price / current_rate - 1.0
        return float(min(-0.0001, max(value, self.stoploss)))

    def custom_exit(
        self, pair, trade, current_time, current_rate, current_profit, **kwargs
    ):
        levels = self._signal_levels(pair, trade.open_date_utc)
        if levels is not None:
            h1, _ = levels
            if current_rate >= h1:
                return "crt_target_h1"
        if current_time - trade.open_date_utc >= timedelta(
            minutes=BAR_MINUTES * TIME_EXIT_BARS
        ):
            return "crt_time_exit_12h"
        return None

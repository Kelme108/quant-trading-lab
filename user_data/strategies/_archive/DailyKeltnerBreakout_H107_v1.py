"""H-107: two-hour Keltner band thrust above the 100-block mean, session entries, flat by 23:00 UTC or 12h.

Rule (research/proposals/H-107.json), chart 1h, closed bars only, UTC, long only, spot:
- Two-hour blocks are built from the 1h bars: the pair of bars opening at an even UTC hour H and at H+1.
  open = open(H), high = max of highs, low = min of lows, close = close(H+1). A block exists only if both bars
  are present. Its values are written on the H+1 row and forward-filled, so nothing is visible before it closed.
- On the series of complete blocks: EMA20 of close (alpha 2/21, seeded with the first close);
  TR(b) = max(high-low, |high-close(b-1)|, |low-close(b-1)|); ATR20 = Wilder smoothing (alpha 1/20) of TR,
  seeded with the mean of the first 20 TRs; UpperBand = EMA20 + 1.5 * ATR20; SMA100 = mean of last 100 closes.
- ENTRY (only on the H+1 row, when a block closes): close(b) > UpperBand(b) and close(b-1) <= UpperBand(b-1)
  and close(b) > SMA100(b) and the block opened at 00:00..16:00 UTC. Fills at the next 1h open.
- EXITS, first to occur: (1) a block closes below its EMA20 (next open); (2) native stop -2% from the entry fill;
  (3) session exit: signal on the bar opening 22:00 UTC, filled at the 23:00 open; (4) time exit at the first
  1h open at least 12 hours after the entry fill (custom_exit).
- No take-profit, no cooldown, no pyramiding. Warm-up 1000 bars.
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

EMA_LENGTH = 20
ATR_LENGTH = 20
BAND_MULT = 1.5
SMA_LENGTH = 100
ENTRY_LAST_BLOCK_OPEN_HOUR = 16
SESSION_EXIT_SIGNAL_HOUR = 22
MAX_HOLD_HOURS = 12


def keltner_block_values(
    block_open: np.ndarray, block_high: np.ndarray, block_low: np.ndarray, block_close: np.ndarray
):
    """EMA20, ATR20 (Wilder), upper band, previous-block close/upper band, for a series of complete blocks.

    Purely recursive and backward-looking: the value for block b depends only on blocks 0..b.
    """
    n = len(block_close)
    ema = np.full(n, np.nan)
    atr = np.full(n, np.nan)
    if n == 0:
        return ema, atr, np.full(n, np.nan)
    alpha = 2.0 / (EMA_LENGTH + 1.0)
    ema[0] = block_close[0]
    for i in range(1, n):
        ema[i] = alpha * block_close[i] + (1.0 - alpha) * ema[i - 1]

    tr = np.full(n, np.nan)
    for i in range(1, n):
        prev_close = block_close[i - 1]
        tr[i] = max(
            block_high[i] - block_low[i],
            abs(block_high[i] - prev_close),
            abs(block_low[i] - prev_close),
        )
    # TR exists from the second block; ATR is seeded with the mean of the first ATR_LENGTH TRs.
    if n > ATR_LENGTH:
        atr[ATR_LENGTH] = tr[1 : ATR_LENGTH + 1].mean()
        for i in range(ATR_LENGTH + 1, n):
            atr[i] = (atr[i - 1] * (ATR_LENGTH - 1) + tr[i]) / ATR_LENGTH
    upper = ema + BAND_MULT * atr
    return ema, atr, upper


class DailyKeltnerBreakout_H107_v1(IStrategy):
    """Fresh close of a 2h block above EMA20 + 1.5 ATR20 and above SMA100, session entries, intraday exits."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    trailing_stop = False
    use_custom_stoploss = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    process_only_new_candles = True
    startup_candle_count = 1000

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        dates = dataframe["date"]
        hour = dates.dt.hour
        one_hour = pd.Timedelta(hours=1)

        prev_open = dataframe["open"].shift(1)
        prev_high = dataframe["high"].shift(1)
        prev_low = dataframe["low"].shift(1)
        values_ok = (
            dataframe[["open", "high", "low", "close"]].notna().all(axis=1)
            & prev_open.notna()
            & prev_high.notna()
            & prev_low.notna()
        )
        # A block closes on the odd-hour row, and only if the even-hour bar is exactly one hour before it.
        is_block = ((hour % 2) == 1) & ((dates - dates.shift(1)) == one_hour) & values_ok
        block_rows = np.flatnonzero(is_block.to_numpy())

        block_open = prev_open.to_numpy(dtype=float)[block_rows]
        block_high = np.maximum(dataframe["high"].to_numpy(dtype=float), prev_high.to_numpy(dtype=float))[block_rows]
        block_low = np.minimum(dataframe["low"].to_numpy(dtype=float), prev_low.to_numpy(dtype=float))[block_rows]
        block_close = dataframe["close"].to_numpy(dtype=float)[block_rows]

        ema, atr, upper = keltner_block_values(block_open, block_high, block_low, block_close)
        sma = pd.Series(block_close).rolling(SMA_LENGTH).mean().to_numpy()
        prev_block_close = pd.Series(block_close).shift(1).to_numpy()
        prev_upper = pd.Series(upper).shift(1).to_numpy()

        def on_rows(values: np.ndarray) -> pd.Series:
            full = np.full(n, np.nan)
            full[block_rows] = values
            return pd.Series(full, index=dataframe.index)

        dataframe["kc_block"] = on_rows(np.ones(len(block_rows))).notna()
        dataframe["kc_block_close"] = on_rows(block_close)
        dataframe["kc_prev_block_close"] = on_rows(prev_block_close)
        dataframe["kc_prev_upper"] = on_rows(prev_upper)
        # Forward-fill so the latest completed block's values are visible on later 1h rows.
        dataframe["kc_ema20"] = on_rows(ema).ffill()
        dataframe["kc_atr20"] = on_rows(atr).ffill()
        dataframe["kc_upper"] = on_rows(upper).ffill()
        dataframe["kc_sma100"] = on_rows(sma).ffill()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = dataframe["date"].dt.hour
        block_open_hour = hour - 1
        ready = (
            dataframe["kc_block"]
            & dataframe["kc_block_close"].notna()
            & dataframe["kc_prev_block_close"].notna()
            & dataframe["kc_upper"].notna()
            & dataframe["kc_prev_upper"].notna()
            & dataframe["kc_sma100"].notna()
            & (dataframe["volume"] > 0)
        )
        thrust = dataframe["kc_block_close"] > dataframe["kc_upper"]
        fresh = dataframe["kc_prev_block_close"] <= dataframe["kc_prev_upper"]
        trend = dataframe["kc_block_close"] > dataframe["kc_sma100"]
        in_window = (block_open_hour >= 0) & (block_open_hour <= ENTRY_LAST_BLOCK_OPEN_HOUR)
        signal = ready & thrust & fresh & trend & in_window
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "keltner_2h_thrust")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        live = (dataframe["volume"] > 0) & dataframe["date"].notna()
        centre_exit = (
            live
            & dataframe["kc_block"]
            & dataframe["kc_ema20"].notna()
            & dataframe["kc_block_close"].notna()
            & (dataframe["kc_block_close"] < dataframe["kc_ema20"])
        )
        session_exit = live & (dataframe["date"].dt.hour == SESSION_EXIT_SIGNAL_HOUR)
        dataframe.loc[centre_exit, ["exit_long", "exit_tag"]] = (1, "below_ema20")
        dataframe.loc[session_exit & ~centre_exit, ["exit_long", "exit_tag"]] = (1, "session_exit")
        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> Optional[str]:
        if current_time >= trade.open_date_utc + timedelta(hours=MAX_HOLD_HOURS):
            return "time_exit_12h"
        return None

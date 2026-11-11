"""H-106: two-hour-block Double 7 dip on 1h candles (long only, spot).

Rule (research/proposals/H-106.json):
- BLOCKS: two-hour blocks aligned to even UTC hours. A block is used only when both of its
  hourly candles exist; its close Cb is the close of the candle opening at HH+1:00.
  Signals are evaluated only on 1h rows that open at an odd UTC hour; orders fill at the next
  hourly open.
- Indicators on block closes, including the just-finished block b: SMA200b (mean of the last 200
  block closes), LOW7 (lowest of the last 7 block closes), HIGH7 (highest of the last 7).
  A window that contains a missing block is undefined (no signal).
- ENTRY: Cb > SMA200b AND Cb <= LOW7 AND the block started at 00:00..16:00 UTC (fills 02:00-18:00).
- EXITS, first wins: (1) a later block with Cb >= HIGH7; (2) native stop -2% (intrabar);
  (3) clock exit: signal on the candle opening 22:00 (sell at 23:00 open);
  (4) time exit: first hourly open at or after fill + 12 hours (custom_exit).
- No ROI, no trailing, no cooldown. Warm-up 420 bars.
"""

from datetime import timedelta

import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

SMA_BLOCKS = 200
LOW_BLOCKS = 7
HIGH_BLOCKS = 7
BLOCK_FREQ = "2h"
ENTRY_LAST_BLOCK_START_HOUR = 16
CLOCK_EXIT_SIGNAL_HOUR = 22  # signal on the 22:00 candle, sell at the 23:00 open
CLOCK_EXIT_HOUR = 23
MAX_HOLD_HOURS = 12


class Double7ChannelDip_H106_v1(IStrategy):
    """Connors Double 7 on two-hour blocks: 7-block closing low above the 200-block mean."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 420

    @property
    def protections(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"])
        hour = date.dt.hour
        block_start = date.dt.floor(BLOCK_FREQ)

        # A block is complete on its odd-hour row when the previous row is exactly 1h earlier.
        prev_is_adjacent = (date - date.shift(1)) == pd.Timedelta(hours=1)
        complete = (hour % 2 == 1) & prev_is_adjacent

        closes = pd.Series(
            dataframe["close"].astype(float).where(complete).values, index=pd.DatetimeIndex(block_start)
        ).dropna()
        closes = closes[~closes.index.duplicated(keep="last")]

        if len(closes) > 0:
            grid = pd.date_range(closes.index.min(), closes.index.max(), freq=BLOCK_FREQ)
            block_closes = closes.reindex(grid)
        else:
            block_closes = closes

        sma = block_closes.rolling(SMA_BLOCKS).mean()
        low7 = block_closes.rolling(LOW_BLOCKS).min()
        high7 = block_closes.rolling(HIGH_BLOCKS).max()

        def lookup(series: pd.Series) -> pd.Series:
            values = block_start.map(series)
            return values.where(complete).astype(float)

        dataframe["hour_utc"] = hour.values
        dataframe["block_complete"] = complete.values
        dataframe["block_close"] = lookup(block_closes)
        dataframe["block_sma"] = lookup(sma)
        dataframe["block_low7"] = lookup(low7)
        dataframe["block_high7"] = lookup(high7)
        dataframe["block_start_hour"] = (hour - 1).values
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["block_complete"].astype(bool)
            & dataframe["block_close"].notna()
            & dataframe["block_sma"].notna()
            & dataframe["block_low7"].notna()
            & (dataframe["volume"] > 0)
        )
        signal = (
            defined
            & (dataframe["block_close"] > dataframe["block_sma"])
            & (dataframe["block_close"] <= dataframe["block_low7"])
            & (dataframe["block_start_hour"] >= 0)
            & (dataframe["block_start_hour"] <= ENTRY_LAST_BLOCK_START_HOUR)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "double7_block_dip")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        channel_defined = (
            dataframe["block_complete"].astype(bool)
            & dataframe["block_close"].notna()
            & dataframe["block_high7"].notna()
            & (dataframe["volume"] > 0)
        )
        channel_exit = channel_defined & (dataframe["block_close"] >= dataframe["block_high7"])
        clock_exit = (dataframe["hour_utc"] == CLOCK_EXIT_SIGNAL_HOUR) & (dataframe["volume"] > 0)
        dataframe.loc[clock_exit, ["exit_long", "exit_tag"]] = (1, "clock_exit_23utc")
        dataframe.loc[channel_exit, ["exit_long", "exit_tag"]] = (1, "block_close_at_high7")
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        opened = pd.Timestamp(trade.open_date_utc)
        now = pd.Timestamp(current_time)
        if now >= opened + timedelta(hours=MAX_HOLD_HOURS):
            return "time_exit_12h"
        if now.normalize() > opened.normalize() or now.hour >= CLOCK_EXIT_HOUR:
            return "clock_exit_23utc"
        return None

"""H-138: Williams Greatest Swing Value breakout on 8h UTC sessions, 15m entry, flat at session end.

Rule (research/proposals/H-138.json), 15m, UTC, closed bars only, spot, long only:
- SESSIONS: 00:00, 08:00, 16:00 UTC blocks of 32 15m bars (offset k opens at start + 15*k min).
  Session candle: open = first bar open, high = max, low = min, close = last bar close (bars present).
- NOISE: close > open -> open - low; close < open -> high - open; equal -> min(open - low, high - open).
- AvgNoise = mean NOISE of the last 10 completed session candles (current excluded; a missing
  session inside the window makes it undefined). GSV = 2 x AvgNoise. O = open of the first bar.
  LEVEL_UP = O + GSV, LEVEL_DN = O - GSV. ARMED: GSV / O >= 0.008.
- FILTER: close of the last COMPLETED 4h candle > SMA(50) of 4h closes (4h candles built from the 15m
  data in UTC blocks, attached with merge_informative_pair, so only closed 4h bars are visible).
- ENTRY (signal at the close, fill at the next open): armed session, offset 0..27, close > LEVEL_UP,
  FILTER true, and it is the first such bar of the session (one entry per session, no re-entry).
- EXITS: (a) a bar closes < LEVEL_DN of its session (the entry session) -> exit signal;
  (b) time exit in custom_exit: the position is sold at the first bar opening at or after the end of
  the entry session (the offset-31 bar closes, next open is the boundary);
  (c) native stoploss 3%. No take-profit, no trailing, no cooldown.
- Warm-up 900 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair

SESSION_HOURS = 8
BAR_MINUTES = 15
BARS_PER_SESSION = 32
NOISE_LOOKBACK = 10
GSV_MULTIPLE = 2.0
MIN_GSV_OVER_OPEN = 0.008
LAST_ENTRY_OFFSET = 27
HTF_SMA_LENGTH = 50


def four_hour_from_intraday(dataframe: DataFrame) -> DataFrame:
    """4h UTC-block closes from the 15m bars, on a gap-free calendar, with the 50-block simple mean."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    block = dates.dt.floor("4h")
    block_close = dataframe["close"].groupby(block.to_numpy()).last()
    block_close.index = pd.DatetimeIndex(block_close.index)
    if block_close.index.tz is None:
        block_close.index = block_close.index.tz_localize("UTC")
    calendar = pd.date_range(block_close.index.min(), block_close.index.max(), freq="4h")
    block_close = block_close.reindex(calendar)
    return DataFrame(
        {
            "date": calendar,
            "close": block_close.to_numpy(dtype=float),
            "hsma": block_close.rolling(HTF_SMA_LENGTH).mean().to_numpy(dtype=float),
        }
    )


def session_noise(dataframe: DataFrame, session: pd.Series) -> pd.Series:
    """Per-session AvgNoise of the 10 previous completed sessions, indexed by session start."""
    grouped = DataFrame(
        {
            "open": dataframe["open"].astype(float),
            "high": dataframe["high"].astype(float),
            "low": dataframe["low"].astype(float),
            "close": dataframe["close"].astype(float),
        },
        index=dataframe.index,
    ).groupby(session)
    candles = DataFrame(
        {
            "open": grouped["open"].first(),
            "high": grouped["high"].max(),
            "low": grouped["low"].min(),
            "close": grouped["close"].last(),
        }
    )
    candles.index = pd.DatetimeIndex(candles.index)
    calendar = pd.date_range(
        candles.index.min(), candles.index.max(), freq=f"{SESSION_HOURS}h", tz=candles.index.tz
    )
    candles = candles.reindex(calendar)
    down = candles["open"] - candles["low"]
    up = candles["high"] - candles["open"]
    noise = pd.Series(
        np.where(
            candles["close"] > candles["open"],
            down,
            np.where(candles["close"] < candles["open"], up, np.minimum(down, up)),
        ),
        index=calendar,
    ).where(candles["close"].notna() & candles["open"].notna())
    return noise.rolling(NOISE_LOOKBACK).mean().shift(1)


class GreatestSwingValue_H138_v1(IStrategy):
    """Buy a close beyond open + 2 x AvgNoise in an armed 8h session, 4h uptrend; flat at session end."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 900

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        session = date.dt.floor(f"{SESSION_HOURS}h")
        key = pd.DatetimeIndex(session)

        avg_noise = session_noise(dataframe, session)
        dataframe["avg_noise"] = avg_noise.reindex(key).to_numpy(dtype=float)
        dataframe["session_open"] = (
            dataframe["open"].groupby(session).transform("first").astype(float)
        )
        dataframe["session_offset"] = (
            (date - session).dt.total_seconds() // (BAR_MINUTES * 60)
        ).to_numpy()
        dataframe["gsv"] = GSV_MULTIPLE * dataframe["avg_noise"]
        dataframe["level_up"] = dataframe["session_open"] + dataframe["gsv"]
        dataframe["level_dn"] = dataframe["session_open"] - dataframe["gsv"]
        dataframe["gsv_ratio"] = dataframe["gsv"] / dataframe["session_open"]
        dataframe["session_start"] = session

        four_hour = four_hour_from_intraday(dataframe)
        dataframe = merge_informative_pair(dataframe, four_hour, self.timeframe, "4h", ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        cond = (
            close.notna()
            & dataframe["level_up"].notna()
            & dataframe["gsv_ratio"].notna()
            & dataframe["close_4h"].notna()
            & dataframe["hsma_4h"].notna()
            & (dataframe["volume"] > 0)
            & (dataframe["gsv_ratio"] >= MIN_GSV_OVER_OPEN)
            & (dataframe["session_offset"] <= LAST_ENTRY_OFFSET)
            & (close > dataframe["level_up"])
            & (dataframe["close_4h"] > dataframe["hsma_4h"])
        ).fillna(False)
        # Only the first qualifying bar of each session may signal an entry.
        order = cond.astype(int).groupby(dataframe["session_start"]).cumsum()
        first = cond & (order == 1)
        dataframe.loc[first, ["enter_long", "enter_tag"]] = (1, "gsv_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hit = (
            dataframe["level_dn"].notna()
            & dataframe["close"].notna()
            & (dataframe["volume"] > 0)
            & (dataframe["close"] < dataframe["level_dn"])
        ).fillna(False)
        dataframe.loc[hit, ["exit_long", "exit_tag"]] = (1, "close_below_gsv_dn")
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        opened = pd.Timestamp(trade.open_date_utc)
        session_end = opened.floor(f"{SESSION_HOURS}h") + timedelta(hours=SESSION_HOURS)
        if pd.Timestamp(current_time) >= session_end:
            return "time_exit_session_end"
        return None

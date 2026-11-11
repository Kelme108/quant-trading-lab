"""H-113: cross-sectional abnormal-volume (attention) leader on 1h, spot long only.

Closed candles only; signal at the close of bar t, order filled at the open of bar t+1.
All times UTC.

Universe: BTC, ETH, BNB, XRP, ADA, LTC, LINK, DOGE, SOL against USDT. Every pair other
than the traded pair X is loaded as an informative 1h pair and aligned on the candle date.

Per pair i at bar t (backwards looking, clock-time grid, gaps become NaN):
- V4(t)   = sum of volume over bars t-3..t (4 bars, current included)
- Base(t) = mean of V4(t-4k), k = 1..42 (all 42 terms required, Base > 0)
- AV(t)   = V4(t) / Base(t)
- R4(t)   = close(t) / close(t-4) - 1

A pair counts at bar t only if AV(t) and R4(t) are defined. With fewer than 5 counting
pairs, or if X does not count, there is no signal. Rank counting pairs by AV (largest
first; ties by larger R4, then by pair name ascending). MED(t) = median of R4 over the
counting pairs.

Entry for X at the close of bar t when all hold: rank of X <= 2, AV_X >= 1.5,
R4_X >= 0.006 and R4_X > MED (strict), close_X > open_X, volume > 0; one position per
pair (engine); at most 2 entries per pair per UTC day of the fill time
(confirm_trade_entry); cooldown of 2 candles after any exit (CooldownPeriod).

Exits (custom_exit), first of:
- take-profit: profit >= +1.8%
- time exit: the position is closed at the open of bar e+6 (e = fill bar), i.e. an exit
  signal at the close of bar e+5, so every position lasts at most 6 hours
- stop: native stoploss of -1.0%
"""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "LTC/USDT",
    "LINK/USDT",
    "DOGE/USDT",
    "SOL/USDT",
]

VOLUME_WINDOW = 4
BASELINE_WINDOWS = 42
BASELINE_STEP = 4
RETURN_WINDOW = 4
RANK_TOP_N = 2
MIN_ABNORMAL_VOLUME = 1.5
MIN_R4 = 0.006
MIN_PAIRS = 5
MAX_ENTRIES_PER_DAY = 2
TAKE_PROFIT = 0.018
TIME_EXIT_BARS = 6  # exit at the open of bar e+6
BAR = pd.Timedelta(hours=1)


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def _hourly(frame: DataFrame, column: str) -> pd.Series:
    """Series indexed by candle date on a complete hourly grid (gaps -> NaN)."""
    data = frame[["date", column]].drop_duplicates("date").sort_values("date")
    series = data.set_index("date")[column].astype(float)
    if len(series) == 0:
        return series
    return series.asfreq("1h")


def pair_stats(frame: DataFrame) -> tuple[pd.Series, pd.Series]:
    """AV and R4 per candle date for one pair (backwards looking only)."""
    close = _hourly(frame, "close")
    volume = _hourly(frame, "volume")
    v4 = volume.rolling(VOLUME_WINDOW).sum()
    lagged = pd.concat(
        [v4.shift(BASELINE_STEP * k) for k in range(1, BASELINE_WINDOWS + 1)], axis=1
    )
    base = lagged.mean(axis=1, skipna=True).where(lagged.notna().all(axis=1))
    av = v4 / base.where(base > 0)
    r4 = close / close.shift(RETURN_WINDOW) - 1.0
    av = av.replace([np.inf, -np.inf], np.nan)
    r4 = r4.replace([np.inf, -np.inf], np.nan)
    return av, r4


class CrossSectionalAttentionVolume_H113_v1(IStrategy):
    """Buy the abnormal-volume leader among nine pairs on a rising 4h move; 6-hour cap."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.01
    trailing_stop = False
    use_exit_signal = True
    startup_candle_count = 400

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 2}]

    def informative_pairs(self):
        return [(pair, "1h") for pair in PAIRS]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get("pair", "")
        dates = dataframe["date"]

        av_cols = {}
        r4_cols = {}

        av_own, r4_own = pair_stats(dataframe)
        av_cols[pair] = dates.map(av_own).astype(float)
        r4_cols[pair] = dates.map(r4_own).astype(float)

        for other in PAIRS:
            if other == pair:
                continue
            other_df = self.dp.get_pair_dataframe(pair=other, timeframe="1h")
            if other_df is None or len(other_df) == 0:
                av_cols[other] = pd.Series(np.nan, index=dataframe.index)
                r4_cols[other] = pd.Series(np.nan, index=dataframe.index)
                continue
            av_o, r4_o = pair_stats(other_df)
            av_cols[other] = dates.map(av_o).astype(float)
            r4_cols[other] = dates.map(r4_o).astype(float)

        av = pd.DataFrame(av_cols, index=dataframe.index)
        r4 = pd.DataFrame(r4_cols, index=dataframe.index)
        counting = av.notna() & r4.notna()
        av = av.where(counting)
        r4 = r4.where(counting)

        av_x = av[pair]
        r4_x = r4[pair]
        beats = pd.DataFrame(False, index=dataframe.index, columns=list(av.columns))
        for other in av.columns:
            if other == pair:
                continue
            av_j = av[other]
            r4_j = r4[other]
            same_av = av_j == av_x
            beats[other] = (
                (av_j > av_x)
                | (same_av & (r4_j > r4_x))
                | (same_av & (r4_j == r4_x) & (other < pair))
            ).fillna(False) & counting[other]

        dataframe["av"] = av_x.to_numpy()
        dataframe["r4"] = r4_x.to_numpy()
        dataframe["xs_count"] = counting.sum(axis=1)
        dataframe["xs_median"] = r4.median(axis=1, skipna=True)
        dataframe["xs_rank"] = (1 + beats.sum(axis=1)).where(counting[pair])
        dataframe["in_universe"] = pair in PAIRS
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        r4 = dataframe["r4"]
        cond = (
            dataframe["in_universe"].astype(bool)
            & dataframe["av"].notna()
            & r4.notna()
            & dataframe["xs_median"].notna()
            & dataframe["xs_rank"].notna()
            & dataframe["open"].notna()
            & dataframe["close"].notna()
            & (dataframe["xs_count"] >= MIN_PAIRS)
            & (dataframe["xs_rank"] <= RANK_TOP_N)
            & (dataframe["av"] >= MIN_ABNORMAL_VOLUME)
            & (r4 >= MIN_R4)
            & (r4 > dataframe["xs_median"])
            & (dataframe["close"] > dataframe["open"])
            & (dataframe["volume"] > 0)
        ).fillna(False)
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "attention_leader")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Take-profit and time exit depend on the open trade: see custom_exit.
        return dataframe

    def confirm_trade_entry(
        self,
        pair,
        order_type,
        amount,
        rate,
        time_in_force,
        current_time,
        entry_tag,
        side,
        **kwargs,
    ) -> bool:
        """At most 2 entries per pair per UTC day of the fill time (closed trades included)."""
        today = utc_day(current_time)
        opened_today = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                opened_today += 1
        return opened_today < MAX_ENTRIES_PER_DAY

    def custom_exit(
        self,
        pair: str,
        trade,
        current_time,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> Optional[str]:
        if current_profit is not None and current_profit >= TAKE_PROFIT:
            return "take_profit_1p8"

        # Fill at the open of bar e; the exit signal is the close of bar e+5, so the
        # order goes out at the open of bar e+6.
        fill_bar = pd.Timestamp(trade.open_date_utc).floor("1h")
        if pd.Timestamp(current_time) >= fill_bar + TIME_EXIT_BARS * BAR:
            return "time_exit_6h"
        return None

"""H-143: hourly cross-sectional momentum, buy 4h leaders of the pair universe on volume (1h).

Rule (research/proposals/H-143.json), 1h, UTC, closed bars, bar time = open time, spot, long only.
A signal at the close of bar t fills at the next bar open.

- Universe: the traded pair plus every other whitelisted pair (informative 1h pairs, same timestamp).
- CHECK BARS: bars opening 03, 07, 11, 15, 19, 23 UTC.
- r4(t) = close(t) / close(t-4) - 1.
  VR(t) = mean volume of bars t-3..t / mean volume of bars t-123..t-4 (the 120 bars before).
- A pair COUNTS at t if it has a candle at t (volume > 0; gap-filled candles carry zero volume),
  r4 and VR are defined (denominator > 0). Fewer than 10 counting pairs, or the traded pair not
  counting: no entry.
- RANK: counting pairs ordered by r4 descending (1 = highest); exact ties by pair name ascending.
- ENTRY at the close of a check bar: rank <= 5, r4 >= 0.015, VR >= 1.5 (flat is handled by the engine).
- EXITS: take-profit +2% and the 12 h time exit in custom_exit; stop-loss -1.2% native (stoploss);
  CHECK EXIT: exit signal at a check bar unless the pair counts with rank <= 5 and r4 >= 0.015
  (no volume condition, no minimum pair count).
- Time exit: the trade opens at the fill bar e; the sale is at the open of bar e+12, i.e. 12 hours after the
  fill, whatever the check says.
- Warm-up 200 bars (longest lookback 124).
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

CHECK_HOURS = (3, 7, 11, 15, 19, 23)
RETURN_BARS = 4
VOLUME_RECENT_BARS = 4
VOLUME_BASE_BARS = 120
RANK_MAX = 5
MIN_R4 = 0.015
VOLUME_RATIO_MIN = 1.5
MIN_COUNTING_PAIRS = 10
TAKE_PROFIT_PCT = 0.02
TIME_EXIT_HOURS = 12


def _pair_metrics(frame: DataFrame, index: pd.DatetimeIndex):
    """Return (r4, vr, has_candle) arrays aligned on ``index`` for one pair.

    Everything looks backwards only. The series is put on a regular hourly grid first, so a
    missing hour can never shift the "4 bars ago" reference; windows touching a hole are undefined.
    """
    n = len(index)
    nan = np.full(n, np.nan)
    if frame is None or len(frame) == 0:
        return nan, nan.copy(), np.zeros(n, dtype=bool)

    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.drop_duplicates("date").sort_values("date").set_index("date")
    grid = pd.date_range(data.index.min(), data.index.max(), freq="1h")
    close = data["close"].astype(float).reindex(grid)
    volume = data["volume"].astype(float).reindex(grid)

    r4 = close / close.shift(RETURN_BARS) - 1.0
    recent = volume.rolling(VOLUME_RECENT_BARS).mean()
    base = volume.shift(VOLUME_RECENT_BARS).rolling(VOLUME_BASE_BARS).mean()
    vr = recent / base.where(base > 0)
    r4 = r4.replace([np.inf, -np.inf], np.nan)
    vr = vr.replace([np.inf, -np.inf], np.nan)
    has_candle = (volume > 0).astype(float)

    return (
        r4.reindex(index).to_numpy(dtype=float),
        vr.reindex(index).to_numpy(dtype=float),
        has_candle.reindex(index).fillna(0.0).to_numpy(dtype=float) > 0,
    )


class IntradayCrossSectionalMomentum_H143_v1(IStrategy):
    """Top-5 of the universe on 4h return, up >= 1.5% on 1.5x volume, checked six times a day."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.012
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 200

    def _whitelist(self) -> list:
        try:
            return list(self.dp.current_whitelist())
        except Exception:
            return []

    def informative_pairs(self):
        return [(pair, "1h") for pair in self._whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get("pair", "")
        index = pd.DatetimeIndex(pd.to_datetime(dataframe["date"]))
        n = len(dataframe)

        own_r4, own_vr, own_has = _pair_metrics(dataframe, index)
        own_counts = own_has & np.isfinite(own_r4) & np.isfinite(own_vr)
        own_r4_counted = np.where(own_counts, own_r4, np.nan)

        rank = np.ones(n, dtype=float)
        n_counting = own_counts.astype(float)
        for other in self._whitelist():
            if other == pair:
                continue
            try:
                other_frame = self.dp.get_pair_dataframe(pair=other, timeframe="1h")
            except Exception:
                continue
            o_r4, o_vr, o_has = _pair_metrics(other_frame, index)
            o_counts = o_has & np.isfinite(o_r4) & np.isfinite(o_vr)
            o_r4 = np.where(o_counts, o_r4, np.nan)
            n_counting = n_counting + o_counts.astype(float)
            with np.errstate(invalid="ignore"):
                ahead = o_r4 > own_r4_counted
                if other < pair:
                    ahead = ahead | (o_r4 == own_r4_counted)
            rank = rank + ahead.astype(float)

        hours = index.hour.to_numpy()
        minutes = index.minute.to_numpy()
        is_check = np.isin(hours, CHECK_HOURS) & (minutes == 0)

        dataframe["r4"] = own_r4
        dataframe["vr"] = own_vr
        dataframe["counts"] = own_counts
        dataframe["n_counting"] = n_counting
        dataframe["xs_rank"] = np.where(own_counts, rank, np.nan)
        dataframe["is_check"] = is_check
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            dataframe["is_check"].astype(bool)
            & dataframe["counts"].astype(bool)
            & dataframe["r4"].notna()
            & dataframe["vr"].notna()
            & dataframe["xs_rank"].notna()
            & (dataframe["volume"] > 0)
            & (dataframe["n_counting"] >= MIN_COUNTING_PAIRS)
            & (dataframe["xs_rank"] <= RANK_MAX)
            & (dataframe["r4"] >= MIN_R4)
            & (dataframe["vr"] >= VOLUME_RATIO_MIN)
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
            dataframe.loc[ok, "enter_tag"] = "xs_momentum_top5"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["is_check"].astype(bool)
            & dataframe["r4"].notna()
            & dataframe["vr"].notna()
            & (dataframe["volume"] > 0)
        )
        holds = (
            dataframe["counts"].astype(bool)
            & dataframe["xs_rank"].notna()
            & (dataframe["xs_rank"] <= RANK_MAX)
            & (dataframe["r4"] >= MIN_R4)
        )
        ok = defined & ~holds
        if ok.any():
            dataframe.loc[ok, "exit_long"] = 1
            dataframe.loc[ok, "exit_tag"] = "check_exit"
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        if current_profit >= TAKE_PROFIT_PCT:
            return "take_profit_2pct"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None

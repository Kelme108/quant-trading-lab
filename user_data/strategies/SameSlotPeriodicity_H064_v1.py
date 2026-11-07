"""H-064: hour-of-week periodicity, trade the weekday 4-hour block with a persistent 26-week same-slot drift.

Rule (1h, closed bars, UTC; a signal at a bar close fills at the next bar open; long only):
- Each UTC day has six 4-hour blocks b = 0..5 starting at 00, 04, 08, 12, 16, 20 UTC.
- R(d, b) = close of the bar opening at hh+3 on day d / open of the bar opening at hh on day d - 1;
  missing if any of the four bars is missing.
- For day d and each block b, use R(d - 7k, b), k = 1..26 (same weekday and block, previous 26 weeks):
  mean m(b), sample std s(b) (ddof=1), t(b) = m(b) / (s(b) / sqrt(26)). Ineligible if any observation is
  missing or s(b) = 0. b* = eligible block with the largest t; ties go to the earliest block.
- Entry only if m(b*) >= 0.0040 and t(b*) >= 1.5: entry signal at the close of the bar opening at hh-1
  (block 0: the 23:00 bar of day d-1), i.e. buy at the open of the first bar of block b*.
- Exit signal at the close of the bar opening at hh+3 (hold 4 bars). Stop-loss 3% (native, intrabar).
- At most one entry per day; if a position is still open when the entry signal fires, the entry is skipped.

Implementation notes
- Bars are placed on a complete UTC hourly grid so that a missing bar is a gap, not a neighbouring row. A bar
  counts as missing if it is absent, has an undefined open/close, or has zero volume (Freqtrade fills gaps in
  the data with zero-volume candles).
- The selection for day d uses only days d-7 .. d-182, all closed before the 23:00 bar of day d-1 closes.
- Collision: the exit signal of a block-5 trade on day d (close of the 23:00 bar) falls on the same candle as
  the entry signal of a block-0 selection on day d+1. Freqtrade ignores an exit when an entry signal is on the
  same candle and ignores an entry when an exit signal is on it, so on that candle only one signal is emitted:
  the exit when the block-5 position is still open (the new entry is skipped, as the rule says), and the entry
  when it is not (its entry signal was not emitted, or the 3% stop was hit at some bar of block 5: low <= 0.97 x
  open of the 20:00 bar, the fill price). This uses only bars up to and including that candle.
"""

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BLOCK_HOURS = 4
BLOCKS_PER_DAY = 6
LOOKBACK_WEEKS = 26
STD_DDOF = 1
MIN_MEAN_RETURN = 0.004
MIN_T_STAT = 1.5
STOP_LOSS = 0.03


def same_slot_signals(dataframe: DataFrame) -> DataFrame:
    """Return per-row columns slot_entry, slot_exit (0/1) and the day's selection (block, mean, t).

    Causal: the selection for day d uses days d-7k (k >= 1) only; the signal rows lie at or after every bar used.
    """
    n = len(dataframe)
    out = pd.DataFrame(
        {
            "slot_entry": np.zeros(n, dtype=int),
            "slot_exit": np.zeros(n, dtype=int),
            "slot_block": np.full(n, np.nan),
            "slot_mean": np.full(n, np.nan),
            "slot_t": np.full(n, np.nan),
        },
        index=dataframe.index,
    )
    if n == 0:
        return out

    dates = pd.to_datetime(dataframe["date"])
    if dates.dt.tz is None:
        dates = dates.dt.tz_localize("UTC")
    else:
        dates = dates.dt.tz_convert("UTC")
    dates = dates.dt.floor("h")
    stamps = pd.DatetimeIndex(dates)

    bars = pd.DataFrame(
        {
            "open": dataframe["open"].to_numpy(dtype=float),
            "low": dataframe["low"].to_numpy(dtype=float),
            "close": dataframe["close"].to_numpy(dtype=float),
            "volume": dataframe["volume"].to_numpy(dtype=float),
        },
        index=stamps,
    )
    bars = bars[~bars.index.duplicated(keep="last")]

    first_day = bars.index.min().floor("D")
    last_day = bars.index.max().floor("D")
    grid = pd.date_range(first_day, last_day + pd.Timedelta(hours=23), freq="h")
    g = bars.reindex(grid)
    n_days = len(grid) // 24

    present = (g["open"].notna() & g["close"].notna() & (g["volume"] > 0)).to_numpy()
    opens = g["open"].to_numpy()
    closes = g["close"].to_numpy()
    lows = g["low"].to_numpy()
    volume_ok = (g["volume"] > 0).to_numpy()

    # Slot returns R[day, block]
    present_d = present.reshape(n_days, BLOCKS_PER_DAY, BLOCK_HOURS)
    opens_d = opens.reshape(n_days, BLOCKS_PER_DAY, BLOCK_HOURS)
    closes_d = closes.reshape(n_days, BLOCKS_PER_DAY, BLOCK_HOURS)
    complete = present_d.all(axis=2)
    ret = np.where(complete, closes_d[:, :, 3] / opens_d[:, :, 0] - 1.0, np.nan)

    # Same weekday and block over the previous LOOKBACK_WEEKS weeks: R[d - 7k], k = 1..26
    hist = np.full((LOOKBACK_WEEKS, n_days, BLOCKS_PER_DAY), np.nan)
    for k in range(1, LOOKBACK_WEEKS + 1):
        lag = 7 * k
        if lag < n_days:
            hist[k - 1, lag:, :] = ret[: n_days - lag, :]
    all_valid = ~np.isnan(hist).any(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        safe = np.where(np.isnan(hist), 0.0, hist)
        mean = np.where(all_valid, safe.mean(axis=0), np.nan)
        std = np.where(all_valid, safe.std(axis=0, ddof=STD_DDOF), np.nan)
        tstat = mean / (std / np.sqrt(LOOKBACK_WEEKS))
    eligible = all_valid & (std > 0)
    score = np.where(eligible, tstat, -np.inf)
    best = np.argmax(score, axis=1)  # first maximum -> earliest block on ties
    any_eligible = eligible.any(axis=1)
    rows = np.arange(n_days)
    m_star = np.where(any_eligible, mean[rows, best], np.nan)
    t_star = np.where(any_eligible, tstat[rows, best], np.nan)
    passes = any_eligible & (m_star >= MIN_MEAN_RETURN) & (t_star >= MIN_T_STAT)

    total = len(grid)
    entry = np.zeros(total, dtype=bool)
    exit_ = np.zeros(total, dtype=bool)
    sel_block = np.full(total, np.nan)
    sel_mean = np.full(total, np.nan)
    sel_t = np.full(total, np.nan)
    for d in range(n_days):
        sel_block[d * 24 : (d + 1) * 24] = best[d] if any_eligible[d] else np.nan
        sel_mean[d * 24 : (d + 1) * 24] = m_star[d]
        sel_t[d * 24 : (d + 1) * 24] = t_star[d]
        if not passes[d]:
            continue
        start = d * 24 + best[d] * BLOCK_HOURS
        entry_row = start - 1
        exit_row = start + BLOCK_HOURS - 1
        if entry_row >= 0:
            entry[entry_row] = True
        exit_[exit_row] = True

    # Signals never fire on zero-volume (or absent) candles.
    entry &= volume_ok
    exit_ &= volume_ok

    # Collision of a block-5 exit (day d) with a block-0 entry (day d+1) on the 23:00 bar of day d.
    last_start = (BLOCKS_PER_DAY - 1) * BLOCK_HOURS
    for d in range(n_days):
        row = d * 24 + 23
        if not (entry[row] and exit_[row]):
            continue
        start = d * 24 + last_start
        opened = entry[start - 1]
        fill = opens[start]
        block_lows = lows[start : start + BLOCK_HOURS]
        stopped = bool(
            np.isfinite(fill) and np.any(np.isfinite(block_lows) & (block_lows <= fill * (1.0 - STOP_LOSS)))
        )
        if opened and not stopped:
            entry[row] = False  # position still open: skip the entry, keep the time exit
        else:
            exit_[row] = False  # no position: keep the entry

    grid_frame = pd.DataFrame(
        {
            "slot_entry": entry.astype(int),
            "slot_exit": exit_.astype(int),
            "slot_block": sel_block,
            "slot_mean": sel_mean,
            "slot_t": sel_t,
        },
        index=grid,
    )
    lookup = grid_frame.reindex(stamps)
    out["slot_entry"] = lookup["slot_entry"].fillna(0).astype(int).to_numpy()
    out["slot_exit"] = lookup["slot_exit"].fillna(0).astype(int).to_numpy()
    out["slot_block"] = lookup["slot_block"].to_numpy()
    out["slot_mean"] = lookup["slot_mean"].to_numpy()
    out["slot_t"] = lookup["slot_t"].to_numpy()
    return out


class SameSlotPeriodicity_H064_v1(IStrategy):
    """Trade the 4-hour block whose same-weekday 26-week drift has the largest t-statistic."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 4400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        signals = same_slot_signals(dataframe)
        for column in signals.columns:
            dataframe[column] = signals[column]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # slot_entry is 1 only where the selected block's mean and t are defined and pass both thresholds.
        ok = (dataframe["slot_entry"] == 1) & (dataframe["volume"] > 0)
        dataframe.loc[ok, ["enter_long", "enter_tag"]] = (1, "same_slot_block")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (dataframe["slot_exit"] == 1) & (dataframe["volume"] > 0)
        dataframe.loc[ok, ["exit_long", "exit_tag"]] = (1, "same_slot_time_exit")
        return dataframe

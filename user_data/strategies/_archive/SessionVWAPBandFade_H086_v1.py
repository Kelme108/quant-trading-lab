"""H-086: UTC-session VWAP 2-sigma lower-band fade on 15m; exit at VWAP, flat by day end.

Closed 15m bars only, UTC clock; a signal at the close of bar t fills at the open of bar t+1.
Long only, spot, one position per pair, whole stake, no leverage.

Session = UTC day, reset at 00:00. tp = (high + low + close) / 3.
VWAP(t) = sum(tp * v) / sum(v) over the session's bars 00:00 .. t.
SD(t)   = sqrt(sum(v * (tp - VWAP(t))^2) / sum(v)) over the same bars.
LB(t)   = VWAP(t) - 2.0 * SD(t).
A session whose first bar is not the 00:00 bar (data starts mid-day) has no defined VWAP.

Signal window: bars opening 02:00 .. 19:45 UTC (tag bars and entry bars).
Trend-day filter: an earlier bar of the same session closed above its own VWAP.
Tag: bar k in the window with low(k) <= LB(k), passing the trend-day filter.
Entry at the close of the first bar t, k+1 <= t <= k+8 (k = most recent tag of the session), in the window,
with LB(t) < close(t) < VWAP(t) and (VWAP(t) - close(t)) / close(t) >= 0.008, and no position open.
Each tag gives at most one entry; after an exit a new tag after the exit bar is required; at most two
entries per session. These state rules are applied by a backward-only bar-by-bar simulation of this
pair's own position (fill at next open, 1% stop intrabar, the exits below).

Stop: native fixed stoploss -1% (intrabar).
Target: exit signal at the close of a bar whose close >= that bar's session VWAP (fill at next open).
Time exit: exit signal at the close of the 23:45 bar (fill at the 00:00 open); custom_exit also exits
after 12 hours (48 bars) in the trade and, as a backstop, at or after 00:00 UTC following the entry day.
Warm-up: 192 bars (no entry on the first 192 rows).
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BAND_SD_MULT = 2.0
WINDOW_START_MINUTE = 2 * 60  # 02:00
WINDOW_LAST_MINUTE = 19 * 60 + 45  # 19:45
SESSION_END_MINUTE = 23 * 60 + 45  # 23:45 bar
REENTRY_WINDOW_BARS = 8
MIN_DISTANCE_TO_VWAP = 0.008
MAX_ENTRIES_PER_SESSION = 2
STOPLOSS_PCT = 0.01
MAX_HOLD_BARS = 48
BAR_MINUTES = 15
WARMUP_BARS = 192


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC), tz-aware."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.floor("D")


def session_vwap_bands(dataframe: DataFrame) -> DataFrame:
    """Cumulative session VWAP, volume-weighted SD and lower band; backward-looking within each UTC day."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    day = dates.dt.floor("D")
    minute = dates.dt.hour * 60 + dates.dt.minute

    high = dataframe["high"].astype(float)
    low = dataframe["low"].astype(float)
    close = dataframe["close"].astype(float)
    volume = dataframe["volume"].astype(float)
    tp = (high + low + close) / 3.0

    usable = tp.notna() & volume.notna()
    vol = volume.where(usable, 0.0)
    tpv = (tp * vol).where(usable, 0.0)
    tp2v = (tp * tp * vol).where(usable, 0.0)

    cum_v = vol.groupby(day).cumsum()
    cum_tpv = tpv.groupby(day).cumsum()
    cum_tp2v = tp2v.groupby(day).cumsum()

    denom = cum_v.where(cum_v > 0)
    vwap = cum_tpv / denom
    # sum(v (tp - VWAP)^2) / sum(v) == sum(v tp^2) / sum(v) - VWAP^2
    variance = (cum_tp2v / denom - vwap * vwap).clip(lower=0.0)
    sd = np.sqrt(variance)

    # A leading session that does not start at 00:00 is incomplete: leave it undefined.
    if len(dataframe) > 0 and int(minute.iloc[0]) != 0:
        partial = day == day.iloc[0]
        vwap = vwap.mask(partial)
        sd = sd.mask(partial)

    dataframe["minute_of_day"] = minute.to_numpy()
    dataframe["session_vwap"] = vwap.to_numpy()
    dataframe["session_sd"] = sd.to_numpy()
    dataframe["session_lb"] = (vwap - BAND_SD_MULT * sd).to_numpy()

    above = (close > vwap).fillna(False) & vwap.notna()
    above_int = above.astype(int)
    # Earlier bars of the same session only (cumulative count minus the current bar).
    prior_above = above_int.groupby(day).cumsum() - above_int
    dataframe["trend_day_ok"] = (prior_above > 0).astype(int).to_numpy()
    return dataframe


def simulate_entries(dataframe: DataFrame, warmup: int) -> np.ndarray:
    """Bar-by-bar, backward-only simulation of this pair's position; returns the entry-signal mask."""
    n = len(dataframe)
    enter = np.zeros(n, dtype=bool)
    if n == 0:
        return enter

    dates = pd.to_datetime(dataframe["date"], utc=True)
    day = dates.dt.floor("D").to_numpy()
    time_ns = dates.dt.tz_convert(None).to_numpy().astype("datetime64[ns]").astype(np.int64)
    minute = dataframe["minute_of_day"].to_numpy()
    open_ = dataframe["open"].to_numpy(dtype=float)
    low = dataframe["low"].to_numpy(dtype=float)
    close = dataframe["close"].to_numpy(dtype=float)
    volume = dataframe["volume"].to_numpy(dtype=float)
    vwap = dataframe["session_vwap"].to_numpy(dtype=float)
    lb = dataframe["session_lb"].to_numpy(dtype=float)
    trend_ok = dataframe["trend_day_ok"].to_numpy() == 1

    bar_ns = BAR_MINUTES * 60 * 1_000_000_000
    max_hold_ns = MAX_HOLD_BARS * bar_ns

    in_window = (minute >= WINDOW_START_MINUTE) & (minute <= WINDOW_LAST_MINUTE)
    vol_ok = np.nan_to_num(volume, nan=0.0) > 0
    defined = ~(np.isnan(low) | np.isnan(close) | np.isnan(vwap) | np.isnan(lb))
    is_tag = in_window & vol_ok & defined & trend_ok & (low <= lb)

    with np.errstate(invalid="ignore", divide="ignore"):
        distance = (vwap - close) / close
    entry_setup = (
        in_window
        & vol_ok
        & defined
        & (close > lb)
        & (close < vwap)
        & (np.nan_to_num(distance, nan=-1.0) >= MIN_DISTANCE_TO_VWAP)
    )
    target_hit = vol_ok & defined & (close >= vwap)

    current_day = None
    entries_today = 0
    last_tag = -1
    tag_used = True
    last_exit_bar = -1
    pending = False
    in_pos = False
    fill_ns = 0
    fill_day = None
    stop_price = 0.0

    for i in range(n):
        if current_day is None or day[i] != current_day:
            current_day = day[i]
            entries_today = 0
            last_tag = -1
            tag_used = True

        if pending:
            pending = False
            if not np.isnan(open_[i]) and open_[i] > 0:
                in_pos = True
                fill_ns = time_ns[i]
                fill_day = day[i]
                stop_price = open_[i] * (1.0 - STOPLOSS_PCT)

        if in_pos:
            # Backstop exits at this bar's open (time limits reached before this bar starts).
            if day[i] != fill_day or time_ns[i] - fill_ns >= max_hold_ns:
                in_pos = False
                last_exit_bar = i - 1
        if in_pos:
            bar_close_ns = time_ns[i] + bar_ns
            if not np.isnan(low[i]) and low[i] <= stop_price:
                exited = True
            elif target_hit[i]:
                exited = True
            elif minute[i] == SESSION_END_MINUTE:
                exited = True
            elif bar_close_ns - fill_ns >= max_hold_ns:
                exited = True
            else:
                exited = False
            if exited:
                in_pos = False
                last_exit_bar = i

        if (
            not in_pos
            and i >= warmup
            and entries_today < MAX_ENTRIES_PER_SESSION
            and last_tag >= 0
            and not tag_used
            and last_tag > last_exit_bar
            and 1 <= i - last_tag <= REENTRY_WINDOW_BARS
            and entry_setup[i]
        ):
            enter[i] = True
            tag_used = True
            entries_today += 1
            pending = True

        if is_tag[i]:
            last_tag = i
            tag_used = False

    return enter


class SessionVWAPBandFade_H086_v1(IStrategy):
    """Fade a 2-sigma stretch below the UTC-session VWAP on a two-sided day; exit at VWAP or day end."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -STOPLOSS_PCT
    use_exit_signal = True
    trailing_stop = False
    startup_candle_count = 192

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return session_vwap_bands(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = simulate_entries(dataframe, self.startup_candle_count)
        if cond.any():
            mask = pd.Series(cond, index=dataframe.index)
            dataframe.loc[mask, "enter_long"] = 1
            dataframe.loc[mask, "enter_tag"] = "vwap_lb_fade"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        vwap = dataframe["session_vwap"]
        live = close.notna() & vwap.notna() & (dataframe["volume"] > 0)
        target = (live & vwap.notna() & (close >= vwap)).fillna(False)
        session_end = (live & (dataframe["minute_of_day"] == SESSION_END_MINUTE)).fillna(False)
        if target.any():
            dataframe.loc[target, "exit_long"] = 1
            dataframe.loc[target, "exit_tag"] = "vwap_target"
        only_end = session_end & ~target
        if only_end.any():
            dataframe.loc[only_end, "exit_long"] = 1
            dataframe.loc[only_end, "exit_tag"] = "session_end_2345"
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        now = pd.Timestamp(current_time)
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        opened = pd.Timestamp(trade.open_date_utc)
        if opened.tzinfo is None:
            opened = opened.tz_localize("UTC")
        if now >= utc_day(opened) + timedelta(days=1):
            return "session_end_0000"
        if now - opened >= timedelta(minutes=BAR_MINUTES * MAX_HOLD_BARS):
            return "time_exit_48_bars"
        return None

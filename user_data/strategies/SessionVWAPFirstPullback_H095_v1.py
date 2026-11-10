"""H-095: first pullback to session VWAP after a high-volume opening drive (15m, UTC).

Sessions (every UTC day): A 00:00-07:45 (32 bars), E 08:00-13:15 (22), U 13:30-23:45 (42).
Closed candles only. The signal candle t is flagged; the order fills at the open of t+1.

- Drive (known after bar 8): max(high 1-8) >= 1.012 * open(bar 1) AND summed volume of
  bars 1-8 >= 1.5 * mean of the same figure for the same session on the 14 previous
  UTC dates (all 14 must exist).
- Test bar s: first bar i >= 9 with low <= VWAP (VWAP over bars 1..s, typical price).
  Void if close(s) < VWAP(s) or volume(s) > mean volume of bars 1..s-1.
- Trigger t: s+1 if close(s+1) > high(s), else s+2 if close(s+2) > high(s); inside session.
- H = max high of bars 1..t. Valid if H >= 1.01 * close(t) and bar t+1 opens no later than
  07:00 (A), 12:15 (E) or 22:45 (U).
- Fill checks (confirm_trade_entry): skip if low(s) < 0.975 * P or P >= H.
- Stop: fixed d = (P - min(low(s), 0.99 P)) / P below the fill (custom_stoploss);
  native -3% is a backstop.
- Take-profit at H and 12-bar (3h) time exit in custom_exit; session-last-bar exit signal.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class SessionVWAPFirstPullback_H095_v1(IStrategy):
    """Buy the first light-volume VWAP pullback after an opening drive."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_custom_stoploss = True
    startup_candle_count = 1440

    drive_bars = 8
    drive_min_excursion = 0.012
    drive_volume_multiple = 1.5
    drive_volume_lookback_days = 14
    min_room_to_session_high = 0.01
    max_fill_low_distance = 0.025
    min_stop_fraction = 0.01
    time_exit_bars = 12

    # (start minute of day, last bar open minute, latest minute t+1 may open)
    session_starts = (0, 480, 810)
    session_last_open = (465, 795, 1425)
    session_latest_fill_open = (420, 735, 1365)

    # ------------------------------------------------------------------ indicators
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        sig = np.zeros(n, dtype=float)
        sig_h = np.full(n, np.nan)
        sig_low_s = np.full(n, np.nan)
        last_bar = np.zeros(n, dtype=float)

        if n == 0:
            dataframe["sig_h"] = sig_h
            dataframe["sig_low_s"] = sig_low_s
            dataframe["sig_flag"] = sig
            dataframe["session_last_bar"] = last_bar
            return dataframe

        date = dataframe["date"]
        mod = (date.dt.hour * 60 + date.dt.minute).to_numpy()
        stype = np.where(mod < 480, 0, np.where(mod < 810, 1, 2))
        starts = np.array(self.session_starts)
        i0 = (mod - starts[stype]) // 15
        day = date.dt.normalize()

        o = dataframe["open"].to_numpy(dtype=float)
        h = dataframe["high"].to_numpy(dtype=float)
        lo = dataframe["low"].to_numpy(dtype=float)
        c = dataframe["close"].to_numpy(dtype=float)
        v = dataframe["volume"].to_numpy(dtype=float)
        tp = (h + lo + c) / 3.0

        last_bar[mod == np.array(self.session_last_open)[stype]] = 1.0

        groups = pd.DataFrame({"day": day.to_numpy(), "stype": stype}).groupby(
            ["day", "stype"], sort=False
        ).indices

        # Pass 1: drive volume of each session (needs bars 1-8 all present).
        drive_vol = {}
        prefix = {}
        for key, pos in groups.items():
            pos = np.sort(pos)
            eq = i0[pos] == np.arange(len(pos))
            k = len(pos) if eq.all() else int(np.argmin(eq))
            prefix[key] = (pos[:k], k)
            if k >= self.drive_bars:
                drive_vol[key] = float(v[pos[: self.drive_bars]].sum())

        # Mean drive volume over the 14 previous UTC dates (all must exist).
        drive_mean = {}
        for st in range(3):
            items = {k[0]: val for k, val in drive_vol.items() if k[1] == st}
            if not items:
                continue
            ser = pd.Series(items).sort_index()
            full = pd.date_range(ser.index.min(), ser.index.max(), freq="D")
            ser = ser.reindex(full)
            mean = ser.shift(1).rolling(self.drive_volume_lookback_days).mean()
            for d_, val in mean.items():
                drive_mean[(d_, st)] = val

        # Pass 2: per session find drive, test bar, trigger.
        for key, (pos, k) in prefix.items():
            if k < self.drive_bars + 1:
                continue
            mean_d = drive_mean.get((pd.Timestamp(key[0]), key[1]), np.nan)
            if not np.isfinite(mean_d) or key not in drive_vol:
                continue
            st = key[1]
            oo, hh, ll, cc, vv, tt = o[pos], h[pos], lo[pos], c[pos], v[pos], tp[pos]
            if not (
                np.max(hh[: self.drive_bars]) >= (1 + self.drive_min_excursion) * oo[0]
                and drive_vol[key] >= self.drive_volume_multiple * mean_d
            ):
                continue
            cum_v = np.cumsum(vv)
            with np.errstate(divide="ignore", invalid="ignore"):
                vwap = np.cumsum(tt * vv) / cum_v
            touched = np.nonzero(ll[self.drive_bars :] <= vwap[self.drive_bars :])[0]
            if len(touched) == 0:
                continue
            s = int(touched[0]) + self.drive_bars
            if cc[s] < vwap[s] or vv[s] > vv[:s].mean():
                continue
            t = None
            if s + 1 < k and cc[s + 1] > hh[s]:
                t = s + 1
            elif s + 2 < k and cc[s + 2] > hh[s]:
                t = s + 2
            if t is None:
                continue
            high_t = float(np.max(hh[: t + 1]))
            if not high_t >= (1 + self.min_room_to_session_high) * cc[t]:
                continue
            next_open_minute = self.session_starts[st] + (t + 1) * 15
            if next_open_minute > self.session_latest_fill_open[st]:
                continue
            if not (vv[t] > 0 and np.isfinite(high_t) and np.isfinite(ll[s])):
                continue
            row = pos[t]
            sig[row] = 1.0
            sig_h[row] = high_t
            sig_low_s[row] = ll[s]

        dataframe["sig_h"] = sig_h
        dataframe["sig_low_s"] = sig_low_s
        dataframe["sig_flag"] = sig
        dataframe["session_last_bar"] = last_bar
        return dataframe

    # ------------------------------------------------------------------ signals
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["sig_flag"] == 1)
                & dataframe["sig_h"].notna()
                & dataframe["sig_low_s"].notna()
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "vwap_first_pullback")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["session_last_bar"] == 1) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "session_end")
        return dataframe

    # ------------------------------------------------------------------ helpers
    def _signal_row(self, pair, entry_time):
        """Closed signal candle (the one before the fill candle) as (H, low_s, frame)."""
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or len(frame) == 0:
            return None
        sig_time = pd.Timestamp(entry_time).floor("15min") - timedelta(minutes=15)
        rows = frame[frame["date"] == sig_time]
        if len(rows) == 0:
            return None
        row = rows.iloc[-1]
        if not (row["sig_flag"] == 1 and pd.notna(row["sig_h"]) and pd.notna(row["sig_low_s"])):
            return None
        return float(row["sig_h"]), float(row["sig_low_s"]), frame

    def _stop_fraction(self, fill_price, low_s):
        stop_price = min(low_s, 0.99 * fill_price)
        return (fill_price - stop_price) / fill_price

    # ------------------------------------------------------------------ trade hooks
    def confirm_trade_entry(
        self, pair, order_type, amount, rate, time_in_force, current_time, entry_tag, side, **kwargs
    ):
        info = self._signal_row(pair, current_time)
        if info is None:
            return False
        high_t, low_s, _ = info
        if low_s < (1 - self.max_fill_low_distance) * rate:
            return False
        if rate >= high_t:
            return False
        return True

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        info = self._signal_row(pair, trade.open_date_utc)
        if info is None:
            return None
        _, low_s, _ = info
        d = self._stop_fraction(trade.open_rate, low_s)
        stop_price = trade.open_rate * (1 - d)
        # distance relative to current_rate, fixed at d below the entry price
        return min(stop_price / current_rate - 1, -0.0001)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_time - trade.open_date_utc >= timedelta(minutes=15 * self.time_exit_bars):
            return "time_12bars"
        info = self._signal_row(pair, trade.open_date_utc)
        if info is None:
            return None
        high_t, _, frame = info
        if current_rate >= high_t:
            return "tp_session_high"
        closed = frame[
            (frame["date"] >= pd.Timestamp(trade.open_date_utc).floor("15min"))
            & (frame["date"] < pd.Timestamp(current_time).floor("15min"))
        ]
        if len(closed) and closed["high"].max() >= high_t:
            return "tp_session_high"
        return None

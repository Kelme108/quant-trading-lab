"""H-133: late-session up-spike of an 8h UTC session accepted by the next session (15m).

Rule (research/proposals/H-133.json), 15m, UTC, closed bars only, spot, long only:
- SESSIONS: S1 00:00-07:45, S2 08:00-15:45, S3 16:00-23:45 (32 bars each). A session with any of
  its 32 bars missing is incomplete: it cannot be a spike session and is not used for AR.
- SPIKE (at the close of bar 32 of a complete session X): BASE = max high of bars 1-24,
  WH / WL = max high / min low of bars 25-32, C = close of bar 32,
  AR = mean (high - low) of the 10 most recent complete sessions of the same type before X.
  Spike: WH > BASE and WH > WL and C >= BASE + 0.25 AR and (C - WL)/(WH - WL) >= 0.70.
- ACCEPTANCE (session N right after X): bars 1-4 of N exist, none of their closes is below
  MID = (BASE + WH)/2, and the close of bar 4 is above WH. Signal at the close of bar 4,
  buy at the open of bar 5. BASE travels in enter_tag ("ssa:<base>").
- FILL CHECK (confirm_trade_entry): skip if BASE < 0.97 E.
- STOP: SP = min(BASE, 0.99 E), d = (E - SP)/E frozen at the fill (custom_stoploss returns the
  ratio that keeps the absolute stop price); native stoploss -0.03 is only a backstop.
- TAKE-PROFIT: TP = E + 1.5 (E - SP) and TIME EXIT 7 h after the entry, both in custom_exit.
- Warm-up 1000 bars.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

SESSION_HOURS = 8
SESSION_BARS = 32
BAR_MINUTES = 15
BASE_BARS = 24
AR_SESSIONS = 10
MIN_SPIKE_AR_MULT = 0.25
MIN_CLOSE_LOCATION = 0.70
ACCEPTANCE_BARS = 4
FILL_BASE_MULT = 0.97
STOP_ENTRY_MULT = 0.99
TARGET_R_MULTIPLE = 1.5
TIME_EXIT_HOURS = 7
TAG_PREFIX = "ssa:"


class SessionSpikeAcceptance_H133_v1(IStrategy):
    """Late-session up-spike, accepted by the next session's first hour, 15m."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 1000

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        date = pd.to_datetime(dataframe["date"])
        session = date.dt.floor(f"{SESSION_HOURS}h")
        pos = ((date - session) / pd.Timedelta(minutes=BAR_MINUTES)).round()

        work = pd.DataFrame(
            {
                "session": session,
                "pos": pos,
                "high": dataframe["high"].astype(float),
                "low": dataframe["low"].astype(float),
                "close": dataframe["close"].astype(float),
            },
            index=dataframe.index,
        )
        # a bar with undefined prices counts as missing
        work = work.dropna(subset=["high", "low", "close"])

        grouped = work.groupby("session")
        sessions = pd.DataFrame(
            {
                "rows": grouped.size(),
                "positions": grouped["pos"].nunique(),
                "high": grouped["high"].max(),
                "low": grouped["low"].min(),
            }
        )
        base_part = work[work["pos"] < BASE_BARS]
        spike_part = work[work["pos"] >= BASE_BARS]
        last_part = work[work["pos"] == SESSION_BARS - 1]
        sessions["base"] = base_part.groupby("session")["high"].max()
        sessions["wh"] = spike_part.groupby("session")["high"].max()
        sessions["wl"] = spike_part.groupby("session")["low"].min()
        sessions["c"] = last_part.groupby("session")["close"].last()
        sessions["complete"] = (sessions["rows"] == SESSION_BARS) & (
            sessions["positions"] == SESSION_BARS
        )

        # AR: mean range of the 10 most recent complete sessions of the same type (not X itself)
        sessions["range"] = sessions["high"] - sessions["low"]
        complete_range = sessions.loc[sessions["complete"], "range"]
        if len(complete_range):
            ar_complete = complete_range.groupby(complete_range.index.hour).transform(
                lambda s: s.shift(1).rolling(AR_SESSIONS).mean()
            )
            sessions["ar"] = ar_complete.reindex(sessions.index)
        else:
            sessions["ar"] = np.nan

        with np.errstate(divide="ignore", invalid="ignore"):
            location = (sessions["c"] - sessions["wl"]) / (sessions["wh"] - sessions["wl"])
        sessions["spike"] = (
            sessions["complete"]
            & sessions["ar"].notna()
            & (sessions["wh"] > sessions["base"])
            & (sessions["wh"] > sessions["wl"])
            & (sessions["c"] >= sessions["base"] + MIN_SPIKE_AR_MULT * sessions["ar"])
            & (location >= MIN_CLOSE_LOCATION)
        )

        # map the previous session X onto every bar of session N
        previous = pd.Index(session - pd.Timedelta(hours=SESSION_HOURS))
        prev_spike = (
            sessions["spike"].reindex(previous).fillna(False).to_numpy(dtype=bool)
            if n
            else np.zeros(0, dtype=bool)
        )
        base_prev = sessions["base"].reindex(previous).to_numpy(dtype=float)
        wh_prev = sessions["wh"].reindex(previous).to_numpy(dtype=float)
        mid_prev = (base_prev + wh_prev) / 2.0

        dataframe["ssa_prev_spike"] = prev_spike
        dataframe["ssa_base"] = np.where(prev_spike, base_prev, np.nan)
        dataframe["ssa_wh"] = np.where(prev_spike, wh_prev, np.nan)
        dataframe["ssa_mid"] = np.where(prev_spike, mid_prev, np.nan)

        # acceptance: bars 1-4 of N exist (4 consecutive bars ending at bar 4), closes >= MID,
        # close of bar 4 > WH. Looks backwards only.
        close = dataframe["close"].astype(float)
        span = date - date.shift(ACCEPTANCE_BARS - 1)
        consecutive = span == pd.Timedelta(minutes=BAR_MINUTES * (ACCEPTANCE_BARS - 1))
        fourth_bar = (pos == ACCEPTANCE_BARS - 1).to_numpy(dtype=bool)
        min_close = close.rolling(ACCEPTANCE_BARS).min().to_numpy(dtype=float)
        close_arr = close.to_numpy(dtype=float)
        with np.errstate(invalid="ignore"):
            accepted = (
                prev_spike
                & fourth_bar
                & consecutive.to_numpy(dtype=bool)
                & (min_close >= mid_prev)
                & (close_arr > wh_prev)
            )
        dataframe["ssa_signal"] = accepted
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            dataframe["ssa_signal"].fillna(False).astype(bool)
            & dataframe["ssa_base"].notna()
            & dataframe["ssa_wh"].notna()
            & dataframe["ssa_mid"].notna()
            & (dataframe["volume"] > 0)
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
            dataframe.loc[ok, "enter_tag"] = dataframe.loc[ok, "ssa_base"].map(
                lambda value: TAG_PREFIX + repr(float(value))
            )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No exit signals: exits are the stop, the take-profit and the time exit (custom_exit).
        return dataframe

    @staticmethod
    def _base_from_tag(tag):
        if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
            return None
        try:
            value = float(tag[len(TAG_PREFIX):])
        except ValueError:
            return None
        return value if np.isfinite(value) and value > 0 else None

    @staticmethod
    def _stop_price(base: float, entry: float) -> float:
        return min(base, STOP_ENTRY_MULT * entry)

    def confirm_trade_entry(
        self, pair: str, order_type: str, amount: float, rate: float,
        time_in_force: str, current_time, entry_tag, side: str, **kwargs
    ) -> bool:
        base = self._base_from_tag(entry_tag)
        if base is None or not rate or rate <= 0:
            return False
        return not (base < FILL_BASE_MULT * rate)

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float,
        current_profit: float, after_fill: bool = False, **kwargs
    ):
        base = self._base_from_tag(trade.enter_tag)
        entry = trade.open_rate
        if base is None or not entry or not current_rate:
            return None  # fall back to the native backstop
        stop_price = self._stop_price(base, entry)
        ratio = stop_price / current_rate - 1.0
        if ratio >= 0:
            # price already at or below the frozen stop: stop out as soon as possible
            return -1e-6
        return ratio

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        base = self._base_from_tag(trade.enter_tag)
        entry = trade.open_rate
        if base is not None and entry and current_rate:
            stop_price = self._stop_price(base, entry)
            target = entry + TARGET_R_MULTIPLE * (entry - stop_price)
            if current_rate >= target:
                return "take_profit_1p5R"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_7h"
        return None

"""H-071: volatility-scaled 24-hour momentum on 1h with a ratcheting 2.5-ATR trail and a 24-hour time exit.

Rule (closed 1h bars; signal at the close of bar t, filled at the open of bar t+1):
- M(t) = close(t) / close(t-24) - 1.
- S(t) = sample std (ddof=1) of M(t-720) .. M(t-1) (rolling 720 std of M, shifted one bar).
- ATR(t) = Wilder ATR(14): true range smoothed with alpha = 1/14.
- ENTRY when M(t) >= 1.5 * S(t), M(t) >= 0.02 and close(t) > close(t-1). One position per pair is enforced by
  Freqtrade; the 6-candle cooldown after any exit is the CooldownPeriod protection.
- TRAILING EXIT (custom_exit, close-based): with e the fill bar, P the fill price and t = e-1 the signal bar,
  T = P - 2.5 * ATR(t). At the close of every bar j >= e: if close(j) < T, exit at the open of j+1; otherwise
  T = max(T, close(j) - 2.5 * ATR(j)).
- TIME EXIT: at the close of bar e+23 (24th bar of the trade), exit at the open of e+24.
- STOP: native 8% stop (intrabar). No ROI table, no take-profit.

Contract detail: an exit is never raised on a zero-volume candle; such a candle is skipped for the exit test
(the trail still ratchets on it) and the exit, if due, is raised on the next candle with volume.
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

MOM_BARS = 24
VOL_WINDOW = 720
SIGMA_THRESHOLD = 1.5
MIN_MOMENTUM = 0.02
ATR_PERIOD = 14
ATR_MULT = 2.5
TIME_EXIT_BARS = 24
COOLDOWN_BARS = 6
BAR = timedelta(hours=1)


def wilder_atr(dataframe: DataFrame, period: int) -> pd.Series:
    """Wilder ATR: true range smoothed with alpha = 1/period. Causal; NaN until `period` true ranges exist."""
    prev_close = dataframe["close"].shift(1)
    true_range = pd.concat(
        [
            dataframe["high"] - dataframe["low"],
            (dataframe["high"] - prev_close).abs(),
            (dataframe["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1, skipna=False)
    return true_range.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def trail_exit_reason(
    dataframe: DataFrame, open_date: datetime, open_rate: float, now: datetime
) -> Optional[str]:
    """Exit reason for a trade filled at `open_date` (open of bar e) at `open_rate`, evaluated at `now`.

    Uses only candles that have closed by `now` (date + 1h <= now). Returns None while no exit is due.
    """
    dates = pd.to_datetime(dataframe["date"])
    closed = dataframe.loc[(dates + BAR) <= now]
    closed_dates = pd.to_datetime(closed["date"])

    signal_rows = closed.loc[closed_dates == open_date - BAR]
    if signal_rows.empty:
        return None
    signal_atr = float(signal_rows["atr"].iloc[-1])
    if np.isnan(signal_atr):
        return None

    trade_rows = closed.loc[closed_dates >= open_date]
    closes = trade_rows["close"].to_numpy(dtype=float)
    atrs = trade_rows["atr"].to_numpy(dtype=float)
    volumes = trade_rows["volume"].to_numpy(dtype=float)

    trail = open_rate - ATR_MULT * signal_atr
    for k in range(len(closes)):
        has_volume = volumes[k] > 0
        if has_volume and closes[k] < trail:
            return "atr_trail"
        if has_volume and k >= TIME_EXIT_BARS - 1:
            return "time_exit_24h"
        if not np.isnan(atrs[k]):
            trail = max(trail, closes[k] - ATR_MULT * atrs[k])
    return None


class ATRTrailMomentum_H071_v1(IStrategy):
    """24h momentum beyond 1.5 sigma of its own 720-bar dispersion, ratcheting 2.5-ATR trail, 24h cap."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.08
    startup_candle_count = 1000

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["mom"] = dataframe["close"] / dataframe["close"].shift(MOM_BARS) - 1.0
        dataframe["mom_std"] = dataframe["mom"].rolling(VOL_WINDOW).std(ddof=1).shift(1)
        dataframe["atr"] = wilder_atr(dataframe, ATR_PERIOD)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["mom"].notna()
            & dataframe["mom_std"].notna()
            & dataframe["atr"].notna()
            & dataframe["close"].shift(1).notna()
        )
        condition = (
            defined
            & (dataframe["mom"] >= SIGMA_THRESHOLD * dataframe["mom_std"])
            & (dataframe["mom"] >= MIN_MOMENTUM)
            & (dataframe["close"] > dataframe["close"].shift(1))
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (1, "vol_scaled_mom24")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits are path-dependent (trail from the fill price, 24-bar cap) and handled in custom_exit.
        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        return trail_exit_reason(dataframe, trade.open_date_utc, float(trade.open_rate), current_time)

"""H-078: low-volume cross-sectional loser reversal, 1h, spot long only.

Closed candles only; signal at the close of bar t, order at the open of t+1.

Universe: BTC, ETH, BNB, XRP, ADA, LTC, LINK, DOGE, SOL against USDT. Every
pair other than the traded pair X is loaded as an informative 1h pair and
aligned on the same candle timestamp.

Per pair at bar t (all lookbacks are by clock time, backwards only):
- r4(t) = close(t) / close(t-4h) - 1
- V4(t) = sum of volume over bars t-3h..t (all 4 bars required)
- VN(t) = mean of V4(t - 24h*k), k = 1..14 (all 14 terms required)

Cross-section: pairs with a defined r4(t). M(t) = median of their r4.
No signal if fewer than 5 pairs count or X does not count.

Entry (all): r4_X is the lowest of the counting pairs (ties allowed),
r4_X <= -0.02, r4_X <= M - 0.015, V4_X <= 1.0 * VN_X with VN_X > 0.

Exit, first of:
- target: close of a bar u >= e (fill bar) with close(u) >= P = close_X(t-4h)
- time: at the close of bar e+11 (filled at the open of e+12)
- stop: native 4% stoploss
Cooldown: 4 candles after any exit.
"""

from datetime import timedelta
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame
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

RETURN_LOOKBACK = 4
VOLUME_WINDOW = 4
VOLUME_NORM_DAYS = 14
VOLUME_NORM_STEP = 24
MIN_ABS_DROP = -0.02
MIN_GAP_BELOW_MEDIAN = 0.015
VOLUME_MULTIPLE_MAX = 1.0
MIN_PAIRS = 5
TIME_EXIT_LAST_BAR = 11  # exit signal at the close of bar e+11
BAR = pd.Timedelta(hours=1)


def _hourly(frame: DataFrame, column: str) -> pd.Series:
    """Series indexed by candle date on a complete hourly grid (gaps -> NaN)."""
    data = frame[["date", column]].drop_duplicates("date").sort_values("date")
    series = data.set_index("date")[column].astype(float)
    if len(series) == 0:
        return series
    return series.asfreq("1h")


def _r4(frame: DataFrame) -> pd.Series:
    close = _hourly(frame, "close")
    return close / close.shift(RETURN_LOOKBACK) - 1.0


class CrossSectionalLowVolReversal_H078_v1(IStrategy):
    """Buy the cross-sectional 4h loser when its drop is on normal/thin volume."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    trailing_stop = False
    startup_candle_count = 400

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 4}]

    def informative_pairs(self):
        return [(pair, "1h") for pair in PAIRS]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get("pair", "")
        dates = dataframe["date"]

        # Own pair: return, pre-drop close, volume windows.
        close_h = _hourly(dataframe, "close")
        volume_h = _hourly(dataframe, "volume")
        r4_own = close_h / close_h.shift(RETURN_LOOKBACK) - 1.0
        pre_drop = close_h.shift(RETURN_LOOKBACK)
        v4 = volume_h.rolling(VOLUME_WINDOW).sum()
        lagged = [
            v4.shift(VOLUME_NORM_STEP * k) for k in range(1, VOLUME_NORM_DAYS + 1)
        ]
        lagged_frame = pd.concat(lagged, axis=1)
        vn = lagged_frame.mean(axis=1, skipna=True)
        vn = vn.where(lagged_frame.notna().all(axis=1))

        dataframe["r4"] = dates.map(r4_own).astype(float)
        dataframe["pre_drop_close"] = dates.map(pre_drop).astype(float)
        dataframe["v4"] = dates.map(v4).astype(float)
        dataframe["vn"] = dates.map(vn).astype(float)

        # Cross-section: own r4 plus every other universe pair, aligned on date.
        columns = {"own": dataframe["r4"]}
        for other in PAIRS:
            if other == pair:
                continue
            other_df = self.dp.get_pair_dataframe(pair=other, timeframe="1h")
            if other_df is None or len(other_df) == 0:
                columns[other] = pd.Series(np.nan, index=dataframe.index)
                continue
            columns[other] = dates.map(_r4(other_df)).astype(float)
        cross = pd.DataFrame(columns, index=dataframe.index)
        cross = cross.replace([np.inf, -np.inf], np.nan)

        dataframe["xs_count"] = cross.notna().sum(axis=1)
        dataframe["xs_median"] = cross.median(axis=1, skipna=True)
        dataframe["xs_min"] = cross.min(axis=1, skipna=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        r4 = dataframe["r4"]
        dataframe.loc[
            (
                r4.notna()
                & dataframe["xs_median"].notna()
                & dataframe["xs_min"].notna()
                & dataframe["v4"].notna()
                & dataframe["vn"].notna()
                & dataframe["pre_drop_close"].notna()
                & (dataframe["xs_count"] >= MIN_PAIRS)
                & (r4 <= dataframe["xs_min"])
                & (r4 <= MIN_ABS_DROP)
                & (r4 <= dataframe["xs_median"] - MIN_GAP_BELOW_MEDIAN)
                & (dataframe["vn"] > 0)
                & (dataframe["v4"] <= VOLUME_MULTIPLE_MAX * dataframe["vn"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "xs_lowvol_loser")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits depend on the trade's own entry (P and bars held): custom_exit.
        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade,
        current_time,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> Optional[str]:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        last = dataframe.iloc[-1]  # last closed candle u
        if not (last["volume"] > 0) or pd.isna(last["close"]):
            return None

        fill_bar = pd.Timestamp(trade.open_date_utc).floor("1h")
        signal_bar = fill_bar - timedelta(hours=1)
        last_date = pd.Timestamp(last["date"])
        bars_held = int((last_date - fill_bar) / BAR)
        if bars_held < 0:
            return None

        signal_rows = dataframe.loc[dataframe["date"] == signal_bar, "pre_drop_close"]
        if len(signal_rows) > 0:
            target = float(signal_rows.iloc[-1])
            if not np.isnan(target) and float(last["close"]) >= target:
                return "target_pre_drop"

        if bars_held >= TIME_EXIT_LAST_BAR:
            return "time_12h"
        return None

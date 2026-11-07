"""H-072: idiosyncratic 6-hour drop versus a flat reference, beta-adjusted residual reversal, 1h.

Closed candles only; the signal at the close of bar t fills at the open of bar t+1. Spot, long only.

Reference B: BTC/USDT for every pair, ETH/USDT for BTC/USDT itself. B is an informative 1h pair
aligned on the same candle timestamp (an exact date join, which is what merge_informative_pair
does for the same timeframe); a missing B bar gives NaN and so no signal.

x = ln(C/C[-1]), b = ln(CB/CB[-1]).
beta(t)  = cov(x, b) / var(b) over bars t-720..t-1 (excludes t); var(b) = 0 or NaN -> no signal.
rB6(t)   = ln(CB(t)/CB(t-6)).
e6(t)    = ln(C(t)/C(t-6)) - beta(t) * rB6(t)   (each e6(i) uses its own beta(i)).
s(t)     = std (ddof=1) of e6 over bars t-720..t-1 (excludes t).

Entry: e6 <= -2.5 * s, e6 <= -0.02, |rB6| <= 0.01, all defined, volume > 0.
Exit (custom_exit, checked at the close of every bar from the entry bar on):
  (a) ln(C(u)/P0) - beta_e * ln(CB(u)/B0) >= 0.6 * E, with beta_e, E = |e6|, B0 = CB taken at
      the signal bar and P0 the entry fill price;
  (b) time: at the close of bar e+11 when the entry filled at the open of bar e.
Stop: fixed 4% native stoploss. No cooldown.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy

BETA_WINDOW = 720
HORIZON = 6
STD_WINDOW = 720
SIGMA_MULT = 2.5
MIN_DROP = 0.02
FLAT_BAND = 0.01
GAP_FRACTION = 0.6
TIME_EXIT_BARS = 12
BAR = timedelta(hours=1)


def reference_pair_for(pair: str) -> str:
    return "ETH/USDT" if pair == "BTC/USDT" else "BTC/USDT"


def residual_indicators(close: pd.Series, ref_close: pd.Series) -> DataFrame:
    """Backward-looking residual indicators; `ref_close` is aligned row by row with `close`."""
    close = close.astype(float)
    ref_close = ref_close.astype(float)
    x = np.log(close / close.shift(1))
    b = np.log(ref_close / ref_close.shift(1))
    x = x.replace([np.inf, -np.inf], np.nan)
    b = b.replace([np.inf, -np.inf], np.nan)

    cov_xb = x.rolling(BETA_WINDOW).cov(b)
    var_b = b.rolling(BETA_WINDOW).var()
    beta_raw = cov_xb / var_b.where(var_b > 0)
    beta_raw = beta_raw.where(x.rolling(BETA_WINDOW).count() == BETA_WINDOW)
    beta = beta_raw.shift(1)  # window t-720..t-1

    r6 = np.log(close / close.shift(HORIZON))
    rb6 = np.log(ref_close / ref_close.shift(HORIZON))
    e6 = (r6 - beta * rb6).replace([np.inf, -np.inf], np.nan)
    s = e6.rolling(STD_WINDOW).std(ddof=1).shift(1)  # window t-720..t-1

    return DataFrame(
        {"ref_close": ref_close, "beta": beta, "rb6": rb6, "e6": e6, "e6_std": s},
        index=close.index,
    )


class IdiosyncraticResidualReversal_H072_v1(IStrategy):
    """Buy a large beta-adjusted residual drop while the reference is flat; exit on 60% gap closure or 12h."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    use_exit_signal = True
    startup_candle_count = 1500

    def informative_pairs(self):
        return [("BTC/USDT", "1h"), ("ETH/USDT", "1h")]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ref_pair = reference_pair_for(metadata.get("pair", ""))
        ref_df = self.dp.get_pair_dataframe(pair=ref_pair, timeframe="1h")
        if ref_df is None or len(ref_df) == 0:
            ref_close = pd.Series(np.nan, index=dataframe.index)
        else:
            series = ref_df.drop_duplicates("date").set_index("date")["close"]
            ref_close = dataframe["date"].map(series).astype(float)
        ind = residual_indicators(dataframe["close"], ref_close)
        for column in ind.columns:
            dataframe[column] = ind[column]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        e6 = dataframe["e6"]
        s = dataframe["e6_std"]
        rb6 = dataframe["rb6"]
        dataframe.loc[
            (
                e6.notna()
                & s.notna()
                & rb6.notna()
                & dataframe["beta"].notna()
                & dataframe["ref_close"].notna()
                & (e6 <= -SIGMA_MULT * s)
                & (e6 <= -MIN_DROP)
                & (rb6.abs() <= FLAT_BAND)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "residual_drop")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Both exits depend on the open trade and are evaluated in custom_exit.
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        last = dataframe.iloc[-1]
        open_date = pd.Timestamp(trade.open_date_utc)
        candle_date = pd.Timestamp(last["date"])
        if candle_date.tzinfo is None and open_date.tzinfo is not None:
            candle_date = candle_date.tz_localize(open_date.tzinfo)
        elif candle_date.tzinfo is not None and open_date.tzinfo is None:
            open_date = open_date.tz_localize(candle_date.tzinfo)
        if candle_date < open_date:
            return None
        if not (last["volume"] > 0) or pd.isna(last["close"]) or pd.isna(last["ref_close"]):
            return None

        # (a) residual gap closure, using the signal bar (one bar before the entry bar).
        dates = pd.to_datetime(dataframe["date"])
        if dates.dt.tz is None and open_date.tzinfo is not None:
            dates = dates.dt.tz_localize(open_date.tzinfo)
        signal_rows = dataframe[(dates == open_date - BAR).to_numpy()]
        if len(signal_rows) > 0:
            sig = signal_rows.iloc[-1]
            beta_e = sig["beta"]
            e6_e = sig["e6"]
            b0 = sig["ref_close"]
            p0 = trade.open_rate
            if (
                pd.notna(beta_e) and pd.notna(e6_e) and pd.notna(b0) and b0 > 0
                and p0 is not None and p0 > 0 and last["close"] > 0 and last["ref_close"] > 0
            ):
                gap = np.log(last["close"] / p0) - beta_e * np.log(last["ref_close"] / b0)
                if gap >= GAP_FRACTION * abs(e6_e):
                    return "residual_gap_closed"

        # (b) time exit at the close of bar e+11.
        if candle_date >= open_date + (TIME_EXIT_BARS - 1) * BAR:
            return "time_12h"
        return None

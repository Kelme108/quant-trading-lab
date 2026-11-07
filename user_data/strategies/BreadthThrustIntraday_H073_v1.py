"""H-073: nine-pair hourly breadth thrust, 1h, long only.

Closed candles only; the signal at the close of bar t fills at the open of bar t+1. Spot, long only.

Universe: BTC, ETH, BNB, XRP, ADA, LTC, LINK, DOGE, SOL against USDT, loaded as informative 1h
pairs and aligned on exact candle timestamps.

BREADTH at bar t:
  A(t) = number of pairs with close(t) > close(t-1); D(t) = number with close(t) < close(t-1).
  Pairs with close(t) = close(t-1), or with no candle at t or at t-1 (exact timestamp t - 1h),
  count in neither. B(t) = A/(A+D), or 0.5 if A+D = 0.
  E = EMA of B, span 10, adjust=False (recursive). Breadth is computed on the union of all
  candle timestamps, independent of the traded pair, then mapped onto the traded pair's candles.
  THRUST(t) = E(t) > 0.615 AND min(E(t-10..t-1)) < 0.40.

ENTRY on pair X at the close of bar t: THRUST(t) and not THRUST(t-1) (rising edge, both defined),
  close_X(t) > close_X(t-10) (exact timestamp t - 10h), volume > 0.
  One position per pair is Freqtrade's own behaviour.

EXIT (custom_exit, read on the last closed candle, filled at the next open), first of:
  (a) TIME: at the close of bar t+24, i.e. the candle dated fill + 23h (fill = open of t+1);
  (c) BREADTH COLLAPSE: at the close of any bar after the fill bar with E < 0.40.
  (b) STOP: native 3% stoploss, intrabar.
No take-profit (minimal_roi 100), no trailing stop, no cooldown.
Warm-up: the proposal sizes it at 200 bars for EMA convergence; 400 is used (lab minimum for EMAs).
"""

from datetime import timedelta

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
EMA_SPAN = 10
THRUST_HIGH = 0.615
THRUST_LOW = 0.40
THRUST_WINDOW = 10
PARTICIPATION_LOOKBACK = 10
TIME_EXIT_BARS = 24
COLLAPSE_LEVEL = 0.40
BAR = timedelta(hours=1)


def _clean_close(frame) -> pd.Series:
    """Close prices indexed by candle date, one row per date."""
    if frame is None or len(frame) == 0:
        return pd.Series(dtype=float)
    frame = frame.drop_duplicates("date", keep="last")
    return pd.Series(frame["close"].astype(float).to_numpy(), index=pd.DatetimeIndex(frame["date"]))


def breadth_indicators(closes: list, extra_dates) -> DataFrame:
    """Breadth B, its EMA E and the thrust flag on the union of all candle dates (backward only)."""
    index = pd.DatetimeIndex(extra_dates)
    for series in closes:
        index = index.union(series.index)
    index = index.drop_duplicates().sort_values()

    advances = pd.Series(0.0, index=index)
    declines = pd.Series(0.0, index=index)
    for series in closes:
        if len(series) == 0:
            continue
        current = pd.Series(series.reindex(index).to_numpy(), index=index)
        previous = pd.Series(series.reindex(index - BAR).to_numpy(), index=index)
        advances += (current > previous).astype(float)
        declines += (current < previous).astype(float)

    total = advances + declines
    breadth = (advances / total.where(total > 0)).fillna(0.5)
    ema = breadth.ewm(span=EMA_SPAN, adjust=False).mean()
    prior_min = ema.shift(1).rolling(THRUST_WINDOW).min()
    thrust = ((ema > THRUST_HIGH) & (prior_min < THRUST_LOW)).astype(float)
    thrust = thrust.where(prior_min.notna())
    thrust_prev = thrust.shift(1)
    return DataFrame(
        {
            "breadth": breadth,
            "breadth_ema": ema,
            "breadth_ema_prior_min": prior_min,
            "thrust": thrust,
            "thrust_prev": thrust_prev,
        },
        index=index,
    )


class BreadthThrustIntraday_H073_v1(IStrategy):
    """Buy the rising edge of an hourly nine-pair breadth thrust; 24h time exit or breadth collapse."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    trailing_stop = False
    use_exit_signal = True
    # Proposal asks for >= 200 bars of EMA warm-up; the lab check requires 400 for recursive indicators.
    startup_candle_count = 400

    def informative_pairs(self):
        return [(pair, "1h") for pair in PAIRS]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        closes = []
        for pair in PAIRS:
            closes.append(_clean_close(self.dp.get_pair_dataframe(pair=pair, timeframe="1h")))

        dates = pd.DatetimeIndex(dataframe["date"])
        ind = breadth_indicators(closes, dates)
        for column in ind.columns:
            dataframe[column] = ind[column].reindex(dates).to_numpy()

        own = _clean_close(dataframe)
        lookback = timedelta(hours=PARTICIPATION_LOOKBACK)
        dataframe["close_lookback"] = own.reindex(dates - lookback).to_numpy()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["thrust"].notna()
                & dataframe["thrust_prev"].notna()
                & dataframe["close"].notna()
                & dataframe["close_lookback"].notna()
                & (dataframe["thrust"] == 1.0)
                & (dataframe["thrust_prev"] == 0.0)
                & (dataframe["close"] > dataframe["close_lookback"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "breadth_thrust")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Both exits depend on the trade's fill time and are evaluated in custom_exit.
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
        if not (last["volume"] > 0) or pd.isna(last["close"]):
            return None

        # (a) time exit at the close of bar t+24 = the candle dated fill + 23h.
        if candle_date >= open_date + (TIME_EXIT_BARS - 1) * BAR:
            return "time_24h"
        # (c) breadth collapse at the close of any bar after the fill bar.
        ema = last["breadth_ema"]
        if candle_date > open_date and pd.notna(ema) and ema < COLLAPSE_LEVEL:
            return "breadth_collapse"
        return None

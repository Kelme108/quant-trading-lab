"""H-144: idiosyncratic alt surge while BTC is flat, volume-backed continuation (15m).

Rule (research/proposals/H-144.json), 15m, UTC, closed candles only, spot, long only:
- REFERENCE: BTC/USDT 15m is loaded as an informative pair of the same timeframe and joined on the
  identical candle open time. BTC/USDT itself is never traded (no signal on that pair).
- r16(i,t) = close(i,t) / close(i,t-16) - 1, where t-16 is the candle exactly 240 minutes earlier
  (time based, so a missing bar gives NaN). r16(BTC,t) likewise. resid = r16(i,t) - r16(BTC,t).
- MV(t) = mean volume of the 96 bars t-96..t-1 (bar t excluded; any missing bar gives NaN).
- CL(t) = (close - low) / (high - low); high == low gives no signal.
- ENTRY at the close of bar t: resid >= 0.020, abs(r16 BTC) <= 0.0075, volume >= 1.5 x MV,
  CL >= 0.70. Fills at the next open. One position per pair (engine), cooldown of 8 candles after
  an exit (CooldownPeriod protection).
- EXITS: take-profit +2.5% and time exit 12 h (48 bars, sold at the open of bar e+48) in
  custom_exit; native intrabar stop-loss -1.25% (stoploss attribute, no trailing).
- Warm-up 120 bars.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

REFERENCE_PAIR = "BTC/USDT"
BAR_MINUTES = 15
RETURN_LOOKBACK_BARS = 16
MIN_RESIDUAL_RETURN = 0.020
MAX_ABS_BTC_RETURN = 0.0075
VOLUME_MEAN_BARS = 96
VOLUME_MULTIPLE = 1.5
MIN_CLOSE_LOCATION = 0.70
COOLDOWN_BARS = 8
TAKE_PROFIT = 0.025
TIME_EXIT_HOURS = 12  # 48 bars of 15m


def _regular_grid(series: pd.Series) -> pd.Series:
    """Put a date-indexed series on a complete 15m grid (missing bars become NaN)."""
    series = series[~series.index.duplicated(keep="first")].sort_index()
    if series.empty:
        return series
    grid = pd.date_range(series.index.min(), series.index.max(), freq=f"{BAR_MINUTES}min")
    return series.reindex(grid)


class IdiosyncraticSurgeMomentum_H144_v1(IStrategy):
    """Alt up >= 2% more than BTC over 4h while BTC is flat, on a volume burst and a strong close."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.0125
    use_custom_stoploss = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 120

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def informative_pairs(self):
        return [(REFERENCE_PAIR, self.timeframe)]

    @staticmethod
    def _r16_on_dates(frame: DataFrame, dates: pd.Series) -> np.ndarray:
        """16-bar (240 min) close return of `frame`, evaluated on `dates` (backward looking only)."""
        close = pd.Series(
            frame["close"].to_numpy(dtype=float), index=pd.to_datetime(frame["date"])
        )
        grid = _regular_grid(close)
        ret = grid / grid.shift(RETURN_LOOKBACK_BARS) - 1.0
        ret = ret.replace([np.inf, -np.inf], np.nan)
        return ret.reindex(pd.DatetimeIndex(dates)).to_numpy(dtype=float)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        nan = np.full(n, np.nan)
        dates = pd.to_datetime(dataframe["date"])
        pair = metadata.get("pair", "") if metadata else ""

        if n == 0:
            dataframe["r16"] = nan
            dataframe["btc_r16"] = nan
            dataframe["resid"] = nan
            dataframe["vmean"] = nan
            dataframe["close_loc"] = nan
            return dataframe

        # own 4h return and 24h mean volume (bar t excluded), both on a complete 15m grid
        dataframe["r16"] = self._r16_on_dates(dataframe, dates)

        volume = pd.Series(dataframe["volume"].to_numpy(dtype=float), index=pd.DatetimeIndex(dates))
        volume_grid = _regular_grid(volume)
        vmean = volume_grid.shift(1).rolling(VOLUME_MEAN_BARS).mean()
        dataframe["vmean"] = vmean.reindex(pd.DatetimeIndex(dates)).to_numpy(dtype=float)

        # BTC reference: same timeframe, joined on the identical open time
        btc_r16 = nan
        if pair != REFERENCE_PAIR:
            btc = self.dp.get_pair_dataframe(pair=REFERENCE_PAIR, timeframe=self.timeframe)
            if btc is not None and len(btc) > 0:
                btc_r16 = self._r16_on_dates(btc, dates)
        dataframe["btc_r16"] = btc_r16
        dataframe["resid"] = dataframe["r16"] - dataframe["btc_r16"]

        span = dataframe["high"] - dataframe["low"]
        dataframe["close_loc"] = ((dataframe["close"] - dataframe["low"]) / span).where(span > 0)
        dataframe["close_loc"] = dataframe["close_loc"].replace([np.inf, -np.inf], np.nan)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get("pair", "") if metadata else ""
        if pair == REFERENCE_PAIR:
            return dataframe
        ok = (
            dataframe["resid"].notna()
            & dataframe["btc_r16"].notna()
            & dataframe["vmean"].notna()
            & dataframe["close_loc"].notna()
            & (dataframe["volume"] > 0)
            & (dataframe["resid"] >= MIN_RESIDUAL_RETURN)
            & (dataframe["btc_r16"].abs() <= MAX_ABS_BTC_RETURN)
            & (dataframe["volume"] >= VOLUME_MULTIPLE * dataframe["vmean"])
            & (dataframe["close_loc"] >= MIN_CLOSE_LOCATION)
        )
        if ok.any():
            dataframe.loc[ok, ["enter_long", "enter_tag"]] = (1, "idio_surge")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No exit signals: exits are the stop, the take-profit and the time exit (custom_exit).
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        if current_profit >= TAKE_PROFIT:
            return "take_profit_2_5pct"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None

"""H-051: high-volume 08-16 UTC session surge carried to the 23:00 UTC close (intraday momentum).

Closed 1h candles, UTC clock. Freqtrade dates a candle by its open time, so the "15:00 bar" is the row dated
15:00 (covering 15:00-16:00); a signal on it fills at the 16:00 open.

At the close of the 15:00 UTC bar of day d:
  S      = close(15:00) / open(08:00) - 1
  SV     = sum of volume of the 8 session bars 08:00..15:00
  VrefS  = mean of SV over calendar days d-20..d-1 (all 20 must exist, day d excluded)
  SH, SL = highest high / lowest low of the 8 session bars
  P      = (close(15:00) - SL) / (SH - SL), no signal if SH == SL
  SMA200 = mean of the last 200 1h closes ending at the 15:00 bar
ENTRY when S >= 0.015, SV >= 1.5 * VrefS, close > SMA200 and P >= 0.75. No signal if a session bar is missing.
EXIT at the close of the 22:00 UTC bar (sell at the 23:00 open), regardless of price.
STOP: fixed 1.5% below entry, the engine's intrabar stoploss. No take-profit, no cooldown.
"""

import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

SESSION_LAST_BAR_HOUR = 15
SESSION_BARS = 8
SESSION_RETURN_MIN = 0.015
VOLUME_MULTIPLE = 1.5
VOLUME_REF_DAYS = 20
CLOSE_LOCATION_MIN = 0.75
TREND_SMA_BARS = 200
EXIT_SIGNAL_BAR_HOUR = 22


class HighVolumeSessionMomentum_H051_v1(IStrategy):
    """Buy a high-volume 08-16 UTC surge that closed near its high; sell at the 23:00 UTC open."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.015
    startup_candle_count = 500

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        hour = date.dt.hour
        day = date.dt.floor("D")

        # All 8 session bars present: the bar 7 rows back opened exactly 7 hours earlier (08:00).
        complete = (date - date.shift(SESSION_BARS - 1)) == pd.Timedelta(hours=SESSION_BARS - 1)
        session_close = (hour == SESSION_LAST_BAR_HOUR) & complete

        session_open = dataframe["open"].shift(SESSION_BARS - 1)
        sv = dataframe["volume"].rolling(SESSION_BARS).sum()
        sh = dataframe["high"].rolling(SESSION_BARS).max()
        sl = dataframe["low"].rolling(SESSION_BARS).min()
        rng = sh - sl

        dataframe["session_close"] = session_close.astype(int)
        dataframe["session_ret"] = (dataframe["close"] / session_open - 1.0).where(session_close)
        dataframe["session_vol"] = sv.where(session_close)
        dataframe["close_loc"] = ((dataframe["close"] - sl) / rng.where(rng > 0)).where(session_close)
        dataframe["sma200"] = dataframe["close"].rolling(TREND_SMA_BARS).mean()

        # Mean session volume of the previous 20 calendar days (d-20..d-1); NaN unless all 20 exist.
        daily_sv = pd.Series(sv[session_close].to_numpy(), index=pd.DatetimeIndex(day[session_close]))
        if len(daily_sv) > 0:
            calendar = pd.date_range(daily_sv.index.min(), daily_sv.index.max(), freq="D")
            vref_daily = daily_sv.reindex(calendar).shift(1).rolling(VOLUME_REF_DAYS).mean()
            dataframe["vol_ref"] = day.map(vref_daily).astype(float).where(session_close)
        else:
            dataframe["vol_ref"] = float("nan")
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            (dataframe["session_close"] == 1)
            & (dataframe["session_ret"] >= SESSION_RETURN_MIN)
            & (dataframe["session_vol"] >= VOLUME_MULTIPLE * dataframe["vol_ref"])
            & (dataframe["close"] > dataframe["sma200"])
            & (dataframe["close_loc"] >= CLOSE_LOCATION_MIN)
            & dataframe["vol_ref"].notna()
            & dataframe["sma200"].notna()
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[ok, ["enter_long", "enter_tag"]] = (1, "session_surge")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = pd.to_datetime(dataframe["date"], utc=True).dt.hour
        exit_bar = (hour == EXIT_SIGNAL_BAR_HOUR) & (dataframe["volume"] > 0)
        dataframe.loc[exit_bar, ["exit_long", "exit_tag"]] = (1, "time_exit_23utc")
        return dataframe

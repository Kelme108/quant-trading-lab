"""H-088: Elder Triple Screen intraday on 1h with a 4h tide.

Closed candles only. Spot long only.
- Tide (4h, built from completed 1h bars in UTC blocks 00,04,..,20; visible at
  the 1h row whose hour % 4 == 3, i.e. once its last 1h bar has closed):
  EMA13 rising AND MACD(12,26,9) histogram rising.
- Setup bar s: tide up at s and FI2(s) < 0 (FI = (close-close[-1])*volume, EMA2).
- Trigger at s+1: close(s+1) > high(s) and tide up at s+1. Fill at next open.
- Stop level L = min(low(s), low(s+1)); entries with (P-L)/P < 0.004 are
  skipped in confirm_trade_entry. Stop is fixed at L (custom_stoploss).
- Exits: stop at L, take-profit P + 2R (custom_exit), tide turned down
  (exit_long), time exit 12 hours after entry (custom_exit).
"""

from datetime import timedelta

import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class ElderTripleScreen_H088_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    use_custom_stoploss = True
    startup_candle_count = 1000

    min_risk_frac = 0.004
    target_r_multiple = 2.0
    time_exit_hours = 12

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = dataframe["date"].dt.hour
        complete = (hour % 4) == 3
        close4 = dataframe["close"][complete]
        ema13 = close4.ewm(span=13, adjust=False).mean()
        macd = (
            close4.ewm(span=12, adjust=False).mean()
            - close4.ewm(span=26, adjust=False).mean()
        )
        hist = macd - macd.ewm(span=9, adjust=False).mean()
        d_ema = ema13.diff()
        d_hist = hist.diff()
        valid = d_ema.notna() & d_hist.notna()
        up = ((d_ema > 0) & (d_hist > 0)).astype(float).where(valid)
        down = (d_ema < 0).astype(float).where(d_ema.notna())
        dataframe["tide_up"] = up.reindex(dataframe.index).ffill()
        dataframe["tide_down"] = down.reindex(dataframe.index).ffill()

        force = (dataframe["close"] - dataframe["close"].shift(1)) * dataframe["volume"]
        dataframe["fi2"] = force.ewm(span=2, adjust=False).mean()

        dataframe["setup_high"] = dataframe["high"].shift(1)
        dataframe["stop_level"] = pd.concat(
            [dataframe["low"], dataframe["low"].shift(1)], axis=1
        ).min(axis=1, skipna=False)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        setup = (dataframe["tide_up"].shift(1) == 1) & (dataframe["fi2"].shift(1) < 0)
        dataframe.loc[
            (
                setup
                & (dataframe["tide_up"] == 1)
                & dataframe["setup_high"].notna()
                & dataframe["stop_level"].notna()
                & (dataframe["close"] > dataframe["setup_high"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "triple_screen")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["tide_down"] == 1) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "tide_down")
        return dataframe

    def _signal_stop_level(self, pair, entry_time):
        """Stop level stored on the signal candle (one 1h bar before the fill)."""
        if self.dp is None:
            return None
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or len(frame) == 0:
            return None
        signal_date = entry_time - timedelta(hours=1)
        rows = frame.loc[frame["date"] == signal_date]
        if len(rows) == 0:
            return None
        level = rows["stop_level"].iloc[-1]
        return None if pd.isna(level) else float(level)

    def confirm_trade_entry(
        self, pair, order_type, amount, rate, time_in_force, current_time, entry_tag, side, **kwargs
    ):
        if self.dp is None:
            return True
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or len(frame) == 0:
            return False
        level = frame["stop_level"].iloc[-1]
        if pd.isna(level) or rate <= 0:
            return False
        return (rate - float(level)) / rate >= self.min_risk_frac

    def custom_stoploss(
        self, pair, trade, current_time, current_rate, current_profit, **kwargs
    ):
        level = self._signal_stop_level(pair, trade.open_date_utc)
        if level is None or current_rate <= 0:
            return self.stoploss
        if level >= current_rate:
            return -0.0001
        return max(level / current_rate - 1.0, self.stoploss)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        level = self._signal_stop_level(pair, trade.open_date_utc)
        if level is not None and trade.open_rate > 0:
            risk_frac = (trade.open_rate - level) / trade.open_rate
            if risk_frac > 0 and current_profit >= self.target_r_multiple * risk_frac:
                return "take_profit_2R"
        if current_time - trade.open_date_utc >= timedelta(hours=self.time_exit_hours):
            return "time_12h"
        return None

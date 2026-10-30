"""H-006: bull-regime-only pullback re-entry with a tight fixed stop.

Closed candles only; every level the current candle is compared with is
shifted by one candle. Orders execute on the following candle. Spot long only.

Rules:
- Regime(t): close > SMA(4800); SMA(2400) > SMA(4800); SMA(4800)(t) > SMA(4800)(t-720).
- Entry: regime AND min(close, t-48..t-1) <= 0.95 * max(high, t-336..t-1)
  AND close > SMA(48) AND previous close <= previous SMA(48).
- Exit: close >= max(high, t-336..t-1); or close < SMA(4800); or 240 bars
  since entry (time stop, custom_exit); 5% hard stop via stoploss.
- Cooldown: 48 candles after any exit (CooldownPeriod protection).
"""

from datetime import timedelta

from pandas import DataFrame
from freqtrade.strategy import IStrategy


class RegimeGatedPullbackTrend_H006_v1(IStrategy):
    """Pullback recovery entries inside a long-term bull regime."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    startup_candle_count = 5520

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 48}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        dataframe["sma_long"] = close.rolling(4800).mean()
        dataframe["sma_mid"] = close.rolling(2400).mean()
        dataframe["sma_long_lag"] = dataframe["sma_long"].shift(720)
        dataframe["sma_fast"] = close.rolling(48).mean()
        dataframe["sma_fast_prev"] = dataframe["sma_fast"].shift(1)
        dataframe["close_prev"] = close.shift(1)
        dataframe["recent_low_close"] = close.rolling(48).min().shift(1)
        dataframe["prior_high"] = dataframe["high"].rolling(336).max().shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        valid = (
            dataframe["sma_long"].notna()
            & dataframe["sma_mid"].notna()
            & dataframe["sma_long_lag"].notna()
            & dataframe["sma_fast"].notna()
            & dataframe["sma_fast_prev"].notna()
            & dataframe["close_prev"].notna()
            & dataframe["recent_low_close"].notna()
            & dataframe["prior_high"].notna()
        )
        regime = (
            (dataframe["close"] > dataframe["sma_long"])
            & (dataframe["sma_mid"] > dataframe["sma_long"])
            & (dataframe["sma_long"] > dataframe["sma_long_lag"])
        )
        pullback = dataframe["recent_low_close"] <= 0.95 * dataframe["prior_high"]
        recovery = (dataframe["close"] > dataframe["sma_fast"]) & (
            dataframe["close_prev"] <= dataframe["sma_fast_prev"]
        )
        dataframe.loc[
            valid & regime & pullback & recovery & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "pullback_recovery")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        target = dataframe["prior_high"].notna() & (
            dataframe["close"] >= dataframe["prior_high"]
        )
        lost = dataframe["sma_long"].notna() & (
            dataframe["close"] < dataframe["sma_long"]
        )
        dataframe.loc[
            (target | lost) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "target_or_regime_loss")
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_time - trade.open_date_utc >= timedelta(hours=240):
            return "time_stop_240"
        return None

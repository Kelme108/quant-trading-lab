"""H-004: slow 60-day breakout, 200-day regime filter, 30-day low exit.

Closed candles only. Channels are shifted by one candle so the current
candle is never part of the level it is compared with. Orders execute on the
following candle. Spot long only.

Rules:
- Entry: close > prior 1440-candle high AND close > SMA(4800) of close.
- Exit: close < prior 720-candle low; 15% hard stop via stoploss.
- Cooldown: 168 candles after any exit (CooldownPeriod protection).
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy


class SlowTimeSeriesMomentum_H004_v1(IStrategy):
    """Slow time-series momentum breakout."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.15
    # Backtest windows hold only ~2880 candles with no earlier data, so the
    # 200-day SMA uses up to 4800 candles but needs only 1440 to be defined.
    startup_candle_count = 1440

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 168}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["entry_high"] = dataframe["high"].rolling(1440).max().shift(1)
        dataframe["exit_low"] = dataframe["low"].rolling(720).min().shift(1)
        dataframe["regime_sma"] = dataframe["close"].rolling(4800, min_periods=1440).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["entry_high"].notna()
                & dataframe["regime_sma"].notna()
                & (dataframe["close"] > dataframe["entry_high"])
                & (dataframe["close"] > dataframe["regime_sma"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "tsmom60_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["exit_low"].notna()
                & (dataframe["close"] < dataframe["exit_low"])
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "tsmom30_breakdown")
        return dataframe

"""H-089: fast 14-hour breakout in a 60h/180h uptrend, forced flat within the UTC day.

Closed candles only; channels the current candle is compared with are shifted
by one candle. Orders execute on the following candle. Spot long only.

Rules:
- Regime(t): SMA(60) > SMA(180) and close > SMA(60).
- Entry: regime AND close > prior 14-bar high AND signal bar opens 00:00-15:00 UTC;
  at most 2 entries per pair per UTC date (confirm_trade_entry).
- Exit: close < prior 6-bar low OR close < SMA(60).
- 2% hard stop via stoploss; 2-candle cooldown after any exit.
- Time exit in custom_exit: at/after 23:00 UTC or 12 hours after entry.
- Exposure is set by the lab (tradable_balance_ratio), not here.
"""

from datetime import timedelta

from pandas import DataFrame
from freqtrade.strategy import IStrategy


class WeeklyBreakoutRegime_H089_v1(IStrategy):
    """Fast hourly channel breakout in an SMA uptrend with a day-trade time exit."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    startup_candle_count = 200

    max_entries_per_day = 2
    max_hold_hours = 12
    forced_exit_hour = 23
    last_signal_hour = 15

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 2}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma_fast"] = dataframe["close"].rolling(60).mean()
        dataframe["sma_slow"] = dataframe["close"].rolling(180).mean()
        dataframe["entry_high"] = dataframe["high"].rolling(14).max().shift(1)
        dataframe["exit_low"] = dataframe["low"].rolling(6).min().shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = dataframe["date"].dt.hour
        dataframe.loc[
            (
                dataframe["sma_fast"].notna()
                & dataframe["sma_slow"].notna()
                & dataframe["entry_high"].notna()
                & (dataframe["sma_fast"] > dataframe["sma_slow"])
                & (dataframe["close"] > dataframe["sma_fast"])
                & (dataframe["close"] > dataframe["entry_high"])
                & (hour <= self.last_signal_hour)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "breakout14")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["exit_low"].notna()
                & dataframe["sma_fast"].notna()
                & (
                    (dataframe["close"] < dataframe["exit_low"])
                    | (dataframe["close"] < dataframe["sma_fast"])
                )
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "low6_or_regime_lost")
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_time.hour >= self.forced_exit_hour:
            return "time_2300"
        if current_time - trade.open_date_utc >= timedelta(hours=self.max_hold_hours):
            return "time_12h"
        return None

    def confirm_trade_entry(
        self, pair, order_type, amount, rate, time_in_force, current_time, entry_tag, side, **kwargs
    ):
        from freqtrade.persistence import Trade

        day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        trades = Trade.get_trades_proxy(pair=pair, open_date=day_start)
        today = [t for t in trades if t.open_date_utc >= day_start]
        return len(today) < self.max_entries_per_day

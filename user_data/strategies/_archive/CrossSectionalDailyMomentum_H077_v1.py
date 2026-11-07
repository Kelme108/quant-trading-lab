"""H-077: daily cross-sectional momentum over nine large pairs, 1h, long only.

Closed candles only; orders execute on the following candle. Spot long only.
All times UTC.

- Ranking (on the 23:00 bar of day d-1): for each of the nine pairs,
  R = close(23:00 d-1) / close(23:00 d-2) - 1 (24-bar return). A pair is
  dropped if any of its 25 hourly closes from 23:00 d-2 through 23:00 d-1 is
  missing. Remaining pairs ranked by R descending; exact ties broken by pair
  name ascending (earlier name ranks higher).
- Entry: only on the 23:00 bar, if the traded pair is ranked 1..4.
- Exit: time exit, signal on the 22:00 bar (fills at the 23:00 open).
- Stop: fixed 5% native stoploss.

Other pairs are read as informative 1h pairs and aligned on the exact candle
timestamp (no forward fill, so missing bars stay missing as the rule needs).
"""

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

LOOKBACK = 24
WINDOW = LOOKBACK + 1
RANK_HOUR = 23
EXIT_HOUR = 22
TOP_N = 4


class CrossSectionalDailyMomentum_H077_v1(IStrategy):
    """Hold the top-4 of nine pairs by prior UTC-day return for 23 hours."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    startup_candle_count = 50

    def informative_pairs(self):
        return [(pair, "1h") for pair in PAIRS]

    @staticmethod
    def _daily_return(series: pd.Series, grid: pd.DatetimeIndex) -> pd.Series:
        """24-bar return on a complete hourly grid; NaN if any of 25 closes is missing."""
        closes = series.reindex(grid).astype(float)
        complete = closes.notna().astype(float).rolling(WINDOW).sum() == WINDOW
        ret = closes / closes.shift(LOOKBACK) - 1.0
        ret = ret.replace([np.inf, -np.inf], np.nan)
        return ret.where(complete)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get("pair", "")
        dates = pd.to_datetime(dataframe["date"])
        if len(dates) > 0:
            grid = pd.date_range(dates.min(), dates.max(), freq="1h")
        else:
            grid = pd.DatetimeIndex(dates)

        returns = {}
        for name in PAIRS:
            if name == pair:
                own = dataframe.drop_duplicates("date").set_index("date")["close"]
                returns[name] = self._daily_return(own, grid)
                continue
            other_df = self.dp.get_pair_dataframe(pair=name, timeframe="1h")
            if other_df is None or len(other_df) == 0:
                returns[name] = pd.Series(np.nan, index=grid)
                continue
            other = other_df.drop_duplicates("date").set_index("date")["close"]
            returns[name] = self._daily_return(other, grid)

        if pair in returns:
            own_ret = returns[pair]
            better = pd.Series(0.0, index=grid)
            for name in PAIRS:
                if name == pair:
                    continue
                other_ret = returns[name]
                ahead = (other_ret > own_ret) | ((other_ret == own_ret) & (name < pair))
                better = better + (ahead & other_ret.notna()).astype(float)
            rank = (better + 1.0).where(own_ret.notna())
        else:
            own_ret = pd.Series(np.nan, index=grid)
            rank = pd.Series(np.nan, index=grid)

        dataframe["day_return"] = dates.map(own_ret).astype(float).values
        dataframe["xs_rank"] = dates.map(rank).astype(float).values
        dataframe["utc_hour"] = dates.dt.hour.values
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["day_return"].notna()
                & dataframe["xs_rank"].notna()
                & (dataframe["utc_hour"] == RANK_HOUR)
                & (dataframe["xs_rank"] <= TOP_N)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "xs_top4_daily")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close"].notna()
                & (dataframe["utc_hour"] == EXIT_HOUR)
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "time_exit_23h")
        return dataframe

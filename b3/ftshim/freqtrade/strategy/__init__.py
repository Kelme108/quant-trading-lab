"""IStrategy and the strategy helpers the crypto strategies import (see b3/ftshim/README.md)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

from freqtrade.persistence import Trade  # noqa: F401  (re-exported like Freqtrade does)

_UNITS = {"m": 1, "h": 60, "d": 1440, "w": 10080}


def timeframe_to_minutes(timeframe: str) -> int:
    return int(timeframe[:-1]) * _UNITS[timeframe[-1]]


def merge_informative_pair(dataframe: pd.DataFrame, informative: pd.DataFrame, timeframe: str, timeframe_inf: str,
                           ffill: bool = True, append_timeframe: bool = True, date_column: str = "date",
                           suffix: str | None = None) -> pd.DataFrame:
    """Each base candle gets the last informative candle that CLOSED at or before the base candle's close."""
    minutes, minutes_inf = timeframe_to_minutes(timeframe), timeframe_to_minutes(timeframe_inf)
    if minutes_inf < minutes:
        raise ValueError("Tried to merge a faster timeframe to a slower timeframe.")
    if suffix and append_timeframe:
        raise ValueError("You can not specify `append_timeframe` as True and a `suffix`.")
    inf = informative.copy()
    avail = pd.to_datetime(inf[date_column], utc=True) + pd.Timedelta(minutes=minutes_inf)
    if append_timeframe:
        inf.columns = [f"{c}_{timeframe_inf}" for c in inf.columns]
    elif suffix:
        inf.columns = [f"{c}_{suffix}" for c in inf.columns]
    cols = list(inf.columns)
    inf["_ft_available"] = avail.to_numpy()
    left = dataframe.copy()
    left["_ft_close"] = pd.to_datetime(left["date"], utc=True) + pd.Timedelta(minutes=minutes)
    left["_ft_row"] = range(len(left))
    merged = pd.merge_asof(left.sort_values("_ft_close", kind="stable"), inf.sort_values("_ft_available"),
                           left_on="_ft_close", right_on="_ft_available", direction="backward")
    merged = merged.sort_values("_ft_row").reset_index(drop=True)
    merged.index = dataframe.index
    if not ffill:      # only the base candle whose close coincides keeps the values (the exact-join behaviour)
        merged.loc[merged["_ft_available"] != merged["_ft_close"], cols] = float("nan")
    return merged.drop(columns=["_ft_close", "_ft_available", "_ft_row"])


@dataclass
class InformativeData:
    asset: str
    timeframe: str
    fmt: str | Callable | None
    ffill: bool
    candle_type: Any = None


def informative(timeframe: str, asset: str = "", fmt: str | Callable | None = None, *, candle_type=None,
                ffill: bool = True) -> Callable:
    def decorator(fn: Callable) -> Callable:
        infs = getattr(fn, "_ft_informative", [])
        infs.append(InformativeData(asset, timeframe, fmt, ffill, candle_type))
        fn._ft_informative = infs
        return fn
    return decorator


def stoploss_from_absolute(stop_rate: float, current_rate: float, is_short: bool = False,
                           leverage: float = 1.0) -> float:
    if current_rate == 0:
        return 1
    stoploss = 1 - (stop_rate / current_rate)
    if is_short:
        stoploss = -stoploss
    return max(min(stoploss, 1.0), 0.0) * leverage


def stoploss_from_open(open_relative_stop: float, current_profit: float, is_short: bool = False,
                       leverage: float = 1.0) -> float:
    _current_profit = current_profit / leverage
    if (_current_profit == -1 and not is_short) or (is_short and _current_profit == 1):
        return 1
    if is_short:
        stoploss = -1 + ((1 - open_relative_stop / leverage) / (1 - _current_profit))
    else:
        stoploss = 1 - ((1 + open_relative_stop / leverage) / (1 + _current_profit))
    return max(stoploss * leverage, 0.0)


class _Param:
    def __init__(self, *args, default=None, **kwargs):
        self.value = default if default is not None else (args[-1] if args else None)


IntParameter = DecimalParameter = RealParameter = CategoricalParameter = BooleanParameter = _Param


class IStrategy:
    INTERFACE_VERSION = 3
    timeframe = "5m"
    stoploss = -0.10
    minimal_roi: dict = {"0": 100.0}
    trailing_stop = False
    trailing_stop_positive = None
    trailing_stop_positive_offset = 0.0
    trailing_only_offset_is_reached = False
    use_custom_stoploss = False
    use_exit_signal = True
    exit_profit_only = False
    exit_profit_offset = 0.0
    ignore_roi_if_entry_signal = False
    startup_candle_count = 0
    can_short = False
    process_only_new_candles = True
    position_adjustment_enable = False
    order_types: dict = {}
    order_time_in_force: dict = {}

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}
        self.dp = None

    def informative_pairs(self):
        return []

    def bot_start(self, **kwargs) -> None:
        return None

    def populate_indicators(self, dataframe, metadata):  # pragma: no cover - overridden
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):  # pragma: no cover - overridden
        return dataframe

    def populate_exit_trend(self, dataframe, metadata):  # pragma: no cover - overridden
        return dataframe

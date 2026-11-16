"""Proxy markets: symbols of the MetaQuotes-Demo MT5 server that stand in for WIN/WDO-like day trading
while no Brazilian broker demo is available (owner, 2026-11-14: "baixar ativos semelhantes ao WIN/WDO
presentes no MT5").

Each proxy is researched with the SAME backtester as WIN/WDO (b3/backtest.py): long and short, stop
on every entry, entries only inside the session's entry window, book flat before the session close.
What changes per market is only data that is fixed in advance:

- the regular session (local time zone and hours) where day trades happen;
- the price grid (MT5 `point`) and the value of one point for one unit (quote currency);
- the cost scenarios, as a share of the traded notional per round trip. They are the costs of the
  REAL instrument the proxy stands for (the MetaQuotes demo spread is a dealer quote, not a market
  cost), written here BEFORE any backtest was run (2026-11-14):
    * index CFDs -> CME micro/mini index futures: about 0.01% round trip including 1 tick of spread
      (MES: ~US$1.1-2.5 fees + 1 tick US$1.25 on a ~US$33k contract);
    * USDBRL -> B3 mini dollar WDO: base 0.02%, from b3/costs.py "base" (BRL 1.00 fees + 1 tick per
      side on a ~BRL 56k contract);
    * EURUSD / GBPUSD / USDJPY -> ECN spot FX: ~0.7 pip round trip incl. commission, ~0.006%.
  optimistic = half of base, conservative = 2x base, stress = 4x base. Nothing in the results may move
  these numbers; a change is an owner decision recorded here with its date.
- 2026-11-14, owner decision (review 2026-11-14-veredito-1m-5m, option a): every STOP fill on an index pays
  0.005% of the price more in the base scenario (scaled like the other costs: 0.0025% / 0.005% / 0.01% /
  0.02%), because the bar replay fills exactly at the stop while the ticks jump past it (p99 0.009-0.013%,
  research/proxies/tick_fidelity.json). The FX pairs and USDBRL are out of the research scope
  (b3/config/scope_proxies.json) and keep 0.

Results are in the quote currency per 1 unit (index points, or currency units for FX). Gates read
them as a share of the price (b3/metrics.py works on the trade list).
"""

from __future__ import annotations

import hashlib
import inspect
import os
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from b3.calendar import B3SessionCalendar, SessionDay, SessionRules
from b3.costs import REQUIRED_SCENARIOS, B3Cost, get_cost
from b3.instruments import INSTRUMENTS, Instrument
from b3.strategy import B3Strategy
from live.core.clock import B3Calendar, SessionConfig

UTC = ZoneInfo("UTC")
NEW_YORK = ZoneInfo("America/New_York")
# git-ignored exports (research tools run from a worktree point MT5_PROXY_DATA at the main checkout's folder)
DATA_DIR = Path(os.environ.get("MT5_PROXY_DATA") or
                Path(__file__).resolve().parents[1] / "user_data" / "data" / "mt5" / "MetaQuotes-Demo")
COSTS_WRITTEN = "2026-11-14"


@dataclass(frozen=True)
class ProxyMarket:
    symbol: str                 # MT5 symbol on MetaQuotes-Demo
    stands_for: str             # the real instrument it approximates
    tz: str                     # local time zone of the regular session
    open: time                  # regular session, local
    close: time
    tick_size: float            # MT5 `point` of the symbol (price grid of stops)
    currency: str               # quote currency (results are in it, per 1 unit)
    base_round_trip: float      # share of notional per round trip, base scenario
    source: str
    stop_slippage_frac: float = 0.0   # extra adverse share of the price on each stop fill, base scenario

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.tz)

    def instrument(self) -> Instrument:
        return Instrument(root=self.symbol, name=f"{self.symbol} (proxy of {self.stands_for})",
                          point_value_brl=1.0, tick_size=self.tick_size,
                          source=f"MetaQuotes-Demo symbol spec; values per 1 unit in {self.currency}")

    def cost(self, scenario: str) -> B3Cost:
        factor = {"optimistic": 0.5, "base": 1.0, "conservative": 2.0, "stress": 4.0}
        if scenario not in factor:
            raise ValueError(f"unknown scenario {scenario!r}; expected {REQUIRED_SCENARIOS}")
        f = factor[scenario]
        return B3Cost(scenario, 0.0, 0.0, 0.0, notional_frac_per_side=self.base_round_trip * f / 2,
                      stop_slippage_frac=self.stop_slippage_frac * f)


_IDX = ("CME micro/mini index futures: ~0.01% round trip incl. 1 tick (MES ~US$1.1-2.5 fees + US$1.25 tick "
        "on ~US$33k); Optimus Futures, NexusFi, broker tables 2026")
INDEX_STOP_SLIPPAGE = 0.00005
_US = dict(tz="America/New_York", open=time(9, 30), close=time(16, 0), currency="USD", base_round_trip=0.0001,
           stop_slippage_frac=INDEX_STOP_SLIPPAGE)
_FX = ("ECN spot FX: ~0.7 pip round trip incl. commission (~0.006%); base rounded up to 0.01%")
_LDN = dict(tz="Europe/London", open=time(8, 0), close=time(17, 0), base_round_trip=0.0001)

MARKETS: dict[str, ProxyMarket] = {m.symbol: m for m in (
    ProxyMarket("US500", "S&P 500 futures (ES/MES)", tick_size=0.01, source=_IDX, **_US),
    ProxyMarket("USTEC", "Nasdaq-100 futures (NQ/MNQ)", tick_size=0.01, source=_IDX, **_US),
    ProxyMarket("US30", "Dow futures (YM/MYM)", tick_size=0.01, source=_IDX, **_US),
    ProxyMarket("US2000", "Russell 2000 futures (RTY/M2K)", tick_size=0.01, source=_IDX, **_US),
    ProxyMarket("DE40", "DAX futures (FDAX/FDXS)", tz="Europe/Berlin", open=time(9, 0), close=time(17, 30),
                tick_size=0.01, currency="EUR", base_round_trip=0.0001, source=_IDX + "; Xetra session",
                stop_slippage_frac=INDEX_STOP_SLIPPAGE),
    # MetaQuotes-Demo quotes USDBRL only ~09:30-17:00 Sao Paulo (counted on the export, 2026-11-14)
    ProxyMarket("USDBRL", "B3 mini dollar (WDO)", tz="America/Sao_Paulo", open=time(9, 30), close=time(17, 0),
                tick_size=0.0001, currency="BRL", base_round_trip=0.0002,
                source="b3/costs.py WDO base: BRL 1.00 fees + 1 tick per side on ~BRL 56k = ~0.02%"),
    ProxyMarket("EURUSD", "EUR/USD spot / 6E futures", tick_size=0.00001, currency="USD", source=_FX, **_LDN),
    ProxyMarket("GBPUSD", "GBP/USD spot / 6B futures", tick_size=0.00001, currency="USD", source=_FX, **_LDN),
    ProxyMarket("USDJPY", "USD/JPY spot / 6J futures", tick_size=0.001, currency="JPY", source=_FX, **_LDN),
)}


@dataclass(frozen=True)
class B3Market(ProxyMarket):
    """WIN or WDO itself (real B3 data from the Clear demo, b3/b3_data.py). Same rule interface as a proxy, but the
    instrument and the costs are the B3 ones in BRL per contract (b3/instruments.py, b3/costs.py) and the session
    comes from b3/calendar.py (official holidays and hours by date). A stop fill pays `stop_extra_ticks_base`
    ticks more in the base scenario, scaled 0 / 1 / 2 / 4 (plan docs/plano-b3-reuso.md F1, written 2026-11-16
    before any WIN/WDO backtest)."""

    root: str = ""
    data_symbol: str = ""
    stop_extra_ticks_base: float = 1.0

    def instrument(self) -> Instrument:
        return INSTRUMENTS[self.root]

    def cost(self, scenario: str) -> B3Cost:
        factor = {"optimistic": 0.0, "base": 1.0, "conservative": 2.0, "stress": 4.0}
        if scenario not in factor:
            raise ValueError(f"unknown scenario {scenario!r}; expected {REQUIRED_SCENARIOS}")
        return replace(get_cost(self.root, scenario), stop_extra_ticks=self.stop_extra_ticks_base * factor[scenario])


_B3 = dict(tz="America/Sao_Paulo", open=time(9, 0), currency="BRL", base_round_trip=0.0)
B3_MARKETS: dict[str, B3Market] = {m.symbol: m for m in (
    B3Market("WIN", "WIN (mini Ibovespa), Clear demo WIN$N", close=time(18, 25), tick_size=5.0, root="WIN",
             data_symbol="WIN$N", source="b3/costs.py WIN: BRL 0.25/0.50 fees + 0-4 ticks per side", **_B3),
    B3Market("WDO", "WDO (mini dólar), Clear demo WDO$N", close=time(18, 30), tick_size=0.5, root="WDO",
             data_symbol="WDO$N", source="b3/costs.py WDO: BRL 1.00/1.50 fees + 0-4 ticks per side", **_B3),
)}


def market(symbol: str) -> ProxyMarket:
    key = symbol.upper()
    if key in B3_MARKETS:
        return B3_MARKETS[key]
    try:
        return MARKETS[key]
    except KeyError as exc:
        raise ValueError(f"{symbol}: not a market; expected one of {sorted(MARKETS) + sorted(B3_MARKETS)}") from exc


def is_b3(symbol: str) -> bool:
    return symbol.upper() in B3_MARKETS


# ---------------------------------------------------------------------------------------------
# Server time. MetaQuotes-Demo stamps bars in "New York + 7 h" (the FX week opens at 00:00 server
# time on Monday = 17:00 New York on Sunday, in winter and in summer). Checked on the exported files
# by research/tools/proxy_data_check.py (timestamps only).
# ---------------------------------------------------------------------------------------------

SERVER_OFFSET_FROM_NEW_YORK = timedelta(hours=7)


def server_to_utc(server_epoch_s: pd.Series) -> pd.Series:
    """MT5 bar times (seconds, server clock written as if UTC) -> true UTC timestamps."""
    naive = pd.to_datetime(server_epoch_s, unit="s") - SERVER_OFFSET_FROM_NEW_YORK
    return naive.dt.tz_localize(NEW_YORK, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert(UTC)


def load_bars(symbol: str, timeframe: str = "5m", data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Bars in the backtester's format: time (UTC, bar open), open, high, low, close, volume, spread."""
    # the export (MT5 copy_rates structured array, saved by numpy): `time` = MT5 SERVER epoch seconds
    raw = pd.DataFrame(np.load(Path(data_dir) / f"{symbol}-{timeframe}.npy"))
    out = pd.DataFrame({"time": server_to_utc(raw["time"]).to_numpy(), "open": raw["open"].values,
                        "high": raw["high"].values, "low": raw["low"].values, "close": raw["close"].values,
                        "volume": raw["tick_volume"].values, "spread": raw["spread"].values})
    out = out.dropna(subset=["time"]).drop_duplicates("time").sort_values("time").reset_index(drop=True)
    out["time"] = pd.to_datetime(out["time"], utc=True)
    return out


def session_only(bars: pd.DataFrame, mkt: ProxyMarket) -> pd.DataFrame:
    """Keep the bars that OPEN inside the regular session (local open <= t < close). The CFDs quote almost
    24 hours; dropping the overnight bars gives the strategies B3-like days: bar_in_day 0 is the session's
    first bar, day_open its open, and the overnight move shows up as the gap to the previous close."""
    local = bars["time"].dt.tz_convert(mkt.zone).dt.time
    return bars[(local >= mkt.open) & (local < mkt.close)].reset_index(drop=True)


# ---------------------------------------------------------------------------------------------
# Session calendar
# ---------------------------------------------------------------------------------------------

class ProxySessionCalendar(B3Calendar):
    """Same phases as b3.calendar.B3SessionCalendar (closed | no_entry | entry | flatten), for a proxy
    market's regular session in its own time zone. Holidays: `closed_days` (inferred from the data:
    weekdays with no bar inside the session); any other weekday is a session day."""

    def __init__(self, mkt: ProxyMarket, rules: SessionRules | None = None,
                 closed_days: frozenset[date] = frozenset()) -> None:
        super().__init__(SessionConfig(), mkt.zone)
        self.market = mkt
        self.root = mkt.symbol
        self.rules = rules or SessionRules()
        self.closed_days = frozenset(closed_days)
        self._cache: dict[date, SessionDay | None] = {}

    def is_trading_day(self, d: date) -> bool:
        return d.weekday() < 5 and d not in self.closed_days

    def session(self, d: date) -> SessionDay | None:
        if d in self._cache:
            return self._cache[d]
        out = None
        if self.is_trading_day(d):
            o = datetime.combine(d, self.market.open, self.tz)
            c = datetime.combine(d, self.market.close, self.tz)
            r = self.rules
            entry_start = o + timedelta(minutes=r.entry_start_after_open_min)
            entry_end = c - timedelta(minutes=r.entry_end_before_close_min)
            flatten = c - timedelta(minutes=r.flatten_before_close_min)
            if not (o <= entry_start <= entry_end <= flatten <= c):
                raise ValueError(f"{self.root} {d}: session rules do not fit {self.market.open}-{self.market.close}")
            out = SessionDay(d, o, entry_start, entry_end, flatten, c)
        self._cache[d] = out
        return out

    def phase(self, dt: datetime) -> str:
        loc = dt.astimezone(self.tz)
        s = self.session(loc.date())
        if s is None or loc < s.open or loc >= s.close:
            return "closed"
        if loc >= s.flatten_at:
            return "flatten"
        if s.entry_start <= loc < s.entry_end:
            return "entry"
        return "no_entry"


def infer_closed_days(bars: pd.DataFrame, mkt: ProxyMarket) -> frozenset[date]:
    """Weekdays between the first and last bar with no bar inside the regular session (holidays and
    data holes). Acceptable for HISTORY only: exchange holidays are announced in advance."""
    local = bars["time"].dt.tz_convert(mkt.zone)
    t = local.dt.time
    inside = local[(t >= mkt.open) & (t < mkt.close)].dt.date
    have = set(inside)
    d, end, out = local.iloc[0].date(), local.iloc[-1].date(), set()
    while d <= end:
        if d.weekday() < 5 and d not in have:
            out.add(d)
        d += timedelta(days=1)
    return frozenset(out)


def session_coverage(bars: pd.DataFrame, mkt: ProxyMarket, timeframe_min: int) -> pd.Series:
    """Per local session day that has bars: the share of the regular session's bar slots that hold a bar."""
    local = bars["time"].dt.tz_convert(mkt.zone)
    t = local.dt.time
    inside = local[(t >= mkt.open) & (t < mkt.close)]
    minutes = (datetime.combine(date(2000, 1, 3), mkt.close) - datetime.combine(date(2000, 1, 3), mkt.open))
    expected = minutes.total_seconds() / 60 / timeframe_min
    return inside.groupby(inside.dt.date).size() / expected


def incomplete_days(bars: pd.DataFrame, mkt: ProxyMarket, timeframe_min: int, min_coverage: float) -> frozenset[date]:
    """Session days with bars but fewer than `min_coverage` of the session's slots (feed holes, early closes).
    HISTORY ONLY (it counts the whole day's bars): b3/config/scope_proxies.json min_session_coverage."""
    cov = session_coverage(bars, mkt, timeframe_min)
    return frozenset(cov.index[cov < min_coverage])


# ---------------------------------------------------------------------------------------------
# Strategy base
# ---------------------------------------------------------------------------------------------

class ProxyStrategy(B3Strategy):
    """B3Strategy for a proxy market: set `name`, `symbol`, `timeframe_min`, `warmup`, `rules`, `params`.

    Session features (local_date, minute_of_day, bar_in_day, day_open, minutes_to_close) are computed
    in the market's own time zone."""

    symbol: str = ""

    def __init__(self, calendar: B3Calendar | None = None) -> None:
        if not self.name or (self.symbol not in MARKETS and self.symbol not in B3_MARKETS):
            raise ValueError(f"{type(self).__name__}: set `name` and `symbol` "
                             f"(one of {sorted(MARKETS) + sorted(B3_MARKETS)})")
        self.root = self.symbol
        self.market = market(self.symbol)
        if calendar is None:
            calendar = (B3SessionCalendar(self.market.root, rules=self.rules) if isinstance(self.market, B3Market)
                        else ProxySessionCalendar(self.market, self.rules))
        self.calendar = calendar
        if self.calendar.rules != self.rules:
            raise ValueError("the calendar's session rules differ from the strategy's own rules")

    def instrument(self) -> Instrument:
        return self.market.instrument()

    @classmethod
    def on(cls, symbol: str) -> type["ProxyStrategy"]:
        """The same rule bound to another proxy market (the symbol is part of the strategy's hash)."""
        market(symbol)
        return type(f"{cls.__name__}_{symbol}", (cls,), {"symbol": symbol, "__module__": cls.__module__})

    @property
    def hash(self) -> str:
        source = Path(inspect.getsourcefile(type(self))).read_bytes()
        ident = repr((self.name, self.symbol, self.timeframe_min, self.warmup, self.rules,
                      sorted(self.params.items()))).encode()
        return hashlib.sha256(source + ident).hexdigest()[:12]

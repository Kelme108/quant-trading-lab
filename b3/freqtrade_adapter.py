"""Run the crypto lab's Freqtrade strategies (user_data/strategies/, _archive/) inside the B3 engine (plan
docs/plano-b3-reuso.md F2; owner 2026-11-16 "testar as estratégias criadas para cripto aqui").

The strategy's OWN code runs unchanged: populate_indicators / populate_entry_trend / populate_exit_trend, the
@informative methods and merge_informative_pair, the fixed `stoploss`, custom_stoploss, custom_exit,
confirm_trade_entry (with Trade.get_trades_proxy) and the CooldownPeriod protection. When the real Freqtrade
package is not importable, b3/ftshim/ provides that interface.

Two clocks:
- the strategy clock: candles of the strategy's timeframe (15m, 1h, 4h), built from the execution bars by UTC
  buckets like an exchange, and 1d candles per session. Signals, custom_exit and custom_stoploss are evaluated
  once per strategy candle, at its close, like a Freqtrade backtest without --timeframe-detail;
- the execution clock: 5-minute WIN/WDO bars (`exec_timeframe_min`). Entries and exits fill at the open of the
  next execution bar, the stop is checked on every execution bar, and the B3 engine closes everything before the
  session ends (b3/backtest.py).

On WIN/WDO the rule reads the BACK-ADJUSTED $N series (`price_series = "back_adjusted"`, b3/b3_data.py) so
indicators that span sessions see no roll jump; the runner measures returns against the raw price.

Session rules are the same for every ported strategy, fixed here before any WIN/WDO read (2026-11-16): entries
from 15 minutes after the open to 30 minutes before the close, flat 10 minutes before the close.

Declared differences from a Freqtrade backtest (measured on BTC by research/tools/adapter_fidelity.py):
- custom_exit / custom_stoploss / confirm_trade_entry receive current_rate = the close of the candle just closed
  (Freqtrade passes the next candle's open, and the candle's high to custom_stoploss);
- the first stop is set from that close (Freqtrade: from the fill price); it is re-anchored to the fill price at the
  next strategy candle;
- protections other than CooldownPeriod and the trailing_stop attribute are not modelled (`unsupported` lists
  what a strategy declares that is not);
- positions never cross the session close; long only (no ported strategy shorts).
Excluded: strategies that read another pair (BTC/..., cross-sectional whitelists), listed by `portability()`.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import math
import re
import sys
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, EXIT, HOLD, tick_floor
from live.core.models import Signal

ROOT = Path(__file__).resolve().parents[1]
SHIM = Path(__file__).resolve().parent / "ftshim"
STRATEGY_DIRS = (ROOT / "user_data" / "strategies", ROOT / "user_data" / "strategies" / "_archive")
ADAPTER_RULES = SessionRules(entry_start_after_open_min=15, entry_end_before_close_min=30, flatten_before_close_min=10)
SESSION_BARS_5M = 113          # longest B3 session in 5-minute bars (09:00-18:30)
OTHER_PAIR = re.compile(r"""["'][A-Z0-9]{2,10}/(USDT|USD|BUSD|BTC)["']""")


def ensure_imports() -> None:
    """Freqtrade (real, or the shim) and the strategy folders on sys.path."""
    try:
        import freqtrade.strategy  # noqa: F401
    except ImportError:
        sys.path.insert(0, str(SHIM))
    for d in STRATEGY_DIRS:
        if str(d) not in sys.path:
            sys.path.append(str(d))


def strategy_files() -> dict[str, Path]:
    """Strategy name -> file, by the lab's convention: the file is named after its class."""
    out = {}
    for d in STRATEGY_DIRS:
        for p in sorted(d.glob("*.py")):
            src = p.read_text(encoding="utf-8", errors="replace")
            if p.stem not in out and re.search(rf"^class\s+{re.escape(p.stem)}\s*\(", src, re.M):
                out[p.stem] = p
    return out


def portability(name: str, path: Path) -> dict:
    """Static check: can this strategy run on one B3 contract? Reasons when not."""
    src = path.read_text(encoding="utf-8", errors="replace")
    reasons = []
    if OTHER_PAIR.search(src):
        reasons.append("reads another pair (e.g. BTC/USDT) that has no B3 counterpart")
    if "current_whitelist" in src and "for pair in self.dp.current_whitelist()" not in src:
        reasons.append("cross-sectional: uses the whole whitelist")
    if "can_short = True" in src:
        reasons.append("shorts")
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    return {"strategy": name, "file": str(rel).replace("\\", "/"),
            "archived": path.parent.name == "_archive", "portable": not reasons, "reasons": reasons}


def load_class(name: str, path: Path | None = None) -> type:
    ensure_imports()
    path = path or strategy_files()[name]
    spec = importlib.util.spec_from_file_location(f"ftstrat_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return getattr(mod, name)


def tf_minutes(tf: str) -> int:
    return int(tf[:-1]) * {"m": 1, "h": 60, "d": 1440, "w": 10080}[tf[-1]]


# ---------------------------------------------------------------------------------------------
# Candles
# ---------------------------------------------------------------------------------------------

def candles(bars: pd.DataFrame, minutes: int, exec_minutes: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Strategy candles from execution bars (UTC buckets; 1440 = one per UTC day, which holds a whole B3 session).
    Returns (candles with `date` = bucket start, and for each candle the row index of its LAST execution bar)."""
    t = pd.to_datetime(bars["time"], utc=True)
    if minutes == exec_minutes:
        c = pd.DataFrame({"date": t, "open": bars["open"].to_numpy(), "high": bars["high"].to_numpy(),
                          "low": bars["low"].to_numpy(), "close": bars["close"].to_numpy(),
                          "volume": bars["volume"].to_numpy()})
        return c.reset_index(drop=True), np.arange(len(bars))
    bucket = t.dt.floor(f"{minutes}min") if minutes < 1440 else t.dt.floor("1D")
    g = pd.DataFrame({"b": bucket.to_numpy(), "open": bars["open"].to_numpy(), "high": bars["high"].to_numpy(),
                      "low": bars["low"].to_numpy(), "close": bars["close"].to_numpy(),
                      "volume": bars["volume"].to_numpy(), "i": np.arange(len(bars))}).groupby("b", sort=True)
    c = pd.DataFrame({"date": g["b"].first().index, "open": g["open"].first().to_numpy(),
                      "high": g["high"].max().to_numpy(), "low": g["low"].min().to_numpy(),
                      "close": g["close"].last().to_numpy(), "volume": g["volume"].sum().to_numpy()})
    c["date"] = pd.to_datetime(c["date"], utc=True)
    return c, g["i"].last().to_numpy()


class DataProvider:
    """The part of Freqtrade's DataProvider the strategies call, for ONE pair."""

    def __init__(self, pair: str, frames: dict[str, pd.DataFrame], timeframe: str):
        self.pair, self.frames, self.timeframe = pair, frames, timeframe
        self.analyzed: pd.DataFrame | None = None
        self.cursor = -1                       # index of the last CLOSED strategy candle

    def _check(self, pair: str) -> None:
        if pair != self.pair:
            raise LookupError(f"the strategy asked for {pair}; only {self.pair} exists here")

    def get_pair_dataframe(self, pair: str, timeframe: str | None = None, candle_type: str = "") -> pd.DataFrame:
        self._check(pair)
        tf = timeframe or self.timeframe
        if tf not in self.frames:
            raise LookupError(f"timeframe {tf} not prepared")
        return self.frames[tf].copy()

    def historic_ohlcv(self, pair: str, timeframe: str | None = None, candle_type: str = "") -> pd.DataFrame:
        return self.get_pair_dataframe(pair, timeframe)

    def get_analyzed_dataframe(self, pair: str, timeframe: str):
        self._check(pair)
        if self.analyzed is None or self.cursor < 0:
            return pd.DataFrame(), None
        df = self.analyzed.iloc[: self.cursor + 1]
        return df, df["date"].iloc[-1]

    def current_whitelist(self) -> list[str]:
        return [self.pair]


def informative_timeframes(strategy) -> set[str]:
    tfs = {tf for _, tf, *_ in (strategy.informative_pairs() or [])}
    for _, fn in inspect.getmembers(type(strategy), predicate=callable):
        for inf in getattr(fn, "_ft_informative", []):
            tfs.add(inf.timeframe)
    return tfs


def analyze(strategy, df: pd.DataFrame, pair: str) -> pd.DataFrame:
    """Freqtrade's advise_all_indicators + entry + exit, for one pair."""
    from freqtrade.strategy import merge_informative_pair
    meta = {"pair": pair}
    for _, fn in inspect.getmembers(type(strategy), predicate=callable):
        for inf in getattr(fn, "_ft_informative", []):
            if inf.asset:
                raise LookupError(f"@informative on another asset ({inf.asset})")
            inf_df = fn(strategy, strategy.dp.get_pair_dataframe(pair, inf.timeframe), meta)
            fmt = inf.fmt or "{column}_{timeframe}"
            if callable(fmt):
                names = {c: fmt(column=c, timeframe=inf.timeframe, asset="", base="", quote="") for c in inf_df.columns}
            else:
                names = {c: fmt.format(column=c, timeframe=inf.timeframe, asset="", base="", quote="",
                                       BASE="", QUOTE="") for c in inf_df.columns}
            date_col = names["date"]
            inf_df = inf_df.rename(columns=names)
            df = merge_informative_pair(df, inf_df, strategy.timeframe, inf.timeframe, ffill=inf.ffill,
                                        append_timeframe=False, date_column=date_col)
    df = strategy.populate_indicators(df, meta)
    df = strategy.populate_entry_trend(df, meta)
    df = strategy.populate_exit_trend(df, meta)
    for col, default in (("enter_long", 0), ("exit_long", 0), ("enter_tag", None), ("exit_tag", None)):
        if col not in df.columns:
            df[col] = default
    return df


def _protections(strategy) -> list[dict]:
    p = getattr(strategy, "protections", [])
    return list(p() if callable(p) else p or [])


# ---------------------------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------------------------

@dataclass
class _State:
    trades: list
    open_trade: object | None = None
    pending: tuple | None = None          # (fill time, tag) of an entry just sent
    lock_until: pd.Timestamp | None = None
    last_open_now: pd.Timestamp | None = None
    reanchor: bool = False


class FreqtradeRule(ProxyStrategy):
    """Base of the generated rules (`make_rule`). Bind to a market with `.on("WIN")`."""

    ft_class: type = None
    ft_path: Path = None
    price_series = "back_adjusted"
    rules = ADAPTER_RULES
    exec_timeframe_min = 5
    pair_name = "WIN/BRL"
    fee_per_side: float | None = None        # Freqtrade fee for current_profit; None = the market's base cost

    # ---- identity: the adapter AND the strategy file ----
    @property
    def hash(self) -> str:
        src = Path(inspect.getsourcefile(FreqtradeRule)).read_bytes() + Path(self.ft_path).read_bytes()
        ident = repr((self.name, self.symbol, self.exec_timeframe_min, self.rules)).encode()
        return hashlib.sha256(src + ident).hexdigest()[:12]

    def _fee(self, raw_price: float) -> float:
        if self.fee_per_side is not None:
            return self.fee_per_side
        c, inst = self.market.cost("base"), self.market.instrument()
        return (c.cash_per_side_brl + c.slippage_ticks_per_side * inst.tick_value_brl) / (raw_price * inst.point_value_brl)

    # ---- vectorised part ----
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        ensure_imports()
        from freqtrade.persistence import Trade
        st = self.ft_class(config={"runmode": "backtest", "timeframe": self.ft_class.timeframe,
                                   "exchange": {"name": "b3", "pair_whitelist": [self.pair_name]},
                                   "stake_currency": "BRL", "dry_run": True})
        self.ft = st
        tf = tf_minutes(st.timeframe)
        self.ft_tf = tf
        base, last_row = candles(df, tf, self.exec_timeframe_min)
        frames = {st.timeframe: base}
        st.dp = DataProvider(self.pair_name, frames, st.timeframe)
        for inf_tf in informative_timeframes(st) | {"1h", "4h", "1d"}:
            m = tf_minutes(inf_tf)
            if m >= tf and inf_tf not in frames:
                frames[inf_tf] = candles(df, m, self.exec_timeframe_min)[0]
        Trade._registry = lambda pair: self._state.trades
        self._state = _State(trades=[])
        st.bot_start()
        analyzed = analyze(st, base.copy(), self.pair_name)
        st.dp.analyzed = analyzed
        self.cooldown = sum(int(p.get("stop_duration_candles", 0)) for p in _protections(st)
                            if p.get("method") == "CooldownPeriod")
        n = len(df)
        enter = np.zeros(n, dtype=bool)
        exit_ = np.zeros(n, dtype=bool)
        cidx = np.full(n, -1, dtype=np.int64)
        tags = np.full(n, None, dtype=object)
        xtags = np.full(n, None, dtype=object)
        e, x = analyzed["enter_long"].fillna(0).to_numpy() == 1, analyzed["exit_long"].fillna(0).to_numpy() == 1
        cidx[last_row] = np.arange(len(analyzed))
        enter[last_row] = e
        exit_[last_row] = x
        tags[last_row] = analyzed["enter_tag"].to_numpy()
        xtags[last_row] = analyzed["exit_tag"].to_numpy()
        df["ft_cidx"], df["ft_enter"], df["ft_exit"], df["ft_tag"], df["ft_xtag"] = cidx, enter, exit_, tags, xtags
        return df

    # ---- bar by bar ----
    def decide(self, row, position):
        from freqtrade.persistence import Trade
        s = self._state
        now = pd.Timestamp(row.time) + timedelta(minutes=self.exec_timeframe_min)
        raw = row.close - getattr(row, "adj_offset", 0.0)
        # the engine's view of the position is the truth: record fills and closes it made
        if s.pending is not None:
            fill_time, tag = s.pending
            s.pending = None
            if position is not None:
                s.open_trade = Trade(self.pair_name, fill_time.to_pydatetime(), float(position.entry_price), tag,
                                     self._fee(raw), self._fee(raw), stop_loss=position.stop_loss)
                s.trades.append(s.open_trade)
                s.reanchor = True
        if position is None and s.open_trade is not None:
            closed_at = now
            if s.last_open_now is not None and s.last_open_now.date() != now.date():
                ses = self.calendar.session(s.last_open_now.tz_convert(self.calendar.tz).date())
                closed_at = pd.Timestamp(ses.flatten_at) if ses else s.last_open_now
            self._close(closed_at, None, "engine_exit")
        if position is not None:
            s.last_open_now = now
        if row.ft_cidx < 0:
            return Signal(HOLD)
        self.ft.dp.cursor = int(row.ft_cidx)
        current_time = now.to_pydatetime()
        rate = float(row.close)
        tick = self.market.tick_size
        st = self.ft
        if position is not None and s.open_trade is not None:
            t = s.open_trade
            profit = t.calc_profit_ratio(rate)
            reason = None
            if hasattr(st, "custom_exit"):
                r = st.custom_exit(pair=self.pair_name, trade=t, current_time=current_time, current_rate=rate,
                                   current_profit=profit)
                if r:
                    reason = r if isinstance(r, str) else "custom_exit"
            if reason is None and st.use_exit_signal and row.ft_exit:
                if not st.exit_profit_only or profit > st.exit_profit_offset:
                    reason = row.ft_xtag if isinstance(row.ft_xtag, str) and row.ft_xtag else "exit_signal"
            if reason:
                self._close(now, rate, reason)
                return Signal(EXIT, reason=reason)
            stop = position.stop_loss
            target = stop
            if s.reanchor:          # first strategy candle after the fill: the fixed stop from the FILL price
                target = tick_floor(t.open_rate * (1 + st.stoploss), tick)
                s.reanchor = False
            if st.use_custom_stoploss:          # Freqtrade: a custom stop only ever moves up
                sl = st.custom_stoploss(pair=self.pair_name, trade=t, current_time=current_time, current_rate=rate,
                                        current_profit=profit, after_fill=False)
                if sl is not None and not (isinstance(sl, float) and math.isnan(sl)):
                    cand = tick_floor(rate * (1 - abs(float(sl))), tick)
                    target = cand if target is None else max(target, cand)
            if target is not None and target != stop:
                if target >= rate:                       # already through the stop: out at the next open
                    self._close(now, rate, "stop_loss")
                    return Signal(EXIT, reason="stop_loss")
                t.stop_loss = target
                return Signal(HOLD, stop_price=target, reason="move_stop")
            return Signal(HOLD)
        if position is None and row.ft_enter:
            if s.lock_until is not None and now < s.lock_until:
                return Signal(HOLD)
            tag = row.ft_tag if isinstance(row.ft_tag, str) and row.ft_tag else None
            if hasattr(st, "confirm_trade_entry"):
                ok = st.confirm_trade_entry(pair=self.pair_name, order_type="market", amount=1.0, rate=rate,
                                            time_in_force="gtc", current_time=current_time, entry_tag=tag, side="long")
                if not ok:
                    return Signal(HOLD)
            stop = tick_floor(rate * (1 + st.stoploss), tick)
            if not stop < rate:
                stop = tick_floor(rate - tick, tick)
            s.pending = (now, tag)
            return Signal(ENTER_LONG, stop_price=stop, reason=tag or "enter_signal")
        return Signal(HOLD)

    def _close(self, when: pd.Timestamp, rate, reason: str) -> None:
        s = self._state
        t = s.open_trade
        if t is None:
            return
        t.is_open = False
        t.close_date_utc = pd.Timestamp(when).to_pydatetime()
        t.close_rate = rate
        t.exit_reason = reason
        s.open_trade = None
        s.last_open_now = None
        if self.cooldown:
            s.lock_until = pd.Timestamp(when) + timedelta(minutes=self.cooldown * self.ft_tf)


def rule_id(name: str) -> str:
    return f"C-{name}"


def make_rule(name: str, path: Path | None = None, **overrides) -> type[FreqtradeRule]:
    """A B3 rule class running the Freqtrade strategy `name`; bind it with `.on("WIN")`."""
    path = Path(path or strategy_files()[name])
    cls = load_class(name, path)
    tf = tf_minutes(cls.timeframe)
    # Freqtrade counts startup_candle_count in candles of the STRATEGY timeframe and loads every informative timeframe
    # over that same span; on B3 the same number of strategy candles spans ~2.5x more calendar time (9-hour
    # sessions), so the informative frames get at least as many candles as Freqtrade gave them.
    warmup = int(cls.startup_candle_count or 0) * max(1, tf // 5) + 2 * SESSION_BARS_5M
    attrs = {"name": rule_id(name), "ft_class": cls, "ft_path": path, "warmup": warmup,
             "timeframe_min": 5, "params": {"freqtrade_strategy": name, "strategy_timeframe": cls.timeframe},
             "__module__": __name__} | overrides
    return type(f"FT_{name}", (FreqtradeRule,), attrs)


# ---------------------------------------------------------------------------------------------
# 24-hour crypto mode, for the fidelity check against the lab's own Freqtrade backtests
# ---------------------------------------------------------------------------------------------

class _CryptoCalendar:
    """Always `entry` (no session, no flatten); days and weeks in UTC."""

    def __init__(self, rules: SessionRules):
        from live.core.clock import AlwaysOpenCalendar
        self._c = AlwaysOpenCalendar()
        self.tz, self.rules = self._c.tz, rules

    def phase(self, dt):
        return "entry"

    def session(self, d):
        return None

    def day_key(self, dt):
        return self._c.day_key(dt)

    def week_key(self, dt):
        return self._c.week_key(dt)


@dataclass(frozen=True)
class _CryptoMarket:
    symbol: str
    fee: float
    tick_size: float = 0.01

    def instrument(self):
        from b3.instruments import Instrument
        return Instrument(root=self.symbol, name=self.symbol, point_value_brl=1.0, tick_size=self.tick_size,
                          source="crypto spot, 1 unit")

    def cost(self, scenario: str = "base"):
        from b3.costs import B3Cost
        return B3Cost(scenario, 0.0, 0.0, 0.0, notional_frac_per_side=self.fee)


def make_crypto_rule(name: str, fee: float, pair: str = "BTC/USDT", path: Path | None = None) -> FreqtradeRule:
    """The same adapter on 24-hour data with the strategy's own timeframe as the execution clock (a Freqtrade
    backtest without --timeframe-detail): fills at the next candle's open, stop at the stop price, fee on notional."""
    cls = make_rule(name, path, pair_name=pair, fee_per_side=fee)
    tf = tf_minutes(cls.ft_class.timeframe)

    def __init__(self):
        self.root = self.symbol = pair
        self.market = _CryptoMarket(pair, fee)
        self.calendar = _CryptoCalendar(self.rules)

    crypto = type(f"FTC_{name}", (cls,), {"__init__": __init__, "exec_timeframe_min": tf, "timeframe_min": tf,
                                          "warmup": int(cls.ft_class.startup_candle_count or 0),
                                          "rules": SessionRules(0, 0, 0)})
    return crypto()

"""A conveyor family variant (b3/families) with an exit-menu exit (b3/config/exit_menu.json), as a live-engine rule
for the Clear DEMO. Owner 2026-11-18: 'agora e com vc, deixe tudo ligado... teste tudo, stop loss, take profit, novas
estrategias'. Demonstration, NOT evidence; validation stays unread.

Same computations as the research (b3/exit_menu.py + b3/p026_lab.py):
- the family's own signal on the live window (the conveyor's 21-session check guarantees the window rebuilds it),
  zero during the first 20 sessions of the window, only inside the entry window (SessionRules 15/30/10);
- V = mean |30-minute return| at the signal bar's minute of day over the 20 previous sessions;
- stop k_s x V x price and target k_t x V x price, rounded up to the tick (at least 1 tick), sent to the SERVER with
  the entry (the entry price is unknown: measured from the signal bar's close);
- breakeven/trailing (exit S4) through MOVE_STOP at every bar close (tighten only); a close through the level exits;
- time exit 60 minutes after the entry; the engine flattens 10 minutes before the close;
- at most 10 entries per session: risk.max_entries_per_day in the demo config.
"""

from __future__ import annotations

import json
import math
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from b3 import esteira as es
from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, MOVE_STOP, bars_to_frame
from live.core.models import Signal

_CFG = Path(__file__).resolve().parent / "config"
# V-based menu S1..S4 and the fixed-BRL menu B1..B5 (owner 2026-11-21: stop/take-profit in reais)
EXITS = {**json.loads((_CFG / "exit_menu.json").read_text(encoding="utf-8"))["exits"],
         **json.loads((_CFG / "exit_brl.json").read_text(encoding="utf-8"))["exits"]}
RULES = SessionRules(entry_start_after_open_min=15, entry_end_before_close_min=30, flatten_before_close_min=10)
EPS = 1e-9
BARS_PER_SESSION_1M = 560


def _ceil_tick(x: float, tick: float) -> float:
    return max(math.ceil(x / tick - 1e-9) * tick, tick)


def build(family_id: str, market: str, tf: int, params: dict, exit_id: str,
          other_market_ok: bool = False) -> type[ProxyStrategy]:
    """`other_market_ok`: DEMO only (owner 2026-11-23, "todos nos dois ativos"): run the family on a market it was never
    screened on. The rule code is unchanged; there is no research number for that market to compare with."""
    fams = {f.id: f for f in es.load_families()}
    if family_id not in fams:
        raise SystemExit(f"unknown conveyor family {family_id}")
    fam = fams[family_id]
    if tf not in fam.timeframes or (market not in fam.markets and not other_market_ok):
        raise SystemExit(f"{family_id} does not run on {market} {tf}m")
    if params not in fam.variants():
        raise SystemExit(f"{family_id}: {params} is not a variant of its grid")
    spec = EXITS[exit_id]

    class EsteiraRule(_Base):
        pass

    EsteiraRule.name = f"{family_id}_{exit_id}_{tf}m_" + "_".join(f"{k}{v}" for k, v in params.items())
    EsteiraRule.symbol = market
    EsteiraRule.timeframe_min = tf
    EsteiraRule.warmup = 22 * BARS_PER_SESSION_1M // tf
    EsteiraRule.rules = RULES
    EsteiraRule.params = {"family": family_id, "code_hash": fam.code_hash, "exit": exit_id, **params}
    EsteiraRule.family, EsteiraRule.variant, EsteiraRule.spec = fam, dict(params), spec
    return EsteiraRule


class _Base(ProxyStrategy):
    family = None
    variant: dict = {}
    spec: dict = {}

    def __init__(self, calendar=None) -> None:
        super().__init__(calendar)
        self._trade: dict | None = None

    @property
    def hash(self) -> str:                    # the family's code hash + the variant + the exit
        import hashlib
        ident = repr((self.name, self.symbol, self.timeframe_min, self.family.code_hash, sorted(self.variant.items()),
                      json.dumps(self.spec, sort_keys=True))).encode()
        return hashlib.sha256(ident).hexdigest()[:12]

    def indicators(self, df):
        day = pd.factorize(df["local_date"])[0]
        fr = SimpleNamespace(df=df, tf=self.timeframe_min, day=day)
        ctx = es.Ctx(fr)
        d = es.directions(self.family, fr, self.variant, ctx=ctx)
        m30 = ctx.bars(30)
        df["em_side"] = d
        df["em_v"] = ctx.same_minute(np.abs(ctx.c / ctx.prev(ctx.c, m30) - 1.0), "mean")
        return df

    def signal(self, bars, position):
        return self.decide_frame(self.prepare(bars_to_frame(bars)), position)

    def decide(self, row, position):
        return self._entry(row) if position is None else Signal(HOLD)

    def _dist(self, key, v, price):
        s = self.spec.get(key)
        if s is None:
            return None
        if s[0] == "brl":            # fixed BRL per contract (b3/config/exit_brl.json), as b3/p026_lab.distances
            return _ceil_tick(s[1] / self.market.instrument().point_value_brl, self.market.tick_size)
        if s[0] != "V":
            raise ValueError(f"exit kind {s[0]!r} is not supported live")
        return _ceil_tick(s[1] * v * price, self.market.tick_size)

    def _plan(self, side, v, c, since):
        return {"side": side, "since": since, "stop": self._dist("stop", v, c), "target": self._dist("target", v, c),
                "trail": self._dist("trail", v, c), "be": self._dist("breakeven", v, c)}

    def _entry(self, row):
        side, v, c = int(row.em_side), float(row.em_v), float(row.close)
        if side == 0 or not (math.isfinite(v) and v > 0):
            return Signal(HOLD)
        tr = self._plan(side, v, c, row.time + timedelta(minutes=self.timeframe_min))
        self._trade = tr
        tp = None if tr["target"] is None else c + side * tr["target"]
        kind = ENTER_LONG if side > 0 else ENTER_SHORT
        return Signal(kind, stop_price=c - side * tr["stop"], take_profit=tp, reason=f"{self.family.id}_{self.params['exit']}")

    def _recover(self, frame, side):
        before = frame.iloc[:-1]
        f = before[(before["local_date"] == frame["local_date"].iloc[-1]) & (before["em_side"] == side)]
        if not len(f):
            return None
        r = f.iloc[-1]
        return self._plan(side, float(r["em_v"]), float(r["close"]), r["time"] + timedelta(minutes=self.timeframe_min))

    def decide_frame(self, frame, position):
        row = next(frame.tail(1).itertuples(index=False, name="Row"))
        if position is None or not position.volume:
            self._trade = None
            return self._entry(row)
        side = 1 if position.volume > 0 else -1
        tr = self._trade if self._trade and self._trade["side"] == side else self._recover(frame, side)
        if tr is None:
            return Signal(HOLD, reason="open position without a known signal: server stop/target and flatten only")
        self._trade = tr
        if row.time + timedelta(minutes=self.timeframe_min) >= tr["since"] + timedelta(minutes=self.spec["hold_min"]):
            return Signal(EXIT, reason="time_exit")
        if tr["trail"] is None and tr["be"] is None:
            return Signal(HOLD)
        held = frame[frame["time"] >= tr["since"]]
        if not len(held):
            return Signal(HOLD)
        e = float(position.entry_price)
        best = float(held["high"].max()) if side > 0 else float(held["low"].min())
        x_e, x_best = side * e, side * best                                   # long-like coordinates
        lvl = x_e - tr["stop"]
        if tr["be"] is not None and x_best - x_e >= tr["be"] - EPS:
            lvl = max(lvl, x_e)
        if tr["trail"] is not None:
            lvl = max(lvl, x_best - tr["trail"])
        level = side * lvl
        if side * float(row.close) <= lvl + EPS:
            return Signal(EXIT, reason="trail_through")
        cur = position.stop_loss
        if cur is None or side * level > side * cur + EPS:
            return Signal(MOVE_STOP, stop_price=float(level), reason="breakeven_trailing")
        return Signal(HOLD)

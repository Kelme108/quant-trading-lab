"""Entry point of the live engine on MetaTrader 5 (Windows host, terminal open).

    live/.venv/Scripts/python.exe -m live.run --config live/config/live.json --check
    live/.venv/Scripts/python.exe -m live.run --config live/config/live.json

--check  connects, prints account / symbol specs / server-time estimate and the
         real-money guard verdict, and sends NOTHING.
(no flag) runs the loop: every `poll_seconds` one engine step (closed bars only,
         risk checks, journal). Stop it with Ctrl+C or the kill switch file.

Credentials come only from the environment or an untracked env file
(default live/.env): MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, MT5_PATH. They are
never printed. LIVE_MODE defaults to "demo"; in demo a REAL account is refused.

B3 demonstration (owner 2026-11-16, live/config/demo-b3-*.json): strategy
{"name": "b3_rule", "rule": "P-004", "market": "WIN"} runs a research rule on
the Clear DEMO. `broker.attach` names b3/config/broker_mt5.json: the engine
attaches to that terminal AS IT IS LOGGED IN, with no login or password, and
the env file is NOT read (live/.env holds another broker's account). It
refuses any account that is not a demo, any server other than the one in that
file, and any server whose name has PRD or REAL. Shorts (risk.long_only=false)
are allowed only there.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable

from live.brokers.mt5 import MT5Broker, MT5Unavailable
from live.core.clock import AlwaysOpenCalendar, B3Calendar, Clock, SessionConfig, SystemClock
from live.core.engine import Engine
from live.core.journal import Journal
from live.core.killswitch import KillSwitch
from live.core.realguard import trading_blockers
from live.core.risk import RiskConfig, RiskManager
from live.strategies.b3_rule import B3RuleStrategy
from live.strategies.smoke import SmokeStrategy

log = logging.getLogger("live.run")
MAX_CONSECUTIVE_ERRORS = 20


def load_env_file(path: str | Path) -> None:
    """KEY=VALUE lines into os.environ, without overriding what is already set."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config(path: str | Path) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    if cfg.get("allow_real") and os.environ.get("LIVE_MODE", "demo") != "real":
        raise SystemExit("allow_real=true in the config but LIVE_MODE is not 'real'; refusing")
    if cfg.get("strategy", {}).get("name") == "b3_rule":
        if cfg.get("allow_real") or cfg.get("mode") != "demo":
            raise SystemExit("a b3_rule demonstration runs only with mode=demo and allow_real=false")
        if not cfg.get("broker", {}).get("attach"):
            raise SystemExit("a b3_rule demonstration attaches to the broker terminal (broker.attach)")
    if not cfg.get("risk", {}).get("long_only", True) and cfg.get("mode") != "demo":
        raise SystemExit("risk.long_only=false (shorts) is allowed only with mode=demo")
    return cfg


def attach_config(cfg: dict) -> dict | None:
    path = cfg.get("broker", {}).get("attach")
    if not path:
        return None
    a = json.loads(Path(path).read_text(encoding="utf-8"))
    server = str(a.get("server", ""))
    if not server or any(bad in server.upper() for bad in ("PRD", "REAL")) or a.get("account_type") != "demo":
        raise SystemExit(f"{path}: only a demo server can be attached (got {server!r})")
    return a


def build_calendar(cfg: dict, strategy=None) -> B3Calendar:
    if isinstance(strategy, B3RuleStrategy):
        return strategy.calendar          # the rule's own session rules, official holidays and session hours
    if cfg.get("calendar", "b3") == "always_open":
        return AlwaysOpenCalendar()
    from datetime import date, time as dtime
    s = cfg.get("session_brt", {})
    t = lambda k, d: dtime.fromisoformat(s.get(k, d))  # noqa: E731
    return B3Calendar(SessionConfig(open=t("open", "09:00"), entry_start=t("entry_start", "09:15"),
                                    entry_end=t("entry_end", "17:00"), flatten_at=t("flatten_at", "17:45"),
                                    close=t("close", "18:00"),
                                    holidays=frozenset(date.fromisoformat(h) for h in s.get("holidays", []))))


def build_broker(cfg: dict, mt5_module: Any, alert: Callable[[str], None] | None = None,
                 now: Callable | None = None, require_offset: bool = True) -> MT5Broker:
    b = cfg.get("broker", {})
    offset = b.get("server_utc_offset_hours")
    if offset is None:
        if require_offset:
            raise SystemExit("broker.server_utc_offset_hours is required; run --check to estimate it")
        offset = 0.0
    kw = {"now": now} if now else {}
    allow_short = not cfg.get("risk", {}).get("long_only", True)
    att = attach_config(cfg)
    if att is not None:            # the logged-in terminal, no credentials at all
        creds = {"path": att["terminal_path"], "login": None, "password": None, "server": None}
    else:
        creds = {"path": os.environ.get("MT5_PATH") or None, "login": os.environ.get("MT5_LOGIN") or None,
                 "password": os.environ.get("MT5_PASSWORD") or None, "server": os.environ.get("MT5_SERVER") or None}
    return MT5Broker(mt5_module, magic=int(b.get("magic", 260611)), server_utc_offset_hours=float(offset),
                     deviation_points=int(b.get("deviation_points", 20)), alert=alert,
                     allow_short=allow_short, **creds, **kw)


def build_strategy(cfg: dict, broker: MT5Broker):
    s = cfg.get("strategy", {"name": "smoke"})
    if s.get("name") == "b3_rule":
        st = B3RuleStrategy(str(s["rule"]), str(s["market"]), cfg.get("snapshot_file"), cfg["symbols"][0])
        if len(cfg["symbols"]) != 1 or not cfg["symbols"][0].upper().startswith(st.market):
            raise SystemExit(f"a b3_rule runs on exactly one {st.market} contract (e.g. {st.market}Z26)")
        if int(cfg.get("timeframe_min", st.timeframe_min)) != st.timeframe_min:
            raise SystemExit(f"{st.rule_id} runs on {st.timeframe_min}-minute bars")
        return st
    if s.get("name") != "smoke":
        raise SystemExit(f"strategy {s.get('name')!r} is not available in the live engine yet "
                         "(only a validated, frozen B3 hypothesis may be added here)")
    if len(cfg["symbols"]) != 1:
        raise SystemExit("the smoke strategy runs on exactly one symbol")
    spec = broker.symbol_spec(cfg["symbols"][0])
    return SmokeStrategy(int(cfg["timeframe_min"]), spec.tick_size, int(s.get("stop_ticks", 50)))


def guard(cfg: dict, config_path: str | Path, broker: MT5Broker, strategy) -> list[str]:
    acc = broker.account()
    why = trading_blockers(os.environ, config_path, cfg.get("sha_file", "live/config/live.sha256"),
                           acc.is_demo, acc.account_id, strategy_approved=False)
    if strategy.name == "smoke" and not acc.is_demo:
        why.append("smoke_strategy_on_non_demo_account")
    if isinstance(strategy, B3RuleStrategy) and not acc.is_demo:
        why.append("b3_demonstration_on_non_demo_account")
    if not cfg.get("risk", {}).get("long_only", True) and not acc.is_demo:
        why.append("shorts_on_non_demo_account")
    att = attach_config(cfg)
    if att is not None:
        info = broker.mt5.account_info()
        if getattr(info, "server", None) != att["server"]:
            why.append("attached_server_differs_from_broker_config")
    return why


def check(cfg: dict, config_path: str | Path, broker: MT5Broker) -> int:
    acc = broker.account()
    print(f"conta: {'DEMO' if acc.is_demo else 'NÃO-DEMO (real/contest)'} | id={acc.account_id} | "
          f"saldo={acc.balance:.2f} | {'HEDGING' if broker.is_hedging() else 'NETTING'}")
    configured = cfg.get("broker", {}).get("server_utc_offset_hours")
    for symbol in cfg["symbols"]:
        try:
            s = broker.symbol_spec(symbol)
        except ValueError as exc:
            print(f"{symbol}: INDISPONÍVEL ({exc})")
            return 2
        print(f"{symbol}: tick={s.tick_size} valor_tick={s.tick_value} vol_min={s.volume_min} "
              f"vol_step={s.volume_step} vol_max={s.volume_max}")
        est = broker.estimate_server_offset(symbol)
        print(f"  fuso do servidor estimado: {est if est is not None else 'indeterminado (mercado parado?)'} h"
              f" | configurado: {configured}")
        if est is not None and configured is not None and abs(est - float(configured)) > 1e-9:
            print("  ATENÇÃO: o fuso configurado difere do estimado")
    strategy = build_strategy(cfg, broker)
    blockers = guard(cfg, config_path, broker, strategy)
    print(f"estratégia: {strategy.name} hash={strategy.hash}")
    print("guarda de dinheiro real:", "OK para operar em demo" if not blockers else f"BLOQUEADO {blockers}")
    return 0 if not blockers else 3


def run(cfg: dict, config_path: str | Path, broker: MT5Broker, clock: Clock | None = None,
        max_steps: int | None = None, sleep: Callable[[float], None] = time.sleep) -> int:
    clock = clock or SystemClock()
    strategy = build_strategy(cfg, broker)
    blockers = guard(cfg, config_path, broker, strategy)
    if blockers:
        log.error("refusing to trade: %s", blockers)
        return 3
    journal = Journal(cfg.get("journal_db", "live/journal.sqlite"), clock, strategy.name)
    r = cfg.get("risk", {})
    risk = RiskManager(RiskConfig(**{k: v for k, v in r.items() if k in RiskConfig.__dataclass_fields__}))
    engine = Engine(broker, strategy, clock, build_calendar(cfg, strategy), journal, risk,
                    KillSwitch(cfg.get("killswitch_file", "live/STOP")), list(cfg["symbols"]),
                    volume=float(cfg.get("volume", 1)), alert=lambda m: log.warning("ALERT %s", m))
    engine.start()
    poll, steps, errors = float(cfg.get("poll_seconds", 5)), 0, 0
    feed_file, feed_every, feed_at = cfg.get("feed_file"), float(cfg.get("feed_every_s", 5)), 0.0
    try:
        while max_steps is None or steps < max_steps:
            steps += 1
            try:
                if guard(cfg, config_path, broker, strategy):   # account switched under us?
                    log.error("guard tripped during the run; stopping without new orders")
                    return 3
                acts = engine.step()
                errors = 0
                if acts:
                    log.info("step: %s", acts)
                if feed_file and time.monotonic() - feed_at >= feed_every:
                    feed_at = time.monotonic()
                    try:                       # the portal's live picture never stops the engine
                        from live.feed import build_feed, write_feed
                        write_feed(feed_file, build_feed(broker, strategy, cfg["symbols"][0], clock.now()))
                    except Exception as exc:
                        log.warning("live feed not written: %r", exc)
            except MT5Unavailable as exc:
                errors += 1
                log.error("MT5 unavailable (%d): %s", errors, exc)
            except Exception:
                errors += 1
                log.exception("engine step failed (%d)", errors)
            if errors >= MAX_CONSECUTIVE_ERRORS:
                log.error("too many consecutive errors; stopping")
                return 4
            if max_steps is None or steps < max_steps:
                sleep(poll)
    except KeyboardInterrupt:
        log.info("stopped by operator (positions keep their server-side stops)")
    finally:
        journal.close()
    return 0


def setup_logging(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    file_h = RotatingFileHandler(path, maxBytes=5_000_000, backupCount=10, encoding="utf-8")
    file_h.setFormatter(fmt)
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers[:] = [file_h, console]


def main(argv: list[str] | None = None, mt5_module: Any = None) -> int:
    ap = argparse.ArgumentParser(prog="live.run")
    ap.add_argument("--config", default="live/config/live.json")
    ap.add_argument("--env", default="live/.env")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    raw = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if not raw.get("broker", {}).get("attach"):
        load_env_file(args.env)          # never for an attached terminal: live/.env is another account
    cfg = load_config(args.config)
    setup_logging(cfg.get("log_file", "live/logs/live.log"))
    if mt5_module is None:
        import MetaTrader5 as mt5_module  # noqa: N813  (Windows only)
    broker = build_broker(cfg, mt5_module, require_offset=not args.check)
    try:
        broker.connect()
        return check(cfg, args.config, broker) if args.check else run(cfg, args.config, broker)
    except MT5Unavailable as exc:
        log.error("%s", exc)
        return 1
    finally:
        broker.shutdown()


if __name__ == "__main__":
    sys.exit(main())

"""Live view of the dry-run bots for the portal: what each bot did, and the price it did it in. Read-only.

Two feeds:
  bots_state()  one entry per frozen hypothesis: verdict (lab/dryrun.py), per-pair metrics, open positions with their
                unrealised result at the current price, and the last closed trades;
  live_chart()  candles of one pair (Binance PUBLIC klines, no key; the lab's own candle file when the network fails) with
                every bot's entries and exits on that pair, so the chart shows how each robot trades inside the asset.

Nothing here writes, starts a bot, sends an order or uses an exchange key. The public klines endpoint needs none.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from datetime import timezone
from pathlib import Path

from lab import dryrun, forward

ROOT = Path(__file__).parents[1]
TIMEFRAMES = {"15m": 900, "1h": 3600}
KLINES = "https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit={limit}"
CACHE_SECONDS = 4.0
_cache: dict[tuple, tuple[float, dict]] = {}
_lock = threading.Lock()


def clean(value):
    """JSON-safe copy: infinities and NaN (a profit factor with no losing trade) become null."""
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        return None
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


def _ts(value) -> float | None:
    parsed = forward._ts(value)
    return None if parsed is None else parsed.replace(tzinfo=timezone.utc).timestamp()


def fetch_klines(pair: str, tf: str, limit: int = 400) -> list[list[float]]:
    """[[unix_seconds, open, high, low, close, volume], ...] from Binance public data; raises on any failure."""
    url = KLINES.format(symbol=pair.replace("/", ""), tf=tf, limit=limit)
    request = urllib.request.Request(url, headers={"User-Agent": "trading-lab-live"})
    raw = json.load(urllib.request.urlopen(request, timeout=8))
    return [[int(k[0]) // 1000, float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in raw]


def disk_candles(pair: str, tf: str, limit: int = 400, root: Path = ROOT) -> list[list[float]]:
    import pandas as pd

    path = root / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-{tf}.feather"
    if not path.is_file():
        return []
    frame = pd.read_feather(path).tail(limit)
    return [[int(row.date.timestamp()), float(row.open), float(row.high), float(row.low), float(row.close), float(row.volume)]
            for row in frame.itertuples()]


def _bot_trades(hid: str, root: Path) -> dict[str, list[dict]]:
    out = {}
    for key in forward.pair_keys(hid, root):
        trades, _ = forward.read_database(root / forward.database_path(hid, key))
        out[forward.PAIR_KEYS.get(key, key)] = trades
    return out


def _unrealised(trade: dict, price: float | None) -> float | None:
    return None if not price or not trade.get("open_rate") else 100.0 * (price / trade["open_rate"] - 1.0)


def bots_state(root: Path = ROOT, prices: dict[str, float] | None = None) -> dict:
    """Every frozen bot: verdict, metrics, open positions (with the unrealised result when a price is known)."""
    cfg = dryrun.load_config()
    prices = prices or {}
    bots = []
    for hid in dryrun.frozen_hypotheses(root):
        try:
            result = dryrun.evaluate_hypothesis(hid, cfg, root)
            freeze = json.loads((root / "research" / "forward" / f"{hid}-freeze.json").read_text(encoding="utf-8"))
            open_trades, closed_trades = [], []
            for pair, trades in _bot_trades(hid, root).items():
                for t in trades:
                    if t.get("is_open"):
                        open_trades.append({"pair": pair, "open_date": str(t["open_date"])[:16], "open_rate": t["open_rate"],
                                            "stake": t["stake_amount"], "unrealised_pct": _unrealised(t, prices.get(pair))})
                for c in forward.closed_as_backtest_trades(trades):
                    closed_trades.append({"pair": pair, "open_date": c["open_date"][:16], "close_date": c["close_date"][:16],
                                          "profit_pct": 100 * c["profit_ratio"], "profit": c["profit_abs"],
                                          "reason": c.get("exit_reason"), "minutes": c.get("trade_duration")})
            closed_trades.sort(key=lambda t: t["close_date"], reverse=True)
            pairs = {p: {**m, "open": sum(1 for t in open_trades if t["pair"] == p)} for p, m in result["per_pair"].items()}
            bots.append({"id": hid, "strategy": freeze["strategy"]["class"], "frozen_at": freeze["frozen_at_utc"][:16],
                         "verdict": result["verdict"], "reasons": result["reasons"], "pooled": result["pooled"],
                         "wallet": result["wallet"], "pairs": pairs, "open": open_trades, "closed": closed_trades[:60],
                         "need_trades": cfg["min_closed_trades"], "need_days": cfg["min_days"]})
        except Exception as error:  # one broken bot must not hide the others
            bots.append({"id": hid, "error": f"{type(error).__name__}: {error}"[:200]})
    return {"bots": bots}


def live_chart(pair: str, tf: str, root: Path = ROOT, *, fetch=fetch_klines) -> dict:
    """Candles plus every bot's trades on `pair`. Cached a few seconds so several open tabs do not hammer Binance."""
    if tf not in TIMEFRAMES:
        raise ValueError("timeframe must be 15m or 1h")
    if pair not in forward.PAIR_KEYS.values():
        raise ValueError("unknown pair")
    with _lock:
        hit = _cache.get((pair, tf))
        if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
            return hit[1]
    source, error = "binance", None
    try:
        candles = fetch(pair, tf)
    except Exception as exc:
        candles, source, error = disk_candles(pair, tf, root=root), "disco (sem rede para a Binance)", f"{type(exc).__name__}"
    last = candles[-1][4] if candles else None
    bots = []
    for hid in dryrun.frozen_hypotheses(root):
        try:
            trades = _bot_trades(hid, root).get(pair, [])
        except Exception:
            continue
        marks = []
        for t in trades:
            opened = _ts(t["open_date"])
            if opened is None:
                continue
            closed = None if t.get("is_open") else _ts(t.get("close_date"))
            marks.append({"open_ts": opened, "close_ts": closed, "open_rate": t["open_rate"], "close_rate": t.get("close_rate"),
                          "is_open": bool(t.get("is_open")),
                          "profit_pct": None if t.get("is_open") or t.get("close_profit") is None else 100 * float(t["close_profit"]),
                          "profit": None if t.get("is_open") else t.get("close_profit_abs"),
                          "unrealised_pct": _unrealised(t, last) if t.get("is_open") else None, "stake": t.get("stake_amount")})
        if any(forward.PAIR_KEYS.get(k) == pair for k in forward.pair_keys(hid, root)):
            bots.append({"id": hid, "trades": marks})
    payload = {"pair": pair, "tf": tf, "step": TIMEFRAMES[tf], "source": source, "error": error, "last_price": last,
               "served_at": int(time.time()), "candles": candles, "bots": bots,
               "pairs": sorted({p for h in dryrun.frozen_hypotheses(root) for p in
                                (forward.PAIR_KEYS.get(k, k) for k in forward.pair_keys(h, root))})}
    with _lock:
        _cache[(pair, tf)] = (time.monotonic(), payload)
    return payload


def last_prices(root: Path = ROOT, *, fetch=None) -> dict[str, float]:
    """Last traded price of every pair a frozen bot trades (Binance public ticker); {} when the network fails."""
    def ticker(pair: str) -> float:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=" + pair.replace("/", "")
        return float(json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "trading-lab-live"}), timeout=6))["price"])

    fetch = fetch or ticker
    pairs = sorted({forward.PAIR_KEYS.get(k, k) for h in dryrun.frozen_hypotheses(root) for k in forward.pair_keys(h, root)})
    prices = {}
    for pair in pairs:
        with _lock:
            hit = _cache.get(("price", pair))
        if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
            prices[pair] = hit[1]["price"]
            continue
        try:
            price = fetch(pair)
        except Exception:
            continue
        prices[pair] = price
        with _lock:
            _cache[("price", pair)] = (time.monotonic(), {"price": price})
    return prices

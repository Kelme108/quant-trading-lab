"""Dry-run (forward) evidence collection: freeze a strategy by hash, then read what the bots did.

Nothing here starts a bot, edits a protected file or places an order. The bots are started by the user with
`docker compose -f docker-compose.forward.yml up -d`.

Freeze: SHA-256 of the strategy, the per-pair overlays, the forward compose, the base config and the base compose, the
image tag and the git commit, written to research/forward/<H>-freeze.json. `check_freeze` fails when any of them
changed, so a bot is never trusted after an edit.

Read: the Freqtrade SQLite of each bot, opened read-only. The report is about EXECUTION (fills, slippage, fees,
missed entries). It does not aggregate returns unless asked, and then it says "monitoring, not evaluated": the formal
evaluation is the prospective holdout (lab/config/holdout.json). A signal-by-signal comparison with a backtest over
the same days is deferred to that evaluation, because a backtest over those days would read the holdout.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from lab import costs

ROOT = Path(__file__).parents[1]
PAIR_KEYS = {"btc": "BTC/USDT", "eth": "ETH/USDT", "bnb": "BNB/USDT"}
COMPOSE = "docker-compose.forward.yml"
BASE_FILES = ("user_data/config.dryrun.json", "docker-compose.yml")
LABEL = ("Dry-run como coleta de evidência: NÃO validada; sem evidência prospectiva; não é aprovação, não é holdout "
         "e não consome a leitura da validação.")
RULES = (
    "O resultado do dry-run é monitoramento; a avaliação formal é o holdout (>= 2027-04-21, >= 30 trades, protocolo v3 8.3).",
    "Mudar regra, parâmetro ou exposição depois de ver o forward cria uma hipótese nova (novo ID, relógio zerado, N inclui a anterior).",
    "Relatórios de execução podem ser vistos a qualquer momento; retorno agregado leva o rótulo 'monitoramento, não avaliado'.",
    "O bot não reinicia com arquivo alterado: a checagem de hash precisa passar antes de qualquer relatório.",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tag(hypothesis_id: str) -> str:
    """H-009 -> h009 (the name used in overlay files and database names)."""
    return "h" + hypothesis_id.split("-")[1]


def overlay_path(hypothesis_id: str, key: str) -> str:
    return f"forward/config.{tag(hypothesis_id)}.{key}.json"


def database_path(hypothesis_id: str, key: str) -> str:
    return f"user_data/tradesv3.forward.{tag(hypothesis_id)}.{key}.sqlite"


def compose_path(hypothesis_id: str, root: Path = ROOT) -> str:
    """docker-compose.forward.<tag>.yml when the hypothesis has its own file, else the shared one (H-009).

    One compose per hypothesis keeps the freezes independent: adding bots for a new hypothesis never changes the
    bytes of a file an older freeze hashed."""
    own = f"docker-compose.forward.{tag(hypothesis_id)}.yml"
    return own if (root / own).is_file() else COMPOSE


def pair_keys(hypothesis_id: str, root: Path = ROOT) -> list[str]:
    """The pairs this hypothesis runs on: those with an overlay file (all three when none exists yet)."""
    present = [key for key in PAIR_KEYS if (root / overlay_path(hypothesis_id, key)).is_file()]
    return present or list(PAIR_KEYS)


def find_strategy(hypothesis_id: str, root: Path = ROOT) -> Path:
    number = int(hypothesis_id.split("-")[1])
    found = sorted((root / "user_data" / "strategies").glob(f"*_H{number:03d}_v*.py"))
    if not found:
        raise FileNotFoundError(f"{hypothesis_id}: no strategy file in the strategy path (a dry-run needs the active file)")
    return found[-1]


def tracked_files(hypothesis_id: str, root: Path = ROOT) -> list[str]:
    """Every file whose bytes decide what the bots do."""
    files = [str(find_strategy(hypothesis_id, root).relative_to(root)).replace("\\", "/"),
             compose_path(hypothesis_id, root), *BASE_FILES]
    files += [overlay_path(hypothesis_id, key) for key in pair_keys(hypothesis_id, root)]
    return files


def _git(args: list[str], root: Path) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def image_tag(root: Path = ROOT, compose: str = COMPOSE) -> str:
    for line in (root / compose).read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("image:"):
            return line.split(":", 1)[1].strip()
    raise ValueError(f"no image in {compose}")


def build_freeze(hypothesis_id: str, root: Path = ROOT, now: str | None = None) -> dict:
    """The freeze record. Refuses uncommitted files: the recorded commit must contain exactly the hashed bytes."""
    files = tracked_files(hypothesis_id, root)
    missing = [f for f in files if not (root / f).is_file()]
    if missing:
        raise FileNotFoundError(f"missing: {missing}")
    dirty = _git(["status", "--porcelain", "--", *files], root)
    if dirty:
        raise ValueError("these files are not committed, so the freeze would not match a commit:\n" + dirty)
    strategy_file = files[0]
    exposures = {key: json.loads((root / overlay_path(hypothesis_id, key)).read_text(encoding="utf-8"))["tradable_balance_ratio"]
                 for key in pair_keys(hypothesis_id, root)}
    return {
        "hypothesis": hypothesis_id, "label": LABEL, "rules": list(RULES),
        "frozen_at_utc": now or datetime.now(timezone.utc).isoformat(),
        "git_commit": _git(["rev-parse", "HEAD"], root), "image": image_tag(root, compose_path(hypothesis_id, root)),
        "strategy": {"class": Path(strategy_file).stem, "file": strategy_file, "sha256": sha256_file(root / strategy_file)},
        "exposure_by_pair": {PAIR_KEYS[k]: v for k, v in exposures.items()},
        "databases": {PAIR_KEYS[k]: database_path(hypothesis_id, k) for k in pair_keys(hypothesis_id, root)},
        "files": {f: sha256_file(root / f) for f in files},
    }


def freeze_path(hypothesis_id: str, root: Path = ROOT) -> Path:
    return root / "research" / "forward" / f"{hypothesis_id}-freeze.json"


def check_freeze(hypothesis_id: str, root: Path = ROOT) -> list[str]:
    """Problems found (empty = the files are byte-identical to the freeze). Also checks the files are committed."""
    path = freeze_path(hypothesis_id, root)
    if not path.is_file():
        return [f"{hypothesis_id}: no freeze record at {path.relative_to(root)}"]
    frozen = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    for name, digest in frozen["files"].items():
        target = root / name
        if not target.is_file():
            problems.append(f"missing {name}")
        elif sha256_file(target) != digest:
            problems.append(f"changed since the freeze: {name}")
    if not problems:
        dirty = _git(["status", "--porcelain", "--", *frozen["files"]], root)
        if dirty:
            problems.append("uncommitted changes in frozen files:\n" + dirty)
    return problems


# --- reading the bots -------------------------------------------------------

def _connect_ro(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def read_database(db: Path) -> tuple[list[dict], list[dict]]:
    """(trades, orders) from a Freqtrade SQLite, read-only. ([], []) when the file does not exist yet."""
    if not db.is_file():
        return [], []
    conn = _connect_ro(db)
    try:
        trades = [dict(r) for r in conn.execute("SELECT * FROM trades ORDER BY open_date")]
        orders = [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY order_date")]
    finally:
        conn.close()
    return trades, orders


def _ts(value) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text.split("+")[0], fmt)
        except ValueError:
            continue
    return None


def closed_as_backtest_trades(trades: list[dict]) -> list[dict]:
    """Closed bot trades in the shape lab/analytics.py and lab/tradereview.py read."""
    out = []
    for t in trades:
        if t.get("is_open") or t.get("close_profit") is None:
            continue
        opened, closed = _ts(t["open_date"]), _ts(t["close_date"])
        out.append({
            "open_date": str(t["open_date"]), "close_date": str(t["close_date"]), "open_rate": t["open_rate"],
            "close_rate": t["close_rate"], "min_rate": t.get("min_rate"), "max_rate": t.get("max_rate"),
            "profit_ratio": float(t["close_profit"]), "profit_abs": float(t["close_profit_abs"] or 0.0),
            "stake_amount": t["stake_amount"], "fee_open": t["fee_open"], "fee_close": t["fee_close"],
            "exit_reason": t.get("exit_reason"),
            "trade_duration": (closed - opened).total_seconds() / 60.0 if opened and closed else None,
        })
    return out


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def execution_quality(trades: list[dict], orders: list[dict], scenario: str = "base") -> dict:
    """Fills, slippage, fees and missed entries. Slippage is signed against what the bot asked for: positive = paid
    more on entry / received less on exit (worse). Compared with the per-side cost the backtest scenario assumes."""
    entry_slip, exit_slip, fee_open, fee_close = [], [], [], []
    for t in trades:
        if t.get("open_rate") and t.get("open_rate_requested"):
            entry_slip.append(t["open_rate"] / t["open_rate_requested"] - 1.0)
        if not t.get("is_open") and t.get("close_rate") and t.get("close_rate_requested"):
            exit_slip.append(1.0 - t["close_rate"] / t["close_rate_requested"])
        if t.get("fee_open") is not None:
            fee_open.append(float(t["fee_open"]))
        if not t.get("is_open") and t.get("fee_close") is not None:
            fee_close.append(float(t["fee_close"]))
    entries = [o for o in orders if o.get("ft_order_side") == "buy"]
    missed = [o for o in entries if o.get("status") in ("canceled", "cancelled", "expired", "rejected") and not (o.get("filled") or 0)]
    latency = []
    for o in entries:
        placed, filled = _ts(o.get("order_date")), _ts(o.get("order_filled_date"))
        if placed and filled and filled >= placed:
            latency.append((filled - placed).total_seconds() / 60.0)
    assumed = costs.get_scenario(scenario)
    observed_side = [fee + max(slip, 0.0) for fee, slip in zip(fee_open, entry_slip)]
    return {
        "trades": len(trades), "closed": sum(1 for t in trades if not t.get("is_open")),
        "open": sum(1 for t in trades if t.get("is_open")),
        "entry_orders": len(entries), "entry_orders_not_filled": len(missed),
        "entry_slippage_mean": _mean(entry_slip), "entry_slippage_worst": max(entry_slip) if entry_slip else None,
        "exit_slippage_mean": _mean(exit_slip), "exit_slippage_worst": max(exit_slip) if exit_slip else None,
        "fee_open_mean": _mean(fee_open), "fee_close_mean": _mean(fee_close),
        "fill_latency_minutes_mean": _mean(latency), "fill_latency_minutes_max": max(latency) if latency else None,
        "assumed_scenario": scenario, "assumed_cost_per_side": assumed.effective_fee_per_side,
        "observed_entry_cost_per_side_mean": _mean(observed_side),
    }


def render_markdown(hypothesis_id: str, by_pair: dict[str, dict], frozen: dict, returns: dict | None = None) -> str:
    def p(value, digits=3, scale=100.0, suffix="%") -> str:
        return "–" if value is None else f"{value * scale:.{digits}f}{suffix}"

    lines = [f"# Dry-run: qualidade de execução de {hypothesis_id}", "", frozen["label"], "",
             f"Congelada em {frozen['frozen_at_utc']} (commit `{frozen['git_commit'][:10]}`, imagem `{frozen['image']}`). "
             "Os arquivos conferem com o congelamento.", "",
             "| Par | Trades (fechados/abertos) | Ordens de entrada | Não preenchidas | Slippage médio na entrada | Pior entrada | Slippage médio na saída | Taxa média (entrada) | Custo/lado assumido (backtest) | Custo/lado observado na entrada | Latência média de preenchimento |",
             "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for pair, q in by_pair.items():
        lat = "–" if q["fill_latency_minutes_mean"] is None else f"{q['fill_latency_minutes_mean']:.1f} min"
        lines.append(f"| {pair} | {q['closed']}/{q['open']} | {q['entry_orders']} | {q['entry_orders_not_filled']} | "
                     f"{p(q['entry_slippage_mean'])} | {p(q['entry_slippage_worst'])} | {p(q['exit_slippage_mean'])} | "
                     f"{p(q['fee_open_mean'])} | {p(q['assumed_cost_per_side'])} | {p(q['observed_entry_cost_per_side_mean'])} | {lat} |")
    lines += ["", "Slippage positivo = pior do que o preço pedido. A comparação sinal a sinal com o backtest fica para a avaliação do holdout "
              "(rodar um backtest sobre esses dias leria o holdout).", ""]
    if returns is not None:
        lines += ["## Retorno agregado (monitoramento, NÃO avaliado)", "",
                  "Nenhuma regra, parâmetro ou exposição pode ser alterado com base nestes números; isso criaria uma hipótese nova.", ""]
        for pair, r in returns.items():
            lines.append(f"- {pair}: {r['closed']} trades fechados, lucro {r['net_profit_abs']:.2f} USDT")
        lines.append("")
    lines += ["## Regras do forward", ""] + [f"{i}. {rule}" for i, rule in enumerate(frozen["rules"], 1)] + [""]
    return "\n".join(lines)

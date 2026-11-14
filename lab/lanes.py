"""Market lanes of the lab: Binance spot (the original one) and Binance USDⓈ-M perpetual futures in dry-run.

Owner decision D2 (2026-11-13), specification in docs/faixa-futuros.md (pre-registered before any futures backtest):
- leverage 1x: a strategy may not define `leverage()` (lab/strategy_check.py forbids it in every lane), and Freqtrade's
  default is 1; isolated margin; long AND short, both sides written in the rule before it is tested;
- costs: the same slippage and spread as spot, only the fee changes (taker 0.05% per side, 0.045% paying in BNB,
  https://www.binance.com/support/faq/360033544231); funding is charged by Freqtrade from the downloaded history;
- data: `freqtrade download-data --trading-mode futures` into user_data/data/binance/futures/;
- the protected spot config (user_data/config.dryrun.json) is untouched: futures runs use their own config file.
Everything defaults to the spot lane, so every existing call behaves exactly as before.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parents[1]


@dataclass(frozen=True)
class Lane:
    name: str
    config: str               # file name under user_data/
    fee_per_side: float       # exchange fee, with the BNB discount the lab assumes in both lanes
    pair_suffix: str          # Freqtrade pair name suffix (":USDT" for USDⓈ-M perpetuals)
    can_short: bool           # whether a strategy of this lane may sell short
    data_subdir: str          # under user_data/data/binance/
    candle_suffix: str        # file name suffix of the candles Freqtrade stores
    splits: str               # file name under lab/config/

    def pair(self, base_pair: str) -> str:
        """'BTC/USDT' -> the lane's Freqtrade name ('BTC/USDT' or 'BTC/USDT:USDT')."""
        return base_pair if base_pair.endswith(self.pair_suffix) or not self.pair_suffix else base_pair + self.pair_suffix

    def feather_path(self, base_pair: str, timeframe: str = "1h", root: Path = ROOT) -> Path:
        name = self.pair(base_pair).replace("/", "_").replace(":", "_")
        folder = root / "user_data" / "data" / "binance"
        if self.data_subdir:
            folder = folder / self.data_subdir
        return folder / f"{name}-{timeframe}{self.candle_suffix}.feather"


SPOT = Lane(name="spot", config="config.dryrun.json", fee_per_side=0.00075, pair_suffix="", can_short=False,
            data_subdir="", candle_suffix="", splits="splits.json")
FUTURES = Lane(name="futures", config="config.futures.dryrun.json", fee_per_side=0.00045, pair_suffix=":USDT",
               can_short=True, data_subdir="futures", candle_suffix="-futures", splits="splits_futures.json")
LANES = {SPOT.name: SPOT, FUTURES.name: FUTURES}


MARKET_RE = re.compile(r'^LAB_MARKET\s*=\s*["\']([a-z]+)["\']', re.M)


def strategy_market(strategy_file: Path) -> str:
    """The lane a strategy file declares with a module constant `LAB_MARKET = "futures"`; "spot" when it has none, so
    every strategy written before the futures lane stays spot. The constant is part of the strategy's frozen bytes."""
    found = MARKET_RE.search(Path(strategy_file).read_text(encoding="utf-8"))
    return get(found.group(1)).name if found else SPOT.name


def get(name: str) -> Lane:
    try:
        return LANES[name]
    except KeyError as exc:
        raise ValueError(f"unknown lane {name!r}; expected one of {sorted(LANES)}") from exc

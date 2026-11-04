"""One-off: register H-018 (Donchian Ensemble, protocol v3) BEFORE any run. Writes research/proposals/H-018.json,
validates it with lab/proposals.py and registers the hypothesis. Nothing is executed."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import proposals, registry, runner  # noqa: E402

HID = "H-018"
RULE = (
    "Protocol docs/protocolo-validacao-v3.md section 2.2. Signals come from CLOSED daily candles (merge_informative_pair, ffill, as in Sma200Baseline) and are "
    "executed on the 1h chart at the next open. Four members (N, M) = (20,10), (55,20), (100,50), (200,100). Member state is a two-level latch computed on the daily "
    "frame: ON when daily close > max(daily high of the N days before the current day) ; OFF when daily close < min(daily low of the M days before the current day) ; "
    "otherwise the previous state is kept ; undefined (NaN) channel values give OFF. Channels use rolling(N).max().shift(1) and rolling(M).min().shift(1) on the daily frame "
    "before the merge. ENTRY: at least 2 of the 4 members are ON and the strategy is flat (level entry, including the first candle of a split if already ON). "
    "EXIT: fewer than 2 members ON. No stop-loss (stoploss attribute -0.99 only to satisfy the engine contract), no take-profit, no sizing hooks, no cooldown. "
    "Exposure is the fixed share chosen by the lab rule (bootstrap.choose_exposure on exploration trades). Sensitivities reported, never selectable: threshold 1 and 3 of 4, "
    "each member alone, the vote without member (20,10), thresholds counted in the DSR N. Warm-up: 400 bars (daily candles; the state at the first day of a split was verified "
    "equal to the full-history state for 400, 600 and 900 days on BTC, ETH and BNB)."
)
RATIONALE = (
    "Mechanism: trend-following profits from slow reaction to information and from the persistence of large moves (time-series momentum). A single Donchian lookback is "
    "the main source of overfitting in channel rules; voting across four fixed horizons removes the choice of one lookback and is how the cited crypto study combines "
    "channel models. Expected trades: roughly 10 to 30 per pair in the exploration window; the minimum of 30 trades per pair may not be met (protocol D-2 keeps the gate, "
    "so an inconclusive result is possible and is reported as such). Round trip cost 0.35 percent at base is small against multi-week moves, but the member (20,10) trades "
    "most and is the most cost sensitive. This is NOT volatility sizing: that is a non-decisive overlay in the protocol. Honest caveat: the family was chosen after seeing that "
    "trend rules worked in this history, and the cited study could not be read in full here."
)
NOVELTY = (
    "H-002 was a single 20/10 channel on 1h bars with a 10 percent stop (rejected: drawdown 60 to 98 percent). H-007, H-009 and H-017 are 1h breakout rules with a regime gate. "
    "This rule works on daily channels, four horizons, a majority vote and no stop; it is the closest relative of Sma200Baseline at the long members, so redundancy with it is "
    "expected and will be measured."
)
PROPOSAL = {
    "hypothesis_id": HID,
    "family": "DonchianEnsemble",
    "title": "Donchian ensemble: majority vote of four daily channels, no stop",
    "ex_ante_rule": RULE,
    "parameters": {"n1": 20, "m1": 10, "n2": 55, "m2": 20, "n3": 100, "m3": 50, "n4": 200, "m4": 100,
                   "vote_threshold": 2, "warmup_daily_bars": 400, "stop": "none"},
    "rationale": RATIONALE,
    "novelty_vs_tried": NOVELTY,
    "sources": [
        {"title": "Catching Crypto Trends (Zarattini, Pagani, Barbon), Swiss Finance Institute RP 25-80",
         "url": "https://econpapers.repec.org/RePEc:chf:rpseri:rp2580"},
        {"title": "A Century of Evidence on Trend-Following Investing (Hurst, Ooi, Pedersen), AQR",
         "url": "https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing"},
        {"title": "Time Series Momentum (Moskowitz, Ooi, Pedersen), SSRN",
         "url": "https://papers.ssrn.com/abstract=2089463"},
    ],
    "timeframe": "1h",
    "data_visible_at_proposal": "Protocol v3 and exploration-only audit facts; no validation or holdout result was used for this rule.",
}


def main() -> int:
    conn = registry.connect()
    errors = proposals.validate_proposal(
        PROPOSAL, expected_id=HID, enabled_timeframes=runner.enabled_timeframes(),
        variants_in_family=lambda f: registry.count_variants_in_family(conn, f),
        max_variants_per_family=3,
    )
    if errors:
        print("INVALID:", errors)
        return 2
    if registry.get_hypothesis(conn, HID) is not None:
        print("already registered")
        return 0
    path = proposals.proposal_path(HID)
    path.write_text(json.dumps(PROPOSAL, indent=2, ensure_ascii=False), encoding="utf-8")
    registry.add_hypothesis(
        conn, hypothesis_id=HID, family=PROPOSAL["family"], ex_ante_rule=RULE,
        proposed_at_utc=datetime.now(timezone.utc).isoformat(),
        data_visible_at_proposal=PROPOSAL["data_visible_at_proposal"], status="proposed",
        notes=PROPOSAL["title"] + ". Protocol v3 (docs/protocolo-validacao-v3.md); decisions D-1..D-10 per the user's 2026-11-04 'use all proposals'; "
              "gates.json/portfolio.json still PROPOSED, so every decision is provisional.")
    registry.sync_ledger_markdown(conn)
    registry.dump_sql(conn)
    print("registered", HID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

Target of the next proposal: an improvement of H-009 (WeeklyBreakoutRegime). It must be a NEW hypothesis (a child of H-009, reusing family name `WeeklyBreakoutRegime` only if the mechanism below is a variant of H-009's rule). H-009's own rule is not changed.

Every number below is from the EXPLORATION split (per-pair windows in lab/config/splits.json), base cost unless stated, exposure 0.25 as calibrated. Source: research/audit/H-009-exploration-metrics.json and research/experiments/H-009-exploration/. Provisional: gates.json is still PROPOSED. No validation or holdout data was used.

## What H-009 does (see its rule above)
Breakout of the prior 168-bar high while SMA720 > SMA2160 and close > SMA720; exit below the prior 72-bar low or below SMA720; -6% stop; 24-bar cooldown.

## Observed failure mechanisms (exploration only)
1. Profit is concentrated in the 2020-21 bull cycle. Return by cycle, BTC / ETH / BNB:
   2018: -2% / +9% / -5%; 2019: +21% / +10% / +26%; 2020-21: +32% / +36% / +115%; 2022: 0% (no trades) / -2% / -7%; 2023+ (to the end of exploration): +9% / 0% / -2%.
2. Low hit rate with fixed-size stop losses. Win rate 38% / 31% / 31% (Wilson 95% CI 27-51% / 22-42% / 22-42%). Stop-loss exits: 9 of 58 (BTC), 22 of 81 (ETH), 22 of 80 (BNB); the stop fills near -6.3%. The other exits are the 72-bar low or loss of the SMA720 regime.
3. Long losing streaks after the 2021 peak: longest run of losing trades 9 / 14 / 11 (BTC / ETH / BNB). On ETH and BNB the longest run lasts about 14-17 months, from late 2021 to early 2023, with failed breakouts that are stopped out quickly (some within 1-3 hours of entry) and quick re-entries.
4. One trade carries BNB: the 2021-01-29 trade is 80% of BNB base profit; without it BNB profit falls from 133.6 to 27.0. Bootstrap 95% CI of the total return: BTC [0.21, 2.20], ETH [-0.00, 1.95], BNB [-0.08, 9.16].
5. Weak differentiation from a plain trend filter: in position, H-009 overlaps with Sma200Baseline 89-93% of the time, and the daily-return correlation is 0.48 (BTC), 0.43 (ETH), 0.71 (BNB). At base_2x costs and the same exposure, annualised daily Sharpe of H-009 vs buy-and-hold vs Sma200Baseline: BTC 1.11 / 0.89 / 0.66; ETH 0.58 / 0.83 / 0.71; BNB 0.59 / 1.32 / 0.81. H-009 beats both only on BTC.
6. Drawdown: gate drawdown (closed trades) 7.2% / 18.5% / 14.5% at base; mark-to-market drawdown on the hourly curve 11% / 25% / 32% (informative only, not a gate).

## Constraints the proposal must respect
- The mechanism fixed must be named explicitly and tied to one of items 1-5 above (for example failed breakouts in non-trending phases, or the choice of exit), not to a better-looking backtest.
- Round, ex-ante parameters; no tuning on these results; the same rule on BTC, ETH and BNB.
- Declare the complete grid of values to be explored before any run (size small; each cell counts as a test and the variant cap is 3 per family).
- Warm-up at most 4500 bars, stated literally as 'Warm-up: N bars'. At least 30 trades per pair are needed, so a filter must not be so restrictive that it lands below that (H-009 has 58 / 81 / 80).
- Spot, long only, 1h, native fixed stop, no custom_stake_amount, no leverage.
- Win rate is not a criterion. Success will be judged by the existing gates plus, on the in-sample window only, DSR >= 0.95, PBO <= 0.5, parameter plateau, and Sharpe above buy-and-hold and above Sma200Baseline at 2x costs.

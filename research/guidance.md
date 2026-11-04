Focus this search on drawdown control and robustness, not on maximizing historical return.

Why: H-002 lost money (about 800 trades per pair, cost-dominated). H-005 returned +500% to +880% but its maximum drawdown was 43% to 51%, against the 25% gate. Its worst drawdown on each pair was a streak of 8 to 13 consecutive losing trades (average loss 6% to 8% each, whole balance per trade) in a bear or range market after the 2021 peak, with at most one winner inside it. Do not repeat that pattern.

Guidelines:
1. Look for risk-control mechanisms: trend or regime filters, entry confirmation, volatility filters, exit conditions. Each must have a stated reason tied to the failure above; no unjustified indicator combinations, no parameter tuning.
2. Aim for max drawdown below 25% in all four cost scenarios with positive expected return. Remember that with a whole balance per trade, N consecutive losses of L% each must stay under the 25% ceiling.
3. Keep trade count in mind: fewer than 30 trades in a split is "inconclusive", and a filter that is too restrictive will land there (H-004 had 13 to 16 trades). Equally, very frequent signals are eaten by costs (H-002).
4. The same rule and parameters must work on BTC, ETH and BNB. No per-pair tuning.
5. Spot, long only, 1h. Sizing methods such as custom_stake_amount are forbidden by the strategy check, so risk must be controlled by entries and exits.
6. Respect the variant cap of 3 per family. Prefer a new family over spending a variant of a family that already failed, unless you can name the specific mechanism that the variant fixes.
7. In the proposal rationale, state the technical justification, the expected mechanism of risk reduction, and objective success criteria (the existing gates), before anything is implemented.

The gates, limits and protocol are unchanged. Do not design the rule to make approval easier; design it to be a strategy that could survive the validation split, which you cannot see.

Technical limit learned from H-006: Freqtrade refuses any strategy whose warm-up (startup_candle_count) is more than 4999 candles on Binance 1h ("requires 5520 candles ... more than 5x (4999) the amount Binance provides"). H-006 needed 5520 (a 4800-bar SMA) and the backtest never started. Keep every lookback, and the warm-up, at or below about 4500 bars (about 187 days); a 200-day mean is not available.

The proposal's ex_ante_rule must state its warm-up literally as 'Warm-up: N bars' (the longest lookback plus any slope lag, e.g. SMA(4000) with a 300-bar slope = 4300). A proposal that omits it, or states more than 4500, is rejected before it is registered; the developer's startup_candle_count is checked against the same limit.

Lesson from H-003 (Bollinger mean reversion with RSI and a long-term filter, now tested): 50 to 71 trades per pair, and it lost money on BTC (-15%) and ETH (-20%) at the base cost, with drawdowns of 32% to 43%. It made +49% on BNB with a 17.7% drawdown at base (30% at stress). So a rule that works on one pair does not generalize; require the same rule to hold on all three. It also failed the recursive gate on every pair with startup_candle_count = 200, so size the warm-up for recursive indicators (RSI, EMA, Wilder smoothing) generously, within the 4500 limit.

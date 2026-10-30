# Risk assessment: H-005 (VolatilitySqueezeBreakout), exploration split

Sources: `research/experiments/H-005-exploration/facts.json` (called "facts" below), `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv` (same directory), `research/proposals/H-005.json`, `lab/config/gates.json`, `lab/config/portfolio.json`, and `research/experiments/H-004-exploration/trades-btc-usdt.csv` for overlap.

I counted the losing streaks and date spans by hand from the trade lists. Treat them as approximate. I did not run any code.

## 1. Drawdown
The gate ceiling is 25% in every cost scenario (`gates.json`, max_drawdown.max_ratio 0.25). All 12 pair/scenario cells fail it by a wide margin (facts, `max_drawdown_pct__*`).

| Pair | Optimistic | Base | Conservative | Stress |
|---|---|---|---|---|
| BTC/USDT | 49.05% | 50.12% | 51.19% | 54.27% |
| ETH/USDT | 49.55% | 50.63% | 51.68% | 54.72% |
| BNB/USDT | 42.04% | 42.92% | 43.80% | 46.36% |

The best case (BNB, optimistic) is still about 1.7 times the ceiling. Cost scenario changes drawdown by only about 5 points, so drawdown is a property of the strategy and not of the cost assumptions.

Losing stretches, from the trade lists (base scenario, dates are open to close):
- **BTC:**
  - Longest run: 7 consecutive losers, opened 2022-03-22 to closed 2023-08-17 (about 17 months), losing about 181 quote in total.
  - The last winner before it closed 2021-11-18, and the next winner opened 2023-10-02.
  - The 2021-02-17 to 2021-09-20 stretch has 6 consecutive stop-outs or small losses, about 238 quote.
- **ETH:**
  - 8 consecutive losers, opened 2021-11-25 to closed 2022-11-08 (about 11.5 months), about 473 quote lost.
  - That is close to the whole base-scenario profit of 507 quote. A second run of 5 losers falls in 2023-04 to 2023-12.
- **BNB:**
  - 10 consecutive losers, opened 2021-12-23 to closed 2023-11-21 (about 23 months), about 359 quote lost.
  - An earlier run of 9 losers runs from 2018-02-15 to 2019-01-28 (about 11.5 months), but it is small in quote terms.
- Many of the losses are fixed-stop exits. The `profit_ratio` on stop_loss rows is about -8.32%, which matches the 8% stop plus costs. The strategy loses at the stop level often and relies on rare large winners.

## 2. Cost sensitivity
Net profit (quote) from facts, `net_profit_quote__*`:

| Pair | Optimistic | Base | Conservative | Stress | Optimistic to stress |
|---|---|---|---|---|---|
| BTC | 549.5 | 520.4 | 492.3 | 415.9 | -24.3% |
| ETH | 540.7 | 507.2 | 475.5 | 389.9 | -27.9% |
| BNB | 933.1 | 879.2 | 827.9 | 689.5 | -26.1% |

- About 4.3 quote per trade is lost from optimistic to stress on BTC (133.6 over 31 trades). This is a moderate decline.
- The step from conservative to stress is steeper than the earlier steps. BTC loses 29.1 and 28.0 in the first two steps and 76.5 in the last.
- A break-even cost cannot be read from these numbers. I did not read the fee and slippage values behind each scenario, and profit is still positive in the harshest scenario tested. Break-even lies beyond the stress scenario.
- Headline profit staying positive hides thin margins once the best trade is removed (see section 3). The excl-best-trade figures at stress:
  - BNB: 3.0 (barely above zero).
  - ETH: 22.5.
  - BTC: 91.9.

## 3. Concentration
**Dependence on a few trades.**
- Profit excluding the best trade, base scenario (facts, `net_profit_excl_best_trade__base`):

| Pair | Net profit | Excluding best trade | Largest single trade (CSV) |
|---|---|---|---|
| BTC | 520.4 | 129.8 | +408 (2020-10-08 to 2021-01-22) |
| ETH | 507.2 | 51.1 | +412 (2020-10-09 to 2021-02-23) |
| BNB | 879.2 | 27.1 | +624 (2020-12-14 to 2021-03-25) |

- The best trade is a large share of profit: roughly 75% on BTC and about 90% or more on ETH and BNB. These figures are approximate because the gate metric may be computed differently from the CSV `profit_abs`.
- The two largest trades together exceed total base profit on all three pairs. For BTC: 408 + 165 = 573 against 520. For ETH: 412 + 366 = 778 against 507. For BNB: 624 + 414 = 1038 against 879.
- Roughly 8 to 11 of the 31 to 36 trades per pair are winners. Most trades are losers.

**Dependence on a single time stretch.**
- Each pair's biggest winner is the same late-2020 to early-2021 rally.
- ETH and BTC also share the 2020-07-06 entry (BTC 2020-07-06 16:00, ETH 2020-07-06 12:00).
- A large share of profit therefore comes from one market regime. This is one bull run, not independent evidence.

**Dependence on a single pair.**
- The three pairs are similar in shape. All three have a drawdown of 42% to 55% and profit that depends on one or two trades.
- BNB has the highest profit but the weakest robustness (excl-best 27 at base, 3 at stress).
- The cross-pair consistency criterion in `portfolio.json` is profit per day with min/max at least 0.25. I did not compute it, because the cell lengths are not in the files I read.

## 4. Overlap
Only H-004 has trade lists to compare, and I read only its BTC file (`research/experiments/H-004-exploration/trades-btc-usdt.csv`). I did not read its ETH or BNB lists, and I did not compute the `portfolio.json` correlation (max 0.7). The following is a date comparison by eye on BTC:
- H-005's largest BTC winners fall inside H-004 BTC holding windows:
  - 2020-10-08 to 2021-01-22 sits inside H-004's 2020-10-21 to 2021-04-23.
  - 2020-07-06 to 2020-09-03 sits inside H-004's 2020-04-30 to 2020-09-03.
  - 2019-02-19 to 2019-07-16 partly overlaps H-004's 2019-04-03 to 2019-08-29.
  - 2023-10-02 to 2024-01-18 nearly coincides with H-004's 2023-10-23 to 2024-01-19.
  - 2024-02-07 to 2024-03-20 sits inside H-004's 2024-02-12 to 2024-04-17.
  - 2017-11-25 to 2017-12-22 sits inside H-004's 2017-10-20 to 2018-01-16.
- H-005's 2021 stop-outs (2021-02-17 to 2021-09-20) occur while H-004 was holding or flat in the same year. For example, H-005 stopped out on 2021-02-17 to 2021-02-23 and 2021-03-30 to 2021-04-18, both inside H-004's open trade ending 2021-04-23.
- I conclude the two strategies are in the market in the same rallies. Their returns are likely correlated and are not independent profit sources. This is unquantified.
- I found no other H-numbered review directories with trade files.

## 5. Execution realism
- **Trade frequency.** About 31 to 36 trades per pair over the whole exploration split, so there are few trades. Each live miss (a missed fill, a gap past the stop) matters more than in a high-frequency strategy.
- **Stops.**
  - The 8% stop is a native intrabar stop. Backtest stop fills land at about -8.32%, i.e. right at the stop plus costs.
  - On a flash crash, an exchange outage, or a gap, the live fill can be worse than 8% on a spot venue. The backtest cannot show this.
  - ETH has several stop-outs within one to two days of entry (for example 2021-06-15 to 2021-06-16, 2021-11-25 to 2021-11-26, 2022-09-06 to 2022-09-07). These suggest entries near breakout spikes that reverse quickly.
- **Entries and exits.**
  - Signals fire at bar close with execution at the next bar open. Breakouts after a volatility squeeze are exactly when spreads widen and slippage rises. Market-order slippage at those moments may exceed the scenario values. I did not check the scenario values.
  - The `low336_breakdown` exit fires at the close of a bar, so the exit price follows a breakdown and can be worse in fast markets.
  - If limit orders were used live, fills at a breakout are not guaranteed. A missed entry on the few large winners would remove most of the profit.
- **Holding periods.** Winners are held for weeks or months (for example 212,700 minutes, about 148 days, on BTC 2019). The position is exposed to exchange outages, delisting, and custody risk for that whole period. The backtest ignores these.
- **Single position, whole balance.** The rule is one position with the whole balance (proposal `ex_ante_rule`). This is why drawdown is about 50%. A run of stop-outs hits the whole balance each time.
- **Not verified.** I have not seen the data gaps, the funding or borrow assumptions, or the exchange rules behind these numbers. Everything here comes from the backtest files only.
- **Outcome.** The recorded decision for all three pairs is `rejected` on the drawdown gate (facts, `decision`).

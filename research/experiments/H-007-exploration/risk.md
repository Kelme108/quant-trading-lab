# Risk assessment: H-007 (exploration split)

Sources: `research/experiments/H-007-exploration/facts.json` and `trades-{btc,eth,bnb}-usdt.csv`, `research/proposals/H-007.json`, `lab/config/gates.json`, `lab/config/portfolio.json`, `lab/config/scenarios.json`. For overlap I used `research/experiments/H-004-exploration/trades-{btc,eth}-usdt.csv` and `research/experiments/H-005-exploration/trades-{btc,eth}-usdt.csv`. Trade-list sums below are my own arithmetic on the CSVs. They are not compounded.

## 0. Data-integrity flags that affect everything below
- BNB/USDT: `lookahead_has_bias: true` and `recursive_is_stable: false`. Its numbers may not be trustworthy.
- BTC/USDT: `recursive_is_stable: false`. ETH is stable.
- All three pairs have fewer trades than a clean read needs. BTC has 23 and ETH has 27, both under the 30 minimum. BNB has 36.
- `facts.json` records the decision as "rejected" on all three pairs. This file does not re-decide.

## 1. Drawdown
Gate ceiling is 25% in every cost scenario (`lab/config/gates.json`).

| Pair | optimistic | base | conservative | stress | vs 25% |
|---|---|---|---|---|---|
| BTC | 35.68% | 36.75% | 37.81% | 40.90% | above in all 4 |
| ETH | 43.69% | 44.72% | 45.73% | 48.67% | above in all 4 |
| BNB | 23.87% | 25.13% | 26.42% | 30.98% | passes only optimistic |

Source: `facts.json` metrics. The proposal expected about 24% for 4 straight losses and said long streaks were "unlikely". The trade lists show longer streaks (base scenario, `profit_abs`, trades in order).

**BTC**
- Longest losing run is 7 trades in a row, 2023-01-29 to 2023-07-17 close. That is about 5.5 months open-to-close, and the run sums to about -231 USDT.
  - Six of the seven were 6.33% stop-outs. The seventh was a regime-exit loss of -5.4%.
  - Several lasted only hours. The 2023-03-14 trade ran 360 minutes and the 2023-03-22 trade ran 240 minutes.
  - The next winner opened 2023-11-01.
- Earlier, 3 stop-outs in a row: 2021-03-13, 2021-04-10 and 2021-09-03.
- Latest, 2 losses in 2024-04/05.

**ETH**
- Longest losing run is 12 consecutive losing trades, from 2021-10-08 to the 2024-01-22 close. That is about 2.3 years without a winner.
  - It is 4 stops in Oct–Nov 2021 (about -135 USDT), then 8 losses from 2023-02-02 to 2024-01-22 (about -127 USDT).
  - The next winner opened 2024-02-09.
- Trade-list losses over that run total about -262 USDT, against net profit of 329.5 at base.

**BNB**
- 7 losses in a row from 2020-09-01 to 2021-01-17, about 4.5 months (about -28 USDT, small because the stake was small).
- 6 losses from 2019-05-15 to the 2020-07-10 close, about 14 months.
- 5 losses from 2022-10-04 to the 2023-12-18 close, about 14.5 months.
- 4 losses at the end of the sample, 2024-03-12 to 2024-06-11 (about -79 USDT).

I cannot say from the files exactly which dates the maximum drawdown peak and trough fall on. The streaks above are the likely sources but that is inference.

## 2. Cost sensitivity
Net profit in USDT, from `facts.json`:

| Pair | optimistic | base | conservative | stress | opt→stress |
|---|---|---|---|---|---|
| BTC | 586.1 | 563.3 | 541.6 | 479.7 | -18.2% |
| ETH | 347.1 | 329.5 | 312.7 | 265.9 | -23.4% |
| BNB | 177.9 | 163.3 | 149.5 | 112.0 | -37.1% |

- The step from conservative to stress costs more than optimistic to base plus base to conservative combined. BTC loses 22.8, then 21.7, then 61.9. ETH and BNB show the same shape.
- The numeric per-scenario fee and slippage values are not in the files I read, so I cannot compute a break-even cost per trade. Profit is still positive at stress on all pairs, but only with all trades included. A break-even cost is not readable from these numbers.
- Excluding the single best trade (`net_profit_excl_best_trade`):
  - BTC: base 144.7, stress 114.5.
  - ETH: base 43.4, stress 22.7. ETH is thin there.
  - BNB: negative in every scenario (-42.9 optimistic, -45.8 base, -48.6 conservative, -56.1 stress).
- Observed stop losses cost -6.33% against a 6% stop. The roughly 0.33 point difference is in the CSVs. I can't split it between fees and slippage from the files.
- With 23–36 trades over about 7 years, costs per trade are small against winners. They matter mostly because the many short stop-outs each pay the round trip.

## 3. Concentration
- **Few trades carry the profit.**
  - BTC: 8 winners of 23. The largest, 2020-10-10 to 2021-01-21 (+365.8), is 65% of the 563.3 base profit. The top two (365.8 + 231.4, the 2024-02 trade) sum to 597.1, which exceeds total profit. The other 21 trades net about -34 on a plain sum.
  - ETH: 6 winners of 27. The top two (240.9 in 2020-11→2021-02 and 224.0 in 2021-04→05) sum to 464.9 against 329.5 total. The other 25 net about -135 on a plain sum.
  - BNB: 8 winners of 36. One trade (2021-02-01→03-25, +211.9) exceeds the whole 163.3. Profit excluding it is negative per `facts.json`.
- **Time concentration.** On all three pairs the large winners fall in two windows: Oct 2020–May 2021, and Oct 2023–Mar 2024. Most of the 2021-10 to 2024 stretch, outside those windows, is losses on ETH and BNB and a mix on BTC. There are no trades in 2022 on BTC or ETH, and BNB has just one (2022-10-04), so there is no evidence about 2022 behaviour.
- **Pair concentration.** BTC contributes 563 of 1,056 total (53%), but pairs are not independent: `scenarios.json` gives daily-return correlation 0.787 (ETH/BTC) and 0.635 (BNB/BTC) over all common days. The same market windows drive all three.
- Profit is in a compounding, whole-balance account. Late-sample trades are therefore larger in USDT than early ones, so USDT sums mix different stake sizes. I did not rebuild the compounding.

## 4. Overlap
No correlation was computed. This is a descriptive comparison of trade windows. BNB lists for H-004/H-005 were not read.

The overlap is strong on the big trades (open→close dates):

| Window | H-007 | H-005 | H-004 |
|---|---|---|---|
| BTC 2020 rally | 2020-10-10→2021-01-21 | 2020-10-08→2021-01-22 | 2020-10-21→2021-04-23 |
| BTC late 2021 | 2021-10-03→11-18 | 2021-10-01→11-18 | 2021-10-06→11-18 |
| BTC late 2023 | 2023-11-01→2024-01-14 | 2023-10-02→2024-01-18 | 2023-10-23→2024-01-19 |
| BTC early 2024 | 2024-02-07→03-17 | 2024-02-07→03-20 | 2024-02-12→04-17 |
| ETH 2020 rally | 2020-11-17→2021-02-23 | 2020-10-09→2021-02-23 | 2020-11-06→2021-05-23 |
| ETH Q1 2024 | 2024-02-09→03-16 | 2024-01-30→03-20 | 2024-10-24→2024-04-13 (long hold from 2023-10-24) |

- H-007 BTC and H-004 BTC both opened on 2023-03-14 13:00.
- H-007 BTC and H-005 BTC both closed on 2021-11-18 and share the same Feb–Mar 2024 window.
- H-007 loss clusters (early-to-mid 2023, Oct–Nov 2021 on ETH) also coincide with H-005 loss clusters (e.g. H-005 BTC stops in Apr–Aug 2023, H-005 ETH stops in 2021-11 and 2022).
- Overall, on the days I compared, the strategies were in the market together during the large trends and flat in similar quiet spells. H-007 looks like a filtered subset of the H-004/H-005 exposure. `portfolio.json` excludes a candidate whose daily-return correlation exceeds 0.7 with an included strategy. I have not computed that figure.

## 5. Execution realism
- **Trading frequency.** About 3–5 trades per year per pair, with winners held for weeks to months. Latency on entries and exits matters little. The costly events are the stop-outs.
- **Stops.** The backtest fills the 6% stop at the stop price (losses land at -6.33% consistently). In live trading a fast move or a weekend gap could fill below the stop. Short-duration stops (4–6 hours in March 2023, 12 hours in April 2024 on BNB) are the cases most likely to differ.
- **Signal execution.** Entries and channel exits execute at the next bar open after a close signal. Live fills can differ from the backtest open, especially on breakout bars that coincide with fast moves.
- **Outages.** `scenarios.json` notes 28 BTC data gaps between 2017-09 and 2023-03, the largest 33 missing hours, consistent with exchange downtime. A live stop or exit during downtime would not execute. The backtest tolerates the gaps without filling them.
- **Early history.** The 2017–2018 trades are from a period of lower liquidity. Fill and cost assumptions there may be optimistic.
- **Data quality.** The BNB lookahead flag and the BTC/BNB recursive instability mean the backtest signals may not match what a live run would compute on the same bars.
- **Compounding.** The whole-balance, single-position design means a late big loss hits the largest stake. The 2024 stop-outs are bigger in USDT than the 2017–2019 ones.
- **Small sample.** With 23–36 trades, the profit mostly comes from 2–3 trends. Nothing in these files shows how it would hold up on trends not yet seen.

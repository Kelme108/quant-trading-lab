# Quant review: H-040 (Daily NR7 breakout), exploration split

Sources: `research/experiments/H-040-exploration/facts.json` (metrics, gates), `crosscheck.json`, `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv`, `research/proposals/H-040.json`, `lab/config/gates.json`. Profit is in quote units on a 100 USDT starting balance (`crosscheck.json`). The deterministic gates decide; this note only describes. Exposure is 0.35 on all pairs (`facts.json`).

## 1. Per-pair results (all from `facts.json`)

### BTC/USDT
| Scenario | Trades | Net profit | Max drawdown % |
|---|---|---|---|
| optimistic | 95 | 66.11 | 6.09 |
| base | 95 | 58.05 | 7.62 |
| conservative | 95 | 50.33 | 9.16 |
| stress | 95 | 29.38 | 13.62 |

Profit without best trade (compounded, per `crosscheck.json`): base 36.76, conservative 30.15, optimistic 43.66, stress 12.19. Benchmarks: cash 0.0%, buy-and-hold +1252.7%. Gate verdict: `candidate_for_portfolio`. All listed gates pass.

### ETH/USDT
| Scenario | Trades | Net profit | Max drawdown % (the gate reads the max_relative_drawdown value) |
|---|---|---|---|
| optimistic | 80 | 43.60 | 3.25 (relative 4.39) |
| base | 80 | 37.70 | 3.60 (relative 4.60) |
| conservative | 80 | 32.06 | 4.00 (relative 4.80) |
| stress | 80 | 16.35 | 6.28 (relative 6.28) |

Without best trade: base 27.86, conservative 22.69, optimistic 33.29, stress 8.29. Benchmarks: cash 0.0%, buy-and-hold +929.6%. Gate verdict: `candidate_for_portfolio`.

### BNB/USDT
| Scenario | Trades | Net profit | Max drawdown % (relative) |
|---|---|---|---|
| optimistic | 87 | 45.86 | 9.29 (10.51) |
| base | 87 | 39.38 | 10.28 (11.12) |
| conservative | 87 | 33.20 | 11.83 (11.83) |
| stress | 87 | 16.13 | 16.41 (16.41) |

Without best trade: base 5.36, conservative 0.71, optimistic 10.16, **stress −11.97**. Benchmarks: cash 0.0%, buy-and-hold +33023.5%. Gate verdict: `candidate_for_portfolio`. The profit-excluding-best gate is only required in base (`gates.json`), so the negative stress value does not enter the verdict.

Note: the gates here only cover the exploration split. `gates.json` (split_progression) says a candidate must clear everything again on the validation split.

## 2. Cost sensitivity

Trade counts are identical across the four scenarios (`facts.json`), so only cost changes the result. The proposal gives a round trip of 0.35% at base and 0.95% at stress (`H-040.json`, rationale).

| Pair | Optimistic | Base | Conservative | Stress | Stress as % of optimistic (derived) |
|---|---|---|---|---|---|
| BTC | 66.11 | 58.05 | 50.33 | 29.38 | 44% |
| ETH | 43.60 | 37.70 | 32.06 | 16.35 | 37% |
| BNB | 45.86 | 39.38 | 33.20 | 16.13 | 35% |

Moving from optimistic to stress removes roughly 56–65% of profit on every pair (derived: 1 − stress/optimistic). Profit stays positive in the headline scenarios for all three pairs, so the average move per trade does cover the base round-trip cost. Edge over cost is thin at stress. BNB at stress, with its best trade removed, is negative (−11.97). Without that trade the BNB result is not covered by cost at the 0.95% round trip.

## 3. Concentration (derived from the `profit_abs` column of the trade CSVs)

Method: sort trades by `profit_abs`, sum the top 1/5/10, divide by the base net profit in `facts.json`. Shares are additive-quote approximations, because the stake compounds. A share above 100% means the remaining trades together lost money.

| Pair | Best 1 | Best 5 | Best 10 |
|---|---|---|---|
| BTC (net 58.05) | 16.86 → 29% | 46.21 → 80% | 73.93 → 127% |
| ETH (net 37.70) | 8.13 → 22% | 31.17 → 83% | 52.30 → 139% |
| BNB (net 39.38) | 36.80 → 93% | 69.25 → 176% | 88.41 → 224% |

- BNB's best trade is the 2021-02-17 entry, with profit_ratio +0.924, in `trades-bnb-usdt.csv`. This is not the 10-day trade that `validator.md` guessed. The 10-day trade (2019-05-13, +0.397, 14940 min) is the second largest. This agrees with the excl-best figure of 5.36 in `crosscheck.json`.
- On all three pairs the top 10 trades account for more than 100% of profit. The remaining ~85, ~70 and ~77 trades are net negative in sum (derived).

Exit reasons (counted by hand from the CSVs):

| Pair | stop_loss | close_below_nr7_low | time_exit_48 |
|---|---|---|---|
| BTC (95) | 31 | 15 | 49 |
| ETH (80) | 34 | 3 | 43 |
| BNB (87) | 43 | 7 | 37 |

- Stop-loss exits book about −3.34% each (`profit_ratio` ≈ −0.0334, i.e. the 3% stop plus costs). That is 33–49% of trades on each pair: BTC 33%, ETH 43%, BNB 49% (derived).
- Winners come almost entirely from `time_exit_48`. Trades that reach the 48-bar exit have a duration of 2880 min.
- Duration: all stop-loss and NR7-low exits are shorter than 2880 min, except a few close_below exits (e.g. ETH 4440 min, BNB 3660 min). Time exits longer than 2880 min (stretched holds) number 2 on BTC (5640, 5520), 0 on ETH, and 6 on BNB (5220, 14940, 4620, 3960, 5280, 6960). `validator.md` finding 1 attributes these to signals that reset the exit clock while a position is open. This departs from the proposal's "at most 2 days" and from the "48 bars since entry" rule. I have not checked the strategy file myself.

## 4. Consistency and limits

- All three pairs are positive in all four cost scenarios and pass every gate (`facts.json`), with 80–95 trades each (above the 30-trade floor). Drawdowns are well below the 25% bar (maximum 16.4% at stress, BNB).
- The pairs are not equally robust. BTC and ETH keep most of their profit without the best trade (36.76 of 58.05; 27.86 of 37.70). BNB's result depends on one trade (5.36 of 39.38 without it).
- The three pairs share many entry dates (for example 2019-04-01/04-18, 2020-01-14/01-26, 2022-03-27, 2023-03-26, 2024-03-10 across the lists), so they are not independent samples (observation from the CSVs, not quantified).
- What it shows: on this history, over the exploration split, the NR7 breakout rule had positive net results at every cost level on every pair, with a small number of large time-exit winners and many −3.3% stops.
- What it does not show: a stable per-trade edge. Profit is carried by the top ~10 trades per pair, and the sample of big winners is small. Buy-and-hold beats the strategy by a large margin on every pair (benchmarks above), though the gates do not require beating it, and exposure is 0.35. The stress result roughly halves profit or worse. Nothing here covers the validation split, and the exposure derivation (0.35) was not in the files I read. The BNB result in particular is not distinguishable from one outlier trade.

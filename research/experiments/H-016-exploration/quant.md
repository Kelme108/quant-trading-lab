# H-016 exploration – quant read-out

Sources: `research/experiments/H-016-exploration/facts.json` (metrics, gate reasons), `trades-<pair>.csv`, `crosscheck.json`, `lab/config/gates.json`. The proposal `research/proposals/H-016.json` was not found (Glob returned nothing), so I say nothing about the stated hypothesis or parameters. All profit figures are in USDT. The starting balance is 100 (`crosscheck.json`). Any share or ratio below is my own derivation and the method is stated.

## 1. Per-pair tables (`facts.json`)

### BTC/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 94 | 155.62 | 13.62 |
| base | 94 | 150.24 | 14.00 |
| conservative | 94 | 144.78 | 14.39 |
| stress | 94 | 129.48 | 15.49 |

- Profit without the best trade: 77.89 (base), 74.02 (conservative), 81.74 (optimistic), 63.22 (stress).
- Benchmark: cash 0.0%, buy-and-hold +1252.66%.
- Gate verdict: `candidate_for_portfolio`. Every gate listed in `decision_reasons` passes.

### ETH/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 89 | 119.78 | 11.18 |
| base | 89 | 115.19 | 11.43 |
| conservative | 89 | 110.90 | 11.66 |
| stress | 89 | 98.42 | 12.35 |

- Profit without the best trade: 69.74 (base), 66.38 (conservative), 73.35 (optimistic), 56.55 (stress).
- Benchmark: cash 0.0%, buy-and-hold +929.58%.
- Gate verdict: `candidate_for_portfolio`.

### BNB/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 96 | 530.96 | 9.63 |
| base | 96 | 516.96 | 9.70 |
| conservative | 96 | 503.49 | 9.76 |
| stress | 96 | 463.86 | 10.01 |

- Profit without the best trade: 201.54 (base), 194.92 (conservative), 208.42 (optimistic), 175.50 (stress).
- Benchmark: cash 0.0%, buy-and-hold +33023.53%.
- Gate verdict: `candidate_for_portfolio`.

Gate bars (`gates.json`, `facts.json` reasons):
- Minimum 30 trades.
- Net profit above 1.10 in base and conservative. The bar is 1.0 × (1 + 0.1 × 1 prior variant).
- Profit without the best trade above 0 in base.
- Drawdown at or below 25% in every scenario.
- Lookahead and recursive checks pass for all three pairs.
- Beating the benchmark is not required.
- `gates.json` is marked PROPOSED and not yet user-approved.
- This is the exploration split only. `gates.json` says a candidate must clear the gates again on the validation split.

## 2. Cost sensitivity (derived from `facts.json` `net_profit_quote__*`)

| Pair | Optimistic | Base | Conservative | Stress | Stress vs optimistic |
|---|---|---|---|---|---|
| BTC | 155.62 | 150.24 | 144.78 | 129.48 | −26.14 (−16.8%) |
| ETH | 119.78 | 115.19 | 110.90 | 98.42 | −21.36 (−17.8%) |
| BNB | 530.96 | 516.96 | 503.49 | 463.86 | −67.10 (−12.6%) |

- The percentages are (stress − optimistic) / optimistic.
- Moving from optimistic to base removes about 3% of profit on each pair: BTC 3.5%, ETH 3.8%, BNB 2.6%.
- Profit stays positive and above the gate bar in every scenario on all three pairs.
- The total cost effect is small next to the profit. About 90 trades per pair are priced in each scenario, and the stress-versus-optimistic gap is roughly 13–18% of profit.
- Winning trades are very large relative to cost. For example, the BTC trade at 2.09 return ratio (2017-10-09 to 2018-01-10) and the BNB trade at 6.95 (`trades-*.csv` `profit_ratio`).
- Most profit therefore comes from a few trades whose moves dwarf the round-trip cost. In that sense the average move covers cost.
- Many short trades lose a few percent or less. The result is not an artefact of cost, but short-trade losses and wins are of a size where cost matters at the margin.
- I did not read the actual fee or slippage values behind the four scenarios, so I do not state them.

## 3. Concentration (from `trades-*.csv`)

Method: I took the largest `profit_abs` values by hand and divided their sum by the pair's total `profit_abs`, which equals the base net profit (`crosscheck.json` confirms the match). Shares above 100% mean the remaining trades are net negative. These are hand calculations from the CSVs. `profit_abs` is not proportional to `profit_ratio`, so the stake size varies by trade.

| Pair | Best 1 | Best 5 | Best 10 |
|---|---|---|---|
| BTC (total 150.24) | 59.10 → ~39% | 152.73 → ~102% | 193.74 → ~129% |
| ETH (total 115.19) | 32.19 → ~28% | 94.47 → ~82% | 135.19 → ~117% |
| BNB (total 516.96) | 233.30 → ~45% | 531.29 → ~103% | 615.78 → ~119% |

- Best trade in each pair:
  - BTC: 2020-10-04 to 2021-02-07.
  - ETH: 2020-12-25 to 2021-03-06.
  - BNB: 2020-12-26 to 2021-03-22.
- Profit excluding the best trade is compounded (`crosscheck.json` method), so it is not total minus the best trade's `profit_abs`:
  - BTC: 77.89 versus 150.24, a drop of about 48%.
  - ETH: 69.74 versus 115.19, a drop of about 39%.
  - BNB: 201.54 versus 516.96, a drop of about 61%.
- Profit is concentrated in a handful of multi-month trends, and the best 5 trades account for roughly 80–100% of profit or more.
- Trade duration (`trade_duration` in minutes), hand-counted:
  - Trades of 30 days or longer (≥43200 min): BTC ~16 of 94, ETH ~21 of 89, BNB ~18 of 96. Almost all of them are winners.
  - Many of the remaining trades last 1–3 days (1440–4320 min) and are mostly small losses.
  - The profit-making group is the minority long-hold trades.
- Exit reason:
  - All BTC and ETH trades, and 95 of 96 BNB trades, exit with `tsmom_not_positive`.
  - The single other BNB trade is a `force_exit` on 2024-07-25, a −3.7% trade at the end of the data.
  - There are no stop-loss or ROI exits in these files.
- The drawdown figures (9.7–14.0% base) are lower than single-trade losses in the lists would suggest (e.g. BNB −34.3% `profit_ratio`, −28.46 `profit_abs`, 2021-05-19). That is consistent with `exposure` of 0.15 in `facts.json`, but I did not verify the sizing logic.

## 4. Consistency and limits

- Consistency across pairs:
  - All three pairs are profitable in all four scenarios and pass every gate. They are all long-only, trend-following in structure, and share the same exit reason.
  - Their profits cluster in the same windows: late 2020 to early 2021, and 2019–2020 on ETH and BTC.
  - The three pairs are therefore not independent evidence. They show one crypto-wide trend regime, not three separate confirmations.
- Magnitude differs widely: BNB 516.96 versus ETH 115.19 base.
- Buy-and-hold beat the strategy by a large margin on every pair (+1252.66% / +929.58% / +33023.53% versus the strategy's returns). Beating it is not required, but the strategy captures only a small part of the underlying move and is exposed for part of the time.
- Trade count (89–96) clears the 30-trade minimum, but the profit rests on roughly 5–10 long trends per pair, so the effective sample is small.
- Cost does not explain the result: profit survives stress, and the best trade's removal still leaves positive profit.
- What the numbers show:
  - On this exploration split, in this backtest, the rule makes money after costs on three correlated pairs, mostly from a few large trend trades.
- What they do not show:
  - Out-of-sample performance (the validation split is still required).
  - Independence between pairs.
  - Robustness to removing more than one trend.
  - Any advantage over holding the asset. They also do not show that the profit is more than one favourable regime.
- The multiple-testing penalty is minimal (1 prior variant) and the gates are marked PROPOSED.
- The deterministic gates give `candidate_for_portfolio` for each pair on the exploration split. That is the recorded verdict; I add no recommendation.

# Risk assessment: H-047 (RelativeStrengthRatioRotation), exploration split

Sources: `research/experiments/H-047-exploration/facts.json`, `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv`, `research/proposals/H-047.json`, `lab/config/gates.json`, `lab/config/portfolio.json`, and for overlap `research/experiments/H-046-exploration/trades-btc-usdt.csv` (first 59 trades only).

I did not run any calculation tool. Figures not printed in facts.json come from reading the trade lists by eye. They are marked "approx." and should be checked before they are relied on.

## 1. Drawdown

The gate ceiling is 25% in every cost scenario (`lab/config/gates.json`). Values below are `max_drawdown_pct` from facts.json.

| Pair | Optimistic | Base | Conservative | Stress |
|---|---|---|---|---|
| BTC/USDT | 6.65 | 7.99 | 9.44 | 13.79 |
| ETH/USDT | 7.35 | 8.00 | 10.00 | 14.05 |
| BNB/USDT | 8.67 | 9.60 | 10.58 | 15.19 |

- Every cell is under the ceiling. The worst is BNB stress at 15.19%, which leaves about 9.8 points of headroom.
- For ETH, facts.json gives two base-scenario figures: `max_drawdown_pct__base` is 8.00 and `max_relative_drawdown_pct__base` is 8.62. The gate reasons use the 8.62 figure, so the gate's own numbers are slightly higher than the absolute figure.
- The drawdowns are small partly because each trade is capped near -6.3%. The stop-loss trades all show profit_ratio of about -0.0633, which is the 6% stop plus fees. Stake per trade is about 20 USDT on the 100 USDT wallet, judging from -1.26 profit on -6.3% trades.
- Longest losing stretches, read from the lists (approx.):
  - BTC: from 2023-07-06 to about 2023-10-08, about 3 months. There are about 15 closed trades. Only one win of note (+0.24 on 2023-09-13) and one near-zero. Net is roughly -4.6 USDT at base cost.
    - BTC also had a run of losers from 2024-03-26 to 2024-05-14, with no win until 2024-05-15.
  - ETH: 2021-04-15 to 2021-08-08 is a mixed stretch. It has repeated stop-outs (2021-04-15, 04-22, 05-08, 05-14, 06-07, 07-04) offset by only a few winners.
    - Another is 2023-05-05 to 2023-08-13, with no winning trade except +0.34 (2023-06-21).
  - BNB: 2021-06-02 to 2021-08-12 has about 10 consecutive losers (three stops: 06-04, 06-05, 08-11). The late 2023-12 and 2024-01 and 2024-03/04 stretches also lose.
  - The maximum drawdown percentage is the better measure here, because I did not rebuild equity curves.
- Stops cluster across pairs. In 2021-06, BNB stopped on 06-04 and 06-05, ETH on 06-07, and BTC on 06-16. Cross-pair clustering of stops in the same weeks suggests drawdowns of the three pairs would not diversify fully if combined.

## 2. Cost sensitivity

`net_profit_quote` from facts.json (100 USDT wallet):

| Pair | Optimistic | Base | Conservative | Stress |
|---|---|---|---|---|
| BTC | 28.88 | 22.27 | 16.06 | -0.63 |
| ETH | 23.75 | 15.83 | 8.28 | -11.32 |
| BNB | 93.07 | 81.29 | 70.17 | 40.57 |

- Trade counts are 174 (BTC), 223 (ETH) and 211 (BNB), unchanged across scenarios. The cost effect is therefore proportional to trade count.
- Profit falls by about 6 to 8 USDT per step from optimistic to conservative. The conservative-to-stress step is much larger: -16.7 for BTC, -19.6 for ETH, and -29.6 for BNB.
- BTC and ETH are not profitable under stress. BTC ends at -0.63, essentially break-even. ETH loses 11.32. BNB stays positive.
- Rough break-even, assuming profit is linear in round-trip cost and that the proposal's 0.35% base and 0.95% stress round-trip costs match the scenarios (the scenario definitions were not read; check `lab/config/scenarios.json`):
  - BTC: about 0.9% round trip.
  - ETH: about 0.7%.
  - BNB: about 1.5%.
- The ETH figure leaves only about 0.35 percentage points of cost room above the 0.35% base. This is the thinnest margin of the three.
- Many winners are small. Dozens of trades have profit_ratio under 1.5% in absolute terms, roughly the size of costs plus noise. That is why profit is sensitive to costs at this trade count (174 to 223 trades over about 6.7 years, which is roughly 26 to 33 trades per year per pair, in line with the proposal's 15-40 estimate).

## 3. Concentration

- Single-trade dependence (facts.json `net_profit_excl_best_trade`):
  - BTC: base 17.15 (from 22.27), conservative 11.23, stress -4.64. Removing the best trade costs about 5.1 USDT, about 23% of base profit. The best BTC trade I can see is +4.34 (2017-12-06), so the metric difference is larger than that trade. I cannot explain the gap from the files.
  - ETH: base 9.23 (from 15.83), conservative 2.19, stress -16.16. Removing the best trade removes about 42% of base profit. The conservative profit without the best trade (2.19) is barely above the 1.0 USDT bar. The best ETH trade is +6.30 (2022-07-14 to 07-19, +30%).
  - BNB: base 55.93 (from 81.29), conservative 46.34, stress 21.05. The best trade is about 25 USDT.
- BNB is dominated by a few huge trades: 2021-02-17 (+81%, +24.93), 2017-12-24 (+80%, +17.50), 2021-02-09 (+41%, +11.78), 2017-12-15 (+49%, +9.85), 2019-03-04 (+29%, +7.62). These five total about 71.7 of 81.3 USDT, roughly 88% of base profit. Most BNB trades outside them are small or losing.
- Time concentration: BNB profit comes largely from 2017-12 to 2018-04 and 2021-02, which are periods of explosive single-coin moves. ETH has large winners in 2018-04/05, 2020-11 (+23%), 2021-01 (+23%) and 2022-07 (+30%). BTC wins cluster in 2019, 2020-11 to 2021-01 and 2023-01 and 2023-06. All three pairs earn well in the same bull-market windows (2020-11 to 2021-05).
- Pair dependence: the portfolio consistency rule uses profit per day (`lab/config/portfolio.json`, min ratio 0.25 of the max). On base profit alone, BTC at 22.27 and ETH at 15.83 are within about 3.6x and 5.1x of BNB's 81.29 before dividing by cell length (all three have the same exploration span, so the ratio is about 0.27 for BTC and 0.19 for ETH). On this crude ratio ETH falls below 0.25. This is not a formal evaluation: it needs the real day counts, and the rule applies to every required split. Treat it as a flag only.
- Only the exploration split exists in this directory. Nothing here shows the result holds outside it.

## 4. Overlap

- Within H-047: the same-day-held signal is built from the same three prices, so the pairs share regime exposure. Example: BTC 2020-11-16 to 11-19 (+8.7%) and ETH 2020-11-20 to 11-24 (+23%) are back to back. BTC 2021-01-01 to 01-03 (+16%) and ETH 2021-01-03 to 01-06 (+23%) are adjacent. The portfolio's correlation test is not computed here.
- Against H-046 (BTC list, first 59 trades only): H-046 holds BTC for long stretches (it is a trailing-low strategy, with holds of 5 to 20 days), and H-047 trades fall inside them:
  - H-047 2018-07-17 to 07-21 sits inside H-046 2018-07-17 to 07-21 (identical dates).
  - H-047 2019-05-07 to 05-11 sits inside H-046 2019-05-03 to 05-17.
  - H-047 2019-06-14 to 06-17 and 06-22 to 06-27 sit inside H-046 2019-06-14 to 06-27.
  - H-047 2020-04-29 to 05-01 sits inside H-046 2020-04-23 to 05-04.
  - H-047 2020-10-19 to 10-22 sits inside H-046 2020-10-09 to 10-26.
  - Several of H-047's large BTC winners fall in H-046's large winners. Both profit from the same BTC rallies.
- Other hypotheses (H-004 through H-040): not compared, since only H-046 was compared. The overlap picture is therefore incomplete. The portfolio correlation rule (max |r| 0.7, daily returns spread over holding days) was not computed.

## 5. Execution realism

- Hourly signals with next-open fills. Winners are mostly a few hundred bars long, so fill timing matters less than for a scalper, but about 25 to 33 round trips per pair per year, each costing 0.35% to 0.95%, makes spread and fee assumptions material (section 2).
- Stop-loss fills: dozens of trades exit at exactly the 6% stop (profit_ratio about -0.0633). Many of these have trade_duration of 0 or 60 minutes (for example BNB 2017-12-03, 2018-01-05, 2018-01-11, 2018-03-13, 2022-11-08; ETH 2018-01-16, 2019-06-26). Fills at exactly the stop level on same-bar entries and exits assume no gap or slippage. In a fast crypto move, or a fast move on an outage, live fills could be worse than -6%. The stress cost scenario does not obviously model gap risk beyond fees. I do not know how slippage is modelled in the stress scenario.
- BNB stops cluster in volatile, explosive periods (2017-12 to 2018-03) where gaps are most likely, and where the strategy also makes its biggest gains. The same volatility that makes BNB profitable is where a stop-fill assumption is hardest to trust.
- Exits are "ratio weak or regime lost", sent at the next open. A rule that triggers on small moves (many losers of -0.5% to -3% in 1 to a few hours) can produce churn. Cooldown is 12 bars.
- Early BNB history (2017) and the order sizes (whole balance, around 20 USDT per trade in this 100 USDT test) assume liquidity is not an issue. That is plausible for the size shown, but this is untested by the files.
- Live data differences: the signal needs three pairs' closed candles aligned each hour. An outage or a stale candle on any one of the three pairs would corrupt the ratio signal for the other two. The backtest assumes a clean, complete feed.
- Dry-run or live behaviour is not evidenced anywhere in these files. One BNB trade at the end (2024-07-25) was a `force_exit`, an artefact of the backtest end.

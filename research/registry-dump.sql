BEGIN TRANSACTION;
CREATE TABLE agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    hypothesis_id TEXT,
    purpose TEXT NOT NULL,
    status TEXT NOT NULL,                -- completed | failed | guard_violation
    cost_usd REAL,
    num_turns INTEGER,
    duration_s REAL,
    session_id TEXT,
    result_excerpt TEXT,
    started_at_utc TEXT NOT NULL
);
INSERT INTO "agent_runs" VALUES(1,'research','H-004','propose attempt 1','completed',5.846829999999999388e-02,5,2.632629050000105053e+01,'386b9e9c-8ff7-49b9-b3d4-c8d1a729e9b0','research/proposals/H-004.json','2026-10-30T13:28:07.648531+00:00');
INSERT INTO "agent_runs" VALUES(2,'developer','H-004','implement attempt 1','completed',0.10518,8,1.084572556999992229e+02,'51706821-e094-4a46-b482-12147926910c','I wrote the strategy and its test. The new test module passes (5 tests), and so does the full suite (220 tests).

- `user_data/strategies/SlowTimeSeriesMomentum_H004_v1.py`
- `tests/test_slowtimeseriesmomentum_h004_v1.py`

- **Cooldown:** I implemented the 168-bar cooldown as a Freqtrade `CooldownPeriod` protection, not in the signal columns. So the signal frame alone doesn''t enforce the 7-day wait. Only a real backtest or live run does, and the unit tests don''t cover it.
- **Hard stop:** The 15% stop is `stoploss = -0.15`, which Freqtrade checks inside each bar. The proposal says to check it on closed bars, so a stop can trigger slightly earlier than the rule states.','2026-10-30T13:28:34.704014+00:00');
INSERT INTO "agent_runs" VALUES(3,'developer','H-004','implement attempt 2','completed',0.0964745,13,1.147941748000012013e+02,'2972b334-50fa-47bd-97c4-f33af41ee21f','I fixed the startup failure. Both test runs pass: the new test module (5 tests) and the full suite (220 tests). I didn''t re-run the real Freqtrade backtest, so that part is unconfirmed.

**What failed:** the backtest window is 120 days, which is about 2,880 hourly candles, and it starts at the first day of data. With `startup_candle_count = 4800` the engine had nothing left to trade on.

**The change:** `startup_candle_count` is now 1440, and the 200-day average of close is `rolling(4800, min_periods=1440)`. It still averages up to 4800 candles, but it is defined once 1440 candles are available. Before that point it is undefined, so no entry fires.

**Rule deviation:** this departs from H-004''s stated rule and from your instruction that `startup_candle_count` be at least the longest lookback (4800). Early in a data series the regime filter averages fewer than 200 days, and `startup_candle_count` is below the 4800-candle lookback. The alternative is that this 120-day window can never run. I didn''t check whether the static contract check flags the 1440.

I also changed two lines in the test file to match: the startup assertion now expects 1440, and the undefined-start-up test checks the first 1440 rows.

Files:
- `D:\Trade-Initial\user_data\strategies\SlowTimeSeriesMomentum_H004_v1.py`
- `D:\Trade-Initial\tests\test_slowtimeseriesmomentum_h004_v1.py`','2026-10-30T13:32:28.022963+00:00');
INSERT INTO "agent_runs" VALUES(4,'validator','H-004','review exploration','completed',0.2052564,14,67.0240879999983,'d69a61e3-4719-4b9c-83fd-8413c3afde24','I wrote the report to `research/experiments/H-004-exploration/validator.md`. Seven of its nine findings are notes or checks that passed; the four warnings are below.

**Warnings**
- **Cooldown:** The 7-day cooldown doesn''t look active in the trade lists. BTC re-entered about 4.75 days after an exit (2023-03-09 to 2023-03-14), and ETH about 3.2 days after (2023-02-13 to 2023-02-16). The backtest probably ran without protections, but I couldn''t confirm that from the files I read.
- **Regime filter:** The "200-day" SMA is built with `min_periods=1440`. At the start of the data it is a 60 to 199-day average, and the earliest trades on all three pairs probably used it. This likely relates to the recursive-analysis failure.
- **Stop-loss:** The 15% stop fires intrabar, while the proposal says it is checked on closed bars.
- **Profit concentration:**
  - One 2020–21 trade carries 49% of net profit on BTC, 93% on ETH and 72% on BNB.
  - The stored `net_profit_excl_best_trade` doesn''t match simple subtraction. BNB shows 89.4, against 573.4 by subtraction. Compounding may explain it, but I couldn''t verify the method.

**Checks that passed**
- Trade counts (13, 15 and 16) and net profits agree with `crosscheck.json` and with the trade lists.
- I found no forward-looking indexing: both channels are shifted by one bar.
- Lookbacks match the proposal.

I also left a stray file, `validator.md.tmp`, in the review directory by mistake. I can''t delete it, so please remove it.','2026-10-30T13:43:18.894240+00:00');
INSERT INTO "agent_runs" VALUES(5,'validator','H-004','review exploration','guard_violation',NULL,NULL,NULL,NULL,'agent ''validator'' step wrote outside its allowed paths: [''research/experiments/H-004-exploration/validator.md.tmp'']','2026-10-30T13:44:26.424809+00:00');
INSERT INTO "agent_runs" VALUES(6,'research','H-005','propose attempt 1','completed',7.619139999999999246e-02,5,3.197338800000579794e+01,'01abb3cd-b87a-496c-b629-86cda430012d','research/proposals/H-005.json','2026-10-30T13:49:05.800871+00:00');
INSERT INTO "agent_runs" VALUES(7,'developer','H-005','implement attempt 1','completed',0.1003891,8,1.204003595000031054e+02,'0ee5903e-fd7f-462c-86b2-7fee19a1c762','I wrote the strategy and its test, and both the new test module and the full suite pass (228 tests).

- `user_data/strategies/VolatilitySqueezeBreakout_H005_v1.py`
- `tests/test_volatilitysqueezebreakout_h005_v1.py`

The rule is implemented as written, with no changes to any number. The cooldown is a 72-candle `CooldownPeriod` protection, and `startup_candle_count` is 2400.

I did not run any other checks, including the static contract check, so I can''t say whether it passes.','2026-10-30T13:49:38.766390+00:00');
INSERT INTO "agent_runs" VALUES(8,'validator','H-005','review exploration','completed',0.1478699,11,4.215701320000516716e+01,'920f5239-f96e-4499-a24b-f28c1af19f20','I wrote the report to `research/experiments/H-005-exploration/validator.md`. It has no blocking findings: the code matches the proposal, I found no look-ahead, and the stored numbers agree with `crosscheck.json` and the trade lists.

- **Code against proposal:** every level the current close is compared with is shifted by one candle. The only additions are a `volume > 0` condition on entry and exit, which has negligible effect, and a rule that a window with any undefined squeeze value cannot enter.
- **Cooldown:** the 72-candle cooldown is in the code, but I couldn''t confirm the backtest ran with protections enabled. The shortest gap between an exit and the next entry in the trade lists is about 76 hours, so the lists are consistent with it without proving it.
- **Numbers:** trade counts are BTC 31, ETH 36 and BNB 36. Net profit and profit excluding the best trade match `crosscheck.json` for all three pairs. Stop-loss exits show about −8.32%, which fits the 8% stop plus costs.
- **Warnings:**
  - **Profit concentration:** one trade carries most of the profit in each pair. Without it, BNB falls from 879 to 27 (3.0 in the stress scenario), ETH from 507 to 51, and BTC from 520 to 130.
  - **Win rate:** low, with 8 of 31 trades winning on BTC, 12 of 36 on ETH and 9 of 36 on BNB. Many trades are 8% stop-outs.
  - **Drawdown:** 42–55% in every cost scenario on every pair, against the 25% limit.

All three pairs are stored as rejected, solely on the max-drawdown gate. I did not read the manifests, the raw export zip or `validation-protocol-v2.md`.','2026-10-30T14:00:25.871585+00:00');
INSERT INTO "agent_runs" VALUES(9,'quant','H-005','review exploration','completed',0.1629706,10,6.966781949999858626e+01,'fed5bb7f-f2f1-43a1-b611-1e0d97df6775','I wrote `research/experiments/H-005-exploration/quant.md`. The gates rejected H-005 on all three pairs, and the only gate that failed was max drawdown. I created no other file.

- **Drawdown:** it was 42–55% in every cost scenario on every pair, against the 25% bar in `gates.json`. Even at optimistic cost it was 49.1% on BTC, 49.5% on ETH and 42.0% on BNB.
- **Cost:** net profit stayed positive in all four cost scenarios on every pair. Going from optimistic to stress cut profit by about 24–28%. Cost does not explain the rejection.
- **Concentration:** the best single trade gave 71–81% of total profit. Removing it cut profit by about 75% on BTC, 90% on ETH and 97% on BNB. Stress-case BNB profit without its best trade is only 3.01.
- **Same episode:** the best trade on each pair comes from the 2020–21 rally.
- **Win rate and exits:** winners were 9 of 31 trades on BTC, 11 of 36 on ETH and 8 of 36 on BNB. Every winner exited through `low336_breakdown`. Stop-losses were 12, 18 and 17 trades, each losing about 8.3%.
- **Sample:** trade counts of 31, 36 and 36 sit just above the 30-trade minimum. The three pairs overlap in time, so they are not independent confirmations.

The top-N shares and the exit counts are my own tallies from the trade CSVs, and the note says how I derived them. I did not state a per-trade cost figure, because the files I read don''t contain one.','2026-10-30T14:01:08.545616+00:00');
INSERT INTO "agent_runs" VALUES(10,'risk','H-005','review exploration','completed',0.1766041,11,5.568592200000421144e+01,'7bbdb464-a79a-45f7-9a5e-b66c528c338b','I wrote `research/experiments/H-005-exploration/risk.md`. The recorded decision for all three pairs is `rejected`.

- **Drawdown:** Every pair and cost scenario fails the 25% ceiling. Base-scenario drawdown is 50.1% on BTC, 50.6% on ETH and 42.9% on BNB. The worst losing streaks are:
  - BNB: 10 losers in a row over about 23 months, roughly 359 quote lost.
  - ETH: 8 losers over about 11.5 months, roughly 473 quote lost.
  - BTC: 7 losers over about 17 months, roughly 181 quote lost.
- **Cost sensitivity:** Net profit falls 24% to 28% from optimistic to stress and stays positive. The drop from conservative to stress is steeper than the earlier steps. I could not read a break-even cost. I didn''t read the fee and slippage values behind each scenario, and profit is still positive at stress.
- **Concentration:** One late-2020 to early-2021 rally supplies the best trade on every pair. The best trade is about 75% of profit on BTC and about 90% or more on ETH and BNB. Excluding it, profit at the stress scenario drops to 91.9 on BTC, 22.5 on ETH and 3.0 on BNB.
- **Overlap:** I compared by date only against H-004, and only its BTC trades. H-005''s biggest BTC winners fall inside H-004''s holding windows, so the two are probably correlated. I did not compute a correlation. No other hypothesis had trade lists to compare.
- **Execution realism:** Only about 31 to 36 trades per pair. The backtest assumes the 8% stop fills at the stop price, with no gap or outage risk. It also assumes breakout entries fill with no extra spread. Winners are held for weeks to months.','2026-10-30T14:02:18.730616+00:00');
INSERT INTO "agent_runs" VALUES(11,'research','H-006','propose attempt 1','completed',1.248654999999999904e-01,6,4.181572759999835399e+01,'a5056a86-a68c-4d63-81ff-9598a3cad2d7','research/proposals/H-006.json','2026-10-30T17:41:45.228132+00:00');
INSERT INTO "agent_runs" VALUES(12,'developer','H-006','implement attempt 1','completed',0.1264169,8,1.281110224000003654e+02,'5ce76b6d-c335-4a37-af58-e075b8ac6c01','I wrote both files. The new test module (6 tests) and the full suite (298 tests) pass.

- `user_data/strategies/RegimeGatedPullbackTrend_H006_v1.py`
- `tests/test_regimegatedpullbacktrend_h006_v1.py`

The 240-bar time stop is implemented in `custom_exit`, as a check on elapsed time since entry. It is not a candle-close signal, so it may fire a bit differently from the proposal''s "exit at close of bar t, executed next open". `custom_exit` is not on the banned-method list, but I didn''t run the static contract check.','2026-10-30T17:42:27.616383+00:00');
INSERT INTO "agent_runs" VALUES(13,'research','H-007','propose attempt 1','completed',0.0883192,5,3.361079589999280869e+01,'0d66688b-1e9a-4677-9b3d-5068b9e3a6a4','research/proposals/H-007.json','2026-10-30T18:28:30.477663+00:00');
INSERT INTO "agent_runs" VALUES(14,'developer','H-007','implement attempt 1','completed',1.096873000000000153e-01,10,2.238089094999886584e+02,'8603c3b5-ea91-46f6-9a89-7c928a132142','I wrote the H-007 strategy and its test file. The new test module passes (6 tests), and so does the full suite (309 tests).

The rule is implemented as written in the proposal, with `startup_candle_count = 2880`.

My first test run failed because of an off-by-one in my own test, not in the strategy. SMA(1200) is first defined at row 1199, and my test had assumed row 1200. I corrected the test and left the rule alone.

- `D:\Trade-Initial\user_data\strategies\RisingTrendBreakoutGate_H007_v1.py`
- `D:\Trade-Initial\tests\test_risingtrendbreakoutgate_h007_v1.py`','2026-10-30T18:36:01.724838+00:00');
INSERT INTO "agent_runs" VALUES(15,'validator','H-007','review exploration','completed',0.1259849,10,3.170832199999131262e+01,'c532b07e-57bd-4359-afd6-021c96ed46a9','I wrote the report to `research/experiments/H-007-exploration/validator.md`. It has no blocking findings and several warnings.

- **Code against proposal:** the strategy matches the proposal on regime, entry, exit, stop, cooldown and warm-up. The only additions are `volume > 0` and not-NaN guards, which are harmless.
- **Look-ahead:** I found no forward-looking indexing in the code. Both channel levels are shifted by one bar before the comparison. BNB still fails the lookahead gate (`lookahead_has_bias: true` in `facts.json`). I couldn''t trace the cause from the files.
- **Stored numbers:** `crosscheck.json` shows the stored values match the export for all three pairs, and the BTC and BNB CSV row counts match the trade counts. I did not open the ETH CSV, so its durations and exit reasons are unchecked. I also did not read `research/validation-protocol-v2.md` or the manifests.
- **Reliability:**
  - **Profit concentration:** each pair leans on one trade. BNB''s net profit is negative without its best trade (−45.8). BTC drops from 563 to 145 without its best trade, and ETH from 330 to 43.
  - **Loss streaks:** the proposal predicted the regime gate would prevent them, but BTC has eight consecutive stop-losses in 2023, broken by one signal exit. BNB has runs of six or more in 2019 and 2020.
  - **Drawdown and trade counts:** max drawdown at base is 36.7% for BTC, 44.7% for ETH and 25.1% for BNB, all over the 25% limit. BTC and ETH have 23 and 27 trades, under the 30-trade minimum.
  - **Recursive analysis:** it is unstable on BTC and BNB.','2026-10-30T18:48:37.160318+00:00');
INSERT INTO "agent_runs" VALUES(16,'quant','H-007','review exploration','completed',0.1616735,10,5.223043339999276213e+01,'7e4bb16f-d0aa-421d-b12e-eabc12f343b0','I wrote `research/experiments/H-007-exploration/quant.md`. All three pairs are rejected by the gates, and I did not change that.

- **BTC/USDT:** 23 trades, base profit 563.30 USDT, max drawdown 36.75%. It fails the recursive check and the drawdown gate in every cost scenario, and 23 trades is below the 30-trade minimum.
- **ETH/USDT:** 27 trades, base profit 329.51 USDT, max drawdown 44.72%. It fails the drawdown gate in every scenario, and 27 trades is below the minimum.
- **BNB/USDT:** 36 trades, base profit 163.34 USDT, max drawdown 25.13%. It fails lookahead, recursive and the profit-without-best-trade gate (−45.83 USDT). It misses the drawdown limit in base, conservative and stress.

**Cost:** profit stays positive in all four cost scenarios on every pair. Stress cuts optimistic profit by 18% on BTC, 23% on ETH and 37% on BNB. The files don''t give the fee and slippage rates for each scenario, so I couldn''t say by how many points.

**Concentration (my arithmetic from the trade CSVs):** the best trade is 65% of net profit on BTC, 73% on ETH and 130% on BNB. The best 5 trades exceed 150% of total profit on all three pairs, because the remaining trades lose money overall. Only 6 to 8 trades win per pair, and stop-loss exits are about half of all exits (11 of 23, 13 of 27, 19 of 36).

**Consistency:** the profit comes from the 2019–2021 and early-2024 trend phases. Loss streaks of 5 to 7 trades appear, which the proposal said the regime gate should prevent. The sample is too small on BTC and ETH to conclude anything from the winners, and none of this is validation-split evidence.

I created no other files.','2026-10-30T18:49:09.350648+00:00');
INSERT INTO "agent_runs" VALUES(17,'risk','H-007','review exploration','completed',0.2307171,17,6.849326009998912923e+01,'9424014b-f622-4a09-8273-0230ae49336d','I wrote `research/experiments/H-007-exploration/risk.md`, covering all five sections.

- **Drawdown:** Every pair is over the 25% ceiling in all four cost scenarios, except BNB in the optimistic scenario (23.87%).

  | Pair | Base drawdown | Longest losing run |
  |---|---|---|
  | BTC | 36.75% | 7 straight losses, 2023-01-29 to 2023-07-17 |
  | ETH | 44.72% | 12 straight losses, 2021-10-08 to 2024-01-22 (about 2.3 years) |
  | BNB | 25.13% | 7 straight losses, 2020-09-01 to 2021-01-17 |

  These streaks are longer than the proposal''s expectation of about 4. I could not date the drawdown peaks from the files, so linking them to these streaks is inference.
- **Cost sensitivity:** Profit falls 18% on BTC, 23% on ETH and 37% on BNB from optimistic to stress. The conservative-to-stress step costs more than the two earlier steps combined. The fee and slippage values per scenario are not in the files I read, so I could not compute a break-even cost.
- **Concentration:**
  - Profit rests on a few trades. On BTC the top two trades exceed total profit.
  - On ETH the top two trades also exceed total profit.
  - On BNB one trade exceeds total profit, and profit without it is negative in every scenario.
  - The big winners fall in two windows: Oct 2020–May 2021 and Oct 2023–Mar 2024.
  - There is no evidence about 2022 on BTC or ETH, because neither pair traded then.
- **Overlap:** I compared H-004 and H-005 on BTC and ETH only. H-007 entered and exited on nearly the same dates as both during the large trends, and one BTC entry matches H-004 to the hour. I did not compute a correlation, and I did not read the BNB lists for H-004 and H-005.
- **Execution:** The risks are stop fills at the exact stop price, gaps and exchange downtime, and entries at the next bar''s open. Several stops triggered within hours of entry.

Data-integrity flags: BNB has a lookahead-bias flag and an unstable recursive check, and BTC also has an unstable recursive check. BTC (23 trades) and ETH (27) are ','2026-10-30T18:50:02.033688+00:00');
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    decision TEXT NOT NULL,              -- rejected | inconclusive | candidate_for_forward_test
    reasons_json TEXT NOT NULL,
    gates_sha256 TEXT NOT NULL,
    decided_at_utc TEXT NOT NULL
);
INSERT INTO "decisions" VALUES(1,'20261027T143611Z-donchian-h002-explore','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: inconclusive (1 < 30)", "minimum_trades[base]: inconclusive (1 < 30)", "minimum_trades[conservative]: inconclusive (1 < 30)", "minimum_trades[stress]: inconclusive (1 < 30)", "net_profit[base]: FAIL (net_profit_quote=-4.06698331)", "net_profit[conservative]: FAIL (net_profit_quote=-4.21393789)", "profit_excluding_best_trade[base]: FAIL (value=0.0)", "max_drawdown[optimistic]: pass (3.920028740000006% <= 25.0%)", "max_drawdown[base]: pass (4.066983309999998% <= 25.0%)", "max_drawdown[conservative]: pass (4.213937889999997% <= 25.0%)", "max_drawdown[stress]: pass (4.654801620000001% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=-29.74143029368761%); beating the benchmark is not required"]','64a72f65485202335db7f841b5e19dd34cf9d10c5f3e463f6fa12a16a94562da','2026-10-27T14:37:11.884855+00:00');
INSERT INTO "decisions" VALUES(2,'20261030T130132Z-donchian-h002-explore-btc-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (787 >= 30)", "minimum_trades[base]: pass (787 >= 30)", "minimum_trades[conservative]: pass (787 >= 30)", "minimum_trades[stress]: pass (498 >= 30)", "net_profit[base]: FAIL (net_profit_quote=-51.69842568 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: FAIL (net_profit_quote=-85.11376844 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: FAIL (value=-91.79509390999999)", "max_drawdown[optimistic]: FAIL (60.766378022442424% <= 25.0%)", "max_drawdown[base]: FAIL (79.83078863318426% <= 25.0%)", "max_drawdown[conservative]: FAIL (92.96089481473999% <= 25.0%)", "max_drawdown[stress]: FAIL (96.85469864035524% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=1252.6553612001403%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T13:03:06.037210+00:00');
INSERT INTO "decisions" VALUES(3,'20261030T130132Z-donchian-h002-explore-eth-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (819 >= 30)", "minimum_trades[base]: pass (819 >= 30)", "minimum_trades[conservative]: pass (819 >= 30)", "minimum_trades[stress]: pass (331 >= 30)", "net_profit[base]: FAIL (net_profit_quote=-28.804597049999984 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: FAIL (net_profit_quote=-79.15442569999999 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: FAIL (value=-71.29084771999999)", "max_drawdown[optimistic]: FAIL (58.43094234664827% <= 25.0%)", "max_drawdown[base]: FAIL (73.622012350602% <= 25.0%)", "max_drawdown[conservative]: FAIL (83.86254383862803% <= 25.0%)", "max_drawdown[stress]: FAIL (95.12215241355811% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=929.5812473061238%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T13:04:39.117888+00:00');
INSERT INTO "decisions" VALUES(4,'20261030T130132Z-donchian-h002-explore-bnb-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (835 >= 30)", "minimum_trades[base]: pass (835 >= 30)", "minimum_trades[conservative]: pass (835 >= 30)", "minimum_trades[stress]: pass (655 >= 30)", "net_profit[base]: pass (net_profit_quote=60.96892004999995 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: FAIL (net_profit_quote=-54.09181266999991 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: FAIL (value=-352.92893437000004)", "max_drawdown[optimistic]: FAIL (81.20388566438248% <= 25.0%)", "max_drawdown[base]: FAIL (88.55541888370247% <= 25.0%)", "max_drawdown[conservative]: FAIL (93.21151069083065% <= 25.0%)", "max_drawdown[stress]: FAIL (98.4342718005962% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=33023.529411764706%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T13:06:13.050975+00:00');
INSERT INTO "decisions" VALUES(5,'20261030T133614Z-h-004-exploration-btc-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: FAIL (is_stable=False)", "minimum_trades[optimistic]: inconclusive (13.0 < 30)", "minimum_trades[base]: inconclusive (13.0 < 30)", "minimum_trades[conservative]: inconclusive (13.0 < 30)", "minimum_trades[stress]: inconclusive (13.0 < 30)", "net_profit[base]: pass (net_profit_quote=1906.2048170499997 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=1870.2073444400003 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=407.4800835984504)", "max_drawdown[optimistic]: pass (7.654851085305318% <= 25.0%)", "max_drawdown[base]: pass (7.801052919545276% <= 25.0%)", "max_drawdown[conservative]: pass (7.944618666954156% <= 25.0%)", "max_drawdown[stress]: pass (8.376998959846325% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=1252.6553612001403%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T13:43:18.624629+00:00');
INSERT INTO "decisions" VALUES(6,'20261030T133614Z-h-004-exploration-eth-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: FAIL (is_stable=False)", "minimum_trades[optimistic]: inconclusive (15.0 < 30)", "minimum_trades[base]: inconclusive (15.0 < 30)", "minimum_trades[conservative]: inconclusive (15.0 < 30)", "minimum_trades[stress]: inconclusive (15.0 < 30)", "net_profit[base]: pass (net_profit_quote=1495.8396605 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=1461.8698943400002 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=268.0827833160337)", "max_drawdown[optimistic]: FAIL (36.075733722221095% <= 25.0%)", "max_drawdown[base]: FAIL (36.67390021006673% <= 25.0%)", "max_drawdown[conservative]: FAIL (37.264979756601605% <= 25.0%)", "max_drawdown[stress]: FAIL (39.1441991321387% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=929.5812473061238%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T13:43:18.631058+00:00');
INSERT INTO "decisions" VALUES(7,'20261030T133614Z-h-004-exploration-bnb-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: FAIL (is_stable=False)", "minimum_trades[optimistic]: inconclusive (16.0 < 30)", "minimum_trades[base]: inconclusive (16.0 < 30)", "minimum_trades[conservative]: inconclusive (16.0 < 30)", "minimum_trades[stress]: inconclusive (16.0 < 30)", "net_profit[base]: pass (net_profit_quote=2045.7018400799998 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=1995.4013924 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=89.41631952877114)", "max_drawdown[optimistic]: FAIL (41.64563524366887% <= 25.0%)", "max_drawdown[base]: FAIL (42.10727432174309% <= 25.0%)", "max_drawdown[conservative]: FAIL (42.5663456608892% <= 25.0%)", "max_drawdown[stress]: FAIL (43.924416360315874% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=33023.529411764706%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T13:43:18.637975+00:00');
INSERT INTO "decisions" VALUES(8,'20261030T135346Z-h-005-exploration-btc-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (31.0 >= 30)", "minimum_trades[base]: pass (31.0 >= 30)", "minimum_trades[conservative]: pass (31.0 >= 30)", "minimum_trades[stress]: pass (31.0 >= 30)", "net_profit[base]: pass (net_profit_quote=520.36933964 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=492.3369603000001 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=129.76304978973582)", "max_drawdown[optimistic]: FAIL (49.05119695159429% <= 25.0%)", "max_drawdown[base]: FAIL (50.119209325097124% <= 25.0%)", "max_drawdown[conservative]: FAIL (51.19152003738006% <= 25.0%)", "max_drawdown[stress]: FAIL (54.27126160501704% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=1252.6553612001403%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T14:00:25.582354+00:00');
INSERT INTO "decisions" VALUES(9,'20261030T135346Z-h-005-exploration-eth-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (36.0 >= 30)", "minimum_trades[base]: pass (36.0 >= 30)", "minimum_trades[conservative]: pass (36.0 >= 30)", "minimum_trades[stress]: pass (36.0 >= 30)", "net_profit[base]: pass (net_profit_quote=507.23876498000004 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=475.47933744999983 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=51.142465101975574)", "max_drawdown[optimistic]: FAIL (49.549665632018566% <= 25.0%)", "max_drawdown[base]: FAIL (50.625558155839244% <= 25.0%)", "max_drawdown[conservative]: FAIL (51.68120148592084% <= 25.0%)", "max_drawdown[stress]: FAIL (54.72438571486683% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=929.5812473061238%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T14:00:25.589421+00:00');
INSERT INTO "decisions" VALUES(10,'20261030T135346Z-h-005-exploration-bnb-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (36.0 >= 30)", "minimum_trades[base]: pass (36.0 >= 30)", "minimum_trades[conservative]: pass (36.0 >= 30)", "minimum_trades[stress]: pass (36.0 >= 30)", "net_profit[base]: pass (net_profit_quote=879.1521404599999 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=827.88634406 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=27.076199203033696)", "max_drawdown[optimistic]: FAIL (42.040079972695324% <= 25.0%)", "max_drawdown[base]: FAIL (42.92453129892464% <= 25.0%)", "max_drawdown[conservative]: FAIL (43.80257578270251% <= 25.0%)", "max_drawdown[stress]: FAIL (46.35792206861492% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=33023.529411764706%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T14:00:25.596763+00:00');
INSERT INTO "decisions" VALUES(11,'20261030T182309Z-h-003-exploration-btc-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: FAIL (is_stable=False)", "minimum_trades[optimistic]: pass (71.0 >= 30)", "minimum_trades[base]: pass (71.0 >= 30)", "minimum_trades[conservative]: pass (71.0 >= 30)", "minimum_trades[stress]: pass (71.0 >= 30)", "net_profit[base]: FAIL (net_profit_quote=-14.80131341000001 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: FAIL (net_profit_quote=-23.471013759999998 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: FAIL (value=-22.198099827906333)", "max_drawdown[optimistic]: FAIL (27.857623579501055% <= 25.0%)", "max_drawdown[base]: FAIL (31.93539143865834% <= 25.0%)", "max_drawdown[conservative]: FAIL (37.35120467576893% <= 25.0%)", "max_drawdown[stress]: FAIL (52.874092790177286% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=1252.6553612001403%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T18:28:09.517467+00:00');
INSERT INTO "decisions" VALUES(12,'20261030T182309Z-h-003-exploration-eth-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: FAIL (is_stable=False)", "minimum_trades[optimistic]: pass (61.0 >= 30)", "minimum_trades[base]: pass (61.0 >= 30)", "minimum_trades[conservative]: pass (61.0 >= 30)", "minimum_trades[stress]: pass (61.0 >= 30)", "net_profit[base]: FAIL (net_profit_quote=-19.882731670000002 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: FAIL (net_profit_quote=-26.898651330000003 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: FAIL (value=-22.95395339118393)", "max_drawdown[optimistic]: FAIL (40.1902374754145% <= 25.0%)", "max_drawdown[base]: FAIL (42.69374180439966% <= 25.0%)", "max_drawdown[conservative]: FAIL (45.07968562205861% <= 25.0%)", "max_drawdown[stress]: FAIL (51.649737312970004% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=929.5812473061238%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T18:28:09.525188+00:00');
INSERT INTO "decisions" VALUES(13,'20261030T182309Z-h-003-exploration-bnb-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: FAIL (is_stable=False)", "minimum_trades[optimistic]: pass (50.0 >= 30)", "minimum_trades[base]: pass (50.0 >= 30)", "minimum_trades[conservative]: pass (50.0 >= 30)", "minimum_trades[stress]: pass (50.0 >= 30)", "net_profit[base]: pass (net_profit_quote=48.71615493 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=37.993779659999994 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=20.82543542575179)", "max_drawdown[optimistic]: pass (15.185501724160622% <= 25.0%)", "max_drawdown[base]: pass (17.708545861477337% <= 25.0%)", "max_drawdown[conservative]: pass (20.990062298243764% <= 25.0%)", "max_drawdown[stress]: FAIL (30.0873131784284% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=33023.529411764706%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T18:28:09.529584+00:00');
INSERT INTO "decisions" VALUES(14,'20261030T184141Z-h-007-exploration-btc-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: FAIL (is_stable=False)", "minimum_trades[optimistic]: inconclusive (23.0 < 30)", "minimum_trades[base]: inconclusive (23.0 < 30)", "minimum_trades[conservative]: inconclusive (23.0 < 30)", "minimum_trades[stress]: inconclusive (23.0 < 30)", "net_profit[base]: pass (net_profit_quote=563.30124416 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=541.557591 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=144.74508387043255)", "max_drawdown[optimistic]: FAIL (35.68258386634105% <= 25.0%)", "max_drawdown[base]: FAIL (36.74974786715349% <= 25.0%)", "max_drawdown[conservative]: FAIL (37.80885719425586% <= 25.0%)", "max_drawdown[stress]: FAIL (40.896082790015406% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=1252.6553612001403%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T18:48:20.962938+00:00');
INSERT INTO "decisions" VALUES(15,'20261030T184141Z-h-007-exploration-eth-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: inconclusive (27.0 < 30)", "minimum_trades[base]: inconclusive (27.0 < 30)", "minimum_trades[conservative]: inconclusive (27.0 < 30)", "minimum_trades[stress]: inconclusive (27.0 < 30)", "net_profit[base]: pass (net_profit_quote=329.51363899999996 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=312.68657704 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=43.39988601846997)", "max_drawdown[optimistic]: FAIL (43.68865568996132% <= 25.0%)", "max_drawdown[base]: FAIL (44.71646510161663% <= 25.0%)", "max_drawdown[conservative]: FAIL (45.733999590312926% <= 25.0%)", "max_drawdown[stress]: FAIL (48.66855268524086% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=929.5812473061238%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T18:48:20.972466+00:00');
INSERT INTO "decisions" VALUES(16,'20261030T184141Z-h-007-exploration-bnb-usdt','rejected','["lookahead: FAIL (has_bias=True)", "recursive: FAIL (is_stable=False)", "minimum_trades[optimistic]: pass (36.0 >= 30)", "minimum_trades[base]: pass (36.0 >= 30)", "minimum_trades[conservative]: pass (36.0 >= 30)", "minimum_trades[stress]: pass (36.0 >= 30)", "net_profit[base]: pass (net_profit_quote=163.34367730999998 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=149.53208684999998 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: FAIL (value=-45.833972205992865)", "max_drawdown[optimistic]: pass (23.871898460602992% <= 25.0%)", "max_drawdown[base]: FAIL (25.12737850130608% <= 25.0%)", "max_drawdown[conservative]: FAIL (26.41914790569768% <= 25.0%)", "max_drawdown[stress]: FAIL (30.975016296933976% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=33023.529411764706%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-10-30T18:48:20.977896+00:00');
INSERT INTO "decisions" VALUES(17,'20261030T182309Z-h-003-exploration-btc-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (71.0 >= 30)", "minimum_trades[base]: pass (71.0 >= 30)", "minimum_trades[conservative]: pass (71.0 >= 30)", "minimum_trades[stress]: pass (71.0 >= 30)", "net_profit[base]: FAIL (net_profit_quote=-14.80131341000001 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: FAIL (net_profit_quote=-23.471013759999998 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: FAIL (value=-22.198099827906333)", "max_drawdown[optimistic]: FAIL (27.857623579501055% <= 25.0%)", "max_drawdown[base]: FAIL (31.93539143865834% <= 25.0%)", "max_drawdown[conservative]: FAIL (37.35120467576893% <= 25.0%)", "max_drawdown[stress]: FAIL (52.874092790177286% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=1252.6553612001403%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-11-02T22:36:36.504844+00:00');
INSERT INTO "decisions" VALUES(18,'20261030T182309Z-h-003-exploration-eth-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (61.0 >= 30)", "minimum_trades[base]: pass (61.0 >= 30)", "minimum_trades[conservative]: pass (61.0 >= 30)", "minimum_trades[stress]: pass (61.0 >= 30)", "net_profit[base]: FAIL (net_profit_quote=-19.882731670000002 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: FAIL (net_profit_quote=-26.898651330000003 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: FAIL (value=-22.95395339118393)", "max_drawdown[optimistic]: FAIL (40.1902374754145% <= 25.0%)", "max_drawdown[base]: FAIL (42.69374180439966% <= 25.0%)", "max_drawdown[conservative]: FAIL (45.07968562205861% <= 25.0%)", "max_drawdown[stress]: FAIL (51.649737312970004% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=929.5812473061238%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-11-02T22:36:36.516490+00:00');
INSERT INTO "decisions" VALUES(19,'20261030T182309Z-h-003-exploration-bnb-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (50.0 >= 30)", "minimum_trades[base]: pass (50.0 >= 30)", "minimum_trades[conservative]: pass (50.0 >= 30)", "minimum_trades[stress]: pass (50.0 >= 30)", "net_profit[base]: pass (net_profit_quote=48.71615493 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=37.993779659999994 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=20.82543542575179)", "max_drawdown[optimistic]: pass (15.185501724160622% <= 25.0%)", "max_drawdown[base]: pass (17.708545861477337% <= 25.0%)", "max_drawdown[conservative]: pass (20.990062298243764% <= 25.0%)", "max_drawdown[stress]: FAIL (30.0873131784284% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=33023.529411764706%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-11-02T22:36:36.527510+00:00');
INSERT INTO "decisions" VALUES(20,'20261030T184141Z-h-007-exploration-btc-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: inconclusive (23.0 < 30)", "minimum_trades[base]: inconclusive (23.0 < 30)", "minimum_trades[conservative]: inconclusive (23.0 < 30)", "minimum_trades[stress]: inconclusive (23.0 < 30)", "net_profit[base]: pass (net_profit_quote=563.30124416 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=541.557591 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=144.74508387043255)", "max_drawdown[optimistic]: FAIL (35.68258386634105% <= 25.0%)", "max_drawdown[base]: FAIL (36.74974786715349% <= 25.0%)", "max_drawdown[conservative]: FAIL (37.80885719425586% <= 25.0%)", "max_drawdown[stress]: FAIL (40.896082790015406% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=1252.6553612001403%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-11-02T22:36:36.538361+00:00');
INSERT INTO "decisions" VALUES(21,'20261030T184141Z-h-007-exploration-bnb-usdt','rejected','["lookahead: FAIL (has_bias=True)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (36.0 >= 30)", "minimum_trades[base]: pass (36.0 >= 30)", "minimum_trades[conservative]: pass (36.0 >= 30)", "minimum_trades[stress]: pass (36.0 >= 30)", "net_profit[base]: pass (net_profit_quote=163.34367730999998 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=149.53208684999998 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: FAIL (value=-45.833972205992865)", "max_drawdown[optimistic]: pass (23.871898460602992% <= 25.0%)", "max_drawdown[base]: FAIL (25.12737850130608% <= 25.0%)", "max_drawdown[conservative]: FAIL (26.41914790569768% <= 25.0%)", "max_drawdown[stress]: FAIL (30.975016296933976% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=33023.529411764706%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-11-02T22:36:36.550068+00:00');
INSERT INTO "decisions" VALUES(22,'20261102T224114Z-h-001-exploration-btc-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (383.0 >= 30)", "minimum_trades[base]: pass (383.0 >= 30)", "minimum_trades[conservative]: pass (383.0 >= 30)", "minimum_trades[stress]: pass (383.0 >= 30)", "net_profit[base]: pass (net_profit_quote=186.46461585000003 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=61.13777701999996 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=127.49915838082975)", "max_drawdown[optimistic]: FAIL (41.186765828202056% <= 25.0%)", "max_drawdown[base]: FAIL (50.40990304969395% <= 25.0%)", "max_drawdown[conservative]: FAIL (61.83959632109356% <= 25.0%)", "max_drawdown[stress]: FAIL (87.74418653756916% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=1252.6553612001403%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-11-02T22:43:57.410945+00:00');
INSERT INTO "decisions" VALUES(23,'20261102T224114Z-h-001-exploration-eth-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (388.0 >= 30)", "minimum_trades[base]: pass (388.0 >= 30)", "minimum_trades[conservative]: pass (388.0 >= 30)", "minimum_trades[stress]: pass (388.0 >= 30)", "net_profit[base]: pass (net_profit_quote=759.6395541699999 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=380.11916413000006 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=453.67644229920256)", "max_drawdown[optimistic]: FAIL (38.17569701275583% <= 25.0%)", "max_drawdown[base]: FAIL (46.50057884100519% <= 25.0%)", "max_drawdown[conservative]: FAIL (53.70857459543185% <= 25.0%)", "max_drawdown[stress]: FAIL (75.4349517971588% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=929.5812473061238%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-11-02T22:45:58.107015+00:00');
INSERT INTO "decisions" VALUES(24,'20261102T224114Z-h-001-exploration-bnb-usdt','rejected','["lookahead: pass (has_bias=False)", "recursive: pass (is_stable=True)", "minimum_trades[optimistic]: pass (366.0 >= 30)", "minimum_trades[base]: pass (366.0 >= 30)", "minimum_trades[conservative]: pass (366.0 >= 30)", "minimum_trades[stress]: pass (366.0 >= 30)", "net_profit[base]: pass (net_profit_quote=2529.8174609499997 > required 1.0000, after 0 prior variant(s) in family)", "net_profit[conservative]: pass (net_profit_quote=1418.6806844400005 > required 1.0000, after 0 prior variant(s) in family)", "profit_excluding_best_trade[base]: pass (value=1094.4415311405198)", "max_drawdown[optimistic]: FAIL (36.28804943707682% <= 25.0%)", "max_drawdown[base]: FAIL (43.956989795109116% <= 25.0%)", "max_drawdown[conservative]: FAIL (52.02077748876348% <= 25.0%)", "max_drawdown[stress]: FAIL (74.17935077798096% <= 25.0%)", "benchmark_comparison: reported (cash=0.0%, buy_and_hold=33023.529411764706%); beating the benchmark is not required"]','bb3cf3c43dbc848b73722dd789f9e9ef837711cc744e0e18965664b600b855f7','2026-11-02T22:48:09.104869+00:00');
CREATE TABLE experiments (
    id TEXT PRIMARY KEY,                 -- experiment id, e.g. "2026-10-27-donchian-h002-explore"
    hypothesis_id TEXT NOT NULL REFERENCES hypotheses(id),
    strategy_file TEXT NOT NULL,
    strategy_sha256 TEXT NOT NULL,
    cost_scenario TEXT NOT NULL,         -- optimistic | base | conservative | stress
    split TEXT NOT NULL,                 -- exploration | validation | final_test
    command TEXT NOT NULL,               -- exact argv, space-joined, for the record
    artifact_path TEXT,
    status TEXT NOT NULL,                -- pending | running | completed | failed
    created_at_utc TEXT NOT NULL
, pair TEXT NOT NULL DEFAULT 'BTC/USDT');
INSERT INTO "experiments" VALUES('20261027T143611Z-donchian-h002-explore','H-002','user_data/strategies/DonchianBreakoutBaseline.py','2eca97e49b1a0b048dd35ac1aec5be7155b8f390f7ee32f05d1616a42305ce0e','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario',NULL,'completed','2026-10-27T14:36:11.123755+00:00','BTC/USDT');
INSERT INTO "experiments" VALUES('20261030T125953Z-donchian-h002-explore-btc-usdt','H-002','user_data/strategies/DonchianBreakoutBaseline.py','2eca97e49b1a0b048dd35ac1aec5be7155b8f390f7ee32f05d1616a42305ce0e','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario',NULL,'failed','2026-10-30T12:59:55.474754+00:00','BTC/USDT');
INSERT INTO "experiments" VALUES('20261030T130132Z-donchian-h002-explore-btc-usdt','H-002','user_data/strategies/DonchianBreakoutBaseline.py','2eca97e49b1a0b048dd35ac1aec5be7155b8f390f7ee32f05d1616a42305ce0e','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T130132Z-donchian-h002-explore-btc-usdt/raw/backtest-result-2026-10-30_13-02-06.zip','completed','2026-10-30T13:01:34.409742+00:00','BTC/USDT');
INSERT INTO "experiments" VALUES('20261030T130132Z-donchian-h002-explore-eth-usdt','H-002','user_data/strategies/DonchianBreakoutBaseline.py','2eca97e49b1a0b048dd35ac1aec5be7155b8f390f7ee32f05d1616a42305ce0e','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T130132Z-donchian-h002-explore-eth-usdt/raw/backtest-result-2026-10-30_13-03-37.zip','completed','2026-10-30T13:03:06.071633+00:00','ETH/USDT');
INSERT INTO "experiments" VALUES('20261030T130132Z-donchian-h002-explore-bnb-usdt','H-002','user_data/strategies/DonchianBreakoutBaseline.py','2eca97e49b1a0b048dd35ac1aec5be7155b8f390f7ee32f05d1616a42305ce0e','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T130132Z-donchian-h002-explore-bnb-usdt/raw/backtest-result-2026-10-30_13-05-10.zip','completed','2026-10-30T13:04:39.151053+00:00','BNB/USDT');
INSERT INTO "experiments" VALUES('20261030T133614Z-h-004-exploration-btc-usdt','H-004','user_data/strategies/SlowTimeSeriesMomentum_H004_v1.py','8d94a7412ca80660ff6b8277df7e8f1e05008256af7e4b0559b8fa7ef0c136a0','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T133614Z-h-004-exploration-btc-usdt/raw/backtest-result-2026-10-30_13-36-45.zip','completed','2026-10-30T13:36:17.041312+00:00','BTC/USDT');
INSERT INTO "experiments" VALUES('20261030T133614Z-h-004-exploration-eth-usdt','H-004','user_data/strategies/SlowTimeSeriesMomentum_H004_v1.py','8d94a7412ca80660ff6b8277df7e8f1e05008256af7e4b0559b8fa7ef0c136a0','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T133614Z-h-004-exploration-eth-usdt/raw/backtest-result-2026-10-30_13-39-00.zip','completed','2026-10-30T13:38:30.430638+00:00','ETH/USDT');
INSERT INTO "experiments" VALUES('20261030T133614Z-h-004-exploration-bnb-usdt','H-004','user_data/strategies/SlowTimeSeriesMomentum_H004_v1.py','8d94a7412ca80660ff6b8277df7e8f1e05008256af7e4b0559b8fa7ef0c136a0','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T133614Z-h-004-exploration-bnb-usdt/raw/backtest-result-2026-10-30_13-41-39.zip','completed','2026-10-30T13:41:04.126467+00:00','BNB/USDT');
INSERT INTO "experiments" VALUES('20261030T135346Z-h-005-exploration-btc-usdt','H-005','user_data/strategies/VolatilitySqueezeBreakout_H005_v1.py','b690cf994ad318fe50be372dc434b0e5670b1c4ffea595c27b8edb84de469eb7','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T135346Z-h-005-exploration-btc-usdt/raw/backtest-result-2026-10-30_13-54-17.zip','completed','2026-10-30T13:53:49.069127+00:00','BTC/USDT');
INSERT INTO "experiments" VALUES('20261030T135346Z-h-005-exploration-eth-usdt','H-005','user_data/strategies/VolatilitySqueezeBreakout_H005_v1.py','b690cf994ad318fe50be372dc434b0e5670b1c4ffea595c27b8edb84de469eb7','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T135346Z-h-005-exploration-eth-usdt/raw/backtest-result-2026-10-30_13-56-46.zip','completed','2026-10-30T13:56:11.092804+00:00','ETH/USDT');
INSERT INTO "experiments" VALUES('20261030T135346Z-h-005-exploration-bnb-usdt','H-005','user_data/strategies/VolatilitySqueezeBreakout_H005_v1.py','b690cf994ad318fe50be372dc434b0e5670b1c4ffea595c27b8edb84de469eb7','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T135346Z-h-005-exploration-bnb-usdt/raw/backtest-result-2026-10-30_13-59-02.zip','completed','2026-10-30T13:58:31.739322+00:00','BNB/USDT');
INSERT INTO "experiments" VALUES('20261030T174629Z-h-006-exploration-btc-usdt','H-006','user_data/strategies/RegimeGatedPullbackTrend_H006_v1.py','6a5ac4247dfe14fd069d20e1a09570911395a5e27f91710282ba6a849cf5c117','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario',NULL,'failed','2026-10-30T17:46:31.717794+00:00','BTC/USDT');
INSERT INTO "experiments" VALUES('20261030T182309Z-h-003-exploration-btc-usdt','H-003','user_data/strategies/BollingerMeanReversionBaseline.py','da38ebf7d4db29c44a2a6b1d3f146ac3b07cf5dda2ca6ddcc6478375a873c75a','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T182309Z-h-003-exploration-btc-usdt/raw/backtest-result-2026-10-30_18-23-38.zip','completed','2026-10-30T18:23:11.787659+00:00','BTC/USDT');
INSERT INTO "experiments" VALUES('20261030T182309Z-h-003-exploration-eth-usdt','H-003','user_data/strategies/BollingerMeanReversionBaseline.py','da38ebf7d4db29c44a2a6b1d3f146ac3b07cf5dda2ca6ddcc6478375a873c75a','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T182309Z-h-003-exploration-eth-usdt/raw/backtest-result-2026-10-30_18-25-18.zip','completed','2026-10-30T18:24:50.262590+00:00','ETH/USDT');
INSERT INTO "experiments" VALUES('20261030T182309Z-h-003-exploration-bnb-usdt','H-003','user_data/strategies/BollingerMeanReversionBaseline.py','da38ebf7d4db29c44a2a6b1d3f146ac3b07cf5dda2ca6ddcc6478375a873c75a','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T182309Z-h-003-exploration-bnb-usdt/raw/backtest-result-2026-10-30_18-27-00.zip','completed','2026-10-30T18:26:33.015484+00:00','BNB/USDT');
INSERT INTO "experiments" VALUES('20261030T184141Z-h-007-exploration-btc-usdt','H-007','user_data/strategies/RisingTrendBreakoutGate_H007_v1.py','38972085a0972c4d8c2a6d30571951d8ca59ecd062844d6efb83974717e9cb86','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T184141Z-h-007-exploration-btc-usdt/raw/backtest-result-2026-10-30_18-42-12.zip','completed','2026-10-30T18:41:43.618221+00:00','BTC/USDT');
INSERT INTO "experiments" VALUES('20261030T184141Z-h-007-exploration-eth-usdt','H-007','user_data/strategies/RisingTrendBreakoutGate_H007_v1.py','38972085a0972c4d8c2a6d30571951d8ca59ecd062844d6efb83974717e9cb86','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T184141Z-h-007-exploration-eth-usdt/raw/backtest-result-2026-10-30_18-44-38.zip','completed','2026-10-30T18:44:11.036444+00:00','ETH/USDT');
INSERT INTO "experiments" VALUES('20261030T184141Z-h-007-exploration-bnb-usdt','H-007','user_data/strategies/RisingTrendBreakoutGate_H007_v1.py','38972085a0972c4d8c2a6d30571951d8ca59ecd062844d6efb83974717e9cb86','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261030T184141Z-h-007-exploration-bnb-usdt/raw/backtest-result-2026-10-30_18-46-51.zip','completed','2026-10-30T18:46:22.997087+00:00','BNB/USDT');
INSERT INTO "experiments" VALUES('20261102T224114Z-h-001-exploration-btc-usdt','H-001','user_data/strategies/SmaTrendBaseline.py','0edc921c5e0b507dcf7b9128aeebb54e624d68d6e4f5d13e8874218e6fadebcc','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261102T224114Z-h-001-exploration-btc-usdt/raw/backtest-result-2026-11-02_22-42-25.zip','completed','2026-11-02T22:41:27.045657+00:00','BTC/USDT');
INSERT INTO "experiments" VALUES('20261102T224114Z-h-001-exploration-eth-usdt','H-001','user_data/strategies/SmaTrendBaseline.py','0edc921c5e0b507dcf7b9128aeebb54e624d68d6e4f5d13e8874218e6fadebcc','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261102T224114Z-h-001-exploration-eth-usdt/raw/backtest-result-2026-11-02_22-44-36.zip','completed','2026-11-02T22:43:57.420588+00:00','ETH/USDT');
INSERT INTO "experiments" VALUES('20261102T224114Z-h-001-exploration-bnb-usdt','H-001','user_data/strategies/SmaTrendBaseline.py','0edc921c5e0b507dcf7b9128aeebb54e624d68d6e4f5d13e8874218e6fadebcc','multi:optimistic,base,conservative,stress','exploration','see raw/*.stdout.txt per cost scenario','research/experiments/20261102T224114Z-h-001-exploration-bnb-usdt/raw/backtest-result-2026-11-02_22-46-38.zip','completed','2026-11-02T22:45:58.114163+00:00','BNB/USDT');
CREATE TABLE hypotheses (
    id TEXT PRIMARY KEY,                 -- e.g. "H-004"
    family TEXT NOT NULL,
    ex_ante_rule TEXT NOT NULL,
    proposed_at_utc TEXT NOT NULL,
    data_visible_at_proposal TEXT NOT NULL,  -- what data window was visible when the rule was fixed
    status TEXT NOT NULL,                -- e.g. "proposed", "frozen reference", "candidate", "rejected"
    notes TEXT
);
INSERT INTO "hypotheses" VALUES('H-001','SmaTrendBaseline','SMA20/SMA50 cross, close > SMA200, stop -10%','2026-10-20T00:00:00Z','BTC/USDT 1h through 2026-10-20','frozen reference','Original result (1 trade) was a harness artifact. Re-tested 2026-11-02 under the corrected harness (exploration, BTC/ETH/BNB): rejected on all three, drawdown 44-50% at base, 74-88% at stress; lookahead and recursive pass.');
INSERT INTO "hypotheses" VALUES('H-002','DonchianBreakoutBaseline','Close > prior 20-candle high; exit below prior 10-candle low; stop -10%','2026-10-20T00:00:00Z','BTC/USDT 1h through 2026-10-20','rejected at exploration','Corrected harness, exploration on BTC/ETH/BNB: positive only at the optimistic cost, drawdown 60-98%. Do not select by return alone.');
INSERT INTO "hypotheses" VALUES('H-003','BollingerMeanReversionBaseline','Lower 20-band, RSI14 < 30, close > SMA200; exit at middle band; stop -10%','2026-10-20T00:00:00Z','BTC/USDT 1h through 2026-10-20','rejected at exploration','Not yet tested under the corrected harness. Trend-failure risk.');
INSERT INTO "hypotheses" VALUES('H-004','SlowTimeSeriesMomentum','Use closed 1h candles only; signals evaluated at bar close, order executed at next bar open. Long only, one position, whole balance. ENTRY: close > highest high of the prior 1440 bars (60 days, excluding current bar) AND close > SMA(4800 bars, 200 days) of close AND no open position. EXIT: close < lowest low of the prior 720 bars (30 days, excluding current bar), OR close below entry price by 15% (hard stop, checked on closed bars). After any exit, no re-entry until at least 168 bars (7 days) have passed. No other filters, no pyramiding, no take-profit.','2026-10-30T13:28:34.345485+00:00','BTC, ETH, BNB 1h through 2026-10-30; no result data viewed beyond the context file''s exploration summaries','invalid: implementation deviated from rule','Exploration ran on an implementation that used min_periods=1440 on the 4800-candle SMA (to satisfy a too-short smoke window) and without the 168-candle cooldown (backtest ran without --enable-protections). Both harness flaws are fixed. The rule itself is untested. Recorded results: research/experiments/H-004-exploration/ and the 20261030T133614Z-h-004-* manifests.');
INSERT INTO "hypotheses" VALUES('H-005','VolatilitySqueezeBreakout','Closed 1h candles only; signals evaluated at bar close, order executed at next bar open. Long only, one position, whole balance. Definitions (all use completed bars): R(t) = (highest high of the 168 bars ending at t - lowest low of the 168 bars ending at t) / close(t). Squeeze(t) is true if R(t) is <= the 20th percentile of R over the 2160 bars ending at t-1 (rolling quantile 0.20, excluding the current bar). ENTRY at close of bar t when ALL hold: (1) Squeeze was true on at least one of the previous 24 bars (t-24..t-1); (2) close(t) > highest high of the prior 168 bars (t-168..t-1, excluding current bar); (3) close(t) > SMA(2400) of close; (4) no open position; (5) cooldown satisfied. EXIT at close of bar t when close(t) < lowest low of the prior 336 bars (t-336..t-1, excluding current), or via the hard stop. STOP-LOSS: fixed 8% below entry price (native intrabar stop). COOLDOWN: no re-entry for 72 candles after any exit. No take-profit, no pyramiding, no other filters. Warm-up: 2400 bars.','2026-10-30T13:49:38.324198+00:00','No price data viewed; only the context file and validation protocol (BTC, ETH, BNB 1h description through 2026-10-30).','rejected at exploration','Long breakout after a multi-day volatility squeeze in an established uptrend');
INSERT INTO "hypotheses" VALUES('H-006','RegimeGatedPullbackTrend','Closed 1h candles only; signals evaluated at bar close, order executed at next bar open. Long only, one position, whole balance. REGIME at bar t (all must hold): (a) close(t) > SMA(4800) of close; (b) SMA(2400)(t) > SMA(4800)(t); (c) SMA(4800)(t) > SMA(4800)(t-720). ENTRY at close of bar t when REGIME holds AND min(close over bars t-48..t-1) <= 0.95 * max(high over bars t-336..t-1) (a pullback of at least 5% from the 14-day high occurred within the last 48 bars) AND close(t) > SMA(48) of close AND close(t-1) <= SMA(48) at t-1 (fresh recovery cross above the 2-day mean) AND no open position AND cooldown satisfied. EXIT at close of bar t (executed next open) when any of: close(t) >= max(high over bars t-336..t-1) (prior 14-day high retested); close(t) < SMA(4800)(t) (regime lost); 240 bars have elapsed since entry (time stop). STOP-LOSS: fixed 5% below entry price (native intrabar stop). COOLDOWN: no re-entry for 48 candles after any exit. No pyramiding, no other filters. Warm-up: 5520 bars.','2026-10-30T17:42:27.332302+00:00','BTC, ETH, BNB 1h through 2026-10-20; exploration results listed in the context file only','failed','Bull-regime-only pullback re-entry with long-term slope gate and tight fixed stop');
INSERT INTO "hypotheses" VALUES('H-007','RisingTrendBreakoutGate','Closed 1h candles only; signals evaluated at bar close, order executed at next bar open. Long only, one position, whole balance. REGIME at bar t (all must hold): (a) SMA(1200)(t) > SMA(2400)(t); (b) SMA(2400)(t) > SMA(2400)(t-480) (long mean rising over the last 20 days); (c) close(t) > SMA(1200)(t). ENTRY at close of bar t when REGIME holds AND close(t) > highest high of the prior 480 bars (t-480..t-1, excluding current bar) AND no open position AND cooldown satisfied. EXIT at close of bar t (executed next open) when close(t) < lowest low of the prior 240 bars (t-240..t-1, excluding current bar) OR close(t) < SMA(1200)(t) (regime lost). STOP-LOSS: fixed 6% below entry price (native intrabar stop). COOLDOWN: no re-entry for 120 candles after any exit. No take-profit, no pyramiding, no other filters. Warm-up: 2880 bars (SMA(2400) plus 480-bar slope lag); startup_candle_count should be set to 2880 or a bit more (at most 4500) so recursive analysis is stable.','2026-10-30T18:29:04.404068+00:00','BTC, ETH, BNB 1h exploration-period summary results listed in the context file only, through 2026-10-30; no validation results seen','rejected at exploration','20-day breakout only inside a confirmed, rising multi-month uptrend, with 10-day channel exit');
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    name TEXT NOT NULL,
    value REAL,
    text_value TEXT,                     -- for non-numeric metrics (e.g. has_bias, notes)
    UNIQUE(experiment_id, name)
);
INSERT INTO "metrics" VALUES(1,'20261027T143611Z-donchian-h002-explore','trades__optimistic',1.0,NULL);
INSERT INTO "metrics" VALUES(2,'20261027T143611Z-donchian-h002-explore','net_profit_quote__optimistic',-3.92002874,NULL);
INSERT INTO "metrics" VALUES(3,'20261027T143611Z-donchian-h002-explore','net_profit_excl_best_trade__optimistic',0.0,NULL);
INSERT INTO "metrics" VALUES(4,'20261027T143611Z-donchian-h002-explore','max_drawdown_pct__optimistic',3.920028740000006007e+00,NULL);
INSERT INTO "metrics" VALUES(5,'20261027T143611Z-donchian-h002-explore','trades__base',1.0,NULL);
INSERT INTO "metrics" VALUES(6,'20261027T143611Z-donchian-h002-explore','net_profit_quote__base',-4.06698331,NULL);
INSERT INTO "metrics" VALUES(7,'20261027T143611Z-donchian-h002-explore','net_profit_excl_best_trade__base',0.0,NULL);
INSERT INTO "metrics" VALUES(8,'20261027T143611Z-donchian-h002-explore','max_drawdown_pct__base',4.066983309999997686e+00,NULL);
INSERT INTO "metrics" VALUES(9,'20261027T143611Z-donchian-h002-explore','trades__conservative',1.0,NULL);
INSERT INTO "metrics" VALUES(10,'20261027T143611Z-donchian-h002-explore','net_profit_quote__conservative',-4.21393789,NULL);
INSERT INTO "metrics" VALUES(11,'20261027T143611Z-donchian-h002-explore','net_profit_excl_best_trade__conservative',0.0,NULL);
INSERT INTO "metrics" VALUES(12,'20261027T143611Z-donchian-h002-explore','max_drawdown_pct__conservative',4.213937889999996856e+00,NULL);
INSERT INTO "metrics" VALUES(13,'20261027T143611Z-donchian-h002-explore','trades__stress',1.0,NULL);
INSERT INTO "metrics" VALUES(14,'20261027T143611Z-donchian-h002-explore','net_profit_quote__stress',-4.65480162,NULL);
INSERT INTO "metrics" VALUES(15,'20261027T143611Z-donchian-h002-explore','net_profit_excl_best_trade__stress',0.0,NULL);
INSERT INTO "metrics" VALUES(16,'20261027T143611Z-donchian-h002-explore','max_drawdown_pct__stress',4.65480162000000064e+00,NULL);
INSERT INTO "metrics" VALUES(17,'20261027T143611Z-donchian-h002-explore','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(18,'20261027T143611Z-donchian-h002-explore','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(19,'20261027T143611Z-donchian-h002-explore','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(20,'20261027T143611Z-donchian-h002-explore','benchmark_buy_and_hold_return_pct',-2.974143029368761048e+01,NULL);
INSERT INTO "metrics" VALUES(21,'20261030T130132Z-donchian-h002-explore-btc-usdt','trades__optimistic',787.0,NULL);
INSERT INTO "metrics" VALUES(22,'20261030T130132Z-donchian-h002-explore-btc-usdt','net_profit_quote__optimistic',5.725055569999997829e+01,NULL);
INSERT INTO "metrics" VALUES(23,'20261030T130132Z-donchian-h002-explore-btc-usdt','net_profit_excl_best_trade__optimistic',1.112994237999998149e+01,NULL);
INSERT INTO "metrics" VALUES(24,'20261030T130132Z-donchian-h002-explore-btc-usdt','max_drawdown_pct__optimistic',6.076637802244242436e+01,NULL);
INSERT INTO "metrics" VALUES(25,'20261030T130132Z-donchian-h002-explore-btc-usdt','trades__base',787.0,NULL);
INSERT INTO "metrics" VALUES(26,'20261030T130132Z-donchian-h002-explore-btc-usdt','net_profit_quote__base',-51.69842568,NULL);
INSERT INTO "metrics" VALUES(27,'20261030T130132Z-donchian-h002-explore-btc-usdt','net_profit_excl_best_trade__base',-9.179509390999999142e+01,NULL);
INSERT INTO "metrics" VALUES(28,'20261030T130132Z-donchian-h002-explore-btc-usdt','max_drawdown_pct__base',7.983078863318425534e+01,NULL);
INSERT INTO "metrics" VALUES(29,'20261030T130132Z-donchian-h002-explore-btc-usdt','trades__conservative',787.0,NULL);
INSERT INTO "metrics" VALUES(30,'20261030T130132Z-donchian-h002-explore-btc-usdt','net_profit_quote__conservative',-85.11376844,NULL);
INSERT INTO "metrics" VALUES(31,'20261030T130132Z-donchian-h002-explore-btc-usdt','net_profit_excl_best_trade__conservative',-123.04454423,NULL);
INSERT INTO "metrics" VALUES(32,'20261030T130132Z-donchian-h002-explore-btc-usdt','max_drawdown_pct__conservative',9.29608948147399871e+01,NULL);
INSERT INTO "metrics" VALUES(33,'20261030T130132Z-donchian-h002-explore-btc-usdt','trades__stress',498.0,NULL);
INSERT INTO "metrics" VALUES(34,'20261030T130132Z-donchian-h002-explore-btc-usdt','net_profit_quote__stress',-9.4477328440000008e+01,NULL);
INSERT INTO "metrics" VALUES(35,'20261030T130132Z-donchian-h002-explore-btc-usdt','net_profit_excl_best_trade__stress',-1.265053597100000075e+02,NULL);
INSERT INTO "metrics" VALUES(36,'20261030T130132Z-donchian-h002-explore-btc-usdt','max_drawdown_pct__stress',9.68546986403552382e+01,NULL);
INSERT INTO "metrics" VALUES(37,'20261030T130132Z-donchian-h002-explore-btc-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(38,'20261030T130132Z-donchian-h002-explore-btc-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(39,'20261030T130132Z-donchian-h002-explore-btc-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(40,'20261030T130132Z-donchian-h002-explore-btc-usdt','benchmark_buy_and_hold_return_pct',1.252655361200140305e+03,NULL);
INSERT INTO "metrics" VALUES(41,'20261030T130132Z-donchian-h002-explore-eth-usdt','trades__optimistic',819.0,NULL);
INSERT INTO "metrics" VALUES(42,'20261030T130132Z-donchian-h002-explore-eth-usdt','net_profit_quote__optimistic',1.433653772900000262e+02,NULL);
INSERT INTO "metrics" VALUES(43,'20261030T130132Z-donchian-h002-explore-eth-usdt','net_profit_excl_best_trade__optimistic',7.461777119000002755e+01,NULL);
INSERT INTO "metrics" VALUES(44,'20261030T130132Z-donchian-h002-explore-eth-usdt','max_drawdown_pct__optimistic',5.843094234664827268e+01,NULL);
INSERT INTO "metrics" VALUES(45,'20261030T130132Z-donchian-h002-explore-eth-usdt','trades__base',819.0,NULL);
INSERT INTO "metrics" VALUES(46,'20261030T130132Z-donchian-h002-explore-eth-usdt','net_profit_quote__base',-2.880459704999998394e+01,NULL);
INSERT INTO "metrics" VALUES(47,'20261030T130132Z-donchian-h002-explore-eth-usdt','net_profit_excl_best_trade__base',-7.129084771999998794e+01,NULL);
INSERT INTO "metrics" VALUES(48,'20261030T130132Z-donchian-h002-explore-eth-usdt','max_drawdown_pct__base',73.622012350602,NULL);
INSERT INTO "metrics" VALUES(49,'20261030T130132Z-donchian-h002-explore-eth-usdt','trades__conservative',819.0,NULL);
INSERT INTO "metrics" VALUES(50,'20261030T130132Z-donchian-h002-explore-eth-usdt','net_profit_quote__conservative',-7.915442569999999022e+01,NULL);
INSERT INTO "metrics" VALUES(51,'20261030T130132Z-donchian-h002-explore-eth-usdt','net_profit_excl_best_trade__conservative',-1.191163971499999831e+02,NULL);
INSERT INTO "metrics" VALUES(52,'20261030T130132Z-donchian-h002-explore-eth-usdt','max_drawdown_pct__conservative',8.386254383862802797e+01,NULL);
INSERT INTO "metrics" VALUES(53,'20261030T130132Z-donchian-h002-explore-eth-usdt','trades__stress',331.0,NULL);
INSERT INTO "metrics" VALUES(54,'20261030T130132Z-donchian-h002-explore-eth-usdt','net_profit_quote__stress',-94.51028994,NULL);
INSERT INTO "metrics" VALUES(55,'20261030T130132Z-donchian-h002-explore-eth-usdt','net_profit_excl_best_trade__stress',-127.74627002,NULL);
INSERT INTO "metrics" VALUES(56,'20261030T130132Z-donchian-h002-explore-eth-usdt','max_drawdown_pct__stress',9.51221524135581121e+01,NULL);
INSERT INTO "metrics" VALUES(57,'20261030T130132Z-donchian-h002-explore-eth-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(58,'20261030T130132Z-donchian-h002-explore-eth-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(59,'20261030T130132Z-donchian-h002-explore-eth-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(60,'20261030T130132Z-donchian-h002-explore-eth-usdt','benchmark_buy_and_hold_return_pct',9.29581247306123827e+02,NULL);
INSERT INTO "metrics" VALUES(61,'20261030T130132Z-donchian-h002-explore-bnb-usdt','trades__optimistic',835.0,NULL);
INSERT INTO "metrics" VALUES(62,'20261030T130132Z-donchian-h002-explore-bnb-usdt','net_profit_quote__optimistic',4.639373102499994275e+02,NULL);
INSERT INTO "metrics" VALUES(63,'20261030T130132Z-donchian-h002-explore-bnb-usdt','net_profit_excl_best_trade__optimistic',-2.932882685300005505e+02,NULL);
INSERT INTO "metrics" VALUES(64,'20261030T130132Z-donchian-h002-explore-bnb-usdt','max_drawdown_pct__optimistic',8.120388566438248291e+01,NULL);
INSERT INTO "metrics" VALUES(65,'20261030T130132Z-donchian-h002-explore-bnb-usdt','trades__base',835.0,NULL);
INSERT INTO "metrics" VALUES(66,'20261030T130132Z-donchian-h002-explore-bnb-usdt','net_profit_quote__base',6.096892004999995152e+01,NULL);
INSERT INTO "metrics" VALUES(67,'20261030T130132Z-donchian-h002-explore-bnb-usdt','net_profit_excl_best_trade__base',-3.529289343700000358e+02,NULL);
INSERT INTO "metrics" VALUES(68,'20261030T130132Z-donchian-h002-explore-bnb-usdt','max_drawdown_pct__base',8.85554188837024725e+01,NULL);
INSERT INTO "metrics" VALUES(69,'20261030T130132Z-donchian-h002-explore-bnb-usdt','trades__conservative',835.0,NULL);
INSERT INTO "metrics" VALUES(70,'20261030T130132Z-donchian-h002-explore-bnb-usdt','net_profit_quote__conservative',-5.409181266999991067e+01,NULL);
INSERT INTO "metrics" VALUES(71,'20261030T130132Z-donchian-h002-explore-bnb-usdt','net_profit_excl_best_trade__conservative',-2.800401721199999087e+02,NULL);
INSERT INTO "metrics" VALUES(72,'20261030T130132Z-donchian-h002-explore-bnb-usdt','max_drawdown_pct__conservative',9.32115106908306502e+01,NULL);
INSERT INTO "metrics" VALUES(73,'20261030T130132Z-donchian-h002-explore-bnb-usdt','trades__stress',655.0,NULL);
INSERT INTO "metrics" VALUES(74,'20261030T130132Z-donchian-h002-explore-bnb-usdt','net_profit_quote__stress',-9.46135353299998911e+01,NULL);
INSERT INTO "metrics" VALUES(75,'20261030T130132Z-donchian-h002-explore-bnb-usdt','net_profit_excl_best_trade__stress',-2.762465993599998911e+02,NULL);
INSERT INTO "metrics" VALUES(76,'20261030T130132Z-donchian-h002-explore-bnb-usdt','max_drawdown_pct__stress',98.4342718005962,NULL);
INSERT INTO "metrics" VALUES(77,'20261030T130132Z-donchian-h002-explore-bnb-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(78,'20261030T130132Z-donchian-h002-explore-bnb-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(79,'20261030T130132Z-donchian-h002-explore-bnb-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(80,'20261030T130132Z-donchian-h002-explore-bnb-usdt','benchmark_buy_and_hold_return_pct',3.302352941176470631e+04,NULL);
INSERT INTO "metrics" VALUES(81,'20261030T133614Z-h-004-exploration-btc-usdt','trades__optimistic',13.0,NULL);
INSERT INTO "metrics" VALUES(82,'20261030T133614Z-h-004-exploration-btc-usdt','net_profit_quote__optimistic',1942.58294189,NULL);
INSERT INTO "metrics" VALUES(83,'20261030T133614Z-h-004-exploration-btc-usdt','net_profit_excl_best_trade__optimistic',4.166974503705105235e+02,NULL);
INSERT INTO "metrics" VALUES(84,'20261030T133614Z-h-004-exploration-btc-usdt','max_drawdown_pct__optimistic',7.654851085305318215e+00,NULL);
INSERT INTO "metrics" VALUES(85,'20261030T133614Z-h-004-exploration-btc-usdt','trades__base',13.0,NULL);
INSERT INTO "metrics" VALUES(86,'20261030T133614Z-h-004-exploration-btc-usdt','net_profit_quote__base',1.906204817049999747e+03,NULL);
INSERT INTO "metrics" VALUES(87,'20261030T133614Z-h-004-exploration-btc-usdt','net_profit_excl_best_trade__base',4.074800835984503919e+02,NULL);
INSERT INTO "metrics" VALUES(88,'20261030T133614Z-h-004-exploration-btc-usdt','max_drawdown_pct__base',7.801052919545275798e+00,NULL);
INSERT INTO "metrics" VALUES(89,'20261030T133614Z-h-004-exploration-btc-usdt','trades__conservative',13.0,NULL);
INSERT INTO "metrics" VALUES(90,'20261030T133614Z-h-004-exploration-btc-usdt','net_profit_quote__conservative',1.870207344440000269e+03,NULL);
INSERT INTO "metrics" VALUES(91,'20261030T133614Z-h-004-exploration-btc-usdt','net_profit_excl_best_trade__conservative',3.984271218595376923e+02,NULL);
INSERT INTO "metrics" VALUES(92,'20261030T133614Z-h-004-exploration-btc-usdt','max_drawdown_pct__conservative',7.944618666954156083e+00,NULL);
INSERT INTO "metrics" VALUES(93,'20261030T133614Z-h-004-exploration-btc-usdt','trades__stress',13.0,NULL);
INSERT INTO "metrics" VALUES(94,'20261030T133614Z-h-004-exploration-btc-usdt','net_profit_quote__stress',1.765583521709999559e+03,NULL);
INSERT INTO "metrics" VALUES(95,'20261030T133614Z-h-004-exploration-btc-usdt','net_profit_excl_best_trade__stress',3.722255121686899315e+02,NULL);
INSERT INTO "metrics" VALUES(96,'20261030T133614Z-h-004-exploration-btc-usdt','max_drawdown_pct__stress',8.376998959846325476e+00,NULL);
INSERT INTO "metrics" VALUES(97,'20261030T133614Z-h-004-exploration-btc-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(98,'20261030T133614Z-h-004-exploration-btc-usdt','recursive_is_stable',NULL,'false');
INSERT INTO "metrics" VALUES(99,'20261030T133614Z-h-004-exploration-btc-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(100,'20261030T133614Z-h-004-exploration-btc-usdt','benchmark_buy_and_hold_return_pct',1.252655361200140305e+03,NULL);
INSERT INTO "metrics" VALUES(101,'20261030T133614Z-h-004-exploration-eth-usdt','trades__optimistic',15.0,NULL);
INSERT INTO "metrics" VALUES(102,'20261030T133614Z-h-004-exploration-eth-usdt','net_profit_quote__optimistic',1530.20174889,NULL);
INSERT INTO "metrics" VALUES(103,'20261030T133614Z-h-004-exploration-eth-usdt','net_profit_excl_best_trade__optimistic',2.758942704376138976e+02,NULL);
INSERT INTO "metrics" VALUES(104,'20261030T133614Z-h-004-exploration-eth-usdt','max_drawdown_pct__optimistic',3.607573372222109498e+01,NULL);
INSERT INTO "metrics" VALUES(105,'20261030T133614Z-h-004-exploration-eth-usdt','trades__base',15.0,NULL);
INSERT INTO "metrics" VALUES(106,'20261030T133614Z-h-004-exploration-eth-usdt','net_profit_quote__base',1495.8396605,NULL);
INSERT INTO "metrics" VALUES(107,'20261030T133614Z-h-004-exploration-eth-usdt','net_profit_excl_best_trade__base',2.680827833160337264e+02,NULL);
INSERT INTO "metrics" VALUES(108,'20261030T133614Z-h-004-exploration-eth-usdt','max_drawdown_pct__base',3.667390021006673351e+01,NULL);
INSERT INTO "metrics" VALUES(109,'20261030T133614Z-h-004-exploration-eth-usdt','trades__conservative',15.0,NULL);
INSERT INTO "metrics" VALUES(110,'20261030T133614Z-h-004-exploration-eth-usdt','net_profit_quote__conservative',1.461869894340000201e+03,NULL);
INSERT INTO "metrics" VALUES(111,'20261030T133614Z-h-004-exploration-eth-usdt','net_profit_excl_best_trade__conservative',2.604336074276269529e+02,NULL);
INSERT INTO "metrics" VALUES(112,'20261030T133614Z-h-004-exploration-eth-usdt','max_drawdown_pct__conservative',3.726497975660160478e+01,NULL);
INSERT INTO "metrics" VALUES(113,'20261030T133614Z-h-004-exploration-eth-usdt','trades__stress',15.0,NULL);
INSERT INTO "metrics" VALUES(114,'20261030T133614Z-h-004-exploration-eth-usdt','net_profit_quote__stress',1.364605768100000205e+03,NULL);
INSERT INTO "metrics" VALUES(115,'20261030T133614Z-h-004-exploration-eth-usdt','net_profit_excl_best_trade__stress',2.384264942193527759e+02,NULL);
INSERT INTO "metrics" VALUES(116,'20261030T133614Z-h-004-exploration-eth-usdt','max_drawdown_pct__stress',39.1441991321387,NULL);
INSERT INTO "metrics" VALUES(117,'20261030T133614Z-h-004-exploration-eth-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(118,'20261030T133614Z-h-004-exploration-eth-usdt','recursive_is_stable',NULL,'false');
INSERT INTO "metrics" VALUES(119,'20261030T133614Z-h-004-exploration-eth-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(120,'20261030T133614Z-h-004-exploration-eth-usdt','benchmark_buy_and_hold_return_pct',9.29581247306123827e+02,NULL);
INSERT INTO "metrics" VALUES(121,'20261030T133614Z-h-004-exploration-bnb-usdt','trades__optimistic',16.0,NULL);
INSERT INTO "metrics" VALUES(122,'20261030T133614Z-h-004-exploration-bnb-usdt','net_profit_quote__optimistic',2096.71894746,NULL);
INSERT INTO "metrics" VALUES(123,'20261030T133614Z-h-004-exploration-bnb-usdt','net_profit_excl_best_trade__optimistic',9.37265028064848308e+01,NULL);
INSERT INTO "metrics" VALUES(124,'20261030T133614Z-h-004-exploration-bnb-usdt','max_drawdown_pct__optimistic',4.164563524366887037e+01,NULL);
INSERT INTO "metrics" VALUES(125,'20261030T133614Z-h-004-exploration-bnb-usdt','trades__base',16.0,NULL);
INSERT INTO "metrics" VALUES(126,'20261030T133614Z-h-004-exploration-bnb-usdt','net_profit_quote__base',2.045701840079999783e+03,NULL);
INSERT INTO "metrics" VALUES(127,'20261030T133614Z-h-004-exploration-bnb-usdt','net_profit_excl_best_trade__base',8.941631952877114032e+01,NULL);
INSERT INTO "metrics" VALUES(128,'20261030T133614Z-h-004-exploration-bnb-usdt','max_drawdown_pct__base',4.210727432174309114e+01,NULL);
INSERT INTO "metrics" VALUES(129,'20261030T133614Z-h-004-exploration-bnb-usdt','trades__conservative',16.0,NULL);
INSERT INTO "metrics" VALUES(130,'20261030T133614Z-h-004-exploration-bnb-usdt','net_profit_quote__conservative',1995.4013924,NULL);
INSERT INTO "metrics" VALUES(131,'20261030T133614Z-h-004-exploration-bnb-usdt','net_profit_excl_best_trade__conservative',8.520202173039112381e+01,NULL);
INSERT INTO "metrics" VALUES(132,'20261030T133614Z-h-004-exploration-bnb-usdt','max_drawdown_pct__conservative',42.5663456608892,NULL);
INSERT INTO "metrics" VALUES(133,'20261030T133614Z-h-004-exploration-bnb-usdt','trades__stress',16.0,NULL);
INSERT INTO "metrics" VALUES(134,'20261030T133614Z-h-004-exploration-bnb-usdt','net_profit_quote__stress',1852.36125169,NULL);
INSERT INTO "metrics" VALUES(135,'20261030T133614Z-h-004-exploration-bnb-usdt','net_profit_excl_best_trade__stress',7.311330515790817231e+01,NULL);
INSERT INTO "metrics" VALUES(136,'20261030T133614Z-h-004-exploration-bnb-usdt','max_drawdown_pct__stress',4.392441636031587393e+01,NULL);
INSERT INTO "metrics" VALUES(137,'20261030T133614Z-h-004-exploration-bnb-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(138,'20261030T133614Z-h-004-exploration-bnb-usdt','recursive_is_stable',NULL,'false');
INSERT INTO "metrics" VALUES(139,'20261030T133614Z-h-004-exploration-bnb-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(140,'20261030T133614Z-h-004-exploration-bnb-usdt','benchmark_buy_and_hold_return_pct',3.302352941176470631e+04,NULL);
INSERT INTO "metrics" VALUES(141,'20261030T135346Z-h-005-exploration-btc-usdt','trades__optimistic',31.0,NULL);
INSERT INTO "metrics" VALUES(142,'20261030T135346Z-h-005-exploration-btc-usdt','net_profit_quote__optimistic',5.494849663899998404e+02,NULL);
INSERT INTO "metrics" VALUES(143,'20261030T135346Z-h-005-exploration-btc-usdt','net_profit_excl_best_trade__optimistic',1.403385722368040546e+02,NULL);
INSERT INTO "metrics" VALUES(144,'20261030T135346Z-h-005-exploration-btc-usdt','max_drawdown_pct__optimistic',4.905119695159429227e+01,NULL);
INSERT INTO "metrics" VALUES(145,'20261030T135346Z-h-005-exploration-btc-usdt','trades__base',31.0,NULL);
INSERT INTO "metrics" VALUES(146,'20261030T135346Z-h-005-exploration-btc-usdt','net_profit_quote__base',520.36933964,NULL);
INSERT INTO "metrics" VALUES(147,'20261030T135346Z-h-005-exploration-btc-usdt','net_profit_excl_best_trade__base',1.297630497897358168e+02,NULL);
INSERT INTO "metrics" VALUES(148,'20261030T135346Z-h-005-exploration-btc-usdt','max_drawdown_pct__base',5.0119209325097124e+01,NULL);
INSERT INTO "metrics" VALUES(149,'20261030T135346Z-h-005-exploration-btc-usdt','trades__conservative',31.0,NULL);
INSERT INTO "metrics" VALUES(150,'20261030T135346Z-h-005-exploration-btc-usdt','net_profit_quote__conservative',4.923369603000001006e+02,NULL);
INSERT INTO "metrics" VALUES(151,'20261030T135346Z-h-005-exploration-btc-usdt','net_profit_excl_best_trade__conservative',1.196528519455882815e+02,NULL);
INSERT INTO "metrics" VALUES(152,'20261030T135346Z-h-005-exploration-btc-usdt','max_drawdown_pct__conservative',5.119152003738005873e+01,NULL);
INSERT INTO "metrics" VALUES(153,'20261030T135346Z-h-005-exploration-btc-usdt','trades__stress',31.0,NULL);
INSERT INTO "metrics" VALUES(154,'20261030T135346Z-h-005-exploration-btc-usdt','net_profit_quote__stress',4.158743608999999424e+02,NULL);
INSERT INTO "metrics" VALUES(155,'20261030T135346Z-h-005-exploration-btc-usdt','net_profit_excl_best_trade__stress',9.191384037101315129e+01,NULL);
INSERT INTO "metrics" VALUES(156,'20261030T135346Z-h-005-exploration-btc-usdt','max_drawdown_pct__stress',5.427126160501703822e+01,NULL);
INSERT INTO "metrics" VALUES(157,'20261030T135346Z-h-005-exploration-btc-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(158,'20261030T135346Z-h-005-exploration-btc-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(159,'20261030T135346Z-h-005-exploration-btc-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(160,'20261030T135346Z-h-005-exploration-btc-usdt','benchmark_buy_and_hold_return_pct',1.252655361200140305e+03,NULL);
INSERT INTO "metrics" VALUES(161,'20261030T135346Z-h-005-exploration-eth-usdt','trades__optimistic',36.0,NULL);
INSERT INTO "metrics" VALUES(162,'20261030T135346Z-h-005-exploration-eth-usdt','net_profit_quote__optimistic',540.66668951,NULL);
INSERT INTO "metrics" VALUES(163,'20261030T135346Z-h-005-exploration-eth-usdt','net_profit_excl_best_trade__optimistic',5.928944742234654086e+01,NULL);
INSERT INTO "metrics" VALUES(164,'20261030T135346Z-h-005-exploration-eth-usdt','max_drawdown_pct__optimistic',4.954966563201856644e+01,NULL);
INSERT INTO "metrics" VALUES(165,'20261030T135346Z-h-005-exploration-eth-usdt','trades__base',36.0,NULL);
INSERT INTO "metrics" VALUES(166,'20261030T135346Z-h-005-exploration-eth-usdt','net_profit_quote__base',5.072387649800000418e+02,NULL);
INSERT INTO "metrics" VALUES(167,'20261030T135346Z-h-005-exploration-eth-usdt','net_profit_excl_best_trade__base',5.114246510197557427e+01,NULL);
INSERT INTO "metrics" VALUES(168,'20261030T135346Z-h-005-exploration-eth-usdt','max_drawdown_pct__base',5.062555815583924356e+01,NULL);
INSERT INTO "metrics" VALUES(169,'20261030T135346Z-h-005-exploration-eth-usdt','trades__conservative',36.0,NULL);
INSERT INTO "metrics" VALUES(170,'20261030T135346Z-h-005-exploration-eth-usdt','net_profit_quote__conservative',4.754793374499998322e+02,NULL);
INSERT INTO "metrics" VALUES(171,'20261030T135346Z-h-005-exploration-eth-usdt','net_profit_excl_best_trade__conservative',4.341214674326818113e+01,NULL);
INSERT INTO "metrics" VALUES(172,'20261030T135346Z-h-005-exploration-eth-usdt','max_drawdown_pct__conservative',5.168120148592083752e+01,NULL);
INSERT INTO "metrics" VALUES(173,'20261030T135346Z-h-005-exploration-eth-usdt','trades__stress',36.0,NULL);
INSERT INTO "metrics" VALUES(174,'20261030T135346Z-h-005-exploration-eth-usdt','net_profit_quote__stress',3.898545227799998542e+02,NULL);
INSERT INTO "metrics" VALUES(175,'20261030T135346Z-h-005-exploration-eth-usdt','net_profit_excl_best_trade__stress',2.251341006826780244e+01,NULL);
INSERT INTO "metrics" VALUES(176,'20261030T135346Z-h-005-exploration-eth-usdt','max_drawdown_pct__stress',5.472438571486682691e+01,NULL);
INSERT INTO "metrics" VALUES(177,'20261030T135346Z-h-005-exploration-eth-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(178,'20261030T135346Z-h-005-exploration-eth-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(179,'20261030T135346Z-h-005-exploration-eth-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(180,'20261030T135346Z-h-005-exploration-eth-usdt','benchmark_buy_and_hold_return_pct',9.29581247306123827e+02,NULL);
INSERT INTO "metrics" VALUES(181,'20261030T135346Z-h-005-exploration-bnb-usdt','trades__optimistic',36.0,NULL);
INSERT INTO "metrics" VALUES(182,'20261030T135346Z-h-005-exploration-bnb-usdt','net_profit_quote__optimistic',9.33085805320000077e+02,NULL);
INSERT INTO "metrics" VALUES(183,'20261030T135346Z-h-005-exploration-bnb-usdt','net_profit_excl_best_trade__optimistic',33.9259455443613,NULL);
INSERT INTO "metrics" VALUES(184,'20261030T135346Z-h-005-exploration-bnb-usdt','max_drawdown_pct__optimistic',4.204007997269532381e+01,NULL);
INSERT INTO "metrics" VALUES(185,'20261030T135346Z-h-005-exploration-bnb-usdt','trades__base',36.0,NULL);
INSERT INTO "metrics" VALUES(186,'20261030T135346Z-h-005-exploration-bnb-usdt','net_profit_quote__base',8.791521404599999415e+02,NULL);
INSERT INTO "metrics" VALUES(187,'20261030T135346Z-h-005-exploration-bnb-usdt','net_profit_excl_best_trade__base',2.707619920303369554e+01,NULL);
INSERT INTO "metrics" VALUES(188,'20261030T135346Z-h-005-exploration-bnb-usdt','max_drawdown_pct__base',4.292453129892464147e+01,NULL);
INSERT INTO "metrics" VALUES(189,'20261030T135346Z-h-005-exploration-bnb-usdt','trades__conservative',36.0,NULL);
INSERT INTO "metrics" VALUES(190,'20261030T135346Z-h-005-exploration-bnb-usdt','net_profit_quote__conservative',827.88634406,NULL);
INSERT INTO "metrics" VALUES(191,'20261030T135346Z-h-005-exploration-bnb-usdt','net_profit_excl_best_trade__conservative',2.057677184351784661e+01,NULL);
INSERT INTO "metrics" VALUES(192,'20261030T135346Z-h-005-exploration-bnb-usdt','max_drawdown_pct__conservative',4.380257578270251173e+01,NULL);
INSERT INTO "metrics" VALUES(193,'20261030T135346Z-h-005-exploration-bnb-usdt','trades__stress',36.0,NULL);
INSERT INTO "metrics" VALUES(194,'20261030T135346Z-h-005-exploration-bnb-usdt','net_profit_quote__stress',6.894879682299998648e+02,NULL);
INSERT INTO "metrics" VALUES(195,'20261030T135346Z-h-005-exploration-bnb-usdt','net_profit_excl_best_trade__stress',3.005720405876019186e+00,NULL);
INSERT INTO "metrics" VALUES(196,'20261030T135346Z-h-005-exploration-bnb-usdt','max_drawdown_pct__stress',4.635792206861491849e+01,NULL);
INSERT INTO "metrics" VALUES(197,'20261030T135346Z-h-005-exploration-bnb-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(198,'20261030T135346Z-h-005-exploration-bnb-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(199,'20261030T135346Z-h-005-exploration-bnb-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(200,'20261030T135346Z-h-005-exploration-bnb-usdt','benchmark_buy_and_hold_return_pct',3.302352941176470631e+04,NULL);
INSERT INTO "metrics" VALUES(201,'20261030T182309Z-h-003-exploration-btc-usdt','trades__optimistic',71.0,NULL);
INSERT INTO "metrics" VALUES(202,'20261030T182309Z-h-003-exploration-btc-usdt','net_profit_quote__optimistic',-5.210441740000005594e+00,NULL);
INSERT INTO "metrics" VALUES(203,'20261030T182309Z-h-003-exploration-btc-usdt','net_profit_excl_best_trade__optimistic',-1.35845864251857904e+01,NULL);
INSERT INTO "metrics" VALUES(204,'20261030T182309Z-h-003-exploration-btc-usdt','max_drawdown_pct__optimistic',2.785762357950105539e+01,NULL);
INSERT INTO "metrics" VALUES(205,'20261030T182309Z-h-003-exploration-btc-usdt','trades__base',71.0,NULL);
INSERT INTO "metrics" VALUES(206,'20261030T182309Z-h-003-exploration-btc-usdt','net_profit_quote__base',-1.480131341000000945e+01,NULL);
INSERT INTO "metrics" VALUES(207,'20261030T182309Z-h-003-exploration-btc-usdt','net_profit_excl_best_trade__base',-2.219809982790633284e+01,NULL);
INSERT INTO "metrics" VALUES(208,'20261030T182309Z-h-003-exploration-btc-usdt','max_drawdown_pct__base',3.193539143865833907e+01,NULL);
INSERT INTO "metrics" VALUES(209,'20261030T182309Z-h-003-exploration-btc-usdt','trades__conservative',71.0,NULL);
INSERT INTO "metrics" VALUES(210,'20261030T182309Z-h-003-exploration-btc-usdt','net_profit_quote__conservative',-2.347101375999999818e+01,NULL);
INSERT INTO "metrics" VALUES(211,'20261030T182309Z-h-003-exploration-btc-usdt','net_profit_excl_best_trade__conservative',-2.995307497511532802e+01,NULL);
INSERT INTO "metrics" VALUES(212,'20261030T182309Z-h-003-exploration-btc-usdt','max_drawdown_pct__conservative',3.735120467576893333e+01,NULL);
INSERT INTO "metrics" VALUES(213,'20261030T182309Z-h-003-exploration-btc-usdt','trades__stress',71.0,NULL);
INSERT INTO "metrics" VALUES(214,'20261030T182309Z-h-003-exploration-btc-usdt','net_profit_quote__stress',-4.443828624000000361e+01,NULL);
INSERT INTO "metrics" VALUES(215,'20261030T182309Z-h-003-exploration-btc-usdt','net_profit_excl_best_trade__stress',-4.888075185043122417e+01,NULL);
INSERT INTO "metrics" VALUES(216,'20261030T182309Z-h-003-exploration-btc-usdt','max_drawdown_pct__stress',5.287409279017728637e+01,NULL);
INSERT INTO "metrics" VALUES(217,'20261030T182309Z-h-003-exploration-btc-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(218,'20261030T182309Z-h-003-exploration-btc-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(219,'20261030T182309Z-h-003-exploration-btc-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(220,'20261030T182309Z-h-003-exploration-btc-usdt','benchmark_buy_and_hold_return_pct',1.252655361200140305e+03,NULL);
INSERT INTO "metrics" VALUES(221,'20261030T182309Z-h-003-exploration-eth-usdt','trades__optimistic',61.0,NULL);
INSERT INTO "metrics" VALUES(222,'20261030T182309Z-h-003-exploration-eth-usdt','net_profit_quote__optimistic',-12.14207558,NULL);
INSERT INTO "metrics" VALUES(223,'20261030T182309Z-h-003-exploration-eth-usdt','net_profit_excl_best_trade__optimistic',-1.569818238551498268e+01,NULL);
INSERT INTO "metrics" VALUES(224,'20261030T182309Z-h-003-exploration-eth-usdt','max_drawdown_pct__optimistic',40.1902374754145,NULL);
INSERT INTO "metrics" VALUES(225,'20261030T182309Z-h-003-exploration-eth-usdt','trades__base',61.0,NULL);
INSERT INTO "metrics" VALUES(226,'20261030T182309Z-h-003-exploration-eth-usdt','net_profit_quote__base',-1.988273167000000186e+01,NULL);
INSERT INTO "metrics" VALUES(227,'20261030T182309Z-h-003-exploration-eth-usdt','net_profit_excl_best_trade__base',-2.295395339118392997e+01,NULL);
INSERT INTO "metrics" VALUES(228,'20261030T182309Z-h-003-exploration-eth-usdt','max_drawdown_pct__base',4.269374180439965726e+01,NULL);
INSERT INTO "metrics" VALUES(229,'20261030T182309Z-h-003-exploration-eth-usdt','trades__conservative',61.0,NULL);
INSERT INTO "metrics" VALUES(230,'20261030T182309Z-h-003-exploration-eth-usdt','net_profit_quote__conservative',-2.689865133000000342e+01,NULL);
INSERT INTO "metrics" VALUES(231,'20261030T182309Z-h-003-exploration-eth-usdt','net_profit_excl_best_trade__conservative',-2.958524422229086781e+01,NULL);
INSERT INTO "metrics" VALUES(232,'20261030T182309Z-h-003-exploration-eth-usdt','max_drawdown_pct__conservative',4.507968562205861219e+01,NULL);
INSERT INTO "metrics" VALUES(233,'20261030T182309Z-h-003-exploration-eth-usdt','trades__stress',61.0,NULL);
INSERT INTO "metrics" VALUES(234,'20261030T182309Z-h-003-exploration-eth-usdt','net_profit_quote__stress',-44.51454445,NULL);
INSERT INTO "metrics" VALUES(235,'20261030T182309Z-h-003-exploration-eth-usdt','net_profit_excl_best_trade__stress',-46.2470162023799,NULL);
INSERT INTO "metrics" VALUES(236,'20261030T182309Z-h-003-exploration-eth-usdt','max_drawdown_pct__stress',5.16497373129700037e+01,NULL);
INSERT INTO "metrics" VALUES(237,'20261030T182309Z-h-003-exploration-eth-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(238,'20261030T182309Z-h-003-exploration-eth-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(239,'20261030T182309Z-h-003-exploration-eth-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(240,'20261030T182309Z-h-003-exploration-eth-usdt','benchmark_buy_and_hold_return_pct',9.29581247306123827e+02,NULL);
INSERT INTO "metrics" VALUES(241,'20261030T182309Z-h-003-exploration-bnb-usdt','trades__optimistic',50.0,NULL);
INSERT INTO "metrics" VALUES(242,'20261030T182309Z-h-003-exploration-bnb-usdt','net_profit_quote__optimistic',6.028497304999998363e+01,NULL);
INSERT INTO "metrics" VALUES(243,'20261030T182309Z-h-003-exploration-bnb-usdt','net_profit_excl_best_trade__optimistic',3.004063308138674415e+01,NULL);
INSERT INTO "metrics" VALUES(244,'20261030T182309Z-h-003-exploration-bnb-usdt','max_drawdown_pct__optimistic',1.518550172416062161e+01,NULL);
INSERT INTO "metrics" VALUES(245,'20261030T182309Z-h-003-exploration-bnb-usdt','trades__base',50.0,NULL);
INSERT INTO "metrics" VALUES(246,'20261030T182309Z-h-003-exploration-bnb-usdt','net_profit_quote__base',48.71615493,NULL);
INSERT INTO "metrics" VALUES(247,'20261030T182309Z-h-003-exploration-bnb-usdt','net_profit_excl_best_trade__base',2.082543542575179175e+01,NULL);
INSERT INTO "metrics" VALUES(248,'20261030T182309Z-h-003-exploration-bnb-usdt','max_drawdown_pct__base',1.770854586147733656e+01,NULL);
INSERT INTO "metrics" VALUES(249,'20261030T182309Z-h-003-exploration-bnb-usdt','trades__conservative',50.0,NULL);
INSERT INTO "metrics" VALUES(250,'20261030T182309Z-h-003-exploration-bnb-usdt','net_profit_quote__conservative',3.799377965999999419e+01,NULL);
INSERT INTO "metrics" VALUES(251,'20261030T182309Z-h-003-exploration-bnb-usdt','net_profit_excl_best_trade__conservative',1.226324172700904568e+01,NULL);
INSERT INTO "metrics" VALUES(252,'20261030T182309Z-h-003-exploration-bnb-usdt','max_drawdown_pct__conservative',2.09900622982437639e+01,NULL);
INSERT INTO "metrics" VALUES(253,'20261030T182309Z-h-003-exploration-bnb-usdt','trades__stress',50.0,NULL);
INSERT INTO "metrics" VALUES(254,'20261030T182309Z-h-003-exploration-bnb-usdt','net_profit_quote__stress',1.017781702000000798e+01,NULL);
INSERT INTO "metrics" VALUES(255,'20261030T182309Z-h-003-exploration-bnb-usdt','net_profit_excl_best_trade__stress',-9.95194291446787816e+00,NULL);
INSERT INTO "metrics" VALUES(256,'20261030T182309Z-h-003-exploration-bnb-usdt','max_drawdown_pct__stress',30.0873131784284,NULL);
INSERT INTO "metrics" VALUES(257,'20261030T182309Z-h-003-exploration-bnb-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(258,'20261030T182309Z-h-003-exploration-bnb-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(259,'20261030T182309Z-h-003-exploration-bnb-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(260,'20261030T182309Z-h-003-exploration-bnb-usdt','benchmark_buy_and_hold_return_pct',3.302352941176470631e+04,NULL);
INSERT INTO "metrics" VALUES(261,'20261030T184141Z-h-007-exploration-btc-usdt','trades__optimistic',23.0,NULL);
INSERT INTO "metrics" VALUES(262,'20261030T184141Z-h-007-exploration-btc-usdt','net_profit_quote__optimistic',586.1124101,NULL);
INSERT INTO "metrics" VALUES(263,'20261030T184141Z-h-007-exploration-btc-usdt','net_profit_excl_best_trade__optimistic',1.529564296114090496e+02,NULL);
INSERT INTO "metrics" VALUES(264,'20261030T184141Z-h-007-exploration-btc-usdt','max_drawdown_pct__optimistic',3.568258386634104796e+01,NULL);
INSERT INTO "metrics" VALUES(265,'20261030T184141Z-h-007-exploration-btc-usdt','trades__base',23.0,NULL);
INSERT INTO "metrics" VALUES(266,'20261030T184141Z-h-007-exploration-btc-usdt','net_profit_quote__base',563.30124416,NULL);
INSERT INTO "metrics" VALUES(267,'20261030T184141Z-h-007-exploration-btc-usdt','net_profit_excl_best_trade__base',1.44745083870432552e+02,NULL);
INSERT INTO "metrics" VALUES(268,'20261030T184141Z-h-007-exploration-btc-usdt','max_drawdown_pct__base',3.674974786715348785e+01,NULL);
INSERT INTO "metrics" VALUES(269,'20261030T184141Z-h-007-exploration-btc-usdt','trades__conservative',23.0,NULL);
INSERT INTO "metrics" VALUES(270,'20261030T184141Z-h-007-exploration-btc-usdt','net_profit_quote__conservative',541.557591,NULL);
INSERT INTO "metrics" VALUES(271,'20261030T184141Z-h-007-exploration-btc-usdt','net_profit_excl_best_trade__conservative',1.368002703167163361e+02,NULL);
INSERT INTO "metrics" VALUES(272,'20261030T184141Z-h-007-exploration-btc-usdt','max_drawdown_pct__conservative',3.780885719425585733e+01,NULL);
INSERT INTO "metrics" VALUES(273,'20261030T184141Z-h-007-exploration-btc-usdt','trades__stress',23.0,NULL);
INSERT INTO "metrics" VALUES(274,'20261030T184141Z-h-007-exploration-btc-usdt','net_profit_quote__stress',4.796938943999999196e+02,NULL);
INSERT INTO "metrics" VALUES(275,'20261030T184141Z-h-007-exploration-btc-usdt','net_profit_excl_best_trade__stress',1.144798300907228565e+02,NULL);
INSERT INTO "metrics" VALUES(276,'20261030T184141Z-h-007-exploration-btc-usdt','max_drawdown_pct__stress',4.089608279001540581e+01,NULL);
INSERT INTO "metrics" VALUES(277,'20261030T184141Z-h-007-exploration-btc-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(278,'20261030T184141Z-h-007-exploration-btc-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(279,'20261030T184141Z-h-007-exploration-btc-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(280,'20261030T184141Z-h-007-exploration-btc-usdt','benchmark_buy_and_hold_return_pct',1.252655361200140305e+03,NULL);
INSERT INTO "metrics" VALUES(281,'20261030T184141Z-h-007-exploration-eth-usdt','trades__optimistic',27.0,NULL);
INSERT INTO "metrics" VALUES(282,'20261030T184141Z-h-007-exploration-eth-usdt','net_profit_quote__optimistic',347.0654593,NULL);
INSERT INTO "metrics" VALUES(283,'20261030T184141Z-h-007-exploration-eth-usdt','net_profit_excl_best_trade__optimistic',4.91029800670132488e+01,NULL);
INSERT INTO "metrics" VALUES(284,'20261030T184141Z-h-007-exploration-eth-usdt','max_drawdown_pct__optimistic',4.368865568996132254e+01,NULL);
INSERT INTO "metrics" VALUES(285,'20261030T184141Z-h-007-exploration-eth-usdt','trades__base',27.0,NULL);
INSERT INTO "metrics" VALUES(286,'20261030T184141Z-h-007-exploration-eth-usdt','net_profit_quote__base',3.295136389999999551e+02,NULL);
INSERT INTO "metrics" VALUES(287,'20261030T184141Z-h-007-exploration-eth-usdt','net_profit_excl_best_trade__base',4.339988601846997084e+01,NULL);
INSERT INTO "metrics" VALUES(288,'20261030T184141Z-h-007-exploration-eth-usdt','max_drawdown_pct__base',4.471646510161662747e+01,NULL);
INSERT INTO "metrics" VALUES(289,'20261030T184141Z-h-007-exploration-eth-usdt','trades__conservative',27.0,NULL);
INSERT INTO "metrics" VALUES(290,'20261030T184141Z-h-007-exploration-eth-usdt','net_profit_quote__conservative',312.68657704,NULL);
INSERT INTO "metrics" VALUES(291,'20261030T184141Z-h-007-exploration-eth-usdt','net_profit_excl_best_trade__conservative',3.791491751706709578e+01,NULL);
INSERT INTO "metrics" VALUES(292,'20261030T184141Z-h-007-exploration-eth-usdt','max_drawdown_pct__conservative',4.573399959031292638e+01,NULL);
INSERT INTO "metrics" VALUES(293,'20261030T184141Z-h-007-exploration-eth-usdt','trades__stress',27.0,NULL);
INSERT INTO "metrics" VALUES(294,'20261030T184141Z-h-007-exploration-eth-usdt','net_profit_quote__stress',2.659129109900000572e+02,NULL);
INSERT INTO "metrics" VALUES(295,'20261030T184141Z-h-007-exploration-eth-usdt','net_profit_excl_best_trade__stress',2.268687385000767165e+01,NULL);
INSERT INTO "metrics" VALUES(296,'20261030T184141Z-h-007-exploration-eth-usdt','max_drawdown_pct__stress',4.866855268524086143e+01,NULL);
INSERT INTO "metrics" VALUES(297,'20261030T184141Z-h-007-exploration-eth-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(298,'20261030T184141Z-h-007-exploration-eth-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(299,'20261030T184141Z-h-007-exploration-eth-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(300,'20261030T184141Z-h-007-exploration-eth-usdt','benchmark_buy_and_hold_return_pct',9.29581247306123827e+02,NULL);
INSERT INTO "metrics" VALUES(301,'20261030T184141Z-h-007-exploration-bnb-usdt','trades__optimistic',36.0,NULL);
INSERT INTO "metrics" VALUES(302,'20261030T184141Z-h-007-exploration-bnb-usdt','net_profit_quote__optimistic',1.778909079699999723e+02,NULL);
INSERT INTO "metrics" VALUES(303,'20261030T184141Z-h-007-exploration-bnb-usdt','net_profit_excl_best_trade__optimistic',-4.2914278722476773e+01,NULL);
INSERT INTO "metrics" VALUES(304,'20261030T184141Z-h-007-exploration-bnb-usdt','max_drawdown_pct__optimistic',2.387189846060299204e+01,NULL);
INSERT INTO "metrics" VALUES(305,'20261030T184141Z-h-007-exploration-bnb-usdt','trades__base',36.0,NULL);
INSERT INTO "metrics" VALUES(306,'20261030T184141Z-h-007-exploration-bnb-usdt','net_profit_quote__base',1.633436773099999754e+02,NULL);
INSERT INTO "metrics" VALUES(307,'20261030T184141Z-h-007-exploration-bnb-usdt','net_profit_excl_best_trade__base',-4.58339722059928647e+01,NULL);
INSERT INTO "metrics" VALUES(308,'20261030T184141Z-h-007-exploration-bnb-usdt','max_drawdown_pct__base',2.512737850130607953e+01,NULL);
INSERT INTO "metrics" VALUES(309,'20261030T184141Z-h-007-exploration-bnb-usdt','trades__conservative',36.0,NULL);
INSERT INTO "metrics" VALUES(310,'20261030T184141Z-h-007-exploration-bnb-usdt','net_profit_quote__conservative',1.495320868499999846e+02,NULL);
INSERT INTO "metrics" VALUES(311,'20261030T184141Z-h-007-exploration-bnb-usdt','net_profit_excl_best_trade__conservative',-4.860434277236942791e+01,NULL);
INSERT INTO "metrics" VALUES(312,'20261030T184141Z-h-007-exploration-bnb-usdt','max_drawdown_pct__conservative',2.641914790569768101e+01,NULL);
INSERT INTO "metrics" VALUES(313,'20261030T184141Z-h-007-exploration-bnb-usdt','trades__stress',36.0,NULL);
INSERT INTO "metrics" VALUES(314,'20261030T184141Z-h-007-exploration-bnb-usdt','net_profit_quote__stress',1.119666535300000163e+02,NULL);
INSERT INTO "metrics" VALUES(315,'20261030T184141Z-h-007-exploration-bnb-usdt','net_profit_excl_best_trade__stress',-5.609397550533672216e+01,NULL);
INSERT INTO "metrics" VALUES(316,'20261030T184141Z-h-007-exploration-bnb-usdt','max_drawdown_pct__stress',3.097501629693397617e+01,NULL);
INSERT INTO "metrics" VALUES(317,'20261030T184141Z-h-007-exploration-bnb-usdt','lookahead_has_bias',NULL,'true');
INSERT INTO "metrics" VALUES(318,'20261030T184141Z-h-007-exploration-bnb-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(319,'20261030T184141Z-h-007-exploration-bnb-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(320,'20261030T184141Z-h-007-exploration-bnb-usdt','benchmark_buy_and_hold_return_pct',3.302352941176470631e+04,NULL);
INSERT INTO "metrics" VALUES(326,'20261102T224114Z-h-001-exploration-btc-usdt','trades__optimistic',383.0,NULL);
INSERT INTO "metrics" VALUES(327,'20261102T224114Z-h-001-exploration-btc-usdt','net_profit_quote__optimistic',4.088057333500001391e+02,NULL);
INSERT INTO "metrics" VALUES(328,'20261102T224114Z-h-001-exploration-btc-usdt','net_profit_excl_best_trade__optimistic',3.034883639386341087e+02,NULL);
INSERT INTO "metrics" VALUES(329,'20261102T224114Z-h-001-exploration-btc-usdt','max_drawdown_pct__optimistic',4.118676582820205568e+01,NULL);
INSERT INTO "metrics" VALUES(330,'20261102T224114Z-h-001-exploration-btc-usdt','trades__base',383.0,NULL);
INSERT INTO "metrics" VALUES(331,'20261102T224114Z-h-001-exploration-btc-usdt','net_profit_quote__base',1.864646158500000296e+02,NULL);
INSERT INTO "metrics" VALUES(332,'20261102T224114Z-h-001-exploration-btc-usdt','net_profit_excl_best_trade__base',1.274991583808297548e+02,NULL);
INSERT INTO "metrics" VALUES(333,'20261102T224114Z-h-001-exploration-btc-usdt','max_drawdown_pct__base',5.040990304969395198e+01,NULL);
INSERT INTO "metrics" VALUES(334,'20261102T224114Z-h-001-exploration-btc-usdt','trades__conservative',383.0,NULL);
INSERT INTO "metrics" VALUES(335,'20261102T224114Z-h-001-exploration-btc-usdt','net_profit_quote__conservative',6.113777701999995884e+01,NULL);
INSERT INTO "metrics" VALUES(336,'20261102T224114Z-h-001-exploration-btc-usdt','net_profit_excl_best_trade__conservative',2.827083469006831251e+01,NULL);
INSERT INTO "metrics" VALUES(337,'20261102T224114Z-h-001-exploration-btc-usdt','max_drawdown_pct__conservative',6.183959632109355909e+01,NULL);
INSERT INTO "metrics" VALUES(338,'20261102T224114Z-h-001-exploration-btc-usdt','trades__stress',383.0,NULL);
INSERT INTO "metrics" VALUES(339,'20261102T224114Z-h-001-exploration-btc-usdt','net_profit_quote__stress',-71.32761291,NULL);
INSERT INTO "metrics" VALUES(340,'20261102T224114Z-h-001-exploration-btc-usdt','net_profit_excl_best_trade__stress',-7.70085913479499311e+01,NULL);
INSERT INTO "metrics" VALUES(341,'20261102T224114Z-h-001-exploration-btc-usdt','max_drawdown_pct__stress',8.774418653756916342e+01,NULL);
INSERT INTO "metrics" VALUES(342,'20261102T224114Z-h-001-exploration-btc-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(343,'20261102T224114Z-h-001-exploration-btc-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(344,'20261102T224114Z-h-001-exploration-btc-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(345,'20261102T224114Z-h-001-exploration-btc-usdt','benchmark_buy_and_hold_return_pct',1.252655361200140305e+03,NULL);
INSERT INTO "metrics" VALUES(346,'20261102T224114Z-h-001-exploration-eth-usdt','trades__optimistic',388.0,NULL);
INSERT INTO "metrics" VALUES(347,'20261102T224114Z-h-001-exploration-eth-usdt','net_profit_quote__optimistic',1.43772461641000018e+03,NULL);
INSERT INTO "metrics" VALUES(348,'20261102T224114Z-h-001-exploration-eth-usdt','net_profit_excl_best_trade__optimistic',8.893830841506542129e+02,NULL);
INSERT INTO "metrics" VALUES(349,'20261102T224114Z-h-001-exploration-eth-usdt','max_drawdown_pct__optimistic',3.817569701275583328e+01,NULL);
INSERT INTO "metrics" VALUES(350,'20261102T224114Z-h-001-exploration-eth-usdt','trades__base',388.0,NULL);
INSERT INTO "metrics" VALUES(351,'20261102T224114Z-h-001-exploration-eth-usdt','net_profit_quote__base',7.59639554169999883e+02,NULL);
INSERT INTO "metrics" VALUES(352,'20261102T224114Z-h-001-exploration-eth-usdt','net_profit_excl_best_trade__base',4.536764422992025629e+02,NULL);
INSERT INTO "metrics" VALUES(353,'20261102T224114Z-h-001-exploration-eth-usdt','max_drawdown_pct__base',4.650057884100519345e+01,NULL);
INSERT INTO "metrics" VALUES(354,'20261102T224114Z-h-001-exploration-eth-usdt','trades__conservative',388.0,NULL);
INSERT INTO "metrics" VALUES(355,'20261102T224114Z-h-001-exploration-eth-usdt','net_profit_quote__conservative',3.801191641300000584e+02,NULL);
INSERT INTO "metrics" VALUES(356,'20261102T224114Z-h-001-exploration-eth-usdt','net_profit_excl_best_trade__conservative',2.098467524844051581e+02,NULL);
INSERT INTO "metrics" VALUES(357,'20261102T224114Z-h-001-exploration-eth-usdt','max_drawdown_pct__conservative',5.37085745954318483e+01,NULL);
INSERT INTO "metrics" VALUES(358,'20261102T224114Z-h-001-exploration-eth-usdt','trades__stress',388.0,NULL);
INSERT INTO "metrics" VALUES(359,'20261102T224114Z-h-001-exploration-eth-usdt','net_profit_quote__stress',-1.67196538499999292e+01,NULL);
INSERT INTO "metrics" VALUES(360,'20261102T224114Z-h-001-exploration-eth-usdt','net_profit_excl_best_trade__stress',-4.569837193268411824e+01,NULL);
INSERT INTO "metrics" VALUES(361,'20261102T224114Z-h-001-exploration-eth-usdt','max_drawdown_pct__stress',75.4349517971588,NULL);
INSERT INTO "metrics" VALUES(362,'20261102T224114Z-h-001-exploration-eth-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(363,'20261102T224114Z-h-001-exploration-eth-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(364,'20261102T224114Z-h-001-exploration-eth-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(365,'20261102T224114Z-h-001-exploration-eth-usdt','benchmark_buy_and_hold_return_pct',9.29581247306123827e+02,NULL);
INSERT INTO "metrics" VALUES(366,'20261102T224114Z-h-001-exploration-bnb-usdt','trades__optimistic',366.0,NULL);
INSERT INTO "metrics" VALUES(367,'20261102T224114Z-h-001-exploration-bnb-usdt','net_profit_quote__optimistic',4449.51279989,NULL);
INSERT INTO "metrics" VALUES(368,'20261102T224114Z-h-001-exploration-bnb-usdt','net_profit_excl_best_trade__optimistic',1.965102370253855497e+03,NULL);
INSERT INTO "metrics" VALUES(369,'20261102T224114Z-h-001-exploration-bnb-usdt','max_drawdown_pct__optimistic',3.628804943707682185e+01,NULL);
INSERT INTO "metrics" VALUES(370,'20261102T224114Z-h-001-exploration-bnb-usdt','trades__base',366.0,NULL);
INSERT INTO "metrics" VALUES(371,'20261102T224114Z-h-001-exploration-bnb-usdt','net_profit_quote__base',2.529817460949999713e+03,NULL);
INSERT INTO "metrics" VALUES(372,'20261102T224114Z-h-001-exploration-bnb-usdt','net_profit_excl_best_trade__base',1.094441531140519828e+03,NULL);
INSERT INTO "metrics" VALUES(373,'20261102T224114Z-h-001-exploration-bnb-usdt','max_drawdown_pct__base',4.395698979510911641e+01,NULL);
INSERT INTO "metrics" VALUES(374,'20261102T224114Z-h-001-exploration-bnb-usdt','trades__conservative',366.0,NULL);
INSERT INTO "metrics" VALUES(375,'20261102T224114Z-h-001-exploration-bnb-usdt','net_profit_quote__conservative',1.418680684440000505e+03,NULL);
INSERT INTO "metrics" VALUES(376,'20261102T224114Z-h-001-exploration-bnb-usdt','net_profit_excl_best_trade__conservative',5.908560765801784101e+02,NULL);
INSERT INTO "metrics" VALUES(377,'20261102T224114Z-h-001-exploration-bnb-usdt','max_drawdown_pct__conservative',5.20207774887634784e+01,NULL);
INSERT INTO "metrics" VALUES(378,'20261102T224114Z-h-001-exploration-bnb-usdt','trades__stress',366.0,NULL);
INSERT INTO "metrics" VALUES(379,'20261102T224114Z-h-001-exploration-bnb-usdt','net_profit_quote__stress',1.912160881099999585e+02,NULL);
INSERT INTO "metrics" VALUES(380,'20261102T224114Z-h-001-exploration-bnb-usdt','net_profit_excl_best_trade__stress',3.367470078985687109e+01,NULL);
INSERT INTO "metrics" VALUES(381,'20261102T224114Z-h-001-exploration-bnb-usdt','max_drawdown_pct__stress',7.417935077798095734e+01,NULL);
INSERT INTO "metrics" VALUES(382,'20261102T224114Z-h-001-exploration-bnb-usdt','lookahead_has_bias',NULL,'false');
INSERT INTO "metrics" VALUES(383,'20261102T224114Z-h-001-exploration-bnb-usdt','recursive_is_stable',NULL,'true');
INSERT INTO "metrics" VALUES(384,'20261102T224114Z-h-001-exploration-bnb-usdt','benchmark_cash_return_pct',0.0,NULL);
INSERT INTO "metrics" VALUES(385,'20261102T224114Z-h-001-exploration-bnb-usdt','benchmark_buy_and_hold_return_pct',3.302352941176470631e+04,NULL);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('metrics',385);
INSERT INTO "sqlite_sequence" VALUES('decisions',24);
INSERT INTO "sqlite_sequence" VALUES('agent_runs',17);
COMMIT;

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
CREATE TABLE hypotheses (
    id TEXT PRIMARY KEY,                 -- e.g. "H-004"
    family TEXT NOT NULL,
    ex_ante_rule TEXT NOT NULL,
    proposed_at_utc TEXT NOT NULL,
    data_visible_at_proposal TEXT NOT NULL,  -- what data window was visible when the rule was fixed
    status TEXT NOT NULL,                -- e.g. "proposed", "frozen reference", "candidate", "rejected"
    notes TEXT
);
INSERT INTO "hypotheses" VALUES('H-001','SmaTrendBaseline','SMA20/SMA50 cross, close > SMA200, stop -10%','2026-10-20T00:00:00Z','BTC/USDT 1h through 2026-10-20','frozen reference','Original result (1 trade) was a harness artifact: fixed stake equal to wallet. Not yet tested under the corrected harness.');
INSERT INTO "hypotheses" VALUES('H-002','DonchianBreakoutBaseline','Close > prior 20-candle high; exit below prior 10-candle low; stop -10%','2026-10-20T00:00:00Z','BTC/USDT 1h through 2026-10-20','rejected at exploration','Corrected harness, exploration on BTC/ETH/BNB: positive only at the optimistic cost, drawdown 60-98%. Do not select by return alone.');
INSERT INTO "hypotheses" VALUES('H-003','BollingerMeanReversionBaseline','Lower 20-band, RSI14 < 30, close > SMA200; exit at middle band; stop -10%','2026-10-20T00:00:00Z','BTC/USDT 1h through 2026-10-20','candidate','Not yet tested under the corrected harness. Trend-failure risk.');
INSERT INTO "hypotheses" VALUES('H-004','SlowTimeSeriesMomentum','Use closed 1h candles only; signals evaluated at bar close, order executed at next bar open. Long only, one position, whole balance. ENTRY: close > highest high of the prior 1440 bars (60 days, excluding current bar) AND close > SMA(4800 bars, 200 days) of close AND no open position. EXIT: close < lowest low of the prior 720 bars (30 days, excluding current bar), OR close below entry price by 15% (hard stop, checked on closed bars). After any exit, no re-entry until at least 168 bars (7 days) have passed. No other filters, no pyramiding, no take-profit.','2026-10-30T13:28:34.345485+00:00','BTC, ETH, BNB 1h through 2026-10-30; no result data viewed beyond the context file''s exploration summaries','invalid: implementation deviated from rule','Exploration ran on an implementation that used min_periods=1440 on the 4800-candle SMA (to satisfy a too-short smoke window) and without the 168-candle cooldown (backtest ran without --enable-protections). Both harness flaws are fixed. The rule itself is untested. Recorded results: research/experiments/H-004-exploration/ and the 20261030T133614Z-h-004-* manifests.');
INSERT INTO "hypotheses" VALUES('H-005','VolatilitySqueezeBreakout','Closed 1h candles only; signals evaluated at bar close, order executed at next bar open. Long only, one position, whole balance. Definitions (all use completed bars): R(t) = (highest high of the 168 bars ending at t - lowest low of the 168 bars ending at t) / close(t). Squeeze(t) is true if R(t) is <= the 20th percentile of R over the 2160 bars ending at t-1 (rolling quantile 0.20, excluding the current bar). ENTRY at close of bar t when ALL hold: (1) Squeeze was true on at least one of the previous 24 bars (t-24..t-1); (2) close(t) > highest high of the prior 168 bars (t-168..t-1, excluding current bar); (3) close(t) > SMA(2400) of close; (4) no open position; (5) cooldown satisfied. EXIT at close of bar t when close(t) < lowest low of the prior 336 bars (t-336..t-1, excluding current), or via the hard stop. STOP-LOSS: fixed 8% below entry price (native intrabar stop). COOLDOWN: no re-entry for 72 candles after any exit. No take-profit, no pyramiding, no other filters. Warm-up: 2400 bars.','2026-10-30T13:49:38.324198+00:00','No price data viewed; only the context file and validation protocol (BTC, ETH, BNB 1h description through 2026-10-30).','rejected at exploration','Long breakout after a multi-day volatility squeeze in an established uptrend');
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
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('metrics',200);
INSERT INTO "sqlite_sequence" VALUES('decisions',10);
INSERT INTO "sqlite_sequence" VALUES('agent_runs',10);
COMMIT;

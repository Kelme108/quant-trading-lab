---
name: project-structural-decisions
description: "Pending owner decisions (2026-11-12) on more pairs, futures dry-run and maker-only orders to make frequent day trading viable"
metadata:
  node_type: memory
  type: project
  modified: 2026-11-14T09:55:57.299Z
---

Pending owner decisions raised 2026-11-12 in research/reviews/2026-11-12-revisao-day-trade.md: (1) widen the universe from 9 to ~25-30 liquid pairs (frequency per multi-pair bot comes from the pair count; needs data, new splits, breadth rule change); (2) futures (perpetual) dry-run for lower fees and short selling (fixes the 2022-24 losses; adds leverage/liquidation risk); (3) maker-only limit orders on spot. The owner kept the Docker memory cap unchanged on 2026-11-12.

**Why:** the review found no spot, long-only rule that is day trade, frequent (100+/yr/pair) AND net-positive after the 0.30% round trip; frequent rules had gross moves near zero.

Research added 2026-11-12 (research/reviews/2026-11-12-pesquisa-direcao-day-trade.md): recomputing the scoreboard's 56 day-trade rules at a lower round trip, 9 rules with 40+ trades/yr/pair turn net-positive at 0.15% (futures taker) vs 6 at 0.30%: futures is the lever with most support in the lab's own data. Also raised: taker-buy volume from Binance klines as new free data, and B3 WIN/WDO via the existing MT5 layer (~0.01-0.02% round trip) as a later second market. Evidence on autonomous LLM traders (Alpha Arena, 6-month production fleets arXiv 2609.05663) shows no edge: keep LLMs as researchers, never deciders.

**Decision 2026-11-13:** the owner chose (1) more pairs. Universe is now 26 pairs (+17: AVAX DOT TRX NEAR UNI BCH XLM FIL AAVE INJ HBAR OP APT ARB SUI ATOM ETC), commit bf4d5fb, breadth 0.6 unchanged (16 of 26). Futures and maker orders stay NOT chosen. Retired H-100..H-104 (0 trades in 2 days) are being re-run on 26 pairs via `recalibrate --rule-change-reason`; the loop kept running.

**Decisions 2026-11-13 (plan research/reviews/2026-11-13-plano-evolucao-day-trade.md):** D1 YES replace the 2-day inactivity retirement by "expected vs observed" (trades cluster: H-104 on 26 pairs survives 14 days only 8% under the 2-day rule); D2 YES a separate perpetual-futures dry-run lane, isolated margin, 1x, long+short, real_money untouched; D3 maker orders NOT now; D5 5m/1m and ML NOT now; D4 keep breadth 16/26 (synthetic sim: 13/26 passes 38% of break-even rules).

**Done 2026-11-13 (main 3b49421):** D1 rule live (lab/activity.py, the freeze carries `activity_expectation`); parallel exploration (LAB_PARALLEL_PAIRS=3, early stop; H-121 re-run gave identical gate reasons, 20 vs 58 min); lab/gitops.py; futures lane infra (lab/lanes.py, config.futures.dryrun.json, futures data for 26 pairs in user_data/data/binance/futures). Futures still pending: the owner's confirmation of the futures splits (docs/faixa-futuros.md section 4: same dates as spot, hypotheses whose spot validation was read cannot be validated on futures), then lane in registry/pipeline/agents and dry-run. Finding: in 2021 long futures paid ~0.05%/8h funding; under the lab's slippage model futures base is 0.24% and conservative 0.39% round trip, so the futures gain is mostly the short side.

**Change 2026-11-13 (later the same day):** the owner REVERSED D5 for charts: wants to operate on 1m, 5m and 1h "if possible, even if it means restructuring everything". Measured (Binance 1m, last 30 days): BTC moves a median 0.022% in 1 min and 0.051% in 5 min; only 0.5% (1m) / 4.5% (5m) of windows beat the 0.24% futures round trip (ATOM 3.3% / 20%). So 1m/5m can only be entry timing with holds of 30-120 min, or need maker fees (D3, still not chosen). Futures lane part 2 sits uncommitted on branch futures-lane-2 (worktree scratchpad/wt2).

**Decision 2026-11-14 (owner, AskUserQuestion):** refocus the lab on 1m/5m. (a) market: FUTURES only for short timeframes; (b) old strategies: QUICK SCREEN — run each archived strategy at 5m and 1m on exploration data only (ends 2024-07-04; validation is 2024-07-05..2026-10-20 and stays unread), 3 pairs, measure gross per trade and trades/day; survivors become new hypotheses through the normal pipeline; every screened variant counts as a trial; the 9 families whose validation was read may be explored, never validated again; (c) loop PAUSED (STOP_CYCLES) after the current cycle until 1m/5m infra is ready, then restart with agents focused on 1m/5m. Futures lane is on main (7f11427, 2026-11-14).

**How to apply:** do not implement any of the three without the owner's explicit choice; bring them up when the owner asks how to get more trades or better results. Related: [[day-trade-focus]].

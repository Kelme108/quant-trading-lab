---
name: day-trade-focus
description: "Owner wants day-trade bots with MANY trades per day, fast dry-run validation; inactivity judged against the bot's own exploration since 2026-11-13"
metadata:
  node_type: memory
  type: user
  modified: 2026-11-13T18:09:42.395Z
---

The owner wants DAY TRADE strategies with many trades per day — real intraday bots, ideally 1-4 trades/day/pair (400-1500/yr) across the pair universe — so dry-run and live evidence builds in days/weeks. Slow rules with a few trades per year (e.g. H-004) are "sem sentido" for the goal, however good the backtest. They accept high agent spend. Backtests use a 1000 USDT paper wallet since 2026-11-08 (their choice).

**Why:** stated 2026-11-06, reinforced 2026-11-08 ("estratégias que façam muitos trades diários"), 2026-11-09 ("sempre lembre disso, é day trade") and 2026-11-12 ("queremos day trade apenas, estratégias boas e que façam bastante trades").

**How to apply:** keep agent guidance on 15m/1h intraday with forced-flat time exits and a gross move per trade well above the 0.30% base round trip; never propose slow trend rules. Stay honest that costs kill tiny-move scalps.

**Dry-run rule:** the 2-day rule (owner, 2026-11-12) was REPLACED on 2026-11-13 (owner decision D1) by "expected vs observed": a bot is retired when its closed trades after T days fall below the 1st percentile of its own exploration over T-day windows, or it stays quiet longer than the longest gap of that exploration (lab/activity.py, record stored in the freeze; legacy 2-day keys only for freezes without the record). Reason: trades come in bursts, so the 2-day rule retired ~92% of even the best bots before day 14. auto_retire still on; retired freezes go to research/forward/retired/. Any watchdog must only restart bots with an active freeze.

**Sources (owner asked 2026-11-12 to strengthen them and feed results back):** evidence first (research/knowledge/evidence.md, sources-queue section 0), then bot repos; ICT/SMC concepts were all noise. The day-trade scoreboard (lab/knowledge.py) feeds agents every step. 2026-11-12 review: 0 of 17 frequent day-trade rules had a positive net per trade; structural levers (more pairs, futures, maker orders) were left as owner decisions — see [[project-structural-decisions]].

**B3 (2026-11-16):** same wish restated for WIN/WDO ('saiba que quero regras com bastante trades', after P-004 trades once a day): b3_program.json scope.min_expected_trades_per_year = 500 per market from P-014 (validate_proposal refuses fewer). Honest caveat to keep repeating: on WIN exploration the frequent rules lost per trade (P-005 1m ~4,480/yr, -0.0135% gross); only P-004 (246/yr) passed exploration. Related: [[b3-win-wdo-plan]], [[b3-timeframes-1-5-15]].

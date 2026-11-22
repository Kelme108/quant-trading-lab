---
name: b3-win-wdo-plan
description: "B3 WIN/WDO via the Clear MT5 demo: since 2026-11-16 the project's main lane (5y data, approved splits A, B3 lane in the runner, crypto adapter, portal sections, agents on WIN/WDO)"
metadata:
  node_type: memory
  type: project
  modified: 2026-11-16T15:08:22.887Z
---

Owner decided 2026-11-12 to bring B3 WIN/WDO into the lab; on 2026-11-16 approved docs/plano-b3-reuso.md with every recommendation ("tudo mais que você sugeriu, pode fazer", D1-D6) after raising the Clear terminal's "Max bars in chart" to Unlimited.

**Account/data:** Clear terminal `C:\Program Files\Clear Investimentos MT5 Terminal\terminal64.exe`, server ClearInvestimentos-DEMO, owner keeps it logged in; attach with `python -m b3.data.mt5_history ... --attach b3/config/broker_mt5.json` (no password, demo only; live/.env holds the OLD XP account, never use it; never XPMT5-PRD). Data in user_data/data/b3/clear/ (gitignored): WIN$N/WDO$N 1m/5m/15m/D1 from 2021-11-16 + WIN$/WDO$ D1 (proportional, used only to find roll days). Server clock = Sao Paulo.

**Done 2026-11-16 (commits e49611c..20a0ef0):** splits_b3.json approved (scenario A: exploration 2021-11-16..2024-07-01, validation ..2025-10-01, final test after, locked); gates_b3 = proxy gates; scope_b3 WIN/WDO >=1m; b3/b3_data.py (rolls, back-adjust, history calendar); B3Market in b3/markets.py (stop pays 1 extra tick base); runner b3 lane -> research/b3/ (own ledger). b3/freqtrade_adapter.py + b3/ftshim run the 126 portable crypto strategies (12 excluded: other pairs), fidelity on BTC 96-100%. Screen protocol b3/config/crypto_screen_b3.json; follow-up research/tools/b3_screen_followup.py (DSR/PBO + one validation read). Portal: lab/universes.py + universes.js -> nav sections Cripto / B3: WIN e WDO / Substitutos with the same Resultados pages and the candle chart. Agents: b3/config/b3_program.json (lane b3, from P-013, stop 2026-12-16), task TradeInitial-ProxyCycle every 3h until 2026-12-16.

**Results so far:** P-001..P-011 on WIN/WDO exploration: only P-004 WIN passed, failed its validation read (-1.13% vs bar 2.9%). WDO costs 0.0235% round trip (move/cost 5m 1.6x) - hard market; WIN 0.011% (5m 4.7x).

**How to apply:** never read validation twice or the final test (owner unlocks); new reads go through b3/proxy_research.py so they count as trials; the live engine does NOT do shorts or moving stops yet (F6 needs that before any dry-run of such a rule); dry-run as EVIDENCE only with a validation-approved rule (D6 a).

**Demonstration 2026-11-16 (owner: "continue o motor de validar estratégias, mas quero apenas demonstração de como está se portando no demo"):** P-004 (failed validation) runs on the Clear DEMO as a demonstration, NOT evidence: live/config/demo-b3-p004-win.json (WINZ26, 1 contract, shorts allowed only on demo, attaches without credentials), live/strategies/b3_rule.py, Windows task TradeInitial-DemoB3 (weekdays 08:40), portal page #/b3-demo (lab/demo_b3.py; live 1/5/15m view from live/feed.py, every 5 s). Same day the owner added P-004 on WDO (WDOZ26, task TradeInitial-DemoB3-WDO; P-004 failed WDO exploration). Roll WINZ26 -> WING27 before 2026-12-16 and WDOZ26 -> WDOF27 before 2026-12-01. Stop: live/STOP. Owner also asked half of new agent rules on 1 minute and half on 5 (b3_program.json alternate_timeframes_min, P-013 1m, P-014 5m, ...). Related: [[proxy-markets-lane]], [[day-trade-focus]], [[parallel-sessions]].

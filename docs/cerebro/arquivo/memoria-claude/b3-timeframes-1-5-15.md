---
name: b3-timeframes-1-5-15
description: "Owner 2026-11-16: WIN/WDO research and charts only on 1, 5 and 15 minutes; focus 1 and 5 minutes; charts must show 1-minute candles"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-16T15:48:48.941Z
---

On 2026-11-16 the owner corrected me ("você está seguindo errado"): WIN/WDO work stays on 1, 5 and 15-minute timeframes only, the focus is 1 and 5 minutes, and the portal charts must show 1-minute candles too.

**Why:** the owner wants fast intraday day trading on B3; I had run the crypto strategies at their own 1h/4h candles and the chart only on 15m.

**How to apply:** enforced in b3/config/scope_b3.json timeframes_min [1,5,15] (runner refuses other SIGNAL timeframes, crypto ports judged by their own candles) and b3_program.json; agents propose 1/5-minute rules first; B3 charts are per session on 1/5/15m, default the rule's 1m/5m. Never add 30/60-minute or hourly rules to the B3 lane without asking. Related: [[b3-win-wdo-plan]], [[day-trade-focus]].

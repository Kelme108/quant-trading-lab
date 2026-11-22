---
name: esteira-conveyor
description: "2026-11-17 owner approved the strategy conveyor (b3/esteira.py): families screened with a soft anti-overfit gate, demo is the real test, 15-rule stop replaced by daily limits"
metadata:
  node_type: memory
  type: project
  modified: 2026-11-17T22:25:14.931Z
---

Owner 2026-11-17 ("tudo aprovado"): the backtest is a filter, not the judge, because live changes the profile; generate many simple rules fast ("esteira").

- **Config:** b3/config/esteira_b3.json (approved, pre-registered).
- **Code:** b3/esteira.py, with families in b3/families/*.py (`FAMILIES = [Family(...)]`, at most 3 params, small grid).
- **Screen** (exploration only, measured cost decides): ≥500 trades/yr; mean net > 0; ≥5 of 8 time slices positive; plateau (≥2/3 one-step neighbours positive); best per family; overlap ≤0.5 with selected rules. DSR/PBO only reported; they stay the bar for real money.
- **Checks before any read:** look-ahead and a 21-session window. Each family id is screened once; a changed idea needs a new id.
- **Default exit:** target R$30 / stop R$30 / 30 min, replayed on 1m bars. The vectorized version matched a plain loop 2996/2996.
- **Demo step (not built yet):** auto-deploy survivors, cut after 60 trades if mean net < 0, owner review at 200. The 15-rule stop is replaced by limits of 40 families/day and US$15/day of agent cost (numbers set by the assistant).
- **Batch 1** (8 families E-001..E-008, 152 variants, commit 8774af0): none passes.
  - WIN is about 50% hits.
  - WDO loses about R$6-8/trade, because R$30 is only 6 ticks and the cost is ~20% of the target. The default exit in BRL is unfair to WDO: raise this when the owner decides stop/take-profit.

**Why:** the owner found the agent pipeline slow (one rule per ~20-minute cycle) and the strict gate pointless before live.

**How to apply:**
- Next steps: agent writes families in batches (step 4), then demo auto-deploy and cut (step 3).
- Live parity relies on the window check.
- Related: [[b3-pattern-search]], [[day-trade-focus]].

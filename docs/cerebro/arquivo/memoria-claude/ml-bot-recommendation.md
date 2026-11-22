---
name: ml-bot-recommendation
description: "ML / heavier bot: owner decided NOT now (D5, 2026-11-13); revisit only as a pre-registered low-dim meta-label filter (B-ML-1) on a B3 rule that already showed gross edge"
metadata:
  node_type: memory
  type: project
  modified: 2026-11-13T18:55:27.589Z
---

On 2026-11-13 the owner asked whether to invest in a "parrudo" bot (combined indicators, gradient boosting, FreqAI, direction/regime classifiers). The owner had already decided on 2026-11-13 (D5 in research/reviews/2026-11-13-plano-evolucao-day-trade.md): "5m/1m e ML: não agora". The analysis below agrees and adds the conditions for revisiting. Recommendation given (analysis only, nothing implemented):

- Verdict: not now. In crypto spot, no (cost wall: 0 of 17 frequent day-trade rules net-positive). In B3, only as a meta-labeling filter on a simple rule (B-1 session momentum) that first shows gross edge > conservative cost in exploration.
- Evidence used: adding the RVol filter cut trades 26-73% in 5 rules (H-043→H-104 etc.), conflicting with the 2-day inactivity rule; 14 hypotheses failed causality checks already; strategy_check allows only numpy/pandas and no file I/O, so a model must be embedded as constant coefficients (logistic / shallow tree); lab/walkforward.py has no refit/purge/embargo.
- Proposed B-ML-1: logistic L2 C=1, 5 fixed features, target = net >0 at conservative cost, anchored yearly walk-forward with 1-session embargo, threshold p>0.5, validation read once, 1 variant only; pass requires B3 gates + net PnL and Sharpe ≥ unfiltered + improves in ≥60% of years + ≥150 trades/yr.

**Why:** B3 data are still clean ([[b3-win-wdo-plan]] rule: don't peek before splits); ML would spend them on tuning.
**How to apply:** if the owner revisits ML, start from this; don't re-derive. Run B-ML-1 only after F1.2 depth, approved B3 splits and B-1 exploration. Related: [[day-trade-focus]], [[project-structural-decisions]].

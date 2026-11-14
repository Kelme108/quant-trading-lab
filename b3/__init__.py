"""B3 research lane: mini Ibovespa (WIN) and mini dollar (WDO) futures.

Plan: docs/plano-b3-win-wdo.md. This package holds what the Freqtrade lab cannot do for B3 futures:
the trading calendar and session hours, contract expiries and rolls, costs in BRL per contract, a
bar backtester that follows the same fill rules as live/brokers/paper.py, data download from MT5
and data checks.

Rules carried over from the crypto lab:
- a strategy is one object, used unchanged by the backtester and by live/core/engine.py;
- indicators look backwards only (checked by lab/causality.py, see b3/checks.py);
- no calendar or contract fact is written from memory: holidays and hours live in b3/config/*.json
  with their official source, contract specs are read from the server and cross-checked;
- B3 returns are not looked at before the B3 splits are approved (plan, section 7).
"""

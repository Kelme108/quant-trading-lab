---
tipo: decisao
data: 2026-11-13
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# Robô de ML ('parrudo'): não agora

**Data:** 2026-11-13

O dono perguntou por um robô "parrudo" (indicadores combinados, gradient boosting, FreqAI). Já havia decidido D5: "5m/1m e ML: não agora". A análise concordou:

- Em cripto spot: **não** (0 de 17 regras frequentes lucrativas após custo).
- Em B3: só como **meta-label** sobre uma regra simples que **já mostre lucro bruto acima do custo conservador** na exploração.
- `strategy_check` só aceita numpy/pandas e sem E/S de arquivo: um modelo teria de entrar como coeficientes constantes. `lab/walkforward.py` não tem refit/purge/embargo.
- **B-ML-1** proposto: regressão logística L2, 5 atributos fixos, alvo = líquido > 0 no custo conservador, walk-forward anual com embargo de 1 sessão, limiar 0,5, validação lida uma vez, 1 variante; passa só se bater o não filtrado, melhorar em ≥ 60% dos anos e ter ≥ 150 trades/ano.

**Como aplicar:** se o dono reabrir o ML, parta daqui, sem rederivar. Só vale sobre uma regra de B3 com lucro bruto comprovado (ver [[2026-11-17-esteira-aprovada]]).

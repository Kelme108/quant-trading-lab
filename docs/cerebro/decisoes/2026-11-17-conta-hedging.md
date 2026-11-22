---
tipo: decisao
data: 2026-11-17
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# As contas do dono são hedging

**Data:** 2026-11-17

O dono disse: "minha conta é a hedging"; reforçou: "hedging, já foi falado". A conta real (servidor `ClearInvestimentos-CLEAR`) e a demo (`ClearInvestimentos-DEMO`) leem `account_info().margin_mode == 2` (0 netting, 1 exchange, 2 hedging).

Um rótulo anterior "netting" era um bug do Claude: comparou com uma constante do MT5 em vez do número.

**Como aplicar:** vários robôs por contrato são aceitáveis nas duas contas; **não volte a falar em netting**. Ao checar o modo, imprima o número bruto. Um terminal segura uma conta por vez; logar outra conta no terminal demo derruba os robôs (como às 14:20 de 2026-11-17).

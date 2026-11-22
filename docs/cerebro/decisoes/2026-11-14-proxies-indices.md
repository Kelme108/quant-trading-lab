---
tipo: decisao
data: 2026-11-14
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# Linha de proxies (CFDs de índice), encerrada

**Data:** 2026-11-14 a 2026-11-16

O dono não tinha conta de corretora brasileira, então a pesquisa de day trade 1m/5m foi para **proxies** na conta MetaQuotes-Demo: US500, USTEC, US30, US2000, DE40 (só dados), FX e USDBRL (substituto do WDO). Motor `b3/` com as regras P-001.. em `b3/strategies/proxies.py`.

**Resultado:** de 58 pares regra×mercado, 3 passaram a exploração, 2 a validação e 0 o teste final (P-003 em US500 e USTEC rejeitada depois que o dono destrancou o teste final só para ela). 1m inviável (P-005: bruto 0,003% por trade contra 0,01% de custo); FX sem edge; ordens maker em cripto sofrem seleção adversa.

**Encerrada em 2026-11-16**, quando a conta Clear demo trouxe WIN/WDO reais. Os agentes passaram para WIN/WDO ([[2026-11-16-b3-win-wdo-plano]]). Material em `research/proxies/`; veredito em `research/reviews/2026-11-14-veredito-1m-5m.md`.

**Como aplicar:** não religar sem pedido do dono. O modelo de custos (stop paga slippage) foi herdado pela B3.

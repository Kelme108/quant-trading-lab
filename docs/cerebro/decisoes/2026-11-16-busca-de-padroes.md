---
tipo: decisao
data: 2026-11-16
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# Busca de padrões no WIN (A, B, C), ticks e estudo de saídas

**Data:** 2026-11-16 e 2026-11-17

Plano aprovado: [plano-busca-padroes-b3](../../plano-busca-padroes-b3.md). Pré-registrado em `b3/config/pattern_search_b3.json`; código `b3/pattern_search.py`; resultados em `research/b3/search/`.

**Resultado (só exploração):**
- **A**: 552 variantes; nenhuma passa. Melhor bruto frequente +0,004% por trade contra o alvo de 0,033%; DSR máx. 0,002; PBO 0,20.
- **B** (filtro LightGBM em 3 bases): 9 variantes, PBO 0,81; nenhuma passa.
- **Alavanca 1** (custo medido nos ticks): 36 variantes com líquido > 0 no custo médio, **nenhuma no p90**; DSR máx. 0,009; PBO 0,51.
- **WDO**: 0 de 398 variantes frequentes lucrativas, mesmo no custo medido.
- **C** (regras mais raras, 849 tentativas): melhor C04 (fade de choque de faixa, 5m, 61/ano, +7%), DSR máx. 0,034; nenhuma passa.
- **Programa de ticks** (aprovado; leitura de decisão só após 2026-12-31): a leitura interina T02 (fade de desequilíbrio, 15 min) é o sinal mais forte até agora e **ainda é ruído** (DSR 0,22, PBO 0,57).
- **Estudo de saídas** (2026-11-17, 96 variantes WIN): nenhuma passa; melhor +R$ 0,20 por trade no custo medido, negativo no p90. As saídas cortam perdas mas não criam edge.

**Como aplicar:** não rerode variações dessas 16 famílias: já contam como 561 tentativas. Alavancas restantes: slippage real e ordens limite, fluxo de ordens por tick, trades mais raros e maiores. Ver [[Resultados-B3]].

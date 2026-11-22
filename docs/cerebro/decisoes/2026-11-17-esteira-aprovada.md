---
tipo: decisao
data: 2026-11-17
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# Esteira de estratégias aprovada

**Data:** 2026-11-17 ('tudo aprovado')

O dono achou o pipeline de agentes lento (uma regra por ciclo de ~20 min) e o portão estrito sem sentido antes do ao vivo. Aprovou a **esteira**: o backtest é filtro, a demo é o teste ([[Esteira]]).

- Config pré-registrada: `b3/config/esteira_b3.json`. Filtro só na exploração, com custo medido.
- Saída padrão: alvo R$ 30 / stop R$ 30 / 30 min (depois, o [[Menu-de-saidas]]). A versão vetorizada bateu com o laço simples em 2996/2996 trades.
- O limite de 15 regras do pipeline foi trocado por limites diários (famílias por dia e gasto de agente).
- **Lote 1** (E-001..E-008, 152 variantes): nenhuma passou. WIN acerta ~50%; WDO perde ~R$ 6–8 por trade (R$ 30 são só 6 ticks).
- O passo de demo automática (cortar após 60 trades se líquido < 0, revisão do dono em 200) foi planejado e **nunca construído**: hoje o Claude liga os robôs à mão.

**Como aplicar:** ver [[Esteira]] para o ciclo e os limites.

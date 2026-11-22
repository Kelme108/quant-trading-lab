---
tipo: resultados
atualizado: 2026-11-19
tags: [cerebro, resultados, b3]
---

# Resultados da linha B3 (até 2026-11-19)

> Honestidade primeiro: **nenhuma regra tem evidência fora da amostra para dinheiro real.** Tudo abaixo é exploração, exceto a leitura única da validação da P-004. Números novos devem ir para o ledger e para esta nota, com a data.

## Quadro geral

| Frente | Resultado | Fonte |
|---|---|---|
| P-001..P-011 em WIN/WDO (exploração) | Só a **P-004 WIN** passou; **reprovou na validação** (−1,13% contra barra de 2,9%) | `research/b3/ledger.jsonl` |
| Regras de agente P-014..P-030 | Rejeitadas na exploração de WIN; rodam na demo só como demonstração | `research/b3/results/` |
| Busca de padrões A/B/C | Nenhuma passa; melhor bruto frequente +0,004% contra alvo 0,033% | [[2026-11-16-busca-de-padroes]] |
| Custo medido (WIN) | 0,39 tick por lado a mercado; slippage ≈ 80% do custo | `research/b3/execution_cost.json` |
| WDO | 0 de 398 variantes frequentes lucrativas; custo 0,0235% | `research/b3/search/wdo/` |
| Estudo de saídas (96 variantes) | Nenhuma passa; saídas cortam perdas mas não criam edge | [[2026-11-16-busca-de-padroes]] |
| Programa de ticks (interino) | Sinal T02 mais forte, mas ruído (DSR 0,22, PBO 0,57) | `research/b3/ticks/` |
| Estudo P-026 → P-032 | Fade de caixa comprimida passa na exploração (+R$ 2,37 por trade, p90 +0,67) | [[2026-11-18-p026-menu-de-saidas]] |
| Esteira E-001..E-387 + menu de saídas | ~20 mil versões lidas; 314 candidatas; 11 na demo | [[Menu-de-saidas]], [[Esteira]] |
| Saídas em reais (alvo R$ 35 / stop R$ 90 e vizinhos) | 6.160 versões em 76 famílias; 29 com lucro no p90; nenhuma ligada | [[2026-11-20-saidas-em-reais-35-90]] |

## O que a demo ainda não respondeu

- Só **um pregão** com os 24 robôs ligados (2026-11-19: 44 trades; ver [[Demo-diario]]). Dos 11 robôs da esteira, 4 operaram, com 16 trades: amostra pequena demais para concluir.
- Comparar sempre: taxa de acerto, resultado por trade e motivos de saída contra a pesquisa ([[Robos-demo]]).

## Como ler números destas notas

- "Por trade" é **líquido de custo medido** (cenário médio), em R$ por contrato.
- "p90" é o cenário de custo pessimista.
- A taxa de acerto depende da saída: S2 ≈ 65–68%, S3 ≈ 41–43%. Resultado por trade é o que importa ([[Menu-de-saidas]]).
- Com muitas versões lidas, parte das candidatas é sorte. Só a validação e a demo separam sorte de edge.

## Evidência exigida para dinheiro real

Leitura única da validação (aprovada pelo dono para aquela regra), DSR ≥ 0,95, PBO ≤ 0,3, líquido > 0 em custo base e conservador, depois a demo coerente com a pesquisa, e por fim a decisão do dono por escrito ([[Regras-inviolaveis]], [../../checklist-operacao-real.md](../../checklist-operacao-real.md)).

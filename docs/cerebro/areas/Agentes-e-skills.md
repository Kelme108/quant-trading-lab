---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, agentes, skills]
---

# Agentes e skills

Definições em `.claude/agents/` e `.claude/skills/`. Cada agente só pode criar os arquivos esperados no seu passo; o guard confere ([[Lab-de-pesquisa]]).

## Agentes

| Agente | Uso |
|---|---|
| `esteira-research` | Escreve **um lote** de 5–10 famílias em `b3/families/` ([[Esteira]]) |
| `proxy-research` | Propõe **uma** regra P-NNN em JSON (linha B3/proxies) |
| `proxy-developer` | Implementa a proposta em `b3/proxy_rules/` + teste sintético |
| `scout` | Coleta ideias de papers, artigos e documentação |
| `research` | Propõe uma hipótese H-NNN (linha cripto) |
| `developer` | Implementa a hipótese como estratégia Freqtrade + teste |
| `validator`, `quant`, `risk` | Revisões em texto dos resultados registrados |

Regra: **nenhum agente decide** aprovação, rejeição ou dinheiro. Teto de gasto: [[Esteira]] e `lab/config/budget.json`.

## Skills `trader-*`

Fluxo de investimento discricionário independente do laboratório; geram **propostas**, nunca ordens sem confirmação: `trader-copycat`, `-analyst`, `-screener`, `-budget`, `-risk`, `-broker`, `-rebalance`, `-tax`, `-news`, `-alerts`, `-pelosi`. Não usadas na linha B3.

## Fontes de ideias

Evidência primeiro (`research/knowledge/evidence.md`, fila em `research/sources-queue.md`), depois repositórios de robôs. Conceitos ICT/SMC foram todos ruído. Ver [[2026-11-06-day-trade-foco]].

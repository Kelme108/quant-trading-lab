---
tipo: decisao
data: 2026-11-16
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# Relógio dos ticks do MT5 da Clear

**Data:** 2026-11-16

No terminal Clear demo, `time_msc` dos ticks é o **relógio de parede da B3** contado como se fosse UTC (igual aos horários das barras; os configs usam deslocamento do servidor −3).

- Pedidos a `copy_ticks_range`/`copy_ticks_from` usam o mesmo relógio: para ler 09:00–09:20 da B3, passe `datetime(…, 9, 0, tzinfo=UTC)` consciente.
- Um datetime **ingênuo** é lido pelo pacote como hora local da máquina (BRT) e cai 3 h adiante.
- O erro apareceu quando o último tick do dia mostrava 15:31 em vez de 18:31. A primeira versão de `research/tools/b3_execution_cost.py` lia 12:00–18:30 achando que era 09:00–15:30; foi corrigida e remedida.
- Contratos vencidos não são selecionáveis: só o corrente e o próximo.

**Como aplicar:** em todo código novo de ticks, converta com `timezone.utc` para hora de parede da B3; nunca fuso de São Paulo, nunca ingênuo. Ver [[Dados]].

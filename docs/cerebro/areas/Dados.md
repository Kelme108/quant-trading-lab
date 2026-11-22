---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, dados, mt5]
---

# Dados

Nada de dado de mercado vai para o git (`user_data/data/` é ignorado). Quem clonar precisa reconstruir.

## B3 (WIN/WDO)

- Origem: terminal **MetaTrader 5 da Clear**, conta demo, anexado **sem senha** (`b3/config/broker_mt5.json`). O dono mantém o terminal logado.
- Ferramenta: `python -m b3.data.mt5_history ... --attach b3/config/broker_mt5.json`.
- Destino: `user_data/data/b3/clear/`: `WIN$N`/`WDO$N` em 1m, 5m, 15m e D1 desde 2021-11-16, e `WIN$`/`WDO$` em D1 (proporcional, só para achar dias de rolagem).
- O terminal precisa de "Max bars in chart" em **Unlimited** para entregar 5 anos de 1 minuto.
- Relógio do servidor = horário de São Paulo. **Ticks** usam outra convenção: [[2026-11-16-relogio-tick-mt5]].
- **Gravador de ticks**: `b3/data/tick_recorder.py` (tarefa dos dias úteis às 19:05, só leitura) grava em `user_data/data/b3/clear/ticks/`. Só dá para ler contrato corrente e próximo; contratos vencidos somem. Há ~58 milhões de ticks desde 2026-08-17.
- Qualidade: dias com menos de 90% das barras da sessão não geram entrada. Relatório em `research/b3/data_quality.json`.

## Cripto (linha antiga)

Candles públicos da Binance (spot e futuros) em `user_data/data/binance/`, baixados pelo Freqtrade ou por `python -m lab.orchestrator expand-data`. Ver [[Cripto-Freqtrade]].

## Proxies (encerrada)

CFDs de índice exportados do MetaQuotes-Demo para `user_data/data/mt5/`. Ver [[2026-11-14-proxies-indices]].

## Cuidados

- Ticks ficam **dentro do teste final** do programa de barras: um programa de ticks precisa de splits próprios aprovados (já existem em `b3/config/tick_program_b3.json`).
- Nunca peça ao dono para colar credenciais; o terminal logado basta.

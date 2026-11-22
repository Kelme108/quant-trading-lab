---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, cripto, freqtrade, legado]
---

# Linha cripto (Freqtrade) — pausada

Primeira linha do projeto: 26 pares spot da Binance (BTC, ETH, BNB e mais 23) em `15m` e `1h`, backtest e dry-run com **Freqtrade 2026.9** em Docker. Ver o [README](../../../README.md) e [../../funcionamento-geral.md](../../funcionamento-geral.md) (**envelhecido**, de 2026-11-08).

## Por que está pausada

Revisão de 2026-11-12: nenhuma regra spot, só comprada e frequente era lucrativa depois do custo de 0,30% por ida e volta. Em 2026-11-14 o dono refocou 1m/5m em mercados com custo ~0,01% ([[2026-11-14-proxies-indices]], depois [[2026-11-16-b3-win-wdo-plano]]). O loop de pesquisa de cripto foi pausado (`STOP_CYCLES`); não há dry-run ativo.

## O que ficou

- 140+ estratégias em `user_data/strategies/` (e arquivadas), com testes em `tests/archive/`.
- `research/experiments/`, `manifests/`, `proposals/`: um conjunto por hipótese (H-NNN).
- Regra de inatividade D1 (esperado × observado) e universo de 26 pares: [[2026-11-13-decisoes-estruturais]].
- Linha de futuros (perpétuos) montada na infraestrutura; sem dry-run (aguarda divisões do dono).
- 126 estratégias de cripto portadas para B3 por `b3/freqtrade_adapter.py` (fidelidade 96–100% em BTC).

## Para religar

Ler [../../migracao-linux.md](../../migracao-linux.md) e `ops/linux/`. **Pergunte ao dono**: o loop gasta dinheiro de agente.

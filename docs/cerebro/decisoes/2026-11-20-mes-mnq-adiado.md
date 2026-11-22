---
tipo: decisao
data: 2026-11-20
atualizado: 2026-11-20
tags: [cerebro, decisao, mes, mnq, adiado]
---

# MES e MNQ na seção de outros ativos: adiado

**Data:** 2026-11-20  ·  **Quem decidiu:** o dono ("vamos deixar pra depois isso, vai ser um pouco trabalhoso")

## O pedido

Colocar o micro S&P 500 (**MES**) e o micro Nasdaq-100 (**MNQ**) na seção de outros ativos do portal ao lado de Cripto, B3 e Substitutos, rodar a esteira neles e validar, para uso no passo seguinte.

## O que a análise (sem alterar código) encontrou

- **Não há dado real de MES/MNQ.** O projeto tem só os substitutos da conta MetaQuotes-Demo: `US500` (~ES/MES) e `USTEC` (~NQ/MNQ), CFDs com negociação desabilitada. Os mercados já estão em `b3/markets.py` com custo de 0,01% por ida e volta e 0,005% extra por stop.
- **Cobertura:** US500 tem sessões completas desde 2017-04; **USTEC só desde 2022-07** (exploração de ~1,5 ano, evidência fraca para o MNQ).
- **Contratos reais:** MES = US$ 5 por ponto, MNQ = US$ 2 por ponto, tick de 0,25 ponto.
- **A esteira só lê dados da B3.** Para rodar em MES/MNQ seria preciso: ramo de carga de barras e calendário de Nova York em `b3/pattern_search.py` (`_session_bars`, `split_bounds`, `other_market`), `load_minutes` e `costs_for` em `b3/esteira.py`, e custo **proporcional ao preço** nos dois simuladores (`b3/esteira.py` e `b3/p026_lab.py`), que hoje só aceitam taxa fixa em reais e slippage em ticks.
- **Uso ao vivo:** a conta MetaQuotes não negocia esses CFDs. Operar MES/MNQ exige uma corretora de futuros CME com demo no MT5. Decisão do dono, ainda aberta.
- **Validação:** o mesmo dado de US500/USTEC já teve a janela de validação lida para P-001 e P-003, e o teste final foi aberto só para a P-003. Regras novas podem ter leitura nova, uma por regra e mercado; ler em massa queimaria a validação.

## Se retomarem

1. Dono decide a fonte de dados (substitutos CFD ou dado real de futuros) e a corretora para o uso ao vivo.
2. Implementar o ramo de dados e custos acima, com testes.
3. Pré-registrar escopo (famílias com prévia na B3 primeiro), custos e a regra de quantos finalistas vão à validação, e só então rodar.
4. Seção do portal: o caminho barato é uma página própria com a tabela de candidatas; replicar as páginas completas de Resultados exige gerar arquivos no formato da linha de proxies.

Ver [[Pendencias-e-calendario]] e [[2026-11-14-proxies-indices]].

# Plano: levar o projeto para WIN e WDO reaproveitando tudo (16/11/2026)

## Objetivo

Pesquisar, visualizar e acompanhar day trade em **WIN** (mini Ibovespa) e **WDO** (mini dólar) com dados reais da B3, pela conta de demonstração da Clear. A ideia é reaproveitar o que já foi construído para cripto e para os mercados substitutos:
- o motor de backtest;
- o protocolo de exploração, validação e teste final;
- os agentes;
- o portal e suas páginas de resultados;
- as 140 estratégias já escritas;
- o robô de dry-run.

## Onde estamos (16/11)

| Item | Estado |
|---|---|
| Conta | Clear, demonstração, servidor ClearInvestimentos-DEMO, gravada em `b3/config/broker_mt5.json` |
| Conexão | `python -m b3.data.mt5_history ... --attach b3/config/broker_mt5.json`: usa o terminal já logado, sem senha, só demonstração |
| Dados exportados | `user_data/data/b3/clear/`: WIN$N e WDO$N em 1, 5, 15 min e diário. Relógio do servidor = São Paulo (1º candle às 09:00) |
| Profundidade | 15 min e diário desde **16/11/2021** (5 anos). 5 min só desde abr/2023 e 1 min desde mar/2026, porque o terminal limita a **100.000 barras** |
| Divisão do período | Proposta em `b3/config/splits_b3.json`, **não aprovada**. Nenhum preço ou retorno foi olhado |

## O que já existe e como será reaproveitado

| Já existe | Hoje serve | Passa a servir |
|---|---|---|
| Motor `b3/backtest.py` (compra e venda, stop, fechamento antes do fim do pregão, paridade com o robô real) | Substitutos (US500, USTEC…) | WIN e WDO, com o pregão da B3 e os custos em reais por contrato (`b3/costs.py`) |
| Calendário da B3 (`b3/calendar.py`, `b3/config/holidays.json`, `sessions.json`) | Planejado | Feriados e horários do WIN (09:00–18:25) e do WDO (09:00–18:30) |
| Executor com leituras registradas, critérios, "lê a validação uma vez", régua que sobe por tentativa | `b3/proxy_research.py` | O mesmo executor, com WIN e WDO como mercados e registro próprio (`research/b3/ledger.jsonl`) |
| Lista de operações por leitura | Substitutos | WIN e WDO, do mesmo jeito |
| Pipeline de agentes, com limite de 3 por semana e parada automática | Substitutos (pausado por limite de uso) | WIN e WDO |
| Portal, seção Índices | Substitutos | Vira "B3 (WIN/WDO)", com os substitutos como aba |
| Portal, páginas de cripto (Ranking, Operações, Comparar, Estratégia, gráfico de candles com as operações) | Cripto | **As mesmas páginas**, com um seletor de universo: Cripto / B3 / Substitutos |
| 140 estratégias de cripto (Freqtrade) | Cripto | Rodadas no WIN e no WDO por um adaptador (fase 2) |
| Robô `live/` com corretora MT5 (`live/brokers/mt5.py`) | Planejado | Dry-run na conta de demonstração da Clear |

## Fases

### Fase 0: dados e divisão do período (feita, falta a sua aprovação)

- **Você:** no MT5 da Clear, em Ferramentas → Opções → Gráficos, coloque "Máx. barras no gráfico" em **Ilimitado** e reinicie o terminal.
- **Eu:** baixo de novo e confirmo se 5 min e 1 min passam a cobrir desde nov/2021.
- **Você escolhe o cenário da divisão:**
  - **A, com 5 anos:** exploração de 16/11/2021 a 30/06/2024; validação de 01/07/2024 a 30/09/2025; teste final de 01/10/2025 em diante, trancado.
  - **B, com a profundidade de hoje:** exploração de abr/2023 a dez/2024; validação em 2025; teste final em 2026. Sem pesquisa em 1 min.

### Fase 1: WIN e WDO no motor e no executor

- WIN e WDO entram como mercados do executor, com o pregão da B3, os feriados e a regra de qualidade dos 90%.
- **Custos:** os de `b3/costs.py`. No cenário base, R$ 0,25 por lado mais 1 tick, o que dá cerca de 0,007% de ida e volta no WIN; o conservador é o dobro, e o stop paga 1 tick a mais.
- **Critérios:** os mesmos dos substitutos (`gates_proxies.json`), em `gates_b3.json`. Registro e régua próprios do mercado B3.
- **Pronto quando:** os testes com dados sintéticos e a paridade com o robô real passarem.

### Fase 2: adaptador das estratégias de cripto

Rodar o **próprio código** de cada estratégia do Freqtrade dentro do motor da B3:
- os sinais de entrada e saída das funções `populate_*`;
- o stop fixo e as funções de saída e stop personalizadas (`custom_exit`, `custom_stoploss`), chamadas a cada candle fechado com uma operação simulada;
- os dados de tempo gráfico maior (1 h, 4 h, diário), montados a partir do próprio contrato.

O pregão, os custos e o fechamento antes do fim do dia ficam por conta do motor da B3.

- **Fica de fora:** 14 estratégias que usam o BTC como referência, sem equivalente na B3.
- **Prova de fidelidade:** rodar o adaptador em dados de BTC para 3 estratégias e comparar com o backtest do próprio Freqtrade, que já está exportado. As operações precisam coincidir.
- **Limitações declaradas:**
  - todas as estratégias são só de compra (o lado vendido seria uma variante nova);
  - foram feitas para cripto 24 h, então numa sessão de 9 h algumas operarão pouco;
  - as proteções do Freqtrade (pausa após perdas) serão aproximadas ou marcadas.

### Fase 3: triagem das 140 estratégias no WIN e no WDO

São cerca de 250 combinações. Pela regra atual, a régua subiria para 26% de lucro mínimo. Proposta:
- Uma **triagem** só na exploração, com custo base e conservador, contada como uma família de tentativas e registrada.
- Passam da triagem as que tiverem ganho bruto de pelo menos 3x o custo e líquido positivo no conservador, até as **10 melhores**.
- As 10 seguem o protocolo normal: os critérios da exploração, com a régua contando as 250 tentativas; o Sharpe deflacionado e o PBO de `lab/stats.py`; a validação lida uma vez.
- O teste final continua só com o seu desbloqueio.

### Fase 4: portal igual ao de cripto

- **Seletor de universo** nas páginas de Resultados (Início, Ranking, Operações, Comparar, Estratégia): Cripto / B3 / Substitutos. As leituras da B3 são montadas no mesmo formato das de cripto, então as mesmas páginas funcionam sem duplicar código:
  - curva de capital e queda desde o pico;
  - mapa mês a mês e horários de entrada;
  - filtros de operações e comparação lado a lado.
- **Gráfico de candles com as operações** marcadas, a partir dos dados exportados da Clear.
- A seção Índices vira **"B3 (WIN/WDO)"**, com o programa de agentes, os ciclos e as medições; os substitutos ficam como aba.
- **Pronto quando:** o teste no navegador cobrir as páginas com o universo B3, sem rolagem lateral no celular.

### Fase 5: agentes no WIN e no WDO

- O mesmo pipeline e os mesmos limites (3 por semana; para após 15 regras sem passar a validação), propondo regras para WIN e WDO.
- O agente pesquisador só vê exploração.
- **Os substitutos encerram:** eram uma ponte até termos dados da B3.
- **Retomada:** o pipeline está pausado desde 16/11 01:47, porque o limite semanal de uso da sua conta Claude acabou. Ele só volta com o seu "ok", porque os agentes gastam do mesmo limite que você usa nas conversas.

### Fase 6: dry-run na demo da Clear

- O robô `live/` operando o contrato vigente (WINZ26 → WING27…) na conta de demonstração.
- **Venda a descoberto:** você aprovou em 14/11 para simulação e demonstração; falta implementar no robô.
- **Só entra** estratégia que passar a validação. O teste final segue a sua regra de desbloqueio.

## Decisões do dono

| Decisão | Opções | Recomendação |
|---|---|---|
| D1. Profundidade e divisão | (a) Subir "Máx. barras" para Ilimitado, re-medir e usar o cenário A; (b) cenário B com o que há hoje | (a): 5 anos dão uma exploração 60% maior e permitem 1 min |
| D2. Critérios da B3 | (a) Os mesmos dos substitutos, com custos de `b3/costs.py`; (b) os do plano B3 de 12/11, com piso em R$ por contrato | (a): o portal compara tudo na mesma escala |
| D3. Estratégias de cripto | (a) Adaptador + triagem das 140, com as 10 melhores seguindo o protocolo; (b) só as 13 ativas; (c) não portar | (a) |
| D4. Portal | (a) Seletor de universo nas páginas de Resultados + seção B3; (b) só a seção B3 | (a): é o "tudo igual" que você pediu |
| D5. Agentes | (a) Retomar o pipeline já apontando para WIN/WDO quando a fase 1 estiver pronta e encerrar os substitutos; (b) retomar já nos substitutos | (a) |
| D6. Dry-run | (a) Só com estratégia aprovada na validação; (b) já com a melhor da triagem, marcada como não validada | (a) |

## Ordem e dependências

```
F0 (você: Máx. barras + escolha da divisão)
 └─ F1 motor B3 ──┬─ F2 adaptador ── F3 triagem ──┐
                  ├─ F5 agentes (B3) ─────────────┼─ F4 portal (cresce junto) ── F6 dry-run
                  └─ F4 portal (estrutura) ───────┘
```

Nenhum retorno de WIN ou WDO é olhado antes da sua aprovação da divisão (D1).

## Entregue em 16/11/2026

Você aprovou todas as recomendações (D1 a D6) depois de liberar o "Máx. barras" no MT5 da Clear.

| Fase | O que ficou pronto | Onde |
|---|---|---|
| F0 | 1 e 5 min re-medidos: agora vão até 16/11/2021. Cenário A aprovado e trancado | `b3/config/splits_b3.json`, `research/b3/data_quality.json` |
| F1 | WIN e WDO no executor, com registro, régua e critérios próprios. Calendário histórico (horários inferidos das barras, feriados inferidos até 2025) e dias de rolagem achados pela série ajustada (30 no WIN, 60 no WDO). O stop paga 1 tick a mais | `b3/b3_data.py`, `b3/markets.py`, `b3/proxy_research.py`, `b3/config/gates_b3.json`, `scope_b3.json` |
| F2 | Adaptador que roda o código das estratégias do Freqtrade no motor da B3: 126 portáveis, 12 de fora. Fidelidade em BTC contra os backtests do próprio Freqtrade: 4 estratégias com 100% das operações iguais e 2 com 96% a 99,9% | `b3/freqtrade_adapter.py`, `b3/ftshim/`, `research/b3/adapter_fidelity.json` |
| F3 | Triagem registrada antes de qualquer leitura; depois, Sharpe deflacionado e PBO para as 10 melhores e uma única leitura da validação para quem passar | `b3/config/crypto_screen_b3.json`, `research/b3/crypto_screen.json`, `screen_followup.json` |
| F4 | Menu com **Cripto**, **B3: WIN e WDO** e **Substitutos**, cada um com Início, Ranking, Operações, Comparar, relatório da estratégia e gráfico de candles com as operações. Abas no topo trocam de universo | `lab/universes.py`, `lab/dashboard_assets/universes.js` |
| F5 | Agentes apontados para WIN e WDO, com os mesmos limites (3 regras por semana; parada após 15 sem validação ou em 16/12). Programa dos substitutos encerrado | `b3/config/b3_program.json`, `b3/proxy_pipeline.py` |
| F6 | Ainda não: nenhuma regra passou na validação, e o robô ao vivo ainda não faz venda a descoberto nem stop móvel | — |

**Primeiras leituras na B3 (exploração):** as 11 regras dos substitutos (P-001 a P-011) foram lidas no WIN e no WDO, 20 leituras. Só o P-004 passou, no WIN, e reprovou na leitura única da validação: −1,13% contra uma régua de 2,9%. O WDO perdeu em quase todas: o tick de meio ponto custa caro, e a ida e volta sai a 0,0235% contra 0,011% no WIN.

**Para ver no portal:** pare e rode de novo `python -m lab.dashboard serve`, e abra a seção "B3: WIN e WDO" no menu.

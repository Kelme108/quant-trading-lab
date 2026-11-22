# Plano B3: mini-índice (WIN) e mini-dólar (WDO) no laboratório

Escrito em 12/11/2026, a pedido do dono: "integrar mini índice e mini dólar, ver tudo que já foi pesquisado e coletado, o que é necessário, e aprimorar ao máximo".

Base: o código atual de `live/` e `lab/`, o plano original [prompt-execucao-tempo-real.md](prompt-execucao-tempo-real.md) (Etapas 0 a 5), [live/DECISIONS.md](../live/DECISIONS.md), as duas revisões de 12/11 em `research/reviews/` e uma pesquisa nova sobre a B3 (fontes na seção 11).

**Nada aqui libera dinheiro real.** Este plano leva WIN e WDO até a conta demo com o mesmo rigor do laboratório de cripto. A operação real continua sendo a Etapa 5, bloqueada, que só o dono libera.

---

## 0. Andamento

**12/11/2026: código da F1 e da F2 pronto** (o dono disse "pode começar; a conta XP eu envio depois").

| Item do plano | Estado | Onde |
|---|---|---|
| F2.1 Calendário | pronto | [b3/calendar.py](../b3/calendar.py). Feriados de 2026 transcritos do OC 041/2026-VNC em [b3/config/holidays.json](../b3/config/holidays.json). Horários por data em [b3/config/sessions.json](../b3/config/sessions.json): WIN das 9h às 18h25 pelo OC 005/2026-PRE; WDO até 18h30 **só pela imprensa, a confirmar**. Ano sem lista oficial gera erro, em vez de chute |
| F2.2 Contratos | pronto | [b3/contracts.py](../b3/contracts.py). Achado: no dia do vencimento, o contrato do WIN que vence para às 17h, então a rolagem padrão é 2 pregões antes |
| F2.3 Custos | pronto, **hipótese** | [b3/costs.py](../b3/costs.py); valores da seção 2.1 até a medição na F3.4 |
| F2.4 Backtester | pronto | [b3/backtest.py](../b3/backtest.py); compra e venda; mesmas regras do `PaperBroker` |
| F2.5 Paridade | **passou** | [tests/b3/test_b3_parity.py](../tests/b3/test_b3_parity.py): engine real e backtester com fills idênticos em 5 cenários (3 aleatórios, zeragem, travas de perda com limite de entradas) |
| F2.6 / F2.7 Contrato da estratégia e checagens | pronto | [b3/strategy.py](../b3/strategy.py), [b3/strategy_check.py](../b3/strategy_check.py), [b3/checks.py](../b3/checks.py): causalidade e paridade entre a janela do live e o histórico completo |
| Métricas em R$ | pronto | [b3/metrics.py](../b3/metrics.py), com estimativa de IR à parte |
| F1.1 a F1.5 Código de dados | pronto, **sem dados** | [b3/data/](../b3/data/): lista de símbolos, profundidade, download de barras e ticks, conversão de fuso, checagens, série contínua |
| F2.8 Gates e splits B3 | aguardando | Depende da profundidade medida na F1.2 e do sim do dono |
| F2.9 Registro | aguardando | Junto com a F2.8 |
| F3 Venda no live | aguardando | Decisão 2 da seção 10 |

Testes: `python -m pytest tests/b3 -q` dá 59 aprovados; `tests/live` continua com 105.

### Quando a conta demo da XP chegar (F1.1 e F1.2)

1. Abra o MT5 e faça login no **servidor demo da XP**. Crie o `live/.env` com `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` e `MT5_PATH`. Esse arquivo não entra no git, e as credenciais nunca vão para o chat.
2. Em Ferramentas → Opções → Gráficos, aumente o "Máximo de barras no gráfico" para o maior valor e reinicie o MT5. Esse limite corta o histórico que o Python consegue ler.
3. Liste os símbolos (só leitura):
   `live/.venv/Scripts/python.exe -m b3.data.mt5_history symbols`
4. Meça a profundidade do histórico, usando os nomes que aparecerem no passo 3. Mantenha as **aspas simples**: no PowerShell, `$N` sem aspas é lido como variável e some.
   `live/.venv/Scripts/python.exe -m b3.data.mt5_history depth --symbols 'WIN$N' 'WDO$N' WINZ26 WDOZ26 --report research/b3/data-depth-<data>.json`
5. Me mande a saída. Com ela eu proponho os splits B3 (seção 7) e a regra de rolagem, para sua aprovação, **antes** de baixar e olhar qualquer retorno.

---

## 1. Resumo executivo

1. **Por que a B3.** Em cripto spot, a ida e volta custa 0,30%, e nenhuma regra frequente passou disso. No WIN, a ida e volta estimada fica entre **0,007% e 0,015%** do valor do contrato. Medido contra o quanto o mercado anda num dia, o custo é de 6 a 14 vezes menor que no cripto do lab. Além disso, a venda é natural e o pregão tem abertura e fechamento de verdade, que é a condição em que a literatura acha momentum intraday.
2. **O que não muda.** Custo baixo não cria vantagem. O WIN é o mercado do estudo em que 97% dos day traders persistentes perderam dinheiro, e tem muito algoritmo. A vantagem tem que vir de um mecanismo, com hipótese registrada antes e validação lida uma vez.
3. **Bloqueio número 1: a conta.** A conta demo atual (MetaQuotes-Demo) **não tem WIN nem WDO**. Isso já está registrado em `live/DECISIONS.md`: 12.197 símbolos, nenhum da B3, conta hedging, moeda USD. É preciso uma conta demo MT5 de **corretora brasileira** (Clear, XP, Rico, Modal ou outra).
4. **O que já está pronto.** O motor de execução (`live/`) já tem engine, risco, kill switch, journal, reconciliação, adaptador MT5 e broker simulado. São 105 testes passando hoje. O modelo de fill do `PaperBroker` já foi desenhado para ser o mesmo do backtester da B3.
5. **O que falta.**
   - Dados históricos da B3.
   - Um backtester de futuros (o Freqtrade não cobre a B3).
   - Calendário, vencimentos e custos da B3.
   - Suporte a venda a descoberto.
   - Protocolo e gates em reais.
   - Agentes ensinados a pesquisar a B3.
   - Os ajustes no painel.
6. **Ordem proposta.** F0 decisões e conta → F1 dados → F2 motor de pesquisa → F3 venda e smoke na demo → F4 pesquisa com hipóteses → F5 forward na demo → F6 piloto real (bloqueado). F1 e F2 podem andar em paralelo: boa parte do código não depende da conta.
7. **Uma regra que segui de propósito: não olhei nenhum retorno histórico da B3.** Os dados da B3 ainda estão limpos para o lab. Os cortes de exploração e validação precisam ser fixados antes de qualquer pessoa ou agente olhar para eles.

---

## 2. Por que a B3 muda a conta

### 2.1 Custo por operação (estimativas, a medir na F1 e na F3)

Premissas: WIN perto de 172 mil pontos (ponto = R$ 0,20, então o contrato vale cerca de R$ 34 mil; tick = 5 pontos = R$ 1,00). WDO perto de 5.600 pontos (ponto = R$ 10, então o contrato vale cerca de R$ 56 mil; tick = 0,5 ponto = R$ 5,00). Corretagem zero, que é comum em minicontratos.

| Ativo | Cenário | Taxas B3 (ida e volta) | Derrapagem | Custo total por contrato | % do valor | Em pontos |
|---|---|--:|--:|--:|--:|--:|
| WIN | otimista | R$ 0,50 | 0 | R$ 0,50 | 0,0015% | 2,5 |
| WIN | base | R$ 0,50 | 1 tick por lado | R$ 2,50 | 0,0073% | 12,5 |
| WIN | conservador | R$ 1,00 | 2 ticks por lado | R$ 5,00 | 0,0145% | 25 |
| WIN | estresse | R$ 1,00 | 4 ticks por lado | R$ 9,00 | 0,026% | 45 |
| WDO | base | ~R$ 2 (a confirmar) | 1 tick por lado | ~R$ 12 | ~0,021% | ~1,2 |
| WDO | conservador | ~R$ 3 | 2 ticks por lado | ~R$ 23 | ~0,041% | ~2,3 |
| Cripto spot do lab | base | 0,15% | incluída | — | **0,30%** | — |

- **Taxa do WIN:** a Genial estima cerca de R$ 0,50 de ida e volta por contrato na primeira faixa de volume. A B3 cobra emolumentos e taxa de registro por contrato, com desconto para day trade, e os valores já incluem PIS/COFINS e ISS.
- **Taxa do WDO:** não consegui ler a tabela oficial (as páginas bloquearam o acesso automático). Por isso o valor do WDO está marcado como "a confirmar".
- **Valor final:** sai do extrato de deals da conta demo e do PDF de tarifação da B3 (F3.4).

**Custo comparado ao tamanho do movimento.** A volatilidade diária típica é de cerca de 1,2% no Ibovespa, 0,8% no dólar e 3% a 4% no cripto do lab (valores aproximados, a medir na F1). Nessa medida, o custo base do WIN é cerca de 0,6% do movimento de um dia, o do WDO cerca de 2,7%, e o do cripto spot cerca de 8% a 9%.

**O WIN é o melhor dos dois.** No WDO, um único tick já vale cerca de 0,009% do contrato, então a derrapagem pesa mais.

### 2.2 Diferenças estruturais que importam para a pesquisa

| Ponto | Cripto spot do lab | WIN / WDO |
|---|---|---|
| Pregão | 24/7, sem abertura nem fechamento | Abertura às 9h e fechamento às 18h25 (WIN) ou 18h30 (WDO), com a informação da noite acumulada no gap |
| Venda a descoberto | Proibida (spot) | Natural, sem aluguel |
| Custo | 0,30% de ida e volta | 0,007% a 0,04% |
| Instrumento | 9 pares, muito correlacionados entre si | 2 contratos de mercados diferentes (índice e câmbio) |
| Vencimento | Não tem | WIN nos meses pares, WDO todo mês: é preciso rolar e montar uma série contínua |
| Eventos | Poucos e espalhados | Agenda fixa: abertura do mercado à vista, abertura dos EUA, IPCA, CPI e payroll americanos, FOMC, Copom, janelas da PTAX |
| Imposto | Ganho de capital | 20% sobre o lucro líquido mensal de day trade, mais 1% retido na fonte sobre o lucro do dia (DARF 6015) |
| Alavancagem | Nenhuma | Alta: margem de day trade de dezenas a centenas de reais por contrato |

**O ponto mais importante para a pesquisa:** o lab tentou rompimento da faixa de abertura e "noise area" em cripto (H-052, H-069, H-092) e tudo virou ruído. Mas cripto não tem abertura de verdade. Os estudos que documentam esses efeitos são todos em mercados com pregão:
- Gao et al. 2018 e Li, Sakkas e Urquhart 2022 (16 mercados desenvolvidos);
- Baltussen et al. 2021 (dezenas de futuros);
- Zarattini et al. 2024 (SPY e ações americanas).

A B3 é um mercado com pregão. **Nenhum desses estudos inclui o Ibovespa**, então a B3 é um teste limpo, mas também sem garantia.

---

## 3. O que já existe no projeto

| Parte | Estado | Onde | Observação |
|---|---|---|---|
| Engine (candle fechado → sinal → risco → ordem → journal) | pronto | `live/core/engine.py` | Idempotente, reconcilia com a corretora, modo seguro, trava por perda, zeragem no fim do dia |
| RiskManager | pronto, **só compra** | `live/core/risk.py` | Vetos testados um a um; `long_only=True`; o stop só é aceito abaixo do preço |
| Calendário B3 | parcial | `live/core/clock.py` | Fases do pregão por horário fixo; **sem feriados reais, sem histórico de horários, sem meio pregão** |
| Adaptador MT5 | pronto, **só compra** | `live/brokers/mt5.py` | `order_check` antes do envio, stop no servidor, fecha por ticket, nunca abre venda |
| PaperBroker | pronto | `live/brokers/paper.py` | Fill no próximo open com derrapagem em ticks e custo por contrato; o stop é checado a cada barra |
| Kill switch, guarda de dinheiro real, journal | prontos | `live/core/` | Dinheiro real exige 4 condições independentes |
| Ferramenta de inspeção da conta (só leitura) | pronta | `live/tools/probe_mt5.py` | Lista WIN e WDO e o tipo de conta |
| Ambiente | pronto | `live/.venv` | MetaTrader5 5.0.6231 no Python 3.14; 105 testes em `tests/live` passando hoje |
| Configuração de exemplo para a B3 | **desatualizada** | `live/config/live.example.json` | Lista `WDOX26`, que venceu em 03/11/2026. Os símbolos precisam vir de um resolvedor de vencimento, não do arquivo |
| Conta B3 | **não existe** | `live/DECISIONS.md` | MetaQuotes-Demo não tem B3 |
| Dados históricos B3 | **não existem** | — | — |
| Backtester de futuros | **não existe** | — | O Freqtrade não cobre a B3 |
| Custos B3 | **não existem** | `lab/costs.py` é só cripto | — |
| Splits, gates e holdout B3 | **não existem** | `lab/config/` | — |
| Partes do lab reaproveitáveis | prontas | `lab/stats.py` (Sharpe deflacionado, PBO, bootstrap por blocos), `lab/causality.py` (testes anti-antecipação genéricos), `lab/walkforward.py`, `lab/bootstrap.py`, `lab/registry.py` | Nenhuma depende do Freqtrade |
| Agentes | só cripto | `.claude/agents/*.md` | O developer escreve estratégias Freqtrade; o scout e o research usam a guidance de cripto |

---

## 4. Fatos de mercado que o código precisa respeitar

Regra do plano original, mantida aqui: **nada de calendário ou especificação escrito de memória no código.** As especificações são lidas do servidor (`symbol_info`) e conferidas contra a especificação da B3. Datas de vencimento e feriados vêm do calendário oficial, com testes de borda.

| Item | WIN | WDO | Fonte / estado |
|---|---|---|---|
| Valor do ponto | R$ 0,20 | R$ 10,00 | B3; Toro |
| Tick | 5 pontos = R$ 1,00 | 0,5 ponto = R$ 5,00 | Toro (WDO); ler do servidor |
| Tamanho | 20% do índice cheio (IND) | US$ 10 mil (20% do dólar cheio, DOL) | B3; Toro |
| Vencimento | Meses pares (G, J, M, Q, V, Z), na quarta-feira mais próxima do dia 15 | Todo mês, no 1º dia útil (F a Z) | Confirmar na especificação da B3: uma página da B3 mistura as duas regras |
| Contrato vigente hoje | WINZ26 (vence em 16/12/2026) | WDOZ26 (vence em 01/12/2026). O WDOX26 do exemplo já venceu | Resolvedor de vencimento (F2.2) |
| Horário (desde 03/11/2026) | 9h às 18h25 | 9h às 18h30 | BP Money, Suno; confirmar no Ofício Circular da B3 |
| Mudança de horário | **Duas vezes por ano**, acompanhando o horário de verão dos EUA | Idem | O backtest precisa de uma **tabela de horários por data**, não de um horário fixo |
| Feriados 2026 | Calendário no OC 054/2025-VNC, com errata no OC 041/2026-VNC | | Arquivo de feriados por ano com a fonte citada |
| Meio pregão | Quarta-feira de Cinzas e outros, conforme o OC do ano | | Idem |
| Leilão de abertura | Sim | Sim | Barras do leilão marcadas, nunca usadas para entrar |
| Margem day trade | Definida pela corretora | Definida pela corretora | Registrar a da conta escolhida |
| Imposto | 20% do lucro líquido mensal de day trade e 1% retido sobre o lucro do dia, DARF 6015; prejuízo compensa só dentro do day trade | Idem | Blogs especializados; confirmar com a Receita ou com um contador. O sistema só exporta o histórico |

**Agenda fixa de eventos** (as horas em BRT mudam com o horário de verão dos EUA; guardar a tabela por data):
- 9h: abertura dos futuros.
- 10h: abertura do mercado à vista.
- 10h30 ou 11h30: abertura de Nova York.
- 9h: divulgação do IPCA.
- 9h30 ou 10h30: CPI e payroll americanos.
- 15h ou 16h: decisão do FOMC.
- Depois das 18h30: Copom (efeito no dia seguinte).
- 10h, 11h, 12h e 13h: as quatro janelas da PTAX. A PTAX liquida o WDO.

---

## 5. Arquitetura proposta

```text
            ┌──────────── pesquisa (offline, determinística) ─────────────┐
 MT5 demo ─▶│ b3/data: download → checagens → séries por contrato         │
 (barras,   │ b3/calendar + b3/contracts: feriados, horários, vencimentos │
  ticks)    │ b3/costs: R$ por contrato e ticks de derrapagem, 4 cenários │
            │ b3/backtest: mesmas regras de fill do PaperBroker           │
            │   └─ roda a MESMA estratégia que vai para o live            │
            │ lab: stats / causality / walkforward / registry / gates B3  │
            └──────────────────────────────┬──────────────────────────────┘
                                           │ estratégia congelada (hash)
            ┌──────────────── execução (Windows, MT5) ────────────────────┐
            │ live/engine → risk (compra e venda) → MT5 adapter → journal │
            │ calendário B3 real, resolvedor de vencimento, kill switch   │
            └──────────────────────────────┬──────────────────────────────┘
                                           ▼
                           painel (somente leitura): pista B3
```

Princípios de desenho:

1. **Uma estratégia, um objeto.** A classe da estratégia já segue o `Strategy` do engine (`timeframe_min`, `warmup`, `signal(bars, position)`). O backtester B3 chama exatamente o mesmo `signal`, e um teste de paridade compara um pregão inteiro do engine com `PaperBroker` contra o backtester. Proibido reimplementar a regra.
2. **Indicadores vetorizados e causais.** Cada estratégia expõe `indicators(df)`, que o backtest usa por velocidade, e `signal()` lê a última linha. O `lab/causality.py` (invariância de prefixo e corrupção do futuro) roda em toda estratégia, como gate.
3. **Preço de execução sem ajuste, indicador com série ajustada.** Cada pregão usa um só contrato, o vigente pela regra de rolagem fixada antes. Indicadores que atravessam dias (média de 14 dias, por exemplo) usam uma série contínua com ajuste de rolagem, para não ver o salto entre vencimentos como movimento. Como nenhuma posição atravessa o dia, o resultado nunca depende do ajuste.
4. **Pessimismo dentro da barra.** Se uma barra toca o stop e o alvo, conta o stop. Se ela abre além do stop (gap), o fill é na abertura. A zeragem é no primeiro preço a partir do horário de zeragem da tabela do dia.
5. **Tudo em reais por contrato.** Os gates em R$ substituem os gates em USDT. O drawdown é medido contra um capital hipotético por contrato, que o dono define (F0).

---

## 6. Fases

Cada fase termina com os arquivos alterados, os testes e resultados, os problemas encontrados e as decisões pendentes. Ela **para à espera do "sim" do dono** antes de seguir, como manda o plano original. Commits só depois do sim.

### F0. Decisões e conta (dono)
- **F0.1 Abrir conta numa corretora brasileira com MT5 e pedir o servidor demo da B3.**
  - **Clear:** tem servidor "CLEAR DEMO". A demo custa R$ 9,90 por mês, ou é grátis com 1 minicontrato operado no mês e RLP ativo; confirmar as condições.
  - **XP e Rico:** usam MT5 na B3; um fórum de 2020 lista também Modal e Terra.
  - **Genial:** usuários relatam que não oferece demo.
  - **O que conferir:** se a conta é netting ou hedging (um blog afirma que o padrão nas corretoras B3 é hedging, e o adaptador já trata os dois); a profundidade do histórico; e quanto custa o MT5 depois do período demo.
- **F0.2 Respostas que só o dono dá:** a lista da seção 10.
- **F0.3 Máquina:** o MT5 com Python só roda no Windows. Na demo, o PC ligado das 8h45 às 18h45 basta. Para a F5 em diante, um VPS Windows. A VM Ubuntu do runbook não serve para o MT5.

### F1. Dados (começa assim que a conta existir; o código pode ser feito antes)
| Item | Entrega | Teste |
|---|---|---|
| F1.1 Inspeção da conta | `probe_mt5.py` estendido: lista WIN*, WDO*, IND*, DOL*, as séries contínuas (`WIN$`, `WIN$N` e variações da corretora) e os contratos vencidos ainda disponíveis | Saída registrada em `live/DECISIONS.md` pelo dono |
| F1.2 **Medir a profundidade do histórico** | `b3/data/depth.py`: primeira barra disponível por símbolo e timeframe (M1, M5, M15, H1, D1) e primeiro tick com marcação de agressor (`COPY_TICKS_ALL`, `TICK_FLAG_BUY`/`SELL`) | Relatório `research/b3/data-depth-<data>.md`. **Decide os splits** |
| F1.3 Download | `b3/data/download.py` grava `user_data/data/b3/<símbolo>-<tf>.feather`, com manifesto: corretora, servidor, data da coleta, fuso do servidor, hash | Testes com MT5 falso (já existe `tests/live/fake_mt5.py`) |
| F1.4 Checagens | `b3/data/quality.py`: lacunas **dentro** do pregão, barras de leilão, saltos na rolagem, barras fora da tabela de horários, volume zero | Casos sintéticos para cada defeito |
| F1.5 Séries contínuas | Por contrato (preço cru) e ajustada (para indicadores), com a regra de rolagem fixada antes (por exemplo: WIN rola N pregões antes do vencimento; WDO rola no penúltimo pregão do mês). Comparar com a série `$N` da corretora | Rolagem em feriado e em véspera de vencimento |
| F1.6 Plano B de dados | Se o M5 da corretora tiver menos de cerca de 5 anos: avaliar comprar a base histórica da Nelogica (tick a tick de WINFUT e WDOFUT desde 2012; preço não publicado). O FTP gratuito da B3 foi desligado em 2020 | Decisão do dono, com custo |

### F2. Motor de pesquisa B3 (não depende da conta; pode começar já)
| Item | Entrega | Teste |
|---|---|---|
| F2.1 Calendário | `b3/calendar.py` com feriados por ano (arquivo de dados com o OC citado), meio pregão e **tabela de horários por intervalo de datas** (abertura, leilão, fim de entradas, zeragem, fechamento). Substitui o `SessionConfig` fixo do live, que passa a ler a mesma tabela | Bordas: troca de horário em março e novembro, Cinzas, véspera de Natal |
| F2.2 Contratos | `b3/contracts.py`: regra de vencimento do WIN e do WDO, código do contrato vigente e data de rolagem, feriados respeitados | As datas reais de 2025 e 2026 conferidas uma a uma contra a B3 |
| F2.3 Custos | `b3/costs.py`: 4 cenários (otimista, base, conservador, estresse) em R$ por contrato por lado, mais derrapagem em ticks, com fonte e data. Os valores iniciais são os da seção 2.1, **marcados como hipótese** até a F3.4 medir | Ida e volta calculada bate com a tabela |
| F2.4 Backtester | `b3/backtest.py`: laço por barra; fill no próximo open com derrapagem; stop pessimista dentro da barra; zeragem pela tabela; máximo de operações por dia; compra e venda; saída como lista de trades no formato que `lab/stats` e `lab/bootstrap` já leem | Casos feitos à mão: gap no stop, stop e alvo na mesma barra, zeragem, leilão, rolagem |
| F2.5 **Paridade** | `tests/b3/test_parity.py`: o mesmo pregão no engine com `PaperBroker` e no backtester dá as mesmas ordens e os mesmos fills | Obrigatório, como no plano original |
| F2.6 Contrato da estratégia | `b3/strategies/` com uma estratégia base de exemplo; checagem estática própria, que reaproveita a lógica de `lab/strategy_check.py`: só pandas, numpy e math; sem `shift(-n)`; sem arquivo nem rede; `warmup` declarado | Estratégia ruim de propósito é rejeitada |
| F2.7 Causalidade | `lab/causality.py` aplicado a `indicators()` de toda estratégia B3 | Já testado no lab; só a ligação é nova |
| F2.8 Gates e protocolo | `lab/config/gates_b3.json`, `splits_b3.json`, `holdout_b3.json` (seção 7). **Só depois da F1.2 e do sim do dono** | Testes iguais aos de `tests/test_lab_gates.py` |
| F2.9 Registro | O registry já tem `pair`: usar `B3:WIN` e `B3:WDO`, e família e hipótese com prefixo próprio (por exemplo `B-001`), para não misturar a contagem de múltiplos testes com o cripto | Migração testada sem tocar nos dados de cripto |

### F3. Venda a descoberto e smoke test na demo B3
| Item | Entrega | Teste |
|---|---|---|
| F3.1 Modelos | `Position` com lado (`long` ou `short`), `Signal` com `enter_long`, `enter_short` e `exit` | Os testes atuais continuam verdes |
| F3.2 Risco | `long_only` vira opção por mercado; o stop é checado do lado certo (acima do preço na venda); proibido virar a mão numa ordem só (zerar e depois entrar) | Um veto novo por regra |
| F3.3 Adaptador MT5 | Venda com `sl` acima. Em conta **netting**, ordem oposta com volume exato; em **hedging**, fechar por ticket e nunca manter compra e venda ao mesmo tempo. Reconciliação com volume com sinal | Testes com MT5 falso para os dois modos |
| F3.4 **Smoke na demo B3** | 1 WIN e depois 1 WDO, com o dono acompanhando: entrada com stop, posição conferida, saída, journal. Depois os testes de falha (matar o processo com posição aberta, rede caída, volume inválido, kill switch). **Medir as taxas reais e a derrapagem no histórico de deals** | Relatório `research/b3/smoke-<data>.md`; os custos medidos substituem as hipóteses da F2.3 |
| F3.5 Fuso do servidor | `--check` estima o fuso; o valor vai para a configuração | Já existe; confirmar com mercado aberto |

### F4. Pesquisa: hipóteses B3 pelo protocolo
- Arquivos novos para os agentes:
  - `research/knowledge/evidence-b3.md`, com a evidência da seção 8;
  - uma seção B3 em `research/guidance.md`;
  - uma fila de fontes da B3;
  - um agente developer B3, que escreve estratégias `b3/strategies/` em vez de Freqtrade.
- Primeiro, uma **baseline simples registrada antes de rodar**, como pede o plano original. Depois as hipóteses da seção 8, uma família por vez, com variantes limitadas e penalidade de múltiplos testes.
- A exploração roda nos dois contratos. A validação é lida **uma vez**, com aprovação do dono registrada (`research/tools/approve.py`, que já existe).

### F5. Forward na conta demo
- Só uma estratégia que passou na validação, com hash congelado.
- Mínimo de **60 operações fechadas e 4 semanas**, com os mesmos critérios de `lab/config/dryrun.json`: fator de lucro, expectativa, drawdown, concentração e custo observado contra o conservador.
- Regra de inatividade **em pregões**, não em dias corridos: fim de semana e feriado não contam.
- Relatório semanal: as operações da demo contra o replay do backtest no mesmo período, derrapagem medida em ticks, rejeições e incidentes.
- O painel ganha uma pista B3 somente leitura, com dados do journal.

### F6. Piloto real (bloqueado)
Segue o [checklist-operacao-real.md](checklist-operacao-real.md) e a Etapa 5 do plano original:
- 1 contrato;
- critério de parada escrito antes;
- VPS Windows;
- as 4 travas de dinheiro real em `live/core/realguard.py`.

Nenhum código desta fase é escrito sem autorização explícita.

---

## 7. Protocolo B3 (a aprovar antes de qualquer teste)

| Item | Proposta | Por quê |
|---|---|---|
| Splits | Depende da F1.2. Exemplo com M5 desde 2016: **exploração** do início até 31/12/2022, **validação** de 01/01/2023 a 31/12/2025, **teste final** a partir de 01/01/2026, trancado | A validação cobre anos recentes com custos parecidos com os de hoje; o teste final é o período mais novo e nunca analisado |
| Holdout prospectivo | Do congelamento em diante, na demo | Igual ao cripto |
| Capital hipotético | R$ 10 mil por contrato (proposta) | Base do drawdown e do retorno |
| Lucro mínimo | Positivo nos cenários base **e** conservador, acima de um piso em R$ por contrato e por ano, que sobe a cada variante da família | Mesma lógica de `gates.json` |
| Sem dependência do melhor trade | Lucro sem o melhor trade > 0 | Igual |
| Drawdown | Até 25% do capital hipotético, no base e no conservador | Igual |
| Amostra mínima | 30 operações por split por contrato; meta de **200 ou mais por ano** | O dono quer muitas operações |
| Amplitude | A regra declara antes o contrato principal. No outro contrato, o resultado não pode ser negativo no base. Walk-forward por ano: positivo em pelo menos 60% dos anos da exploração | Com só 2 contratos, a regra "6 de 9 pares" não serve |
| Múltiplos testes | Sharpe deflacionado e PBO quando houver grade; teto de variantes por família | Já existe em `lab/stats.py` |
| Imposto | Relatado (20% sobre o lucro mensal de day trade), não usado como gate | O imposto depende do resto da vida fiscal do dono |
| Dados vistos | `data_visible_at_proposal` diz "B3" e a janela | Igual |

---

## 8. Agenda de pesquisa: o que testar primeiro na B3

Cada hipótese declara quatro coisas:
- o mecanismo;
- **quem está do outro lado do trade e por que perde ou aceita perder**;
- a frequência esperada por ano;
- o movimento bruto esperado contra o custo da seção 2.1.

| # | Mecanismo | Evidência | Regra (esboço, a fixar na proposta) | Frequência | Do outro lado |
|---|---|---|---|---|---|
| B-1 | **Momentum intraday da sessão**: o retorno do início do dia prevê o da última meia hora ou hora | Gao, Han, Li e Zhou (JFE 2018, S&P 500); Li, Sakkas e Urquhart (JFM 2022, 16 mercados desenvolvidos; mais forte com pouca liquidez, muita volatilidade e notícia); Baltussen et al. (JFE 2021, dezenas de futuros; ligado ao hedge de gama de opções e de ETFs alavancados); Shen et al. 2022 em bitcoin, já no evidence.md. Nenhum inclui o Brasil | Sinal = retorno do ajuste anterior até 10h30 (ou do dia até a penúltima meia hora); entrar na última janela no mesmo sentido; zerar no fechamento. Compra **e venda** | ~250 por ano por contrato | Quem rebalanceia no fim do dia por obrigação (hedge, fundos) |
| B-2 | **"Noise area"**: só operar quando o preço sai da faixa normal de movimento a partir da abertura | Zarattini, Aziz e Barbon 2024 (SPY 2007-2024, Sharpe de 1,33 líquido, segundo os autores; 4º lugar no Quantpedia Awards 2025) | Faixa = média de 14 dias do movimento absoluto desde a abertura, por horário; entrar no rompimento; stop móvel; zerar no fechamento | 1 a 3 por dia | Desequilíbrio de oferta e demanda que persiste no dia |
| B-3 | **Rompimento da faixa de abertura só em dia "em jogo"**: volume relativo alto ou gap grande | Zarattini, Barbon e Aziz 2024 (ações americanas 2016-2023; o filtro de dia "em jogo" é o que sobrevive ao custo); o placar do lab mostra que o rompimento genérico em cripto é ruído | Faixa dos primeiros 5 a 15 minutos; só entra se o volume dessa janela estiver acima de um múltiplo da média, fixado antes; alvo aberto e zeragem no fechamento | 0,5 a 1 por dia | Notícia da noite ainda não precificada |
| B-4 | **Dias de evento**: CPI, payroll, FOMC, IPCA, dia seguinte ao Copom | Guidance do lab de 10/11 (datas como constantes, calendário oficial como fonte); Gao et al.: o efeito é mais forte em dias de notícia macro | Dois usos, cada um com hipótese própria: (a) filtro, que fica fora ou só opera nesses dias; (b) rompimento da barra do evento | ~40 dias por ano | Quem estava posicionado antes da notícia |
| B-5 | **Abertura do mercado à vista (10h)** e gap das 9h | Fraca: só mecanismo (fluxo do à vista e dos estrangeiros) | Continuação e reversão do gap são **duas hipóteses diferentes** | 1 por dia | — |
| B-6 | **WDO: janelas da PTAX e fim de mês** | Só prática de mercado (a PTAX liquida o DOL e o WDO; disputa no fim do mês) | Movimento nas janelas das 10h às 13h e no último pregão do mês | ~12 a 250 por ano | Exportadores, importadores e mesas de derivativos |
| B-7 | **Fluxo agressor (delta) nos ticks** | Em cripto, reversão depois de barra empurrada pelo fluxo (arXiv 2608.21888). Ticks do MT5 da B3 trazem a marcação de compra e venda (`COPY_TICKS_ALL`) | Depende da profundidade de ticks da F1.2 | Alta | Agressor desinformado |

Também está nos planos, sem ordem:
- índice e dólar juntos (o dólar puxa o índice?);
- um filtro de regime por volatilidade (o VIX Brasil da B3).

**O que não fazer:**
- portar as regras de cripto quase aprovadas (H-104 e outras) "porque quase passaram": isso é seleção pelos dados;
- usar ICT/SMC, que o lab já mostrou que é ruído;
- confiar em resultado anunciado de robô do MQL5 Market ou de curso.

---

## 9. Riscos e como o plano lida com eles

| Risco | Tratamento |
|---|---|
| Histórico curto na corretora | A F1.2 mede antes de fixar os splits; plano B na F1.6 |
| Série contínua errada (salto de rolagem) | Execução no contrato vigente; indicadores na série ajustada; testes de rolagem |
| Horário que muda duas vezes por ano | Tabela de horários por data, usada no backtest e no live |
| Alavancagem | 1 contrato por padrão; perda diária e semanal já travam o dia e a semana (R$ 300 e R$ 900 em `live/DECISIONS.md`) |
| Venda a descoberto mal implementada | Proibido virar a mão numa ordem só; reconciliação com sinal; testes para netting e hedging |
| Diferença entre backtest e demo | Teste de paridade (F2.5) e relatório semanal contra o replay (F5) |
| Derrapagem maior que a estimada | Custos medidos na F3.4 substituem a hipótese; o cenário conservador decide junto com o base |
| Excesso de testes até "dar certo" | Penalidade por variante, Sharpe deflacionado e PBO, validação lida uma vez, prefixo próprio no registro |
| Mercado muito disputado (HFT, os 97% que perdem) | Toda hipótese diz quem está do outro lado; expectativa honesta: a maioria vai falhar |
| PC desligado no pregão | Demo no PC; VPS Windows antes do piloto |

---

## 10. Decisões do dono

| # | Decisão | Recomendação |
|---|---|---|
| 1 | Qual corretora e servidor demo MT5 da B3 | Clear (tem demo B3 documentada) ou XP; ver custo e histórico |
| 2 | **Permitir venda a descoberto em WIN e WDO** (hoje `live/DECISIONS.md` diz "somente comprado") | **Sim.** As regras da literatura usam os dois lados, e só comprado foi o que mais perdeu no lab |
| 3 | Capital hipotético por contrato, para os gates | R$ 10 mil |
| 4 | Manter os limites atuais (R$ 300 por dia, R$ 900 por semana, 2 contratos, 10 operações por dia) | Sim na demo; com até 3 operações por dia por estratégia, 10 basta |
| 5 | Comprar dados (Nelogica), se o histórico da corretora for curto | Decidir depois da F1.2 |
| 6 | Splits B3 | Aprovar depois da F1.2, antes de qualquer hipótese |
| 7 | Máquina para a F5 em diante | PC na demo; VPS Windows antes do piloto |
| 8 | Começar F1 e F2 já, sem esperar a conta, só com o código que não depende dela | Sim |

---

## 11. Fontes

**Custos, contratos, horários e impostos**
- [B3: mini-índice (WIN)](https://b3.com.br/en_us/news/what-is-mini-index-win-and-why-does-it-attract-day-trade-newcomers.htm)
- [B3: regras de cálculo de tarifas](https://b3.com.br/pt_br/produtos-e-servicos/tarifas/regras-de-calculo-para-derivativos-de-indices-moedas-commodities-e-divida-soberana/)
- [B3: tarifação V4.6 (PDF)](https://www.b3.com.br/data/files/8F/A2/65/D5/A78DF91094DCD8F9AC094EA8/Tarifacao_V4.6_PT.pdf)
- [Genial: custo real do day trade](https://www.genialinvestimentos.com.br/artigos/custo-real-day-trade/)
- [Toro: especificação do WDO](https://blog.toroinvestimentos.com.br/mini-dolar-o-que-e-como-funciona-wdo/)
- [BP Money: horários a partir de novembro](https://bpmoney.com.br/mercado/b3-muda-horarios-pregao-3-novembro-fim-horario-de-verao/)
- [Suno: fim do horário de verão nos EUA](https://www.suno.com.br/noticias/b3-2026-fim-horario-verao/)
- [B3: calendário 2026](https://www.b3.com.br/pt_br/noticias/calendario-de-negociacao-da-b3-confira-o-funcionamento-da-bolsa-em-2026.htm)
- [OC 054/2025 (feriados)](https://www.b3.com.br/data/files/C2/E3/28/AD/4FAEA9105B12E5A9AC094EA8/OC%20054-2025-VNC%20CALENDARIO%20DE%20FERIADOS%20EM%202026%20E%20FUNCIONAMENTO%20DA%20B3%20EM%2018022026%20QUARTAFEIRA%20DE%20CINZAS_PT.pdf)
- [OC 041/2026 (errata)](https://www.b3.com.br/data/files/20/57/01/AA/06A1F910ADC36BE9AC094EA8/OC%20041-2026-VNC%20ERRATA%20-%20CALENDARIO%20DE%20FERIADOS%20EM%202026_PT.pdf)
- [Awake Trader: impostos de WIN e WDO](https://www.awaketrader.com/pt/educacao/impostos-mini-indice-mini-dolar-b3-2026)

**Corretoras, MT5 e dados**
- [Clear: MetaTrader 5](https://corretora.clear.com.br/plataformas/metatrader/)
- [Fórum MQL5: demo com ativos B3](https://www.mql5.com/pt/forum/464231)
- [Traderbot: corretoras com MT5 na B3](https://blog.traderbot.com.br/corretoras-com-metatrader-5-na-b3/)
- [Asimov: baixar dados da B3 com MT5 e Python](https://hub.asimov.academy/blog/como-baixar-dados-da-b3-com-metatrader-5-e-python/)
- [MQL5: copy_ticks_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py)
- [MQL5 book: flags de tick](https://mql5.com/en/book/applications/timeseries/timeseries_ticks_mqltick)
- [Nelogica: base histórica](https://use.nelogica.com.br/pr-capt-lp-bases-historicas)

**Evidência sobre estratégias**
- [Gao et al. 2018 (cópia)](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- [Li, Sakkas e Urquhart 2022](https://centaur.reading.ac.uk/95566)
- [Baltussen et al. 2021](https://www3.nd.edu/~zda/intramom.pdf)
- [Zarattini, Aziz e Barbon 2024: noise area](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy)
- [Zarattini, Barbon e Aziz 2024: ORB em ações em jogo](https://econpapers.repec.org/RePEc:chf:rpseri:rp2498)
- [Chague, De-Losso e Giovannetti: Day Trading for a Living?](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101)
- [arXiv 2608.21888: fluxo agressor](https://arxiv.org/pdf/2608.21888)
- Revisões do lab: [revisão de day trade](../research/reviews/2026-11-12-revisao-day-trade.md) e [pesquisa de direção](../research/reviews/2026-11-12-pesquisa-direcao-day-trade.md)

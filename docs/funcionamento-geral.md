# Como o Trading Lab funciona

Este documento explica o projeto inteiro, do começo ao fim: de onde vêm as ideias, como uma estratégia é testada, quem decide o quê, e o que falta para tudo rodar sozinho numa VPS. O README diz **o que** o projeto é. Este documento diz **como ele funciona**.

Estado descrito: 06/11/2026.

---

## 1. A ideia em uma página

O projeto é uma **fábrica de estratégias com controle de qualidade**. Ela tem duas metades:

```
 PESQUISA (lab/)                                     EXECUÇÃO (Freqtrade, live/, ops/)
 ─────────────────────────────────────────           ─────────────────────────────────────

 Internet ──► Scout ──► Triagem ──► Pesquisador        Estratégia aprovada
 (papers,    (ideias)  (código,    (hipótese                │
  blogs)               regras)      formal H-NNN)           ▼
                                        │              Freeze (hash do código)
                                        ▼                   │
                                   Developer                ▼
                                   (escreve o código)   Bot dry-run (ordens simuladas,
                                        │               preço real, 24/7)
                                        ▼                   │
                         Checagem de causalidade            ▼
                         (a regra olha o futuro?)       Holdout prospectivo
                                        │               (≥ 2027-04-21, ≥ 30 trades)
                                        ▼                   │
                         Calibração + EXPLORAÇÃO            ▼
                         (backtest 2017–2024,           Testnet → piloto real
                          4 cenários de custo)          (só com sua liberação)
                                        │
                     ┌──────────────────┴─────────────────┐
                 reprovada                            passou
                     │                                    │
                 arquivada                AUTOPILOT lê a VALIDAÇÃO (política sua)
                                                          │
                                          backtest 2024–2026 (lido UMA vez)
                                                          │
                                          AUTOPILOT sobe o dry-run nos pares
                                          que passaram (dinheiro real: nunca)
```

**A regra mais importante do projeto:** os agentes de IA **escrevem textos e código**, mas **nunca decidem**. Quem aprova ou reprova são regras fixas em código (os "portões"). Desde 06/11/2026, uma **política sua** (o autopilot, seção 7) libera sozinha a leitura da validação e o dry-run. **Dinheiro real continua exclusivamente com você.**

---

## 2. Por que tanta trava? (o problema que o projeto resolve)

Quase qualquer estratégia parece ótima se você testá-la muitas vezes no mesmo histórico e ficar com a melhor. Isso se chama **overfitting**, ou sobreajuste: a regra decorou o passado em vez de aprender algo que se repete.

Exemplo: teste 50 regras aleatórias em 2017–2024. Por puro acaso, umas 2 ou 3 vão parecer lucrativas. Se você escolher essas e operar, vai perder dinheiro.

O projeto se defende de quatro formas:

1. **Dados separados por período.** Uma parte do histórico é usada para procurar (exploração). Outra parte fica guardada e é lida **uma única vez** para confirmar (validação). Depois vem o futuro de verdade (holdout prospectivo), que ninguém viu.
2. **Contagem de tentativas.** Cada regra testada entra no "N" do *Deflated Sharpe Ratio*. Quanto mais tentativas, mais exigente fica a régua. Hoje o N está acima de 60.
3. **Regra escrita antes do teste.** A hipótese é registrada com todos os números **antes** de rodar. Mudar um número depois de ver o resultado cria uma **hipótese nova**, que conta como mais uma tentativa.
4. **Portões fixos.** Os critérios de aprovação estão num arquivo protegido por hash (`lab/config/gates.json`). Nenhum agente consegue afrouxá-los.

---

## 3. Os dados

- **Pares:** BTC/USDT, ETH/USDT e BNB/USDT, spot da Binance, só comprado (sem short, sem alavancagem).
- **Timeframes:** 1h e 15m (o 15m foi habilitado em 05/11/2026). Regras "diárias" usam candles diários fechados e executam no gráfico de 1h.
- **Histórico:** de ago/2017 até hoje, em `user_data/data/binance/` (fora do git).

| Janela | Período (BTC) | Para que serve | Quem pode ler |
|---|---|---|---|
| **Exploração** | 2017-08 → 2024-07 | Procurar e calibrar | O pipeline, à vontade |
| **Validação** | 2024-07 → 2026-10 | Confirmar, **uma vez** por hipótese | Só com a sua aprovação registrada |
| **Holdout prospectivo** | 2026-10-21 → | A prova final, com dados que não existiam quando as regras foram criadas | Ninguém até 2027-04-21 |

Definição: `lab/config/splits.json` e `lab/config/holdout.json`.

---

## 4. O ciclo de pesquisa, passo a passo

Um ciclo é rodado com `python -m lab.pipeline weekly`. O nome diz "semanal", mas ele pode rodar a qualquer hora. Cada passo:

### 4.1 Scout: coletar ideias
O agente **scout** pesquisa na internet (papers, blogs quantitativos, documentação de repositórios) e escreve cada ideia como um JSON em `research/intake/`. A ideia é uma regra **em palavras**, com o **mecanismo**: quem está do outro lado do trade e por que deixaria esse dinheiro na mesa. O scout é proibido de copiar código e de reportar desempenho, e não enxerga nenhum resultado do laboratório.

### 4.2 Triagem: filtro automático (sem IA)
O código `lab/triage.py` descarta, sem gastar nada, as ideias que:
- usam um timeframe que o laboratório não roda;
- precisam de mais histórico de aquecimento do que o Freqtrade carrega (4.500 candles);
- pedem short, alavancagem, martingale ou position sizing;
- vão gerar poucos trades (abaixo de cerca de 5 por ano por par, o que não dá 30 no total);
- repetem uma regra já testada (sobreposição de palavras);
- pertencem a uma família que já gastou suas **3 variantes**.

As restantes ganham uma nota (simplicidade, parâmetros fixos, fonte acadêmica, folga de trades) e entram na fila.

### 4.3 Pesquisador: formalizar a hipótese
O agente **research** transforma a ideia numa hipótese formal (`research/proposals/H-NNN.json`), com regra completa, todos os números, mecanismo e fontes. O código valida o formato e registra a hipótese no banco (`research/lab.sqlite`) e no ledger (`research/hypothesis-ledger.md`), **antes de qualquer teste**. O pesquisador também não enxerga resultados de validação.

### 4.4 Developer: escrever o código
O agente **developer** escreve a estratégia Freqtrade (`user_data/strategies/<Familia>_H<NNN>_v1.py`) e um teste unitário. Uma checagem estática recusa:
- imports proibidos;
- acesso a arquivos ou rede;
- `shift(-n)` (olhar o futuro);
- métodos de sizing ou alavancagem.

Depois a **suíte inteira de testes** precisa passar. Se falhar, o código é posto de lado em `research/rejected/`.

### 4.5 Checagem de causalidade
Duas análises do próprio Freqtrade:
- **lookahead-analysis:** a regra usa alguma informação que só existiria no futuro?
- **recursive-analysis:** os indicadores dão o mesmo valor com mais ou menos histórico carregado?

Reprovar aqui significa que a regra está **tecnicamente errada**. Foi o que aconteceu com H-021, H-029 e H-037.

### 4.6 Calibração e exploração
1. **Calibração:** um backtest com exposição total na exploração, para obter a lista de trades. Menos de 30 trades em qualquer par descarta a hipótese.
2. **Exposição:** um bootstrap (reamostragem dos trades) escolhe **qual fração da carteira** arriscar, num grid de 5%, para o drawdown simulado ficar abaixo de 25% em 95% dos casos. Exemplo: H-024 ficou com 25%, H-020 com 10%.
3. **Exploração oficial:** um backtest com essa exposição, nos **4 cenários de custo**:

| Cenário | Custo por ida e volta |
|---|---|
| otimista | menor |
| **base** | **0,35%** |
| conservador | maior |
| stress | 0,95% |

### 4.7 Portões (o juiz)
`lab/gates.py` aplica estas regras a cada par. Para virar **candidata**, precisa passar em **todas**, nos **três** pares:

| Portão | Exigência |
|---|---|
| Lookahead / recursive | sem viés, indicadores estáveis |
| Trades mínimos | ≥ 30 no período (abaixo disso é "inconclusiva") |
| Lucro líquido | positivo nos cenários base e conservador (a régua sobe 10% a cada variante da mesma família) |
| Lucro sem o melhor trade | ainda positivo (não pode depender de um trade de sorte) |
| Drawdown máximo | ≤ 25% em todos os cenários |
| Benchmarks | comparar com caixa e com buy-and-hold (é obrigatório reportar, não é obrigatório vencer) |

As decisões possíveis são só três: `rejected`, `inconclusive` e `candidate_for_portfolio`. **Não existe "aprovado para operar real"** no laboratório.

### 4.8 Revisão e arquivo
- **Candidata:** três agentes revisores escrevem pareceres (`validator`, `quant`, `risk`). Eles comentam os números, mas não os mudam nem decidem. Depois o **autopilot** assume (seção 7).
- **Reprovada** na exploração ou na validação: vai para o **arquivo**.
  - O código vai para `user_data/strategies/_archive/`, com o hash registrado, e o teste vai para `tests/archive/`.
  - O Freqtrade não carrega essa pasta, e a suíte de testes não roda esses testes.
  - O **portal não mostra** arquivadas em nenhuma lista, ranking, curva ou comparação. Elas só entram nas contagens do funil.
  - O arquivo existe para os agentes consultarem o que já foi tentado e não funcionou (as regras e os resultados de exploração vão no contexto deles).
  - Nada é apagado, então tudo continua reproduzível.

No fim, o ciclo grava um relatório em `research/pipeline/cycle-*.md` e faz commit de tudo.

---

## 5. Da candidata ao dinheiro real

Cada degrau exige uma decisão sua, registrada com data e texto:

| Degrau | O que acontece | Quem libera | Comando |
|---|---|---|---|
| 1. Exploração | Automático no ciclo | o pipeline | `python -m lab.pipeline weekly` |
| 2. **Validação** | Backtest em 2024–2026, lido uma vez | **autopilot** (política sua) ou você | automático no ciclo; manual: `approve.py H-NNN --stage validation` e `validate_once.py` |
| 3. **Dry-run forward** | Bot com preço real e ordens simuladas, 24/7, só nos pares que passaram na validação | **autopilot** (política sua) ou você | automático no ciclo; manual: `approve.py --stage dryrun`, `forward_freeze.py` e `docker compose ... up -d` |
| 4. Holdout | Avaliação formal com dados novos | data fixa | a partir de 2027-04-21, com ≥ 30 trades fechados |
| 5. Testnet | Testa a mecânica (chaves, ordens, stop na corretora) com dinheiro fictício | você | `docker-compose.testnet.yml` |
| 6. **Real** | Piloto pequeno | **só você**, com várias travas | ver `docs/runbook-ao-vivo.md` |

**Freeze (congelamento):** antes do dry-run, o código, a configuração e o compose da estratégia são "fotografados" por SHA-256 (`research/forward/H-NNN-freeze.json`). Se qualquer byte mudar, o bot deixa de ser confiável e a checagem acusa. Ninguém pode "dar uma ajustadinha" numa estratégia que está sendo avaliada.

**Portfólio:** `lab/portfolio.py` só aceita uma estratégia que:
- é candidata em todos os pares, na exploração **e** na validação;
- é consistente entre pares (o pior par rende pelo menos 25% do lucro diário do melhor);
- tem correlação ≤ 0,7 com as estratégias que já estão no portfólio.

Os pesos são iguais e a ordem de entrada é a de registro, nunca pelo retorno.

---

## 6. Os agentes (quem são e o que podem fazer)

Todos são subagentes do Claude Code, definidos em `.claude/agents/*.md`. O código os chama em modo headless (`claude -p --agent <nome>`, em `lab/agents.py`).

| Agente | Função | Pode escrever em | Não pode ver |
|---|---|---|---|
| scout | coletar ideias na web | `research/intake/` | qualquer resultado |
| research | formalizar a hipótese | `research/proposals/` | resultados de validação, banco, relatórios |
| developer | escrever a estratégia e o teste | `user_data/strategies/`, `tests/` | — |
| validator, quant, risk | escrever pareceres | `research/experiments/*/` (um arquivo cada) | — |

**Guard** (`lab/guard.py`): depois de **cada** chamada de agente, o código compara o repositório antes e depois. Se o agente escreveu fora do permitido, ou tocou num arquivo protegido, o ciclo inteiro **para** (`GuardAbort`). Por isso, outra pessoa ou sessão escrevendo no repositório enquanto um ciclo roda derruba o ciclo: o guard não tem como saber quem escreveu.

**Orçamento** (`lab/config/budget.json`):

| Limite | Valor |
|---|---|
| Por chamada de agente | US$ 2 |
| Por ciclo | US$ 15 |
| Hipóteses novas por ciclo | até 3 |
| Variantes por família | até 3 |
| Tempo máximo por agente | 1.500 s |

Na prática um ciclo tem custado entre US$ 0,40 e US$ 1,40.

---

## 7. "Os agentes vão melhorando as estratégias sozinhos?"

**Em parte, e de propósito só em parte.**

O que **já é automático**:
- buscar ideias novas, formalizar, programar, testar, reprovar e arquivar;
- aprender com o que falhou: o pesquisador lê as regras e os resultados de **exploração** já tentados e recebe a sua direção em `research/guidance.md`;
- tentar uma **variante** de uma família promissora (até 3 por família), com o motivo da mudança declarado antes do teste.

O que **não é automático, por desenho**:
- **Ajustar parâmetros olhando o resultado.** "A H-024 perdeu em BNB, então vamos trocar 20 dias por 15" é exatamente o overfitting que o projeto existe para evitar. Uma melhoria vira uma **hipótese nova**, com ID novo, contada no N, e passa por todo o funil de novo.
- **Ler a validação.** Cada leitura gasta um recurso que não volta: depois de lido, aquele período deixa de ser "não visto" para aquela hipótese.
- **Pôr em dry-run e, principalmente, em dinheiro real.**

### O autopilot (ligado desde 06/11/2026)
A sua decisão "toda candidata pode chegar até dry-run sozinha; operação real não" está em `lab/config/autopilot.json` e é executada por `lab/autopilot.py`:

1. Uma hipótese passa na exploração nos 3 pares, e o autopilot lê a validação **uma vez**, com a exposição calibrada. Nada é ajustado.
2. Cada par que passar na validação recebe um bot de dry-run. O autopilot gera a configuração, faz o freeze por hash, commita e roda `docker compose up -d`.
3. Se nenhum par passar, a hipótese é **arquivada**, como qualquer reprovada.
4. **Travas:**
   - não sobe o bot se a ordem ficar abaixo de 10 USDT, o mínimo da Binance;
   - no máximo 12 bots de dry-run ao mesmo tempo (acima disso, ele pede a você);
   - `real_money` precisa ser `false`, ou o código recusa a política;
   - nenhum agente pode editar a política;
   - a configuração base, protegida por hash, mantém `dry_run: true`.
5. **Registro:** cada passo fica gravado como aprovação de `autopilot-policy`, com o seu nome e a data da política, então o ledger mostra o que foi automático.

Para desligar: `"enabled": false` no arquivo. Para aplicar a candidatas antigas: `python -m lab.pipeline autopilot H-NNN`.

### O que ainda dá para automatizar
1. **Alertas.** Telegram ou e-mail quando um bot novo subir.
2. **Ciclos contínuos.** Hoje eu rodo os ciclos em sequência manualmente. Na VPS isso vira um agendamento (cron).

Dinheiro real **nunca** deve ser automático. O próprio teste `tests/test_live_readiness_safety.py` impede isso.

---

## 8. A execução (onde as estratégias rodam)

### 8.1 Bots Freqtrade em dry-run (o que está ligado hoje)
- **Docker Desktop:** `docker-compose.forward.yml` (H-009 em BTC, ETH e BNB) e `docker-compose.forward.h016.yml` (H-016 em ETH).
- **Carteira:** cada bot tem a sua carteira fictícia de 100 USDT e o seu banco SQLite (`user_data/tradesv3.forward.*.sqlite`).
- **Restrições:** sem API, sem chave de corretora e sem porta exposta.
- **Relatório de execução:** `python research/tools/forward_report.py H-009`.

### 8.2 Guarda de portfólio (`ops/freqtrade_guard.py`)
Fica **fora** dos bots e roda a cada 5 minutos por cron. Ele:
- verifica se cada bot está vivo;
- soma o prejuízo do dia e o total;
- se um limite for atingido, ou se existir o arquivo `ops/state/STOP.<nome>`, **para todos os bots**.

Nada religa sozinho.

### 8.3 Camada `live/` (MetaTrader 5)
Um motor próprio para operar via MT5, pensando em mini índice e mini dólar na B3 no futuro. Ele tem:
- gestor de risco: perda diária de R$ 300, perda semanal de R$ 900, no máximo 2 contratos e 10 operações por dia;
- kill switch por arquivo `live/STOP`;
- journal, reconciliação e corretora simulada.

Hoje só foi testado numa conta demo da MetaQuotes, que **não tem B3**. Nenhuma estratégia do laboratório foi pesquisada para B3 ainda.

---

## 9. A VPS: como vai funcionar

### 9.1 O que já está preparado
Feito por outra sessão e descrito em `docs/runbook-ao-vivo.md`:
- **Máquina:** Ubuntu 24.04 no Azure (Brazil South, B2als v2: 2 vCPU e 4 GB), cerca de US$ 52/mês.
- **Script `ops/vps/bootstrap-ubuntu.sh`:** instala o Docker, deixa o relógio em UTC, liga o firewall só com SSH, ativa rotação de logs, o **cron do guarda** (a cada 5 min) e o **backup diário** dos bancos.
- Com isso, a VPS fica pronta para rodar **os bots** (dry-run, testnet e, um dia, o real) 24/7, sem depender do seu notebook.

### 9.2 O que **não** está configurado: a pesquisa automática
O bootstrap **não** liga o pipeline de pesquisa. Para os agentes trabalharem sozinhos na VPS, faltam estes passos:

| # | Passo | Por quê |
|---|---|---|
| 1 | Instalar Python 3 + dependências do lab e o **Claude Code CLI** (`claude`) | os agentes são chamadas `claude -p --agent ...` |
| 2 | **Autenticar o `claude` na VPS** com uma chave de API Anthropic com crédito, numa variável de ambiente, nunca no git | sem isso nenhum agente roda; o gasto sai dessa conta |
| 3 | Baixar o histórico de candles (1h, 15m, 1d, 4h) | os dados não vão no git |
| 4 | **Criar um repositório remoto privado** (GitHub) e dar push | hoje o repositório **não tem remote**; a VPS precisa clonar, e os resultados precisam voltar para o seu PC |
| 5 | Agendar os ciclos no cron, por exemplo de 2 em 2 horas, com `python -m lab.pipeline weekly --max-new 3` seguido de `git push` | rodar sem você |
| 6 | Alertas (Telegram) quando surgir uma candidata | você aprova pelo celular |
| 7 | Ver se a máquina aguenta | backtests de 15m com 4 cenários × 3 pares são pesados; 2 vCPU e 4 GB podem deixar o ciclo lento. Sugestão: uma VM maior só para pesquisa, ou deixar a pesquisa no PC e só os bots na VPS |
| 8 | **Uma única pessoa/processo escrevendo no repositório da VPS** | o guard derruba o ciclo se outra coisa escrever no meio |

Nenhum desses passos é difícil. Posso preparar um script `ops/vps/research-setup.sh` e o cron quando você decidir.

### 9.3 Como fica o dia a dia com a VPS
```
VPS (24/7)                                         Você (celular/PC)
──────────                                         ─────────────────
cron a cada N horas: ciclo de pesquisa ──alerta──► "H-0xx passou na exploração"
                                                     │
                                                     ▼
                                       aprova a validação (1 comando, ou pelo
                                       alerta se houver política automática)
                                                     │
validação roda ─────────────────────alerta──────► "passou / não passou"
                                                     │
                                                     ▼
                                       aprova o dry-run
                                                     │
freeze + bot sobe ◄──────────────────────────────────┘
guarda a cada 5 min (para tudo se perder demais)
backup diário dos bancos
```

---

## 10. Onde estamos (06/11/2026)

- **Hipóteses registradas:** 39 (H-001 a H-039).
- **Em dry-run:**
  - **H-009** (WeeklyBreakoutRegime) em BTC, ETH e BNB. Passou na exploração; validação ainda não lida.
  - **H-016** (momentum de 30 dias) em ETH. É a única com validação positiva, e só em ETH; o drawdown é alto.
- **Candidatas da exploração, entregues ao autopilot:**
  - H-020 (Double7ChannelDip): risco baixo, lucro pequeno.
  - H-040 (DailyNR7Breakout): de 80 a 95 trades por par, exposição de 35%.
- **Leram a validação e não passaram:** H-008, H-024 e H-025. As diárias geraram só 9 a 16 trades em 2 anos, abaixo do mínimo de 30.
- **Rodada intradiária (H-028 a H-039):** as regras de alta frequência (150 a 700 trades) perdem para o custo de 0,35% por ida e volta. A direção recomendada é a faixa de **50 a 150 trades por ano** em 1h/4h.
- **Corrigido em 06/11:** quando a exposição calibrada dá uma ordem abaixo de 10 USDT, a hipótese agora é descartada com o motivo certo ("exposição abaixo da ordem mínima"), em vez de virar um backtest sem trades.

**Até hoje nenhuma estratégia tem evidência suficiente para dinheiro real.** Isso é o resultado normal de um processo honesto: a maioria das ideias de trading não sobrevive a um teste justo.

---

## 11. Mapa de pastas

| Pasta / arquivo | O que tem |
|---|---|
| `lab/` | o motor de pesquisa: pipeline, orquestrador, portões, calibração, guard, registry |
| `lab/config/` | regras: portões, splits, holdout, custos, orçamento, portfólio |
| `.claude/agents/` | instruções de cada agente |
| `research/` | tudo o que a pesquisa produz: ledger, propostas, ideias, experimentos, relatórios de ciclo, freezes |
| `research/lab.sqlite` | banco com hipóteses, experimentos, métricas, decisões e aprovações (a fonte da verdade) |
| `research/guidance.md` | **a sua direção para os agentes**: edite aqui para mudar o foco da pesquisa |
| `user_data/strategies/` | estratégias ativas (`_archive/` guarda as reprovadas) |
| `user_data/data/` | candles (fora do git) |
| `forward/`, `docker-compose.forward*.yml` | configuração dos bots de dry-run |
| `ops/` | guarda de portfólio, bootstrap da VPS |
| `live/` | motor de execução MT5 |
| `testnet/` | ensaio na testnet da Binance |
| `tests/` | mais de 560 testes automáticos |
| `docs/` | protocolos, checklist da operação real, runbook |

---

## 12. Comandos do dia a dia

```bash
# Um ciclo de pesquisa (até 3 hipóteses novas)
python -m lab.pipeline weekly --scout-count 8 --max-new 3

# Retomar hipóteses que falharam por problema de infraestrutura
python -m lab.pipeline resume H-029 H-031

# Ver hipóteses, decisões e gasto
python -m lab.orchestrator status

# Aplicar o autopilot a candidatas antigas
python -m lab.pipeline autopilot H-020 H-040

# Liberar a validação manualmente (leitura única), se o autopilot estiver desligado
python research/tools/approve.py H-020 --stage validation
python research/tools/validate_once.py H-020 --exposure 0.1

# Colocar em dry-run
python research/tools/approve.py H-020 --stage dryrun
python research/tools/forward_freeze.py H-020
docker compose -f docker-compose.forward.h020.yml up -d

# Conferir se um bot continua íntegro
python research/tools/forward_freeze.py H-009 --check

# Relatório de execução do dry-run
python research/tools/forward_report.py H-009

# Testes
python -m unittest discover -s tests
```

---

## 13. Glossário

- **Backtest:** simular a regra no histórico, candle a candle.
- **Bootstrap:** reamostrar os trades milhares de vezes para estimar o pior caso provável.
- **Candidata:** passou em todos os portões de uma janela. Não quer dizer aprovada para operar.
- **Drawdown:** a maior queda do saldo a partir de um pico.
- **Dry-run / forward test:** o bot roda ao vivo com preço real, mas as ordens são simuladas.
- **Exposição:** a fração da carteira usada em cada trade.
- **Família:** um grupo de regras com a mesma ideia. São permitidas 3 variantes por família.
- **Freeze:** a foto por hash do código e da configuração de um bot.
- **Holdout prospectivo:** dados que não existiam quando a regra foi criada; a prova final.
- **Lookahead (viés de):** a regra usa informação do futuro sem perceber.
- **N / Deflated Sharpe Ratio:** a correção estatística pelo número de tentativas feitas.
- **Overfitting:** a regra decorou o passado em vez de capturar algo que se repete.
- **Portões (gates):** os critérios fixos de aprovação, em `lab/config/gates.json`.
- **Split:** um pedaço do histórico com um uso definido: exploração, validação ou holdout.

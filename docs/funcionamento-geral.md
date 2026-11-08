# Manual do Trading Lab: como o projeto funciona e como você pode ajudar

Este é o manual completo do projeto. Ele explica, do começo ao fim, de onde vêm as ideias, como uma estratégia é
testada, quem decide o quê, onde os robôs rodam, quais arquivos controlam cada parte e, no fim (seção 13), **o que você
pode fazer para ajudar o Claude e os agentes a chegarem numa estratégia vencedora**.

Estado descrito: **08/11/2026**. Os números de cada seção são desta data.

Como ler: as seções 1 a 3 dão a visão geral; 4 a 6 são o motor de pesquisa por dentro; 7 a 9 são a execução (dry-run,
VPS); 10 a 12 são referência (situação atual, pastas, comandos); 13 é o seu papel; 14 é o glossário.

---

## 1. A ideia em uma página

O projeto é uma **fábrica de estratégias de trading com controle de qualidade**. Ela tem duas metades:

```
 PESQUISA (lab/, agentes de IA)                      EXECUÇÃO (Freqtrade, ops/, live/)
 ───────────────────────────────────────────         ───────────────────────────────────

 Internet ──► Scout ──► Triagem ──► Research           Estratégia que passou na validação
 (papers,    (ideias)  (código,    (hipótese                │
  repos de             sem IA)      formal H-NNN)           ▼
  robôs)                                │              Freeze (hash de cada byte)
                                        ▼                   │
                                   Developer                ▼
                                   (código Freqtrade    Bot de dry-run (preço real,
                                    + teste)            ordens simuladas, 24/7)
                                        │                   │
                                        ▼                   ▼
                         Checagem de causalidade        Holdout prospectivo
                         (olha o futuro? estável?)      (a partir de 2027-04-21)
                                        │                   │
                                        ▼                   ▼
                         Calibração + EXPLORAÇÃO        Testnet → piloto real
                         (backtest 2017–2024, 9 pares,  (SÓ com a sua liberação)
                          4 cenários de custo)
                                        │
                     ┌──────────────────┴─────────────────┐
                 reprovada                     passou em ≥ 6 dos 9 pares
                     │                                    │
                 arquivada               AUTOPILOT lê a VALIDAÇÃO (uma vez)
                                                          │
                                          ≥ 2 pares passaram? AUTOPILOT sobe
                                          os bots de dry-run (dinheiro real: nunca)
```

**A regra mais importante:** os agentes de IA **escrevem textos e código, mas nunca decidem**. Quem aprova ou reprova são
regras fixas em código (os **portões**, ou *gates*). Uma **política sua** (o autopilot, seção 6) libera sozinha a
leitura da validação e o dry-run. **Dinheiro real é exclusivamente seu.**

---

## 2. Por que tanta trava? O problema que o projeto resolve

Quase qualquer estratégia parece ótima se você testá-la muitas vezes no mesmo histórico e ficar com a melhor. Isso é
**overfitting** (sobreajuste): a regra decorou o passado em vez de capturar algo que se repete.

Exemplo: teste 50 regras aleatórias em 2017–2024. Por puro acaso, 2 ou 3 parecem lucrativas. Opere essas e você perde.

O projeto se defende de cinco formas:

1. **Dados separados no tempo.** Uma parte do histórico serve para procurar (exploração). Outra fica guardada e é lida
   **uma única vez** por hipótese (validação). Depois vem o futuro de verdade (holdout prospectivo).
2. **Contagem de tentativas.** Toda configuração testada entra no **N** do *Deflated Sharpe Ratio*. Hoje N passa de 115.
   Quanto maior o N, mais forte uma estratégia precisa ser para ser levada a sério.
3. **Regra escrita antes do teste.** A hipótese é registrada com todos os números **antes** de rodar. Mudar um número
   depois de ver o resultado cria uma **hipótese nova** (ID novo, conta no N).
4. **Portões fixos.** Os critérios estão em `lab/config/gates.json`, protegido: nenhum agente consegue afrouxá-los.
5. **Amplitude.** Com 9 pares, a regra precisa funcionar na maioria deles (6 de 9), não num par de sorte.

---

## 3. Os dados

### 3.1 Universo
- **9 pares spot da Binance contra USDT** (desde 06/11/2026): BTC, ETH, BNB (os originais), XRP, ADA, LTC, LINK, DOGE e
  SOL. Só comprado: sem short, sem alavancagem, sem margem.
- **Timeframes:** `15m` e `1h`. Filtros de prazo maior (4h, 1d) são montados a partir de candles fechados.
- **Histórico:** de 2017 (2018–2020 nos pares mais novos) até hoje, em `user_data/data/binance/` (fora do git).
- Configuração: `lab/config/scenarios.json`.

### 3.2 As janelas de tempo (splits)

| Janela | Período | Para que serve | Quem lê |
|---|---|---|---|
| **Exploração** | início de cada par → 04/07/2024 | procurar e calibrar | o pipeline, à vontade |
| **Validação** | 05/07/2024 → 20/10/2026 | confirmar, **uma vez** por hipótese | o autopilot (política sua) ou você |
| **Holdout prospectivo** | 21/10/2026 → | prova final, com dados que não existiam quando as regras foram criadas | ninguém até 21/04/2027 |

Todos os pares cortam a exploração no mesmo calendário (BNB tem uma diferença de 3 semanas, de antes). Arquivos:
`lab/config/splits.json` e `lab/config/holdout.json` (protegidos).

---

## 4. O ciclo de pesquisa, passo a passo

Um ciclo roda com `python -m lab.pipeline weekly --scout-count 10 --max-new 10`. O nome diz "semanal", mas roda a
qualquer hora; hoje roda em **loop contínuo**, um ciclo atrás do outro. Um ciclo com 9 pares leva de 2 a 5 horas.

### 4.1 Scout: coletar ideias
O agente **scout** (modelo Opus) pesquisa na internet e escreve cada ideia como JSON em `research/intake/`.
- **Onde procura:** repositórios e documentação de **robôs de day trade** (freqtrade-strategies, Jesse, Hummingbot,
  OctoBot, QuantConnect), descrições de estratégias do TradingView, blogs de praticantes, artigos acadêmicos de cripto
  intraday (SSRN, arXiv).
- **Esforço mínimo:** pelo menos 10 buscas e 8 páginas abertas antes de dizer que não achou nada.
- **O que escreve:** a regra **em palavras**, com o **mecanismo** (quem está do outro lado do trade e por que deixaria
  esse dinheiro na mesa), a fonte com licença e uma estimativa de trades por ano.
- **Proibido:** copiar código, reportar desempenho, ver qualquer resultado do laboratório.

### 4.2 Triagem: filtro automático (sem IA, `lab/triage.py`)
Descarta, sem gastar nada, a ideia que:
- usa um timeframe que o lab não roda, ou precisa de mais de 4.500 candles de aquecimento;
- pede short, alavancagem, martingale ou position sizing;
- vai gerar poucos trades (não dá 30 na exploração);
- repete uma regra já testada (sobreposição de palavras);
- pertence a uma família que já gastou suas **3 variantes**.

As restantes ganham nota (simplicidade, parâmetros fixos, fonte acadêmica, folga de trades) e entram na fila.

### 4.3 Research: formalizar a hipótese
O agente **research** (Opus) transforma a ideia numa hipótese formal, `research/proposals/H-NNN.json`: regra completa,
todos os números, aquecimento declarado, mecanismo e critério de sucesso. O código valida e registra a hipótese em
`research/lab.sqlite` e no `research/hypothesis-ledger.md` **antes de qualquer teste**. O research não vê validação.

### 4.4 Developer: escrever o código
O agente **developer** (Opus) escreve a estratégia Freqtrade, `user_data/strategies/<Familia>_H<NNN>_v1.py`, e um teste
unitário. Uma checagem estática (`lab/strategy_check.py`) recusa imports proibidos, rede e arquivos, `shift(-n)` (olhar o
futuro), sizing e alavancagem. Depois **a suíte inteira** (580 testes) tem de passar. São 2 tentativas; se falhar, o
código vai para `research/rejected/`.

Regras de contrato que valem para toda estratégia: `minimal_roi = {"0": 100}` (o alvo de lucro e a saída por tempo são
feitos em `custom_exit`), `stoploss` negativo, `can_short = False`, só candles fechados.

### 4.5 Checagem de causalidade
Duas análises do próprio Freqtrade, em BTC, ETH e BNB:
- **lookahead-analysis:** a regra usa informação que só existiria no futuro?
- **recursive-analysis:** os indicadores dão o mesmo valor com mais ou menos histórico carregado?

Reprovar aqui quer dizer **erro técnico** na regra (aconteceu com 9 hipóteses).

### 4.6 Calibração e exploração
1. **Calibração:** um backtest com exposição total, para obter a lista de trades. Menos de 30 trades em mais de 3 pares
   descarta a hipótese.
2. **Exposição:** um *bootstrap* (reamostragem dos trades, 4.000 vezes) escolhe **que fração da carteira** arriscar,
   num grid de 5%, para o drawdown simulado ficar abaixo de 25% em 95% dos casos, em pelo menos 6 pares.
3. **Carteira:** todos os backtests começam com **1.000 USDT simulados** (desde 08/11/2026; antes eram 100, e isso
   descartava regras que pediam posições abaixo da ordem mínima de 10 USDT da Binance).
4. **Exploração oficial:** backtest com essa exposição nos **4 cenários de custo**:

| Cenário | Taxa por lado | Slippage + spread por lado | **Ida e volta** |
|---|---|---|---|
| otimista | 0,075% | 0 | 0,15% |
| **base** | 0,075% | 0,075% | **0,30%** |
| conservador | 0,075% | 0,15% | 0,45% |
| stress | 0,075% | 0,375% | 0,90% |

A taxa de 0,075% é a da Binance pagando em BNB (decisão sua de 06/11; a conta real precisa ter BNB para as taxas).

### 4.7 Portões (o juiz, `lab/gates.py`)
Cada par recebe uma decisão. Para a hipótese passar na exploração, **6 dos 9 pares** precisam ser candidatos.

| Portão | Exigência por par |
|---|---|
| Lookahead / recursive | sem viés, indicadores estáveis |
| Trades mínimos | ≥ 30 no período (abaixo disso: "inconclusiva") |
| Lucro líquido | > 10 USDT (1% da carteira) no base **e** no conservador; a régua sobe 10% a cada variante da mesma família |
| Lucro sem o melhor trade | ainda positivo (não pode depender de um trade de sorte) |
| Drawdown máximo | ≤ 25% no otimista, base e conservador (o stress é só reportado, desde 06/11) |
| Benchmarks | comparar com caixa e com buy-and-hold (reportar é obrigatório; vencer não) |

Só existem três decisões: `rejected`, `inconclusive`, `candidate_for_portfolio`. **Não existe "aprovado para operar
real"** no laboratório.

### 4.8 Revisão e arquivo
- **Candidata:** três agentes revisores (validator, quant, risk; modelo Sonnet) escrevem pareceres. Eles comentam, não
  decidem. Depois o **autopilot** assume (seção 6).
- **Reprovada:** vai para o **arquivo**. O código vai para `user_data/strategies/_archive/` com o hash registrado, o
  teste para `tests/archive/`. O portal não mostra arquivadas (só nas contagens do funil). O arquivo serve para os
  agentes consultarem o que já foi tentado. Nada é apagado: tudo é reproduzível.

No fim, o ciclo grava `research/pipeline/cycle-*.md` e faz commit de tudo.

---

## 5. As regras do jogo hoje: day trade com muitos trades

Esta é a sua direção atual (08/11/2026), em `research/guidance.md` e nas instruções de cada agente:

- **Muitos trades por dia:** 1 a 4 por dia por par (400 a 1.500 por ano). Com 9 pares, de 10 a 35 trades por dia no
  portfólio. Assim o dry-run junta evidência em semanas, não em anos.
- **Gráfico de 15m** (ou 1h com saídas intraday). **Toda posição fecha em até 12 horas** (saída por tempo obrigatória).
- **O custo manda:** a ida e volta custa 0,30% (base), então cada trade precisa render em média pelo menos ~0,5% bruto:
  alvos de 0,8% a 2%, stop curto, entradas só em gatilhos intraday fortes (expansão de volatilidade ou volume,
  aberturas de sessão 00:00/08:00/13:30 UTC, rompimentos de faixa, varridas de liquidez, VWAP).
- **Blocos de montagem** estudados do projeto day-trader-skill (ver `docs/estudo-day-trader-skill.md`): faixa de
  abertura com stop no meio da faixa e alvo em R, saída por horário, limite de entradas por dia, parada do dia após
  perdas, e **distância mínima de stop de ~1% do preço**, para o custo não comer o R.

**O que já sabemos (lições pagas):**
- Regras com centenas de trades de movimento pequeno perdem tudo para o custo (H-002, H-041, H-044).
- Regras lentas (H-004: 13 trades em 7 anos) não servem ao objetivo, por melhor que pareça o backtest.
- A maioria das ideias de day trade testadas (H-050 a H-085) **não tinha vantagem nem antes do custo**.
- Faixas de abertura estreitas em 15m: o custo vale 1 a 1,5R por trade (achado da Time Machine).

---

## 6. Da candidata ao dinheiro real

| Degrau | O que acontece | Quem libera |
|---|---|---|
| 1. Exploração | automático no ciclo | o pipeline |
| 2. **Validação** | backtest 2024–2026 nos pares que passaram na exploração, lido uma vez | **autopilot** (política sua) |
| 3. **Dry-run** | bot com preço real e ordens simuladas, 24/7, nos pares que passaram na validação (mínimo 2) | **autopilot** |
| 4. Holdout | avaliação formal com dados novos, ≥ 30 trades fechados | data fixa: a partir de 21/04/2027 |
| 5. Testnet | testa a mecânica (chaves, ordens, stop na corretora) com dinheiro fictício | você |
| 6. **Real** | piloto pequeno, com várias travas | **só você** (`docs/runbook-ao-vivo.md`) |

### 6.1 O autopilot (`lab/autopilot.py`, `lab/config/autopilot.json`)
Sua política de 06/11: "toda candidata pode chegar até dry-run sozinha; operação real não".
1. A hipótese passa na exploração (6 de 9 pares). O autopilot lê a validação **uma vez**, só nesses pares, com a
   exposição calibrada. Nada é ajustado.
2. Se **2 ou mais pares** passarem, ele gera a configuração de cada bot (carteira simulada de 1.000 USDT), faz o
   freeze, commita e sobe os bots (`docker compose up -d`).
3. Se nenhum ou só 1 par passar, a hipótese é arquivada.
4. **Travas:** ordem mínima de 10 USDT; no máximo **20 bots** ao mesmo tempo (acima disso pede a você);
   `real_money: false` obrigatório (senão o código recusa a política); nenhum agente pode editar a política; a
   configuração base mantém `dry_run: true`.
5. Tudo fica registrado como aprovação de `autopilot-policy`, com seu nome e a data da política.

### 6.2 Freeze (congelamento)
Antes do dry-run, a estratégia, as configurações e o compose do bot são "fotografados" por SHA-256
(`research/forward/H-NNN-freeze.json`). Se qualquer byte mudar, a checagem acusa e o bot deixa de valer como evidência.
Ninguém pode "dar uma ajustadinha" numa estratégia em avaliação. Antes de religar um bot, eu sempre rodo essa checagem.

### 6.3 Portfólio (`lab/portfolio.py`)
Só entra a estratégia candidata na exploração **e** na validação, consistente entre pares, com correlação ≤ 0,7 com as
que já estão dentro. Pesos iguais; ordem de entrada pelo registro, nunca pelo retorno.

---

## 7. Os agentes por dentro

Todos são subagentes do Claude Code, definidos em `.claude/agents/*.md`, chamados em modo headless
(`claude -p --agent <nome>`) por `lab/agents.py`.

| Agente | Modelo | Função | Pode escrever em | Não pode ver |
|---|---|---|---|---|
| scout | Opus | coletar ideias na web | `research/intake/` | qualquer resultado |
| research | Opus | formalizar a hipótese | `research/proposals/` | validação, banco, relatórios |
| developer | Opus | estratégia + teste | `user_data/strategies/`, `tests/` | — |
| validator, quant, risk | Sonnet | pareceres | um arquivo cada em `research/experiments/*/` | — |

**O que cada agente lê ao começar:** um "arquivo de contexto" gerado pelo código (`lab/context.py`) com o escopo, os
limites, os custos, as famílias e regras já tentadas (só texto e resultados de exploração), mais `research/guidance.md`.
É por esses dois caminhos que a sua direção chega neles.

**Guard (`lab/guard.py`):** depois de **cada** chamada de agente, o código compara o repositório antes e depois. Se o
agente escreveu fora do permitido, ou alguém tocou num arquivo protegido, o ciclo **para** (`GuardAbort`). Por isso,
**ninguém pode escrever no repositório enquanto um ciclo roda**: o guard não sabe quem escreveu.

**Orçamento (`lab/config/budget.json`):**

| Limite | Valor |
|---|---|
| Por chamada de agente | US$ 4 |
| Por ciclo | US$ 60 |
| Hipóteses novas por ciclo | até 10 |
| Variantes por família | até 3 |
| Tempo máximo por agente | 1.500 s |

Gasto real: de US$ 3 a US$ 10 por ciclo. Total até hoje: cerca de US$ 79 em 245 chamadas.

---

## 8. A execução: onde as estratégias rodam

### 8.1 Bots de dry-run (ligados hoje)
- Rodam no **Docker Desktop** (precisa estar aberto; se ele parar, os bots param junto).
- `docker-compose.forward.yml`: H-009 em BTC, ETH e BNB. `docker-compose.forward.h016.yml`: H-016 em ETH.
  `docker-compose.forward.h047.yml`: H-047 em ETH.
- Os 5 bots atuais têm carteira simulada de 100 USDT (congelada); bots novos nascem com 1.000.
- Sem API exposta, sem chave de corretora, sem porta aberta. Cada bot tem seu banco `user_data/tradesv3.forward.*.sqlite`.
- Relatório: `python research/tools/forward_report.py H-009`.

### 8.2 Time Machine (`lab/timemachine.py`, desde 08/11)
Ferramenta de pesquisa e acompanhamento portada do day-trader-skill: para um plano (par, dia, entrada, stop, alvo, hora
de zerar) ela refaz o resto da sessão 10.000 vezes com os candles de 15m do próprio par e roda a mesma regra de faixa de
abertura nos 60 dias anteriores. Dá as chances (alvo primeiro, stop primeiro, nenhum), o R médio **depois do custo** e
um veredito honesto ("cara ou coroa", "tende ao stop"...). Não é portão.

### 8.3 Guarda de portfólio (`ops/freqtrade_guard.py`)
Fora dos bots, a cada 5 minutos (cron, na VPS): verifica se os bots estão vivos, soma o prejuízo do dia e total, e para
todos se um limite for atingido ou se existir `ops/state/STOP.<nome>`. Nada religa sozinho.

### 8.4 Camada `live/` (MetaTrader 5)
Motor próprio para MT5 (mini índice e mini dólar na B3, no futuro): gestor de risco (perda diária R$ 300, semanal R$ 900,
2 contratos, 10 operações por dia), kill switch `live/STOP`, journal e reconciliação. Testado só em conta demo. Nenhuma
estratégia do lab foi pesquisada para B3 ainda.

---

## 9. A VPS

### 9.1 Pronto
`ops/vps/bootstrap-ubuntu.sh` (Ubuntu 24.04, Azure Brazil South, ~US$ 52/mês): Docker, relógio UTC, firewall só SSH,
rotação de logs, cron do guarda e backup diário. Com isso a VPS roda **os bots** 24/7 sem o seu PC.

### 9.2 Falta para a pesquisa rodar lá
| # | Passo | Por quê |
|---|---|---|
| 1 | Python, dependências e o **Claude Code CLI** | os agentes são chamadas `claude -p` |
| 2 | **Chave de API Anthropic** com crédito, em variável de ambiente | sem ela nenhum agente roda; é de onde sai o gasto |
| 3 | Baixar os candles dos 9 pares (1h e 15m) | os dados não vão no git |
| 4 | **Repositório remoto privado** (GitHub) | hoje não existe remote; a VPS precisa clonar e devolver os resultados |
| 5 | Ciclos no cron + `git push` | rodar sem você |
| 6 | Alertas (Telegram) | saber quando surge candidata ou bot novo |
| 7 | Máquina maior para a pesquisa (ou pesquisa no PC e só bots na VPS) | backtests de 15m em 9 pares × 4 cenários são pesados |
| 8 | Um só processo escrevendo no repositório | o guard derruba o ciclo se outro escrever |

---

## 10. Onde estamos (08/11/2026)

- **Hipóteses registradas:** 87 (H-001 a H-087). Gasto total com agentes: ~US$ 79.
- **Funil:** 48 reprovadas nos portões, 14 descartadas pela ordem mínima (carteira de 100), 11 descartadas por outros
  motivos (poucos trades, drawdown), 9 com erro de causalidade, 1 inválida, 1 candidata de exploração (H-009).
- **Validação lida:** H-008, H-016, H-020, H-024, H-025, H-040, H-046, H-047. Passaram em algum par: **H-016** (ETH) e
  **H-047** (ETH, força relativa entre pares, 74 trades e +10,7% na validação no custo base).
- **Em dry-run:** H-009 (BTC, ETH, BNB), H-016 (ETH), H-047 (ETH).
- **Próximos passos já decididos:** re-rodar, com o código idêntico e a carteira de 1.000, as 14 hipóteses descartadas
  só pela ordem mínima (comando `recalibrate`; inclui H-069, o ORB da abertura de Nova York); testar a variante ORB com
  faixa mínima de 2%; seguir o loop contínuo com a direção de muitos trades.

**Nenhuma estratégia tem, até hoje, evidência suficiente para dinheiro real.** É o resultado normal de um processo
honesto: a maioria das ideias de trading não sobrevive a um teste justo. O lab existe para achar a minoria que sobrevive
sem se enganar no caminho.

---

## 11. Mapa de pastas e arquivos

| Pasta / arquivo | O que tem |
|---|---|
| `lab/pipeline.py` | o ciclo completo (weekly, resume, recalibrate, autopilot) |
| `lab/orchestrator.py` | chamadas aos agentes, registro, backtests, decisões |
| `lab/gates.py`, `lab/calibrate.py`, `lab/bootstrap.py`, `lab/breadth.py` | portões, calibração, bootstrap, regra de 6 de 9 |
| `lab/autopilot.py`, `lab/forward.py` | política até o dry-run; freeze e relatórios dos bots |
| `lab/guard.py`, `lab/agents.py`, `lab/context.py` | guarda do repositório; chamada dos agentes; contexto que eles leem |
| `lab/timemachine.py` | a Time Machine |
| `lab/config/` | regras: `gates.json`, `splits.json`, `holdout.json` (protegidos), `scenarios.json`, `budget.json`, `breadth.json`, `autopilot.json`, `portfolio.json` |
| `.claude/agents/*.md` | instruções de cada agente |
| `research/guidance.md` | **a sua direção para os agentes** |
| `research/lab.sqlite` | banco: hipóteses, experimentos, métricas, decisões, aprovações (a fonte da verdade) |
| `research/hypothesis-ledger.md` | o livro de todas as hipóteses, legível |
| `research/intake/`, `research/proposals/` | ideias do scout; hipóteses formais |
| `research/pipeline/cycle-*.md` | relatório de cada ciclo |
| `research/forward/` | freezes dos bots |
| `user_data/strategies/` | estratégias ativas (`_archive/` guarda as reprovadas) |
| `forward/`, `docker-compose.forward*.yml` | configuração dos bots de dry-run |
| `ops/`, `live/`, `testnet/` | guarda e VPS; motor MT5; ensaio na testnet |
| `tests/` | 580 testes automáticos |
| `docs/` | este manual, protocolos, runbook da operação real, estudo do day-trader-skill |

---

## 12. Comandos do dia a dia

```bash
# Um ciclo de pesquisa
python -m lab.pipeline weekly --scout-count 10 --max-new 10

# Retomar hipóteses que falharam por infraestrutura (Docker caiu, ciclo interrompido)
python -m lab.pipeline resume H-085

# Re-rodar, com o código idêntico, hipóteses descartadas só pela ordem mínima
python -m lab.pipeline recalibrate H-069 H-052

# Aplicar o autopilot a candidatas antigas
python -m lab.pipeline autopilot H-020

# Estado: hipóteses, decisões, gasto
python -m lab.orchestrator status

# Time Machine de um plano
python -m lab.timemachine BTC/USDT --date 2023-03-13 --entry-time 14:15 --entry 22918.8 \
    --stop 22380.3 --target 23995.9 --session-start 13:30 --session-hours 6.5

# Bots: conferir o freeze, ver o relatório
python research/tools/forward_freeze.py H-009 --check
python research/tools/forward_report.py H-009

# Testes
python -m unittest discover -s tests
```

---

## 13. Como você pode ajudar o Claude e os agentes

Os agentes são bons em pesquisar, escrever e testar rápido. O que eles **não** têm é o que só você tem: acesso a
fontes fechadas, conhecimento de mercado, decisões de risco e a máquina ligada. Em ordem de impacto:

### 13.1 Trazer ideias com mecanismo
A melhor contribuição. Um link (repositório, artigo, vídeo, canal de trader) ou uma regra que você já viu funcionar.
Quanto mais concreto, melhor: **entrada exata, saída exata, stop, horário, e por que funciona** (quem perde dinheiro
para essa regra). Foi assim com o day-trader-skill: você mandou o link, eu estudei e virou Time Machine, uma hipótese
nova e uma lição de custo. Mande no chat; eu transformo em ideia no formato do lab (ela passa pela triagem e conta no N
como qualquer outra).

### 13.2 Dar direção, não números
Diga **o que** procurar ("sessão de Nova York", "altcoins voláteis", "reversão depois de liquidações", "não quero
segurar mais de 4 horas"). Eu escrevo isso em `research/guidance.md` e nas instruções dos agentes. **Não** peça para
"trocar o 20 por 15 na H-024": mudar um número depois de ver o resultado é overfitting; vira hipótese nova, e isso é
caro em credibilidade estatística.

### 13.3 Tomar as decisões que são suas
Os portões, os custos, a carteira, o universo de pares, a política do autopilot e, acima de tudo, o dinheiro real são
decisões de risco suas. Quando eu perguntar, a pergunta é sobre isso. Exemplos que você já tomou: taxa com BNB,
drawdown de stress só reportado, 9 pares, carteira de 1.000, day trade. Cada uma ficou registrada com data no arquivo
que ela muda.

### 13.4 Cuidar da infraestrutura
- **Deixar o Docker Desktop aberto** (e configurado para iniciar com o Windows): sem ele os bots e os backtests param.
- **Não fechar a tampa nem desligar** durante um ciclo; se precisar, me peça para pausar (eu paro num ponto
  retomável, como no dia 07/11).
- **Não editar arquivos do projeto enquanto um ciclo roda** (nem outra sessão do Claude): o guard derruba o ciclo.
- Quando decidir pela VPS: criar a conta, a chave de API Anthropic e o repositório privado no GitHub (seção 9.2). O
  resto eu configuro.

### 13.5 Acompanhar o dry-run
Olhar o portal e os relatórios dos bots de vez em quando, e me avisar de qualquer coisa estranha (bot parado, trade
absurdo). Resultado de dry-run é **monitoramento**: não mude nada por causa de uma semana boa ou ruim; a avaliação formal
é o holdout.

### 13.6 Preparar o caminho para o real
Quando uma estratégia chegar ao holdout com evidência: conta na Binance com **BNB para as taxas**, chave de API só com
permissão de trade (sem saque), na variável de ambiente (nunca no chat ou no git), limites de perda definidos por você.
O passo a passo está em `docs/runbook-ao-vivo.md` e `docs/checklist-operacao-real.md`.

### 13.7 Estudar
Ler este manual, `research/guidance.md`, alguns relatórios em `research/pipeline/` e um par de hipóteses no ledger dá
uma boa noção de como os agentes pensam. Os conceitos que mais importam: overfitting, custo por trade em relação ao
movimento, drawdown, e por que a validação só pode ser lida uma vez.

---

## 14. Glossário

- **Backtest:** simular a regra no histórico, candle a candle.
- **Bootstrap:** reamostrar os trades milhares de vezes para estimar o pior caso provável.
- **Bracket:** entrada com stop e alvo definidos antes, como uma ordem só.
- **Candidata:** passou em todos os portões de uma janela. Não é aprovação para operar.
- **Custo de ida e volta:** taxas + slippage + spread de comprar e vender (0,30% no cenário base).
- **Drawdown:** a maior queda do saldo a partir de um pico.
- **Dry-run / forward test:** o bot roda ao vivo, com preço real, mas as ordens são simuladas.
- **Exposição:** a fração da carteira usada em cada trade.
- **Família:** grupo de regras com a mesma ideia; até 3 variantes.
- **Faixa de abertura (opening range, ORB):** a máxima e a mínima dos primeiros minutos de uma sessão; o rompimento dela é um setup clássico de day trade.
- **Freeze:** a foto por hash do código e da configuração de um bot.
- **Holdout prospectivo:** dados que não existiam quando a regra foi criada; a prova final.
- **Lookahead (viés de):** a regra usa informação do futuro sem perceber.
- **N / Deflated Sharpe Ratio:** a correção estatística pelo número de tentativas.
- **Overfitting:** a regra decorou o passado em vez de capturar algo que se repete.
- **Portões (gates):** os critérios fixos de aprovação.
- **R:** a unidade de risco de um trade (distância da entrada ao stop). Alvo de 2R = ganhar o dobro do que se arrisca.
- **Split:** pedaço do histórico com uso definido: exploração, validação ou holdout.
- **Time Machine:** a ferramenta que mede as chances de um plano antes de operá-lo (seção 8.2).

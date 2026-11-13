# Plano de evolução dos bots de day trade (13/11/2026)

Para: o dono do laboratório. Base: o registro (`research/lab.sqlite`), o placar, os relatórios de ciclo e três medições novas feitas hoje com código (scripts em `research/tools/`, citados em cada tabela). Validação e holdout não foram lidos. Nenhum número veio de agente.

## 0. Resumo

1. **O estado da seção 1 confere** com o registro: 129 hipóteses, N do DSR = 159, dry-run vazio, H-104/H-101/H-102/H-035 rejeitadas nos 26 pares (9, 8, 7 e 12 pares candidatos de 16 exigidos), H-100 na terceira tentativa (as duas primeiras caíram no teste de fumaça do Docker no ETH, não na regra).
2. **Achado mais importante de hoje: a regra de 2 dias sem trade aposenta praticamente qualquer bot antes do julgamento.** Os trades vêm em rajadas: o H-104 nos 26 pares faz em média 2,1 trades/dia, mas fica 2 dias sem fechar trade em 24% das janelas (Poisson diria 1,6%). A chance de um bot dele chegar aos 14 dias mínimos do julgamento é 8%; nos pares candidatos, 0%. Mesmo uma regra com lucro real não sobreviveria. Isso é decisão do dono (seção 3, D1).
3. **O custo de execução medido é bem menor que o modelado, mas a taxa domina e o gate conservador continua sendo o limite.** Para uma ordem de 1.000 USDT, o spread mais o impacto custam 0 a 3 pb por lado na maioria dos pares (ETC 7,7 pb, por tick grande); o cenário base supõe 7,5 pb e o conservador 15 pb. A taxa (0,075% por lado) é metade do custo base. Falta medir a derrapagem por atraso nas barras de muito volume, justamente onde as regras entram.
4. **A regra de amplitude 16/26 não é o gargalo.** Na simulação com regras sintéticas, afrouxar para 13/26 aprova 38% das regras que só empatam no custo conservador e 13% das que perdem 0,10% por trade; a avaliação agrupada com bootstrap é mais rígida que a atual. Recomendo manter.
5. **A exploração levava ~1h50 por hipótese em 26 pares** (3,5 min por par: 4 backtests de 33 s, lookahead de 50 s, recursive de 30 s, cada um num contêiner novo). Agora roda 3 pares em paralelo e para quando a aprovação fica matematicamente impossível. Medido: a H-121 arquivada (9 pares) rodou de novo em 20 min contra 58 min, com as mesmas decisões e os mesmos motivos de gate, linha por linha, nos 9 pares.

**Decisões do dono em 13/11/2026:** D1 sim (inatividade esperada contra observada); D2 sim (faixa de futuros 1x em dry-run, especificação em `docs/faixa-futuros.md`); D3 e D5 não agora (maker, 5m/1m, ML); D4 manter 16/26.

Expectativa honesta para a meta (uma hipótese aprovada na exploração e na validação com líquido positivo a 0,45%): baixa enquanto o lab for spot, só compra. As quatro regras mais próximas têm bruto de 0,6-0,7% por trade (líquido médio positivo a 0,45%), mas perdem em 2022-2024 e falham em metade dos pares. A alavanca com mais suporte nos dados continua sendo futuros (custo menor e venda a descoberto), que é decisão sua.

## 1. Diagnóstico conferido

| Afirmação do briefing | Conferido em | Resultado |
|---|---|---|
| 26 pares, amplitude 16/26 | `scenarios.json`, `breadth.json` | Confere |
| Dry-run vazio | `docker ps`, `research/forward/` | Confere: nenhum contêiner de bot |
| H-104 9/26, H-101 8/26, H-102 7/26, H-035 12/26 | decisões de 13/11 no registro | Confere |
| H-100 em nova rodada | processo `recalibrate H-100` (PID 32332, outra sessão) | Confere. As duas falhas anteriores foram `smoke_ok=false` no ETH, com lookahead e recursive limpos: infraestrutura |
| 0 de 17 regras frequentes positivas a 0,30% | `research/knowledge/scoreboard.md` | Confere |
| H-124 implementada, H-125..H-128 falha de implementação, H-129 proposta | `orchestrator status` | Confere |
| `git commit` exit 128 intermitente | logs de ciclo | Confere, sem a causa: o pipeline captura o stderr do git e não o imprime. Hipótese mais provável: `index.lock` disputado com outra sessão ou com o git do VS Code |
| Gasto com agentes | `agent_runs` | 146,89 USD no total |

Mais dois fatos:
- A rodada do H-101 nos 26 pares teve **lookahead FAIL num par** (o último da lista). Não muda a decisão (já rejeitada), mas mostra que o lookahead por par pega coisas que os 3 pares de causalidade não pegam: não proponho cortar isso para ganhar tempo.
- Há muitas mudanças não commitadas de outras sessões (portal, testes apagados de estratégias arquivadas). Não vou commitá-las: só commito os arquivos que eu criar ou mudar, por caminho explícito.

## 2. As três medições de hoje

### 2.1 Regra de 2 dias sem trade (frente C)

Script: `research/tools/inactivity_gaps.py`. Dados: trades da exploração (custo base), últimos 365 dias da exploração, em que os 26 pares têm dados.

| Hipótese | Pares do bot | Trades/dia | 2 dias sem fechar trade (medido) | Poisson | Sobrevive 14 dias | Sobrevive 30 dias | Maior intervalo no ano (dias) |
|---|---|--:|--:|--:|--:|--:|--:|
| H-104 | 26 | 2,07 | 24% | 1,6% | 8% | 1% | 26,6 |
| H-104 | 9 candidatos | 0,62 | 49% | 29% | 0% | 0% | 37,0 |
| H-101 | 26 | 1,53 | 20% | 4,7% | 3% | 0% | 6,7 |
| H-035 | 26 | 1,01 | 38% | 13% | 3% | 0% | 15,4 |
| H-102 | 26 | 0,83 | 38% | 19% | 2% | 0% | 20,0 |
| H-100 | 9 | 1,24 | 26% | 8,3% | 3% | 0% | 9,1 |
| H-043 | 9 | 1,02 | 35% | 13% | 3% | 0% | 39,0 |
| H-123 | 9 | 1,72 | 14% | 3,2% | 6% | 0% | 7,2 |

Leitura: o gatilho das melhores regras é volume alto, e volume alto acontece no mercado todo ao mesmo tempo. Os trades se concentram em dias agitados e somem em semanas calmas, em todos os pares juntos. A conta de Poisson do briefing (25% para 0,7 trade/dia) subestima o problema: medido, é 49%. **Com a regra atual, o dry-run não consegue aprovar nenhuma regra deste tipo**, porque o julgamento exige 14 dias e 60 trades fechados.

Proposta (decisão D1): trocar "2 dias sem trade" por **"esperado contra observado"**, calculado antes de ligar o bot e gravado no congelamento:
- da lista de trades da exploração nos mesmos pares, tirar a distribuição de trades fechados em janelas de T dias (com as rajadas, porque é medida e não suposta);
- aposentar o bot se, depois de T dias, ele fechou menos trades que o percentil 1 dessa distribuição, ou se ficou mais tempo sem trade que o maior intervalo da exploração (no H-104 em 26 pares, 26,6 dias);
- avisar no portal a partir do percentil 5.

Isso mantém o espírito "validação rápida": um bot quebrado (0 trades quando o backtest previa 10) sai em poucos dias. Um bot saudável não sai por calmaria do mercado.

### 2.2 Custo de execução por par (frente A)

Script: `research/tools/book_cost.py` (livro público da Binance, sem conta). Custo de uma ordem a mercado, por lado, em pontos-base (1 pb = 0,01%). Instantâneo de 13/11; a amostragem de 1 hora está na seção 2.2b.

| Par | Meio spread | Compra 250 USDT | Compra 1.000 | Compra 5.000 | Venda 5.000 |
|---|--:|--:|--:|--:|--:|
| BTC | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |
| ETH | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |
| BNB | 0,1 | 0,1 | 0,1 | 0,1 | 0,1 |
| XRP | 0,5 | 0,5 | 0,5 | 0,5 | 0,5 |
| ADA | 2,9 | 2,9 | 2,9 | 2,9 | 2,9 |
| LTC | 1,0 | 1,0 | 1,0 | 1,0 | 2,3 |
| LINK | 0,5 | 0,5 | 0,5 | 1,3 | 2,2 |
| DOGE | 0,8 | 0,8 | 0,8 | 0,8 | 0,8 |
| SOL | 0,6 | 0,6 | 0,6 | 0,6 | 0,6 |
| AVAX | 0,6 | 0,6 | 0,9 | 1,6 | 1,2 |
| DOT | 6,0 | 6,0 | 6,0 | 6,0 | 6,0 |
| TRX | 1,6 | 1,6 | 1,6 | 1,6 | 1,6 |
| NEAR | 1,4 | 1,4 | 1,4 | 2,5 | 1,4 |
| UNI | 0,9 | 0,9 | 0,9 | 1,5 | 3,8 |
| BCH | 2,2 | 2,2 | 2,2 | 3,5 | 5,8 |
| XLM | 3,4 | 3,4 | 3,4 | 3,4 | 3,4 |
| FIL | 1,4 | 1,4 | 2,1 | 3,8 | 3,0 |
| AAVE | 0,5 | 0,7 | 1,2 | 2,8 | 2,3 |
| INJ | 0,7 | 1,6 | 1,9 | 4,3 | 7,3 |
| HBAR | 0,8 | 0,8 | 0,8 | 2,7 | 3,6 |
| OP | 5,3 | 5,3 | 5,3 | 6,3 | 5,3 |
| APT | 0,9 | 0,9 | 2,9 | 4,8 | 5,3 |
| ARB | 3,4 | 3,4 | 3,4 | 3,4 | 3,6 |
| SUI | 0,6 | 0,6 | 0,6 | 1,1 | 1,0 |
| ATOM | 3,6 | 3,6 | 3,6 | 3,6 | 10,2 |
| ETC | 7,7 | 7,7 | 7,7 | 7,7 | 19,9 |
| **Modelo base** | 2,5 | spread + derrapagem = **7,5 por lado** | | | |
| **Modelo conservador** | 5,0 | **15 por lado** | | | |

**2.2b Amostragem de 1 hora** (13 amostras a cada 5 min, 13/11, 338 leituras): as medianas repetem o instantâneo (mediana entre pares de 1,3 pb por lado para 1.000 USDT). O pior momento da hora passou do modelo base em três pares: OP 12,7 pb, ATOM 10,6 e ARB 9,9. Todos ficaram abaixo do conservador (15 pb). Na venda de 5.000 USDT, ETC chegou a 22,9 pb e DOT a 16,3.

Leitura:
- No tamanho de ordem do lab (250 a 300 USDT por trade), o spread mais o impacto custam de 0 a 8 pb por lado. O modelo base (7,5 pb) cobre o pior par; o conservador (15 pb) tem folga de 2 vezes ou mais.
- Em DOT, OP, ETC, XLM e ARB o custo vem do **tick**: o preço mínimo de variação é grande em relação ao preço. Não melhora com ordem menor.
- A taxa (7,5 pb por lado com desconto BNB) é a maior parte do custo. Em futuros, a taxa de taker da Binance é bem menor (a confirmar na tabela pública antes de usar).
- **O que ainda não foi medido:** a derrapagem por atraso. O backtest compra na abertura da barra; o bot real compra alguns segundos depois, e as regras entram justamente em barras de volume alto, quando o preço anda rápido. Isso só se mede com bots rodando (frente D) ou com candles de 1 segundo da Binance nas barras de gatilho.

Proposta: **não mexer nos cenários agora.** O cenário conservador (0,45% ida e volta) parece pessimista para o spread, mas não para o atraso, que não foi medido. Quando houver bots com trades, o relatório de execução compara o custo observado com o modelo, par a par. O `dryrun.json` já tem esse campo (`max_observed_entry_cost_per_side_vs_conservative`).

### 2.3 Regra de amplitude (frente C)

Script: `research/tools/breadth_sim.py`. Regras sintéticas sobre os preços reais de 1h dos 26 pares (só a janela de exploração). Cada regra entra em horas comuns a todos os pares (rajadas de mercado, como as regras reais), segura 10 barras e tem o líquido conservador verdadeiro por trade fixado em μ. Os gates por par imitam `gates.json`. São 300 sorteios por linha. A tabela mostra a chance de passar na exploração.

| μ verdadeiro (líquido a 0,45%) | Atual 16/26 | 13/26 | Agrupado (bootstrap semanal, IC 95%) + 13/26 positivos | 6/9 originais e 9/17 novos | Só os 9 originais, 6/9 |
|---|--:|--:|--:|--:|--:|
| -0,10% (regra perdedora) | 5% | 13% | 0% | 3% | 8% |
| 0 (empata no conservador) | 17% | 38% | 6% | 14% | 26% |
| +0,05% | 27% | 53% | 9% | 22% | 31% |
| +0,10% | 45% | 70% | 22% | 43% | 53% |
| +0,20% | 68% | 89% | 40% | 61% | 72% |
| +0,30% | 91% | 98% | 76% | 88% | 94% |

Com entradas independentes por par (correlação menor), todas as regras ficam mais rígidas contra regras perdedoras: a atual cai para 0,3% e a de 13/26 para 3%. A ordem entre elas não muda.

Leitura:
- A regra atual já é um meio-termo razoável. Afrouxar compra poder aprovando regras que empatam ou perdem.
- A exploração tem pouco poder para uma vantagem pequena: uma regra com +0,10% de líquido conservador verdadeiro passa só 45% das vezes. Isso vem do ruído correlacionado entre pares, e o remédio é mais trades ou custo menor, não uma regra mais frouxa.
- Escolhi as alternativas antes de olhar qualquer hipótese real sob elas, e não calculei como as hipóteses existentes passariam. Fazer isso seria ajustar a regra olhando o resultado.

Proposta (D4): **manter 16/26.**

## 3. Plano priorizado

Impacto: quanto aproxima da meta. Esforço em horas de trabalho meu; custo em USD de agente. "Dono" = precisa da sua escolha antes.

| # | Item | Frente | Impacto | Esforço | Risco | Critério de aceite | Dono |
|---|---|---|---|---|---|---|---|
| 1 | Exploração em paralelo (3 pares por vez) e parada quando a aprovação fica impossível (11 pares não candidatos, sendo pelo menos 1 "rejected") | E | Alto: 4x mais hipóteses por dia | 4-6 h, 0 USD | Médio: Docker Desktop instável com contêineres simultâneos; SQLite com escrita concorrente (cada thread com sua conexão, escrita curta) | Rodar de novo uma hipótese arquivada (H-121, 9 pares) e obter as mesmas decisões par a par; tempo medido; suíte verde | Não |
| 2 | `git commit` com nova tentativa quando o `index.lock` está ocupado, e stderr do git no log | E | Médio: ciclos param menos | 1 h | Baixo | Teste com lock simulado; mensagem do git aparece no log | Não |
| 3 | ~~Caminho auditável para repetir uma etapa que falhou por infraestrutura~~ | E | - | - | - | **Não feito: já existe.** O teste de fumaça tenta 3 vezes desde o commit d28debd (feito por outra sessão hoje), e `recalibrate --rule-change-reason` já repete uma hipótese byte a byte, registrando o motivo | Não |
| 4 | Regra de inatividade: esperado contra observado (2.1) | C | **Muito alto**: sem isso nenhum bot chega ao julgamento | 3-4 h | Baixo | Testes com rajadas sintéticas; para cada bot, o limite gravado no congelamento antes de ligar | **Sim (D1)** |
| 5 | Futuros perpétuos em dry-run, faixa separada: margem isolada, alavancagem 1x, compra e venda, taxa de futuros + funding no custo, dados de futuros, novas divisões de exploração e validação por par | A | **Alto, principalmente pela venda** (ataca as perdas de 2022-24). O ganho de custo é pequeno com o modelo de derrapagem do lab: base 0,24% contra 0,30%, conservador 0,39% contra 0,45% (o número de 0,15% do placar supunha derrapagem bem menor) | 2-3 dias, 0 USD | Médio: liquidação e alavancagem mesmo em dry-run; histórico de futuros mais curto (2019-20) | Bot de futuros em dry-run fechando trades; backtest de uma regra conhecida com resultado conferido à mão; `real_money` intocado | **Sim (D2)** |
| 6 | Fila: exploração da H-124 nos 26 pares; reimplementar H-125..H-128; H-129 | E/B | Baixo a médio: são famílias que o placar já mostrou fracas (Bollinger, CCI, pivô Livermore, cruzamento de EMA) | Máquina: ~8 h hoje, ~2 h depois do item 1; agentes ~10-15 USD | Baixo | Rodam até a decisão | Não (religar a fila) |
| 7 | Relatório de fidelidade do dry-run (sinal a sinal contra o backtest nos mesmos dias; custo observado contra o modelado, por par) | D | Alto, quando houver bots | 1 dia | Baixo | Relatório no portal; serve de alerta, não de avaliação | Não, mas depende do item 4 para ter bots |
| 8 | Ideias novas guiadas pelo placar: momentum intradiário em dias de muito volume nos 26 pares, ranking entre pares (comprar o mais forte do dia), comportamento depois de saltos. Com futuros: as mesmas regras também vendidas | B | Médio | Agentes ~5 USD por ideia | Médio: N do DSR cresce | Cada ideia declara trades/ano/par e bruto esperado | Não (o loop já faz) |
| 9 | Dados novos grátis: volume de compra agressora (taker-buy) dos klines da Binance como filtro | B | Médio, não testado | 1 dia | Médio: mais um grau de liberdade | Ganho incremental medido só na exploração | Não para o dado; cada regra é hipótese nova |
| 10 | Limites de risco da carteira de bots (perda diária total, exposição total, kill switch) | D | Médio | 1 dia | Baixo | Testes; configurável | Valores sim |
| 11 | Ordens maker no spot | A | Incerto | 3-5 dias | Alto: o dry-run mede mal o preenchimento e a seleção adversa | Só com testnet ou dinheiro mínimo | **Sim (D3): recomendo não agora** |
| 12 | 5m / 1m e ML | B | Baixo agora: em barras menores o movimento por trade cai e o custo fica | 2-3 dias cada | Alto: N do DSR, sobreajuste | - | **Sim (D5): recomendo não agora** |
| 13 | Linux, vigia, backups | G | Operacional | Seguir `docs/migracao-linux.md` | Baixo | `verify-migration.sh` no Linux | Sim (quando migrar) |
| 14 | B3 WIN/WDO | H | Alto (custo de 0,01-0,02%) | F1/F2 prontos; falta a conta XP | Baixo | Plano §0 | Aguardando a conta |

## 4. Execução (13/11/2026)

Feito numa cópia isolada do repositório (git worktree) enquanto a rodada do H-100 de outra sessão terminava, com um commit por item:

| Item | Commit | Verificação |
|---|---|---|
| 2. Commits só com os próprios caminhos; espera o `index.lock` | `lab/gitops.py` | 5 testes novos (lock simulado, arquivo de outra sessão fica fora do commit, erro do git aparece); 102 testes de pipeline, orquestrador e autopilot passam |
| 1. Exploração em paralelo e parada antecipada | `lab/calibrate.py` | 5 testes novos; reexecução real da H-121 com decisões e motivos idênticos, 20 min contra 58 |
| 4. Inatividade esperada contra observada (D1) | `lab/activity.py`, `lab/dryrun.py`, `lab/autopilot.py`, `lab/config/dryrun.json` | 8 testes novos com rajadas sintéticas (bot em rajada não sai com 2 dias calmos; bot quebrado em regra constante sai em 3 dias; congelamentos antigos seguem a regra anterior) |
| 5. Futuros (D2) | `docs/faixa-futuros.md` | Especificação pré-registrada; dados dos 26 pares baixados (candles 1h e 15m, mark, funding). Implementação na próxima etapa, depois da sua confirmação das divisões (seção 4 de lá) |

Não feito: o item 3 (já existia). O portal ainda mostra a contagem regressiva da regra de 2 dias (`lab/livedata.py`); não mexi porque os arquivos do portal têm mudanças não commitadas de outra sessão.

Próximos: religar a fila (H-124..H-129) com a exploração nova; implementar a faixa de futuros; itens 7 a 10.

## 5. O que não foi testado

- A derrapagem por atraso nas barras de gatilho.
- O livro em horas de pico (amostragem de 1 hora apenas).
- O comportamento do Docker Desktop com 3 contêineres simultâneos (o item 1 mede isso antes de valer).
- As taxas de futuros (precisam ser conferidas na tabela pública antes do item 5).
